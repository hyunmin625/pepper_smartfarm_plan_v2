# policy-engine

hard block, approval required, manual mode only 정책을 평가하는 서비스 자리다.

현재 포함된 구현 범위:

- policy_engine/output_validator.py: LLM 출력 직후 hard safety/output contract를 강제하는 runtime validator
- policy_engine/loader.py: enabled rule catalog loader와 FilePolicySource/StaticPolicySource/DB source 연결점
- policy_engine/evaluator.py: runtime 정책 DSL(field/operator/value, all/any/not, scope, target_action_types)을 평가하는 공통 evaluator
- policy_engine/precheck.py: dispatch 직전 request/raw context를 다시 읽어 blocked / approval_required / pass를 결정하는 precheck evaluator
- ../schemas/policy_output_validator_rules_schema.json: validator/runtime rule catalog schema
- ../data/examples/policy_output_validator_rules_seed.json: HSV-01~HSV-10, OV-01~OV-10, POL-* seed rule catalog
- ../data/examples/policy_output_validator_cases.jsonl: worker lock, rootzone conflict, climate degraded, robot clearance, approval contract 샘플
- ../scripts/validate_policy_output_validator.py: runtime validator 회귀 검증
- ../scripts/validate_policy_engine_precheck.py: loader/precheck 회귀 검증
- ../scripts/validate_policy_engine_runtime_policies.py: runtime 정책 DSL과 기본 정책 회귀 검증
- ../llm-orchestrator/llm_orchestrator/runtime.py: LLM output -> validator -> audit log wiring skeleton
- ../scripts/validate_llm_output_validator_runtime.py: orchestrator wiring 회귀 검증

현재 연결 상태:

1. llm-orchestrator 출력은 output_validator를 거쳐 audit log에 남는다.
2. execution-gateway는 policy_engine.precheck로 request/raw context를 다시 읽고 policy_result/policy_ids를 재계산한다.
3. 기존 HSV precheck는 HSV-04 관수 경로 degraded block, HSV-09 rootzone conflict fertigation approval escalation 같은 dispatch 전 보수 규칙을 담당한다.
4. runtime evaluator는 POL-* 기본 정책을 함께 평가한다. 현재 포함 범위는 hard block, approval, range limit, scheduling, sensor quality, robot safety다.
5. POL-* 규칙의 condition/scope/target_action_types는 enforcement_json 안에 저장하므로 파일 source와 DB source가 같은 evaluator 경로를 사용한다.

다음 단계:

1. runtime 정책을 ops UI에서 생성/편집하는 전용 화면으로 승격
2. blocked / approval_required event를 runtime bus와 audit log에 분리 저장
3. state constraint / robot constraint evaluator를 실제 sensor snapshot 입력과 더 촘촘히 연결
