# policy-engine

hard block, approval required, manual mode only 정책을 평가하는 서비스 자리다.

현재 포함된 skeleton:

- `policy_engine/output_validator.py`: LLM 출력 직후 hard safety/output contract를 강제하는 runtime validator
- `../schemas/policy_output_validator_rules_schema.json`: validator rule catalog schema
- `../data/examples/policy_output_validator_rules_seed.json`: `HSV-01`~`HSV-10`, `OV-01`~`OV-10` seed rule catalog
- `../data/examples/policy_output_validator_cases.jsonl`: worker lock, rootzone conflict, climate degraded, robot clearance, approval contract 샘플
- `../scripts/validate_policy_output_validator.py`: runtime validator 회귀 검증

다음 단계:

1. LLM orchestrator 출력 직후 `output_validator.apply_output_validator()`를 연결
2. `validator_reason_codes`, `validator_decision`을 audit log와 shadow mode report에 남김
3. 이후 policy evaluator와 approval router를 같은 request envelope 안에서 이어 붙임
