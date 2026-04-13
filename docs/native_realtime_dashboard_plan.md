# Native Realtime Dashboard Plan (SSE + uPlot + TimescaleDB)

이 문서는 **`docs/timeseries_storage_dashboard_plan.md`의 Grafana 임베드 결정과 `docs/grafana_integration_design.md`를 supersede**한다. 이전 결정이 무효라는 뜻이 아니라, 운영자 통합관제 웹 `/dashboard`의 시계열 시각화 레이어를 **Grafana 임베드가 아닌 native SSE + uPlot 경로**로 다시 고정한다는 뜻이다. TimescaleDB 저장 결정과 `docs/timescaledb_schema_design.md`는 그대로 유효하다.

## 1. supersede 이유

운영 요구사항이 **초단위(≤ 1초) 실시간**으로 명확히 정리됐다. 이 요구를 충족시키는 데 있어 기존 Grafana embed 경로에는 구조적 한계가 있다.

- Grafana 기본 dashboard refresh 최소 단위는 `5s`이며, 그 아래로 내리려면 custom plugin이 필요하다.
- Grafana Live(WebSocket streaming)는 `loki`/`prometheus` 등 일부 datasource에서만 동작하고, **PostgreSQL/TimescaleDB datasource plugin은 streaming push를 지원하지 않는다**. SQL polling만 가능하다.
- iframe 임베드는 모바일 터치 제스처(확대/스크롤)와 iFarm 한국어/크림 팔레트와 충돌이 잦고, 운영자 1~3명 규모에는 과한 추가 서비스 비용이다.
- 우리 운영자 UI는 이미 SSE/WebSocket을 받아 그릴 수 있는 단일 SPA(`ops-api/_dashboard_html`)를 보유하고 있고, TimescaleDB가 같은 Postgres 클러스터 안에 있어 SSE 백엔드 구현이 단순하다.

따라서 시각화 레이어는 **Grafana를 빼고 native 경로**로 가는 것이 요구사항·디자인 일관성·구현 비용 모두에서 더 유리하다.

## 2. 데이터 볼륨 점검

요구사항 기반 규모는 작다.

- zone 5개 × 지표 11개 × 1Hz = **초당 55 sample ≈ 2 KB/s**
- 100ms(10Hz)로 올려도 ≈ **20 KB/s**
- 동시 접속 운영자 3명 가정 시 ≈ **60 KB/s**

이는 SSE/WebSocket 표준 패턴으로 충분히 처리 가능한 규모이며, 추가 broker(Kafka 등)를 도입할 필요가 없다.

## 3. 목표 아키텍처

```text
[sensor-ingestor]
  ├─ (a) TimescaleDB raw insert  (sensor_readings hypertable, 영구 저장)
  └─ (b) in-process pubsub broadcast  (asyncio.Queue or Redis pubsub)

[ops-api]
  ├─ GET /zones/{zone_id}/history?metric=...&interval=1m
  │     - 기존 유지. 초기 로드/fallback용.
  ├─ GET /zones/{zone_id}/timeseries?from=...&to=...&interval=1m|5m|raw
  │     - 신규. 임의 구간 조회. zone_state_snapshots / zone_metric_5m / sensor_readings 자동 선택.
  └─ GET /zones/{zone_id}/stream  (Server-Sent Events)
        - 신규. 연결 시 최근 N초 bootstrap 후, sensor-ingestor pubsub에서 들어오는 신규 reading을 그대로 push.

[browser /dashboard]
  - EventSource('/zones/gh-01-zone-a/stream')
  - uPlot.appendData({x: ts, y: value}) per metric
  - 60s / 5m / 30m / 6h / 24h rolling window 선택
  - 자동 재연결 + 백오프
```

## 4. 컴포넌트 결정

### 저장
- **TimescaleDB** (`docs/timescaledb_schema_design.md` 그대로 유지)
- raw `sensor_readings` + `zone_state_snapshots` + `zone_metric_5m` + `zone_metric_30m`

### 백엔드 push
- **FastAPI `StreamingResponse` + Server-Sent Events**
- 단일 ops-api 워커 환경에서는 `asyncio.Queue` broadcast로 충분
- 다중 워커로 확장 시 Redis pubsub으로 1시간 내 교체 가능

### 프론트 차트
- **uPlot** (MIT, ~50 KB gzipped, 의존성 0, canvas 기반 60fps)
- 대안: Chart.js + chartjs-plugin-streaming, ApexCharts. 모두 MIT.
- 기본은 uPlot 1순위, fallback으로 Chart.js streaming 호환 유지.

### 인증
- 기존 ops-api `viewer/operator/service/admin` 역할 그대로 사용.
- SSE 엔드포인트는 최소 `read_runtime` 권한 요구.
- 추가 SSO/Grafana auth proxy 불필요.

## 5. 구현 단계

1. **TimescaleDB migration** — `infra/postgres/002_timescaledb_sensor_readings.sql` 신설. extension + hypertable + index + retention/compression policy. ORM 모델은 read-only로 정의 (insert는 sensor-ingestor 책임).
2. **sensor-ingestor writer + pubsub** — adapter 출력을 `sensor_readings`에 insert + asyncio.Queue로 broadcast. 단일 프로세스 모드 우선.
3. **ops-api SSE 엔드포인트** — `GET /zones/{id}/stream` (`read_runtime` 권한). bootstrap 5분치 + 신규 reading streaming. 연결당 client_id 발급, disconnect 시 정리.
4. **ops-api `/zones/{id}/timeseries` 임의 구간 엔드포인트** — interval에 따라 raw/5m/30m hypertable 자동 선택.
5. **iFarm 대시보드 uPlot 통합** — `존 모니터링` 뷰 11개 SVG 스파크라인을 uPlot 인스턴스로 교체. rolling window 60s/5m/30m/6h/24h selector 추가. EventSource 자동 재연결 + reconnect-on-error.
6. **회귀 smoke** — `scripts/validate_ops_api_sse_stream.py` (TestClient async generator → 이벤트 시퀀스 검증), `scripts/validate_ops_api_timeseries.py` (interval별 hypertable 라우팅), 기존 `validate_ops_api_zone_history`는 fallback 경로로 유지.

## 6. 닫히는 항목과 다시 여는 항목

### 닫힘
- "Grafana embed 임베드 방식" 결정 (`grafana_integration_design.md`의 4·5·7·8장)
- "TimescaleDB datasource provisioning"
- "초단위 실시간을 위한 visualizer 선택"

### 보존(아카이브)
- `docs/timeseries_storage_dashboard_plan.md`의 1·2·3·4·6장(저장소 결정과 데이터 계층 기준)은 유효
- 과거 Grafana 임베드 문서는 업스트림 정리 커밋 `914c8ee`에서 삭제됐다. 향후 엔지니어 전용 ad-hoc 분석 도구가 다시 필요해지면 동일 TimescaleDB를 datasource로 새 설계를 연다.

### 새로 여는 항목
- 14.5 (or 14.4 아래) "native realtime sensor stream" 작업: `/stream` 엔드포인트, sensor-ingestor pubsub, uPlot 통합, SSE smoke

## 7. 트레이드오프

- **포기**: Grafana의 panel 마켓플레이스, threshold/annotation/alert 빌더, 운영자 GUI 대시보드 편집.
- **확보**: 초단위 streaming, 모바일 반응성, iFarm 디자인 일관성, 단일 origin/단일 인증, 추가 서비스 0개, Tailwind 크림 팔레트와 충돌 없음.
- 운영자가 GUI에서 직접 dashboard를 편집하는 능력은 잃지만, 이 프로젝트의 운영자(농가 1~3명) 운영 모델에서는 관리자 개입 없이 dashboard 구조를 바꾸는 시나리오가 거의 없다. 필요해지는 시점에 별도 서브도메인(`analytics.ifarm.local`)에 Grafana를 그대로 띄울 수 있도록 `infra/grafana/`는 보존한다.

## 8. 연결 문서

- `docs/timescaledb_schema_design.md` — 시계열 스토리지 (유효, 유지)
- `docs/timeseries_storage_dashboard_plan.md` — 저장 결정 (유효), Grafana 임베드 부분만 본 문서로 supersede
- `docs/timescaledb_schema_design.md` — raw/snapshot/downsampling/compression DDL 기준
