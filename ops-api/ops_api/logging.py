from __future__ import annotations

import logging


def configure_logging(level: str = "INFO") -> None:
    if getattr(configure_logging, "_configured", False):
        return
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    configure_logging._configured = True
