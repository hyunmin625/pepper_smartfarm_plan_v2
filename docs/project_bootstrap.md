# Project Bootstrap

이 문서는 `0. 프로젝트 관리 초기화`에서 필요한 프로젝트 기본 운영 기준을 정리한다.

## 1. 프로젝트 코드명

- 코드명: `pepper-ops`
- 용도: 브랜치 이름, ADR 제목, 릴리즈 노트, 내부 참조 식별자에 사용한다.

## 2. 저장소 구조 결정

- 저장소 운영 방식: `monorepo`
- 기준 브랜치: `master`
- 서비스 디렉터리: `sensor-ingestor/`, `state-estimator/`, `policy-engine/`, `llm-orchestrator/`, `execution-gateway/`, `plc-adapter/`
- 공통 라이브러리 디렉터리: `libs/`
- 인프라 디렉터리: `infra/`
- 실험/PoC 디렉터리: `experiments/`

## 3. 공통 라이브러리 기준

`libs/`는 아래처럼 쪼갠다.

- `libs/core-schemas`: 공통 schema, enum, validator
- `libs/core-models`: state/action/decision dataclass와 shared model
- `libs/core-utils`: logging, time, id, config helper
- `libs/test-fixtures`: 공통 sample payload와 test fixture

서비스별 구현은 각 서비스 디렉터리에 두고, 둘 이상이 재사용하는 것만 `libs/`로 올린다.

## 4. 연결 문서

- 브랜치/릴리즈/CHANGELOG: `docs/git_workflow.md`
- 개발 환경 기준: `docs/development_toolchain.md`
- 용어/명명 규칙: `docs/glossary.md`, `docs/naming_conventions.md`
- 센서 연결 전환 절차: `docs/post_construction_sensor_cutover.md`
