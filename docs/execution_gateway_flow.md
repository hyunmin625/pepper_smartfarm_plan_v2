# Execution Gateway Flow

이 문서는 `execution-gateway`가 장치 명령과 override 요청을 어떤 순서로 검증하는지 정의한다.

## 1. 입력 유형

- 일반 장치 명령: `docs/execution_gateway_command_contract.md`
- override 요청: `docs/execution_gateway_override_contract.md`

## 2. 검증 단계

1. schema validation
2. range validation
3. device availability / target scope check
4. duplicate action check
5. cooldown check
6. policy re-evaluation
7. approval routing
8. audit logging
9. dispatcher 전달

## 3. 현재 구현 기준

- range validation
  - 일반 장치 명령은 `Device Profile.parameter_specs`의 min/max/enum을 그대로 사용한다.
  - clamp는 하지 않고 즉시 reject한다.

- duplicate action check
  - `device_command`: `device:{device_id}:{action_type}`
  - `override`: `override:{scope_type}:{scope_id}:{override_type}`
  - 최근 동일 key가 중복되면 reject한다.

- cooldown check
  - dedupe key와 동일한 key를 사용한다.
  - cooldown active면 reject한다.

- policy re-evaluation
  - `policy_snapshot.policy_result=blocked`면 reject
  - `approval_required` 또는 `policy_result=approval_required`면 승인 상태를 다시 본다.

- approval routing
  - 장치 명령은 `approval_context.approval_status=approved`일 때만 통과한다.
  - override 중 `manual_override_release`, `emergency_stop_reset_request`, `auto_mode_reentry_request`는 승인 완료가 필요하다.

- audit logging
  - 최소 필드: `request_id`, `request_kind`, `status`, `dedupe_key`, `reasons`

- dispatcher 전달
  - `device_command`는 adapter bridge를 통해 `plc-adapter`로 전달한다.
  - `control_override`는 장치 write가 아니라 `ControlStateStore` 상태 전이로 처리한다.
  - dispatch 결과는 `artifacts/runtime/execution_gateway/dispatch_audit.jsonl`에 남긴다.

## 4. 구현 연결

- `execution-gateway/execution_gateway/contracts.py`
- `execution-gateway/execution_gateway/normalizer.py`
- `execution-gateway/execution_gateway/guards.py`
- `execution-gateway/execution_gateway/dispatch.py`
- `execution-gateway/execution_gateway/state.py`
- `execution-gateway/demo.py`
- `scripts/validate_execution_gateway_flow.py`
- `scripts/validate_execution_dispatcher.py`
- `docs/approval_governance.md`
