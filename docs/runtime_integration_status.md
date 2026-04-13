# Runtime Integration Status

## 목적

`state-estimator -> llm-orchestrator -> policy/output validator -> ops-api -> execution-gateway`를 실제 동작 가능한 단일 경로로 연결한 현재 상태를 정리한다.

## 이번에 연결된 범위

### 1. LLM orchestrator 본연결

- `llm-orchestrator/llm_orchestrator/client.py`
  - `stub` / `openai` provider 지원
  - retry / timeout / repair prompt 경로 포함
- `llm-orchestrator/llm_orchestrator/retriever.py`
  - `data/rag/*.jsonl` 기반 local keyword retriever
- `llm-orchestrator/llm_orchestrator/response_parser.py`
  - strict JSON parse
  - markdown fence 제거
  - brace recovery
  - 최종 safe fallback JSON
- `llm-orchestrator/llm_orchestrator/service.py`
  - prompt version 선택
  - retrieved_context 자동 주입
  - citations 자동 보강
  - output validator 자동 연결

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
  - `GET /actions/history`
  - `GET/POST /runtime/mode`
  - `GET /dashboard`
- `ops-api/ops_api/models.py`
  - `decisions`
  - `approvals`
  - `device_commands`
- `infra/postgres/001_initial_schema.sql`
  - PostgreSQL DDL

### 4. Approval UI

- `ops-api/ops_api/app.py`의 `/dashboard`
  - decision log 표시
  - citations 표시
  - runtime mode toggle
  - approve / reject 버튼

### 5. Shadow -> Approval Mode 경로

- runtime mode 저장: `artifacts/runtime/ops_api/runtime_mode.json`
- shadow mode: decision 생성과 저장만 수행
- approval mode: 승인된 action만 planner를 거쳐 `execution-gateway`로 전달
- 현재 dispatch backend는 `mock PLC adapter`

## 로컬 검증 명령

```bash
python3 scripts/validate_state_estimator_mvp.py
python3 scripts/validate_state_estimator_features.py
python3 scripts/validate_llm_orchestrator_service.py
python3 scripts/validate_ops_api_flow.py
python3 -m py_compile state-estimator/state_estimator/*.py llm-orchestrator/llm_orchestrator/*.py ops-api/ops_api/*.py
```

## 현재 한계

- OpenAI 실호출 경로는 구현했지만, 이 환경에서는 실제 네트워크 호출 검증을 하지 않았다.
- `ops-api`는 로컬 검증에서 SQLite를 쓰고, 운영 전환용 PostgreSQL은 DDL까지만 준비했다.
- auth / role / alerts / policy management / robot task endpoint는 아직 미구현이다.
- approval mode의 실제 장치 실행은 현재 `mock` adapter 기준이다.

## 다음 우선순위

1. 실제 OpenAI model id와 환경 변수로 orchestrator online smoke test
2. sensor-ingestor snapshot을 state-estimator raw loader에 직접 연결
3. approval mode dispatch 결과를 shadow window/report와 한 화면에서 묶기
4. auth / role / alert endpoint 추가
