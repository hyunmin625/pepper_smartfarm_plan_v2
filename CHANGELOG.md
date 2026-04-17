# Changelog

이 파일은 `Keep a Changelog` 스타일로 유지한다.

## [Unreleased]

### Added

- 

### Changed

- 

### Fixed

- 

### Removed

- **2026-04-17**: `gemini_flash_frontier` RAG-first frontier challenger 계획 전량 폐기. Phase A~E 4-way 실측(`artifacts/reports/ab_full_evaluation.md`, `artifacts/reports/ab_frozen_vs_frontier.md`)에서 `gemini-2.5-flash` (thinking) `ext 0.37 / blind 0.50`, `MiniMax M2.7` `ext 0.335 / blind 0.22`로 `ds_v11` (0.70/0.70) 대비 열세였다. reasoning/thinking 모델이 JSON strict + instruction-heavy 결정 경로에 구조적으로 부적합함이 확정됐다. `model_registry`의 `gemini_flash_frontier` alias, `.env*.example`의 `GEMINI_API_KEY`/`GOOGLE_API_KEY` 라인, llm-orchestrator README의 Gemini smoke 블록, `docs/runtime_integration_status.md`의 Gemini smoke 명령을 제거했다. 과거 평가 artifact는 역사 기록으로 보존한다. production champion은 계속 `ds_v11`.
