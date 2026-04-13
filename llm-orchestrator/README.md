# llm-orchestrator

RAG 검색과 structured output 생성을 담당하는 상위 판단 서비스다.

## 현재 구현 범위

- `llm_orchestrator/client.py`
  - `stub` / `openai` provider
  - retry / timeout / repair prompt
  - model alias -> resolved FT model id registry
- `llm_orchestrator/retriever.py`
  - `data/rag/*.jsonl` 기반 local retriever
- `llm_orchestrator/response_parser.py`
  - malformed JSON recovery
  - safe fallback JSON
  - smart quote / trailing comma / prose wrapper recovery
- `llm_orchestrator/tool_registry.py`
  - runtime capability catalog
  - read-only / approval / audit 도구 분리
- `llm_orchestrator/model_registry.py`
  - `champion`, `ds_v11_champion`, `ds_v14_rejected` alias 관리
- `llm_orchestrator/service.py`
  - prompt version 선택
  - retrieved_context 자동 주입
  - tool registry 자동 주입
  - citations 보강
  - output validator 연결
- `llm_orchestrator/runtime.py`
  - `LLM output -> output validator -> audit log`
  - shadow mode audit row 기록

## 검증 명령

```bash
python3 scripts/validate_llm_orchestrator_service.py
python3 scripts/validate_llm_response_parser.py
python3 scripts/validate_llm_output_validator_runtime.py
python3 scripts/validate_shadow_mode_runtime.py
python3 scripts/run_llm_orchestrator_smoke.py --provider stub --model-id champion
```

OpenAI 실연결 smoke는 아래처럼 수행한다.

```bash
export OPENAI_API_KEY='...'
python3 scripts/run_llm_orchestrator_smoke.py --provider openai --model-id champion --prompt-version sft_v5
```

## 연관 경로

- shadow mode 요약: `scripts/build_shadow_mode_report.py`
- 실제 운영 전환용 capture: `scripts/run_shadow_mode_capture_cases.py`
- rolling window 집계: `scripts/build_shadow_mode_window_report.py`
