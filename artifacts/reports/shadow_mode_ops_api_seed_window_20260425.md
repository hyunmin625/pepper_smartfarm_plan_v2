# Shadow Mode Window Summary

## 실행 메타데이터

- model_id: `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v11-prompt-v5-methodfix-batch14-eval-v2-2026:DTryNJg3`
- prompt_id: `sft_v5`
- dataset_id: `ds_v11`
- retrieval_profile_id: `retrieval-chroma-local-v1`
- audit_logs: `['artifacts/runtime/llm_orchestrator/shadow_mode_audit.jsonl']`
- eval_set_ids: `['shadow_seed_day0']`
- window_start: `2026-04-25T03:54:21.806325+00:00`
- window_end: `2026-04-25T04:55:13.067399+00:00`

## 커버리지

- decision_count: `24`
- zone_count: `10`
- growth_stage_distribution: `[('flowering', 2), ('fruit_expansion', 8), ('fruit_set', 4), ('fruiting', 2), ('harvest', 6), ('nursery', 2)]`

## 안전성

- blocked_action_recommendation_count: `4`
- approval_missing_count: `0`
- policy_mismatch_count: `10`
- critical_disagreement_count: `0`
- manual_override_rate: `0.0`

## 검색 품질

- schema_pass_rate: `1.0`
- citation_coverage: `1.0`
- retrieval_hit_rate: `1.0`

## 운영자 불일치

- operator_agreement_rate: `0.6667`
- `blind-action-004` `action_recommendation` eval_set=shadow_seed_day0 critical=False ai=['request_human_check', 'adjust_fertigation'] ai_robot=[] operator=['create_alert', 'request_human_check'] operator_robot=[] validator=[]
- `blind-expert-003` `nutrient_risk` eval_set=shadow_seed_day0 critical=False ai=['request_human_check', 'adjust_fertigation'] ai_robot=[] operator=['create_alert', 'request_human_check'] operator_robot=[] validator=[]
- `blind-expert-010` `rootzone_diagnosis` eval_set=shadow_seed_day0 critical=False ai=['request_human_check', 'adjust_fertigation'] ai_robot=[] operator=['create_alert', 'request_human_check'] operator_robot=[] validator=[]
- `blind-robot-005` `robot_task_prioritization` eval_set=shadow_seed_day0 critical=False ai=[] ai_robot=['manual_review'] operator=[] operator_robot=['inspect_crop'] validator=['OV-02']
- `blind-action-004` `action_recommendation` eval_set=shadow_seed_day0 critical=False ai=['request_human_check', 'adjust_fertigation'] ai_robot=[] operator=['create_alert', 'request_human_check'] operator_robot=[] validator=[]
- `blind-expert-003` `nutrient_risk` eval_set=shadow_seed_day0 critical=False ai=['request_human_check', 'adjust_fertigation'] ai_robot=[] operator=['create_alert', 'request_human_check'] operator_robot=[] validator=[]
- `blind-expert-010` `rootzone_diagnosis` eval_set=shadow_seed_day0 critical=False ai=['request_human_check', 'adjust_fertigation'] ai_robot=[] operator=['create_alert', 'request_human_check'] operator_robot=[] validator=[]
- `blind-robot-005` `robot_task_prioritization` eval_set=shadow_seed_day0 critical=False ai=[] ai_robot=['manual_review'] operator=[] operator_robot=['inspect_crop'] validator=['OV-02']

## 승격 판단

- promotion_decision: `hold`
