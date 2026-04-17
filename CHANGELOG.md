# Changelog

이 파일은 `Keep a Changelog` 스타일로 유지한다.

## [Unreleased]

### Added

- **2026-04-17**: `scripts/benchmark_hybrid_retriever.py` — keyword / tfidf / openai / hybrid 4경로 recall@5·MRR·any_hit 벤치마크 툴. `evals/rag_retrieval_eval_set.jsonl` + `rag_stage_retrieval_eval_set.jsonl` 126 case 지원.
- **2026-04-17**: `docs/blind50_residual_post_ds_v11_closure_plan.md` — Phase K-1 fine-tune 종결 이후 blind50 validator 잔여 5건의 처리 결정(rubric 강화 2건, dataset scale-up 이관 2건, 기존 rubric 유지 1건) 고정.

### Changed

- **2026-04-17**: `docs/risk_level_rubric.md` §4 `robot_task_prioritization`에 "후보 중 하나가 blocked면 `high`, `skip_area` 먼저" 엔트리 추가. `blind-robot-004` 잔여 실패 대응.
- **2026-04-17**: `docs/risk_level_rubric.md` §4 `rootzone_diagnosis / nutrient_risk`와 §5 빠른 판정 규칙에 "GT Master feed-drain EC 차이 2.0mS/cm 이상 + drain 비율 20% 미만 → `high` + `create_alert + request_human_check` 필수 + `observe_only` 단독 금지" 엔트리 추가. `blind-expert-003` 잔여 실패 대응.
- **2026-04-17**: `docs/policy_output_validator_spec.md` §8 Validator Out-Of-Scope 목록에 `GT Master EC gradient > 2.0 + drain rate < 20%`, `robot_task blocked candidate` 2개 항목 추가. score-chasing 원칙을 유지해 validator 신규 규칙 추가 금지.

### Fixed

- 

### Removed

- **2026-04-17**: `gemini_flash_frontier` RAG-first frontier challenger 계획 전량 폐기. Phase A~E 4-way 실측(`artifacts/reports/ab_full_evaluation.md`, `artifacts/reports/ab_frozen_vs_frontier.md`)에서 `gemini-2.5-flash` (thinking) `ext 0.37 / blind 0.50`, `MiniMax M2.7` `ext 0.335 / blind 0.22`로 `ds_v11` (0.70/0.70) 대비 열세였다. reasoning/thinking 모델이 JSON strict + instruction-heavy 결정 경로에 구조적으로 부적합함이 확정됐다. `model_registry`의 `gemini_flash_frontier` alias, `.env*.example`의 `GEMINI_API_KEY`/`GOOGLE_API_KEY` 라인, llm-orchestrator README의 Gemini smoke 블록, `docs/runtime_integration_status.md`의 Gemini smoke 명령을 제거했다. 과거 평가 artifact는 역사 기록으로 보존한다. production champion은 계속 `ds_v11`.
