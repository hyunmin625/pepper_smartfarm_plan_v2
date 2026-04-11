# Glossary

이 문서는 저장소에서 반복해서 쓰는 핵심 용어를 고정한다.

- `zone`: 제어와 센서 수집의 기본 운영 구역
- `sensor`: 계측 장치 하나의 논리 식별 단위
- `device`: 제어 대상 액추에이터 또는 설비 단위
- `model_profile`: 센서/장치 타입별 동작 계약
- `Device Profile`: 장치 action, parameter, ack, interlock 기준
- `site override`: 현장별 controller/channel binding
- `channel_ref`: logical PLC 채널 식별자
- `transport_ref`: 실제 transport read/write key
- `farm_case`: 운영 로그에서 승격된 현장 사례 지식
- `shadow mode`: 실제 실행 없이 판단만 평가하는 운영 모드
- `approval mode`: 승인된 명령만 제한 실행하는 운영 모드
- `limited auto mode`: 제한된 저위험 액션만 자동 실행하는 운영 모드
- `hard block`: 어떤 경우에도 자동 실행하면 안 되는 규칙
- `cooldown`: 동일 액션 재실행을 제한하는 대기 기간
