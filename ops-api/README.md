# ops-api

FastAPI 기반 운영 백엔드다.

- `ops_api/app.py`: `POST /decisions/evaluate-zone`, `GET /zones`, `GET /zones/{zone_id}/history`, `GET /sensors`, `GET /devices`, `GET /policies`, `GET /policies/events`, `POST /policies/{policy_id}`, `POST /actions/approve`, `POST /actions/execute`, `POST /shadow/reviews`, `POST /shadow/cases/capture`, `GET /shadow/window`, `GET /dashboard`, `GET /dashboard/data`, `GET /alerts`, `GET /robot/tasks`, `POST /robot/tasks` 포함
- `ops_api/auth.py`: `viewer/operator/service/admin` 역할과 `disabled/header_token` 인증 모드 정의
- `ops_api/models.py`: `zones`, `sensors`, `devices`, `policies`, `decisions`, `approvals`, `device_commands`, `policy_events`, `policy_event_policy_links`, `alerts`, `robot_candidates`, `robot_tasks`, `policy_evaluations`, `operator_reviews` 저장 모델
- `ops_api/shadow_mode.py`: shadow audit JSONL 적재/summary 계산 helper
- `ops_api/planner.py`: 승인된 action을 `execution-gateway` 요청으로 변환
- `ops_api/seed.py`: sensor/device/policy seed JSON을 reference catalog로 적재
- `ops_api/logging.py`, `ops_api/errors.py`: logger와 공통 예외 응답 경로

운영 DB는 `PostgreSQL + TimescaleDB`만 허용한다. `SQLite`는 지원하지 않는다.

## 운영 실행

가장 빠른 실행 방법은 아래 한 줄이다.

```bash
bash scripts/run_ops_api_postgres_stack.sh
```

이 스크립트는 아래 순서를 자동으로 수행한다.

1. `.env` 로드
2. `scripts/ensure_ops_api_postgres_db.py`로 대상 DB 자동 생성
3. `scripts/apply_ops_api_migrations.py`로 canonical schema 적용
4. `scripts/bootstrap_ops_api_reference_data.py`로 `zones/sensors/devices/policies` seed 적재
5. `.venv/bin/python -m uvicorn ops_api.app:create_app --factory` 실행

상세 절차는 [docs/ops_api_postgres_runbook.md](/home/user/pepper_smartfarm_plan_v2/docs/ops_api_postgres_runbook.md)에 정리한다.

## bootstrap

```bash
set -a
source .env
set +a

.venv/bin/python scripts/ensure_ops_api_postgres_db.py
.venv/bin/python scripts/apply_ops_api_migrations.py
.venv/bin/python scripts/bootstrap_ops_api_reference_data.py
```

`OPS_API_DATABASE_URL` 대상 PostgreSQL DB를 만든 뒤 canonical migration과 reference seed를 적용한다.

운영 DDL은 아래 파일들이 canonical source다.

- [infra/postgres/001_initial_schema.sql](/home/user/pepper-smartfarm-plan-v2/infra/postgres/001_initial_schema.sql:1)
- [infra/postgres/002_timescaledb_sensor_readings.sql](/home/user/pepper-smartfarm-plan-v2/infra/postgres/002_timescaledb_sensor_readings.sql:1)
- [infra/postgres/003_automation_rules.sql](/home/user/pepper-smartfarm-plan-v2/infra/postgres/003_automation_rules.sql:1)
- [infra/postgres/004_automation_trigger_review.sql](/home/user/pepper-smartfarm-plan-v2/infra/postgres/004_automation_trigger_review.sql:1)
- [infra/postgres/005_automation_dispatch_status.sql](/home/user/pepper-smartfarm-plan-v2/infra/postgres/005_automation_dispatch_status.sql:1)
- [infra/postgres/006_policy_event_policy_links.sql](/home/user/pepper-smartfarm-plan-v2/infra/postgres/006_policy_event_policy_links.sql:1)

## auth

- 기본값은 `OPS_API_AUTH_MODE=disabled`이고, 로컬 개발에서는 `X-Actor-Id`, `X-Actor-Role`만으로 동작한다.
- 운영 전환 시 `OPS_API_AUTH_MODE=header_token`으로 바꾸고 `OPS_API_AUTH_TOKENS_JSON`에 `token -> actor_id/role` 맵을 넣는다.
- 권한은 다음처럼 고정한다.
  - `viewer`: catalog/runtime read
  - `operator`: shadow review, approve/execute, robot task write
  - `service`: evaluate-zone
  - `admin`: operator 권한 + runtime mode/policy 관리

## response contract

- 성공 응답은 `{"data": ..., "meta": {...}, "actor": {...}}` 형태를 사용한다.
- 오류 응답은 `{"error": {"code": "...", "message": "..."}}` 형태를 사용한다.

## validation

```bash
set -a
source .env
set +a

.venv/bin/python scripts/validate_ops_api_postgres_smoke.py
.venv/bin/python scripts/validate_ops_api_server_smoke.py
```

- `validate_ops_api_postgres_smoke.py`
  - PostgreSQL/TimescaleDB schema bootstrap
  - reference seed count
  - decision/alert/robot_task write-read round trip
- `validate_ops_api_server_smoke.py`
  - 실제 `uvicorn` 기동
  - `GET /auth/me`
  - `GET/POST /runtime/mode`
  - `GET /policies`
  - `GET /policies/events`
  - `POST /policies/{policy_id}`
  - `POST /decisions/evaluate-zone`
  - `POST /actions/approve`
  - `GET /dashboard/data`

모든 운영 smoke는 `.venv` + PostgreSQL URL 기준으로만 수행한다.
