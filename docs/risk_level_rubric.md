# Risk Level Rubric

이 문서는 fine-tuning training/eval/product gate에서 `risk_level`을 일관되게 쓰기 위한 기준이다.

## 1. 기본 원칙

- `risk_level`은 개별 action severity가 아니라 `현재 상황 전체의 운영 위험도와 자동화 신뢰도`를 나타낸다.
- `recommended_actions[].risk_level`은 개별 행동의 주의 수준을 나타낼 수 있지만, top-level `risk_level`보다 우선하지 않는다.
- 센서 근거가 무너지면 무조건 `high`나 `critical`로 올리지 않는다. 먼저 `unknown` 여부를 판단한다.
- 사람 안전, latched safe mode, 핵심 경로 장애처럼 hard interlock이 필요한 경우만 `critical`을 사용한다.

## 2. 우선순위

`risk_level`은 아래 우선순위로 결정한다.

1. `critical`
2. `unknown`
3. `high`
4. `medium`
5. `low`

즉, `manual_override`, `worker_present`, `safe_mode_active`, `water path loss` 같은 hard block 상황은 다른 생육 위험보다 먼저 본다.

## 3. 레벨 정의

### `critical`

다음 조건이면 `critical`이다.

- `worker_present` 또는 worker-entry active
- `manual_override_active`
- `safe_mode_active` 또는 `reentry_pending`
- 관수, 원수, 건조실 핵심 경로의 `communication_loss` 또는 `readback_mismatch`
- 사람/로봇 충돌 가능성이 있는 zone safety conflict

기본 대응:

- `block_action + create_alert`
- 또는 물/건조 경로 장애면 `enter_safe_mode + request_human_check`

### `unknown`

다음 조건이면 `unknown`을 우선 검토한다.

- 핵심 제어 센서가 `stale`, `missing`, `flatline`, `calibration_error`, `inconsistent`
- 근권/양액 판단 근거가 incomplete
- `drain_sensor_stale`, `drain_sensor_flatline`, `slab_wc_missing`
- 증상이 있어도 센서 fault와 실제 이상을 아직 구분하지 못하는 상태

기본 대응:

- `pause_automation + request_human_check`
- 자동 관수/양액/근권 제어는 보류

### `high`

다음 조건이면 `high`다.

- 충분한 근거가 있는 작물 스트레스 또는 운영 장애
- 예: 개화기 고온, 반복 timeout으로 제어 degraded, 활착기 저온+과습 복합 위험
- 자동 제어를 즉시 멈출 정도는 아니지만 즉각적인 운영 판단이 필요한 상태

기본 대응:

- `create_alert` 또는 `pause_automation`
- 필요 시 `request_human_check`

### `medium`

다음 조건이면 `medium`이다.

- watch/review 단계의 운영 리스크
- 충분한 근거는 있으나 hard block이나 safe mode까지는 필요 없는 상태
- 예: 저장 중 습도 상승 watch, 병해충 suspicion only, 일반적인 점검·검토 권고

기본 대응:

- `request_human_check`
- 필요 시 `create_alert`

### `low`

다음 조건이면 `low`다.

- 정보성 follow-up
- 현재 상황이 안정적이거나, 조치 자체는 낮은 부담의 확인 단계

## 4. task family별 적용 기준

### `safety_policy`

- `worker_present`, `manual_override_active`, `safe_mode_active`면 top-level `risk_level=critical`
- 필수 action은 `block_action + create_alert`
- `safe_mode_active`가 이미 latched면 `enter_safe_mode`를 중복으로 넣지 않는다.

### `sensor_fault`

- 핵심 센서 `stale/missing/flatline/inconsistent`면 기본은 `unknown`
- 센서 fault 그 자체가 곧바로 `critical`은 아니다.
- 다만 사람이 현장에 있고 장치 충돌 위험까지 겹치면 safety policy가 우선한다.

### `failure_response`

- 관수, 원수, 건조실 경로의 `communication_loss/readback_mismatch`는 `critical`
- 필수 action은 `enter_safe_mode + request_human_check`
- 일반 기후 센서 stale이나 단일 sensor timeout은 보통 `high`
- 필수 action은 `pause_automation + request_human_check`

### `rootzone_diagnosis` / `nutrient_risk`

- rootzone/fertigation evidence incomplete면 기본은 `unknown`
- 배지/배액/EC 근거가 복구될 때까지 자동 판단을 보류한다.
- 충분한 근거와 실제 crop stress 조합이 있을 때만 `high`

### `robot_task_prioritization`

- 안전 차단 상황이면 `critical`
- 작업 생성 가능한 일반 운영 상황은 주로 `medium` 또는 `high`
- top-level `risk_level`보다 `robot_tasks` contract completeness가 더 중요하다.

## 5. 빠른 판정 규칙

- 사람 또는 override가 있으면: `critical`
- latched safe mode면: `critical`
- water path loss/readback loss면: `critical`
- 핵심 센서 fault로 근거가 무너지면: `unknown`
- 근거는 충분하고 즉시 대응이 필요한 crop stress면: `high`
- 검토/관찰 위주면: `medium`
- 정보성 follow-up이면: `low`

## 6. 라벨 리뷰 체크리스트

- 같은 조건에서 `risk_level`이 샘플마다 흔들리지 않는가
- `unknown`이어야 할 sensor/evidence incomplete 사례가 `high`로 과상향되지 않았는가
- `critical`이어야 할 safety/path loss 사례가 `high`나 `unknown`으로 내려가지 않았는가
- top-level `risk_level`과 required action pair가 서로 모순되지 않는가
- `safety_policy`, `failure_response`, `sensor_fault`, `rootzone_diagnosis`, `nutrient_risk`가 이 rubric을 따르는가

## 7. 운영 규칙

- 새 sample/eval 추가 전 이 rubric을 먼저 확인한다.
- prompt에는 위 규칙을 요약만 남기고, 세부 기준은 데이터 라벨과 validator가 가진다.
- 감사는 `python3 scripts/report_risk_slice_coverage.py`로 수행한다.
