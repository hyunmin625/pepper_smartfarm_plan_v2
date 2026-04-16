# Ops API PostgreSQL 실행 매뉴얼

이 문서는 `통합제어시스템 Web UI`를 **실전 운영 기준과 동일한 PostgreSQL/TimescaleDB 경로**로 기동하는 절차를 정리한다.

`SQLite`는 더 이상 허용하지 않는다. `ops-api` 런타임은 `OPS_API_DATABASE_URL`이 PostgreSQL URL이 아니면 즉시 실패한다.

## 범위

- 운영 카탈로그 DB: PostgreSQL
- 센서 시계열 DB: TimescaleDB extension이 설치된 같은 PostgreSQL 인스턴스
- Web UI/백엔드: `ops-api` FastAPI + `/dashboard`
- 자동 부트스트랩: DB 생성 -> migration 적용 -> reference seed 적재 -> `uvicorn` 기동

## 사전 조건

1. PostgreSQL 16 이상이 로컬 또는 운영 서버에 설치되어 있어야 한다.
2. TimescaleDB extension이 설치되어 있어야 한다.
3. 프로젝트 가상환경 `.venv`가 준비되어 있어야 한다.
4. `.env`에 최소 아래 항목이 있어야 한다.

```env
OPS_API_DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/pepper_ops
OPS_API_LLM_PROVIDER=stub
OPS_API_MODEL_ID=pepper-ops-local-stub
OPS_API_AUTH_MODE=disabled
```

운영 토큰 인증을 쓸 경우에는 추가로 아래를 넣는다.

```env
OPS_API_AUTH_MODE=header_token
OPS_API_AUTH_TOKENS_JSON={"token-value":{"actor_id":"admin-01","role":"admin"}}
```

## 1. 데이터베이스 자동 구축 + Web 서버 실행

아래 명령 하나로 DB 생성, migration, seed, Web 서버 실행까지 처리한다.

```bash
bash scripts/run_ops_api_postgres_stack.sh
```

내부 순서는 다음과 같다.

1. `.env` 로드
2. `scripts/ensure_ops_api_postgres_db.py`로 대상 DB 자동 생성
3. `scripts/apply_ops_api_migrations.py`로 canonical schema 적용
4. `scripts/bootstrap_ops_api_reference_data.py`로 `zones/sensors/devices/policies` seed 적재
5. `.venv/bin/python -m uvicorn ops_api.app:create_app --factory` 실행

기본 접속 주소는 아래와 같다.

- API health: `http://127.0.0.1:8000/health`
- 통합제어 Web UI: `http://127.0.0.1:8000/dashboard`

포트를 바꾸려면 환경변수를 같이 준다.

```bash
OPS_API_PORT=8010 bash scripts/run_ops_api_postgres_stack.sh
```

## 2. 단계별 수동 실행

자동 스크립트를 쓰지 않을 때는 아래 순서만 허용한다.

```bash
set -a
source .env
set +a

.venv/bin/python scripts/ensure_ops_api_postgres_db.py
.venv/bin/python scripts/apply_ops_api_migrations.py
.venv/bin/python scripts/bootstrap_ops_api_reference_data.py

PYTHONPATH=ops-api:state-estimator:llm-orchestrator:execution-gateway:policy-engine:plc-adapter:sensor-ingestor \
.venv/bin/python -m uvicorn ops_api.app:create_app --factory --host 127.0.0.1 --port 8000
```

## 3. 운영 smoke 검증

실전 경로 확인은 아래 두 개만 기준으로 삼는다.

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
  - `GET /health`
  - `GET /auth/me`
  - `GET/POST /runtime/mode`
  - `GET /policies`
  - `GET /policies/events`
  - `POST /policies/{policy_id}`
  - `POST /decisions/evaluate-zone`
  - `POST /actions/approve`
  - `GET /dashboard/data`

## 4. 장애 점검 포인트

- `CREATE EXTENSION timescaledb`에서 실패하면 PostgreSQL 서버에 TimescaleDB 패키지가 설치되지 않은 것이다.
- `psycopg` 또는 `psycopg2` driver가 없으면 PostgreSQL smoke가 실패한다.
- `OPS_API_DATABASE_URL`이 비어 있거나 PostgreSQL이 아니면 런타임이 시작되지 않는다.
- system Python으로 `uvicorn`을 띄우면 dependency mismatch가 날 수 있으므로 `.venv/bin/python`만 사용한다.

## 5. 운영 원칙

- `SQLite` 기반 smoke, bootstrap, dashboard 실행은 금지다.
- 통합제어 Web UI 공유는 `/dashboard` 기준으로만 한다.
- 다른 에이전트도 이 문서와 `AGENTS.md`의 PostgreSQL-only 규칙을 따라야 한다.
