# Blind50 Residual Batch14 Plan

이 문서는 validator 적용 후에도 남은 blind holdout `50` 잔여 실패 `12건`을 batch14 training sample로 어떻게 옮겼는지 기록한다.

## 1. 목적

- `runtime_validator_gap`이 아니라 `risk_rubric_and_data`, `data_and_model`, `robot_contract_and_model` ownership만 남긴다.
- 남은 실패를 broad tuning이 아니라 residual-aligned sample로 직접 보강한다.
- 후속 challenger 전 `왜 이 sample이 추가됐는지`를 eval id 기준으로 추적 가능하게 만든다.

## 2. 잔여 실패와 batch14 매핑

### A. `risk_rubric_and_data`

- `blind-action-005` -> `action-rec-029`
- `blind-expert-001` -> `state-judgement-108`
- `blind-expert-009` -> `state-judgement-110`
- `blind-expert-003` -> `state-judgement-109`
- `blind-expert-010` -> `action-rec-028`, `state-judgement-111`
- `blind-expert-012` -> `state-judgement-112`
- `blind-robot-004` -> `robot-task-046`

핵심:

- `Delta 6.5` 육묘 야간 고습/잎 젖음은 `high`로 고정
- `GT Master` 낮은 새벽 `WC` + 과도한 `dry-back` + 반복 잎 처짐은 `high`로 고정
- 배액 근거 부재는 `unknown + pause_automation + request_human_check`로 고정
- blocked harvest candidate는 `high + skip_area`로 고정

### B. `data_and_model`

- `blind-action-002` -> `action-rec-028`
- `blind-action-006` -> `action-rec-030`

핵심:

- `required_action_types_present` 누락을 직접 보강
- `adjust_fertigation`를 reflex처럼 내는 경향을 끊고 `create_alert` 또는 `pause_automation` 우선 패턴을 강화

### C. `robot_contract_and_model`

- `blind-robot-002` -> `robot-task-045`
- `blind-robot-005` -> `robot-task-047`
- `blind-robot-007` -> `robot-task-048`

핵심:

- `inspect_crop`, `skip_area`, `manual_review` exact enum을 다시 고정
- `candidate_id`와 `target`을 모두 채운 계약형 sample만 추가

## 3. 생성 파일

- `data/examples/action_recommendation_samples_batch10.jsonl`: `3건`
- `data/examples/state_judgement_samples_batch14.jsonl`: `5건`
- `data/examples/robot_task_samples_batch5.jsonl`: `4건`
- 총 `12건`

## 4. 현재 반영 후 상태

- training rows: `288`
- blind50 validator residual: `12건`
- owner 분포: `risk_rubric_and_data 7`, `data_and_model 2`, `robot_contract_and_model 3`
- training slice:
  - `robot_contract`: `48`
  - `gt_master_dryback_high`: `6`
  - `nursery_cold_humid_high`: `3`
  - `evidence_incomplete_unknown`: `11`

## 5. 다음 단계

- batch14를 포함한 challenger를 한 번만 다시 돌린다.
- 비교 게이트는 `core24 + extended160 + extended200 + blind_holdout50 + product gate(raw/validator)`로 고정한다.
- shadow mode가 없으면 제품 주장으로 올리지 않는다.
