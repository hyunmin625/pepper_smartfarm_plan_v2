#!/usr/bin/env python3
"""Initialize ops-api schema and reference catalog rows."""

from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "ops-api"))

from ops_api.config import load_settings  # noqa: E402
from ops_api.database import build_session_factory, init_db  # noqa: E402
from ops_api.models import DeviceRecord, PolicyRecord, SensorRecord, ZoneRecord  # noqa: E402
from ops_api.seed import bootstrap_reference_data  # noqa: E402


def main() -> int:
    settings = load_settings()
    session_factory = build_session_factory(settings.database_url)
    init_db(session_factory)
    bootstrap_reference_data(session_factory)
    session = session_factory()
    try:
        print(
            json.dumps(
                {
                    "database_url": settings.database_url,
                    "zones": session.query(ZoneRecord).count(),
                    "sensors": session.query(SensorRecord).count(),
                    "devices": session.query(DeviceRecord).count(),
                    "policies": session.query(PolicyRecord).count(),
                },
                ensure_ascii=False,
            )
        )
    finally:
        session.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
