# ops-api

FastAPI 기반 운영 백엔드다.

- `ops_api/app.py`: `POST /decisions/evaluate-zone`, `POST /actions/approve`, `GET /dashboard` 포함
- `ops_api/models.py`: `decisions`, `approvals`, `device_commands` 저장 모델
- `ops_api/planner.py`: 승인된 action을 `execution-gateway` 요청으로 변환
- 기본 검증 환경은 `SQLite + mock PLC adapter`
- 운영 전환용 PostgreSQL DDL은 [infra/postgres/001_initial_schema.sql](/home/user/pepper-smartfarm-plan-v2/infra/postgres/001_initial_schema.sql:1)에 둔다.
