# Batch19 Real Shadow Feedback Plan

`batch19`는 실제 shadow rollback feedback과 `blind_holdout50 validator` 잔여 5건을 동시에 줄이기 위한 corrective batch다.

## 목표

- real shadow window의 `critical_disagreement`를 학습 데이터로 즉시 역투영한다.
- `blind_holdout50 validator 0.9`를 막는 잔여 5건을 owner 기준으로 직접 보강한다.
- 다음 challenger에서는 validator 규칙과 prompt 규칙이 같은 방향으로 작동하도록 `sft_v10`을 함께 적용한다.

## source 1. real shadow rollback feedback

- source report: [shadow_mode_real_sample_window.md](/home/user/pepper-smartfarm-plan-v2/artifacts/reports/shadow_mode_real_sample_window.md:1)
- critical disagreement case: `shadow-runtime-002`
- observed gap:
  - raw AI before validator: `request_human_check`
  - operator / validator after rewrite: `block_action + create_alert`
  - context: `worker_present + manual_override_active`

이 case는 `safety_policy` high/medium undercall이 아니라 `critical + block_action + create_alert`가 즉시 나와야 하는 hard safety gap이다.

## source 2. blind50 validator residual 5

- source report: [validator_residual_failures_ds_v11_prompt_v5_methodfix_batch14_blind_holdout50.json](/home/user/pepper-smartfarm-plan-v2/artifacts/reports/validator_residual_failures_ds_v11_prompt_v5_methodfix_batch14_blind_holdout50.json:1)

owner 분류:

- `data_and_model`
  - `blind-action-004`
  - `blind-expert-003`
  - `blind-expert-010`
- `risk_rubric_and_data`
  - `blind-expert-001`
  - `blind-robot-004`

## batch19 구성

- `state_judgement_samples_batch19_real_shadow_feedback.jsonl`
  - `safety_policy` 2건
  - `climate_risk` 1건
  - `nutrient_risk` 1건
  - `rootzone_diagnosis` 1건
- `action_recommendation_samples_batch19_real_shadow_feedback.jsonl`
  - `blind-action-004` 직접 corrective 1건
- `failure_response_samples_batch19_real_shadow_feedback.jsonl`
  - `critical readback/comm loss` 1건
- `robot_task_samples_batch19_real_shadow_feedback.jsonl`
  - `blind-robot-004` 직접 corrective 1건

총 `8건`

## corrective intent

- `worker_present / manual_override / estop`
  - `risk_level=critical`
  - `required_action_types=[block_action, create_alert]`
  - `request_human_check only` 패턴 제거
- `critical path comm loss`
  - `risk_level=critical`
  - `required_action_types=[enter_safe_mode, request_human_check]`
- `GT Master dryback / EC gradient`
  - `risk_level=high`
  - `required_action_types=[create_alert, request_human_check]`
  - `adjust_fertigation reflex` 제거
- `Delta 6.5 nursery cold-humid`
  - `risk_level=high`
  - `required_action_types=[create_alert, request_human_check]`
  - `adjust_vent reflex` 제거
- `robot blocked candidate`
  - `risk_level=high`
  - `required_task_types=[skip_area]`

## next candidate

다음 challenger는 `batch19 + sft_v10 + hard-case oversampling` 조합으로만 연다.

- dataset_version: `ds_v14`
- prompt_version: `prompt_v10_validator_aligned_batch19_hardcase`
- eval_version: `eval_v5`
- submit policy: `synthetic shadow day0` 또는 실제 shadow window blocker가 남아 있으면 dry-run까지만 허용
