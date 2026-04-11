# Sensor Installation Inventory

이 문서는 `gh-01` 단일 온실을 기준으로 센서/장치 설치 수량, 통신 방식, 보정 주기, 장비 프로파일을 현장형 인벤토리 수준으로 정리한다. 목적은 구매 전에도 `sensor-ingestor`, `state-estimator`, `policy-engine` 입력 계약을 고정하는 것이다.

## 1. 적용 가정

- 대상 시설: 재배 구역 2개(`zone-a`, `zone-b`), 외기 기준점 1개, 양액실 1개, 건조실 1개
- 재배 형태: 적고추 온실 재배, 양액 공급과 배액 수집 포함
- 재배 환경 기준: 육묘용 `Grodan Delta 6.5` block, 본재배용 `Grodan GT Master` slab
- 제어 연동: 현장 센서/장치는 PLC를 거쳐 수집하되, 일부 센서는 직접 Modbus/RTSP 수집 허용
- 장비 선정 원칙: 특정 상용 모델 고정 전까지는 `model_profile`로 요구 성능만 정의

## 2. 설치 수량 요약

| zone_id | 주요 센서 수량 | 주요 장치 수량 | 비고 |
|---|---:|---:|---|
| `gh-01-zone-a` | 11 | 8 | 상단/하단 기후, 근권 2지점, 배액, 카메라 포함 |
| `gh-01-zone-b` | 11 | 8 | `zone-a`와 동일 구조 |
| `gh-01-outside` | 1 | 0 | 외기 기준 weather station |
| `gh-01-nutrient-room` | 3 | 2 | feed EC/pH, 원수/양액 온도, 양액기 |
| `gh-01-dry-room` | 3 | 2 | 건조실 기후 2지점, 제품 함수율 |

총 기준치는 센서 29개, 장치 20개다. 실제 설치 시 구역 면적과 `Grodan GT Master` slab 베드 수가 늘면 `air_temp_rh`, `substrate_moisture`, `substrate_temp`, `circulation_fan`, `irrigation_valve`를 우선 증설한다.

본 문서의 근권 센서와 배액 센서 설치 기준은 `Grodan GT Master` slab 대표 라인 기준이다. 별도 육묘 구역이 추가되면 `Grodan Delta 6.5` block용 센서 배치와 수분 기준을 같은 계약 형식으로 확장한다.

## 3. 센서 프로파일 기준

| sensor_type | model_profile | 선호 프로토콜 | 보정 주기 | 설치 기준 |
|---|---|---|---:|---|
| `air_temp_rh` | `climate_combo_upper_canopy`, `climate_combo_lower_canopy` | `rs485_modbus_rtu` | 180일 | 상단 1, 작업자 높이 1 |
| `co2` | `co2_fixed_canopy` | `rs485_modbus_rtu` | 90일 | 재배 구역별 1 |
| `par` | `par_fixed_canopy` | `rs485_modbus_rtu` | 180일 | 재배 구역별 1 |
| `substrate_moisture` | `substrate_probe_primary`, `substrate_probe_secondary` | `rs485_modbus_rtu` | 90일 | `Grodan GT Master` slab 앞/뒤 대표 라인 각 1 |
| `substrate_temp` | `substrate_temp_probe` | `rs485_modbus_rtu` | 180일 | 함수율 probe와 같은 `Grodan GT Master` slab 위치 |
| `drain_ec_ph` | `drain_ec_ph_station` | `rs485_modbus_rtu` | 30일 | 구역별 배액 수집부 1 |
| `drain_volume` | `drain_flow_counter` | `pulse_counter` | 180일 | 구역별 배액 수집부 1 |
| `outside_weather` | `weather_station_compact` | `rs485_modbus_rtu` | 180일 | 온실 외부 마스트 1 |
| `feed_ec_ph` | `feed_ec_ph_station` | `rs485_modbus_rtu` | 30일 | 양액 공급 헤더 1 |
| `nutrient_solution_temp` | `tank_temp_probe` | `rs485_modbus_rtu` | 180일 | 양액 탱크 1 |
| `source_water_temp` | `source_water_temp_probe` | `rs485_modbus_rtu` | 180일 | 원수 라인 1 |
| `crop_image_frame` | `fixed_crop_camera` | `rtsp_onvif` | 30일 점검 | 구역별 1 |
| `dry_room_temp_rh` | `dry_room_climate_combo` | `rs485_modbus_rtu` | 180일 | 급기/배기측 각 1 |
| `product_moisture` | `product_moisture_probe` | `manual_batch_import` | 30일 | 배치별 수동 측정 |

## 4. 장치 프로파일 기준

| device_type | model_profile | 제어 방식 | 상태 수집 | 응답 제한 | 주요 interlock |
|---|---|---|---|---:|---|
| `circulation_fan` | `fan_inverter_feedback` | `binary_or_percent` | `plc_tag_modbus_tcp` | 30초 | `manual_override`, `motor_fault`, `estop` |
| `vent_window` | `vent_motor_feedback` | `percent_position` | `plc_tag_modbus_tcp` | 45초 | `wind_lock`, `motor_fault`, `estop` |
| `shade_curtain` | `shade_motor_feedback` | `percent_position` | `plc_tag_modbus_tcp` | 45초 | `travel_limit`, `motor_fault`, `estop` |
| `irrigation_valve` | `valve_open_close_feedback` | `binary` | `plc_tag_modbus_tcp` | 15초 | `manual_override`, `line_pressure_fault`, `estop` |
| `heater` | `heater_run_feedback` | `binary_or_stage` | `plc_tag_modbus_tcp` | 60초 | `overtemp_lock`, `fuel_fault`, `estop` |
| `co2_doser` | `co2_valve_feedback` | `binary_or_percent` | `plc_tag_modbus_tcp` | 20초 | `co2_high_lock`, `vent_open_lock`, `estop` |
| `nutrient_mixer` | `fertigation_controller_feedback` | `recipe_stage` | `plc_tag_modbus_tcp` | 60초 | `ec_ph_fault`, `tank_low_level`, `estop` |
| `source_water_valve` | `source_water_valve_feedback` | `binary` | `plc_tag_modbus_tcp` | 15초 | `low_pressure_lock`, `estop` |
| `dehumidifier` | `dehumidifier_feedback` | `binary_or_stage` | `plc_tag_modbus_tcp` | 60초 | `high_temp_lock`, `condensate_fault`, `estop` |
| `dry_fan` | `dry_fan_feedback` | `binary_or_percent` | `plc_tag_modbus_tcp` | 30초 | `manual_override`, `motor_fault`, `estop` |

`control_mode`, `response_timeout_seconds`, `safety_interlocks`, `setpoint_bounds`는 이후 정책 엔진과 실행 게이트의 기본 입력으로 사용한다.

## 5. 구현 연결 포인트

1. `data/examples/sensor_catalog_seed.json`은 인스턴스 단위 장비 목록을 가진다.
2. `schemas/sensor_catalog_schema.json`은 `sensor-ingestor` 설정 검증 스키마로 사용한다.
3. `docs/sensor_ingestor_config_spec.md`와 `data/examples/sensor_ingestor_config_seed.json`은 위 카탈로그를 poller profile, connection, binding group으로 구체화한다.
4. 1차 상용 모델 shortlist는 `docs/sensor_model_shortlist.md`에서 관리하고, 최종 구매 단계에서 `vendor_model`, `serial_prefix`, `calibration_certificate_id`를 확정한다.
5. `product_moisture`처럼 자동 수집이 아닌 항목은 `manual_batch_import` 프로토콜로 분리 저장한다.
6. 장치 `model_profile`은 `docs/device_profile_registry.md`와 `data/examples/device_profile_registry_seed.json`에서 `plc-adapter` 실행 계약으로 관리한다.
7. 실제 controller/channel binding은 `docs/plc_site_override_map.md`와 `data/examples/device_site_override_seed.json`에서 분리 관리한다.
8. 장치 명령 파라미터의 최소/최대 범위는 `docs/device_setpoint_ranges.md`와 `data/examples/sensor_catalog_seed.json`의 `setpoint_bounds`로 관리한다.

## 6. 남은 작업

1. shortlist 장비의 가격/납기/국내 AS와 protocol adapter 적합성 비교
2. PLC tag naming 규칙과 주소 체계 확정
3. protocol adapter별 register/tag mapping 표 작성
4. zone 면적과 베드 수가 확정되면 probe 수량 재산정
