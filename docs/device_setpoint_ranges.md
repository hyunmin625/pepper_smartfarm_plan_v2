# Device Setpoint Ranges

이 문서는 `1.3 각 장치의 최소/최대 setpoint 정리` 결과를 고정한다. 목적은 작물 목표값이 아니라, `policy-engine`, `execution-gateway`, `plc-adapter`가 공유하는 장치 명령 파라미터의 안전 운전 범위를 정의하는 것이다.

## 적용 원칙

- 기준 site: `gh-01`
- 기준 시설: `300평 연동형 비닐온실 1동`
- 값은 vendor 최종 발주값이 아니라 현재 프로젝트의 보수적 기본값이다.
- 실제 명령은 이 범위 안에 있어도 `interlock`, `approval`, `cooldown`, `season` 정책을 다시 통과해야 한다.
- 센서/장치 카탈로그의 각 `device`에는 같은 내용이 `setpoint_bounds`로 들어간다.

## 장치별 기본 범위

| device_type | parameter | 최소 | 최대 | 권장 범위 | 비고 |
|---|---|---:|---:|---:|---|
| `circulation_fan` | `speed_pct` | 0 | 100 | 30~100 | `run_state=on`일 때만 적용 |
| `vent_window` | `position_pct` | 0 | 100 | 10~80 | 강풍 시 `wind_lock` 우선 |
| `shade_curtain` | `position_pct` | 0 | 100 | 0~70 | `100`은 강광/비상 차광 용도 |
| `irrigation_valve` | `duration_seconds` | 30 | 900 | 60~300 | 1회 펄스 기준 |
| `heater` | `stage` | 0 | 2 | 0~1 | `2`는 승인 또는 혹한 대응 전제 |
| `co2_doser` | `dose_pct` | 0 | 100 | 10~60 | 환기창 개방/고농도 lock 시 금지 |
| `nutrient_mixer` | `mix_volume_l` | 50 | 1000 | 100~300 | recipe와 함께 검토 |
| `dehumidifier` | `stage` | 0 | 2 | 0~1 | 건조실 위주 |
| `dry_fan` | `speed_pct` | 0 | 100 | 30~90 | 건조실 배치 품질 기준과 연계 |

## enum/상태형 파라미터

- `circulation_fan.run_state`: `off`, `on`
- `irrigation_valve.run_state`: `closed`, `open`
- `heater.run_state`: `off`, `on`
- `co2_doser.run_state`: `off`, `on`
- `source_water_valve.run_state`: `closed`, `open`
- `dehumidifier.run_state`: `off`, `on`
- `dry_fan.run_state`: `off`, `on`
- `nutrient_mixer.recipe_id`: `hold`, `veg_a`, `veg_b`, `flush`, `sanitize`

## 해석 규칙

1. `binary` 장치는 `run_state`가 주 파라미터고, 필요 시 `duration_seconds`를 보조 파라미터로 쓴다.
2. `binary_or_percent` 장치는 `run_state`와 `speed_pct` 또는 `dose_pct`를 함께 본다.
3. `binary_or_stage` 장치는 `run_state`와 `stage`를 함께 본다.
4. `recipe_stage` 장치는 `recipe_id`가 주 파라미터이고 `mix_volume_l`는 실행 배치 크기 제한으로 쓴다.
5. `recommended_max`를 넘는 값은 자동모드에서 기본 차단하고, 필요 시 승인 경로로 보낸다.

## 후속 작업

1. `execution-gateway`에서 `device_command_request.parameters`를 `setpoint_bounds`와 대조해 reject/approval 분기 추가
2. `policy-engine` 계절별 정책 JSON에 `recommended_max` override 추가
3. 실장비 선정 후 vendor manual 기준으로 `stage`, `duration_seconds`, `mix_volume_l` 범위 미세 조정
