# Extended200 Residual Priority Plan

이 문서는 `ds_v11/prompt_v5_methodfix_batch14` frozen baseline 기준 `extended200` validator 잔여 `42건`을 다음 corrective batch로 어떻게 나눌지 정리한다.

## 1. 기준선

- source report: [validator_residual_failures_ds_v11_prompt_v5_methodfix_batch14_extended200.md](/home/user/pepper-smartfarm-plan-v2/artifacts/reports/validator_residual_failures_ds_v11_prompt_v5_methodfix_batch14_extended200.md:1)
- baseline model: `ds_v11/prompt_v5_methodfix_batch14`
- remaining_failed_cases: `42`
- owner split:
  - `risk_rubric_and_data 34`
  - `data_and_model 13`
  - `robot_contract_and_model 2`
- top checks:
  - `risk_level_match 33`
  - `required_action_types_present 13`
  - `decision_match 2`
  - `required_task_types_present 2`
  - `forbidden_action_types_absent 1`

결정:

- `extended200` corrective backlog는 `ds_v14`의 `40건`이 아니라 `ds_v11`의 `42건`을 공식 planning baseline으로 유지한다.
- 이유는 `ds_v14`가 rejected challenger이기 때문이다. `ds_v14` residual report는 diagnostic delta로만 참고하고, batch 설계와 todo ownership은 `ds_v11` 기준으로 고정한다.

## 2. batch 순서

### Batch21A. `risk_rubric_core`

목표:

- `risk_level_match`와 `decision_match`를 먼저 줄인다.
- broad prompt 수정 없이 `risk_rubric_and_data` 경계를 training/eval label에 다시 맞춘다.

우선 대상 category:

- `failure_response`
- `seasonal`
- `forbidden_action`
- `action_recommendation`
- `nutrient_risk`
- `rootzone_diagnosis`
- `climate_risk`
- `edge_case`

대표 case:

- `action-eval-007`, `action-eval-021`, `action-eval-023`
- `pepper-eval-049`
- `edge-eval-003`, `edge-eval-009`
- `failure-eval-001`, `failure-eval-007`, `failure-eval-009`
- `forbidden-eval-008`, `forbidden-eval-011`, `forbidden-eval-012`, `forbidden-eval-014`
- `pepper-eval-021`, `pepper-eval-022`, `pepper-eval-023`, `pepper-eval-056`
- `pepper-eval-003`, `pepper-eval-018`
- `seasonal-eval-006`, `seasonal-eval-008`, `seasonal-eval-010`, `seasonal-eval-011`, `seasonal-eval-012`, `seasonal-eval-013`, `seasonal-eval-015`
- `robot-eval-015`

corrective intent:

- 근거 공백은 `high` 과호출보다 `unknown + request_human_check` 쪽으로 되돌린다.
- `manual_override`, `safe_mode`, `path/readback loss`, `hard lock`은 `critical`과 `block_action` 또는 `enter_safe_mode`를 우선한다.
- `forbidden_action`은 `decision_match`와 `risk_level_match`를 분리하지 말고 같은 sample에서 동시에 고정한다.

권장 규모:

- `18~24건`

### Batch21B. `required_action_types_and_evidence_gap`

목표:

- `required_action_types_present`와 `forbidden_action_types_absent`를 줄인다.
- `data_and_model` owner를 broad prompt 수정 없이 action triad corrective sample로 직접 줄인다.

우선 대상 case:

- `action-eval-003`
- `action-eval-016`
- `action-eval-022`
- `pepper-eval-010`
- `edge-eval-012`
- `edge-eval-021`
- `failure-eval-003`
- `failure-eval-004`
- `failure-eval-005`
- `failure-eval-006`
- `failure-eval-011`
- `seasonal-eval-003`
- `pepper-eval-014`

corrective intent:

- evidence gap slice는 `pause_automation + request_human_check` 또는 `create_alert + request_human_check`를 빠뜨리지 않는다.
- `adjust_fertigation`, `short_irrigation`, `adjust_vent` 같은 reflex action은 근거 공백 상태에서 금지한다.
- `edge-eval-021`처럼 `forbidden_action_types_absent`가 같이 걸린 케이스는 `required_action_types_present`와 같은 corrective sample로 묶는다.

권장 규모:

- `12~16건`

### Batch21C. `robot_contract_exactness`

목표:

- `robot_contract_and_model` owner를 별도 계약형 batch로 닫는다.
- exact enum, `candidate_id`, `target`, `required_task_types_present`를 모델 내부에서 다시 흔들리지 않게 고정한다.

우선 대상 case:

- `robot-eval-013`
- `robot-eval-016`

corrective intent:

- `manual_review` 같은 generic fallback 대신 `inspect_crop`, `skip_area` exact enum을 강제한다.
- `candidate_id`/`target` 누락이 있으면 usable task로 보지 않는다.
- 이 batch는 `Batch21A`의 `robot-eval-015` risk semantics와 분리한다.

권장 규모:

- `4~6건`

## 3. 실행 원칙

- 순서는 `Batch21A -> Batch21B -> Batch21C`로 고정한다.
- `risk_rubric_core`를 먼저 줄이지 않으면 뒤 batch가 prompt chasing으로 다시 흐를 가능성이 높다.
- `ds_v14`/`ds_v15` residual 변화는 참고하되, owner planning 기준선은 `ds_v11`을 유지한다.
- 실제 submit 검토는 batch 생성 자체가 아니라 `blind50 >= 0.95`, `synthetic shadow day0 promote`, `real shadow pass`가 충족된 뒤에만 연다.

## 4. 다음 액션

- `Batch21A` sample 설계와 생성
- `Batch21B` required action corrective sample 설계와 생성
- `Batch21C` robot exact contract sample 설계와 생성
- 생성 후 `validate_training_examples`, `audit_training_data_consistency`, `report_risk_slice_coverage` 재실행
