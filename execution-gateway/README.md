# Execution Gateway Skeleton

이 디렉터리는 일반 장치 명령과 override 요청을 normalize하고, duplicate/cooldown/approval/policy 재검사를 수행하는 준비 코드다.

## 포함 범위

- device command / override request contract 로드
- request normalizer
- duplicate detector
- cooldown manager
- hard-coded safety guard (`worker_present`, `sensor_quality blocked`, active interlocks)
- policy precheck (`policy-engine` seed rule catalog 재평가)
- approval / policy / manual override / estop guard
- control state store
- execution dispatcher
- audit log writer
- dispatch demo

## 현재 검증 범위

- `scripts/validate_execution_gateway_flow.py`
  - preflight reject/ready 경로
  - `HSV-04` path degraded block, `HSV-09` fertigation approval escalation 확인
- `scripts/validate_execution_dispatcher.py`
  - `override -> state update -> device block -> adapter dispatch -> audit log`
  - dispatch 직전 policy precheck reject 경로 확인

## 실행 예시

```bash
python3 execution-gateway/demo.py
python3 scripts/validate_execution_gateway_flow.py
python3 scripts/validate_execution_dispatcher.py
```
