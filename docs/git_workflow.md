# Git Workflow

이 문서는 브랜치 전략, PR/Issue/ADR 운영, CHANGELOG, 릴리즈 태깅 규칙을 정의한다.

## 1. 브랜치 전략

- trunk branch: `master`
- 작업 브랜치:
  - `feature/<topic>`
  - `fix/<topic>`
  - `docs/<topic>`
  - `chore/<topic>`
  - `experiment/<topic>`
- 직접 `master`에 push하지 않고, 가능한 한 PR을 통해 병합한다.

예:

- `feature/execution-gateway-dispatcher`
- `docs/rag-regression-policy`

## 2. PR 기준

- `.github/pull_request_template.md`를 사용한다.
- 포함 항목:
  - 변경 요약
  - 변경 파일
  - 검증 방법
  - 운영/안전 영향
  - 문서 동기화 여부

## 3. Issue 기준

- `.github/ISSUE_TEMPLATE/bug_report.md`
- `.github/ISSUE_TEMPLATE/feature_request.md`

## 4. ADR 기준

- 템플릿: `docs/adr/0000-template.md`
- 파일명: `docs/adr/NNNN-short-title.md`
- 아키텍처, schema, 제어/안전 정책, 저장소 구조 결정은 ADR로 남긴다.

## 5. CHANGELOG 정책

- 파일: `CHANGELOG.md`
- 형식: `Keep a Changelog` 스타일의 `Unreleased` 유지
- 아래 변경은 반드시 기록한다.
  - schema 변경
  - RAG/eval 기준 변경
  - 안전 정책 변경
  - 서비스 인터페이스 변경

## 6. 릴리즈 태깅 규칙

- 형식: `vMAJOR.MINOR.PATCH`
- 초기 단계는 `v0.x.y`를 사용한다.
- 증가 기준:
  - `MAJOR`: 호환되지 않는 schema/contract 변경
  - `MINOR`: 새 서비스, 새 단계 완료, 중요한 기능 추가
  - `PATCH`: 버그 수정, 문서 정정, 검증 보강

예:

- `v0.4.0`: execution-gateway MVP 추가
- `v0.4.1`: command validator 버그 수정
