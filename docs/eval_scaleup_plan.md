# Eval Scale-up Plan

이 문서는 적고추 스마트팜 운영 전문가 AI Agent의 fine-tuning / champion 승격 / 제품화 판단에 사용할 평가셋을 `24건`에서 `100~200건` 규모로 확장하는 기준을 고정한다.

## 1. 왜 지금 필요한가

- 현재 운영형 fine-tuning benchmark는 총 `24건`이다.
- 현재 최고 성능은 `pass_rate 0.875`이며, `24건` 기준으로는 케이스 1건이 `0.0417`을 움직인다.
- 이 규모에서는 corrective sample 몇 건으로도 점수가 쉽게 흔들리고, `fail-set churn`과 과적합성 보강을 구분하기 어렵다.
- 따라서 `24건` benchmark는 **빠른 회귀 확인용 core regression set**으로만 유지하고, 승격/제품화 판단은 더 큰 extended benchmark에서 수행해야 한다.

## 2. 현재 기준선

현재 file별 eval row 수는 아래와 같다.

- `expert_judgement_eval_set.jsonl`: `8`
- `action_recommendation_eval_set.jsonl`: `2`
- `forbidden_action_eval_set.jsonl`: `2`
- `failure_response_eval_set.jsonl`: `2`
- `robot_task_eval_set.jsonl`: `2`
- `edge_case_eval_set.jsonl`: `4`
- `seasonal_eval_set.jsonl`: `4`
- 합계: `24`

## 3. 운영 원칙

1. 현재 `24건`은 `core regression set`으로 동결한다.
2. 앞으로 추가하는 케이스는 기존 `eval_id`를 바꾸지 않고 append-only로 관리한다.
3. fine-tuning challenger 승격은 `core24 + extended120+`를 동시에 통과해야 한다.
4. `ds_v10` 이후에는 `extended120` 게이트를 통과하기 전까지 새 fine-tuning submit을 기본적으로 중지한다.
5. 제품화 판단은 `extended160` 이상에서 다시 시작하되, 최종 제품 수준 주장은 `extended200`과 blind holdout 확장까지 포함한다.
6. 제품화 승격은 `extended120/160`만으로 결정하지 않고 별도 `blind holdout + safety invariant + field usability + shadow mode` 게이트를 함께 통과해야 한다.

## 4. 목표 규모

### 4.1 최소 운영 게이트

`extended120`을 최소 게이트로 사용한다.

- `expert_judgement_eval_set.jsonl`: `40`
- `action_recommendation_eval_set.jsonl`: `16`
- `forbidden_action_eval_set.jsonl`: `12`
- `failure_response_eval_set.jsonl`: `12`
- `robot_task_eval_set.jsonl`: `8`
- `edge_case_eval_set.jsonl`: `16`
- `seasonal_eval_set.jsonl`: `16`
- 총합: `120`

### 4.2 권장 제품화 게이트

`extended160`을 권장 게이트로 사용한다.

- `expert_judgement_eval_set.jsonl`: `40~56`
- `action_recommendation_eval_set.jsonl`: `16~24`
- `forbidden_action_eval_set.jsonl`: `12~16`
- `failure_response_eval_set.jsonl`: `12~16`
- `robot_task_eval_set.jsonl`: `8~12`
- `edge_case_eval_set.jsonl`: `16~24`
- `seasonal_eval_set.jsonl`: `16~24`
- 총합: `120~172`

### 4.3 최종 제품 주장 게이트

`extended200`을 최종 제품 주장 게이트로 사용한다.

- `expert_judgement_eval_set.jsonl`: `60`
- `action_recommendation_eval_set.jsonl`: `28`
- `forbidden_action_eval_set.jsonl`: `20`
- `failure_response_eval_set.jsonl`: `24`
- `robot_task_eval_set.jsonl`: `16`
- `edge_case_eval_set.jsonl`: `28`
- `seasonal_eval_set.jsonl`: `24`
- 총합: `200`

## 5. 우선 확장 순서

성능 정체와 제품화 리스크를 같이 줄이려면 아래 순서로 늘린다.

1. `expert_judgement`
현재 `8건`으로 너무 작다. `rootzone_diagnosis`, `nutrient_risk`, `sensor_fault`, `pest_disease_risk`, `safety_policy`의 risk calibration을 우선 확장한다.

2. `failure_response`
현재 `2건`이라 `sensor stale`, `communication_loss`, `readback mismatch`, `safe_mode` 같은 운영형 failure를 대표하지 못한다.

3. `action_recommendation` / `forbidden_action`
현재 각 `2건`이라 `required_action_types_present`, `approval_required`, `block_action` 회귀를 잡기 어렵다.

4. `edge_case` / `seasonal`
현재 각 `4건`으로 product gate를 논하기엔 부족하다. `manual_override`, `worker_present`, `spring transplant`, `summer flowering`, `dry-room watch`를 추가한다.

5. `robot_task`
현재 우선순위는 낮지만 최소 `8건`까지는 확보한다.

## 6. 즉시 실행 tranche

### Tranche 1

`24 -> 60+`로 먼저 올린다.

- `expert_judgement`: `8 -> 20`
- `action_recommendation`: `2 -> 10`
- `forbidden_action`: `2 -> 8`
- `failure_response`: `2 -> 8`
- `robot_task`: `2 -> 6`
- `edge_case`: `4 -> 10`
- `seasonal`: `4 -> 10`

### Tranche 2

`60+ -> 120`까지 확장한다.

- `expert_judgement`: `20 -> 40`
- `action_recommendation`: `10 -> 16`
- `forbidden_action`: `8 -> 12`
- `failure_response`: `8 -> 12`
- `robot_task`: `6 -> 8`
- `edge_case`: `10 -> 16`
- `seasonal`: `10 -> 16`

## 7. 통과 기준

### Fine-tuning 재개 기준

- `core24`는 유지
- `extended120` 이상 확보
- safety/failure 계열 최소치 충족:
  - `forbidden_action >= 12`
  - `failure_response >= 12`
  - `edge_case >= 16`
  - `seasonal >= 16`

### 제품화 판단 기준

- `extended160` 이상 확보
- 최종 제품 주장 전 `extended200` 확보
- `strict_json_rate = 1.0`
- `safety_policy`, `forbidden_action`, `failure_response` 치명 miss `0건`
- 전체 `pass_rate >= 0.95`
- 별도 shadow mode / approval mode 로그 검증 통과
- `blind_holdout_pass_rate >= 0.95`
- blind holdout rows `>= 50`
- safety invariant failed case `0건`
- field usability contract failed case `0건`

## 8. Blind Holdout 운영

- `evals/blind_holdout_eval_set.jsonl`은 corrective tuning에 사용하지 않는 별도 frozen 세트다.
- 현재 1차 blind holdout은 `24건`이며, Grodan `Delta 6.5 / GT Master`, 관수·원수 경로 장애, 작업자/override/safe_mode, robot task contract를 집중 점검한다.
- 제품 수준 주장을 위해 blind holdout은 `50+`까지 확장한다.
- blind holdout은 `extended120` coverage와 별개로 운영한다. 즉, `extended120`이 높아도 blind holdout이 낮으면 제품화 승격을 금지한다.

## 9. 운영 도구

즉시 점검용으로 아래 도구를 사용한다.

- `python3 scripts/report_eval_set_coverage.py`
- `python3 scripts/build_eval_jsonl.py --include-source-file`
- `python3 scripts/build_blind_holdout_eval_set.py`
- `python3 scripts/validate_product_readiness_gate.py`

`scripts/report_eval_set_coverage.py --enforce-minimums`는 `extended120` 기준을 아직 못 넘으면 non-zero exit code를 반환한다.
