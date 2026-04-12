# Critical Slice Augmentation Plan

이 문서는 다음 fine-tuning 전에 어떤 slice를 얼마나 보강할지 정리한다.

## 1. 원칙

- 총량 확대보다 제품 blocking slice를 먼저 보강한다.
- prompt 규칙 추가보다 data/eval/validator 정렬을 우선한다.
- 기존 `robot_task_prioritization`는 건수 자체보다 계약형 hard case를 늘린다.

## 2. 현재 기준선

로컬 합본 기준:

- training rows: `194`
- extended eval rows: `120`
- blind holdout rows: `24`

현재 training slice 관측치:

- `safety_policy_hard_block`: `12`
- `sensor_fault_unknown`: `6`
- `evidence_incomplete_unknown`: `2`
- `failure_safe_mode`: `11`
- `robot_task_prioritization`: `24`

현재 eval/holdout 관측치:

- extended eval `safety_policy_hard_block`: `6`
- extended eval `sensor_fault_unknown`: `2`
- extended eval `evidence_incomplete_unknown`: `2`
- extended eval `failure_safe_mode`: `4`
- blind holdout `safety_policy_hard_block`: `1`
- blind holdout `failure_safe_mode`: `3`
- blind holdout `robot_task_prioritization`: `3`

## 3. 우선 보강 목표

### A. `safety_policy`

목표:

- current training `14` -> `20+`
- hard-block slice `12` -> `20+`

추가해야 할 상황:

- `manual_override_active`
- `worker_present`
- `safe_mode_active`
- `worker_present + robot_zone`
- `manual_override + safe_mode`
- `worker_present + dry_room_manual_inspection`

정답 패턴:

- top-level `risk_level=critical`
- `block_action + create_alert`

### B. `sensor_fault`

목표:

- current training `6` -> `20+`

추가해야 할 상황:

- air temp / humidity / CO2 / slab WC / drain sensor `stale`
- `missing`
- `flatline`
- `calibration_error`
- `mutual inconsistency`

정답 패턴:

- top-level `risk_level=unknown`
- `pause_automation + request_human_check`

### C. `failure_response`

목표:

- current training `30` 유지, 단 `path_loss/readback safe_mode` slice `8` -> `14+`
- current training `30` 유지, 단 `path_loss/readback safe_mode` slice `11` -> `16+`

추가해야 할 상황:

- irrigation pump comm loss
- source water low pressure or readback mismatch
- dry-room comm loss
- irrigation valve readback mismatch
- repeated timeout with unknown execution state

정답 패턴:

- top-level `risk_level=critical`
- `enter_safe_mode + request_human_check`

### D. `rootzone_diagnosis` / `nutrient_risk`

목표:

- evidence incomplete unknown slice `2` -> `10+`

추가해야 할 상황:

- `drain_sensor_stale`
- `drain_sensor_flatline`
- `slab_wc_missing`
- `fertigation_evidence_incomplete`
- `rootzone_evidence_incomplete`

정답 패턴:

- top-level `risk_level=unknown`
- `pause_automation + request_human_check`
- forbidden/adjustment 맥락이면 `approval_required`

### E. `robot_task_prioritization`

목표:

- current training `24` 유지
- hard case `+8~12`

추가해야 할 상황:

- candidate는 존재하지만 `worker_present` 또는 `robot_zone_not_clear`
- candidate 간 우선순위가 비슷하지만 하나만 승인 가능한 경우
- `inspect_crop`, `skip_area`, `manual_review`, `harvest_candidate_review` exact enum 분기
- `candidate_id`와 `target` 둘 중 하나만 있는 케이스

핵심:

- 건수보다 `enum exactness`, `candidate_id/target`, `approval_required` 일관성이 중요하다.

## 4. 최소 추가량

다음 fine-tuning 전 최소 추가량:

- `safety_policy`: `+8`
- `sensor_fault`: `+14`
- `failure_response` safe-mode slice: `+5`
- `rootzone/nutrient` evidence incomplete slice: `+8`
- `robot_task` contract hard case: `+8`

총 추가량 가이드:

- `+44` 내외

## 5. eval 확장과 함께 가야 하는 항목

sample만 늘리면 안 된다. 아래 eval도 같이 늘린다.

- `extended160` 먼저 확보
- 최종 제품 주장 전 `extended200`
- blind holdout `24 -> 50`

필수 eval slice:

- `safety_policy_hard_block`
- `sensor_fault_unknown`
- `evidence_incomplete_unknown`
- `failure_safe_mode`
- `robot field usability`

## 6. 현재 자동 감사에서 확인된 라벨 이슈

`python3 scripts/report_risk_slice_coverage.py` 기준 training 쪽에서 아래 mismatch가 보인다.

- `failure_safe_mode_risk_not_critical`: `4`
- `failure_safe_mode_actions_missing`: `3`
- `safety_hard_block_actions_missing`: `1`

즉, 새 sample을 추가하기 전에 기존 training label 일부도 함께 정리해야 한다.

## 7. 제출 전 체크

- `python3 scripts/audit_training_data_consistency.py`
- `python3 scripts/report_risk_slice_coverage.py`
- `python3 scripts/report_eval_set_coverage.py`

위 세 결과가 모두 새 기준과 맞아야 다음 fine-tuning을 검토한다.
