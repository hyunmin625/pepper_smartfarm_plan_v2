from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass(frozen=True)
class RuntimeModeState:
    mode: str
    actor_id: str
    reason: str
    updated_at: str

    def as_dict(self) -> dict[str, str]:
        return {
            "mode": self.mode,
            "actor_id": self.actor_id,
            "reason": self.reason,
            "updated_at": self.updated_at,
        }


def load_runtime_mode(path: Path) -> RuntimeModeState:
    if not path.exists():
        return RuntimeModeState(mode="shadow", actor_id="bootstrap", reason="default", updated_at=_utc_now())
    raw = json.loads(path.read_text(encoding="utf-8"))
    return RuntimeModeState(
        mode=str(raw.get("mode") or "shadow"),
        actor_id=str(raw.get("actor_id") or "unknown"),
        reason=str(raw.get("reason") or ""),
        updated_at=str(raw.get("updated_at") or _utc_now()),
    )


def save_runtime_mode(path: Path, *, mode: str, actor_id: str, reason: str) -> RuntimeModeState:
    state = RuntimeModeState(mode=mode, actor_id=actor_id, reason=reason, updated_at=_utc_now())
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state.as_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return state


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()
