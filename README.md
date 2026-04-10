# Pepper Smartfarm Plan V2

적고추(건고추) 온실 스마트팜 운영을 위한 농업용 LLM/제어 시스템 개발 계획 저장소입니다.

현재 이 저장소는 구현 코드가 아니라 계획, 일정, 작업 로그를 관리하는 문서 저장소입니다.

## 빠른 시작

다른 AI/에이전트는 아래 순서로 문서를 읽으면 됩니다.

1. `PROJECT_STATUS.md`: 현재 진행 상태, 핵심 결정, 다음 우선순위
2. `PLAN.md`: 전체 시스템 목표, 아키텍처, 안전 원칙
3. `schedule.md`: 8주 실행 일정
4. `todo.md`: 세부 작업 체크리스트
5. `WORK_LOG.md`: 진행한 작업과 커밋 이력
6. `AGENTS.md`: 문서 작성, 커밋, 보안, 작업 규칙

## 핵심 방향

- LLM은 상위 판단과 계획만 담당한다.
- 실시간 제어는 PLC, 정책 엔진, 실행 게이트, 상태기계가 담당한다.
- RAG는 재배 매뉴얼, 현장 SOP, 정책 문서처럼 바뀔 수 있는 지식을 담당한다.
- 파인튜닝은 JSON 출력, `action_type` 선택, 안전 거절, follow_up 같은 운영 행동 양식을 담당한다.
- 모든 실행은 policy-engine과 execution-gateway를 통과해야 한다.

## 현재 단계

현재는 구현 전 기획 단계입니다. 다음 우선순위는 `state_schema.json`, `action_schema.json`, `action_type` enum, RAG 문서 메타데이터, 초기 정책 JSON, 행동추천/금지행동 샘플 작성입니다.
