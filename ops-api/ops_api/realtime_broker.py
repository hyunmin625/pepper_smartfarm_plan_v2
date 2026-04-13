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
from dataclasses import dataclass, field
from typing import Any, AsyncIterator


DEFAULT_QUEUE_SIZE = 256


@dataclass
class _Subscriber:
    zone_id: str | None
    queue: asyncio.Queue
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
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def publish(self, record: dict[str, Any]) -> int:
        """Fan out a single record to every interested subscriber.

        Returns the number of subscribers that actually received the
        record (excludes those whose zone filter did not match).
        """
        delivered = 0
        async with self._lock:
            targets = list(self._subscribers)
        zone_id = record.get("zone_id")
        for subscriber in targets:
            if subscriber.zone_id is not None and subscriber.zone_id != zone_id:
                continue
            try:
                subscriber.queue.put_nowait(record)
                delivered += 1
            except asyncio.QueueFull:
                with contextlib.suppress(asyncio.QueueEmpty):
                    subscriber.queue.get_nowait()
                with contextlib.suppress(asyncio.QueueFull):
                    subscriber.queue.put_nowait(record)
                subscriber.dropped += 1
                delivered += 1
        return delivered

    def publish_nowait(self, record: dict[str, Any]) -> int:
        """Synchronous publish for callers running outside an event loop.

        Used by the sensor-ingestor writer when invoked from a sync
        runtime. Internally schedules the publish on the running loop if
        one exists, otherwise falls back to a fresh loop call.
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop is not None and loop.is_running():
            asyncio.run_coroutine_threadsafe(self.publish(record), loop)
            return 0
        try:
            return asyncio.run(self.publish(record))
        except RuntimeError:
            return 0

    @contextlib.asynccontextmanager
    async def subscribe(self, *, zone_id: str | None = None) -> AsyncIterator[asyncio.Queue]:
        subscriber = _Subscriber(zone_id=zone_id, queue=asyncio.Queue(maxsize=self.max_queue))
        async with self._lock:
            self._subscribers.append(subscriber)
        try:
            yield subscriber.queue
        finally:
            async with self._lock:
                if subscriber in self._subscribers:
                    self._subscribers.remove(subscriber)

    async def subscriber_count(self) -> int:
        async with self._lock:
            return len(self._subscribers)

    def subscriber_count_sync(self) -> int:
        return len(self._subscribers)
