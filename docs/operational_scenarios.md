# Operational Scenarios

이 문서는 `1.4 운영 시나리오 정리`의 완료 기준을 위해 초기 운영 시나리오를 정상, 환경 스트레스, 센서 장애, 장치 장애, 안전 이벤트로 정리한다. 각 시나리오는 [synthetic_sensor_scenarios.jsonl](/home/user/pepper-smartfarm-plan-v2/data/examples/synthetic_sensor_scenarios.jsonl)의 합성 입력과 연결된다.

## 시나리오 목록

| scenario_id | category | 핵심 상황 | 기대 반응 |
|---|---|---|---|
| `synthetic-001` | normal_vegetative_growth | 정상 영양생장 | 관찰 유지, trend review |
| `synthetic-002` | flowering_heat_stress | 고온 상승 | 경보, 사람 확인 |
| `synthetic-003` | rootzone_overwet_ec_rise | 과습 + 배액 EC 상승 | 관수 편향 차단, 현장 확인 |
| `synthetic-004` | stale_temperature_sensor | 온도 센서 stale | 자동화 일시 중지 |
| `synthetic-005` | harvest_and_drying_risk | 수확 후보 + 건조실 과습 | 건조 follow-up |
| `synthetic-006` | monsoon_disease_watch | 장마기 병해 압력 | 병해 예찰 강화 |
| `synthetic-007` | humid_condensation_risk | 고습/결로 | 결로 경보, 병해 감시 |
| `synthetic-008` | rapid_solar_ramp | 급격한 일사 증가 | 차광/환기 선제 검토 |
| `synthetic-009` | rootzone_overdry | 과건조 | 관수 재검토 |
| `synthetic-010` | device_stuck_vent_window | 환기창 stuck | 자동화 중지, readback 확인 |
| `synthetic-011` | communication_loss_rootzone_bus | 근권 버스 통신 장애 | 수동 모드 fallback |
| `synthetic-012` | power_outage_reboot_recovery | 정전 후 재기동 | safe mode, 상태 재동기화 |
| `synthetic-013` | manual_override_active | 사람 수동 개입 | 자동 명령 차단 |
| `synthetic-014` | robot_task_interruption | 로봇 작업 중 사람 접근 | 로봇 즉시 중단 |

## 분류 기준

- 정상/환경 스트레스: `synthetic-001`, `002`, `003`, `005`, `006`, `007`, `008`, `009`
- 센서/통신 장애: `synthetic-004`, `011`
- 장치/시스템 장애: `synthetic-010`, `012`
- 사람/로봇 안전 이벤트: `synthetic-013`, `014`

## 활용 규칙

1. offline runner와 상태판단 eval의 공통 입력 seed로 사용한다.
2. `must_have` 센서가 `bad`이면 자동 제어 허용 여부를 낮춘다.
3. 장치 stuck, 통신 장애, 재기동, manual override는 항상 `safe_mode` 또는 `approval` 경로를 우선한다.
4. 사람/로봇 충돌 가능성이 있으면 재배 성능보다 안전 차단을 우선한다.

## 다음 확장

1. 낮/밤 정책 분기 시나리오 추가
2. 계절별 외기 급변 시나리오 추가
3. 품종별 민감도 차이를 반영한 시나리오 추가
