# Output schema drift report

- reference: `artifacts/reports/fine_tuned_model_eval_ds_v11_prompt_v5_methodfix_batch14_extended200.jsonl`
- candidate: `artifacts/reports/fine_tuned_model_eval_ds_v11_b1_extended200.jsonl`

## Overall

| metric | reference | candidate | Δ |
|---|---:|---:|---:|
| records | 200 | 200 | +0 |
| pass_rate | 0.7 | 0.485 | -0.215 |
| strict_json_rate | 1.0 | 1.0 | +0.0 |

## Alarms

- ⚠️  **common_key_drops: 1**
- ⚠️  **rare_key_losses: 1**
- ⚠️  **pass_rate_drop: 0.215 >= 0.15**

## New top-level keys (candidate-only)

- `skipped_candidates`
- `suggested_actions`

## Missing top-level keys (reference-only)

- `skipped_robot_tasks`
- `skipped_task_types`
- `state_type`
- `state_version`

## Common key drops (ref count ≥10, ≥50% drop)

| key | reference | candidate | drop_ratio |
|---|---:|---:|---:|
| `fallback_mode` | 28 | 1 | 0.9643 |

## Rare-key losses (ref count ≥5, candidate 0)

- `skipped_robot_tasks` (reference count: 5)

## Citation shape distribution

- reference majority shape: `['chunk_id', 'document_id']` (0.9003 of citations)
- candidate majority shape: `['chunk_id', 'document_id']` (0.9015 of citations)

### reference citation shapes

| shape | count |
|---|---:|
| `('chunk_id', 'document_id')` | 298 |
| `('<empty>',)` | 33 |

### candidate citation shapes

| shape | count |
|---|---:|
| `('chunk_id', 'document_id')` | 293 |
| `('<empty>',)` | 32 |

