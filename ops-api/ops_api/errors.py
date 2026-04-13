from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse


logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        detail = exc.detail
        if isinstance(detail, dict) and "error" in detail:
            content = detail
        else:
            content = {
                "error": {
                    "code": f"http_{exc.status_code}",
                    "message": str(detail),
                }
            }
        logger.warning("ops-api http error path=%s status=%s detail=%s", request.url.path, exc.status_code, detail)
        return JSONResponse(status_code=exc.status_code, content=content)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled ops-api error path=%s", request.url.path, exc_info=exc)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "internal_error",
                    "message": "internal server error",
                }
            },
        )
