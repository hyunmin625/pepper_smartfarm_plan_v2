# Hard-case Oversampling Plan

이 문서는 `ds_v11` 이후 후속 challenger가 필요할 때 적용할 train-only oversampling 기준을 고정한다.

## 목적

- 평범한 상태 판단보다 `safety_policy`, `failure_response`, `sensor_fault` hard case를 더 강하게 학습시킨다.
- prompt 규칙 추가보다 데이터 가중치와 hard-case batch를 먼저 쓴다.

## 현재 기준

- 실제 제출 중인 run: `ds_v11 / prompt_v5_methodfix_batch14`
- 이 run에는 oversampling을 적용하지 않았다.
- oversampling은 `ds_v11` 평가가 끝난 뒤 필요할 때만 다음 challenger에서 사용한다.

## hard-case batch

다음 전용 hard-case batch를 추가했다.

- `data/examples/state_judgement_samples_batch15_hard_cases.jsonl`
- `data/examples/failure_response_samples_batch15_hard_cases.jsonl`
- `data/examples/robot_task_samples_batch6_hard_cases.jsonl`
- `data/examples/state_judgement_samples_batch16_safety_reinforcement.jsonl`
- `data/examples/failure_response_samples_batch16_safety_reinforcement.jsonl`

핵심 시나리오:

- `worker_present` / `manual_override_active` 아래 동력 장치 차단
- `sensor jump + flatline`, `rootzone evidence incomplete`
- `irrigation/source-water/dry-room/reboot recovery` failure safe-mode
- `worker_present` / `estop_active` 아래 robot task 차단
- `worker_present`는 모두 `risk_level=critical`, `block_action + create_alert`
- `manual_override / safe_mode`는 자동 제어 재시도를 모두 `block_action`으로 차단
- 핵심 readback / communication loss는 모두 `risk_level=critical`, `enter_safe_mode + request_human_check`

## oversampling 규칙

- `safety_policy=5`
- `failure_response=5`
- `sensor_fault=5`
- `robot_task_prioritization=3`

이 가중치는 train split에만 적용한다. validation/eval에는 적용하지 않는다.

## 실행 예시

```bash
python3 scripts/build_openai_sft_datasets.py \
  --system-prompt-version sft_v5 \
  --validation-min-per-family 2 \
  --validation-ratio 0.15 \
  --validation-selection spread \
  --oversample-task-type safety_policy=5 \
  --oversample-task-type failure_response=5 \
  --oversample-task-type sensor_fault=5 \
  --oversample-task-type robot_task_prioritization=3 \
  --train-output artifacts/fine_tuning/openai_sft_train_hardcase.jsonl \
  --validation-output artifacts/fine_tuning/openai_sft_validation_hardcase.jsonl
```

## 원칙

- oversampling은 `next-only`다. 현재 제출된 `ds_v11`에는 소급 적용하지 않는다.
- oversampling을 써도 frozen gate는 그대로 `core24 + extended120 + extended160 + extended200 + blind_holdout50 + raw/validator gate`다.
- score가 오르더라도 blind/generalization이 개선되지 않으면 prompt chasing으로 돌아가지 않는다.
- batch16까지 반영한 현재 training은 `328건`이다. 권장 가중치 dry-run 기준 train `803`, validation `57`, SFT format error `0`을 확인했다.
