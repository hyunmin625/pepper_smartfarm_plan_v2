# TimescaleDB 시계열 저장/대시보드 계획

이 문서는 스마트팜 센서 시계열 저장소와 운영 대시보드 연결 방향을 최종 결정하기 위한 기준 문서다.

## 1. 최종 결정

- canonical 시계열 저장소는 `TimescaleDB`로 고정한다.
- 공식 운영자 화면은 계속 `ops-api /dashboard` 기반 스마트팜 통합관제 웹 페이지다.
- 장기 센서 시계열, zone history drill-down, 비교 차트는 통합관제 웹 내부 기능으로 설계한다.
- 특정 외부 시각화 도구 채택 계획은 현재 열지 않는다.

## 2. 결정 이유

- 현재 시스템의 canonical 운영 데이터는 이미 PostgreSQL 스키마(`zones`, `sensors`, `devices`, `policies`, `alerts`, `approvals`, `robot_tasks`)를 기준으로 정리돼 있다.
- 센서 시계열도 같은 PostgreSQL 계열에서 관리해야 `zone_id`, `device_id`, `policy_event`, `approval`, `robot_task`와 조인되는 운영 질의를 단순하게 유지할 수 있다.
- `sensor_readings raw -> zone_state_snapshots -> trend/continuous aggregate` 구조를 `TimescaleDB hypertable + continuous aggregate + retention/compression`으로 정리하는 편이 현재 아키텍처와 가장 잘 맞는다.
- 현재 `sensor-ingestor`의 line protocol outbox는 로컬 개발용 파일 경계와 publish 추적용 형식일 뿐이며, InfluxDB 채택의 근거로 고정하지 않는다.
- 운영자 관점에서 중요한 것은 별도 도구가 아니라 통합관제 웹 안에서 상태 확인과 승인/조작 흐름이 끊기지 않는 것이다.

## 3. 목표 아키텍처

```text
sensor-ingestor
-> MQTT raw/event stream
-> TimescaleDB raw hypertable
-> zone_state_snapshots / trend continuous aggregates
-> ops-api query/view model
-> ops-api /dashboard 통합관제 웹 시계열 화면
```

- `ops-api`는 승인/실행/정책/알림/로봇/운영 메모 같은 운영 액션 UI를 계속 담당한다.
- `대시보드`와 `존 모니터링` 뷰는 TimescaleDB에서 집계한 long-range 차트와 recent window를 함께 보여준다.
- 최신 상태 카드, 승인 버튼, shadow summary, robot candidate 목록처럼 액션이 필요한 UI는 계속 native SPA 컴포넌트로 유지한다.

## 4. 데이터 계층 기준

- `sensor_readings`: raw 센서/장치 readback 시계열 canonical hypertable
- `zone_state_snapshots`: 1분 단위 존 snapshot hypertable 또는 append-only table
- `zone_state_trends`: 5분/30분 이상 집계는 Timescale continuous aggregate로 생성
- retention은 raw, snapshot, trend 계층별로 분리한다.
- downsampling은 `time_bucket` 기반 aggregate를 canonical trend source로 사용한다.
- compression은 raw historical chunk를 우선 적용하고, dashboard hot window는 uncompressed 또는 최근 chunk만 유지한다.

## 5. 대시보드 통합 원칙

- 시계열 화면은 standalone 운영 포털이 아니라 스마트팜 통합관제 웹의 일부로 취급한다.
- `/dashboard`의 `존 모니터링` 뷰는 `zone_id`, `site_id`, `time range`를 기준으로 TimescaleDB query 결과를 직접 그린다.
- 운영자는 통합관제 웹에서 zone을 고르면 최신 상태 카드와 장기 시계열 화면이 같은 컨텍스트를 공유해야 한다.
- 장기 차트는 읽기 전용 탐색에 집중하고, 승인/실행/정책 토글 같은 write action은 계속 `ops-api` 경로로만 수행한다.
- 권한은 `viewer/operator/admin` 역할 체계를 그대로 사용하고, 시계열 조회도 같은 auth 문맥 안에서 처리한다.

## 6. 구현 순서

1. `infra/postgres`에 TimescaleDB extension, hypertable, index, retention/compression 기준을 추가한다.
2. `sensor-ingestor`의 실제 timeseries writer를 TimescaleDB insert/upsert 경로로 연결한다.
3. `zone_state_snapshots`와 trend continuous aggregate를 정의한다.
4. `ops-api`에 `site_id`, `zone_id`, `time range`, metric group 기준 시계열 조회 경로를 추가한다.
5. `ops-api /dashboard`의 `존 모니터링` 뷰에 장기 시계열 카드와 drill-down 화면을 추가하고, 기존 sparkline은 preview/fallback로만 남긴다.
6. 운영 알람/정책/승인 흐름에서 필요한 deep link를 same-page chart state와 연결한다.

## 7. 이번 결정으로 닫히는 항목

- `TimescaleDB vs InfluxDB` 선택 논쟁은 종료한다.
- 새 시계열 스키마와 dashboard 설계는 `TimescaleDB + 통합관제 웹 native chart` 전제에서만 진행한다.
- 이후 문서에서 `InfluxDB`는 비교 배경이나 대안 설명 외 기본 계획으로 다시 열지 않는다.

## 8. 연결 문서

- `docs/timescaledb_schema_design.md`
