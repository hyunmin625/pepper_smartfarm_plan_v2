# ops-api

FastAPI 기반 운영 백엔드다.

- `ops_api/app.py`: `POST /decisions/evaluate-zone`, `GET /zones`, `GET /zones/{zone_id}/history`, `GET /sensors`, `GET /devices`, `GET /policies`, `POST /actions/approve`, `POST /actions/execute`, `POST /shadow/reviews`, `GET /dashboard`, `GET /dashboard/data`, `GET /alerts`, `GET /robot/tasks`, `POST /robot/tasks` 포함
- `ops_api/models.py`: `zones`, `sensors`, `devices`, `policies`, `decisions`, `approvals`, `device_commands`, `alerts`, `robot_candidates`, `robot_tasks`, `policy_evaluations`, `operator_reviews` 저장 모델
- `ops_api/planner.py`: 승인된 action을 `execution-gateway` 요청으로 변환
- `ops_api/seed.py`: sensor/device/policy seed JSON을 reference catalog로 적재
- `ops_api/logging.py`, `ops_api/errors.py`: logger와 공통 예외 응답 경로
- 기본 검증 환경은 `SQLite + mock PLC adapter`
- 운영 전환용 PostgreSQL DDL은 [infra/postgres/001_initial_schema.sql](/home/user/pepper-smartfarm-plan-v2/infra/postgres/001_initial_schema.sql:1)에 둔다.

## bootstrap

```bash
python3 scripts/bootstrap_ops_api_reference_data.py
```

현재 `OPS_API_DATABASE_URL` 대상 DB에 schema를 만들고 기본 `zones/sensors/devices/policies` reference catalog를 seed한다.
