# Policy Output Validator Spec

이 문서는 `LLM 출력 -> output validator -> policy-engine -> execution-gateway` 흐름에서, 모델 밖으로 강제해야 할 규칙을 고정한다.

목적은 두 가지다.

- hard safety invariant를 prompt나 corrective sample에 덜 의존하게 만든다.
- `ds_v9` `extended160` 재평가에서 반복된 실패를 `validator`, `risk rubric/data`, `output contract`로 분리해 다음 조치 우선순위를 고정한다.

## 1. 왜 지금 필요한가

`artifacts/reports/eval_failure_clusters_ds_v9_prompt_v5_methodfix_extended160.md` 기준:

- 전체 실패는 `68건`이다.
- 이 중 `34건`은 `policy_output_validator` 우선 규칙으로 직접 줄일 수 있다.
- top validator-priority root cause는 아래 4개다.
  - `pause_automation_missing_on_degraded_control_signal`: `13`
  - `block_action_missing_on_safety_lock`: `11`
  - `safe_mode_pair_missing_on_path_or_comms_loss`: `7`
  - `robot_task_enum_drift`: `3`
- 별도로 `citations_missing_in_actionable_output 20건`은 model intelligence보다 output contract 문제다.

즉, 현재 병목은 새 prompt나 새 corrective tuning보다 `안전 차단/감속 pair 강제`, `robot contract 강제`, `citation/follow_up contract 강제`를 모델 밖으로 빼는 쪽이다.

## 2. 배치 위치

validator는 JSON parse 직후, `policy-engine` 전에 실행한다.

1. LLM이 `parsed_output` 생성
2. output validator가 schema/enum/contract/hard rule을 검사
3. 위반 시 아래 중 하나를 수행
   - `reject_to_manual_review`
   - `strip_forbidden_actions`
   - `force_safe_action_pair`
   - `escalate_to_approval_required`
   - `reject_robot_task`
4. 이후 policy-engine과 execution-gateway가 저수준 dispatch 가능 여부를 다시 판단

원칙:

- validator는 `unsafe output`을 실행 가능한 형태로 통과시키지 않는다.
- hard safety는 가능한 한 `rewrite`보다 `reject or force-safe-pair`를 우선한다.
- validator mutation은 모두 `validator_reason_codes`로 감사 로그에 남긴다.

## 3. Hard Safety Rules 10

| id | trigger | validator enforcement | 비고 |
|---|---|---|---|
| `HSV-01` | `worker_present` 또는 worker-entry active | `risk_level=critical`, `block_action + create_alert` 강제, device-control/robot task 제거 | 사람-기계 충돌 방지 |
| `HSV-02` | `manual_override` active | AI device control 제거, `block_action + create_alert` 강제 | 수동 모드 덮어쓰기 금지 |
| `HSV-03` | `manual_override`와 `safe_mode` 동시 active | 모든 추가 제어 제거, `block_action + create_alert` 강제, `enter_safe_mode` 재출력 금지 | latch 상태 유지 |
| `HSV-04` | 관수 펌프/관수 메인 밸브 통신 손실 또는 readback mismatch | `risk_level=critical`, `enter_safe_mode + request_human_check` 강제 | `pause_automation`만으로 통과 금지 |
| `HSV-05` | 원수 메인 밸브 write timeout 또는 stale readback | `risk_level=critical`, `enter_safe_mode + request_human_check` 강제 | source-water path 보호 |
| `HSV-06` | 건조실 fan/dehumidifier 통신 손실 또는 readback mismatch | `risk_level=critical`, `enter_safe_mode + request_human_check` 강제 | 건조 품질 손상 선차단 |
| `HSV-07` | 핵심 기후 센서 stale/missing/inconsistent로 VPD/제어 해석 불가 | `risk_level=unknown`, `pause_automation + request_human_check` 강제 | damage confirmed 전까지 unknown 유지 |
| `HSV-08` | 근권 WC/drain EC/loadcell 충돌 또는 stale로 자동 관수/양액 근거 붕괴 | `risk_level=unknown`, `pause_automation + request_human_check` 강제, `short_irrigation`/`adjust_fertigation` 제거 | GT Master/Delta 6.5 포함 |
| `HSV-09` | EC/pH/drain sensor fault 상태에서 fertigation 변경 제안 또는 forbidden_action 심사 | 자동 승인 금지, `decision=approval_required` 또는 action `approval_required=true` 강제 | hard interlock이 있으면 `block` 허용 |
| `HSV-10` | worker present, zone clearance uncertain, aisle slip hazard, safe_mode active 중 하나에서 robot task 생성 | `harvest_candidate_review`/`inspect_crop` 제거, 필요 시 `skip_area`만 허용 | robot safety interlock |

적용 우선순위:

- `HSV-01`~`HSV-06`은 `rewrite_to_safe_pair`가 허용된다.
- `HSV-07`~`HSV-10`은 unsafe action을 제거하고 `manual_review` 또는 `approval_required`로 보내는 쪽을 우선한다.

## 4. Approval / Output Contract Rules 10

| id | rule | validator enforcement | 비고 |
|---|---|---|---|
| `OV-01` | `action_type`은 허용 enum만 사용 | 미허용 action이면 reject | `maintain`, `hold` 금지 |
| `OV-02` | `robot_task.task_type`은 허용 enum만 사용 | 미허용 task면 reject | generic `create_robot_task` 금지 |
| `OV-03` | `recommended_actions[]`는 `action_type`, `reason`, `risk_level`, `target`, `approval_required`, `expected_effect`, `cooldown_minutes` 필수 | 누락 시 reject | field usability 계약 |
| `OV-04` | `robot_tasks[]`는 `task_type`, `priority`, `reason`, `approval_required`, `candidate_id` 또는 `target` 필수 | 누락 시 reject | `candidate_id/target` 없으면 unusable |
| `OV-05` | actionable output은 `follow_up` 또는 `required_follow_up` 필수 | 누락 시 reject | blind/product gate와 정렬 |
| `OV-06` | `retrieved_context`가 있고 `must_include_citations=true`면 citation 필수 | 누락 시 reject 또는 manual review | 현재 `20건` 반복 실패 |
| `OV-07` | `forbidden_action`은 `decision in {allow, block, approval_required}`와 `blocked_action_type` 계약 준수 | 위반 시 reject | schema-level hard contract |
| `OV-08` | `adjust_fertigation`, `adjust_heating`, `adjust_co2`, `create_robot_task`는 기본 `approval_required=true` | false면 `approval_required=true`로 승격 | 승인 거버넌스와 정렬 |
| `OV-09` | top-level `risk_level`과 action/task item `risk_level`이 safety rule보다 낮아지면 안 됨 | undercall 시 reject | 최소 동일 수준 유지 |
| `OV-10` | validator가 strip/rewrite/reject를 수행하면 `validator_reason_codes`와 `validator_decision`을 남긴다 | audit log 필수 | shadow mode 분석용 |

## 5. Model vs Validator Ownership

모델이 계속 맡아야 하는 것:

- 상황 요약과 도메인 진단 문장
- `high` vs `medium` 경계처럼 rubric 기반의 회색지대 판단
- `inspect_crop` vs `manual_review` 같은 로봇 작업 우선순위 판단
- follow-up 설명과 citation 선택

validator가 우선 맡아야 하는 것:

- `block_action`, `pause_automation`, `enter_safe_mode` 같은 interlock pair 강제
- `worker_present`, `manual_override`, `safe_mode` 아래서 unsafe action strip
- evidence gap 아래 `short_irrigation`, `adjust_fertigation`, `create_robot_task` 차단
- robot task enum, `candidate_id/target`, citation/follow_up contract 강제

## 6. 다음 구현 범위

1. `scripts/report_eval_failure_clusters.py` 결과를 기준으로 `HSV-01`~`HSV-10`, `OV-01`~`OV-10`을 JSON seed로 옮긴다.
2. `scripts/validate_product_readiness_gate.py` 앞단에 output validator 시뮬레이터를 붙여 `순수 모델 결과`와 `validator 적용 결과`를 함께 기록한다.
3. 후속 challenger 비교는 `core24 + extended160 + blind_holdout + validator-applied gate` 기준으로만 수행한다.

## 7. 관련 문서

- `docs/productization_promotion_gate.md`
- `docs/model_product_readiness_reassessment.md`
- `docs/risk_level_rubric.md`
- `docs/approval_governance.md`
- `artifacts/reports/eval_failure_clusters_ds_v9_prompt_v5_methodfix_extended160.md`
