# 저장소 가이드라인

## 프로젝트 구조와 문서 구성

이 저장소는 온실 스마트팜 고추 재배 자동화를 위한 농업용 LLM/제어 시스템의 기획 문서 저장소입니다.

- `PLAN.md`: 프로젝트 목표, 시스템 아키텍처, 안전 원칙, 단계별 개발 계획
- `README.md`: 저장소 목적과 문서 탐색 순서
- `todo.md`: 실제 개발 착수를 위한 세부 작업 목록
- `schedule.md`: 8주 실행 일정과 주차별 완료 기준
- `PROJECT_STATUS.md`: 현재 진행 상태, 핵심 결정, 다음 우선순위
- `WORK_LOG.md`: 주요 변경 작업과 조사 근거 기록
- `AGENTS.md`: 저장소 기여 및 작업 기준

새 AI/에이전트는 먼저 `README.md`와 `PROJECT_STATUS.md`를 읽고, 세부 근거가 필요할 때 `PLAN.md`, `todo.md`, `schedule.md`, `WORK_LOG.md` 순서로 확인합니다.

현재는 구현 코드가 없으므로 루트의 Markdown 문서가 핵심 산출물입니다. 구현이 시작되면 `todo.md`의 계획에 맞춰 `docs/`, `data/`, `experiments/`, `infra/`와 서비스 디렉터리(`sensor-ingestor/`, `state-estimator/`, `policy-engine/`, `llm-orchestrator/`, `execution-gateway/`)를 추가합니다.

## 빌드, 테스트, 개발 명령

현재 별도 빌드 시스템이나 테스트 러너는 없습니다. 문서 변경 시 아래 명령으로 기본 확인을 수행합니다.

- `rg "TODO|TBD" *.md`: 남아 있는 미정 항목 확인
- `sed -n '1,120p' PLAN.md`: 주요 문서 앞부분 확인
- `git status -sb`: 커밋 전 변경 파일 확인

코드가 추가되면 실제 실행 명령을 이 문서와 `README.md`에 함께 기록합니다. 예: `pytest`, `docker compose up`, `npm test`.

## 작성 스타일과 명명 규칙

문서는 짧고 명확한 제목, 간결한 bullet list, 실행 가능한 설명을 사용합니다. 기존 문서의 한국어 도메인 용어는 유지하고, 기계가 읽는 식별자는 영어를 사용합니다.

향후 디렉터리 이름은 kebab-case를 권장합니다. 예: `policy-engine`, `robot-task-manager`. JSON 필드와 내부 식별자는 snake_case를 사용합니다. 예: `zone_id`, `sensor_id`, `device_id`, `action_type`.

## 테스트 기준

아직 자동화 테스트는 없습니다. 구현이 시작되면 안전과 운영 안정성에 직접 영향을 주는 모듈부터 테스트합니다.

우선 테스트 대상은 schema validation, VPD 계산, trend 계산, policy evaluator, action validator, duplicate detector, cooldown manager입니다. 테스트 이름은 기대 동작이 드러나게 작성합니다. 예: `test_blocks_high_risk_action_without_approval`.

## 커밋과 Pull Request 기준

커밋 메시지는 짧은 명령형 문장으로 작성합니다. 예:

- `Add initial state schema`
- `Define sensor naming rules`
- `Update 8 week execution schedule`

PR에는 변경 요약, 변경한 파일, 검증 방법, 안전성 또는 운영 영향도를 포함합니다. 아키텍처나 일정이 바뀌면 `PLAN.md`, `todo.md`, `schedule.md` 중 관련 문서를 함께 갱신합니다.

## 보안과 설정 주의사항

API 키, 온실 접속 정보, PLC 주소, 실제 센서 endpoint, 운영 DB 접속 정보는 커밋하지 않습니다. 필요한 경우 `.env.example`처럼 예시 파일만 만들고 실제 값은 placeholder로 둡니다.

LLM, 정책, 프롬프트, 스키마는 버전 관리 대상입니다. 자동 제어와 관련된 변경은 반드시 정책 엔진, 실행 게이트, 감사 로그 관점에서 함께 검토합니다.
