# Offline Shadow Residual Batch17 Plan

이 문서는 offline shadow replay 기준선에서 남은 drift `4건`을 batch17 sample `8건`으로 어떻게 직접 역투영했는지 기록한다.

## 1. 목적

- replay heuristic false drift를 걷어낸 뒤에도 남은 `data_and_model`, `robot_contract_and_model` 잔여만 직접 겨냥한다.
- broad prompt 수정 없이 `create_alert 누락`, `adjust_fertigation reflex`, `inspect_crop contract 누락`만 training sample에 다시 고정한다.
- 후속 challenger 전 `왜 이 sample이 들어갔는지`를 eval id 기준으로 추적 가능하게 만든다.

## 2. residual drift와 batch17 매핑

### A. `data_and_model`

- `blind-action-004` -> `action-rec-031`, `action-rec-032`
- `blind-expert-003` -> `state-judgement-321`, `state-judgement-322`
- `blind-expert-010` -> `state-judgement-323`, `state-judgement-324`

핵심:

- `GT Master` dry-back + 낮은 새벽 `WC` + 반복 잎 처짐은 `high + create_alert + request_human_check`를 우선 고정한다.
- `GT Master` drain `EC` 급등 + 낮은 drain fraction은 `high + create_alert + request_human_check`를 우선 고정한다.
- 위 세 slice에서는 `adjust_fertigation` reflex를 끊고, recipe 변경보다 경고와 현장 확인이 먼저라는 패턴을 다시 주입한다.

### B. `robot_contract_and_model`

- `blind-robot-005` -> `robot-task-103`, `robot-task-104`

핵심:

- `low-confidence hotspot -> inspect_crop` exact enum을 다시 고정한다.
- `candidate_id`와 `target`을 모두 채운 계약형 sample만 추가한다.
- generic `create_robot_task`로 흐르는 경향을 끊는다.

## 3. 생성 파일

- `data/examples/action_recommendation_samples_batch11_shadow_residual.jsonl`: `2건`
- `data/examples/state_judgement_samples_batch17_shadow_residual.jsonl`: `4건`
- `data/examples/robot_task_samples_batch6_shadow_residual.jsonl`: `2건`
- 총 `8건`

## 4. 기대 효과

- offline shadow residual `4건`을 broad prompt 수정 없이 다음 challenger training seed로 직접 반영한다.
- `blind-action-004`, `blind-expert-003`, `blind-expert-010`의 공통 패턴인 `create_alert` 누락과 `adjust_fertigation` reflex를 줄인다.
- `blind-robot-005`의 `inspect_crop` 계약 누락을 exact enum sample로 다시 고정한다.

## 5. 다음 단계

- batch17 반영 후 `validate_training_examples`, `audit_training_data_consistency`, `report_risk_slice_coverage`, `report_training_sample_stats`를 다시 실행해 반영 상태를 고정한다.
- 후속 challenger는 batch16 + batch17 + hard-case oversampling을 함께 쓸지, batch17만 먼저 쓸지 `ds_v11` 잔여 failure owner 기준으로 결정한다.
- 실제 shadow mode 로그가 확보되기 전에는 offline replay 개선만으로 제품 승격 결론을 내리지 않는다.
