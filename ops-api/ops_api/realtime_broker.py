"""In-process realtime broker for sensor reading fan-out.

The broker is the bridge between the sensor-ingestor write path and the
ops-api `/zones/{id}/stream` SSE endpoint that will be added in the next
phase. It holds a set of asyncio.Queue subscribers and fans out each
published reading.

Design notes:

- Single-process model: the broker only works inside one Python process.
  When sensor-ingestor runs as an in-process background task of ops-api
  (the default for development and small farms), this is enough.
- For a multi-worker deployment, swap the broker for a Redis pubsub
  adapter. The publish/subscribe contract stays identical, so callers do
  not change.
- Subscribers are per-zone-and-metric scoped via the optional
  ``zone_id`` filter on subscribe(). The default subscription receives
  every reading.
- Queue overflow is bounded to avoid runaway memory: when a slow
  subscriber falls behind ``max_queue`` items, the oldest record is
  dropped silently. SSE clients can recover from this gap by issuing a
  fresh ``/zones/{id}/timeseries`` bootstrap on reconnect.

The broker exposes ``publish(record)``, ``subscribe(zone_id=None)`` as an
async context manager, and ``subscriber_count()`` for diagnostics.
"""

from __future__ import annotations

import asyncio
import contextlib
import threading
from dataclasses import dataclass, field
from typing import Any, AsyncIterator


DEFAULT_QUEUE_SIZE = 256


@dataclass
class _Subscriber:
    zone_id: str | None
    queue: asyncio.Queue
    loop: asyncio.AbstractEventLoop
    dropped: int = 0


@dataclass
class RealtimeBroker:
    """Process-local fan-out for sensor readings.

    Usage:

        broker = RealtimeBroker()
        await broker.publish({"zone_id": "gh-01-zone-a", "metric_name": "air_temp_c", ...})

        async with broker.subscribe(zone_id="gh-01-zone-a") as queue:
            while True:
                record = await queue.get()
                ... forward to SSE client ...
    """

    max_queue: int = DEFAULT_QUEUE_SIZE
    _subscribers: list[_Subscriber] = field(default_factory=list)
    _lock: threading.RLock = field(default_factory=threading.RLock)

    async def publish(self, record: dict[str, Any]) -> int:
        """Fan out a single record to every interested subscriber.

        Returns the number of subscribers that actually received the
        record (excludes those whose zone filter did not match).
        """
        return await asyncio.to_thread(self._publish_sync, record)

    def _publish_sync(self, record: dict[str, Any]) -> int:
        """Thread-safe fan-out used by both async and sync publishers.

        Each subscriber's queue lives on the loop that called
        ``subscribe()``. We dispatch the put via
        ``loop.call_soon_threadsafe`` so callers outside that loop can
        deliver records correctly, and so concurrent publishers do not
        race against subscriber bookkeeping.
        """
        delivered = 0
        with self._lock:
            targets = list(self._subscribers)
        zone_id = record.get("zone_id")
        for subscriber in targets:
            if subscriber.zone_id is not None and subscriber.zone_id != zone_id:
                continue
            self._enqueue(subscriber, record)
            delivered += 1
        return delivered

    def _enqueue(self, subscriber: "_Subscriber", record: dict[str, Any]) -> None:
        loop = subscriber.loop
        if loop.is_closed():
            return

        def deliver() -> None:
            try:
                subscriber.queue.put_nowait(record)
            except asyncio.QueueFull:
                with contextlib.suppress(asyncio.QueueEmpty):
                    subscriber.queue.get_nowait()
                with contextlib.suppress(asyncio.QueueFull):
                    subscriber.queue.put_nowait(record)
                subscriber.dropped += 1

        try:
            loop.call_soon_threadsafe(deliver)
        except RuntimeError:
            # Loop has shut down between the snapshot and the call.
            return

    def publish_nowait(self, record: dict[str, Any]) -> int:
        """Synchronous publish for callers running outside an event loop.

        Used by the sensor-ingestor writer when invoked from a sync
        runtime, and by smoke tests that publish from background
        threads. Always dispatches via ``call_soon_threadsafe`` so the
        target queue's loop is never violated.
        """
        return self._publish_sync(record)

    @contextlib.asynccontextmanager
    async def subscribe(self, *, zone_id: str | None = None) -> AsyncIterator[asyncio.Queue]:
        loop = asyncio.get_running_loop()
        subscriber = _Subscriber(
            zone_id=zone_id,
            queue=asyncio.Queue(maxsize=self.max_queue),
            loop=loop,
        )
        with self._lock:
            self._subscribers.append(subscriber)
        try:
            yield subscriber.queue
        finally:
            with self._lock:
                if subscriber in self._subscribers:
                    self._subscribers.remove(subscriber)

    async def subscriber_count(self) -> int:
        with self._lock:
            return len(self._subscribers)

    def subscriber_count_sync(self) -> int:
        with self._lock:
            return len(self._subscribers)
