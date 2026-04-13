# Grafana Provisioning Layout

이 디렉터리는 스마트팜 통합관제 웹에 임베드할 `Grafana` datasource/dashboard provisioning 산출물을 저장하는 위치다.

예상 구조:

```text
infra/grafana/
  provisioning/
    datasources/
      timescaledb.yaml
    dashboards/
      smartfarm-overview.yaml
  dashboards/
    smartfarm-overview.json
    zone-monitoring.json
```

기준 문서:

- [Grafana 통합 설계](../../docs/grafana_integration_design.md)
- [TimescaleDB + Grafana 시계열 저장/시각화 계획](../../docs/timeseries_storage_dashboard_plan.md)
- [TimescaleDB 시계열 스키마 설계](../../docs/timescaledb_schema_design.md)

현재 단계에서는 실제 provisioning 파일보다 디렉터리 기준과 version-control 원칙을 먼저 고정한다.
