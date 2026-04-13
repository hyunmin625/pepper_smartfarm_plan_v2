# Batch20 Post-Validator Residual Plan

`batch20`은 `ds_v14` blind50 validator 재시뮬레이션 이후에도 남는 `5건`만 직접 겨냥하는 corrective batch다.

## 목표

- `runtime_validator_gap`을 `0`으로 만든 뒤 남은 `risk_rubric_and_data`, `data_and_model` 케이스만 분리 보강한다.
- 새 prompt 예외처리 없이 `risk undercall`과 `required_action_types 누락` 경계만 학습 데이터에 다시 주입한다.
- 다음 corrective challenger를 열기 전에 blind50 residual을 training sample로 역투영한다.

## source

- source report: [validator_residual_failures_ds_v14_prompt_v10_validator_aligned_batch19_hardcase_blind_holdout50.md](/home/user/pepper-smartfarm-plan-v2/artifacts/reports/validator_residual_failures_ds_v14_prompt_v10_validator_aligned_batch19_hardcase_blind_holdout50.md:1)

남은 케이스:

- `blind-action-001`
  - owner: `data_and_model`
  - gap: `required_action_types_present`
  - intent: `request_human_check`가 빠진 저광·저온·CO2 부족 action slice 보강
- `blind-action-006`
  - owner: `risk_rubric_and_data`
  - gap: `risk_level_match`
  - intent: 배액 근거 공백은 `high`가 아니라 `unknown`
- `blind-expert-002`
  - owner: `risk_rubric_and_data`
  - gap: `risk_level_match`
  - intent: GT Master night dry-back 부족 + dawn WC 과다는 `high`가 아니라 `medium`
- `blind-expert-012`
  - owner: `risk_rubric_and_data`, `data_and_model`
  - gap: `risk_level_match`, `required_action_types_present`
  - intent: recipe shift 직전 drain 근거 공백은 `unknown + pause_automation + request_human_check`
- `blind-robot-006`
  - owner: `risk_rubric_and_data`
  - gap: `risk_level_match`
  - intent: aisle slip hazard는 `critical`이 아니라 `high`로 두고 `skip_area` 유지

## batch20 구성

- `action_recommendation_samples_batch20_post_validator_residual.jsonl`
  - `blind-action-001` corrective 1건
  - `blind-action-006` corrective 1건
- `state_judgement_samples_batch20_post_validator_residual.jsonl`
  - `blind-expert-002` corrective 2건
  - `blind-expert-012` corrective 2건
- `robot_task_samples_batch20_post_validator_residual.jsonl`
  - `blind-robot-006` corrective 2건

총 `8건`

## corrective intent

- 저광·저온 action recommendation
  - `risk_level=medium`
  - `required_action_types=[request_human_check]`
  - `adjust_vent` 금지
- 배액 근거 공백 action/nutrient slice
  - `risk_level=unknown`
  - `required_action_types=[pause_automation, request_human_check]`
  - `adjust_fertigation` 금지
- GT Master 과습 rootzone slice
  - `risk_level=medium`
  - `required_action_types=[request_human_check]`
  - `short_irrigation` 금지
- robot aisle slip slice
  - `risk_level=high`
  - `required_task_types=[skip_area]`
  - citation 유지

## next usage

`batch20`은 바로 submit용이 아니라 `ds_v14` 잔여 5건을 줄이기 위한 next-only corrective seed다.

- validator 공백은 이미 닫혔으므로, 다음 challenger는 `batch20 + real shadow 누적 로그`가 같이 준비된 뒤에만 검토한다.
- 우선순위는 여전히 `real shadow window hold/rollback 해소`가 batch20 반영보다 앞선다.
