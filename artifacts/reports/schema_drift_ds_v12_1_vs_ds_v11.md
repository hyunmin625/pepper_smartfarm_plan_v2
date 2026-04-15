# Output schema drift report

- reference: `artifacts/reports/fine_tuned_model_eval_ds_v11_prompt_v5_methodfix_batch14_extended200.jsonl`
- candidate: `artifacts/reports/fine_tuned_model_eval_ds_v12_1_extended200.jsonl`

## Overall

| metric | reference | candidate | Δ |
|---|---:|---:|---:|
| records | 200 | 200 | +0 |
| pass_rate | 0.7 | 0.585 | -0.115 |
| strict_json_rate | 1.0 | 1.0 | +0.0 |

## Alarms

- ⚠️  **new_top_level_keys: 5 ≥ 3**
- ⚠️  **rare_key_losses: 1**

## New top-level keys (candidate-only)

- `skipped_candidates`
- `skipped_task_reasons`
- `state`
- `strategy`
- `task_prioritization`

## Missing top-level keys (reference-only)

- `skipped_robot_tasks`
- `state_type`
- `state_version`
- `target`

## Common key drops (ref count ≥10, ≥50% drop)

- 없음

## Rare-key losses (ref count ≥5, candidate 0)

- `skipped_robot_tasks` (reference count: 5)

## Citation shape distribution

- reference majority shape: `['chunk_id', 'document_id']` (0.9003 of citations)
- candidate majority shape: `['chunk_id', 'document_id']` (0.861 of citations)

### reference citation shapes

| shape | count |
|---|---:|
| `('chunk_id', 'document_id')` | 298 |
| `('<empty>',)` | 33 |

### candidate citation shapes

| shape | count |
|---|---:|
| `('chunk_id', 'document_id')` | 285 |
| `('<empty>',)` | 46 |

