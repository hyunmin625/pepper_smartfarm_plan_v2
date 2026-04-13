# Runtime Integration Status

## 목적

`state-estimator -> llm-orchestrator -> policy/output validator -> ops-api -> execution-gateway`를 실제 동작 가능한 단일 경로로 연결한 현재 상태를 정리한다.

## 이번에 연결된 범위

### 1. LLM orchestrator 본연결

- `llm-orchestrator/llm_orchestrator/client.py`
  - `stub` / `openai` provider 지원
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
  - stub / openai provider 공통 진입점

### 2. state-estimator feature engineering

- `state-estimator/state_estimator/features.py`
  - VPD
  - DLI
  - 5분 평균
  - 30분 변화율
  - 관수 후 회복률
  - 배액률
  - rootzone/climate/crop risk score
  - automation/sensor reliability score
- `state-estimator/state_estimator/estimator.py`
  - `sensor_quality bad -> unknown`
  - `worker/manual_override/safe_mode/estop -> critical`
  - zone-state payload 조합

### 3. Backend + Database

- `ops-api/ops_api/app.py`
  - `POST /decisions/evaluate-zone`
  - `GET /decisions`
  - `GET /zones/{zone_id}/state`
  - `POST /actions/approve`
  - `POST /actions/reject`
  - `POST /shadow/reviews`
  - `GET /shadow/reviews`
  - `GET /actions/history`
  - `GET/POST /runtime/mode`
  - `GET /dashboard`
  - `GET /dashboard/data`
  - `GET /alerts`
  - `GET /robot/tasks`
- `ops-api/ops_api/models.py`
  - `decisions`
  - `approvals`
  - `device_commands`
  - `policy_evaluations`
  - `operator_reviews`
- `infra/postgres/001_initial_schema.sql`
  - PostgreSQL DDL

### 4. Approval UI

- `ops-api/ops_api/app.py`의 `/dashboard`
  - zone overview 카드
  - decision log 표시
  - citations / validator reason 표시
  - alert / robot task / execution history 패널
  - runtime mode toggle
  - shadow agree / disagree 버튼
  - approve / reject 버튼
  - note prompt 기반 운영 메모

### 5. Shadow -> Approval Mode 경로

- runtime mode 저장: `artifacts/runtime/ops_api/runtime_mode.json`
- shadow mode: decision 생성과 저장만 수행
- shadow review: 운영자가 AI 추천과 실제 판단의 일치/불일치를 기록
- approval mode: 승인된 action만 planner를 거쳐 `execution-gateway`로 전달
- 현재 dispatch backend는 `mock PLC adapter`

## 로컬 검증 명령

```bash
python3 scripts/validate_state_estimator_mvp.py
python3 scripts/validate_state_estimator_features.py
python3 scripts/validate_llm_orchestrator_service.py
python3 scripts/validate_llm_response_parser.py
python3 scripts/validate_ops_api_flow.py
python3 scripts/run_llm_orchestrator_smoke.py --provider stub --model-id champion
python3 -m py_compile state-estimator/state_estimator/*.py llm-orchestrator/llm_orchestrator/*.py ops-api/ops_api/*.py
```

## 현재 한계

- OpenAI 실호출 경로와 smoke script는 구현했지만, 이 환경에서는 실제 네트워크 호출 검증을 하지 않았다.
- `ops-api`는 로컬 검증에서 SQLite를 쓰고, 운영 전환용 PostgreSQL은 DDL까지만 준비했다.
- auth / role / policy management 전용 화면, real sensor 시계열 차트는 아직 미구현이다.
- approval mode의 실제 장치 실행은 현재 `mock` adapter 기준이다.

## 다음 우선순위

1. `OPS_API_LLM_PROVIDER=openai`, `OPS_API_MODEL_ID=champion` 기준 online smoke 실행
2. sensor-ingestor snapshot을 state-estimator raw loader에 직접 연결
3. approval mode dispatch 결과를 shadow window/report와 한 화면에서 묶기
4. auth / role / alert endpoint 추가
