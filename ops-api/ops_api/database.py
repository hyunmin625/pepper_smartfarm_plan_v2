from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .bootstrap import REPO_ROOT


class Base(DeclarativeBase):
    pass


MIGRATION_PATHS: tuple[Path, ...] = (
    REPO_ROOT / "infra" / "postgres" / "001_initial_schema.sql",
    REPO_ROOT / "infra" / "postgres" / "002_timescaledb_sensor_readings.sql",
    REPO_ROOT / "infra" / "postgres" / "003_automation_rules.sql",
    REPO_ROOT / "infra" / "postgres" / "004_automation_trigger_review.sql",
    REPO_ROOT / "infra" / "postgres" / "005_automation_dispatch_status.sql",
    REPO_ROOT / "infra" / "postgres" / "006_policy_event_policy_links.sql",
)


def build_engine(database_url: str):
    normalized = database_url.strip()
    if not (
        normalized.startswith("postgresql://") or normalized.startswith("postgresql+")
    ):
        raise RuntimeError(
            "ops-api runtime requires PostgreSQL/TimescaleDB. SQLite is no longer allowed."
        )
    return create_engine(database_url)


def build_session_factory(database_url: str) -> sessionmaker[Session]:
    engine = build_engine(database_url)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def _split_sql_statements(sql_text: str) -> list[str]:
    statements: list[str] = []
    buffer: list[str] = []
    in_single_quote = False
    index = 0
    length = len(sql_text)

    while index < length:
        char = sql_text[index]
        if char == "'" and (index == 0 or sql_text[index - 1] != "\\"):
            in_single_quote = not in_single_quote
            buffer.append(char)
            index += 1
            continue
        if char == ";" and not in_single_quote:
            statement = "".join(buffer).strip()
            if statement:
                statements.append(statement)
            buffer = []
            index += 1
            continue
        buffer.append(char)
        index += 1

    tail = "".join(buffer).strip()
    if tail:
        statements.append(tail)
    return statements


def _has_executable_sql(statement: str) -> bool:
    stripped_lines = []
    for line in statement.splitlines():
        candidate = line.strip()
        if not candidate or candidate.startswith("--"):
            continue
        stripped_lines.append(candidate)
    return bool(stripped_lines)


def apply_postgres_migrations(engine: Engine) -> list[str]:
    applied_paths: list[str] = []
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
        for path in MIGRATION_PATHS:
            sql_text = path.read_text(encoding="utf-8")
            for statement in _split_sql_statements(sql_text):
                if not _has_executable_sql(statement):
                    continue
                connection.exec_driver_sql(statement)
            applied_paths.append(str(path.relative_to(REPO_ROOT)))
    return applied_paths


def init_db(session_factory: sessionmaker[Session]) -> None:
    session = session_factory()
    engine = session.get_bind()
    session.close()
    if engine.dialect.name != "postgresql":
        raise RuntimeError(
            "ops-api init_db requires PostgreSQL/TimescaleDB. SQLite is no longer allowed."
        )
    apply_postgres_migrations(engine)


@contextmanager
def session_scope(session_factory: sessionmaker[Session]):
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
