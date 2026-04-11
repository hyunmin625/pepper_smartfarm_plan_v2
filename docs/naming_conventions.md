# Naming Conventions

이 문서는 저장소의 ID, 이벤트, 식별자 이름 규칙을 정리한다.

## 1. 기본 원칙

- 사람용 문서는 한국어 설명을 유지한다.
- 기계가 읽는 ID와 필드는 영어 `snake_case`를 사용한다.
- 디렉터리 이름은 `kebab-case`를 사용한다.

## 2. ID 규칙

- `zone_id`
  - 예: `gh-01-zone-a`, `gh-01-zone-b`, `gh-01-dry-room`
- `sensor_id`
  - 예: `gh-01-zone-a--air-temp-rh--01`
- `device_id`
  - 예: `gh-01-zone-a--circulation-fan--01`
- `robot_id`
  - 형식: `{site_id}-{workcell}--{robot_type}--{nn}`
  - 예: `gh-01-harvest-line--arm--01`

## 3. action_type 규칙

- 동사로 시작한다.
- 목적이 드러나야 한다.
- 예:
  - `adjust_fan`
  - `adjust_vent`
  - `short_irrigation`
  - `pause_automation`
  - `enter_safe_mode`

## 4. 이벤트 이름 규칙

- 형식: `{domain}.{subject}.{event_name}`
- 예:
  - `sensor.air_temp.updated`
  - `sensor.rootzone_ec.stale`
  - `device.heater.readback_mismatch`
  - `control.override.manual_started`
  - `control.safety.estop_latched`
  - `decision.action.blocked`
  - `robot.harvest.interrupted`

## 5. 로그 키 규칙

- `request_id`, `decision_id`, `action_id`, `chunk_id`, `policy_id`처럼 suffix를 통일한다.
- dedupe/cooldown key는 `:` 구분자를 사용한다.
  - 예: `device:gh-01-zone-a--circulation-fan--01:adjust_fan`
