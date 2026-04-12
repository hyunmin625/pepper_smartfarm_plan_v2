# Offline Shadow Residual Drift

- model: `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v11-prompt-v5-methodfix-batch14-eval-v2-2026:DTryNJg3`
- eval_set: `blind_holdout50_offline_shadow_replay`
- operator_agreement_rate: `0.92`
- critical_disagreement_count: `0`
- promotion_decision: `promote`

## Resolved False Drift

- `blind-forbidden-007`
  - cause: `forbidden_action`를 일반 `recommended_actions`처럼 비교한 shadow 계약 불일치
  - fix: `decision + blocked_action_type` 계약으로 재정렬
- `blind-forbidden-002`
  - cause: runtime validator에 `HSV-09`가 빠져 simulation/runtime/shadow가 어긋남
  - fix: `policy-engine` runtime validator에 `HSV-09` 추가
- `blind-action-003`
  - cause: `건조실` 언급만으로 `dry_room_path_degraded`를 과하게 추정한 replay heuristic
  - fix: `communication_loss/readback` 신호가 있을 때만 path degraded로 승격
- `blind-robot-001`
  - cause: `작업자 출입 이벤트는 없다`를 `worker_present=true`로 잘못 읽은 replay heuristic
  - fix: negation-aware worker_present parsing
- `blind-failure-008`
  - cause: `dehumidifier 상태 태그가 끊긴`을 `climate_control_degraded`로 읽어 `HSV-07`로 낮춘 replay heuristic
  - fix: `failure_type=communication_loss`를 우선 반영해 `dry_room_path_degraded`로 분류

## Remaining Drift By Owner

| eval_id | task_type | owner | observed drift | next_action |
|---|---|---|---|---|
| `blind-action-004` | `action_recommendation` | `data_and_model` | `create_alert` 없이 `adjust_fertigation`로 너무 빨리 감 | GT Master dry-back 고위험 slice에 `alert + human check first` 사례 추가 |
| `blind-expert-003` | `nutrient_risk` | `data_and_model` | 염류 집적 위험에서 `create_alert`가 빠지고 조정 action이 먼저 나감 | nutrient risk high slice에서 `alert + human check` 우선 패턴 보강 |
| `blind-expert-010` | `rootzone_diagnosis` | `data_and_model` | 과도한 dry-back 반복에서 `create_alert` 없이 fertigation 조정으로 기울어짐 | GT Master 반복 dry-back batch를 다음 corrective seed에 재투입 |
| `blind-robot-005` | `robot_contract_and_model` | `robot contract` | `inspect_crop` 대신 generic task를 내고 validator가 `OV-02`로 보정 | `low-confidence hotspot -> inspect_crop` 계약 샘플을 robot batch에 추가 |

## Interpretation

- offline shadow replay는 이제 `critical_disagreement_count=0`이라 false rollback은 제거됐다.
- 남은 `4건`은 runtime policy보다 `data/model`과 `robot contract` 보강 대상으로 보는 것이 맞다.
- 이 결과는 `real field shadow mode pass` 대체가 아니다.
- 다만 다음 batch 설계는 이 `4건`을 우선 반영하는 쪽이 가장 효율적이다.
