# ops-api

FastAPI 기반 운영 백엔드다.

- `ops_api/app.py`: `POST /decisions/evaluate-zone`, `GET /zones`, `GET /zones/{zone_id}/history`, `GET /sensors`, `GET /devices`, `GET /policies`, `GET /policies/events`, `POST /policies/{policy_id}`, `POST /actions/approve`, `POST /actions/execute`, `POST /shadow/reviews`, `POST /shadow/cases/capture`, `GET /shadow/window`, `GET /dashboard`, `GET /dashboard/data`, `GET /alerts`, `GET /robot/tasks`, `POST /robot/tasks` 포함
- `ops_api/auth.py`: `viewer/operator/service/admin` 역할과 `disabled/header_token` 인증 모드 정의
- `ops_api/models.py`: `zones`, `sensors`, `devices`, `policies`, `decisions`, `approvals`, `device_commands`, `policy_events`, `alerts`, `robot_candidates`, `robot_tasks`, `policy_evaluations`, `operator_reviews` 저장 모델
- `ops_api/shadow_mode.py`: shadow audit JSONL 적재/summary 계산 helper
- `ops_api/planner.py`: 승인된 action을 `execution-gateway` 요청으로 변환
- `ops_api/seed.py`: sensor/device/policy seed JSON을 reference catalog로 적재
- `ops_api/logging.py`, `ops_api/errors.py`: logger와 공통 예외 응답 경로
- 기본 검증 환경은 `SQLite + mock PLC adapter`
- 운영 전환용 PostgreSQL/TimescaleDB DDL은 [infra/postgres/001_initial_schema.sql](/home/user/pepper-smartfarm-plan-v2/infra/postgres/001_initial_schema.sql:1), [infra/postgres/002_timescaledb_sensor_readings.sql](/home/user/pepper-smartfarm-plan-v2/infra/postgres/002_timescaledb_sensor_readings.sql:1)에 둔다.

## bootstrap

```bash
python3 scripts/apply_ops_api_migrations.py
```

운영용 PostgreSQL에서는 `infra/postgres/001_initial_schema.sql` → `002_timescaledb_sensor_readings.sql` 순서로 canonical migration을 적용한다. SQLite 개발 환경은 기존처럼 SQLAlchemy `create_all` 경로를 사용한다.

```bash
python3 scripts/bootstrap_ops_api_reference_data.py
```

현재 `OPS_API_DATABASE_URL` 대상 DB에 schema를 만든 뒤 기본 `zones/sensors/devices/policies` reference catalog를 seed한다. PostgreSQL이면 SQL migration을 먼저 적용하고, SQLite면 `create_all` fallback을 사용한다.

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
python3 scripts/validate_ops_api_auth.py
python3 scripts/validate_ops_api_schema_models.py
python3 scripts/validate_ops_api_error_responses.py
python3 scripts/validate_ops_api_flow.py
python3 scripts/validate_ops_api_load_scenario.py
python3 scripts/validate_ops_api_shadow_mode.py
python3 scripts/validate_ops_api_server_smoke.py
python3 scripts/validate_ops_api_postgres_smoke.py
```

- `validate_ops_api_server_smoke.py`는 실제 `uvicorn`을 띄운 뒤 localhost HTTP 경로를 점검한다.
  - 현재 smoke 범위: `GET /auth/me`, `GET/POST /runtime/mode`, `GET /policies`, `GET /policies/events`, `POST /policies/{policy_id}`, `POST /decisions/evaluate-zone`, `POST /actions/approve`, `GET /dashboard/data`
- `validate_ops_api_flow.py`는 SQLite 기준으로 `blocked / approval_required` policy event가 approval dispatch 경로에서 실제 적재되는지까지 검증한다.
- `validate_ops_api_postgres_smoke.py`는 `OPS_API_POSTGRES_SMOKE_URL` 또는 `OPS_API_DATABASE_URL`가 PostgreSQL URL이고 driver(`psycopg`/`psycopg2`)가 설치돼 있을 때만 실제 smoke를 수행한다. 환경이 없으면 `blocked` 상태로 종료한다.
