#!/usr/bin/env python3
"""Ensure the ops-api PostgreSQL database exists before migrations run."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, make_url


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "ops-api"))

from ops_api.config import load_settings  # noqa: E402


def _quote_identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def _build_admin_url(database_url: str) -> tuple[URL, str]:
    url = make_url(database_url)
    if not url.drivername.startswith("postgresql"):
        raise RuntimeError(
            "OPS_API_DATABASE_URL must point to PostgreSQL/TimescaleDB. "
            "SQLite runtime is no longer allowed."
        )
    if not url.database:
        raise RuntimeError("OPS_API_DATABASE_URL must include a database name.")

    admin_database = "postgres" if url.database != "postgres" else "template1"
    return url.set(database=admin_database), url.database


def main() -> int:
    settings = load_settings()
    admin_url, target_database = _build_admin_url(settings.database_url)
    engine = create_engine(admin_url)

    created = False
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
        exists = (
            connection.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :database_name"),
                {"database_name": target_database},
            ).scalar_one_or_none()
            is not None
        )
        if not exists:
            connection.exec_driver_sql(f"CREATE DATABASE {_quote_identifier(target_database)}")
            created = True

    print(
        json.dumps(
            {
                "status": "ok",
                "admin_database": admin_url.database,
                "target_database": target_database,
                "created": created,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
