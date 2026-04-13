#!/usr/bin/env python3
"""Apply ops-api PostgreSQL migrations in canonical order."""

from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "ops-api"))

from ops_api.config import load_settings  # noqa: E402
from ops_api.database import apply_postgres_migrations, build_engine  # noqa: E402


def main() -> int:
    settings = load_settings()
    engine = build_engine(settings.database_url)
    if engine.dialect.name != "postgresql":
        print(
            json.dumps(
                {
                    "status": "blocked",
                    "reason": "OPS_API_DATABASE_URL is not a PostgreSQL URL",
                    "database_url": settings.database_url,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    applied_paths = apply_postgres_migrations(engine)
    print(
        json.dumps(
            {
                "status": "ok",
                "database_url": settings.database_url,
                "applied_migrations": applied_paths,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
