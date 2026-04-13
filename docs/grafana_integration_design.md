# Grafana 통합 설계

이 문서는 `TimescaleDB`를 datasource로 사용하는 `Grafana`를 스마트팜 통합관제 웹 `/dashboard`에 통합하기 위한 설계 기준을 정의한다.

## 1. 역할 분리

- `Grafana`: read-only 시계열 탐색, 장기 차트, 기간 확대/축소, 다중 패널 비교
- `ops-api /dashboard`: 승인/거절/수동 실행/정책 토글/알림/로봇/운영 메모 같은 write-heavy 운영 UI
- 운영자는 단일 통합관제 웹을 사용하고, Grafana는 그 내부 시계열 패널 계층으로만 노출한다.

## 2. 배포 구조

```text
browser
-> reverse proxy
   -> /dashboard       -> ops-api
   -> /dashboard/data  -> ops-api
   -> /grafana/        -> grafana
-> TimescaleDB
```

- 기본 배포는 같은 도메인 아래 `/grafana/` subpath reverse proxy를 사용한다.
- cross-domain iframe은 지양하고 same-origin 또는 trusted subpath를 우선한다.
- Grafana는 read-only org/viewer 권한으로만 연결한다.

## 3. datasource provisioning 기준

- datasource 이름: `timescaledb-smartfarm`
- datasource type: PostgreSQL
- default DB: 운영 PostgreSQL/TimescaleDB
- 허용 schema: `public`
- time column: panel query에서 `measured_at` 또는 `bucket_start`
- 최소 연결 정보:
  - `host`
  - `port`
  - `database`
  - `user`
  - `ssl_mode`
  - `read_only_role`

## 4. 버전 관리 구조

`infra/grafana/` 아래 구조를 기준으로 버전 관리한다.

```text
infra/grafana/
  README.md
  provisioning/
    datasources/
      timescaledb.yaml
    dashboards/
      smartfarm-overview.yaml
  dashboards/
    smartfarm-overview.json
    zone-monitoring.json
```

- datasource provisioning YAML과 dashboard JSON은 저장소에 함께 커밋한다.
- dashboard 수정은 UI 수동 편집만으로 끝내지 않고 export JSON을 다시 저장소에 반영한다.
- panel UID, dashboard UID, template variable 이름은 stable identifier로 고정한다.

## 5. dashboard 구성

### 5.1 `smartfarm-overview`

- 목적: 운영자 첫 화면의 장기 추세 요약
- 주요 패널:
  - zone별 air temperature 24h
  - zone별 RH/VPD 24h
  - zone별 CO2/PAR 24h
  - irrigation event count / drain volume
  - alert 발생 시점 overlay

### 5.2 `zone-monitoring`

- 목적: 특정 zone drill-down
- 주요 패널:
  - `air_temp_c`, `rh_pct`, `vpd_kpa`
  - `substrate_moisture_pct`, `substrate_temp_c`
  - `co2_ppm`, `par_umol_m2_s`
  - `feed_ec_ds_m`, `drain_ec_ds_m`, `feed_ph`, `drain_ph`
  - `device_state` readback annotations
  - `policy_event`, `approval`, `manual_override` annotation overlay

## 6. 템플릿 변수

- `site_id`
- `zone_id`
- `from`
- `to`
- `metric_group`

기본 규칙:

- `/dashboard`에서 선택한 `site_id`, `zone_id`, time range를 Grafana panel URL에 그대로 전달한다.
- native SPA의 존 선택과 Grafana panel의 변수 값은 항상 동기화된다.

## 7. `/dashboard` embed 방식

- 기본 방식은 signed iframe 또는 Grafana panel embed URL
- 위치:
  - `대시보드` 뷰: 요약 패널 1~2개
  - `존 모니터링` 뷰: zone drill-down 패널 묶음
- fallback:
  - native SPA sparkline은 최근 window preview 용도로 유지
  - 상세 확대/비교는 Grafana panel에서 수행

## 8. 권한 / 인증

- 통합관제 웹의 canonical role은 계속 `viewer/operator/service/admin`
- Grafana는 최소 `viewer` read-only 접근만 연다
- `operator/admin`도 Grafana 안에서 write 권한은 주지 않는다
- 정책/장치 조작은 모두 `ops-api` endpoint로만 수행한다
- embedding 토큰 또는 reverse proxy 인증은 서버 측에서 처리하고 브라우저에 DB credential을 노출하지 않는다

## 9. 운영 규칙

- panel deep link는 `zone_id`, `time range`를 유지한 채 alerts/approvals 화면과 왕복 가능해야 한다
- panel query는 raw hypertable보다 `zone_state_snapshots`, `zone_metric_5m`, `zone_metric_30m`를 우선 사용한다
- raw drill-down은 장애 조사/센서 검증 용도에만 노출한다

## 10. 이번 설계로 닫히는 항목

- `TimescaleDB datasource provisioning 설계`
- `Grafana dashboard/panel JSON 버전관리 구조 설계`
- `/dashboard` 존 모니터링 뷰에 Grafana panel embed 설계
- `통합관제 role/auth와 Grafana read-only 접근 정책 정리`
