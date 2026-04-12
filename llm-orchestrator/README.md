# llm-orchestrator

RAG 검색과 structured output 생성을 담당하는 상위 판단 서비스 자리다.

- `llm_orchestrator/runtime.py`는 `LLM output -> output validator -> audit log`와 `shadow mode audit row`까지 기록하는 최소 runtime skeleton을 제공한다.
- shadow mode 요약은 `scripts/build_shadow_mode_report.py`로 집계한다.
