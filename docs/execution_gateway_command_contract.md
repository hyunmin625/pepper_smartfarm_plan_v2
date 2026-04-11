# Execution Gateway Command Contract

이 문서는 `execution-gateway`가 `plc-adapter`로 넘기는 저수준 장치 명령 요청 형식을 정의한다.

## 1. 목적

- LLM 추천 액션과 실제 장치 실행 요청을 분리한다.
- `device_id`, `action_type`, `parameters`, 승인/정책 문맥을 명시적으로 남긴다.
- `execution-gateway`가 schema validation, device availability check, policy 재평가를 수행한 뒤에만 `plc-adapter`를 호출하도록 한다.

## 2. 필수 필드

- `schema_version`
- `request_id`
- `issued_at`
- `farm_id`
- `zone_id`
- `device_id`
- `action_id`
- `action_type`
- `parameters`
- `approval_required`
- `requested_by`
- `source_decision_id`

## 3. 규칙

1. `action_type`은 `schemas/action_schema.json` enum 안에 있어야 한다.
2. `device_id`는 `data/examples/sensor_catalog_seed.json`에 존재해야 한다.
3. `device_id`가 참조하는 `model_profile`의 `supported_action_types`에 해당 `action_type`이 포함돼야 한다.
4. `approval_required=true`이면 `approval_context.approval_status`가 `approved` 또는 `pending`이어야 한다.
5. 실제 write 직전에는 `execution-gateway`가 `policy_snapshot`, `operator_context`, `cooldown_context`를 다시 검토한다.

## 4. 연결 파일

- `schemas/device_command_request_schema.json`
- `data/examples/device_command_request_samples.jsonl`
- `scripts/validate_device_command_requests.py`
