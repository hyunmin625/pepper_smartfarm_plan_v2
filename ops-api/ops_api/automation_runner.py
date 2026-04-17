"""Background automation runner.

Periodically assembles a per-zone sensor snapshot from the
``sensor_readings`` hypertable and feeds it into
:func:`ops_api.automation.evaluate_rules`. This closes the Phase O ->
Phase P gap where rules were only evaluable via the manual
``POST /automation/evaluate`` dry-run.

Design notes are in ``docs/automation_runner_design.md``.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import timedelta
from typing import TYPE_CHECKING
from sqlalchemy import desc, distinct, select
from sqlalchemy.orm import Session, sessionmaker

from .api_models import AUTOMATION_SENSOR_KEYS
from .automation import EvaluationReport, evaluate_rules
from .automation_dispatcher import DispatchSummary, dispatch_approved_triggers
from .config import Settings
from .models import AutomationRuleRecord, SensorReadingRecord, utc_now
from .runtime_mode import load_runtime_mode


if TYPE_CHECKING:  # pragma: no cover
    from execution_gateway.dispatch import ExecutionDispatcher


logger = logging.getLogger(__name__)


@dataclass
class TickResult:
    zone_id: str | None
    evaluated_rules: int
    matched_rules: int
    snapshot_keys: int
    error: str = ""
    dispatched: list[DispatchSummary] = field(default_factory=list)


class AutomationRunner:
    """Periodic evaluator that connects sensor_readings → evaluate_rules.

    The runner is intentionally stateless beyond the asyncio task handle.
    Each tick opens a fresh SQLAlchemy session, builds one sensor
    snapshot per zone that has enabled rules, and calls
    :func:`evaluate_rules` with ``persist=True`` so triggers land in
    ``automation_rule_triggers``.

    When a dispatcher is supplied (Phase Q wiring), the tick also flushes
    any ``status='approved'`` triggers that operators approved in the
    previous interval: each one is mapped to a synthetic
    :class:`DecisionRecord` and handed to
    ``ExecutionDispatcher.dispatch_device_command``. Without a dispatcher
    the runner still works — it just leaves approved triggers in place.
    """

    def __init__(
        self,
        *,
        session_factory: sessionmaker[Session],
        settings: Settings,
        dispatcher: "ExecutionDispatcher | None" = None,
    ) -> None:
        self.session_factory = session_factory
        self.settings = settings
        self.dispatcher = dispatcher
        self._task: asyncio.Task[None] | None = None
        self._stop_event: asyncio.Event | None = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    async def start(self) -> None:
        if self._task is not None:
            return
        if not self.settings.automation_enabled:
            logger.info("automation_runner disabled by settings")
            return
        if self.settings.automation_interval_sec <= 0:
            logger.info(
                "automation_runner disabled (interval_sec=%.2f)",
                self.settings.automation_interval_sec,
            )
            return
        self._stop_event = asyncio.Event()
        self._task = asyncio.create_task(self._loop(), name="automation_runner")
        logger.info(
            "automation_runner started interval=%.2fs window=%.2fs",
            self.settings.automation_interval_sec,
            self.settings.automation_snapshot_window_sec,
        )

    async def stop(self) -> None:
        if self._task is None:
            return
        assert self._stop_event is not None
        self._stop_event.set()
        self._task.cancel()
        try:
            await self._task
        except (asyncio.CancelledError, Exception):  # pragma: no cover - shutdown path
            pass
        self._task = None
        self._stop_event = None
        logger.info("automation_runner stopped")

    async def _loop(self) -> None:
        assert self._stop_event is not None
        interval = self.settings.automation_interval_sec
        while not self._stop_event.is_set():
            try:
                self.run_once()
            except Exception:  # pragma: no cover - defensive
                logger.exception("automation_runner tick failed")
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=interval)
            except asyncio.TimeoutError:
                continue

    # ------------------------------------------------------------------
    # Public test hooks
    # ------------------------------------------------------------------
    def run_once(self, *, raise_on_error: bool = False) -> list[TickResult]:
        """Execute one evaluation tick across every active zone.

        Returns a list of :class:`TickResult` so tests can assert on
        outcomes without re-reading the trigger table. Errors per zone
        are swallowed unless ``raise_on_error`` is True.
        """

        results: list[TickResult] = []
        mode_state = load_runtime_mode(self.settings.runtime_mode_path)
        session = self.session_factory()
        try:
            zones = self._discover_active_zones(session)
            for zone_id in zones:
                try:
                    snapshot = self._build_zone_snapshot(session, zone_id)
                    report: EvaluationReport = evaluate_rules(
                        session,
                        runtime_mode=mode_state.mode,
                        sensor_snapshot=snapshot,
                        zone_id=zone_id,
                        persist=True,
                    )
                    results.append(
                        TickResult(
                            zone_id=zone_id,
                            evaluated_rules=report.evaluated_rules,
                            matched_rules=report.matched_rules,
                            snapshot_keys=len(snapshot),
                        )
                    )
                except Exception as exc:
                    logger.warning(
                        "automation_runner zone_id=%s error=%s",
                        zone_id,
                        exc,
                    )
                    results.append(
                        TickResult(
                            zone_id=zone_id,
                            evaluated_rules=0,
                            matched_rules=0,
                            snapshot_keys=0,
                            error=str(exc),
                        )
                    )
                    if raise_on_error:
                        raise
            # Phase Q: flush approved triggers regardless of whether any
            # zone was discovered above. Operators may have approved
            # rows from a previous tick after the corresponding rule
            # was disabled, and we still want those to dispatch.
            dispatched = self._flush_approved(session)
            if dispatched:
                results.append(
                    TickResult(
                        zone_id=None,
                        evaluated_rules=0,
                        matched_rules=0,
                        snapshot_keys=0,
                        dispatched=dispatched,
                    )
                )
        finally:
            session.close()
        return results

    def _flush_approved(self, session: Session) -> list[DispatchSummary]:
        """Hand every ``status='approved'`` trigger to the dispatcher.

        Without a wired dispatcher the approved row stays pending, so a
        runner deployed in a test harness that doesn't need dispatch
        (e.g., smoke of evaluate_rules only) keeps working unchanged.
        """

        if self.dispatcher is None:
            return []
        try:
            return dispatch_approved_triggers(session, self.dispatcher)
        except Exception:  # pragma: no cover - defensive
            logger.exception("automation_runner approved_flush failed")
            return []

    # ------------------------------------------------------------------
    # Snapshot assembly
    # ------------------------------------------------------------------
    def _discover_active_zones(self, session: Session) -> list[str | None]:
        """Return zone ids that have at least one enabled rule.

        If a rule has ``zone_id=None`` (farm-wide), we must still evaluate
        it for every zone that appears in ``sensor_readings``. We expose
        the zone-wise set plus a sentinel ``None`` for farm-wide rules
        with no concrete zone binding (the snapshot for ``None`` is the
        most-recent reading across any zone, which is rarely useful but
        kept for symmetry with evaluate_rules zone_id=None behaviour).
        """

        scoped_zones = set(
            session.scalars(
                select(distinct(AutomationRuleRecord.zone_id))
                .where(AutomationRuleRecord.enabled == 1)
            )
        )
        # Convert None to sentinel. If None is present, expand to every
        # zone that has recent sensor_readings so farm-wide rules have a
        # chance to fire.
        include_farm_wide = None in scoped_zones
        scoped_zones.discard(None)
        if include_farm_wide:
            window = self.settings.automation_snapshot_window_sec
            cutoff = utc_now() - timedelta(seconds=window)
            discovered = set(
                session.scalars(
                    select(distinct(SensorReadingRecord.zone_id))
                    .where(SensorReadingRecord.measured_at >= cutoff)
                )
            )
            scoped_zones.update(str(z) for z in discovered if z)
        return sorted(z for z in scoped_zones if isinstance(z, str))

    def _build_zone_snapshot(
        self,
        session: Session,
        zone_id: str,
    ) -> dict[str, float]:
        """Return the latest numeric metric per key within the window.

        Only metric_names that appear in ``AUTOMATION_SENSOR_KEYS`` and
        have a non-null ``metric_value_double`` are included. Text-only
        readbacks are skipped since automation operators are numeric.
        """

        window = self.settings.automation_snapshot_window_sec
        cutoff = utc_now() - timedelta(seconds=window)
        stmt = (
            select(
                SensorReadingRecord.metric_name,
                SensorReadingRecord.metric_value_double,
                SensorReadingRecord.measured_at,
            )
            .where(SensorReadingRecord.zone_id == zone_id)
            .where(SensorReadingRecord.measured_at >= cutoff)
            .where(SensorReadingRecord.metric_value_double.is_not(None))
            .order_by(desc(SensorReadingRecord.measured_at))
        )
        latest: dict[str, float] = {}
        for metric_name, value_double, _measured_at in session.execute(stmt):
            if metric_name not in AUTOMATION_SENSOR_KEYS:
                continue
            if metric_name in latest:
                continue
            latest[metric_name] = float(value_double)
        return latest
