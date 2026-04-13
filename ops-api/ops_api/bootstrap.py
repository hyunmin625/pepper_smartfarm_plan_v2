from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SERVICE_PATHS = [
    REPO_ROOT / "execution-gateway",
    REPO_ROOT / "llm-orchestrator",
    REPO_ROOT / "plc-adapter",
    REPO_ROOT / "policy-engine",
    REPO_ROOT / "sensor-ingestor",
    REPO_ROOT / "state-estimator",
]


def configure_repo_paths() -> None:
    for path in reversed(SERVICE_PATHS):
        path_str = str(path)
        if path_str not in sys.path:
            sys.path.insert(0, path_str)
