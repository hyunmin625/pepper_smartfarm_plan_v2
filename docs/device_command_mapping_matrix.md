# Device Command Mapping Matrix

이 문서는 `plc-adapter`가 장치별 명령을 어떤 profile, action, encoder, readback 규칙으로 처리하는지 정리한다.

## 1. 목적

- `11.3 장치별 명령 구현` 항목을 문서와 실행 검증 기준으로 고정한다.
- `execution-gateway`가 어떤 `action_type`과 `parameters`를 장치별로 허용해야 하는지 명확히 한다.
- adapter 변경 시 command sample과 validator가 같이 깨지도록 만든다.

## 2. 매핑 기준

- circulation fan / dry fan
  - action: `adjust_fan`, `pause_automation`
  - profile: `fan_inverter_feedback`, `dry_fan_feedback`
  - parameters: `run_state`, 선택 `speed_pct`
  - encoder: `fan_percent_encoder_v1`
  - ack: `run_state_matches`, `speed_pct_within_tolerance`

- vent window / shade curtain
  - action: `adjust_vent`, `adjust_shade`, `pause_automation`
  - profile: `vent_motor_feedback`, `shade_motor_feedback`
  - parameters: `position_pct`
  - encoder: `position_encoder_v1`
  - ack: `position_pct_within_tolerance`

- irrigation valve / source water valve
  - action: `short_irrigation`, `pause_automation`
  - profile: `valve_open_close_feedback`, `source_water_valve_feedback`
  - parameters: `run_state`, 선택 `duration_seconds`
  - encoder: `binary_open_close_encoder_v1`
  - ack: `run_state_matches`

- heater / dehumidifier
  - action: `adjust_heating`, `pause_automation`
  - profile: `heater_run_feedback`, `dehumidifier_feedback`
  - parameters: `run_state`, 선택 `stage`
  - encoder: `stage_encoder_v1`
  - ack: `run_state_matches`, `stage_matches`

- co2 doser
  - action: `adjust_co2`, `pause_automation`
  - profile: `co2_valve_feedback`
  - parameters: `run_state`, 선택 `dose_pct`
  - encoder: `co2_percent_encoder_v1`
  - ack: `run_state_matches`, `dose_pct_within_tolerance`

- nutrient mixer
  - action: `adjust_fertigation`, `pause_automation`
  - profile: `fertigation_controller_feedback`
  - parameters: `recipe_id`, 선택 `mix_volume_l`
  - encoder: `recipe_encoder_v1`
  - ack: `recipe_stage_matches`

## 3. 연결 파일

- command samples: `data/examples/device_command_mapping_samples.jsonl`
- execution validator: `scripts/validate_device_command_mappings.py`
- contract validator: `scripts/validate_device_command_requests.py`
