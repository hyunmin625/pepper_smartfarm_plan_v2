# Safety Requirements

이 문서는 `1.5 안전 요구사항 정리`의 기준 문서다. 목적은 정책 엔진과 실행 게이트가 따라야 할 최소 안전 규칙을 고정하는 것이다.

## 1. 인터록 요구사항

기본 인터록은 [sensor_installation_inventory.md](/home/user/pepper-smartfarm-plan-v2/docs/sensor_installation_inventory.md)의 `safety_interlocks`를 따른다.

- 공통: `estop`, `manual_override`, `motor_fault`
- 환기창: `wind_lock`
- 차광커튼: `travel_limit`
- 관수 밸브: `line_pressure_fault`
- 난방기: `overtemp_lock`, `fuel_fault`
- CO2 주입기: `co2_high_lock`, `vent_open_lock`
- 양액기: `ec_ph_fault`, `tank_low_level`
- 원수 밸브: `low_pressure_lock`
- 제습기: `high_temp_lock`, `condensate_fault`

인터록 active 상태에서는 대상 장치 명령을 즉시 block한다.

## 2. 비상정지 요구사항

- 온실 출입부, 양액실, 건조실, 로봇 작업구역에 물리 `estop`이 있어야 한다.
- `estop`은 latch 방식이어야 하며 자동 복구되면 안 된다.
- `estop` 발생 시 장치 명령 큐를 비우고 실행 게이트를 `blocked`로 전환한다.
- `estop` 해제 후에도 자동모드로 바로 복귀하지 않고 운영자 확인과 상태 재동기화가 필요하다.

## 3. 수동모드 전환 조건

다음 중 하나면 수동모드로 전환한다.

- `must_have` 센서 품질이 `bad`
- 통신 장애로 장치 readback이 불가
- 정전 후 재기동으로 상태 동기화가 안 됨
- `manual_override` active
- 작업자/정비자가 위험 구역에 진입
- 로봇 안전구역 clear 실패

## 4. 자동모드 전환 조건

다음 조건을 모두 만족해야 자동모드 전환을 허용한다.

- `estop` 해제 및 reset 완료
- `manual_override` 해제
- 핵심 인터록 inactive
- `must_have` 센서 품질이 `good` 또는 승인된 `partial`
- 장치 readback 정상
- 최근 정전/재기동 후 상태 재동기화 완료
- 운영자 승인 기록 존재

## 5. 승인 필수 액션

- `adjust_heating`, `adjust_co2`, `adjust_fertigation` 중 setpoint/recipe 변경
- 장시간 관수 또는 작기 중 급격한 관수 전략 변경
- 차광/환기 대폭 변경
- `create_robot_task`
- 재기동 직후 자동모드 복귀
- 건조실 고온 프로파일 전환

## 6. 절대 금지 액션

- `estop` 또는 인터록 active 상태에서 장치 강제 실행
- 사람 감지 상태에서 로봇 작업 시작/재개
- `must_have` 센서가 `bad`인데 자동 제어 명령 실행
- CO2 고농도 lock 또는 환기창 개방 상태에서 CO2 주입 강행
- 장치 readback mismatch 상태에서 동일 명령 재반복
- 정전 후 상태 재동기화 전 자동모드 복귀
- 수동 개입 중인 장치에 AI가 덮어쓰기 명령 전송

## 7. 사람 감지 시 동작 규칙

- 작업자 출입 이벤트 또는 비전 기반 사람 감지가 있으면 해당 zone의 로봇 작업은 즉시 중단한다.
- 사람 감지 중에는 이동형 로봇/로봇암 관련 새 작업을 생성하지 않는다.
- 사람 감지 해제 후에도 최소 clear hold 시간이 지나고 운영자 확인이 있어야 재개 가능하다.
- 사람 감지 이벤트는 decision log와 safety log에 모두 남긴다.

## 8. 로봇 작업 영역 접근 규칙

- 로봇 작업 시작 전 `robot_zone_clear=true`와 출입 센서 정상 상태가 필요하다.
- 작업 중 영역 침범이 감지되면 즉시 stop, task state를 `interrupted`로 전환한다.
- interrupted task는 자동 재시작하지 않는다.
- 로봇 접근 구역 재개방은 운영자 승인 후에만 가능하다.

## 9. 구현 연결

1. 정책 엔진은 이 문서를 `hard_block`, `approval_required`, `manual_mode_only` 규칙으로 쪼개어 정책 JSON으로 변환한다.
2. 실행 게이트는 `state_schema.json`의 `device_status.mode`, `recent_events`, `sensor_quality`를 사용해 검사한다.
3. 로봇 관련 규칙은 `action_schema.json`의 `create_robot_task`와 `robot_tasks[]`에 직접 연결된다.
