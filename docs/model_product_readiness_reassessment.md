# Model Product Readiness Reassessment

이 문서는 `0.95`를 단순 benchmark score가 아니라, 실제 `건고추 온실 스마트팜에 사용 가능한 AI 모델 제품 수준`으로 다시 해석하기 위한 재평가 메모다.

## Update 2026-04-17: frontier RAG challenger 폐기

- **2026-04-14 결정 취소**. `gemini-2.5-flash` RAG-first frontier challenger 계획 전량 폐기.
- 근거: Phase A~E 4-way 실측(`artifacts/reports/ab_full_evaluation.md`, `artifacts/reports/ab_frozen_vs_frontier.md`)에서 `gemini-2.5-flash` (thinking) `ext 0.37 / blind 0.50`, `MiniMax M2.7` `ext 0.335 / blind 0.22`로 `ds_v11` (0.70/0.70) 대비 열세였다. reasoning/thinking 모델이 이 프로젝트 JSON strict + instruction-heavy 결정 경로에 구조적으로 부적합함이 두 모델 실측으로 확정됐다.
- 조치: `gemini_flash_frontier` alias와 `sft_v11_rag_frontier` prompt를 `model_registry`/`.env` 설정에서 제거한다. production champion은 계속 `ds_v11` frozen baseline이다. 과거 평가 artifact는 역사 기록으로 보존한다.

## Update 2026-04-13: ds_v11 완료 후 판단

- 최신 완료 모델은 `ds_v11/prompt_v5_methodfix_batch14`다.
- 결과 model은 `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v11-prompt-v5-methodfix-batch14-eval-v2-2026:DTryNJg3`다.
- frozen gate 재평가 결과는 `core24 0.9167`, `extended120 0.7667`, `extended160 0.75`, `extended200 0.7`, `blind_holdout50 raw 0.7`, `blind_holdout50 validator 0.9`, `strict_json_rate 1.0`이다.
- raw blind50 gate는 `blind_holdout_pass_rate 0.7`, `safety_invariant_pass_rate 0.7083`, `field_usability_pass_rate 1.0`, validator blind50 gate는 `blind_holdout_pass_rate 0.9`, `safety_invariant_pass_rate 1.0`, `field_usability_pass_rate 1.0`이지만 둘 다 `promotion_decision=hold`다.
- `ds_v11`는 기존 baseline `ds_v9`보다 모든 frozen gate에서 개선됐다. 하지만 `blind_holdout50 validator 0.9 < 0.95`와 `shadow_mode_status=not_run` 때문에 제품 수준 주장은 여전히 불가하다.
- validator 적용 후 잔여 실패는 `blind_holdout50 5건`, `extended200 42건`이다. owner 기준으로 blind50은 `data_and_model 3`, `risk_rubric_and_data 2`, extended200은 `risk_rubric_and_data 34`, `data_and_model 13`, `robot_contract_and_model 2`다.
- blind50 기준 offline shadow replay도 추가로 만들었다. 초기에는 `forbidden_action` 계약과 replay heuristic이 어긋나 `operator_agreement_rate 0.8`, `critical_disagreement_count 1`, `promotion_decision rollback`이었지만, `forbidden_action = decision + blocked_action_type` 계약 정렬, runtime `HSV-09` 반영, `worker_present/dry_room_path_degraded` heuristic 보정 뒤 현재 기준선은 `operator_agreement_rate 0.92`, `critical_disagreement_count 0`, `promotion_decision promote`다.
- 다만 runtime envelope 기준 synthetic shadow `day0` seed pack은 아직 `operator_agreement_rate 0.6667`, `critical_disagreement_count 0`, `promotion_decision hold`다. 이는 `robot_task` exact enum drift와 `create_alert` 누락 같은 runtime-shaped backlog가 아직 남아 있음을 보여준다.
- 다만 offline replay는 여전히 실운영 shadow mode를 대체하지 않는다. 현재 남은 의미 drift는 `blind-action-004`, `blind-expert-003`, `blind-expert-010`, `blind-robot-005` 네 건이며, 이는 [shadow_mode_residual_drift_ds_v11_blind_holdout50_offline.md](/home/user/pepper-smartfarm-plan-v2/artifacts/reports/shadow_mode_residual_drift_ds_v11_blind_holdout50_offline.md:1)에 정리했다. 이 네 건은 [docs/offline_shadow_residual_batch17_plan.md](/home/user/pepper-smartfarm-plan-v2/docs/offline_shadow_residual_batch17_plan.md:1)와 batch17 sample `8건`으로 직접 역투영했다.
- synthetic shadow `day0` residual owner report도 따로 남겼다. [shadow_mode_residuals_ds_v11_day0_seed.md](/home/user/pepper-smartfarm-plan-v2/artifacts/reports/shadow_mode_residuals_ds_v11_day0_seed.md:1) 기준 잔여 `4건`은 `data_and_model 3`, `robot_contract_and_model 1`이고, 원인은 `alert_missing_before_fertigation_review 3`, `inspect_crop_enum_drift 1`이다.
- 그 다음 corrective step으로 `real shadow rollback` source `shadow-runtime-002`와 blind50 validator residual `5건`을 직접 역투영한 `batch19` sample `8건`을 추가했다. 동시에 validator hard rule을 자연어로 옮긴 `sft_v10` prompt를 추가했고, 이를 묶은 next-only candidate는 `ds_v14 / prompt_v10_validator_aligned_batch19_hardcase`다.
- `ds_v14`는 train `843`, validation `61`, format error `0`이지만 [challenger_submit_preflight_ds_v14_real_shadow.md](/home/user/pepper-smartfarm-plan-v2/artifacts/reports/challenger_submit_preflight_ds_v14_real_shadow.md:1) 기준 여전히 `blocked`다. blocker는 `blind_holdout50 validator 0.9 < 0.95`, `synthetic shadow day0 hold`, `real shadow mode rollback`이다.
- 이 residual `4건`은 [docs/synthetic_shadow_day0_batch18_plan.md](/home/user/pepper-smartfarm-plan-v2/docs/synthetic_shadow_day0_batch18_plan.md:1)와 batch18 sample `8건`으로 live head에 직접 역투영했다. 다만 `ds_v12` dry-run snapshot은 그대로 유지하고, batch18은 그 다음 corrective 후보 근거로만 추가했다.
- 이 replay는 `real field shadow mode`를 대체하지 않는다. 다만 `validator 이후에도 운영자 기대와 어긋나는 케이스`를 실제 shadow 형식으로 압축해 다음 batch 우선순위를 잡는 데는 유효하다.
- `batch16 + batch17 + hard-case oversampling`을 묶은 `ds_v12 / prompt_v5_methodfix_batch17_hardcase` dry-run package는 준비했다. 현재 draft는 train `815`, validation `57`, format error `0`, manifest `ft-sft-gpt41mini-ds_v12-prompt_v5_methodfix_batch17_hardcase-eval_v3-20260413-035151`이다.
- batch18까지 반영한 현재 live head 기준 추천 split은 train `284`, validation `60`이고, 같은 hard-case oversampling 규칙을 다시 적용한 next-only dry-run은 train `822`, validation `60`, format error `0`이다.
- 따라서 현재 결론은 `다음 submit`이 아니라 `shadow mode`, `risk rubric/data 경계 수정`, `required_action_types` 보강, 그리고 `ds_v12`는 dry-run 상태로만 유지하는 것이다.

## Update 2026-04-13: ds_v14 제출 후 판단

- `ds_v14/prompt_v10_validator_aligned_batch19_hardcase`는 사용자 승인으로 실제 submit했고 run `ftjob-37TzJb1FtgGUghjfyaGqAxkA`는 `succeeded`로 종료됐다.
- 결과 model은 `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v14-prompt-v10-validator-aligned-batch19-har:DU2VQVYz`다.
- frozen gate 재평가 결과는 `core24 0.8333`, `extended120 0.7167`, `extended160 0.6937`, `extended200 0.695`, `blind_holdout50 raw 0.74`, `blind_holdout50 validator 0.9`다.
- `blind_holdout50` raw는 `0.7 -> 0.74`로 소폭 올랐지만, validator blind gate는 `0.9 -> 0.9`로 제자리이고 core/extended는 여전히 떨어졌다.
- raw blind gate도 `blind_holdout_pass_rate 0.74`, `safety_invariant_pass_rate 0.75`, `field_usability_pass_rate 0.98`, `promotion_decision hold`였다.
- validator blind gate는 `blind_holdout_pass_rate 0.9`, `safety_invariant_pass_rate 1.0`, `field_usability_pass_rate 1.0`, `promotion_decision hold`였다.
- validator 적용 후 잔여 실패는 blind50 `5건`, extended200 `40건`이다. owner 기준으로 blind50은 `risk_rubric_and_data 4`, `data_and_model 2`, extended200은 `risk_rubric_and_data 32`, `data_and_model 14`, `robot_contract_and_model 1`이다.
- 즉 `batch19 + prompt_v10 validator alignment`는 blind raw를 조금 올렸지만, validator-aware 안전 의미를 모델 내부에 더 밀어 넣으면서 generalization이 오히려 나빠졌다.
- 특히 remaining failure cluster 기준 blind50의 중심 실패는 이제 `risk_level_match`와 `required_action_types_present`뿐이다. 이는 `prompt alignment`보다 `risk rubric/data label`과 `data slice` ownership 문제라는 기존 판단을 더 강하게 확인해 준다.
- 결론: `ds_v14`는 여전히 rejected challenger다. baseline은 그대로 `ds_v11` 유지다. 다음 단계는 `ds_v15` submit이 아니라 blind50 residual `5건`용 batch20 반영, extended200 `risk_rubric_and_data` 정리, real shadow 로그 누적이다.

## 1. 현재 로컬 증거

### historical baseline `ds_v9` 기준

- 비교용 historical baseline은 `ds_v9/prompt_v5_methodfix`다.
- `ds_v10/prompt_v8`은 최근 sync 기준 `cancelled`이며, 완료 평가 결과가 아직 없다.
- `ds_v9`는 `core24`에서 `pass_rate 0.875`, `extended120`에서 `0.7083`, `extended160`에서 `0.575`, `extended200`에서 `0.51`, `blind_holdout50`에서 `0.32`, `strict_json_rate 1.0`이다.
- 비교 기준인 `ds_v5/prompt_v5`는 `extended120`과 `blind_holdout24`에서 모두 `pass_rate 0.5417`이다.
- blind50 제품화 게이트 기준 raw `ds_v9`는 `promotion_decision=hold`, `blind_holdout_pass_rate=0.32`, `safety_invariant_pass_rate=0.25`, `field_usability_pass_rate=0.92`, `shadow_mode_status=not_run`이다.
- 즉 `ds_v9`는 공개 benchmark 일부와 robot field contract 일부를 개선했지만, 제품 블라인드 세트로 가면 `failure/safety/edge` 일반화가 크게 무너진다.
- 다만 `policy_output_validator` 시뮬레이션을 적용하면 `extended200 0.51 -> 0.755`, `blind_holdout50 0.32 -> 0.76`까지 회복된다.
- validator 적용 blind50 gate는 `safety_invariant_pass_rate 1.0`, `field_usability_pass_rate 1.0`까지 올라간다.
- 그래도 `blind_holdout_pass_rate 0.76 < 0.95`, `shadow_mode_status=not_run`이라 제품 승격은 계속 `hold`다.
- blind50 validator 적용 후에도 실패 `12건`이 남는다. 중심은 `risk_level_match`, `required_action_types_present`, `required_task_types_present`다.
- `scripts/report_validator_residual_failures.py` 기준 blind50 validator 잔여 `12건`은 `risk_rubric_and_data 7`, `data_and_model 2`, `robot_contract_and_model 3`으로 나뉜다.
- 같은 기준으로 `extended200` validator 잔여 `49건`은 `risk_rubric_and_data 38`, `data_and_model 20`, `robot_contract_and_model 7`이다.
- 즉 `validator`만으로는 충분하지 않고, `data + rubric + runtime wiring`이 함께 필요하다.

### 실제 실패 의미

- 실패의 중심은 JSON 포맷이 아니라 `risk_level`과 `required_action_types` 의미 불일치다.
- `manual_override`, `worker_present`, `safe_mode`, `irrigation/source-water/dry-room path loss`에서 `block_action` 또는 `enter_safe_mode`가 빠진다.
- `robot_task`는 점수보다 더 큰 field contract 문제를 보인다. 실제 현장에서는 `candidate_id` 또는 `target`이 없는 generic task는 unusable이다.
- `ds_v9` 재평가에서도 핵심 실패는 여전히 `risk_level_match`, `required_action_types_present`, `required_task_types_present`다.
- `ds_v5`는 `extended120` 실패 시 평균 confidence가 pass 시보다 높아 calibration 문제가 있었고, `ds_v9`는 calibration은 다소 안정됐지만 blind safety invariant는 개선하지 못했다.

## 2. 원인 판단

### A. 모델 자체 문제인가

판단: `지금 단계에서는 아니다.`

- 현재 근거만으로는 `gpt-4.1-mini`의 순수 capability ceiling을 입증하지 못했다.
- 오히려 동일 base model에서 `core24 0.875`까지는 올라간 반면, hidden/product gate에서 무너졌다.
- 이는 모델 성능 상한보다 `학습 목표`, `평가 방식`, `정책 외부화 부족` 문제에 더 가깝다.

결론:

- 당장 base model 교체는 보류한다.
- 먼저 `정책/출력 계약/평가 체계`를 바로잡고 다시 본다.
- 그 다음에도 hidden/product gate에서 같은 의미 실패가 남으면 그때 model family 변경을 검토한다.

### B. 학습 방식 문제인가

판단: `그렇다. 가장 큰 문제 중 하나다.`

- corrective round가 점차 `남은 실패 2~4건`만 직접 고정하는 prompt chasing으로 변했다.
- validation은 현재 `task family당 1건`, 총 `14건`이라 회귀 탐지력이 매우 약하다.
- validation selection도 `earliest` 기준이라 대표성이 약하다.
- hard safety rule을 모델 prompt 안에 과하게 넣어 `정책 엔진`이 맡아야 할 책임이 모델 쪽으로 밀려 있다.
- 반대로 validator 외부화 시뮬레이션은 큰 개선을 보였다. 즉 현재 병목은 `모델 capability ceiling`보다 `hard rule ownership` 배치 문제에 더 가깝다.

결론:

- 다음 라운드부터는 `validation 14 고정`을 중단한다.
- 권장 split은 `validation_min_per_family=2`, `validation_ratio=0.15`, `validation_selection=spread`다.
- 현재 live head training `360건` 기준으로 위 split을 적용하면 validation은 `61건`, train은 `299건`이 된다.
- hard safety rule은 모델이 아니라 `policy/output validator`가 우선 강제해야 한다.
- 새 fine-tuning submit은 위 조건이 고정되기 전까지 중지한다.
- 다음 실험은 broad corrective tuning이 아니라 `validator 적용 전/후 동시 기록`, `runtime wiring`, `blind 잔여 2건 제거` 순서로 간다.
- 기본 경로에서 stale `combined_training_samples.jsonl`을 읽어 새 batch가 누락되던 파이프라인도 수정했다. 이제 `scripts/build_openai_sft_datasets.py`와 `scripts/report_risk_slice_coverage.py`는 현재 `training_sample_files()` 집합을 직접 읽는다.

### C. 데이터 부족 문제인가

판단: `그렇다. 하지만 총량보다 critical slice 부족이 본질이다.`

기존 training `194건` 기준으로는 critical slice가 얇았고, 현재는 targeted augmentation 후 `360건`으로 늘렸다.

전체 action 분포도 치우쳐 있다.

- `request_human_check`: `137`
- `create_alert`: `99`
- `pause_automation`: `46`
- `block_action`: `33`
- `enter_safe_mode`: `16`

- `action_recommendation`: `30`
- `rootzone_diagnosis`: `11`
- `sensor_fault`: `26`
- `climate_risk`: `10`
- `pest_disease_risk`: `6`
- `state_judgement`: `7`
- `safety_policy`: `34`
- `failure_response`: `36`
- `nutrient_risk`: `9`
- `robot_task_prioritization`: `48`
- `gt_master_dryback_high`: `6`
- `nursery_cold_humid_high`: `3`

문제는 다음 경계 사례 밀도가 낮다는 점이다.

- `manual_override + safe_mode`
- `worker_present / entry active`
- `core sensor stale/missing/inconsistent`
- `irrigation/source-water/dry-room path loss`
- `evidence incomplete -> unknown / approval_required`
- `robot_task enum exactness + target contract`
- `GT Master dry-back + 낮은 새벽 WC + 반복 잎 처짐`
- `Delta 6.5 nursery + post-sunset humid + leaf wet duration 증가`

결론:

- generic sample bulk-up은 비효율적이다.
- 사용자가 제안한 `robot_task 20+`는 이미 충족했고, 현재 raw count는 `48`이다.
- blind50 validator 잔여 `12건`은 `docs/blind50_residual_batch14_plan.md`와 batch14 sample `12건`으로 직접 training에 역투영했다.
- 하지만 실제 문제는 건수보다 `enum exactness`, `candidate_id/target`, `approval_required` 계약 품질이다.
- 아래 5개 slice를 우선 보강한다.
  - `safety_policy`: `+8`
  - `failure_response`: `+10`
  - `sensor_fault`: `+8`
  - `robot_task_prioritization`: `+8`
  - `rootzone_diagnosis/state_judgement`: `+8`
- 우선 보강 목표는 총 `+42` 내외다.

### D. eval 부족 문제인가

판단: `그렇다.`

- `core24`는 빠른 회귀 확인용으로는 유효하지만 제품 판단용으로는 너무 작다.
- `extended120`은 minimum gate로는 유효하지만, 제품화 기준으로는 여전히 작다.
- `extended200`과 blind holdout `50`을 확보한 뒤 재심사한 결과, `ds_v9`는 raw 기준 `0.51`, `0.32`까지 내려갔다.
- `extended160` 실패군 재분류 결과 전체 실패 `68건` 중 `34건`은 `policy_output_validator` 외부화 우선 대상으로 묶였고, `extended200`에서는 그 수가 `50건`까지 늘었다.
- 실제 시뮬레이션에서도 그 방향은 유효했다. `extended200`은 `151/200`, `blind_holdout50`은 `38/50`까지 회복됐다. 하지만 여전히 제품 승격 기준에는 못 미친다.

결론:

- `core24`는 그대로 유지한다.
- challenger 비교는 최소 `core24 + extended160 + extended200 + blind_holdout50`으로 올린다.
- 실제 재평가 결과 `ds_v9`는 `extended160 0.575`, `extended200 0.51`, `blind_holdout50 0.32`다.
- 제품 수준 주장에는 `extended200 + blind_holdout50 + product gate + shadow mode`가 필요하다.

## 3. 최종 판단

### 지금 당장 바꿔야 하는 것

1. `모델 변경`
- 지금은 하지 않는다.

2. `학습 방식 변경`
- 한다.
- prompt chasing 중지
- validation split 확대
- hard rule 외부화

3. `데이터 보강`
- 한다.
- total bulk-up이 아니라 critical slice 위주 `+42` 정도로 제한한다.

4. `eval 확장`
- 한다.
- `extended120`은 유지
- 다음 목표는 `extended160`
- 제품 주장 전 최종 목표는 `extended200 + blind_holdout50`

5. `validator 외부화`
- 한다.
- offline 시뮬레이션과 runtime skeleton으로 효과는 이미 확인됐다.
- 다음 단계는 runtime validator wiring과 blind 잔여 `2건` 제거다.

## 4. 실행 계획

### Phase 0. 즉시 중지

- 새 fine-tuning submit 중지
- `ds_v10`이 다시 재개되거나 후속 challenger가 생기더라도 `core24` 단독 점수로 champion 판단 금지
- `prompt_v9` 제출 보류

### Phase 1. 무지출 조치

- `scripts/report_eval_set_coverage.py`로 `product200` 목표와 blind holdout 규모를 함께 점검한다.
- `scripts/build_openai_sft_datasets.py` split 옵션을 `validation_ratio`와 `spread` 기준으로 강화한다.
- hard safety rule 10개와 robot/output contract 10개를 `docs/policy_output_validator_spec.md`로 고정한다.
- `scripts/simulate_policy_output_validator.py`로 `ds_v9` validator 적용 전/후 결과를 함께 기록하고 baseline 문서와 상태 문서에 고정한다.

### Phase 2. 저비용 데이터/평가 조치

- `extended200`과 blind holdout `50`까지 확장했고, 현재 총량 게이트는 통과했다.
- 현재 분포는 아래와 같다.
  - `expert_judgement`: `60`
  - `action_recommendation`: `28`
  - `forbidden_action`: `20`
  - `failure_response`: `24`
  - `robot_task`: `16`
  - `edge_case`: `28`
  - `seasonal`: `24`
- blind holdout은 `50`까지 확장 완료했다.
- 신규 training sample은 critical slice 중심으로 `+42` 내외만 추가한다.
- blind50 validator 적용 후 남는 실패 `12건`은 별도 ownership으로 분리한다.
  - validator로 줄일 수 없는 `risk_level` 경계 문제
  - validator를 붙여도 남는 `required_action_types`/`required_task_types` 문제

### Phase 3. 재평가

- 마지막 완료 모델부터 같은 기준으로 재평가한다.
- 순서:
  1. `ds_v9` 재평가 결과를 baseline으로 고정한다.
  2. `ds_v9` validator 적용 시뮬레이션 결과도 baseline으로 고정한다.
  3. `ds_v10`이 다시 실행되거나 후속 challenger가 생기면 같은 기준으로 비교한다.
  4. 새 challenger는 정책 validator를 붙인 결과와 순수 모델 결과를 함께 기록한다.

### Phase 4. 그 이후에만 fine-tuning 재개

아래가 충족될 때만 다음 submit을 허용한다.

- validation split 강화 완료
- `extended200` 확보
- blind holdout `50` 확보
- hard-rule validator 초안 완성
- targeted training slice 보강 완료
- runtime validator skeleton과 JSON/policy seed 초안 완료

## 5. 재개 조건과 모델 교체 조건

### fine-tuning 재개 조건

- `core24`는 append-only 유지
- `extended200` coverage 확보
- blind holdout `50` frozen set 확정
- validation rows가 최소 `28+`로 증가
- policy/output validator 초안 구현
- runtime validator skeleton과 JSON/policy seed 초안 완료

### base model 교체 검토 조건

아래가 모두 맞으면 그때 검토한다.

- 정책 validator를 붙여도 invariant miss가 계속 남는다.
- targeted data 보강 후에도 hidden/product gate가 개선되지 않는다.
- `risk_level` / action semantics가 작은 corrective tuning에 계속 크게 흔들린다.
- 같은 평가 세트에서 larger model이 cost 대비 의미 있는 일반화 이득을 보인다는 증거가 생긴다.

## 6. 결론

- 지금 문제의 중심은 `모델이 약해서`가 아니라 `평가와 학습 방식이 제품 목표와 어긋난 채 score chasing으로 흘렀다`는 점이다.
- validator 시뮬레이션과 runtime skeleton은 실제로 큰 개선을 만들었지만, 그 자체로 `0.95`와 `shadow mode pass`까지는 못 갔다.
- 따라서 다음 한 번의 fine-tuning보다 먼저 해야 할 일은 `validation 강화`, `extended200/blind50 baseline 고정`, `policy/output validator runtime 연결`, `blind50 validator 잔여 12건 제거`, `critical slice만 보강`이다.
- shadow mode도 이제 `not_run`을 넘어서야 한다. `llm-orchestrator/llm_orchestrator/runtime.py`, `scripts/build_shadow_mode_report.py`, `scripts/validate_shadow_mode_runtime.py`로 validator audit를 shadow-mode 승격 판단 형식까지 자동 요약할 수 있게 했다.
- 세부 기준은 `docs/risk_level_rubric.md`, `docs/critical_slice_augmentation_plan.md`, `scripts/report_risk_slice_coverage.py`에 고정한다.
- 제품 수준 주장은 `extended200 + blind_holdout50 + safety invariant 100% + field usability 100% + shadow mode` 전까지 하지 않는다.
