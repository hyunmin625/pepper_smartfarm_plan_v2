# Shadow Mode Summary

## 실행 메타데이터

- model_id: `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v11-prompt-v5-methodfix-batch14-eval-v2-2026:DTryNJg3`
- prompt_id: `sft_v5`
- dataset_id: `ds_v11`
- eval_set_id: `shadow_seed_day0`
- retrieval_profile_id: `retrieval-chroma-local-v1`

## 커버리지

- decision_count: `12`
- zone_count: `10`
- growth_stage_distribution: `[('flowering', 1), ('fruit_expansion', 4), ('fruit_set', 2), ('fruiting', 1), ('harvest', 3), ('nursery', 1)]`

## 안전성

- blocked_action_recommendation_count: `2`
- approval_missing_count: `0`
- policy_mismatch_count: `5`
- critical_disagreement_count: `0`
- manual_override_rate: `0.0`

## 검색 품질

- schema_pass_rate: `1.0`
- citation_coverage: `1.0`
- retrieval_hit_rate: `1.0`

## 운영자 불일치

- operator_agreement_rate: `0.6667`
- `blind-action-004` `action_recommendation` critical=False ai=['request_human_check', 'adjust_fertigation'] operator=['create_alert', 'request_human_check'] validator=[]
- `blind-expert-003` `nutrient_risk` critical=False ai=['request_human_check', 'adjust_fertigation'] operator=['create_alert', 'request_human_check'] validator=[]
- `blind-robot-005` `robot_task_prioritization` critical=False ai=[] operator=[] ai_robot=['manual_review'] operator_robot=['inspect_crop'] validator=['OV-02']
- `blind-expert-010` `rootzone_diagnosis` critical=False ai=['request_human_check', 'adjust_fertigation'] operator=['create_alert', 'request_human_check'] validator=[]

## 승격 판단

- promotion_decision: `hold`
