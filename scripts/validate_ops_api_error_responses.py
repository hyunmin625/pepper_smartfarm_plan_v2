#!/usr/bin/env python3
"""Validate ops-api error envelope handlers."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from starlette.requests import Request


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "ops-api"))

from ops_api.errors import register_exception_handlers  # noqa: E402


def _build_request(path: str) -> Request:
    scope = {
        "type": "http",
        "method": "GET",
        "path": path,
        "headers": [],
        "query_string": b"",
        "scheme": "http",
        "server": ("testserver", 80),
        "client": ("127.0.0.1", 12345),
        "http_version": "1.1",
    }
    return Request(scope)


async def _decode_response(response) -> dict:
    return json.loads(response.body.decode("utf-8"))


def main() -> int:
    errors: list[str] = []
    app = FastAPI()
    register_exception_handlers(app)

    http_handler = app.exception_handlers.get(HTTPException)
    generic_handler = app.exception_handlers.get(Exception)
    if http_handler is None:
        errors.append("HTTPException handler missing")
    if generic_handler is None:
        errors.append("generic Exception handler missing")

    if errors:
        print(json.dumps({"errors": errors}, ensure_ascii=False, indent=2))
        return 1

    not_found = asyncio.run(http_handler(_build_request("/decisions/999"), HTTPException(status_code=404, detail="decision not found")))
    not_found_body = asyncio.run(_decode_response(not_found))
    if not_found.status_code != 404:
        errors.append(f"expected 404 status, got {not_found.status_code}")
    if not_found_body != {"error": {"code": "http_404", "message": "decision not found"}}:
        errors.append("404 error body mismatch")

    preserved = asyncio.run(
        http_handler(
            _build_request("/runtime/mode"),
            HTTPException(
                status_code=403,
                detail={"error": {"code": "permission_denied", "message": "blocked by role"}},
            ),
        )
    )
    preserved_body = asyncio.run(_decode_response(preserved))
    if preserved.status_code != 403:
        errors.append(f"expected 403 status, got {preserved.status_code}")
    if preserved_body != {"error": {"code": "permission_denied", "message": "blocked by role"}}:
        errors.append("custom 403 error body mismatch")

    internal = asyncio.run(generic_handler(_build_request("/internal"), RuntimeError("boom")))
    internal_body = asyncio.run(_decode_response(internal))
    if internal.status_code != 500:
        errors.append(f"expected 500 status, got {internal.status_code}")
    if internal_body != {"error": {"code": "internal_error", "message": "internal server error"}}:
        errors.append("500 error body mismatch")

    print(
        json.dumps(
            {
                "errors": errors,
                "checked_paths": ["/decisions/999", "/runtime/mode", "/internal"],
                "status_codes": {
                    "http_404": not_found.status_code,
                    "custom_403": preserved.status_code,
                    "internal_500": internal.status_code,
                },
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
