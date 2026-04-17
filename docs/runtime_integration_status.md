# Runtime Integration Status

## 목적

`state-estimator -> llm-orchestrator -> policy/output validator -> ops-api -> execution-gateway`를 실제 동작 가능한 단일 경로로 연결한 현재 상태를 정리한다.

## 이번에 연결된 범위

### 1. LLM orchestrator 본연결

- `llm-orchestrator/llm_orchestrator/client.py`
  - `stub` / `openai` / `gemini` provider 지원
  - retry / timeout / repair prompt 경로 포함
  - model alias -> resolved FT model id 해석
- `llm-orchestrator/llm_orchestrator/retriever.py`
  - `data/rag/*.jsonl` 기반 local keyword retriever
- `llm-orchestrator/llm_orchestrator/response_parser.py`
  - strict JSON parse
  - markdown fence 제거
  - brace recovery
  - smart quote / trailing comma / prose wrapper recovery
  - 최종 safe fallback JSON
- `llm-orchestrator/llm_orchestrator/tool_registry.py`
  - runtime capability catalog 고정
- `llm-orchestrator/llm_orchestrator/model_registry.py`
  - `champion` alias로 frozen FT model id 해석
- `llm-orchestrator/llm_orchestrator/service.py`
  - prompt version 선택
  - retrieved_context 자동 주입
  - tool registry 자동 주입
  - citations 자동 보강
  - output validator 자동 연결
- `scripts/run_llm_orchestrator_smoke.py`
  - sample scenario 기준 end-to-end smoke 경로
  - stub / openai / gemini provider 공통 진입점

### 2. state-estimator feature engineering

- `state-estimator/state_estimator/features.py`
  - VPD
  - DLI
  - 1분 평균
  - 5분 평균
  - 10분 변화율
  - 30분 변화율
  - 관수 후 회복률
  - 배액률
  - climate/rootzone stress score
  - rootzone/climate/crop risk score
  - automation/sensor reliability score
  - raw sensor/device row -> snapshot loader
- `state-estimator/state_estimator/estimator.py`
  - `sensor_quality bad -> unknown`
  - `worker/manual_override/safe_mode/estop -> critical`
  - zone-state payload 조합

### 3. Backend + Database

- `ops-api/ops_api/app.py`
  - `POST /decisions/evaluate-zone`
  - `GET /zones`
  - `GET /zones/{zone_id}/history`
  - `GET /decisions`
  - `GET /zones/{zone_id}/state`
  - `GET /sensors`
  - `GET /devices`
  - `GET /policies`
  - `GET /policies/events`
  - `POST /policies/{policy_id}`
  - `POST /actions/approve`
  - `POST /actions/execute`
  - `POST /actions/reject`
  - `POST /shadow/reviews`
  - `GET /shadow/reviews`
  - `GET /actions/history`
  - `GET/POST /runtime/mode`
  - `GET /dashboard`
  - `GET /dashboard/data`
  - `GET /alerts`
  - `GET /robot/tasks`
  - `POST /robot/tasks`
- `ops-api/ops_api/models.py`
  - `zones`
  - `sensors`
  - `devices`
  - `policies`
  - `decisions`
  - `approvals`
  - `device_commands`
  - `policy_events`
  - `alerts`
  - `robot_candidates`
  - `robot_tasks`
  - `policy_evaluations`
  - `operator_reviews`
- `ops-api/ops_api/seed.py`
  - startup bootstrap
  - `sensor_catalog_seed`, `device_profile_registry_seed`, `device_site_override_seed`, `policy_output_validator_rules_seed` 적재
- `infra/postgres/001_initial_schema.sql`
  - PostgreSQL DDL + catalog/index

### 4. Approval UI

- `ops-api/ops_api/app.py`의 `/dashboard`
  - zone overview 카드
  - auth context 카드
  - decision log 표시
  - citations / validator reason 표시
  - policy management 패널 + enable/disable 토글
  - alert / robot task / execution history 패널
  - shadow window summary 패널
  - runtime mode toggle
  - shadow agree / disagree 버튼
  - approve / reject 버튼
  - note prompt 기반 운영 메모

### 5. Shadow -> Approval Mode 경로

- runtime mode 저장: `artifacts/runtime/ops_api/runtime_mode.json`
- shadow mode: decision 생성과 저장만 수행
- shadow review: 운영자가 AI 추천과 실제 판단의 일치/불일치를 기록
- `POST /shadow/cases/capture`, `GET /shadow/window`로 real shadow case 적재와 rolling summary 조회를 API에서 직접 수행
- approval mode: 승인된 action만 planner를 거쳐 `execution-gateway`로 전달
- `execution-gateway`는 dispatch 직전 `policy-engine/precheck`로 seed policy를 다시 평가한다. 현재 `HSV-04` path degraded block, `HSV-09` fertigation approval escalation을 실제 request/raw context 기준으로 재적용한다.
- planner는 `zone_state.current_state`, `active_constraints`, `sensor_quality`를 dispatch request raw payload로 다시 전파한다. 이 경로로 `blocked / approval_required` policy event가 `policy_events`와 dashboard summary에 실제 저장된다.
- 현재 dispatch backend는 `mock PLC adapter`

## 로컬 검증 명령

```bash
python3 scripts/validate_state_estimator_mvp.py
python3 scripts/validate_state_estimator_features.py
python3 scripts/validate_state_estimator_raw_loader.py
python3 scripts/validate_sensor_to_state_estimator_integration.py
python3 scripts/validate_llm_orchestrator_service.py
python3 scripts/validate_llm_response_parser.py
set -a
source .env
set +a
python3 scripts/ensure_ops_api_postgres_db.py
python3 scripts/apply_ops_api_migrations.py
python3 scripts/bootstrap_ops_api_reference_data.py
python3 scripts/validate_ops_api_postgres_smoke.py
python3 scripts/validate_ops_api_server_smoke.py
python3 scripts/validate_policy_engine_precheck.py
python3 scripts/validate_execution_gateway_flow.py
python3 scripts/validate_execution_dispatcher.py
python3 scripts/run_llm_orchestrator_smoke.py --provider stub --model-id champion
python3 scripts/run_llm_orchestrator_smoke.py --provider openai --model-id champion --prompt-version sft_v10
python3 -m py_compile state-estimator/state_estimator/*.py llm-orchestrator/llm_orchestrator/*.py ops-api/ops_api/*.py
```

## 현재 한계

- OpenAI online smoke는 `.env`와 네트워크가 열린 환경에서 `champion -> ds_v11` FT model alias, retrieval, strict JSON, validator 경로까지 통과했다. 다만 CI나 운영 비밀관리 경로에 얹은 상태는 아직 아니다.
- **폐기 (2026-04-17)**: Gemini frontier path (`gemini_flash_frontier -> gemini-2.5-flash` + `sft_v11_rag_frontier`) 계획 폐기. Phase A~E 실측 기준 결정 경로 부적합 확정. runtime alias와 `.env` GEMINI 설정은 제거됐다.
- `ops-api` 런타임은 이제 `PostgreSQL/TimescaleDB only`다. `SQLite` fallback은 제거했고, bootstrap과 dashboard smoke도 같은 PostgreSQL 경로를 사용한다.
- `scripts/validate_ops_api_postgres_smoke.py`는 이 환경에서 실제로 통과했다. seeded count는 `zones 5 / sensors 29 / devices 20 / policies 20`이고 decision/alert/robot_task round trip도 확인했다.
- `scripts/validate_ops_api_server_smoke.py`도 PostgreSQL URL 기준으로 실제 `uvicorn`을 띄워 HTTP 경로를 통과시킨다.
- dashboard의 auth context / policy management 패널과 policy enable/disable API는 구현됐지만, native `sensor_series` 스파크라인을 넘어서는 `TimescaleDB` 기반 real sensor 시계열 차트와 정책 편집의 세부 폼 편집 UI는 아직 없다.
- approval mode의 실제 장치 실행은 현재 `mock` adapter 기준이다.
- real shadow log 적재 경로는 열렸지만, 실제 운영 window를 충분히 누적한 상태는 아니다.

## 다음 우선순위

1. 실제 shadow case를 누적해 `GET /shadow/window` 기준 real window를 채우기
2. `policy-engine` source versioning과 정책 편집 폼 UI를 추가
3. blind50/extended200 validator residual을 줄이기
4. 실센서 cutover 이후 live sensor stream으로 `/dashboard` 운영 검증을 반복하기
