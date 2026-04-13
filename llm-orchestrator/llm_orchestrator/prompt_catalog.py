from __future__ import annotations

import importlib.util
import sys
from functools import lru_cache
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PROMPT_SOURCE = REPO_ROOT / "scripts" / "build_openai_sft_datasets.py"


@lru_cache(maxsize=1)
def load_system_prompts() -> dict[str, str]:
    spec = importlib.util.spec_from_file_location("build_openai_sft_datasets_runtime", PROMPT_SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load prompt source: {PROMPT_SOURCE}")
    module = importlib.util.module_from_spec(spec)
    script_dir = str(PROMPT_SOURCE.parent)
    added_sys_path = False
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
        added_sys_path = True
    try:
        spec.loader.exec_module(module)
    finally:
        if added_sys_path:
            try:
                sys.path.remove(script_dir)
            except ValueError:
                pass
    prompts = getattr(module, "SYSTEM_PROMPT_BY_VERSION", None)
    if not isinstance(prompts, dict):
        raise RuntimeError(f"SYSTEM_PROMPT_BY_VERSION missing in {PROMPT_SOURCE}")
    return {str(key): str(value) for key, value in prompts.items()}


def get_system_prompt(version: str) -> str:
    prompts = load_system_prompts()
    if version not in prompts:
        raise KeyError(f"unknown system prompt version: {version}")
    return prompts[version]
