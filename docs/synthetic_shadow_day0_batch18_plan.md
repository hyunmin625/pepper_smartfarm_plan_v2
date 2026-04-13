# Synthetic Shadow Day0 Batch18 Plan

이 문서는 `synthetic shadow day0` 기준선에서 남은 drift `4건`을 batch18 sample로 어떻게 직접 옮겼는지 기록한다.

## 1. 목적

- `offline replay`가 아니라 `runtime-shaped shadow day0`에서 실제로 남는 disagreement만 별도 batch로 다시 고정한다.
- `create_alert` 누락과 `inspect_crop` enum drift를 다음 corrective round의 가장 작은 단위로 분리한다.
- `ds_v12` dry-run snapshot은 유지하고, batch18은 그 다음 corrective 후보의 근거만 먼저 쌓는다.

## 2. residual drift와 batch18 매핑

### A. `data_and_model`

- `blind-action-004` -> `action-rec-033`, `action-rec-034`
- `blind-expert-003` -> `state-judgement-325`, `state-judgement-326`
- `blind-expert-010` -> `state-judgement-327`, `state-judgement-328`

핵심:

- `GT Master` dry-back + 낮은 dawn `WC` + 반복 잎 처짐은 `high + create_alert + request_human_check`를 우선 고정한다.
- `drain EC` 누적 + 낮은 `drain fraction`도 `high + create_alert + request_human_check`를 먼저 내고, `adjust_fertigation`은 skipped action으로만 남긴다.
- 즉 `adjust_fertigation reflex`를 끊고 `alert-first` 패턴을 runtime-shaped shadow 기준으로 다시 주입한다.

### B. `robot_contract_and_model`

- `blind-robot-005` -> `robot-task-105`, `robot-task-106`

핵심:

- 낮은 confidence hotspot은 `manual_review`가 아니라 `inspect_crop` exact enum으로 다시 고정한다.
- `candidate_id`와 `target`을 모두 채운 계약형 sample만 추가한다.
- `generic create_robot_task -> manual_review` drift를 끊는다.

## 3. 생성 파일

- `data/examples/action_recommendation_samples_batch12_shadow_day0.jsonl`: `2건`
- `data/examples/state_judgement_samples_batch18_shadow_day0.jsonl`: `4건`
- `data/examples/robot_task_samples_batch7_shadow_day0.jsonl`: `2건`
- 총 `8건`

## 4. 기대 효과

- `synthetic shadow day0` residual `4건`을 broad prompt 수정 없이 training seed로 직접 반영한다.
- `blind-action-004`, `blind-expert-003`, `blind-expert-010`의 공통 패턴인 `create_alert` 누락과 `adjust_fertigation` reflex를 줄인다.
- `blind-robot-005`의 `inspect_crop` 계약 누락을 exact enum sample로 다시 고정한다.

## 5. 다음 단계

- batch18 반영 후 `validate_training_examples`, `audit_training_data_consistency`, `report_risk_slice_coverage`, `report_training_sample_stats`를 다시 실행해 반영 상태를 고정한다.
- `synthetic shadow day0` owner 리포트를 별도로 남겨 `data_and_model`과 `robot_contract_and_model`만 residual로 남도록 추적한다.
- 실제 후속 challenger는 batch18을 포함할지, 아니면 `ds_v12` dry-run snapshot만 먼저 유지할지 shadow/runtime 기준으로 결정한다.

## 6. hold 해소 기준과 submit 정책

결정:

- `synthetic shadow day0` residual `4건`을 줄이는 canonical corrective path는 계속 `batch18`이다.
- `ds_v12`는 frozen dry-run snapshot, `ds_v13`은 batch18 비교용 live-head dry-run으로만 유지한다.
- blind50 `batch20`까지 포함한 최신 next-only candidate는 `ds_v15`지만, 이것도 synthetic shadow `day0`와 real shadow gate가 풀리기 전까지는 submit 후보로 승격하지 않는다.
- 따라서 현재 단계의 결정은 `submit 후보 선택`이 아니라 `submit 보류`다.

해소 완료 조건:

- `synthetic shadow day0`가 `operator_agreement_rate`와 `promotion_decision` 기준으로 `promote`
- `blind-action-004`, `blind-expert-003`, `blind-expert-010`에서 `create_alert` 누락 제거
- `blind-robot-005`에서 `inspect_crop` exact enum drift 제거
- real shadow window도 `rollback`에서 `pass`로 전환
