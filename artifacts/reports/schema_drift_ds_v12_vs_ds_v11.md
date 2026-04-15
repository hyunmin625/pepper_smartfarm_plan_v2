# Output schema drift report

- reference: `artifacts/reports/fine_tuned_model_eval_ds_v11_prompt_v5_methodfix_batch14_extended200.jsonl`
- candidate: `artifacts/reports/fine_tuned_model_eval_ds_v12_extended200.jsonl`

## Overall

| metric | reference | candidate | Δ |
|---|---:|---:|---:|
| records | 200 | 200 | +0 |
| pass_rate | 0.7 | 0.11 | -0.59 |
| strict_json_rate | 1.0 | 1.0 | +0.0 |

## Alarms

- ⚠️  **new_top_level_keys: 17 ≥ 3**
- ⚠️  **common_key_drops: 5**
- ⚠️  **rare_key_losses: 1**
- ⚠️  **citations_majority_shape_below_floor: 0.2284 < 0.8**
- ⚠️  **pass_rate_drop: 0.59 >= 0.15**

## New top-level keys (candidate-only)

- `action_candidates`
- `action_list`
- `actions`
- `approved`
- `backoff_minutes`
- `fallback_reason`
- `recommended_action`
- `recommended_decision`
- `recommended_state`
- `requires_human_intervention`
- `risk_assessment`
- `safety_status`
- `state`
- `state_id`
- `status`
- `suggested_actions`
- `visual_inspection_advice`

## Missing top-level keys (reference-only)

- `blocked_action_type`
- `skipped_task_types`
- `state_version`
- `target`
- `urgency`

## Common key drops (ref count ≥10, ≥50% drop)

| key | reference | candidate | drop_ratio |
|---|---:|---:|---:|
| `fallback_mode` | 28 | 9 | 0.6786 |
| `blocked_action_type` | 20 | 0 | 1.0 |
| `decision` | 20 | 9 | 0.55 |
| `reason` | 20 | 9 | 0.55 |
| `required_follow_up` | 20 | 9 | 0.55 |

## Rare-key losses (ref count ≥5, candidate 0)

- `blocked_action_type` (reference count: 20)

## Citation shape distribution

- reference majority shape: `['chunk_id', 'document_id']` (0.9003 of citations)
- candidate majority shape: `['doc_id', 'doc_type']` (0.2284 of citations)

### reference citation shapes

| shape | count |
|---|---:|
| `('chunk_id', 'document_id')` | 298 |
| `('<empty>',)` | 33 |

### candidate citation shapes

| shape | count |
|---|---:|
| `('doc_id', 'doc_type')` | 74 |
| `('doc_id', 'extract')` | 53 |
| `('<empty>',)` | 52 |
| `('<string>',)` | 25 |
| `('claim', 'source')` | 15 |
| `('document_id', 'excerpt')` | 14 |
| `('doc_id', 'excerpt')` | 13 |
| `('doc_id', 'reason')` | 12 |
| `('document_id', 'page')` | 7 |
| `('citation_id', 'document_title', 'document_type', 'release_date')` | 7 |
| `('source_id', 'source_type')` | 4 |
| `('citation_id', 'document_title', 'document_type', 'source')` | 4 |

