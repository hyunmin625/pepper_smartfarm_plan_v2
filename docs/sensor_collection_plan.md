# Sensor Collection Plan

이 문서는 적고추 온실 스마트팜의 센서 수집 계획을 `zone_id`, `sensor_id`, `device_id`, `sample_rate`, `quality_flag` 수준으로 구체화한다. 목표는 공사 완료 후 바로 `sensor-ingestor`와 상태 추정 파이프라인을 구현할 수 있도록 수집 계약을 고정하는 것이다.

## 1. 기본 원칙

- 현재 기준 site는 `gh-01`이며, 물리 시설은 `300평 연동형 비닐온실 1동`이다.
- 물리적으로는 대형 온실 1개지만, 수집/제어/평가를 위해 논리 zone으로 분리한다.
- 재배 환경 기준은 육묘용 `Grodan Delta 6.5` block, 본재배용 `Grodan GT Master` slab다.
- 원시 수집 주기와 AI 판단 주기를 분리한다.
- AI 입력에는 항상 `quality_flag`, `source`, `calibration_version`을 포함한다.
- 센서값만 저장하지 않고 같은 시점의 장치 상태와 운영 이벤트를 함께 저장한다.
- 제어 판단에 직접 쓰이는 센서는 `must_have`, 보조 판단은 `should_have`, 추후 확장은 `optional`로 구분한다.

## 2. Zone 정의

초기 계획 기준 zone은 아래처럼 둔다.

| zone_id | 설명 | 우선순위 |
|---|---|---|
| `gh-01-zone-a` | 주 재배 구역 A | must_have |
| `gh-01-zone-b` | 주 재배 구역 B | must_have |
| `gh-01-outside` | 외기 기준점 | must_have |
| `gh-01-nutrient-room` | 양액기/원수 관리실 | should_have |
| `gh-01-dry-room` | 건고추 건조·저장 공간 | should_have |

육묘 전용 zone은 현재 1차 논리 zone에 포함하지 않았지만, 육묘 단계 판단 로직과 데이터셋은 `Grodan Delta 6.5` block 환경을 기준으로 유지한다. 본재배 zone의 `substrate_moisture`, `substrate_temp`, `drain_ec_ph`, `drain_volume`는 `Grodan GT Master` slab 라인 대표 지점을 기준으로 배치한다.

## 3. Naming 규칙

- `zone_id`: `gh-<house_no>-<zone_name>`
- `sensor_id`: `<zone_id>--<sensor_type>--<index>`
- `device_id`: `<zone_id>--<device_type>--<index>`

예시:

- `gh-01-zone-a--air-temp-rh--01`
- `gh-01-zone-a--substrate-moisture--02`
- `gh-01-zone-a--circulation-fan--01`

## 4. 수집 카탈로그

| 그룹 | sensor_type | zone | unit | raw sample_rate | AI 집계 주기 | 우선순위 | 주요 quality_flag |
|---|---|---|---|---|---|---|---|
| 환경 | `air_temp_rh` | `gh-01-zone-a/b` | `degC`, `%` | 10초 | 1분 | must_have | stale, outlier, jump |
| 환경 | `co2` | `gh-01-zone-a/b` | `ppm` | 30초 | 1분 | should_have | stale, calibration_due |
| 환경 | `par` | `gh-01-zone-a/b` | `umol_m2_s` | 30초 | 1분 | must_have | flatline, outlier |
| 환경 | `solar_radiation` | `gh-01-outside` | `W_m2` | 30초 | 1분 | should_have | stale, outlier |
| 근권 | `substrate_moisture` | `gh-01-zone-a/b` | `%` | 30초 | 1분 | must_have | stale, flatline |
| 근권 | `substrate_temp` | `gh-01-zone-a/b` | `degC` | 30초 | 1분 | should_have | stale |
| 양액 | `feed_ec_ph` | `gh-01-nutrient-room` | `dS_m`, `pH` | 30초 | 1분 | must_have | stale, calibration_due |
| 양액 | `drain_ec_ph` | `gh-01-zone-a/b` | `dS_m`, `pH` | 60초 | 5분 | must_have | stale, outlier |
| 양액 | `drain_volume` | `gh-01-zone-a/b` | `L` | 이벤트/1분 | 5분 | must_have | missing, jump |
| 외기 | `outside_weather` | `gh-01-outside` | 복합 | 30초 | 1분 | must_have | stale, communication_loss |
| 장치 | `fan_status` | `gh-01-zone-a/b` | `%`, `on_off` | 10초 | 1분 | must_have | readback_mismatch |
| 장치 | `vent_position` | `gh-01-zone-a/b` | `%` | 10초 | 1분 | must_have | readback_mismatch |
| 장치 | `shade_position` | `gh-01-zone-a/b` | `%` | 10초 | 1분 | must_have | readback_mismatch |
| 장치 | `irrigation_valve_status` | `gh-01-zone-a/b` | `on_off` | 이벤트/10초 | 1분 | must_have | stuck, duplicate_event |
| 장치 | `heater_status` | `gh-01-zone-a/b` | `on_off` | 10초 | 1분 | should_have | readback_mismatch |
| 장치 | `dehumidifier_status` | `gh-01-dry-room` | `on_off` | 10초 | 1분 | should_have | readback_mismatch |
| 비전 | `crop_image_frame` | `gh-01-zone-a/b` | image | 5~15분 | event | optional | blur, dark_frame |
| 운영 이벤트 | `manual_override` | 전 zone | event | event | event | must_have | missing_actor |

## 5. quality_flag 기준

최소 공통 flag:

- `good`: 판단 사용 가능
- `partial`: 보조 판단에만 사용
- `bad`: 자동화 입력에서 제외

세부 원인 tag:

- `stale`
- `outlier`
- `jump`
- `flatline`
- `communication_loss`
- `readback_mismatch`
- `calibration_due`
- `missing`

판정 예:

- 환경 센서 3배 주기 이상 업데이트 없음: `stale`
- 장치 명령 후 30초 내 readback 불일치: `readback_mismatch`
- pH/EC 교정 주기 초과: `calibration_due`

## 6. AI/MLOps 연결 규칙

1. raw sensor 저장
2. quality_flag 계산
3. 1분 snapshot 생성
4. 5분/30분 trend 생성
5. `state-estimator` 입력으로 전달
6. 품질 불량 구간은 학습 후보와 `farm_case` 후보에서 기본 제외

## 7. 현장형 인벤토리 연결

수집 카탈로그를 실제 구현 입력으로 쓰기 위해 아래 산출물을 함께 유지한다.

- `docs/sensor_installation_inventory.md`: zone별 설치 수량, protocol, calibration, model_profile
- `schemas/sensor_catalog_schema.json`: 장비 목록 검증 스키마
- `data/examples/sensor_catalog_seed.json`: 인스턴스 단위 sensor/device seed catalog
- `docs/sensor_ingestor_config_spec.md`: poller profile, connection, binding group, publish target 계약
- `schemas/sensor_ingestor_config_schema.json`: `sensor-ingestor` 설정 스키마
- `data/examples/sensor_ingestor_config_seed.json`: `gh-01` 기준 poller/connection/binding seed config

현재 seed catalog는 `gh-01` 기준 센서 29개, 장치 20개를 포함한다. 이 값은 초기 구현 기준치이며, `Grodan GT Master` slab 라인 수와 온실 베드 배치가 확정되면 `air_temp_rh`, `substrate_moisture`, `substrate_temp`, `circulation_fan`, `irrigation_valve`부터 증설한다.

설정 seed는 위 카탈로그를 기반으로 센서 29개, 장치 20개를 정확히 한 번씩 binding하도록 작성했다. 즉, 수집 목록과 런타임 설정이 분리되면서도 coverage 검증이 가능하다.

## 8. 즉시 후속 작업

1. PLC tag naming 규칙과 주소 체계 확정
2. protocol adapter별 register/tag mapping 표 작성
3. redundancy group merge와 `pending_batch` 예외 규칙 확정
4. 상용 장비 shortlist 조사
