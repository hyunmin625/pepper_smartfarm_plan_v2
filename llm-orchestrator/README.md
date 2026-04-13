# llm-orchestrator

RAG 검색과 structured output 생성을 담당하는 상위 판단 서비스다.

## 현재 구현 범위

- `llm_orchestrator/client.py`
  - `stub` / `openai` provider
  - retry / timeout / repair prompt
- `llm_orchestrator/retriever.py`
  - `data/rag/*.jsonl` 기반 local retriever
- `llm_orchestrator/response_parser.py`
  - malformed JSON recovery
  - safe fallback JSON
- `llm_orchestrator/service.py`
  - prompt version 선택
  - retrieved_context 자동 주입
  - citations 보강
  - output validator 연결
- `llm_orchestrator/runtime.py`
  - `LLM output -> output validator -> audit log`
  - shadow mode audit row 기록

## 검증 명령

```bash
python3 scripts/validate_llm_orchestrator_service.py
python3 scripts/validate_llm_output_validator_runtime.py
python3 scripts/validate_shadow_mode_runtime.py
```

## 연관 경로

- shadow mode 요약: `scripts/build_shadow_mode_report.py`
- 실제 운영 전환용 capture: `scripts/run_shadow_mode_capture_cases.py`
- rolling window 집계: `scripts/build_shadow_mode_window_report.py`
