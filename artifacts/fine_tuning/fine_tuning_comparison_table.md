# Fine-tuning Comparison Table

| experiment_name | status | base_model | model_version | dataset_version | prompt_version | eval_version | training_rows | validation_rows | job_id | fine_tuned_model |
|---|---|---|---|---|---|---|---:|---:|---|---|
| ft-sft-gpt41mini-ds_v4-prompt_v4-eval_v1-20260412-070051 | validating_files | gpt-4.1-mini-2025-04-14 | pepper-ops-sft-v1.3.0 | ds_v4 | prompt_v4 | eval_v1 | 150 | 14 | ftjob-xVzFf0yIJIeo5M9Nnnn2N81k | None |
| ft-sft-gpt41mini-ds_v3-prompt_v3-eval_v1-20260412-033726 | succeeded | gpt-4.1-mini-2025-04-14 | pepper-ops-sft-v1.2.0 | ds_v3 | prompt_v3 | eval_v1 | 142 | 14 | ftjob-MiiLGncQBHRXL2NZoBYWxMcc | ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v3-prompt-v3-eval-v1-20260412-033726:DTXjV3Hg |
| ft-sft-gpt41mini-ds_v2-prompt_v2-eval_v1-20260412-021539 | succeeded | gpt-4.1-mini-2025-04-14 | pepper-ops-sft-v1.1.0 | ds_v2 | prompt_v2 | eval_v1 | 133 | 14 | ftjob-ULBuPHoPBbAMah5rPdd2i334 | ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v2-prompt-v2-eval-v1-20260412-021539:DTWRpIbI |
| ft-sft-gpt41mini-ds_v1-prompt_v1-eval_v1-20260412-004953 | succeeded | gpt-4.1-mini-2025-04-14 | pepper-ops-sft-v1.0.0 | ds_v1 | prompt_v1 | eval_v1 | 126 | 14 | ftjob-45KiYE5G2J125jSNg2QqakYm | ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v1-prompt-v1-eval-v1-20260412-004953:DTV5z1FR |
| ft-sft-gpt41mini-ds_v1-prompt_v1-eval_v1-20260412 | failed | gpt-4.1-mini-2025-04-14 | pepper-ops-sft-v1.0.0 | ds_v1 | prompt_v1 | eval_v1 | 126 | 14 | ftjob-2UERXn8JN2B0SDUXL1tukptl | None |
