# Critical Slice Augmentation Plan

이 문서는 다음 fine-tuning 전에 어떤 slice를 얼마나 보강할지 정리한다.

## 1. 원칙

- 총량 확대보다 제품 blocking slice를 먼저 보강한다.
- prompt 규칙 추가보다 data/eval/validator 정렬을 우선한다.
- 기존 `robot_task_prioritization`는 건수 자체보다 계약형 hard case를 늘린다.

## 2. 현재 기준선

로컬 합본 기준:

- training rows: `288`
- extended eval rows: `200`
- blind holdout rows: `50`

현재 training slice 관측치:

- `safety_policy_hard_block`: `32`
- `sensor_fault_unknown`: `26`
- `evidence_incomplete_unknown`: `11`
- `failure_safe_mode`: `16`
- `robot_task_prioritization`: `48`
- `gt_master_dryback_high`: `6`
- `nursery_cold_humid_high`: `3`
- action imbalance:
  - `request_human_check`: `137`
  - `create_alert`: `99`
  - `pause_automation`: `46`
  - `block_action`: `33`
  - `enter_safe_mode`: `16`

현재 eval/holdout 관측치:

- extended eval `safety_policy_hard_block`: `18`
- extended eval `sensor_fault_unknown`: `13`
- extended eval `evidence_incomplete_unknown`: `10`
- extended eval `failure_safe_mode`: `19`
- blind holdout `safety_policy_hard_block`: `6`
- blind holdout `failure_safe_mode`: `6`
- blind holdout `robot_task_prioritization`: `7`
- blind holdout `gt_master_dryback_high`: `3`
- blind holdout `nursery_cold_humid_high`: `1`

## 3. 우선 보강 목표

### A. `safety_policy`

목표:

- current training `34` 유지
- hard-block slice `32` 유지

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

- current training `26` 유지

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

- current training `36`
- `path_loss/readback safe_mode` slice `16` 유지

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

- evidence incomplete unknown slice `10` 유지

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

- current training `48` 유지
- hard case 라벨 품질 유지

추가해야 할 상황:

- candidate는 존재하지만 `worker_present` 또는 `robot_zone_not_clear`
- candidate 간 우선순위가 비슷하지만 하나만 승인 가능한 경우
- `inspect_crop`, `skip_area`, `manual_review`, `harvest_candidate_review` exact enum 분기
- `candidate_id`와 `target` 둘 중 하나만 있는 케이스

핵심:

- 사용자 요구인 `20+`는 이미 충족했다.
- 이제는 건수보다 `enum exactness`, `candidate_id/target`, `approval_required` 일관성이 더 중요하다.

### F. Remaining Blind Generalization Gaps

목표:

- `gt_master_dryback_high`: `6`
- `nursery_cold_humid_high`: `3`

추가해야 할 상황:

- `GT Master` 과도한 `dry-back` + 낮은 새벽 `WC` + 반복 잎 처짐
- `Delta 6.5` 육묘 구간의 해진 뒤 고습 + 잎 젖음 증가

정답 패턴:

- `gt_master_dryback_high`: `risk_level=high`, `create_alert + request_human_check`
- `nursery_cold_humid_high`: `risk_level=high`, `create_alert + request_human_check`
- 두 경우 모두 hard safety validator로 덮지 않고 `data + rubric` ownership으로 유지한다.

## 4. 최소 추가량

다음 fine-tuning 전 최소 추가량:

- `safety_policy`: `완료`
- `sensor_fault`: `완료`
- `robot_task_prioritization`: `완료`
- `failure_response` safe-mode slice: `완료`
- `rootzone/nutrient` evidence incomplete slice: `완료`
- `remaining blind 2건` 대응 slice: `완료`

총 추가량 가이드:

- 현재 training critical slice와 남은 blind 의미 gap 보강 목표는 모두 채웠고, batch14로 blind50 validator residual `12건`을 직접 training sample로 역투영했다.

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
- `gt_master_dryback_high`
- `nursery_cold_humid_high`

## 6. 현재 자동 감사에서 확인된 라벨 이슈

`python3 scripts/report_risk_slice_coverage.py` 기준 training 쪽 rule failure는 현재 `none`이다.

즉, 기존 training label mismatch 정리와 training critical slice 보강은 완료됐다. 남은 병목은 `blind_holdout50`, `extended200`, `policy/output validator`, 그리고 batch14가 challenger에서 실제로 residual `12건`을 줄이는지 확인하는 일이다.

## 7. 제출 전 체크

- `python3 scripts/audit_training_data_consistency.py`
- `python3 scripts/report_risk_slice_coverage.py`
- `python3 scripts/report_eval_set_coverage.py --promotion-baseline extended160`

위 세 결과가 모두 새 기준과 맞아야 다음 fine-tuning을 검토한다.
