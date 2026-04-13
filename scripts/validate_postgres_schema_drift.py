#!/usr/bin/env python3
"""Detect drift between infra/postgres/001_initial_schema.sql and the ORM.

Both paths create ops-api database schemas:

- ``init_db()`` calls ``Base.metadata.create_all`` which stamps tables
  derived from SQLAlchemy ``Mapped[...]`` declarations.
- ``psql -f infra/postgres/001_initial_schema.sql`` applies the hand
  written migration.

When the two disagree on a column's type or nullability the test
environment (sqlite + create_all) silently disagrees with production
(postgres + migration). This smoke parses the migration file and
compares every (table, column) pair against the live SQLAlchemy
metadata. Any difference produces a failure so the gap is caught in
CI rather than at production insert time.

Indexes are not compared — they are additive and easier to reason
about separately. Nullability and simple type families (text,
integer, datetime, boolean) are compared.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "ops-api"))

from sqlalchemy import Boolean, DateTime, Integer, String, Text  # noqa: E402

from ops_api.database import Base  # noqa: E402
from ops_api import models as _models  # noqa: F401,E402  - registers tables


MIGRATION_PATH = REPO_ROOT / "infra" / "postgres" / "001_initial_schema.sql"


_SQL_TYPE_NORMALIZATION = {
    "TEXT": "text",
    "VARCHAR": "text",
    "BIGSERIAL": "integer",
    "BIGINT": "integer",
    "INTEGER": "integer",
    "BOOLEAN": "boolean",
    "TIMESTAMP": "datetime",
}

_ORM_TYPE_NORMALIZATION: dict[type, str] = {
    Text: "text",
    String: "text",
    Integer: "integer",
    Boolean: "boolean",
    DateTime: "datetime",
}


_CREATE_TABLE_RE = re.compile(
    r"CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+(\w+)\s*\((.*?)\)\s*;",
    re.IGNORECASE | re.DOTALL,
)


def _split_columns(body: str) -> list[str]:
    """Split the CREATE TABLE body on top-level commas.

    Simple state machine because the body may contain nested expressions
    like ``DEFAULT (NOW() AT TIME ZONE 'UTC')``. We only split when the
    parenthesis depth returns to zero.
    """
    parts: list[str] = []
    depth = 0
    buffer: list[str] = []
    for char in body:
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        if char == "," and depth == 0:
            parts.append("".join(buffer).strip())
            buffer = []
            continue
        buffer.append(char)
    tail = "".join(buffer).strip()
    if tail:
        parts.append(tail)
    return parts


def _normalize_sql_type(raw_type: str) -> str:
    token = raw_type.split("(", 1)[0].strip().upper()
    if token.startswith("TIMESTAMP"):
        return "datetime"
    return _SQL_TYPE_NORMALIZATION.get(token, token.lower())


def _parse_column(segment: str) -> tuple[str, dict[str, Any]] | None:
    lowered = segment.lower().strip()
    if not lowered:
        return None
    if lowered.startswith(("primary key", "foreign key", "unique", "check", "constraint")):
        return None
    tokens = segment.split()
    if len(tokens) < 2:
        return None
    column_name = tokens[0].strip().lower()
    column_type = tokens[1]
    normalized_type = _normalize_sql_type(column_type)
    nullable = " not null" not in segment.lower()
    return column_name, {"type": normalized_type, "nullable": nullable}


def parse_sql_schema(path: Path) -> dict[str, dict[str, dict[str, Any]]]:
    text = path.read_text(encoding="utf-8")
    tables: dict[str, dict[str, dict[str, Any]]] = {}
    for match in _CREATE_TABLE_RE.finditer(text):
        table_name = match.group(1).lower()
        body = match.group(2)
        columns: dict[str, dict[str, Any]] = {}
        for segment in _split_columns(body):
            parsed = _parse_column(segment)
            if parsed is None:
                continue
            column_name, details = parsed
            columns[column_name] = details
        tables[table_name] = columns
    return tables


def _normalize_orm_type(column) -> str:
    column_type = column.type
    type_cls = type(column_type)
    for base, label in _ORM_TYPE_NORMALIZATION.items():
        if issubclass(type_cls, base):
            return label
    return type_cls.__name__.lower()


def collect_orm_schema() -> dict[str, dict[str, dict[str, Any]]]:
    tables: dict[str, dict[str, dict[str, Any]]] = {}
    for table in Base.metadata.tables.values():
        columns: dict[str, dict[str, Any]] = {}
        for column in table.columns:
            columns[column.name.lower()] = {
                "type": _normalize_orm_type(column),
                "nullable": bool(column.nullable),
            }
        tables[table.name.lower()] = columns
    return tables


def _compare_schemas(
    sql_tables: dict[str, dict[str, dict[str, Any]]],
    orm_tables: dict[str, dict[str, dict[str, Any]]],
) -> list[str]:
    errors: list[str] = []

    sql_only = sorted(set(sql_tables) - set(orm_tables))
    orm_only = sorted(set(orm_tables) - set(sql_tables))
    for table_name in sql_only:
        errors.append(f"table {table_name} exists in SQL migration but not in ORM")
    for table_name in orm_only:
        errors.append(f"table {table_name} exists in ORM but not in SQL migration")

    for table_name in sorted(set(sql_tables) & set(orm_tables)):
        sql_columns = sql_tables[table_name]
        orm_columns = orm_tables[table_name]
        sql_col_only = sorted(set(sql_columns) - set(orm_columns))
        orm_col_only = sorted(set(orm_columns) - set(sql_columns))
        for column_name in sql_col_only:
            errors.append(
                f"{table_name}.{column_name} exists in SQL but not ORM"
            )
        for column_name in orm_col_only:
            errors.append(
                f"{table_name}.{column_name} exists in ORM but not SQL"
            )
        for column_name in sorted(set(sql_columns) & set(orm_columns)):
            sql_details = sql_columns[column_name]
            orm_details = orm_columns[column_name]
            if sql_details["type"] != orm_details["type"]:
                errors.append(
                    f"{table_name}.{column_name} type drift: "
                    f"sql={sql_details['type']} orm={orm_details['type']}"
                )
            # Primary keys are NOT NULL in both worlds even if the ORM
            # marks them as nullable=None; skip the nullability check
            # when either side reports null as ``False`` against a
            # primary-key column named ``id``.
            if column_name == "id":
                continue
            if sql_details["nullable"] != orm_details["nullable"]:
                errors.append(
                    f"{table_name}.{column_name} nullability drift: "
                    f"sql={sql_details['nullable']} orm={orm_details['nullable']}"
                )
    return errors


def main() -> int:
    sql_tables = parse_sql_schema(MIGRATION_PATH)
    orm_tables = collect_orm_schema()
    errors = _compare_schemas(sql_tables, orm_tables)

    print(
        json.dumps(
            {
                "errors": errors,
                "status": "ok" if not errors else "failed",
                "sql_table_count": len(sql_tables),
                "orm_table_count": len(orm_tables),
                "compared_tables": sorted(set(sql_tables) & set(orm_tables)),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
