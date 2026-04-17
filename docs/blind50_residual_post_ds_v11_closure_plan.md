# blind_holdout50 validator residual post-closure 처리 계획

- 작성 시점: 2026-04-17
- 기준 모델: `ds_v11/prompt_v5_methodfix_batch14` (production frozen baseline)
- 기준 리포트: [validator_residual_failures_ds_v11_prompt_v5_methodfix_batch14_blind_holdout50.md](../artifacts/reports/validator_residual_failures_ds_v11_prompt_v5_methodfix_batch14_blind_holdout50.md)
- 전제: [artifacts/reports/fine_tune_iteration_final_postmortem.md](../artifacts/reports/fine_tune_iteration_final_postmortem.md) 기준 **fine-tune iteration은 공식 종결**(Phase K-1). ds_v12 / ds_v12.1 / ds_v11.B1 모두 ds_v11 baseline을 이기지 못했다. 따라서 추가 corrective training submit은 **이 라운드의 옵션이 아니다**.

## 1. 잔여 5건 요약

| eval_id | category | failed checks | owner | 처리 경로 |
|---|---|---|---|---|
| `blind-expert-001` | climate_risk | `risk_level_match` | risk_rubric_and_data | **rubric 강화 완료** |
| `blind-robot-004` | robot_task_prioritization | `risk_level_match` | risk_rubric_and_data | **rubric 강화 완료** |
| `blind-action-004` | action_recommendation | `forbidden_action_types_absent`, `required_action_types_present` | data_and_model | **dataset scale-up 이관** |
| `blind-expert-003` | nutrient_risk | `required_action_types_present` | data_and_model | **rubric 강화 완료**, validator 신규 규칙 보류 |
| `blind-expert-010` | rootzone_diagnosis | `forbidden_action_types_absent`, `required_action_types_present` | data_and_model | **dataset scale-up 이관** |

## 2. 케이스별 처리 결정

### `blind-expert-001` — Delta 6.5 nursery cold+humid post-sunset

- 기대: `risk_level=high`, 필수 `create_alert + request_human_check`, `adjust_vent` 금지
- 관측: 모델이 `medium`으로 undercall
- 처리: `docs/risk_level_rubric.md` §3 `high` + §5 빠른 판정 규칙에 이미 등재되어 있었다. 추가 조치는 없다. **validator 신규 규칙 보류** — `docs/policy_output_validator_spec.md` §8이 이 패턴을 score-chasing 우려로 명시적 out-of-scope로 분류하고 있기 때문이다.

### `blind-robot-004` — robot 후보 중 하나가 blocked

- 기대: `risk_level=high`, `skip_area` 먼저
- 관측: 모델이 `medium`으로 undercall
- 처리: `docs/risk_level_rubric.md` §4 `robot_task_prioritization` 섹션과 §5 빠른 판정 규칙에 **신규 명시 엔트리 추가**: "후보 중 하나가 blocked면 high, skip_area 먼저". 기존에는 "top-level risk_level보다 contract completeness가 더 중요"라는 문장으로 애매했다. 이제는 risk_level도 같이 맞추라고 명시했다.

### `blind-action-004` / `blind-expert-010` — GT Master dry-back

- 기대: `forbidden_action_types=[adjust_fertigation]`, 필수 `create_alert + request_human_check`
- 관측: 모델이 `adjust_fertigation` 포함, 필수 action 누락
- 처리: Phase F Cluster B로 식별된 패턴이다. batch22 cluster B 24건으로 이미 corrective sample 생성·검증했으나 ds_v12/ds_v12.1/ds_v11.B1 fine-tune 실패로 인해 미적용 상태다. **dataset scale-up 프로젝트 착수 시 재투입**한다. 이 라운드에서는 rubric(이미 `high + create_alert + request_human_check`) + `docs/policy_output_validator_spec.md` §8(validator out-of-scope) 경계를 유지한다.

### `blind-expert-003` — GT Master EC gradient > 2.5 + drain rate 낮음

- 기대: `risk_level=high`, 필수 `create_alert + request_human_check`, `observe_only` 금지
- 관측: 모델이 필수 action 누락
- 처리: `docs/risk_level_rubric.md` §3 `high`, §5 빠른 판정 규칙, §4 `rootzone_diagnosis / nutrient_risk` 섹션에 **신규 명시 엔트리 추가**: "`feed EC 대비 drain EC 차이 2.0mS/cm 이상 + drain 비율 20% 미만` → `high`, `create_alert + request_human_check` 필수, `observe_only` 단독 금지". validator 신규 규칙은 **보류**. §8 score-chasing 원칙 유지.

## 3. validator 신규 규칙을 쓰지 않는 이유

`docs/policy_output_validator_spec.md` §8은 `GT Master dry-back` 및 `Delta 6.5 nursery cold+humid` 패턴을 validator scope **밖**으로 확정했다. 근거는:

- 이 패턴들은 hard safety invariant가 아니라 도메인 의미 일반화 문제다.
- validator로 덮기 시작하면 score chasing 규칙이 되고 제품 일반화에 불리하다.

따라서 이번 라운드는 rubric 명시 보강으로 제한하고, 실제 동작 개선은:
- (a) 운영 중 `shadow mode` 실트래픽 수집으로 실제 operator agreement 데이터 누적
- (b) 향후 dataset scale-up 프로젝트에서 batch22 + 추가 variation 재투입
두 경로로 밀어낸다.

## 4. 예상 개선

rubric 변경만으로는 **ds_v11 모델의 출력은 바뀌지 않는다**. 이유는 fine-tune iteration이 종결됐기 때문이다. 다만 본 rubric 강화는:

- 향후 dataset scale-up 프로젝트의 라벨 기준을 명확히 한다.
- 추가 human review / shadow mode case capture 시 operator agreement 판정 기준을 통일한다.
- validator scope 경계가 명문화되어 다른 에이전트가 실수로 HSV 규칙을 추가하는 것을 막는다.

## 5. blind50 validator pass rate 변화

rubric 변경은 validator pass rate를 직접 바꾸지 않는다. `validate_policy_output_validator` 재실행은 OpenAI 재호출을 요구하지 않으므로 이번 라운드에서 구조적으로 변화 없음을 재확인할 수 있다. 수치 비교는 생략한다(변화 없음이 예상된 결과).

## 6. 후속 트리거

이 계획의 다음 갱신 시점은 다음 중 빠른 쪽이다.

- `artifacts/runtime/llm_orchestrator/shadow_mode_real_sample_window.jsonl`에 operator 판정이 **최소 50건** 누적된 경우 — 실트래픽 기준으로 잔여 5건 패턴이 실제로 반복되는지 재평가한다.
- dataset scale-up 프로젝트(기존 346 rows → 3-5배) 착수가 승인되는 경우 — batch22 sample과 본 계획의 5건을 모두 포함한 재학습 설계로 이관한다.
