# todo.md

## 관련 문서
- [저장소 README](README.md)
- [프로젝트 현황 요약](PROJECT_STATUS.md)
- [AI 모델 준비 및 MLOps 계획](AI_MLOPS_PLAN.md)
- [적고추 전문가 AI Agent 구축 계획](EXPERT_AI_AGENT_PLAN.md)
- [데이터셋 분류 체계](docs/dataset_taxonomy.md)
- [학습 데이터 포맷](docs/training_data_format.md)
- [데이터 정제 규칙](docs/data_curation_rules.md)
- [RAG 보완 핵심 과제](docs/rag_next_steps.md)
- [farm_case RAG 환류 파이프라인](docs/farm_case_rag_pipeline.md)
- [Offline Agent Runner 스펙](docs/offline_agent_runner_spec.md)
- [MLOps Registry 설계](docs/mlops_registry_design.md)
- [Shadow Mode Report 포맷](docs/shadow_mode_report_format.md)
- [Device Profile Registry](docs/device_profile_registry.md)
- [PLC Adapter Interface Contract](docs/plc_adapter_interface_contract.md)
- [PLC Site Override Map](docs/plc_site_override_map.md)
- [PLC Runtime Endpoint Config](docs/plc_runtime_endpoint_config.md)
- [PLC Channel Address Registry](docs/plc_channel_address_registry.md)
- [Device Command Mapping Matrix](docs/device_command_mapping_matrix.md)
- [Execution Gateway Command Contract](docs/execution_gateway_command_contract.md)
- [Execution Gateway Override Contract](docs/execution_gateway_override_contract.md)
- [Execution Gateway Flow](docs/execution_gateway_flow.md)
- [System Schema Design](docs/system_schema_design.md)
- [Site Scope Baseline](docs/site_scope_baseline.md)
- [Seasonal Operation Ranges](docs/seasonal_operation_ranges.md)
- [Sensor Model Shortlist](docs/sensor_model_shortlist.md)
- [Device Setpoint Ranges](docs/device_setpoint_ranges.md)
- [Device Operation Rules](docs/device_operation_rules.md)
- [Project Bootstrap](docs/project_bootstrap.md)
- [Git Workflow](docs/git_workflow.md)
- [Development Toolchain](docs/development_toolchain.md)
- [Post Construction Sensor Cutover](docs/post_construction_sensor_cutover.md)
- [Glossary](docs/glossary.md)
- [Naming Conventions](docs/naming_conventions.md)
- [일정 계획 보기](schedule.md)
- [전체 개발 계획 보기](PLAN.md)
- [작업 로그 보기](WORK_LOG.md)
- [평가셋 확장 계획](docs/eval_scaleup_plan.md)

# 온실 스마트팜 고추 재배 자동화를 위한 농업용 LLM 개발 세부 Todo

이 문서는 실제 개발 착수를 위한 **아주 세분화된 단계별 작업 목록**이다.  
각 작업은 가능한 한 작게 쪼개어, 바로 이슈/태스크로 옮길 수 있게 구성한다.

---

# 제품 수준 재평가 우선 작업

- [ ] `docs/model_product_readiness_reassessment.md` 기준으로 새 fine-tuning submit freeze 상태 유지
- [x] RAG-first frontier challenger를 `gemini-2.5-flash`로 고정하고 runtime alias `gemini_flash_frontier` + `gemini` provider smoke 경로를 연다 (`llm-orchestrator/llm_orchestrator/client.py`, `llm-orchestrator/llm_orchestrator/model_registry.py`, `artifacts/runtime/llm_orchestrator/model_registry.json`, `scripts/run_llm_orchestrator_smoke.py`, `.env.example`)
- [ ] `gemini_flash_frontier + sft_v11_rag_frontier`를 `extended200 + blind_holdout50 + real shadow` 기준으로 다시 평가하고 production 승격 여부를 판정
- [x] `scripts/build_openai_sft_datasets.py`로 `validation_min_per_family=2`, `validation_ratio=0.15`, `validation_selection=spread` split 시뮬레이션과 결과 기록
- [x] `docs/risk_level_rubric.md` 기준으로 기존 training/eval의 `risk_level` 전수 점검
- [x] `python3 scripts/report_risk_slice_coverage.py` 기준 mismatch `failure_safe_mode_risk_not_critical 4`, `failure_safe_mode_actions_missing 3`, `safety_hard_block_actions_missing 1` 정리
- [x] hard safety rule 10개를 policy/output validator 요구사항으로 분리 문서화 (`docs/policy_output_validator_spec.md`)
- [x] `extended160` 확장 tranche 작성
- [x] `extended200` 최종 분포와 blind holdout `50` 확장 tranche 작성
- [x] `docs/critical_slice_augmentation_plan.md` 기준 `evidence_incomplete_unknown 2 -> 10+`, `failure_safe_mode 10 -> 16+` 보강
- [x] `blind-action-002`, `blind-expert-001`를 `docs/remaining_blind_gap_root_cause.md`로 분해하고 batch13 `8건`으로 `data + rubric` 보강
- [x] `safety_policy`, `sensor_fault`, `robot_task_prioritization` 각 `20+` 보강 완료
- [x] `failure_response`, `rootzone_diagnosis/state_judgement` 중심 잔여 training 보강 완료
- [x] `scripts/report_eval_failure_clusters.py`로 `extended160` 실패군 재분류와 validator 외부화 우선순위 정리 (`artifacts/reports/eval_failure_clusters_ds_v9_prompt_v5_methodfix_extended160.md`)
- [x] 마지막 완료 모델 `ds_v9`를 `core24 + extended120 + blind_holdout + product gate` 기준으로 재평가하고 결과 문서화
- [x] `ds_v9` 재평가 결과를 baseline으로 고정하고 후속 challenger 비교표/문서에 같은 게이트를 강제 (`artifacts/fine_tuning/challenger_gate_baseline.md`)
- [x] blind50 validator 적용 후 잔여 실패 `12건`을 `risk_rubric_and_data / data_and_model / robot_contract_and_model` ownership으로 재분류 (`artifacts/reports/validator_residual_failures_ds_v9_prompt_v5_methodfix_blind_holdout50.md`)
- [x] `blind-edge-003`, `blind-edge-005` invariant 실패를 runtime wiring 전제에서 다시 검토하고 validator 우선순위/trigger 보정으로 회복
- [x] shadow mode audit -> summary report 경로 추가 (`llm-orchestrator/llm_orchestrator/runtime.py`, `scripts/build_shadow_mode_report.py`, `scripts/validate_shadow_mode_runtime.py`)
- [x] blind50 validator 잔여 `12건`을 batch14 sample `12건`으로 직접 역투영 (`docs/blind50_residual_batch14_plan.md`, `scripts/generate_batch14_residual_samples.py`)
- [x] `scripts/build_openai_sft_datasets.py`, `scripts/report_risk_slice_coverage.py`가 stale `combined_training_samples.jsonl` 대신 현재 `training_sample_files()`를 직접 읽도록 보강
- [x] batch14 기반 challenger draft 생성과 format 검증 (`artifacts/fine_tuning/openai_sft_train_prompt_v5_methodfix_batch14.jsonl`, `artifacts/fine_tuning/openai_sft_validation_prompt_v5_methodfix_batch14.jsonl`)
- [x] 다음 submit용 dry-run manifest 생성 (`artifacts/fine_tuning/runs/ft-sft-gpt41mini-ds_v11-prompt_v5_methodfix_batch14-eval_v2-20260413-000731.json`)
- [x] `ds_v11/prompt_v5_methodfix_batch14` 1회 실제 submit 및 완료 (`ftjob-dTfcY631bh5HJJKJnI5Xi0ML`, status `succeeded`)
- [x] `ds_v11/prompt_v5_methodfix_batch14`를 frozen gate(`core24 + extended120 + extended160 + extended200 + blind_holdout50 + raw/validator gate`)로 재평가
- [x] `ds_v11` residual failure 재분류: extended200 validator 잔여 `42건`, blind50 validator 잔여 `5건`
- [x] `ds_v11` blind50 기준 offline shadow replay 생성 및 계약/heuristic 정렬 (`decision_count 50`, `operator_agreement_rate 0.92`, `critical_disagreement_count 0`, `promotion_decision promote`)
- [ ] `ds_v11` shadow mode audit sample을 누적하고 `operator_agreement_rate`, `critical_disagreement_count`, `promotion_decision`을 실제 운영 로그 형식으로 검증
- [x] synthetic shadow `day0` seed pack `12건` 추가와 baseline 리포트 생성 (`scripts/generate_shadow_mode_day0_seed_pack.py`, `scripts/run_shadow_mode_seed_pack.py`, `scripts/validate_shadow_mode_seed_pack.py`)
- [x] synthetic shadow `day0` residual owner/cause 리포트 생성 (`scripts/report_shadow_mode_seed_residuals.py`, `artifacts/reports/shadow_mode_residuals_ds_v11_day0_seed.md`)
- [x] offline shadow replay false critical disagreement(`blind-forbidden-007`) 해소 및 runtime `HSV-09` 정렬
- [x] offline shadow replay false drift(`blind-action-003`, `blind-robot-001`, `blind-failure-008`)를 replay contract/heuristic 수정으로 제거
- [x] offline shadow replay 잔여 drift(`blind-action-004`, `blind-expert-003`, `blind-expert-010`, `blind-robot-005`)의 owner별 fix를 batch17 sample `8건`으로 설계 확정 (`docs/offline_shadow_residual_batch17_plan.md`, `scripts/generate_batch17_shadow_residual_samples.py`)
- [x] `batch16 + batch17 + hard-case oversampling` 기준 `ds_v12/prompt_v5_methodfix_batch17_hardcase` dry-run package 생성 (`artifacts/fine_tuning/openai_sft_train_prompt_v5_methodfix_batch17_hardcase.jsonl`, `artifacts/fine_tuning/openai_sft_validation_prompt_v5_methodfix_batch17_hardcase.jsonl`, manifest `artifacts/fine_tuning/runs/ft-sft-gpt41mini-ds_v12-prompt_v5_methodfix_batch17_hardcase-eval_v3-20260413-035151.json`)
- [x] synthetic shadow `day0` residual `4건`을 batch18 sample `8건`으로 직접 역투영 (`docs/synthetic_shadow_day0_batch18_plan.md`, `scripts/generate_batch18_shadow_day0_residual_samples.py`)
- [x] batch18 live head 기준 `ds_v13/prompt_v5_methodfix_batch18_hardcase` dry-run package 생성 (`artifacts/fine_tuning/openai_sft_train_prompt_v5_methodfix_batch18_hardcase.jsonl`, `artifacts/fine_tuning/openai_sft_validation_prompt_v5_methodfix_batch18_hardcase.jsonl`, manifest `artifacts/fine_tuning/runs/ft-sft-gpt41mini-ds_v13-prompt_v5_methodfix_batch18_hardcase-eval_v4-20260413-075846.json`)
- [x] `scripts/build_challenger_submit_preflight.py`로 `ds_v12` / `ds_v13` submit blocker 리포트 생성 (`artifacts/reports/challenger_submit_preflight_ds_v12_ds_v13.md`)
- [x] 실제 운영 전환용 shadow capture runner와 rolling window report 추가 (`scripts/run_shadow_mode_capture_cases.py`, `scripts/build_shadow_mode_window_report.py`, `docs/real_shadow_mode_runbook.md`)
- [x] submit preflight에 real shadow window 자동 연결 추가 (`scripts/build_challenger_submit_preflight.py --real-shadow-report`)
- [x] real shadow rollback + blind50 residual `5건`을 batch19 corrective sample로 역투영 (`scripts/generate_batch19_real_shadow_feedback.py`, `docs/batch19_real_shadow_feedback_plan.md`)
- [x] validator 규칙을 자연어로 정렬한 `sft_v10` prompt 추가 (`scripts/build_openai_sft_datasets.py`, `scripts/evaluate_fine_tuned_model.py`)
- [x] `ds_v14/prompt_v10_validator_aligned_batch19_hardcase` dry-run candidate와 preflight 리포트 생성 (`artifacts/fine_tuning/challenger_candidate_ds_v14_prompt_v10_validator_aligned_batch19_hardcase.md`, `artifacts/reports/challenger_submit_preflight_ds_v14_real_shadow.md`)
- [ ] blind50 validator 잔여 `5건`에 대해 `risk_rubric_and_data / data_and_model` 기준 targeted fix 여부를 확정
- [ ] extended200 validator 잔여 `42건` 중 `risk_rubric_and_data 34`, `data_and_model 13`, `robot_contract_and_model 2`의 우선순위 batch를 설계
- [ ] `synthetic shadow day0 hold`를 해소하고 `ds_v12` frozen dry-run package와 `ds_v13` batch18 next candidate 중 실제 submit 후보를 결정
- [x] execution-gateway hard-coded safety interlock 추가 (`execution-gateway/execution_gateway/guards.py`, `scripts/validate_execution_gateway_flow.py`, `scripts/validate_execution_dispatcher.py`)
- [x] state-estimator MVP 추가: `sensor_quality bad -> risk_level unknown` 기본 경로 구현 (`state-estimator/state_estimator/estimator.py`, `scripts/validate_state_estimator_mvp.py`)
- [x] batch15 hard-case `10건` 추가와 next-only oversampling 규칙 고정 (`scripts/generate_batch15_hard_cases.py`, `docs/hard_case_oversampling_plan.md`)
- [x] `scripts/build_openai_sft_datasets.py`에 train-only `--oversample-task-type` 지원 추가 및 dry-run format 검증 완료
- [x] batch16 safety reinforcement `30건` 추가: `worker_present 10`, `manual_override/safe_mode 10`, `critical readback/comm loss 10` (`scripts/generate_batch16_safety_reinforcement.py`)
- [x] ops-api shadow window 런타임 경화: `_redirect_audit_paths` contextmanager로 env 변수 누수 차단, `append=false`는 `manage_runtime_mode` 권한 + `.bak-{ts}` 회전으로 분리, `safe_ratio` None 처리, `promotion_decision` None-aware, 혼합 모델/프롬프트 `mixed` 표기, `critical 우선 top_disagreements` 정렬 (`ops-api/ops_api/shadow_mode.py`, `scripts/validate_ops_api_shadow_mode.py`)
- [x] ops-api auth dependency injection 회귀 해소: `create_app(settings=...)`이 `app.dependency_overrides[load_settings]`로 header_token 경로까지 주입되도록 수정, TestClient 기반 DI 회귀 추가 (`ops-api/ops_api/app.py`, `scripts/validate_ops_api_auth.py`)
- [x] postgres 스키마 드리프트 해소: `infra/postgres/001_initial_schema.sql`의 JSONB 32개 → `TEXT`, TIMESTAMPTZ 21개 → `TIMESTAMP WITHOUT TIME ZONE ... DEFAULT (NOW() AT TIME ZONE 'UTC')`로 ORM과 정렬, `validate_ops_api_postgres_smoke`를 decision/alert/robot_task write round-trip + cleanup으로 격상
- [x] ORM ↔ SQL 자동 드리프트 감지 smoke 추가: `infra/postgres/001_initial_schema.sql` 파서와 `Base.metadata` 비교, 13개 테이블 nullability/type family 정렬, negative test로 `policies.policy_stage` 강제 Integer 변경 드리프트 캐치 확인 (`scripts/validate_postgres_schema_drift.py`)
- [x] policy source abstraction 도입: `PolicySource` Protocol + `FilePolicySource`/`StaticPolicySource`, `set_active_policy_source()` 전역 스위치, ops-api `DbPolicySource`가 `PolicyRecord` 테이블 기반 live lookup, `create_app`이 seed 직후 자동 등록, `PATCH /policies/{id}` 토글이 다음 precheck에 즉시 반영 (`policy-engine/policy_engine/loader.py`, `policy-engine/policy_engine/__init__.py`, `ops-api/ops_api/policy_source.py`, `ops-api/ops_api/app.py`, `scripts/validate_policy_source_db_wiring.py`)
- [x] `/zones/{zone_id}/history` 응답에 `sensor_series` 추가, 9개 지표(air_temp_c, rh_pct, vpd_kpa, substrate_moisture_pct, substrate_temp_c, co2_ppm, par_umol_m2_s, feed_ec_ds_m, drain_ec_ds_m) 시계열, Approval Dashboard에 Zone History Chart 카드 + 인라인 SVG 스파크라인 추가 (`ops-api/ops_api/app.py`, `scripts/validate_ops_api_zone_history.py`)
- [x] state-estimator → policy-engine precheck 통합 smoke: healthy / worker_present / sensor_quality bad 3개 시나리오, HSV-01 `worker_present` 경로와 estimator-only sensor 가드 invariant 회귀 (`scripts/validate_state_estimator_policy_flow.py`)
- [x] llm-orchestrator → ActionDispatchPlanner → ExecutionDispatcher 통합 smoke: stub 기본 응답 log_only 경로, fixture 기반 adjust_fan → device_command acknowledged, pause_automation → control_override state_updated, audit row 2건 (`scripts/validate_llm_to_execution_flow.py`)
- [x] 실시간 shadow runner + gate: `push_shadow_cases_to_ops_api.py`가 `/shadow/cases/capture` → `/shadow/window` 경로를 batch 단위로 호출하고 `--gate rollback|hold|promote`로 최소 promotion_decision을 강제, TestClient monkey-patch 기반 gate 회귀 3개 시나리오 (`scripts/push_shadow_cases_to_ops_api.py`, `scripts/validate_shadow_runner_gate.py`)
- [x] `scripts/validate_execution_safe_mode.py`의 `policy_engine` sys.path pre-existing 버그 수정
- [x] Stitch `WebUI/stitch_ui_v1.zip` 레퍼런스 기반 대시보드 전면 재디자인 + 반응형: Tailwind CDN + Pretendard/Noto Sans KR + Material Symbols, 농경 사령부 컬러, `lg:` breakpoint 이상 고정 사이드바 / 이하 오프스크린 drawer + 햄버거 토글, 메트릭/스파크라인 그리드 반응형, 루트 `/` → `/dashboard` 307 리다이렉트 (`ops-api/ops_api/app.py` `_dashboard_html`)
- [x] AI 어시스턴트 채팅 뷰 + 백엔드: 사이드바 10번째 메뉴, split-pane (좌 chat + quick prompt + Enter 단축키, 우 실시간 관제 카드 + 최근 dispatch + 3×3 zone health), `POST /ai/chat` (`read_runtime` 권한, `ChatMessageRequest`/`ChatRequest`, `_build_chat_system_prompt`/`_render_chat_history`/`_extract_chat_reply` 헬퍼), 클라이언트 메모리 히스토리 + 매 호출마다 최근 8턴 context 전송, `scripts/validate_ops_api_ai_chat.py` 6 invariant 회귀
- [x] AI 어시스턴트 채팅 경로 DB grounding + 단일 모델 경로 정리: `/ai/chat`이 `_detect_zone_hint` + `_build_chat_grounding_context`로 최신 decision/alert/sensor_readings/active policies를 DB에서 조회해 `task_type="chat"` payload를 만들고, 별도 chat client 없이 `services.orchestrator.client`를 그대로 사용한다. decision/chat은 같은 `OPS_API_LLM_PROVIDER` / `OPS_API_MODEL_ID`를 공유하고, `{"reply": "..."}` 단일 JSON 출력 강제를 유지한다. `StubCompletionClient`에 chat task_type 분기, `validate_ops_api_ai_chat`에 4 invariant 추가 (총 10 invariant), 기존 smoke의 `Settings(...)` 호출은 단일 LLM 설정만 사용하도록 정리 (`ops-api/ops_api/config.py`, `ops-api/ops_api/app.py`, `llm-orchestrator/llm_orchestrator/client.py`, `.env.example`, `scripts/validate_ops_api_ai_chat.py`)
- [x] Phase A~E: 4-way 모델 비교 (ds_v11 / gpt-4.1 / gemini-2.5-flash / MiniMax M2.7) + live-rag grading 버그 발견/수정 + retriever 품질 벤치마크 (`artifacts/reports/ab_full_evaluation.md`, `artifacts/reports/ab_frozen_vs_frontier.md`, `scripts/regrade_eval_results.py`, `scripts/evaluate_fine_tuned_model.py::grade_case effective_retrieved_ids`)
- [x] Phase F: validator 후처리 4-way 측정 + TF-IDF+SVD / OpenAI embedding retriever 업그레이드 (`artifacts/reports/phase_f_validator_retriever_improvements.md`, `scripts/apply_validator_postprocess.py`, `scripts/build_rag_index.py --output artifacts/rag_index/pepper_openai_embed_index.json`) - recall@5 0.164→0.352 (2.1배), `safety_policy` 카테고리 0.000→0.542 복구
- [x] Phase G: retriever를 llm-orchestrator 패키지로 이관 + OPS_API_RETRIEVER_TYPE env var 배선 + ds_v12 batch22 설계 문서 (`llm-orchestrator/llm_orchestrator/retriever_vector.py`, `ops-api/ops_api/config.py`, `ops-api/ops_api/app.py`, `scripts/validate_vector_retrievers.py`, `docs/ds_v12_batch22_hard_safety_reinforcement_plan.md`)
- [x] Phase H: batch22 corrective samples 36건 (Cluster A: block_action vs enter_safe_mode 12건, Cluster B: GT Master dry-back 24건) + ds_v12 첫 fine-tune 시도 - `lr_multiplier=2.0+epochs=3` 공격적 hp 선택으로 catastrophic forgetting 발생(ext 0.110, 12가지 citation 포맷 드리프트), 5축 postmortem 해체로 원인 확정 (`scripts/generate_batch22_hard_safety_reinforcement.py`, `artifacts/reports/ds_v12_failure_postmortem.md`)
- [x] Phase I: validation set 확장(14→55) + schema drift 자동 감지 도구 (`scripts/compare_output_schemas.py` 6개 alarm: new_keys, common_drops, rare_losses, citation_majority, pass_drop, strict_json_drop). ds_v12 대비 5/6 alarm 발동 확인 + ds_v11 self-comparison 0 alarm 검증. batch22 cluster B variation 확장(12→24건, 한국어/영어/rockwool/dual-slab 변형)
- [x] Phase J: `run_openai_fine_tuning_job.py`에 `--n-epochs`, `--learning-rate-multiplier`, `--batch-size` 플래그 추가 + ds_v12.1 전면 재학습(보수적 hp `lr=1.0, epochs=2`, ext 0.585 / blind 0.700) + ds_v11.B1 증분 재학습(`ft:...ds_v11` base 위에 batch22 30건만, ext 0.485 / blind 0.540) 병렬 제출 + 3-way 비교 리포트 (`artifacts/reports/ds_v11_vs_ds_v12_1_vs_ds_v11_b1_3way.md`)
- [x] Phase K-1: fine-tune iteration 공식 종결 선언 (`artifacts/reports/fine_tune_iteration_final_postmortem.md`). 3번 시도(ds_v12, ds_v12.1, ds_v11.B1) 모두 ds_v11 baseline 대비 열세. 346 rows/14 카테고리 데이터셋 규모의 구조적 상한에 도달. **Fine-tune iteration 종료**
- [x] Phase K-2: production retriever를 `openai` text-embedding-3-small로 승격 (`.env`에 `OPS_API_RETRIEVER_TYPE=openai` 추가, ops-api boot smoke 검증 `OpenAIEmbeddingRetriever rows=226`). 다음 개선 축은 retriever 품질과 shadow mode 실트래픽 수집으로 이동
- [x] Phase K-3: todo.md / PROJECT_STATUS.md / WORK_LOG.md 전체 동기화 (Phase A~K 상태 반영, PROJECT_STATUS 항목 30~36 추가, WORK_LOG 2026-04-14~15 종합 섹션 추가)
- [x] Phase K-4: 4개 논리 그룹으로 git 커밋 (`c22fd00`, `75979e4`, `3d4ae3b`, `8e8989c`) + 원격 master 푸시
- [x] Phase L-1: `GET /ai/config` 엔드포인트 추가 (read_runtime 권한, llm_provider/model_id/label/family/prompt/retriever/chat_system_prompt 반환) + 대시보드 AI 어시스턴트 뷰 하드코딩 "sft_v10" 배지 → `#aiAssistantMeta` + `#aiAssistantModelChip` 동적 채움(`loadAiConfig()`), `.env` 변경 시 HTML 수정 없이 반영 (`ops-api/ops_api/app.py`)
- [x] Phase L-2: `scripts/validate_ops_api_ai_chat_live.py` 신규 라이브 smoke. 실제 .env 로드 + create_app + `/ai/config` + `/ai/chat` 한 턴 호출로 ds_v11 OpenAI 응답 수신 검증. 한국어 자연어 + provider/model_id 일치 + grounding_keys(`active_policies`, `operator_context`, `zone_id`) 확인. 트랜스크립트는 `artifacts/reports/ai_chat_live_smoke.md`에 append-only.
- [x] Phase L-3: Phase L 커밋 `17ff161` + 원격 master 푸시
- [x] Phase M-1: `llm-orchestrator.HybridRagRetriever` 구현. KeywordRagRetriever + OpenAIEmbeddingRetriever 두 백엔드의 top-k를 Reciprocal Rank Fusion(rrf_k=60)으로 결합. `create_retriever("hybrid")` factory + `__init__.py` export 추가 (`llm-orchestrator/llm_orchestrator/retriever_vector.py`, `llm-orchestrator/llm_orchestrator/__init__.py`). 벤치마크는 UI 고도화 우선순위에 밀려 별도 수행.
- [x] Phase N-1: 시스템 뷰 재설계. 상단에 AI Runtime 카드(`#aiRuntimeCard` + `#aiRuntimeBody` + `#aiRuntimeChip`)로 provider/model_label/family/prompt_version/retriever/chat_system_prompt_id 표시, Runtime Mode 카드(`#runtimeModeChip` 컬러 분기 + mode/reason/actor/role/auth_mode) 분리. Execution History 카드는 하단 풀너비 유지.
- [x] Phase N-2: 헤더 글로벌 champion chip(`#headerChampionChip`) 추가, 모든 view에서 sticky. 오버뷰 metricGrid 첫 카드로 `metric-champion` 강조 스타일 Champion Model 메트릭 카드 추가 (프라이머리 색상 배경 + 흰색 value), tooltip에 model_label·prompt·retriever. `loadAiConfig()`가 `aiAssistantMeta/chip`, `headerChampionChip`, `aiRuntimeBody`를 한 번에 갱신.
- [x] Phase N-3: AI 어시스턴트 우측 패널을 Live Operations → **Grounding Inspector**로 전환. `#groundingInspector` + `#groundingModelLabel` + `#groundingProvider` + `#groundingZoneHint` + `#groundingKeys` + `#groundingAttempts` 필드를 통해 마지막 `/ai/chat` 응답의 model_id/provider/zone_hint/grounding_keys/attempts를 운영자에게 투명 공개. chatState에 `lastGrounding` 추가, `renderGroundingInspector()` 함수가 `/ai/chat` 응답 직후 및 view 전환 시 자동 갱신. 기존 최근 dispatch + Zone Health 카드는 하단으로 이동.
- [x] Phase N-4: `scripts/validate_ops_api_phase_n_dashboard.py` 신규 smoke. 대시보드 HTML에 Phase N UI hook(`headerChampionChip`, `metric-champion`, `aiRuntimeCard/Body/Chip`, `runtimeModeChip`, `groundingInspector` 5종, `renderGroundingInspector`, `loadAiConfig().then`, `dashboardState`, `chatState.lastGrounding`) 16개 존재 검증 + `/ai/config` 7개 필드 검증 + `/ai/chat` grounding 필드 6개 검증. 기존 `validate_ops_api_ai_chat.py` + `validate_vector_retrievers.py` + `validate_ops_api_ai_chat_live.py` 회귀 통과 확인.

---

# 0. 프로젝트 관리 초기화

## 0.0 온실 공사중 전제 반영
- [x] 온실 공사 일정과 AI 준비 일정 분리 (`AI_MLOPS_PLAN.md`, `schedule.md`)
- [x] 실측 데이터 수집 전 AI 준비 범위 정의 (`AI_MLOPS_PLAN.md`)
- [x] 공사 완료 전 사용 가능한 문서/시뮬레이션/합성 데이터 목록화 (`AI_MLOPS_PLAN.md`, `docs/rag_source_inventory.md`, `data/examples/synthetic_sensor_scenarios.jsonl`)
- [x] 공사 완료 후 센서 연결 전환 절차 정의 (`docs/post_construction_sensor_cutover.md`, `AI_MLOPS_PLAN.md`)
- [x] AI 준비 → 센서 계획 → 센서 구현 → 제어 계획 → 제어 구현 → UI → AI 연결 순서 확정 (`AI_MLOPS_PLAN.md`, `schedule.md`, `PLAN.md`)

## 0.1 프로젝트 구조 정의
- [x] 프로젝트 코드명 확정 (`docs/project_bootstrap.md`)
- [x] 저장소 구조 정의 (`AGENTS.md`, `README.md`)
- [x] monorepo 여부 결정 (`docs/project_bootstrap.md`)
- [x] 서비스별 디렉터리 구조 설계 (`AGENTS.md`)
- [x] 공통 라이브러리 디렉터리 정의 (`docs/project_bootstrap.md`, `libs/README.md`)
- [x] infra 디렉터리 구조 정의 (`AGENTS.md`)
- [x] docs 디렉터리 구조 정의 (`AGENTS.md`)
- [x] data 디렉터리 구조 정의 (`AGENTS.md`)
- [x] experiments 디렉터리 구조 정의 (`AGENTS.md`)

## 0.2 형상관리/협업 준비
- [x] Git 브랜치 전략 정의 (`docs/git_workflow.md`)
- [x] commit convention 정의 (`AGENTS.md`)
- [x] PR 템플릿 작성 (`.github/pull_request_template.md`)
- [x] issue 템플릿 작성 (`.github/ISSUE_TEMPLATE/bug_report.md`, `.github/ISSUE_TEMPLATE/feature_request.md`)
- [x] ADR(Architecture Decision Record) 템플릿 작성 (`docs/adr/0000-template.md`, `docs/adr/README.md`)
- [x] CHANGELOG 정책 정리 (`docs/git_workflow.md`, `CHANGELOG.md`)
- [x] 릴리즈 태깅 규칙 정리 (`docs/git_workflow.md`)

## 0.3 개발 환경 공통화
- [x] Python 버전 고정 (`.python-version`, `pyproject.toml`, `docs/development_toolchain.md`)
- [x] 가상환경 전략 정의 (`evals/README.md`, `WORK_LOG.md`)
- [x] package manager 선택 (`docs/development_toolchain.md`)
- [x] 린터 선택 (`pyproject.toml`, `docs/development_toolchain.md`)
- [x] formatter 선택 (`pyproject.toml`, `docs/development_toolchain.md`)
- [x] type checker 선택 (`pyproject.toml`, `docs/development_toolchain.md`)
- [x] pre-commit hook 구성 (`.pre-commit-config.yaml`, `docs/development_toolchain.md`)
- [x] 환경 변수 템플릿 작성 (`.env.example`)
- [x] dev/staging/prod 환경 변수 분리 (`.env.dev.example`, `.env.staging.example`, `.env.prod.example`, `docs/development_toolchain.md`)

## 0.4 문서 기반 정리
- [x] 용어집 작성 (`docs/glossary.md`)
- [x] 장치 명명 규칙 정의 (`docs/naming_conventions.md`, `docs/sensor_collection_plan.md`)
- [x] zone_id 규칙 정의 (`docs/sensor_collection_plan.md`)
- [x] sensor_id 규칙 정의 (`docs/sensor_collection_plan.md`)
- [x] device_id 규칙 정의 (`docs/sensor_collection_plan.md`)
- [x] robot_id 규칙 정의 (`docs/naming_conventions.md`)
- [x] action_type enum 초안 작성 (`schemas/action_schema.json`)
- [x] 이벤트 이름 규칙 정의 (`docs/naming_conventions.md`)

---

# 1. 요구사항/현장 분석

## 1.1 현장 범위 확정
- [x] 대상 온실 수 확정 (`docs/site_scope_baseline.md`, `docs/sensor_collection_plan.md`)
- [x] 초기 적용 zone 확정 (`docs/sensor_collection_plan.md`, `data/examples/sensor_catalog_seed.json`)
- [x] 작물 범위 확정 (`README.md`, `PROJECT_STATUS.md`, `PLAN.md`)
- [x] 품종 범위 확정 (`docs/site_scope_baseline.md`)
- [x] 재배 환경/배지 확정 (`docs/site_scope_baseline.md`, `docs/sensor_collection_plan.md`, `data/examples/sensor_catalog_seed.json`)
- [x] 생육 단계 운영 범위 정의 (`docs/expert_knowledge_map.md`, `EXPERT_AI_AGENT_PLAN.md`)
- [x] 낮/밤 운영 정책 정의 (`docs/site_scope_baseline.md`)
- [x] 계절별 운영 범위 정의 (`docs/seasonal_operation_ranges.md`)

## 1.2 센서 인벤토리 작성
- [x] 온도 센서 모델 조사 (`docs/sensor_model_shortlist.md`)
- [x] 습도 센서 모델 조사 (`docs/sensor_model_shortlist.md`)
- [x] CO2 센서 모델 조사 (`docs/sensor_model_shortlist.md`)
- [x] 광량 센서 모델 조사 (`docs/sensor_model_shortlist.md`)
- [x] 배지 함수율 센서 모델 조사 (`docs/sensor_model_shortlist.md`)
- [x] EC 센서 모델 조사 (`docs/sensor_model_shortlist.md`)
- [x] pH 센서 모델 조사 (`docs/sensor_model_shortlist.md`)
- [x] 외기 센서 모델 조사 (`docs/sensor_model_shortlist.md`)
- [x] 카메라 사양 정리 (`docs/sensor_installation_inventory.md`, `data/examples/sensor_catalog_seed.json`)
- [x] 각 센서의 통신 방식 정리 (`docs/sensor_installation_inventory.md`, `data/examples/sensor_catalog_seed.json`)
- [x] 각 센서의 샘플링 주기 정리 (`docs/sensor_collection_plan.md`, `data/examples/sensor_catalog_seed.json`)
- [x] 각 센서의 보정 주기 정리 (`docs/sensor_installation_inventory.md`, `data/examples/sensor_catalog_seed.json`)
- [x] 품질 플래그 조건 정리 (`docs/sensor_collection_plan.md`, `data/examples/sensor_catalog_seed.json`)
- [x] zone별 설치 수량 가정치 정리 (`docs/sensor_installation_inventory.md`, `data/examples/sensor_catalog_seed.json`)
- [x] sensor `model_profile` 기준 정의 (`docs/sensor_installation_inventory.md`, `schemas/sensor_catalog_schema.json`)

## 1.3 액추에이터 인벤토리 작성
- [x] 환기창 제어 방식 정리 (`docs/sensor_installation_inventory.md`, `data/examples/sensor_catalog_seed.json`)
- [x] 순환팬 제어 방식 정리 (`docs/sensor_installation_inventory.md`, `data/examples/sensor_catalog_seed.json`)
- [x] 난방기 제어 방식 정리 (`docs/sensor_installation_inventory.md`, `data/examples/sensor_catalog_seed.json`)
- [x] 차광커튼 제어 방식 정리 (`docs/sensor_installation_inventory.md`, `data/examples/sensor_catalog_seed.json`)
- [x] 관수 밸브 제어 방식 정리 (`docs/sensor_installation_inventory.md`, `data/examples/sensor_catalog_seed.json`)
- [x] 양액기 제어 방식 정리 (`docs/sensor_installation_inventory.md`, `data/examples/sensor_catalog_seed.json`)
- [x] CO2 주입기 제어 방식 정리 (`docs/sensor_installation_inventory.md`, `data/examples/sensor_catalog_seed.json`)
- [x] 제습기 제어 방식 정리 (`docs/sensor_installation_inventory.md`, `data/examples/sensor_catalog_seed.json`)
- [x] 각 장치의 최소/최대 setpoint 정리 (`docs/device_setpoint_ranges.md`, `data/examples/sensor_catalog_seed.json`)
- [x] 각 장치의 응답 지연 정리 (`docs/sensor_installation_inventory.md`, `data/examples/sensor_catalog_seed.json`)
- [x] 장치별 안전 제한값 정리 (`docs/sensor_installation_inventory.md`, `data/examples/sensor_catalog_seed.json`)
- [x] device `model_profile` 기준 정의 (`docs/sensor_installation_inventory.md`, `schemas/sensor_catalog_schema.json`)

## 1.4 운영 시나리오 정리
- [x] 정상 운영 시나리오 작성 (`data/examples/synthetic_sensor_scenarios.jsonl`)
- [x] 고온 시나리오 작성 (`data/examples/synthetic_sensor_scenarios.jsonl`)
- [x] 고습 시나리오 작성 (`data/examples/synthetic_sensor_scenarios.jsonl`, `docs/operational_scenarios.md`)
- [x] 급격한 일사 증가 시나리오 작성 (`data/examples/synthetic_sensor_scenarios.jsonl`, `docs/operational_scenarios.md`)
- [x] 과건조 시나리오 작성 (`data/examples/synthetic_sensor_scenarios.jsonl`, `docs/operational_scenarios.md`)
- [x] 과습 시나리오 작성 (`data/examples/synthetic_sensor_scenarios.jsonl`)
- [x] 센서 고장 시나리오 작성 (`data/examples/synthetic_sensor_scenarios.jsonl`)
- [x] 장치 stuck 시나리오 작성 (`data/examples/synthetic_sensor_scenarios.jsonl`, `docs/operational_scenarios.md`)
- [x] 통신 장애 시나리오 작성 (`data/examples/synthetic_sensor_scenarios.jsonl`, `docs/operational_scenarios.md`)
- [x] 정전/재기동 시나리오 작성 (`data/examples/synthetic_sensor_scenarios.jsonl`, `docs/operational_scenarios.md`)
- [x] 사람 개입 시나리오 작성 (`data/examples/synthetic_sensor_scenarios.jsonl`, `docs/operational_scenarios.md`)
- [x] 로봇 작업 중단 시나리오 작성 (`data/examples/synthetic_sensor_scenarios.jsonl`, `docs/operational_scenarios.md`)

## 1.5 안전 요구사항 정리
- [x] 인터록 요구사항 목록화 (`docs/safety_requirements.md`, `docs/sensor_installation_inventory.md`)
- [x] 비상정지 요구사항 목록화 (`docs/safety_requirements.md`)
- [x] 수동모드 전환 조건 정의 (`docs/safety_requirements.md`)
- [x] 자동모드 전환 조건 정의 (`docs/safety_requirements.md`)
- [x] 승인 필수 액션 정의 (`docs/safety_requirements.md`, `schemas/action_schema.json`)
- [x] 절대 금지 액션 정의 (`docs/safety_requirements.md`, `data/examples/forbidden_action_samples.jsonl`)
- [x] 사람 감지 시 동작 규칙 정의 (`docs/safety_requirements.md`, `data/examples/robot_task_samples.jsonl`)
- [x] 로봇 작업 영역 접근 규칙 정의 (`docs/safety_requirements.md`, `data/examples/robot_task_samples.jsonl`)

---

# 2. 도메인 지식/데이터 준비

## 2.1 고추 재배 지식셋 정리
- [x] 기존 문서 수집 (`docs/rag_source_inventory.md`)
- [x] 재배 매뉴얼 정리 (`docs/rag_source_inventory.md`, `data/rag/pepper_expert_seed_chunks.jsonl`)
- [x] 생육 단계별 환경 목표 정리 (`docs/expert_knowledge_map.md`, `data/rag/pepper_expert_seed_chunks.jsonl`)
- [x] 관수 기준 정리 (`docs/expert_knowledge_map.md`, `data/rag/pepper_expert_seed_chunks.jsonl`)
- [x] EC/pH 관리 기준 정리 (`docs/expert_knowledge_map.md`, `docs/rag_source_inventory.md`, `data/rag/pepper_expert_seed_chunks.jsonl`)
- [x] 병해 위험 조건 정리 (`docs/expert_knowledge_map.md`, `docs/rag_source_inventory.md`, `data/rag/pepper_expert_seed_chunks.jsonl`)
- [x] 수확 적기 기준 정리 (`docs/expert_knowledge_map.md`, `data/rag/pepper_expert_seed_chunks.jsonl`)
- [x] 품종별 차이 정리 (`docs/rag_source_inventory.md`, `data/rag/pepper_expert_seed_chunks.jsonl`)
- [x] 온실 외기 영향 정리 (`docs/rag_source_inventory.md`, `data/rag/pepper_expert_seed_chunks.jsonl`)
- [x] 장치 운전 경험 규칙 정리 (`docs/device_operation_rules.md`)

## 2.2 데이터셋 분류 체계 정의
- [x] Q&A 데이터 분류 (`docs/dataset_taxonomy.md`, `data/examples/qa_reference_samples.jsonl`)
- [x] 상태판단 데이터 분류 (`data/examples/state_judgement_samples.jsonl`, `evals/expert_judgement_eval_set.jsonl`)
- [x] 행동추천 데이터 분류 (`docs/dataset_taxonomy.md`, `data/examples/action_recommendation_samples.jsonl`)
- [x] 금지행동 데이터 분류 (`data/examples/forbidden_action_samples.jsonl`)
- [x] 실패대응 데이터 분류 (`docs/dataset_taxonomy.md`, `data/examples/failure_response_samples.jsonl`)
- [x] 로봇작업 데이터 분류 (`docs/dataset_taxonomy.md`, `data/examples/robot_task_samples.jsonl`)
- [x] 알람/보고서 데이터 분류 (`docs/dataset_taxonomy.md`, `data/examples/reporting_samples.jsonl`)

## 2.3 학습 데이터 포맷 정의
- [x] input message 포맷 정의 (`docs/training_data_format.md`)
- [x] preferred_output 포맷 정의 (`docs/training_data_format.md`)
- [x] 상태판단 샘플 템플릿 정의 (`docs/training_data_format.md`, `data/examples/state_judgement_samples.jsonl`)
- [x] 행동추천 샘플 템플릿 정의 (`docs/training_data_format.md`, `data/examples/action_recommendation_samples.jsonl`)
- [x] 금지행동 샘플 템플릿 정의 (`docs/training_data_format.md`, `data/examples/forbidden_action_samples.jsonl`)
- [x] 로봇 우선순위 샘플 템플릿 정의 (`docs/training_data_format.md`, `data/examples/robot_task_samples.jsonl`)
- [x] 실패대응 샘플 템플릿 정의 (`docs/training_data_format.md`, `data/examples/failure_response_samples.jsonl`)
- [x] JSON schema 포함 방식 정의 (`docs/training_data_format.md`)
- [x] task family별 학습 seed 20건 이상 확보 (`data/examples/*_samples.jsonl`, `data/examples/*_samples_batch2.jsonl`)

## 2.4 데이터 정제
- [x] 중복 샘플 제거 (`scripts/audit_training_data_consistency.py`)
- [x] 모순 샘플 검토 (`scripts/audit_training_data_consistency.py`)
- [x] 표현 통일 (`docs/data_curation_rules.md`, `scripts/validate_training_examples.py`)
- [x] 장치명 통일 (`docs/data_curation_rules.md`, `scripts/validate_training_examples.py`)
- [x] 단위 통일 (`docs/data_curation_rules.md`, `scripts/validate_training_examples.py`)
- [x] zone 표기 통일 (`docs/data_curation_rules.md`, `scripts/validate_training_examples.py`)
- [x] 생육 단계 표기 통일 (`docs/data_curation_rules.md`, `scripts/validate_training_examples.py`)
- [x] 위험도 레이블 통일 (`docs/data_curation_rules.md`, `scripts/validate_training_examples.py`)
- [x] 근거 서술 스타일 통일 (`docs/data_curation_rules.md`)
- [x] 후속 확인 항목 통일 (`docs/data_curation_rules.md`, `scripts/validate_training_examples.py`)

## 2.5 평가셋 구축
- [x] 상태판단 평가셋 구축 (`evals/expert_judgement_eval_set.jsonl`)
- [x] 행동추천 평가셋 구축 (`evals/action_recommendation_eval_set.jsonl`)
- [x] 금지행동 평가셋 구축 (`evals/forbidden_action_eval_set.jsonl`)
- [x] 장애대응 평가셋 구축 (`evals/failure_response_eval_set.jsonl`)
- [x] 로봇 작업 우선순위 평가셋 구축 (`evals/robot_task_eval_set.jsonl`)
- [x] edge case 평가셋 구축 (`evals/edge_case_eval_set.jsonl`)
- [x] 계절별 평가셋 구축 (`evals/seasonal_eval_set.jsonl`)
- [x] 센서 이상 포함 평가셋 구축 (`evals/expert_judgement_eval_set.jsonl`)

## 2.5.1 평가셋 확장 게이트
- [x] 현재 eval 분포/총량 리포트 스크립트 추가 (`scripts/report_eval_set_coverage.py`)
- [x] `build_eval_jsonl.py`에 file별 row 수 출력 추가 (`scripts/build_eval_jsonl.py`)
- [x] 현재 `24건`을 `core regression set`으로 동결하고 append-only 운영 기준 명시 (`docs/eval_scaleup_plan.md`)
- [x] `Tranche 1`: eval 총량 `60+`까지 확장
- [x] `Tranche 2`: eval 총량 `120`까지 확장
- [x] `Tranche 3`: eval 총량 `160`까지 확장
- [x] `expert_judgement_eval_set.jsonl`를 `40` 이상으로 확장
- [x] `action_recommendation_eval_set.jsonl`를 `16` 이상으로 확장
- [x] `forbidden_action_eval_set.jsonl`를 `12` 이상으로 확장
- [x] `failure_response_eval_set.jsonl`를 `12` 이상으로 확장
- [x] `robot_task_eval_set.jsonl`를 `8` 이상으로 확장
- [x] `edge_case_eval_set.jsonl`를 `16` 이상으로 확장
- [x] `seasonal_eval_set.jsonl`를 `16` 이상으로 확장
- [x] `scripts/report_eval_set_coverage.py --enforce-minimums` 통과로 minimum gate 확인
- [x] `extended120` 게이트를 넘기기 전까지 새 fine-tuning submit 중지 원칙 문서화
- [x] champion `ds_v5/prompt_v5`를 `core24 + extended120` benchmark baseline으로 고정
- [x] corrective seed `batch10` + robot/forbidden 보강을 반영해 combined training `194건`으로 재생성
- [x] `prompt_v9` SFT draft(train `180`, validation `14`, eval overlap `0`) 생성
- [x] 마지막 완료 모델 `ds_v9/prompt_v5_methodfix`를 `extended200 + blind_holdout50 + raw/validator gate` 기준으로 재평가
- [x] batch14 residual 보강을 반영한 다음 challenger `ds_v11/prompt_v5_methodfix_batch14` dry-run package 준비
- [x] `ds_v11/prompt_v5_methodfix_batch14`를 frozen gate(`core24 + extended120 + extended160 + extended200 + blind_holdout50 + raw/validator gate`)로 재평가

## 2.6 RAG 지식베이스 구축 [완료]
- [x] RAG 적용 문서 범위 정의 (`docs/rag_source_inventory.md`)
- [x] RAG 메타데이터 스키마 및 인덱싱 계획 수립 (`docs/rag_indexing_plan.md`)
- [x] RAG 보완 핵심 과제 정리 (`docs/rag_next_steps.md`)
- [x] RAG 청크 검증 스키마와 JSONL 검증 스크립트 추가 (`schemas/rag_chunk_schema.json`, `scripts/validate_rag_chunks.py`)
- [x] 초기 시드 청크(6종) 인덱싱 및 테스트 (`scripts/build_rag_index.py`, `scripts/rag_smoke_test.py`)
- [x] 농촌진흥청 PDF 원문 기반 중복 제외 지식 보강 누적 22개 반영 (`data/rag/pepper_expert_seed_chunks.jsonl`)
- [x] PDF page/section citation 추적용 RAG 메타데이터 반영 (`source_pages`, `source_section`)
- [x] 농촌진흥청 PDF 추가 정밀 추출 후 중복 chunk_id 3건 병합, 전체 seed chunk 72개로 확장
    - [x] 화분/착과 임계값, 비가림 온습도, 자동관수, 차광, 육묘 소질, 플러그 상토 반영
    - [x] 가뭄, 저온해, 고온해, 영양장애, 생리장해, 건고추 저장 판단 기준 반영
    - [x] 병해충/IPM, 총채벌레·진딧물 생물적 방제, 바이러스 전염 생태, 양액 급액 제어 반영
    - [x] 품종 선택 기준, 풋고추 과형 분류, 재배 형태별 재배 시기, 노지 재배력 반영
    - [x] 비가림 재배력, 장마·태풍·우박·저온·서리창 대응 기준 반영
- [x] 육묘/접목/식물공장/비가림 재배 보강으로 전체 seed chunk 100개 확장
    - [x] 육묘 계절 관리, 입고병 예방, 바이러스 매개충 차단, 소질 진단 반영
    - [x] 접목 목적, 대목 분류, 파종 시차, 접목법, 활착 관리, 접목묘 정식 기준 반영
    - [x] 식물공장 육묘·활착 관리, 비가림 구조·밀도·염류·저일조 대응 반영
- [x] 초기 시드 청크의 `source_pages`, `source_section` 누락 경고 해소
    - [x] `python3 scripts/validate_rag_chunks.py` 기준 rows 100, duplicate 0, warnings 0, errors 0 확인
- [x] **지식 데이터 확충 (Phase 1: 전주기 커버리지)**
    - [x] 농사로(RAG-SRC-001~004) 및 현장 사례에서 정밀 청크 100개 이상 추출
    - [x] 농사로 추가 현장 사례(RAG-SRC-018~025) 반영으로 전체 seed chunk 141개 확장
    - [x] RAG-SRC-001 병해충/IPM·비가림 관리·건조 장 추가 추출로 전체 seed chunk 169개 확장
    - [x] 농사로(RAG-SRC-001~004) 및 현장 사례에서 정밀 청크 200개 이상 추출
    - [x] RAG-SRC-001 PDF 병해충/IPM, 양액재배/시설재배 장 추가 추출 지속
    - [x] 적고추 품종별 온도, 착과, 착색, 병저항성 기준 1차 청크화 (`pepper-crop-env-thresholds-001`, `pepper-cultivar-phytophthora-resistance-001`, `pepper-cultivar-fruitset-stability-001`, `pepper-cultivar-honggoeun-001`)
    - [x] 지역별 재배력, 월별 작업, 지역 기상 리스크 1차 청크화 (`pepper-semiforcing-schedule-001`, `pepper-normal-schedule-001`, `pepper-forcing-energy-saving-001`, `pepper-curved-fruit-cropping-shift-001`)
    - [x] 신규 PDF 청크별 **인과관계(Causality) 태그** 및 **시각적 특징(Visual) 태그** 라벨링
    - [x] 수확 후 큐어링·세척 위생, 풋고추 저장·결로, 홍고추 저장, 건고추 장기 저장·산소흡수제 포장, 하우스·열풍건조 운전 규칙 보강
    - [x] 미숙퇴비 암모니아 피해, 수직배수 불량, 과차광 낙화, 육묘 새순 오그라듦, 첫서리 낙화, 노화묘, 해비치·루비홍 품종 사례 반영
    - [x] 역병 초기 발병률, 호밀 혼화·고휴재배, 아인산 예방, 탄저병 빗물 전파·비가림 위생, 가루이·진딧물·나방·응애 세부 운용 규칙 반영
    - [x] 적고추 건조/저장 특화 지식 및 에너지 세이빙 노하우 1차 확장
    - [x] 균핵병·시들음병·잿빛곰팡이병·흰별무늬병·흰비단병·무름병·세균점무늬병·잎굴파리·뿌리혹선충·농약 안전사용 청크 추가로 전체 219개 확장
- [x] **전문가 수준 검색 및 중재 로직 구현**
    - [x] 지식 충돌 시 해결을 위한 **Trust Level 기반 Reranking** 로직 1차 구현
    - [x] 기상 재해·작형 대응 query 5종을 추가해 smoke/eval coverage 16건으로 확장
    - [x] 수확 후·건조·저장 대응 query 8종을 추가해 smoke/eval coverage 24건으로 확장
    - [x] **Multi-turn Contextual Retrieval**: 과거 3~5일간의 상태를 고려한 지식 검색 전략 수립 (`docs/rag_contextual_retrieval_strategy.md`)
    - [x] 로컬 **TF-IDF + SVD vector search PoC** 구현
    - [x] **ChromaDB persistent vector store** 구현 및 local-backed collection 검증
    - [x] OpenAI embedding 모델 연동 및 OpenAI-backed Chroma collection 검증
    - [x] **Metadata Hard Filtering** 로직 1차 구현 (growth/source/sensor/risk filter)
    - [x] `region`, `season`, `cultivar`, `greenhouse_type`, `active` 필터 추가
    - [x] `source_section` 부분 일치 필터와 `trust_level` 기반 reranking 구현
    - [x] `farm_case` 혼합 인덱스에서 official guideline 우선 정렬 guardrail 구현
    - [x] OpenAI-backed Chroma의 낮은 MRR 케이스 분석 및 `local blend 4.0` 기본값 반영
    - [x] backend별 Chroma collection/manifest 분리로 차원 충돌 방지
    - [x] retrieval weight 튜닝 스크립트 추가 (`scripts/tune_rag_weights.py`)
    - [x] Semantic + Keyword 하이브리드 검색 가중치 재검증용 eval set 40개 확장
    - [x] smoke test 81건, retrieval eval 96건으로 공식 PDF 추가 추출분 재검증
    - [x] smoke test 98건, retrieval eval 110건으로 219청크 재검증
    - [x] official + `farm_case` 혼합 인덱스 priority eval 4건 추가
- [x] **RAG 품질 평가 체계 구축**
    - [x] 시나리오별 검색 적중률(Hit Rate) 측정 1차 구현 (`evals/rag_retrieval_eval_set.jsonl`, `scripts/evaluate_rag_retrieval.py`)
    - [x] 출처 누락 방지를 위한 citation metadata 검증 로직 추가 (`scripts/validate_rag_chunks.py`)
    - [x] keyword-only vs local vector hybrid 비교 스크립트 추가 (`scripts/compare_rag_retrieval_modes.py`)
    - [x] 할루시네이션 방지를 위한 응답 citation coverage 검증 로직 추가 (`scripts/validate_response_citations.py`)
    - [x] keyword-only, local vector, local-backed Chroma 검색 hit rate 비교
    - [x] OpenAI vector를 포함한 4모드 검색 hit rate 비교
    - [x] 96개 평가셋 기준 4모드 재검증 완료 (keyword 0.9896, local 1.0, Chroma local 0.9948, Chroma OpenAI 0.9826)
    - [x] 4모드 비교를 더 긴 평가셋(40 case)으로 재검증
    - [x] 4모드 비교를 계절·센서 이상·현장 사례 케이스 포함 80 case로 재검증
    - [x] 110개 평가셋 기준 4모드 재검증 완료 (keyword 0.9909, local 1.0, Chroma local 0.9955, Chroma OpenAI 0.9803)
    - [x] 재배단계별 retrieval eval 16건 추가 (`evals/rag_stage_retrieval_eval_set.jsonl`, keyword/local 모두 hit rate 1.0, MRR 1.0)
    - [x] 공통 110건 + stage 16건 통합 검증 entrypoint 추가 (`scripts/run_rag_validation_suite.py`)

## 2.7 AI 준비/MLOps 기반 구축
- [x] AI_MLOPS_PLAN.md 유지관리
- [x] offline decision runner 요구사항 작성 (`docs/offline_agent_runner_spec.md`)
- [x] 센서 상태 합성 시나리오 작성 (`data/examples/synthetic_sensor_scenarios.jsonl`)
- [x] 평가셋 버전 관리 규칙 정의 (`docs/mlops_registry_design.md`)
- [x] dataset registry 설계 (`docs/mlops_registry_design.md`)
- [x] prompt registry 설계 (`docs/mlops_registry_design.md`)
- [x] model registry 설계 (`docs/mlops_registry_design.md`)
- [x] champion/challenger 모델 승격 규칙 정의 (`docs/mlops_registry_design.md`)
- [x] shadow mode 평가 리포트 포맷 정의 (`docs/shadow_mode_report_format.md`)
- [x] 운영 로그 → 학습 후보 변환 규칙 정의 (`docs/mlops_registry_design.md`)
- [x] 운영 로그 → RAG `farm_case` 후보 변환 규칙 정의 (`docs/farm_case_rag_pipeline.md`)
- [x] `farm_id`, `zone_id`, `cultivar`, `season`, `outcome` metadata 정의 (`schemas/farm_case_candidate_schema.json`)
- [x] 성공/실패 사례를 공식 지식과 충돌 검토 후 RAG에 반영하는 승인 절차 정의 (`docs/farm_case_rag_pipeline.md`)
- [x] `farm_case_candidate` JSONL 샘플 10건 작성 (`data/examples/farm_case_candidate_samples.jsonl`)
- [x] event window builder 규칙을 세부 스펙으로 구체화 (`docs/farm_case_event_window_builder.md`)
- [x] `farm_case_candidate` JSONL 검증 스크립트 추가 (`scripts/validate_farm_case_candidates.py`)
- [x] 승인된 `farm_case` 후보를 RAG chunk JSONL로 변환하는 스크립트 초안 작성 (`scripts/build_farm_case_rag_chunks.py`, `data/rag/farm_case_seed_chunks.jsonl`)

## 2.8 적고추 전문가 AI Agent 구축
- [x] 적고추 재배 전주기 단계 정의 (`docs/expert_knowledge_map.md`, `EXPERT_AI_AGENT_PLAN.md`)
- [x] 생육 단계별 전문가 판단 질문 목록 작성 (`docs/expert_knowledge_map.md`)
- [x] 센서 지표와 판단 항목 매핑 (`docs/sensor_judgement_matrix.md`)
- [x] `docs/expert_knowledge_map.md` 작성
- [x] `docs/sensor_judgement_matrix.md` 작성
- [x] `schemas/feature_schema.json` 작성
- [x] `schemas/sensor_quality_schema.json` 작성
- [x] `evals/expert_judgement_eval_set.jsonl` 작성
- [x] `docs/agent_tool_design.md` 작성
- [x] `docs/offline_agent_runner_spec.md` 작성
- [x] growth-stage-agent 역할 정의 (`EXPERT_AI_AGENT_PLAN.md`)
- [x] climate-agent 역할 정의 (`EXPERT_AI_AGENT_PLAN.md`)
- [x] irrigation-agent 역할 정의 (`EXPERT_AI_AGENT_PLAN.md`)
- [x] nutrient-agent 역할 정의 (`EXPERT_AI_AGENT_PLAN.md`)
- [x] pest-disease-agent 역할 정의 (`EXPERT_AI_AGENT_PLAN.md`)
- [x] harvest-drying-agent 역할 정의 (`EXPERT_AI_AGENT_PLAN.md`)
- [x] safety-agent 역할 정의 (`EXPERT_AI_AGENT_PLAN.md`)
- [x] report-agent 역할 정의 (`EXPERT_AI_AGENT_PLAN.md`)

---

# 3. 파인튜닝 준비 및 수행

## 3.1 학습 목표 재정의
- [x] 지식형 모델 vs 운영형 모델 역할 구분 (`docs/fine_tuning_objectives.md`)
- [x] RAG 담당 지식과 파인튜닝 담당 행동 양식 분리 (`docs/fine_tuning_objectives.md`)
- [x] 파인튜닝 목표 문서화 (`docs/fine_tuning_objectives.md`)
- [x] 구조화 출력 목표 정의 (`docs/fine_tuning_objectives.md`, `schemas/action_schema.json`)
- [x] 허용 action_type 목록 확정 (`docs/fine_tuning_objectives.md`, `schemas/action_schema.json`)
- [x] confidence 출력 요구 정의 (`docs/fine_tuning_objectives.md`)
- [x] follow_up 출력 요구 정의 (`docs/fine_tuning_objectives.md`, `schemas/action_schema.json`)
- [x] citations/retrieval_coverage 출력 요구 정의 (`docs/fine_tuning_objectives.md`, `schemas/action_schema.json`)

## 3.2 데이터 파일 생성
- [x] 학습용 JSONL 생성 스크립트 작성 (`scripts/build_training_jsonl.py`, `artifacts/training/combined_training_samples.jsonl`)
- [x] 검증용 JSONL 생성 스크립트 작성 (`scripts/build_eval_jsonl.py`, `artifacts/training/combined_eval_cases.jsonl`)
- [x] 포맷 검증 스크립트 작성 (`scripts/validate_training_examples.py`)
- [x] 샘플 통계 리포트 생성 (`scripts/report_training_sample_stats.py`, `artifacts/reports/training_sample_stats.json`)
- [x] class imbalance 확인 (`artifacts/reports/training_sample_stats.json`, `docs/training_sample_manual_review.md`)
- [x] action_type 분포 확인 (`artifacts/reports/training_sample_stats.json`, `docs/training_sample_manual_review.md`)
- [x] 길이 분포 확인 (`artifacts/reports/training_sample_stats.json`, `docs/training_sample_manual_review.md`)
- [x] 이상 샘플 수동 검토 (`docs/training_sample_manual_review.md`)

## 3.3 학습 실행
- [x] 모델 버전 결정 (`docs/fine_tuning_runbook.md`)
- [x] 실험명 규칙 정의 (`docs/fine_tuning_runbook.md`)
- [x] 파인튜닝 작업 실행 (`scripts/run_openai_fine_tuning_job.py --submit`, `artifacts/fine_tuning/runs/ft-sft-gpt41mini-ds_v1-prompt_v1-eval_v1-20260412-004953.json`)
- [x] 로그 보관 (`scripts/run_openai_fine_tuning_job.py`, `scripts/sync_openai_fine_tuning_job.py`, `artifacts/fine_tuning/runs/`)
- [x] 학습 실패 케이스 기록 (`artifacts/fine_tuning/failure_cases.jsonl`, `ftjob-2UERXn8JN2B0SDUXL1tukptl`)
- [x] 결과 비교표 작성 (`scripts/render_fine_tuning_comparison_table.py`, `artifacts/fine_tuning/fine_tuning_comparison_table.md`)

## 3.4 파인튜닝 결과 검증
- [x] 상태 요약 품질 평가 (`scripts/evaluate_fine_tuned_model.py`, `artifacts/reports/fine_tuned_model_eval_latest.md`)
- [x] 추천 행동 유효성 평가 (`scripts/evaluate_fine_tuned_model.py`, `artifacts/reports/fine_tuned_model_eval_latest.md`)
- [x] 금지 행동 준수 평가 (`scripts/evaluate_fine_tuned_model.py`, `artifacts/reports/fine_tuned_model_eval_latest.md`)
- [x] JSON 일관성 평가 (`scripts/evaluate_fine_tuned_model.py`, `artifacts/reports/fine_tuned_model_eval_latest.md`)
- [x] RAG 문맥이 주어졌을 때 근거 반영률 평가 (`scripts/evaluate_fine_tuned_model.py`, `artifacts/reports/fine_tuned_model_eval_latest.md`)
- [x] 다음 라운드용 prompt/data remediation 적용 (`data/examples/*_samples_batch3.jsonl`, `scripts/build_openai_sft_datasets.py`, `artifacts/reports/fine_tuned_model_eval_prompt_v2.md`)
- [x] 남은 9개 실패 케이스 기준 batch4/prompt_v3 초안 반영 (`data/examples/*_samples_batch4.jsonl`, `scripts/build_openai_sft_datasets.py`, `docs/fine_tuning_objectives.md`)
- [x] 남은 8개 실패 케이스 기준 batch5/prompt_v4 초안 반영 (`data/examples/*_samples_batch5.jsonl`, `scripts/build_openai_sft_datasets.py`, `docs/fine_tuning_objectives.md`)
- [ ] 검색 근거 부족 시 불확실성 표현 평가
- [ ] hallucination 사례 정리
- [x] confidence calibration 검토 (`scripts/evaluate_fine_tuned_model.py`, `artifacts/reports/fine_tuned_model_eval_latest.md`)
- [ ] 사람 검토 결과 수집
- [ ] 개선 포인트 정리

---

# 4. 시스템 스키마 설계

## 4.1 공통 도메인 모델
- [x] Zone 모델 정의 (`schemas/domain_models_schema.json`, `ops-api/ops_api/models.py`)
- [x] Sensor 모델 정의 (`schemas/domain_models_schema.json`, `ops-api/ops_api/models.py`)
- [x] Device 모델 정의 (`schemas/domain_models_schema.json`, `ops-api/ops_api/models.py`)
- [x] Constraint 모델 정의 (`schemas/domain_models_schema.json`, `schemas/state_schema.json`)
- [x] Decision 모델 정의 (`schemas/decision_schema.json`, `ops-api/ops_api/models.py`)
- [x] Action 모델 정의 (`schemas/action_schema.json`, `docs/system_schema_design.md`)
- [x] RobotCandidate 모델 정의 (`schemas/domain_models_schema.json`, `ops-api/ops_api/models.py`)
- [x] RobotTask 모델 정의 (`schemas/domain_models_schema.json`, `schemas/action_schema.json`, `ops-api/ops_api/models.py`)

## 4.2 상태 스키마 설계
- [x] current_state 필드 목록 확정 (`schemas/state_schema.json`, `docs/system_schema_design.md`)
- [x] derived_features 필드 목록 확정 (`schemas/feature_schema.json`, `docs/system_schema_design.md`)
- [x] device_status 필드 목록 확정 (`schemas/state_schema.json`, `data/examples/zone_state_payload_samples.jsonl`)
- [x] constraints 필드 목록 확정 (`schemas/state_schema.json`, `schemas/domain_models_schema.json`)
- [x] sensor_quality 필드 목록 확정 (`schemas/sensor_quality_schema.json`, `docs/system_schema_design.md`)
- [x] weather_context 필드 목록 확정 (`docs/system_schema_design.md`, `schemas/state_schema.json`)
- [x] growth_stage 필드 목록 확정 (`schemas/state_schema.json`)
- [x] enum 값 정리 (`schemas/state_schema.json`, `schemas/feature_schema.json`, `schemas/sensor_quality_schema.json`)
- [x] JSON schema 작성 (`schemas/state_schema.json`, `scripts/validate_zone_state_payloads.py`)
- [x] 예제 payload 작성 (`data/examples/zone_state_payload_samples.jsonl`)

## 4.3 액션 스키마 설계
- [x] action_type 목록 확정 (`schemas/action_schema.json`, `docs/system_schema_design.md`)
- [x] 장치별 parameter schema 설계 (`docs/device_command_mapping_matrix.md`, `schemas/device_command_request_schema.json`)
- [x] irrigation schema 설계 (`schemas/action_schema.json`, `docs/device_command_mapping_matrix.md`)
- [x] shade schema 설계 (`schemas/action_schema.json`, `docs/device_command_mapping_matrix.md`)
- [x] vent schema 설계 (`schemas/action_schema.json`, `docs/device_command_mapping_matrix.md`)
- [x] fan schema 설계 (`schemas/action_schema.json`, `docs/device_command_mapping_matrix.md`)
- [x] heating schema 설계 (`schemas/action_schema.json`, `docs/device_command_mapping_matrix.md`)
- [x] co2 schema 설계 (`schemas/action_schema.json`, `docs/device_command_mapping_matrix.md`)
- [x] robot task schema 설계 (`schemas/action_schema.json`, `schemas/domain_models_schema.json`)
- [x] follow_up schema 설계 (`schemas/action_schema.json`)
- [x] decision schema 작성 (`schemas/decision_schema.json`, `data/examples/decision_payload_samples.jsonl`, `scripts/validate_decision_payloads.py`)

## 4.4 이벤트 스키마 설계
- [x] sensor.snapshot.updated schema (`schemas/system_event_schema.json`, `data/examples/system_event_samples.jsonl`)
- [x] zone.state.updated schema (`schemas/system_event_schema.json`, `data/examples/system_event_samples.jsonl`)
- [x] action.requested schema (`schemas/system_event_schema.json`, `data/examples/system_event_samples.jsonl`)
- [x] action.blocked schema (`schemas/system_event_schema.json`, `data/examples/system_event_samples.jsonl`)
- [x] action.executed schema (`schemas/system_event_schema.json`, `data/examples/system_event_samples.jsonl`)
- [x] robot.task.created schema (`schemas/system_event_schema.json`, `data/examples/system_event_samples.jsonl`)
- [x] robot.task.failed schema (`schemas/system_event_schema.json`, `data/examples/system_event_samples.jsonl`)
- [x] alert.created schema (`schemas/system_event_schema.json`, `data/examples/system_event_samples.jsonl`)
- [x] approval.requested schema (`schemas/system_event_schema.json`, `data/examples/system_event_samples.jsonl`, `scripts/validate_system_events.py`)

---

# 5. 데이터베이스 설계 및 구축

## 5.1 PostgreSQL 스키마
- [x] zones 테이블 작성 (`infra/postgres/001_initial_schema.sql`, `ops-api/ops_api/models.py`)
- [x] sensors 테이블 작성 (`infra/postgres/001_initial_schema.sql`, `ops-api/ops_api/models.py`)
- [x] devices 테이블 작성 (`infra/postgres/001_initial_schema.sql`, `ops-api/ops_api/models.py`)
- [x] policies 테이블 작성 (`infra/postgres/001_initial_schema.sql`, `ops-api/ops_api/models.py`)
- [x] decisions / llm_decisions canonical 테이블 작성 (`infra/postgres/001_initial_schema.sql`, `ops-api/ops_api/models.py`)
- [x] device_commands 테이블 작성 (`infra/postgres/001_initial_schema.sql`, `ops-api/ops_api/models.py`)
- [x] alerts 테이블 작성 (`infra/postgres/001_initial_schema.sql`, `ops-api/ops_api/models.py`)
- [x] approvals 테이블 작성 (`infra/postgres/001_initial_schema.sql`, `ops-api/ops_api/models.py`)
- [x] robot_candidates 테이블 작성 (`infra/postgres/001_initial_schema.sql`, `ops-api/ops_api/models.py`)
- [x] robot_tasks 테이블 작성 (`infra/postgres/001_initial_schema.sql`, `ops-api/ops_api/models.py`)

## 5.2 인덱스 및 성능
- [x] zone_id 인덱스 설정 (`infra/postgres/001_initial_schema.sql`)
- [x] timestamp 인덱스 설정 (`infra/postgres/001_initial_schema.sql`)
- [x] device command 조회 인덱스 설정 (`infra/postgres/001_initial_schema.sql`)
- [x] robot task 조회 인덱스 설정 (`infra/postgres/001_initial_schema.sql`)
- [x] partition 필요성 검토 (`docs/timescaledb_schema_design.md`)
- [x] 보관 주기 정책 검토 (`docs/timescaledb_schema_design.md`)

## 5.3 시계열 저장소
- [x] TimescaleDB vs InfluxDB 결정 (`docs/timeseries_storage_dashboard_plan.md`)
- [x] sensor_readings hypertable 스키마 작성 (`docs/timescaledb_schema_design.md`)
- [x] zone_state_snapshots 스키마 작성 (`docs/timescaledb_schema_design.md`)
- [x] retention policy 작성 (`docs/timescaledb_schema_design.md`)
- [x] downsampling 정책 작성 (`docs/timescaledb_schema_design.md`)
- [x] 압축 정책 작성 (`docs/timescaledb_schema_design.md`)

## 5.4 마이그레이션/시드
- [x] migration 초기화 (`ops-api/ops_api/database.py`, `scripts/apply_ops_api_migrations.py`, `scripts/bootstrap_ops_api_reference_data.py`)
- [x] seed 데이터 작성 (`ops-api/ops_api/seed.py`, `scripts/bootstrap_ops_api_reference_data.py`)
- [x] 기본 zone 등록 (`data/examples/sensor_catalog_seed.json`, `ops-api/ops_api/seed.py`)
- [x] 기본 sensor 등록 (`data/examples/sensor_catalog_seed.json`, `ops-api/ops_api/seed.py`)
- [x] 기본 device 등록 (`data/examples/sensor_catalog_seed.json`, `data/examples/device_site_override_seed.json`, `ops-api/ops_api/seed.py`)
- [x] 기본 policy 등록 (`data/examples/policy_output_validator_rules_seed.json`, `ops-api/ops_api/seed.py`)
- [x] 기본 enum/reference 데이터 등록 (`data/examples/device_profile_registry_seed.json`, `ops-api/ops_api/seed.py`)

---

# 6. 센서 수집 파이프라인

## 6.1 수집 아키텍처 정의
- [x] polling vs event 방식 결정 (`docs/sensor_collection_plan.md`, `docs/sensor_ingestor_config_spec.md`)
- [x] 샘플링 주기 결정 (`docs/sensor_collection_plan.md`, `data/examples/sensor_catalog_seed.json`)
- [x] timestamp 기준 정의 (`docs/sensor_collection_plan.md`, `docs/sensor_ingestor_runtime_flow.md`)
- [x] 데이터 손실 처리 방식 정의 (`docs/sensor_collection_plan.md`, `docs/sensor_quality_rules_pseudocode.md`, `docs/sensor_ingestor_runtime_flow.md`)
- [x] 재전송 정책 정의 (`docs/sensor_collection_plan.md`, `docs/sensor_ingestor_config_spec.md`, `schemas/sensor_ingestor_config_schema.json`)
- [x] 장애 시 buffer 정책 정의 (`docs/sensor_collection_plan.md`, `docs/sensor_ingestor_config_spec.md`, `docs/post_construction_sensor_cutover.md`)
- [x] AI 학습용 raw data와 feature data 분리 저장 방식 정의 (`AI_MLOPS_PLAN.md`, `docs/sensor_collection_plan.md`)
- [x] 센서 이벤트와 장치 명령 시간축 정렬 방식 정의 (`AI_MLOPS_PLAN.md`)
- [x] calibration_version 저장 방식 정의 (`docs/sensor_collection_plan.md`)

## 6.1.1 센서 수집 계획 보강
- [x] 환경 센서 목록 확정: 온도, 습도, CO2, 광량/PAR, 일사량 (`docs/sensor_collection_plan.md`)
- [x] 배지/양액 센서 목록 확정: 함수율, EC, pH, 배액량, 배액 EC/pH, 양액 온도 (`docs/sensor_collection_plan.md`)
- [x] 외기 센서 목록 확정: 외기 온도, 외기 습도, 풍속, 강우, 외부 일사 (`docs/sensor_collection_plan.md`)
- [x] 장치 상태 수집 목록 확정: 팬, 차광, 환기창, 관수 밸브, 난방기, CO2 공급기, 제습기 (`docs/sensor_collection_plan.md`)
- [x] 비전 데이터 수집 계획 작성: 작물 이미지, 숙도, 병징, 잎 상태, 수확 후보 (`docs/sensor_collection_plan.md`)
- [x] 운영 이벤트 수집 계획 작성: 관수 실행, 차광 변경, 작업자 개입, 알람, 수동 override (`docs/sensor_collection_plan.md`)
- [x] sensor_id/device_id/zone_id naming 규칙 확정 (`docs/sensor_collection_plan.md`)
- [x] sensor quality flag 기준 확정 (`docs/sensor_collection_plan.md`)
- [x] 센서별 수집 주기와 단위 확정 (`docs/sensor_collection_plan.md`, `data/examples/sensor_catalog_seed.json`)
- [x] AI 학습 반영 가능 여부별 데이터 우선순위 지정 (`docs/sensor_collection_plan.md`)

## 6.2 센서 어댑터 구현
- [x] 온도/습도 센서 어댑터 작성 (`sensor-ingestor/sensor_ingestor/adapters.py`, `scripts/validate_sensor_ingestor_adapters.py`)
- [x] CO2 센서 어댑터 작성 (`sensor-ingestor/sensor_ingestor/adapters.py`, `scripts/validate_sensor_ingestor_adapters.py`)
- [x] 광량 센서 어댑터 작성 (`sensor-ingestor/sensor_ingestor/adapters.py`, `scripts/validate_sensor_ingestor_adapters.py`)
- [x] 함수율 센서 어댑터 작성 (`sensor-ingestor/sensor_ingestor/adapters.py`, `scripts/validate_sensor_ingestor_adapters.py`)
- [x] EC 센서 어댑터 작성 (`sensor-ingestor/sensor_ingestor/adapters.py`, `scripts/validate_sensor_ingestor_adapters.py`)
- [x] pH 센서 어댑터 작성 (`sensor-ingestor/sensor_ingestor/adapters.py`, `scripts/validate_sensor_ingestor_adapters.py`)
- [x] 외기 센서 어댑터 작성 (`sensor-ingestor/sensor_ingestor/adapters.py`, `scripts/validate_sensor_ingestor_adapters.py`)
- [x] 각 어댑터 timeout 처리 (`sensor-ingestor/sensor_ingestor/runtime.py`, `scripts/validate_sensor_ingestor_adapters.py`)
- [x] 각 어댑터 retry 처리 (`sensor-ingestor/sensor_ingestor/runtime.py`, `scripts/validate_sensor_ingestor_adapters.py`)
- [x] 품질 플래그 생성 로직 작성 (`sensor-ingestor/sensor_ingestor/quality.py`, `sensor-ingestor/sensor_ingestor/runtime.py`)

## 6.3 sensor-ingestor 서비스
- [x] 프로젝트 초기화 (`sensor-ingestor/README.md`, `sensor-ingestor/main.py`, `sensor-ingestor/sensor_ingestor/`)
- [x] 설정 파일 구조 작성
- [x] sensor poller 구현 (`sensor-ingestor/sensor_ingestor/runtime.py`)
- [x] parser 구현 (`sensor-ingestor/sensor_ingestor/runtime.py`)
- [x] validator 구현 (`scripts/validate_sensor_ingestor_config.py`, `sensor-ingestor/sensor_ingestor/config.py`)
- [x] normalizer 구현 (`sensor-ingestor/sensor_ingestor/runtime.py`)
- [x] MQTT publisher 구현 (`sensor-ingestor/sensor_ingestor/backends.py`, `scripts/validate_sensor_ingestor_runtime.py`)
- [x] timeseries writer 구현 (`sensor-ingestor/sensor_ingestor/backends.py`, `scripts/validate_sensor_ingestor_runtime.py`)
- [x] health check endpoint 작성 (`sensor-ingestor/sensor_ingestor/runtime.py`, `/healthz`)
- [x] metrics endpoint 작성 (`sensor-ingestor/sensor_ingestor/runtime.py`, `/metrics`)

## 6.4 센서 품질 관리
- [x] outlier rule 정의
- [x] stale sensor rule 정의
- [x] jump detection rule 정의
- [x] missing data rule 정의
- [x] quality_flag 계산기 구현 (`sensor-ingestor/sensor_ingestor/quality.py`, `sensor-ingestor/sensor_ingestor/runtime.py`)
- [x] sensor anomaly alert 연결 (`sensor-ingestor/sensor_ingestor/backends.py`, `scripts/validate_sensor_ingestor_runtime.py`)

---

# 7. 상태 추정(state-estimator)

## 7.1 특징량 정의
- [x] VPD 계산식 검증 (`state-estimator/state_estimator/features.py`, `scripts/validate_state_estimator_features.py`)
- [x] DLI 계산 방식 정의 (`state-estimator/state_estimator/features.py`, `scripts/validate_state_estimator_features.py`)
- [x] 1분 평균 정의 (`state-estimator/state_estimator/features.py`, `schemas/feature_schema.json`)
- [x] 5분 평균 정의 (`state-estimator/state_estimator/features.py`)
- [x] 10분 변화율 정의 (`state-estimator/state_estimator/features.py`, `schemas/feature_schema.json`)
- [x] 30분 변화율 정의 (`state-estimator/state_estimator/features.py`)
- [x] 관수 후 회복률 정의 (`state-estimator/state_estimator/features.py`)
- [x] 배액률 정의 (`state-estimator/state_estimator/features.py`)
- [x] 스트레스 점수 정의 (`state-estimator/state_estimator/features.py`)
- [x] 생육 단계 반영 방식 정의 (`state-estimator/state_estimator/features.py`)

## 7.2 feature builder 구현
- [x] raw sensor loader 작성 (`state-estimator/state_estimator/features.py`, `scripts/validate_state_estimator_raw_loader.py`)
- [x] aggregation 함수 작성 (`state-estimator/state_estimator/features.py`)
- [x] VPD calculator 작성 (`state-estimator/state_estimator/features.py`)
- [x] trend calculator 작성 (`state-estimator/state_estimator/features.py`)
- [x] stress score calculator 작성 (`state-estimator/state_estimator/features.py`)
- [x] substrate recovery calculator 작성 (`state-estimator/state_estimator/features.py`)
- [x] derived feature validator 작성 (`state-estimator/state_estimator/features.py`, `scripts/validate_state_estimator_features.py`, `scripts/validate_state_estimator_raw_loader.py`)
- [x] snapshot serializer 작성 (`state-estimator/state_estimator/features.py`, `scripts/validate_state_estimator_features.py`)

## 7.3 zone state 생성
- [x] current_state 조합 (`state-estimator/state_estimator/features.py`, `state-estimator/state_estimator/estimator.py`)
- [x] derived_features 조합 (`state-estimator/state_estimator/features.py`)
- [x] device_status 조합 (`state-estimator/state_estimator/features.py`)
- [x] constraints placeholder 조합 (`state-estimator/state_estimator/features.py`)
- [x] weather context 조합 (`state-estimator/state_estimator/features.py`)
- [ ] final state schema validation
- [ ] snapshot DB 저장
- [ ] state updated event 발행
- [x] state-estimator MVP 작성 (`state-estimator/state_estimator/estimator.py`, `scripts/validate_state_estimator_mvp.py`)

---

# 8. 정책 엔진(policy-engine)

## 8.1 정책 카테고리 정리
- [x] output validator hard safety/output contract 분리 문서화 (`docs/policy_output_validator_spec.md`)
- [ ] hard block 정책 정의
- [ ] approval 정책 정의
- [ ] range limit 정책 정의
- [ ] scheduling 정책 정의
- [ ] sensor quality 정책 정의
- [ ] robot safety 정책 정의

## 8.2 정책 DSL/JSON 포맷 정의
- [x] output validator rule catalog schema/seed 추가 (`schemas/policy_output_validator_rules_schema.json`, `data/examples/policy_output_validator_rules_seed.json`)
- [ ] field/operator/value 포맷 정의
- [ ] AND/OR 표현 방식 정의
- [ ] action_type 대상 지정 방식 정의
- [ ] 조건 템플릿 정의
- [ ] rule version 필드 정의
- [ ] enabled/disabled 정책 정의
- [ ] scope(zone/global) 정의

## 8.3 정책 엔진 구현
- [x] output validator runtime skeleton 작성 (`policy-engine/policy_engine/output_validator.py`, `scripts/validate_policy_output_validator.py`)
- [x] llm output -> validator -> audit log runtime skeleton 작성 (`llm-orchestrator/llm_orchestrator/runtime.py`, `scripts/validate_llm_output_validator_runtime.py`)
- [x] policy loader 작성 (`policy-engine/policy_engine/loader.py`, `scripts/validate_policy_engine_precheck.py`)
- [ ] evaluator 작성
- [ ] action constraint evaluator 작성
- [ ] state constraint evaluator 작성
- [ ] robot constraint evaluator 작성
- [ ] explanation builder 작성
- [x] blocked action event 발행 (`execution-gateway/execution_gateway/dispatch.py`, `ops-api/ops_api/models.py`, `ops-api/ops_api/app.py`, `scripts/validate_ops_api_flow.py`)
- [x] requires approval event 발행 (`execution-gateway/execution_gateway/dispatch.py`, `ops-api/ops_api/models.py`, `ops-api/ops_api/app.py`, `scripts/validate_ops_api_flow.py`)

## 8.4 기본 정책 등록
- [ ] 야간 관수 제한 정책 등록
- [ ] 센서 품질 불량 제한 정책 등록
- [ ] 과습 시 관수 금지 정책 등록
- [ ] 강풍 시 환기 제한 정책 등록
- [ ] 작업자 존재 시 로봇 금지 정책 등록
- [ ] 장치 응답 불량 시 재명령 금지 정책 등록
- [ ] setpoint 급변 제한 정책 등록

---

# 9. LLM 오케스트레이터

## 9.1 역할 정의
- [ ] evaluate_zone 호출 흐름 정의
- [ ] event-driven 호출 흐름 정의
- [ ] on-demand 호출 흐름 정의
- [ ] robot prioritization 호출 흐름 정의
- [ ] alert summary 호출 흐름 정의
- [ ] RAG retrieval 호출 흐름 정의

## 9.2 프롬프트 설계
- [ ] 시스템 프롬프트 초안 작성
- [ ] 역할 제한 문구 작성
- [ ] 안전 원칙 문구 작성
- [ ] RAG 검색 근거 우선 사용 문구 작성
- [ ] 검색 근거 부족 시 보수적 판단 문구 작성
- [ ] JSON only 출력 규칙 작성
- [ ] confidence 규칙 작성
- [ ] 불확실성 처리 규칙 작성
- [ ] follow_up 규칙 작성
- [ ] citations 출력 규칙 작성
- [ ] 장치 enum 삽입 방식 설계
- [ ] constraints 삽입 방식 설계

## 9.3 툴/함수 설계
- [x] get_zone_state 정의 (`docs/agent_tool_design.md`)
- [x] get_recent_trend 정의 (`docs/agent_tool_design.md`)
- [x] get_active_constraints 정의 (`docs/agent_tool_design.md`)
- [ ] get_device_status 정의
- [ ] get_weather_context 정의
- [x] search_cultivation_knowledge 정의 (`docs/agent_tool_design.md`)
- [ ] search_site_sop 정의
- [ ] get_retrieval_citations 정의
- [ ] get_vision_candidates 정의
- [ ] request_device_action 정의
- [ ] request_robot_task 정의
- [x] request_human_approval 정의 (`docs/agent_tool_design.md`)
- [x] log_decision 정의 (`docs/agent_tool_design.md`)

## 9.4 llm-orchestrator 구현
- [x] API client 구성 (`llm-orchestrator/llm_orchestrator/client.py`)
- [x] model config 구조 작성 (`llm-orchestrator/llm_orchestrator/client.py`)
- [x] prompt renderer 구현 (`llm-orchestrator/llm_orchestrator/service.py`, `llm-orchestrator/llm_orchestrator/prompt_catalog.py`)
- [x] rag-retriever client 구현 (`llm-orchestrator/llm_orchestrator/retriever.py`)
- [x] retrieved_context 조합 로직 작성 (`llm-orchestrator/llm_orchestrator/service.py`)
- [x] tool registry 구현 (`llm-orchestrator/llm_orchestrator/tool_registry.py`)
- [x] structured output parser 구현 (`llm-orchestrator/llm_orchestrator/response_parser.py`)
- [x] retry 전략 구현 (`llm-orchestrator/llm_orchestrator/client.py`)
- [x] timeout 전략 구현 (`llm-orchestrator/llm_orchestrator/client.py`)
- [x] malformed JSON 복구 전략 구현 (`llm-orchestrator/llm_orchestrator/response_parser.py`, `llm-orchestrator/llm_orchestrator/client.py`)
- [x] citations 저장 로직 구현 (`llm-orchestrator/llm_orchestrator/service.py`, `ops-api/ops_api/models.py`)
- [x] decision logger 구현 (`ops-api/ops_api/app.py`, `ops-api/ops_api/models.py`)
- [x] evaluation endpoint 작성 (`ops-api/ops_api/app.py`)

## 9.5 응답 검증
- [ ] action_type enum 검증
- [ ] parameter schema 검증
- [ ] confidence 범위 검증
- [ ] follow_up 필드 검증
- [ ] citations 필드 검증
- [ ] retrieval_coverage 필드 검증
- [ ] robot task schema 검증
- [ ] natural language leakage 검토
- [x] policy precheck 연결 (`policy-engine/policy_engine/precheck.py`, `execution-gateway/execution_gateway/guards.py`, `scripts/validate_execution_gateway_flow.py`, `scripts/validate_execution_dispatcher.py`)

---

# 10. 실행 게이트(execution-gateway)

## 10.1 검증 흐름 정의
- [x] schema validation 단계 정의 (`docs/execution_gateway_command_contract.md`, `schemas/device_command_request_schema.json`)
- [x] range validation 단계 정의 (`docs/execution_gateway_flow.md`, `execution-gateway/execution_gateway/guards.py`)
- [x] device availability check 단계 정의 (`docs/execution_gateway_command_contract.md`, `scripts/validate_device_command_requests.py`)
- [x] duplicate action check 단계 정의 (`docs/execution_gateway_flow.md`, `execution-gateway/execution_gateway/normalizer.py`)
- [x] cooldown check 단계 정의 (`docs/execution_gateway_flow.md`, `execution-gateway/execution_gateway/normalizer.py`)
- [x] policy re-evaluation 단계 정의 (`docs/execution_gateway_flow.md`, `execution-gateway/execution_gateway/guards.py`)
- [x] approval routing 단계 정의 (`docs/execution_gateway_flow.md`, `execution-gateway/execution_gateway/guards.py`, `docs/execution_gateway_override_contract.md`)
- [x] audit logging 단계 정의 (`docs/execution_gateway_flow.md`)

## 10.2 게이트 구현
- [x] validator 모듈 작성 (`scripts/validate_device_command_requests.py`)
- [x] command normalizer 작성 (`execution-gateway/execution_gateway/normalizer.py`)
- [x] range clamp 전략 정의 (`docs/execution_gateway_flow.md`)
- [x] duplicate detector 작성 (`execution-gateway/execution_gateway/guards.py`)
- [x] cooldown manager 작성 (`execution-gateway/execution_gateway/guards.py`)
- [x] approval handler 작성 (`execution-gateway/execution_gateway/guards.py`)
- [x] rejection reason builder 작성 (`execution-gateway/execution_gateway/guards.py`)
- [x] execution dispatcher 작성 (`execution-gateway/execution_gateway/dispatch.py`, `execution-gateway/execution_gateway/state.py`, `scripts/validate_execution_dispatcher.py`)
- [x] hard-coded safety interlock 작성 (`execution-gateway/execution_gateway/guards.py`, `scripts/validate_execution_gateway_flow.py`, `scripts/validate_execution_dispatcher.py`)

## 10.3 승인 체계
- [x] 저위험 액션 목록 확정 (`docs/approval_governance.md`)
- [x] 중위험 액션 목록 확정 (`docs/approval_governance.md`)
- [x] 고위험 액션 목록 확정 (`docs/approval_governance.md`)
- [x] 승인자 역할 정의 (`docs/approval_governance.md`)
- [x] 승인 UI 요구사항 작성 (`docs/approval_governance.md`)
- [x] 승인 timeout 정책 정의 (`docs/approval_governance.md`)
- [x] 거절 시 fallback 정책 정의 (`docs/approval_governance.md`)

---

# 11. PLC/장치 연동

## 11.1 프로토콜 설계
- [x] Device Profile registry/schema 정의 (`docs/device_profile_registry.md`, `schemas/device_profile_registry_schema.json`, `data/examples/device_profile_registry_seed.json`)
- [x] `model_profile -> profile_id` cross-check 검증기 작성 (`scripts/validate_device_profile_registry.py`)
- [x] `source_water_valve`처럼 인터록/ack가 다른 장치를 별도 profile로 분리하는 기준 정의 (`docs/device_profile_registry.md`)
- [x] site override address map schema/seed 정의 (`docs/plc_site_override_map.md`, `schemas/device_site_override_schema.json`, `data/examples/device_site_override_seed.json`)
- [x] site override 정합성 검증기 작성 (`scripts/validate_device_site_overrides.py`)
- [x] PLC 통신 방식 확인 (`docs/plc_modbus_governance.md`)
- [x] Modbus address map 확보 (`docs/plc_channel_address_registry.md`, `schemas/device_channel_address_registry_schema.json`, `data/examples/device_channel_address_registry_seed.json`, `scripts/build_device_channel_address_registry.py`, `scripts/validate_device_channel_address_registry.py`)
- [ ] OPC UA node map 확보
- [x] register/write 안전 규칙 정의 (`docs/plc_modbus_governance.md`)
- [x] readback 검증 방식 정의 (`docs/plc_modbus_governance.md`, `scripts/validate_plc_modbus_transport.py`)
- [x] 장애 코드 정의 (`docs/plc_modbus_governance.md`)

## 11.2 plc-adapter 구현
- [x] `plc-adapter` interface contract 정의 (`docs/plc_adapter_interface_contract.md`, `plc-adapter/plc_adapter/interface.py`)
- [x] profile 기반 mock adapter skeleton 구현 (`plc-adapter/plc_adapter/mock_adapter.py`, `plc-adapter/demo.py`)
- [x] profile 기반 parameter validation / ack evaluation 구현 (`plc-adapter/plc_adapter/device_profiles.py`, `plc-adapter/plc_adapter/mock_adapter.py`)
- [x] `device_id -> profile -> controller/channel` resolver 구현 (`plc-adapter/plc_adapter/device_catalog.py`, `plc-adapter/plc_adapter/site_overrides.py`, `plc-adapter/plc_adapter/resolver.py`)
- [x] `plc_tag_modbus_tcp` adapter skeleton 구현 (`docs/plc_tag_modbus_tcp_adapter.md`, `plc-adapter/plc_adapter/plc_tag_modbus_tcp.py`)
- [x] controller endpoint runtime override 구현 (`docs/plc_runtime_endpoint_config.md`, `plc-adapter/plc_adapter/runtime_config.py`, `.env.example`)
- [x] logical channel ref -> transport address resolution 구현 (`docs/plc_channel_address_registry.md`, `plc-adapter/plc_adapter/channel_address_registry.py`, `plc-adapter/plc_adapter/channel_refs.py`)
- [x] 연결 초기화 구현 (`plc-adapter/plc_adapter/plc_tag_modbus_tcp.py`, `plc-adapter/plc_adapter/transports.py`)
- [x] reconnect 로직 구현 (`plc-adapter/plc_adapter/plc_tag_modbus_tcp.py`)
- [x] write command 구현 (`plc-adapter/plc_adapter/plc_tag_modbus_tcp.py`, `plc-adapter/plc_adapter/codecs.py`)
- [x] readback 구현 (`plc-adapter/plc_adapter/plc_tag_modbus_tcp.py`, `plc-adapter/plc_adapter/codecs.py`)
- [x] timeout 처리 구현 (`plc-adapter/plc_adapter/plc_tag_modbus_tcp.py`, `plc-adapter/plc_adapter/transports.py`)
- [x] retry 처리 구현 (`plc-adapter/plc_adapter/plc_tag_modbus_tcp.py`)
- [x] ack 처리 구현 (`plc-adapter/plc_adapter/device_profiles.py`, `plc-adapter/plc_adapter/plc_tag_modbus_tcp.py`)
- [x] result mapping 구현 (`plc-adapter/plc_adapter/plc_tag_modbus_tcp.py`, `plc-adapter/plc_adapter/interface.py`)
- [x] adapter health check 작성 (`plc-adapter/plc_adapter/plc_tag_modbus_tcp.py`, `plc-adapter/plc_adapter/transports.py`)

## 11.3 장치별 명령 구현
- [x] 순환팬 명령 매핑 (`docs/device_command_mapping_matrix.md`, `data/examples/device_command_mapping_samples.jsonl`, `scripts/validate_device_command_mappings.py`)
- [x] 차광커튼 명령 매핑 (`docs/device_command_mapping_matrix.md`, `data/examples/device_command_mapping_samples.jsonl`, `scripts/validate_device_command_mappings.py`)
- [x] 관수 밸브 명령 매핑 (`docs/device_command_mapping_matrix.md`, `data/examples/device_command_mapping_samples.jsonl`, `scripts/validate_device_command_mappings.py`)
- [x] 환기창 명령 매핑 (`docs/device_command_mapping_matrix.md`, `data/examples/device_command_mapping_samples.jsonl`, `scripts/validate_device_command_mappings.py`)
- [x] 난방기 명령 매핑 (`docs/device_command_mapping_matrix.md`, `data/examples/device_command_mapping_samples.jsonl`, `scripts/validate_device_command_mappings.py`)
- [x] CO2 명령 매핑 (`docs/device_command_mapping_matrix.md`, `data/examples/device_command_mapping_samples.jsonl`, `scripts/validate_device_command_mappings.py`)
- [x] 긴급 정지 명령 분리 (`docs/execution_gateway_override_contract.md`, `schemas/control_override_request_schema.json`, `data/examples/control_override_request_samples.jsonl`, `scripts/validate_control_override_requests.py`)
- [x] 수동 override 명령 분리 (`docs/execution_gateway_override_contract.md`, `schemas/control_override_request_schema.json`, `data/examples/control_override_request_samples.jsonl`, `scripts/validate_control_override_requests.py`)

## 11.4 실행 검증
- [x] write 후 readback 비교 (`scripts/validate_plc_modbus_transport.py`)
- [x] 상태 반영 시간 측정 (`plc-adapter/plc_adapter/plc_tag_modbus_tcp.py`, `scripts/validate_plc_modbus_transport.py`)
- [x] 무응답 장치 감지 (`scripts/validate_plc_modbus_transport.py`)
- [x] 부분 성공 처리 방식 정의 (`docs/plc_modbus_governance.md`)
- [x] rollback 가능 액션 정의 (`docs/plc_modbus_governance.md`)
- [x] safe mode 전환 조건 연결 (`execution-gateway/execution_gateway/state.py`, `execution-gateway/execution_gateway/dispatch.py`, `scripts/validate_execution_safe_mode.py`)

---

# 12. API 서버 / 백엔드

## 12.1 공통 백엔드
- [x] FastAPI 프로젝트 초기화 (`ops-api/ops_api/app.py`)
- [x] settings 모듈 작성 (`ops-api/ops_api/config.py`)
- [x] logger 설정 (`ops-api/ops_api/logging.py`, `ops-api/ops_api/app.py`)
- [x] exception handler 작성 (`ops-api/ops_api/errors.py`, `ops-api/ops_api/app.py`)
- [x] response model 작성 (`ops-api/ops_api/api_models.py`, `ops-api/ops_api/app.py`)
- [x] auth 방식 정의 (`ops-api/ops_api/auth.py`, `.env.example`)
- [x] role 기반 권한 정의 (`ops-api/ops_api/auth.py`)
- [x] OpenAPI 문서 정리 (`ops-api/ops_api/app.py`, `ops-api/README.md`)

## 12.2 주요 API
- [x] GET /zones (`ops-api/ops_api/app.py`)
- [x] GET /zones/{zone_id}/state (`ops-api/ops_api/app.py`)
- [x] GET /zones/{zone_id}/history (`ops-api/ops_api/app.py`)
- [x] POST /decisions/evaluate-zone (`ops-api/ops_api/app.py`)
- [x] POST /actions/execute (`ops-api/ops_api/app.py`)
- [x] POST /actions/approve (`ops-api/ops_api/app.py`)
- [x] GET /actions/history (`ops-api/ops_api/app.py`)
- [x] GET /alerts (`ops-api/ops_api/app.py`)
- [x] GET /policies (`ops-api/ops_api/app.py`)
- [x] POST /robot/tasks (`ops-api/ops_api/app.py`)

## 12.3 테스트
- [x] API unit test 작성 (`scripts/validate_ops_api_flow.py`)
- [x] schema validation test 작성 (`scripts/validate_ops_api_schema_models.py`)
- [x] auth test 작성 (`scripts/validate_ops_api_auth.py`)
- [x] error response test 작성 (`scripts/validate_ops_api_error_responses.py`)
- [x] load test 최소 시나리오 작성 (`scripts/validate_ops_api_load_scenario.py`)
- [x] localhost server smoke 작성 (`scripts/validate_ops_api_server_smoke.py`)
- [ ] real PostgreSQL smoke 실행 (`scripts/validate_ops_api_postgres_smoke.py`)

---

# 13. 모니터링/알람/감사

## 13.1 로깅 설계
- [ ] request log 포맷 정의
- [ ] decision log 포맷 정의
- [ ] command log 포맷 정의
- [ ] robot log 포맷 정의
- [x] policy block log 포맷 정의 (`ops-api/ops_api/models.py`, `ops-api/ops_api/app.py`, `execution-gateway/execution_gateway/dispatch.py`)
- [ ] sensor anomaly log 포맷 정의

## 13.2 메트릭 설계
- [ ] sensor ingest rate
- [ ] stale sensor count
- [ ] decision latency
- [ ] malformed response count
- [x] blocked action count (`ops-api/ops_api/app.py`, `scripts/validate_ops_api_flow.py`)
- [ ] approval pending count
- [ ] command success rate
- [ ] robot task success rate
- [ ] safe mode count

## 13.3 알람 설계
- [ ] 고온 알람
- [ ] 고습 알람
- [ ] 센서 이상 알람
- [ ] 장치 무응답 알람
- [ ] 정책 차단 과다 알람
- [ ] decision 실패 알람
- [ ] robot safety 알람
- [ ] safe mode 진입 알람

## 13.4 감사 체계
- [x] decision trace 저장 (`ops-api/ops_api/models.py`, `ops-api/ops_api/app.py`)
- [x] source state 저장 (`ops-api/ops_api/models.py`, `ops-api/ops_api/app.py`)
- [x] policy evaluation 결과 저장 (`ops-api/ops_api/models.py`, `ops-api/ops_api/app.py`)
- [x] final execution 결과 저장 (`ops-api/ops_api/models.py`, `ops-api/ops_api/app.py`)
- [ ] operator override 저장
- [x] approval action 저장 (`ops-api/ops_api/models.py`, `ops-api/ops_api/app.py`)
- [x] 모델/프롬프트 버전 저장 (`ops-api/ops_api/models.py`, `ops-api/ops_api/app.py`)

---

# 14. 프론트엔드/운영 대시보드

## 14.1 기본 화면 정의
- [x] zone overview 화면 설계 (`ops-api/ops_api/app.py`)
- [x] real-time sensor 화면 설계 (`ops-api/ops_api/app.py` Zone Realtime Chart 카드 + uPlot 11 인스턴스 + `/zones/{zone_id}/stream` SSE + `/zones/{zone_id}/timeseries` bootstrap, `scripts/validate_ops_api_sse_stream.py`, `scripts/validate_ops_api_timeseries.py`, `scripts/validate_ops_api_zone_history.py`)
- [x] decision 로그 화면 설계 (`ops-api/ops_api/app.py`)
- [x] action 승인 화면 설계 (`ops-api/ops_api/app.py`)
- [x] alert 화면 설계 (`ops-api/ops_api/app.py`)
- [x] robot task 화면 설계 (`ops-api/ops_api/app.py`)
- [x] policy 관리 화면 설계 (`ops-api/ops_api/app.py`, `ops-api/ops_api/api_models.py`)

## 14.2 시각화
- [x] 온도/습도 시계열 차트 (`ops-api/ops_api/app.py` `TRACKED_SENSOR_METRICS` air_temp_c/rh_pct/vpd_kpa + `renderZoneHistory` SVG sparkline)
- [x] CO2 시계열 차트 (`ops-api/ops_api/app.py` `TRACKED_SENSOR_METRICS` co2_ppm)
- [x] 함수율/EC/pH 시계열 차트 (`ops-api/ops_api/app.py` `TRACKED_SENSOR_METRICS` substrate_moisture_pct/feed_ec_ds_m/drain_ec_ds_m/feed_ph/drain_ph, `scripts/validate_ops_api_dashboard_section14.py`)
- [x] 장치 상태 카드 (`ops-api/ops_api/app.py` `_build_dashboard_payload` zone.device_status + `renderDeviceStatus`, `scripts/validate_ops_api_dashboard_section14.py`)
- [x] 현재 제약 조건 카드 (`ops-api/ops_api/app.py` zone.active_constraints + `renderActiveConstraints`, `scripts/validate_ops_api_dashboard_section14.py`)
- [x] 최근 결정 카드 (`ops-api/ops_api/app.py`)
- [x] blocked/rejected 명령 리스트 (`ops-api/ops_api/app.py`)
- [x] shadow window summary 카드 (`ops-api/ops_api/app.py`, `ops-api/ops_api/shadow_mode.py`)
- [x] robot candidate 리스트 (`ops-api/ops_api/app.py` `GET /robot/candidates`, `_serialize_robot_candidate`, `renderRobotCandidates`, dashboard payload `robot_candidates`, `scripts/validate_ops_api_dashboard_section14.py`)

## 14.3 운영 기능
- [x] 수동 명령 입력 UI (`ops-api/ops_api/app.py` `executeAction()` JS → `POST /actions/execute`, `scripts/validate_ops_api_dashboard_section14.py`)
- [x] 자동/수동 모드 전환 UI (`ops-api/ops_api/app.py`)
- [x] 승인/거절 UI (`ops-api/ops_api/app.py`)
- [x] 주석/운영 메모 UI (`ops-api/ops_api/app.py`)
- [x] 문제 사례 태깅 UI (`ops-api/ops_api/app.py` `flagCase()` JS → `POST /shadow/reviews` with `flag:` prefix, `scripts/validate_ops_api_dashboard_section14.py` operator_review 회귀)

## 14.4 시계열 대시보드 통합
- [x] TimescaleDB backend/query 경계 설계 (`docs/timeseries_storage_dashboard_plan.md`, `docs/timescaledb_schema_design.md`)
- [x] 통합관제 웹 시계열 카드/드릴다운 화면 분리 기준 정리 (`docs/timeseries_storage_dashboard_plan.md`)
- [x] `/dashboard` 존 모니터링 뷰 시계열 drill-down 설계 (`docs/timeseries_storage_dashboard_plan.md`)
- [x] 통합관제 role/auth 문맥에서 read-only 시계열 조회 정책 정리 (`docs/timeseries_storage_dashboard_plan.md`)

## 14.5 Native Realtime SSE + uPlot 구현
- [x] 결정 문서: Grafana 임베드 supersede + 초단위 실시간 SSE/uPlot 아키텍처 고정 (`docs/native_realtime_dashboard_plan.md`)
- [x] `infra/postgres/002_timescaledb_sensor_readings.sql`: extension + `sensor_readings`/`zone_state_snapshots` hypertable + index + retention/compression policy + `zone_metric_5m`/`zone_metric_30m` continuous aggregate (`docs/timescaledb_schema_design.md` 기준)
- [x] `ops-api/ops_api/models.py`에 `SensorReadingRecord`/`ZoneStateSnapshotRecord` ORM 모델 추가 (sqlite portable PK, Float import, SQL drift validator 정렬)
- [x] `ops-api/ops_api/realtime_broker.py`: `RealtimeBroker` (asyncio.Queue fan-out, zone_id 필터, oldest-drop overflow, sync `publish_nowait` shim)
- [x] sensor-ingestor TimescaleDB writer 경로: `sensor-ingestor/sensor_ingestor/timeseries_writer.py` `TimeseriesWriter` + `SensorIngestorService.__init__(timeseries_writer=...)` + `run_once()`에서 publisher 직후 `_timeseries_write` 호출
- [x] `scripts/validate_sensor_timeseries_writer.py`: writer 6 invariant + broker fan-out + zone 필터 + overflow 회귀
- [x] `scripts/validate_postgres_schema_drift.py`를 두 SQL 파일(`001` + `002`) 동시 파싱으로 확장, Float 타입 매핑 추가
- [x] `ops-api/ops_api/realtime_broker.py` cross-loop/cross-thread safety 보강: subscriber loop 캡처 + `loop.call_soon_threadsafe` dispatch + `threading.RLock` 경계
- [x] `AppServices.realtime_broker` 필드 + `create_app` 단일 instance 부착
- [x] ops-api `GET /zones/{zone_id}/stream` (SSE, `read_runtime` 권한): ready → bootstrap(최근 N초 sensor_readings) → bootstrap_complete → broker.subscribe 기반 reading 무한 루프, 15s keepalive 코멘트, `text/event-stream + Cache-Control: no-cache + X-Accel-Buffering: no` 헤더
- [x] ops-api `GET /zones/{zone_id}/timeseries?from&to&interval=raw|1m|5m|30m`: interval에 따라 raw / on-the-fly bucket(production: `zone_metric_5m`/`zone_metric_30m`) 라우팅, 잘못된 interval/from>=to 400, header_token viewer 경로 200
- [x] iFarm 대시보드 `구역 모니터링` 뷰 uPlot 통합: 11개 지표 SVG 스파크라인을 `uPlot 1.6.30` 캔버스 11 인스턴스로 교체, `EventSource('/zones/{id}/stream')` 기반 streaming, 60s/5m/30m/6h/24h 롤링 윈도우 selector, 윈도우 변경 시 `bootstrapTimeseries` 재시드, 지수 백오프 자동 재연결, `streamStatus` chip, `존 → 구역` 표기 통일
- [x] `scripts/validate_ops_api_sse_stream.py` 회귀: ready 1 + bootstrap 4 + bootstrap_complete 1 + reading 3 시나리오, zone-b broadcast 격리, `text/event-stream` content-type, header_token 401, 7 invariant
- [x] `scripts/validate_ops_api_timeseries.py` 회귀: raw / 1m bucket / metric filter / from-to clamp / 잘못된 interval 400 / from>=to 400 / header_token 401·200, 7 invariant
- [x] `scripts/validate_ops_api_zone_history.py` hook 목록 업데이트 (Phase 4 마크업 정렬: `Zone Realtime Chart`, `bootstrapTimeseries`, `openStream`, `TRACKED_METRICS`, `historyWindow`, `uPlot`)
- [x] `validate_ops_api_flow` expected_routes에 `/zones/{zone_id}/timeseries`, `/zones/{zone_id}/stream` 추가

---

# 15. 시뮬레이터/디지털 트윈

## 15.1 시뮬레이션 목표 정의
- [ ] 환경 반응 시뮬레이션 범위 정의
- [ ] 관수 반응 시뮬레이션 범위 정의
- [ ] 차광 영향 시뮬레이션 범위 정의
- [ ] 환기 영향 시뮬레이션 범위 정의
- [ ] 센서 이상 주입 방식 정의
- [ ] 장치 stuck 주입 방식 정의

## 15.2 시나리오 구축
- [ ] 맑은 낮 시나리오
- [ ] 흐린 날 시나리오
- [ ] 급격한 일사 증가 시나리오
- [ ] 고온 외기 시나리오
- [ ] 센서 드리프트 시나리오
- [ ] 함수율 센서 고장 시나리오
- [ ] 관수 밸브 불응답 시나리오
- [ ] 네트워크 지연 시나리오
- [ ] 사람 접근 시 로봇 중지 시나리오

## 15.3 시뮬레이터 구현
- [ ] 환경 상태 모델 작성
- [ ] 장치 반응 모델 작성
- [ ] 관수 반응 모델 작성
- [ ] 잡음 주입 기능 작성
- [ ] 이벤트 주입 기능 작성
- [ ] replay runner 작성
- [ ] score calculator 작성

## 15.4 시뮬레이터 평가
- [ ] 목표 유지율 측정
- [ ] 불필요 명령 수 측정
- [ ] 차단되지 않은 위험 명령 수 측정
- [ ] 승인이 필요한 명령 비율 측정
- [ ] safe mode 진입 빈도 측정

---

# 16. 비전 파이프라인

## 16.1 데이터 준비
- [ ] 수확 대상 이미지 수집
- [ ] 숙도 레이블 정의
- [ ] 병징 레이블 정의
- [ ] occlusion 레이블 정의
- [ ] reachable 레이블 정의
- [ ] annotation 가이드 작성
- [ ] 데이터셋 분할
- [ ] 증강 전략 정의

## 16.2 모델 개발
- [ ] detection baseline 선정
- [ ] segmentation 필요성 검토
- [ ] ripeness score 모델 설계
- [ ] disease suspicion score 모델 설계
- [ ] reachable classifier 설계
- [ ] occlusion 판정 로직 설계

## 16.3 추론 서비스
- [ ] vision-inference 프로젝트 초기화
- [ ] 모델 로딩 구현
- [ ] inference endpoint 작성
- [ ] candidate schema serializer 작성
- [ ] 결과 저장 로직 작성
- [ ] 이미지 링크 저장 로직 작성

## 16.4 결과 검증
- [ ] precision/recall 계산
- [ ] 숙도 score calibration
- [ ] false positive 사례 정리
- [ ] false negative 사례 정리
- [ ] 실패 이미지 태깅 체계 정의

---

# 17. 로봇 태스크 매니저

## 17.1 작업 모델 정의
- [ ] harvest task schema 정의
- [ ] inspect task schema 정의
- [ ] skip reason schema 정의
- [ ] robot capability schema 정의
- [ ] work area schema 정의

## 17.2 후보 생성/정렬
- [ ] ripeness threshold 정의
- [ ] reachable filter 정의
- [ ] occlusion filter 정의
- [ ] disease exclusion rule 정의
- [ ] time budget rule 정의
- [ ] max target count rule 정의
- [ ] priority score 공식 정의

## 17.3 LLM 연동
- [ ] robot prioritization prompt 작성
- [ ] candidate summary 생성기 작성
- [ ] robot task JSON parser 작성
- [ ] fallback deterministic sorter 작성
- [ ] approval 필요 조건 정의

## 17.4 로봇 제어기 인터페이스
- [ ] task enqueue API 정의
- [ ] task status callback 정의
- [ ] task failure callback 정의
- [ ] emergency stop callback 정의
- [ ] human detected callback 정의

---

# 18. 테스트 전략

## 18.1 단위 테스트
- [ ] schema validator 테스트
- [ ] VPD calculator 테스트
- [ ] trend calculator 테스트
- [x] policy evaluator 테스트 (`scripts/validate_policy_engine_precheck.py`)
- [ ] action validator 테스트
- [ ] duplicate detector 테스트
- [ ] cooldown manager 테스트

## 18.2 통합 테스트
- [x] sensor → state-estimator 통합 테스트 (`scripts/validate_sensor_to_state_estimator_integration.py`, `state-estimator/state_estimator/ingestor_bridge.py`)
- [x] state-estimator → policy-engine 통합 테스트 (`scripts/validate_state_estimator_policy_flow.py`)
- [ ] RAG retrieval → llm-orchestrator 통합 테스트
- [ ] policy-engine → llm-orchestrator 통합 테스트
- [x] llm-orchestrator → execution-gateway 통합 테스트 (`scripts/validate_llm_to_execution_flow.py`)
- [ ] execution-gateway → plc-adapter 통합 테스트
- [ ] vision → robot-task-manager 통합 테스트

## 18.3 E2E 테스트
- [ ] 5분 주기 zone 평가 E2E
- [ ] RAG 근거 검색 포함 zone 평가 E2E
- [ ] 고온 이벤트 E2E
- [ ] 센서 고장 E2E
- [ ] 장치 무응답 E2E
- [ ] 로봇 후보 생성 E2E
- [ ] 승인 흐름 E2E
- [ ] safe mode 전환 E2E

## 18.4 현장 검증 테스트
- [ ] shadow mode 운영
- [ ] 사람 승인 모드 운영
- [ ] 저위험 자동 실행 운영
- [ ] 운영 로그 리뷰
- [ ] 오경보/미경보 분석
- [ ] 현장 피드백 반영

---

# 19. 배포/인프라

## 19.1 배포 전략
- [ ] Docker 이미지 작성
- [ ] docker-compose 개발환경 구성
- [ ] staging 배포 구조 설계
- [ ] production 배포 구조 설계
- [ ] 비밀정보 관리 방식 정의
- [ ] 롤백 전략 정의

## 19.2 운영 인프라
- [ ] DB 백업 정책 정의
- [ ] object storage 백업 정책 정의
- [ ] 로그 보관 정책 정의
- [ ] 메트릭 수집 인프라 구성
- [ ] 대시보드 구성
- [ ] 장애 알람 채널 연동

## 19.3 안정성
- [ ] service restart 정책 정의
- [ ] circuit breaker 검토
- [ ] queue backlog 대응 전략 정의
- [ ] network partition 대응 전략 정의
- [ ] degraded mode 정책 정의

---

# 20. 단계적 운영 전환

## 20.1 Shadow Mode
- [x] LLM은 추천만 생성 (`ops-api/ops_api/app.py`, `llm-orchestrator/llm_orchestrator/runtime.py`)
- [x] 실제 장치 제어 없음 (`ops-api/ops_api/app.py`)
- [x] 운영자 수동 비교 검토 (`ops-api/ops_api/models.py`, `ops-api/ops_api/app.py`)
- [x] 추천 적합도 기록 (`llm-orchestrator/llm_orchestrator/runtime.py`, `scripts/build_shadow_mode_report.py`)
- [x] 오판 사례 수집 (`scripts/run_shadow_mode_capture_cases.py`, `scripts/build_shadow_mode_window_report.py`)
- [x] real shadow case API 적재/조회 (`ops-api/ops_api/app.py`, `ops-api/ops_api/shadow_mode.py`, `scripts/validate_ops_api_shadow_mode.py`)

## 20.2 Approval Mode
- [x] 모든 액션 승인 후 실행 (`ops-api/ops_api/app.py`, `ops-api/ops_api/planner.py`)
- [x] 승인/거절 이유 기록 (`ops-api/ops_api/models.py`, `ops-api/ops_api/app.py`)
- [ ] 과도한 승인 요청 분석
- [ ] 승인 기준 튜닝

## 20.3 Limited Auto Mode
- [ ] 저위험 장치만 자동
- [ ] 차광 자동 적용
- [ ] 순환팬 자동 적용
- [ ] 짧은 관수 자동 적용
- [ ] rollback 가능 여부 검증

## 20.4 Expanded Auto Mode
- [ ] 더 많은 zone 적용
- [ ] 더 많은 액션 적용
- [ ] 계절별 정책 반영
- [ ] 장치 조합 전략 적용
- [ ] 운영 KPI 비교

---

# 21. 재학습/고도화

## 21.1 운영 로그 데이터화
- [ ] 좋은 결정 사례 태깅
- [ ] 나쁜 결정 사례 태깅
- [ ] blocked 사례 분류
- [ ] 승인 거절 사례 분류
- [ ] 사람 수정 사례 분류
- [ ] 센서 이상 사례 분류
- [ ] 로봇 실패 사례 분류
- [ ] 센서 변화와 작물 반응 지연시간 매핑
- [ ] 운영자 승인/거절 이유 구조화
- [ ] AI 추천과 실제 조치 차이 분석

## 21.2 데이터셋 재생성
- [ ] 운영 로그 → 학습 샘플 변환기 작성
- [ ] preference pair 생성기 검토
- [ ] 실패사례 보강 데이터 생성
- [ ] 계절/품종별 샘플 균형화
- [ ] prompt version별 성능 비교
- [ ] RAG 문서 업데이트 후보 생성
- [ ] eval regression set 자동 갱신

## 21.3 모델/정책 개선
- [x] 파인튜닝 재실행
- [ ] 시스템 프롬프트 개선
- [ ] 정책 엔진 규칙 추가
- [ ] approval threshold 튜닝
- [ ] confidence threshold 튜닝
- [ ] fallback 전략 개선
- [ ] champion/challenger 비교 평가
- [ ] 모델 승격/롤백 기록 저장

---

# 22. 권장 마일스톤

## M1. 도메인/스키마 확정
- [ ] 요구사항 문서 완료
- [ ] 센서/장치 인벤토리 완료
- [ ] state/action schema 완료
- [ ] 학습 데이터 포맷 완료

## M2. 데이터/파인튜닝 완료
- [ ] 학습셋 구축 완료
- [ ] 파인튜닝 완료
- [ ] 평가셋 통과
- [ ] JSON 출력 안정화

## M3. 센서/정책/LLM 연결 완료
- [ ] 센서 수집 완료
- [ ] state-estimator 완료
- [ ] policy-engine 완료
- [ ] llm-orchestrator 완료

## M4. 안전 실행 완료
- [ ] execution-gateway 완료
- [ ] plc-adapter 완료
- [ ] 승인 체계 완료
- [ ] shadow mode 완료

## M5. 현장 자동화 1차 완료
- [ ] approval mode 완료
- [ ] limited auto mode 완료
- [ ] KPI 측정 시작

## M6. 비전/로봇 연동 완료
- [ ] vision pipeline 완료
- [ ] robot-task-manager 완료
- [ ] 반자동 작업 성공

## M7. 운영 고도화 완료
- [ ] retraining loop 완료
- [ ] simulator/replay 검증 완료
- [ ] 확대 적용 준비 완료

---

# 23. 즉시 착수 우선순위

## 이번 주 바로 시작할 일
- [x] state schema 초안 작성 (`schemas/state_schema.json`)
- [x] action schema 초안 작성 (`schemas/action_schema.json`)
- [x] RAG 문서 범위와 메타데이터 초안 작성 (`docs/rag_source_inventory.md`, `docs/rag_indexing_plan.md`)
- [x] 적고추/건고추 재배 문서 수집 목록 작성 (`docs/rag_source_inventory.md`)
- [x] 기존 파인튜닝 데이터 재분류 (`docs/dataset_taxonomy.md`, `data/examples/`)
- [x] 행동추천 JSON 샘플 100개 작성 (`data/examples/action_recommendation_samples_batch23_seed_completion.jsonl` 포함 총 `100건`)
- [x] 금지행동 샘플 100개 작성 (`data/examples/forbidden_action_samples_batch23_seed_completion.jsonl` 포함 총 `100건`)
- [x] sensor/device inventory 문서 작성 (`docs/sensor_collection_plan.md`, `docs/sensor_installation_inventory.md`, `data/examples/sensor_catalog_seed.json`)
- [x] sensor-ingestor config/poller profile 초안 작성 (`docs/sensor_ingestor_config_spec.md`, `schemas/sensor_ingestor_config_schema.json`, `data/examples/sensor_ingestor_config_seed.json`, `scripts/validate_sensor_ingestor_config.py`)
- [x] sensor 품질 규칙과 ingestor runtime flow 문서 작성 (`docs/sensor_quality_rules_pseudocode.md`, `docs/sensor_ingestor_runtime_flow.md`)
- [x] policy 초안 20개 작성 (`data/examples/policy_output_validator_rules_seed.json` 20건, `policy-engine/policy_engine/loader.py`, `precheck.py`)
- [x] llm-orchestrator 인터페이스 초안 작성 (`llm-orchestrator/llm_orchestrator/service.py`, `runtime.py`, `prompt_catalog.py`)

## 그 다음 주
- [x] RAG vector store PoC 작성 (`scripts/build_chroma_index.py`, `scripts/rag_chroma_store.py`)
- [x] 검색 품질 평가셋 작성 (`evals/rag_retrieval_eval_set.jsonl`, `scripts/evaluate_rag_retrieval.py`)
- [x] sensor-ingestor MVP 작성 (`sensor-ingestor/main.py`, `sensor-ingestor/sensor_ingestor/runtime.py`, `sensor-ingestor/sensor_ingestor/backends.py`, `sensor-ingestor/sensor_ingestor/quality.py`)
- [x] state-estimator MVP 작성 (`state-estimator/state_estimator/estimator.py`, `feature_builder.py`, `ingestor_bridge.py`, `scripts/validate_state_estimator_mvp.py`)
- [x] policy-engine MVP 작성 (`policy-engine/policy_engine/loader.py`, `precheck.py`, `scripts/validate_policy_engine_precheck.py`)
- [x] 파인튜닝 재실행
- [x] evaluate-zone API 작성 (`ops-api/ops_api/app.py` `/decisions/evaluate-zone`, `scripts/validate_ops_api_flow.py`)
- [x] decision log 저장 구조 구현 (`ops-api/ops_api/models.py` `DecisionRecord`, `PolicyEventRecord`, `infra/postgres/001_initial_schema.sql`)

## 그 다음 단계
- [x] execution-gateway MVP 구현 (`execution-gateway/execution_gateway/dispatch.py`, `execution-gateway/execution_gateway/state.py`, `scripts/validate_execution_dispatcher.py`)
- [ ] plc-adapter 테스트 연결
- [x] approval UI 초안 작성 (`ops-api/ops_api/app.py` `_dashboard_html`, `/dashboard`, `/dashboard/data`, shadow window / alert / robot task / policy card)
- [ ] shadow mode 운영 개시  <!-- ops-api shadow capture/window 경로는 완성됐으나 실제 현장 shadow 로그 누적이 남음 -->
  - [x] ops-api `/shadow/cases/capture` + `/shadow/window` 엔드포인트 (`ops-api/ops_api/shadow_mode.py`, `scripts/validate_ops_api_shadow_mode.py`)
  - [ ] real shadow log 누적(현장 의존)

---

# 24. 최종 체크리스트

출시 전 아래 항목을 모두 만족해야 한다.

- [ ] LLM이 허용되지 않은 action_type을 출력하지 않는다
- [ ] RAG 검색 결과가 decision log에 citation으로 남는다
- [ ] 검색 근거가 부족할 때 LLM이 보수적으로 응답한다
- [ ] malformed JSON이 운영을 중단시키지 않는다
- [ ] 센서 이상 시 자동화가 안전하게 축소된다
- [ ] 장치 무응답 시 safe mode가 동작한다
- [ ] 승인 필수 액션이 우회되지 않는다
- [ ] 모든 결정과 실행이 audit log로 남는다
- [ ] 사람이 언제든 수동 override 할 수 있다
- [ ] 로봇 작업 시 사람 감지 규칙이 동작한다
- [ ] 시뮬레이터 핵심 시나리오를 통과한다
- [ ] shadow mode에서 충분한 적합도를 보였다
