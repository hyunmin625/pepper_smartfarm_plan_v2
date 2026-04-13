# policy-engine

hard block, approval required, manual mode only 정책을 평가하는 서비스 자리다.

현재 포함된 구현 범위:

- `policy_engine/output_validator.py`: LLM 출력 직후 hard safety/output contract를 강제하는 runtime validator
- `policy_engine/loader.py`: enabled rule catalog loader
- `policy_engine/precheck.py`: dispatch 직전 request/raw context를 다시 읽어 `blocked / approval_required / pass`를 결정하는 precheck evaluator
- `../schemas/policy_output_validator_rules_schema.json`: validator rule catalog schema
- `../data/examples/policy_output_validator_rules_seed.json`: `HSV-01`~`HSV-10`, `OV-01`~`OV-10` seed rule catalog
- `../data/examples/policy_output_validator_cases.jsonl`: worker lock, rootzone conflict, climate degraded, robot clearance, approval contract 샘플
- `../scripts/validate_policy_output_validator.py`: runtime validator 회귀 검증
- `../scripts/validate_policy_engine_precheck.py`: loader/precheck 회귀 검증
- `../llm-orchestrator/llm_orchestrator/runtime.py`: `LLM output -> validator -> audit log` wiring skeleton
- `../scripts/validate_llm_output_validator_runtime.py`: orchestrator wiring 회귀 검증

현재 연결 상태:

1. `llm-orchestrator` 출력은 `output_validator`를 거쳐 audit log에 남는다.
2. `execution-gateway`는 `policy_engine.precheck`로 request/raw context를 다시 읽고 `policy_result/policy_ids`를 재계산한다.
3. 현재 precheck는 `HSV-04` 관수 경로 degraded block, `HSV-09` rootzone conflict fertigation approval escalation 같은 dispatch 전 보수 규칙을 담당한다.

다음 단계:

1. ops DB나 파일에서 정책 카탈로그를 동적으로 읽는 policy source abstraction 추가
2. blocked / approval_required event를 runtime bus와 audit log에 분리 저장
3. state constraint / robot constraint evaluator 확장
