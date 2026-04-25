# Pepper Smartfarm Plan V2

적고추(건고추) 온실 스마트팜 운영을 위한 농업용 LLM/제어 시스템 개발 계획 저장소입니다.

현재 이 저장소는 계획/문서 중심 저장소이며, 일부 서비스 skeleton과 검증 스크립트가 함께 포함되어 있습니다.

## 빠른 시작

다른 AI/에이전트는 아래 순서로 문서를 읽으면 됩니다.

1. `PROJECT_STATUS.md`: 현재 진행 상태, 핵심 결정, 다음 우선순위
2. `AI_MLOPS_PLAN.md`: 온실 공사 중 선행할 AI 모델 준비와 MLOps 흐름
3. `EXPERT_AI_AGENT_PLAN.md`: 적고추 재배 전주기 전문가 AI Agent 구축 단계
4. `PLAN.md`: 전체 시스템 목표, 아키텍처, 안전 원칙
5. `docs/eval_scaleup_plan.md`: `core24 + extended120/160` 평가 확장 계획
6. `docs/productization_promotion_gate.md`: blind holdout, safety invariant, field usability, shadow mode 승격 게이트
7. `docs/model_product_readiness_reassessment.md`: 모델/학습/데이터/eval 재평가와 재개 조건
8. `docs/risk_level_rubric.md`: `risk_level` 정의와 우선순위 기준
9. `docs/policy_output_validator_spec.md`: hard safety/output contract를 모델 밖으로 빼는 기준
10. `docs/critical_slice_augmentation_plan.md`: 다음 fine-tuning 전 보강해야 할 slice와 수량
11. `docs/hard_case_oversampling_plan.md`: 후속 challenger에서만 적용할 hard-case oversampling 기준
12. `docs/blind50_residual_batch14_plan.md`: blind50 validator 잔여 `12건`을 batch14 sample로 옮긴 매핑
13. `docs/offline_shadow_residual_batch17_plan.md`: offline shadow 잔여 `4건`을 batch17 sample로 옮긴 매핑
14. `docs/synthetic_shadow_day0_batch18_plan.md`: synthetic shadow day0 잔여 `4건`을 batch18 sample로 옮긴 매핑
15. `docs/runtime_integration_status.md`: orchestrator/state-estimator/API/dashboard 연결 상태
16. `docs/timeseries_storage_dashboard_plan.md`: TimescaleDB 시계열 저장/대시보드 방향
17. `docs/timescaledb_schema_design.md`: raw/snapshot/downsampling/compression 스키마 기준
18. `docs/native_realtime_dashboard_plan.md`: 초단위 실시간 SSE + uPlot 시각화 결정 (Grafana 임베드 supersede)
19. `ops-api/README.md`: 운영 API, 역할 권한, seed/bootstrap 절차
20. `docs/ops_api_postgres_runbook.md`: PostgreSQL/TimescaleDB 자동 구축과 `/dashboard` 실행 절차
21. `schedule.md`: 개정 실행 순서와 8주 일정
22. `todo.md`: 세부 작업 체크리스트
23. `WORK_LOG.md`: 진행한 작업과 커밋 이력
24. `AGENTS.md`: 문서 작성, 커밋, 보안, 작업 규칙

## 핵심 방향

- LLM은 상위 판단과 계획만 담당한다.
- 실시간 제어는 PLC, 정책 엔진, 실행 게이트, 상태기계가 담당한다.
- RAG는 재배 매뉴얼, 현장 SOP, 정책 문서처럼 바뀔 수 있는 지식을 담당한다.
- 파인튜닝은 JSON 출력, `action_type` 선택, 안전 거절, follow_up 같은 운영 행동 양식을 담당한다.
- 모든 실행은 policy-engine과 execution-gateway를 통과해야 한다.

## 현재 진행 상황

현재는 온실 공사 중인 구현 전 기획 단계이지만, AI 준비와 RAG 기반은 상당 부분 구체화되었습니다.

- 프로젝트 관리 초기화 단계: `완료`
- Phase -1 AI 준비 구축 및 MLOps 기반 설계: `설계 기준 완료`
- 대상 현장 범위 고정: `300평 연동형 비닐온실 1동`, `gh-01`
- 품종 운영 범위 고정: 건고추/고춧가루용 적고추, 1차 shortlist `왕조`, `칼탄열풍`, `조생강탄`
- 재배 환경 조건 확정: 육묘용 `Grodan Delta 6.5`, 본재배용 `Grodan GT Master`
- 낮/밤 운영 기본값 고정: 낮 `25~28℃`, 밤 `18℃ 전후`, 허용 밴드 낮 `25~30℃`/밤 `18~20℃`
- 계절별 운영 범위 정의 완료: 겨울 육묘/보온, 봄 활착, 여름 고온 억제, 가을 후기 수확 기준 반영
- 핵심 센서 1차 상용 모델 shortlist 완료: `HMP110`, `GMP252`, `SQ-522-SS`, `TEROS 12`, `Guardian Inline Wi-Fi`, `WXT536`
- 장치별 최소/최대 setpoint 범위 고정 완료: fan/vent/shade/irrigation/heater/CO2/fertigation/dehumidifier/dry-fan
- 장치 운전 경험 규칙 정리 완료: 환기-팬-차광 우선순위, 관수 펄스 원칙, CO2/난방/건조실 운전 SOP 반영
- 학습 seed 확장 완료: 7개 task family(`qa_reference`, `state_judgement`, `action_recommendation`, `forbidden_action`, `failure_response`, `robot_task_prioritization`, `alert_report`) 기준 총 `360건`
- 학습 seed 중복/모순 감사 자동화 완료: `360개` sample 기준 duplicate `0`, contradiction `0`, eval overlap `0`
- 파인튜닝 목표 재정의 완료: RAG/파인튜닝 역할 분리, 허용 `action_type`, `confidence`, `follow_up`, `retrieval_coverage` 요구 고정
- 학습/eval 합본 생성과 통계 리포트 완료: training `360건`, extended eval `200건`, blind holdout `50건`, 기본 validation 기준 eval 총 `250건`, longest sample 수동 검토 완료
- `core24`는 append-only 회귀셋으로 유지하고, `extended120` minimum benchmark는 달성했다. 현재 승격 baseline은 `extended160`이고, 최종 제품 주장 baseline은 `extended200 + blind_holdout50`이다.
- 파인튜닝 runbook 1차 완료: base model `gpt-4.1-mini-2025-04-14`, challenger `gpt-4.1-2025-04-14`, 실험명 규칙 고정
- **폐기 (2026-04-17)**: `gemini-2.5-flash` RAG-first frontier challenger 계획을 폐기했다. Phase A~E 4-way 실측에서 Gemini는 `ext 0.37 / blind 0.50`으로 `ds_v11` (0.70/0.70) 대비 열세였고, reasoning/thinking 모델이 JSON strict + instruction-heavy 결정 경로에 구조적으로 부적합함이 확정됐다. runtime alias `gemini_flash_frontier`, prompt `sft_v11_rag_frontier`, `.env` GEMINI 설정은 제거한다. 과거 평가 artifact는 역사 기록으로 보존한다.
- OpenAI SFT 실제 submit 완료: 1차 job `ftjob-2UERXn8JN2B0SDUXL1tukptl`은 학습 파일 top-level `metadata` 때문에 `invalid_file_format`로 실패했고, `messages` only 포맷으로 수정한 2차 job `ftjob-45KiYE5G2J125jSNg2QqakYm`는 `succeeded`, `batch3 + prompt_v2`를 반영한 3차 job `ftjob-ULBuPHoPBbAMah5rPdd2i334`, `batch4 + prompt_v3`를 반영한 4차 job `ftjob-MiiLGncQBHRXL2NZoBYWxMcc`도 `succeeded`
- 최신 완료 challenger `ds_v11/prompt_v5_methodfix_batch14` 재평가 완료: `core24 0.9167`, `extended120 0.7667`, `extended160 0.75`, `extended200 0.7`, `blind_holdout50 raw 0.7`, `blind_holdout50 validator 0.9`, `strict_json_rate 1.0`이다.
- 최신 완료 challenger model: `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v11-prompt-v5-methodfix-batch14-eval-v2-2026:DTryNJg3`
- `ds_v11`는 이전 baseline `ds_v9/prompt_v5_methodfix`보다 모든 frozen gate에서 개선됐다. 비교값은 `core24 0.875 -> 0.9167`, `extended120 0.7083 -> 0.7667`, `extended160 0.575 -> 0.75`, `extended200 0.51 -> 0.7`, `blind_holdout50 raw 0.32 -> 0.7`, `blind_holdout50 validator 0.76 -> 0.9`다.
- 다만 `ds_v11`도 제품 승격은 아니다. raw gate는 `blind_holdout_pass_rate 0.7`, `safety_invariant_pass_rate 0.7083`, `field_usability_pass_rate 1.0`, validator gate는 `blind_holdout_pass_rate 0.9`, `safety_invariant_pass_rate 1.0`, `field_usability_pass_rate 1.0`, `shadow_mode_status=not_run`로 모두 `hold`다.
- `ds_v11` validator 적용 후 잔여 실패는 blind50 `5건`, extended200 `42건`이다. 중심 owner는 blind50에서 `data_and_model 3`, `risk_rubric_and_data 2`, extended200에서 `risk_rubric_and_data 34`, `data_and_model 13`, `robot_contract_and_model 2`다.
- `ds_v14/prompt_v10_validator_aligned_batch19_hardcase`도 실제 제출 후 같은 frozen gate로 재평가했다. 결과 model은 `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v14-prompt-v10-validator-aligned-batch19-har:DU2VQVYz`다.
- `ds_v14` 결과는 `core24 0.8333`, `extended120 0.7167`, `extended160 0.6937`, `extended200 0.695`, `blind_holdout50 raw 0.74`, `blind_holdout50 validator 0.9`였다. blind raw는 소폭 올랐지만 extended 계열과 core가 모두 `ds_v11`보다 나빠 승격 실패로 확정했다.
- `ds_v14` raw gate는 `blind_holdout_pass_rate 0.74`, `safety_invariant_pass_rate 0.75`, validator gate는 `blind_holdout_pass_rate 0.9`, `safety_invariant_pass_rate 1.0`, `field_usability_pass_rate 1.0`, `shadow_mode_status=not_run`으로 모두 `hold`다.
- `ds_v14` validator 적용 후 잔여 실패는 blind50 `5건`, extended200 `40건`이다. blind50의 `runtime_validator_gap`은 `0`으로 닫혔고, 남은 owner는 `risk_rubric_and_data 4`, `data_and_model 2`만 남았다. extended200은 `risk_rubric_and_data 32`, `data_and_model 14`, `robot_contract_and_model 1`이다.
- `scripts/build_shadow_mode_replay_from_eval.py`로 blind50 기준 offline shadow replay도 생성했다. 최근에는 `forbidden_action`을 `decision + blocked_action_type` 계약으로 재정렬하고 replay heuristic을 다듬어 `decision_count 50`, `operator_agreement_rate 0.92`, `critical_disagreement_count 0`, `promotion_decision promote`까지 올렸다.
- 이 offline shadow replay는 `shadow_mode pass` 대체가 아니라, 실제 현장 shadow 전에 남은 의미 실패를 압축해 보는 사전 기준선이다.
- 현재 offline shadow의 실제 corrective backlog는 [shadow_mode_residual_drift_ds_v11_blind_holdout50_offline.md](/home/user/pepper-smartfarm-plan-v2/artifacts/reports/shadow_mode_residual_drift_ds_v11_blind_holdout50_offline.md:1)로 고정했고, 남은 drift `4건`은 [docs/offline_shadow_residual_batch17_plan.md](/home/user/pepper-smartfarm-plan-v2/docs/offline_shadow_residual_batch17_plan.md:1)와 batch17 sample `8건`으로 직접 역투영했다.
- `robot_task`까지 포함한 synthetic shadow `day0` seed pack도 추가했다. [shadow_mode_ds_v11_day0_seed.md](/home/user/pepper-smartfarm-plan-v2/artifacts/reports/shadow_mode_ds_v11_day0_seed.md:1) 기준 `decision_count 12`, `operator_agreement_rate 0.6667`, `critical_disagreement_count 0`, `promotion_decision hold`다.
- synthetic shadow `day0` residual owner report도 추가했다. [shadow_mode_residuals_ds_v11_day0_seed.md](/home/user/pepper-smartfarm-plan-v2/artifacts/reports/shadow_mode_residuals_ds_v11_day0_seed.md:1) 기준 남은 `4건`은 `data_and_model 3`, `robot_contract_and_model 1`이고, 원인은 `create_alert` 누락 `3`, `inspect_crop` enum drift `1`로 정리됐다.
- 이 residual `4건`은 [docs/synthetic_shadow_day0_batch18_plan.md](/home/user/pepper-smartfarm-plan-v2/docs/synthetic_shadow_day0_batch18_plan.md:1)과 batch18 sample `8건`으로 직접 역투영했다. batch18은 `ds_v12` frozen dry-run snapshot을 바꾸지 않고, 그 다음 corrective 후보의 live head에만 반영했다.
- `batch16 + batch17 + hard-case oversampling`을 묶은 다음 challenger `ds_v12/prompt_v5_methodfix_batch17_hardcase`는 dry-run package까지만 준비했다. train `815`, validation `57`, SFT format error `0`이며 실제 submit은 아직 막아 두었다.
- batch18까지 반영한 현재 live head 기준 추천 split은 train `284`, validation `60`이고, 같은 hard-case oversampling 규칙을 다시 적용한 next-only dry-run은 train `822`, validation `60`, format error `0`이다.
- batch18 live head 기준 `ds_v13/prompt_v5_methodfix_batch18_hardcase` dry-run package도 분리했다. [challenger_submit_preflight_ds_v12_ds_v13.md](/home/user/pepper-smartfarm-plan-v2/artifacts/reports/challenger_submit_preflight_ds_v12_ds_v13.md:1) 기준 현재 `ds_v12`, `ds_v13` 둘 다 `blocked`이며 공통 blocker는 `blind50 validator 0.9`, `synthetic shadow day0 hold`, `real shadow mode not_run`이다.
- 실제 운영 전환용 shadow 경로도 추가했다. [docs/real_shadow_mode_runbook.md](/home/user/pepper-smartfarm-plan-v2/docs/real_shadow_mode_runbook.md:1), `scripts/run_shadow_mode_capture_cases.py`, `scripts/build_shadow_mode_window_report.py` 기준으로 일자별 capture와 rolling window 승격 판단을 바로 만들 수 있다. 2026-04-25에는 ops-api PostgreSQL audit log 기반 seed window report [shadow_mode_ops_api_seed_window_20260425.md](artifacts/reports/shadow_mode_ops_api_seed_window_20260425.md)를 생성했고 결과는 `decision_count 24`, `operator_agreement_rate 0.6667`, `critical_disagreement_count 0`, `promotion_decision hold`다.
- submit preflight도 이 real shadow window를 직접 읽을 수 있다. `scripts/build_challenger_submit_preflight.py --real-shadow-report <window.json>` 경로로 실제 shadow 결과를 `pass / hold / rollback`으로 자동 반영한다.
- `real shadow rollback`과 blind50 validator 잔여 `5건`을 직접 역투영한 batch19도 추가했다. [docs/batch19_real_shadow_feedback_plan.md](/home/user/pepper-smartfarm-plan-v2/docs/batch19_real_shadow_feedback_plan.md:1) 기준 corrective sample `8건`과 validator-aligned `sft_v10` prompt를 묶어 `ds_v14/prompt_v10_validator_aligned_batch19_hardcase` package를 만들고 실제 submit까지 진행했다.
- 그 뒤 `policy output validator`의 citation alignment와 `forbidden_action on path loss` contract를 보정해 `runtime_validator_gap`을 `0`으로 줄였다. 같은 기준으로 남은 blind50 `5건`은 [docs/batch20_post_validator_residual_plan.md](/home/user/pepper-smartfarm-plan-v2/docs/batch20_post_validator_residual_plan.md:1)과 batch20 sample `8건`으로 다시 역투영했다.
- batch20 live head 기준 `ds_v15/prompt_v10_validator_aligned_batch20_hardcase` dry-run package도 생성했다. 현재 draft는 train `855`, validation `61`, format error `0`, manifest `ft-sft-gpt41mini-ds_v15-prompt_v10_validator_aligned_batch20_hardcase-eval_v6-20260413-152557`이다.
- [challenger_submit_preflight_ds_v15_real_shadow.md](/home/user/pepper-smartfarm-plan-v2/artifacts/reports/challenger_submit_preflight_ds_v15_real_shadow.md:1) 기준 `ds_v15`도 여전히 `blocked`이며 blocker는 `blind50 validator 0.9 < 0.95`, `synthetic shadow day0 hold`, `real shadow rollback`이다.
- submit manifest는 [ft-sft-gpt41mini-ds_v14-prompt_v10_validator_aligned_batch19_hardcase-eval_v5-20260413-113447.json](/home/user/pepper-smartfarm-plan-v2/artifacts/fine_tuning/runs/ft-sft-gpt41mini-ds_v14-prompt_v10_validator_aligned_batch19_hardcase-eval_v5-20260413-113447.json:1)이고, 결과는 `succeeded`다. 하지만 frozen gate 재평가에서 `ds_v11` baseline을 넘지 못해 rejected challenger로 남겼다.
- `ds_v9/prompt_v5_methodfix`는 이제 frozen historical baseline으로 유지한다. raw `extended200 0.51`, `blind_holdout50 0.32`였고, validator 적용 후에도 `blind_holdout50 0.76`에 그쳤다.
- `extended160` 실패군 재분류 완료: 전체 실패 `68건` 중 `34건`은 `policy_output_validator` 우선 규칙으로 직접 줄일 수 있는 타입으로 묶였다.
- `extended200` 실패군 재분류 완료: 전체 실패 `98건` 중 `50건`은 validator 외부화 우선 대상으로 묶였고, 새 tranche 실패 `25건`은 `edge/seasonal`의 unseen generalization 문제를 더 선명하게 드러냈다.
- `docs/policy_output_validator_spec.md`에 hard safety `10개`, approval/output contract `10개`를 고정했고, `scripts/simulate_policy_output_validator.py`로 오프라인 시뮬레이터도 구현했다.
- runtime validator skeleton 추가 완료: `policy-engine/policy_engine/output_validator.py`, `schemas/policy_output_validator_rules_schema.json`, `data/examples/policy_output_validator_rules_seed.json`, `scripts/validate_policy_output_validator.py`
- `llm-orchestrator/llm_orchestrator/runtime.py`를 추가해 `LLM output -> output validator -> validator audit log` runtime skeleton도 연결했다.
- `execution-gateway/execution_gateway/guards.py`에 hard-coded safety interlock을 추가했다. `worker_present`, `manual_override`, `safe_mode`, `estop`, `sensor_quality blocked`는 LLM 출력과 무관하게 execution-gateway에서 다시 차단한다.
- `state-estimator/state_estimator/estimator.py` MVP를 추가했다. `sensor_quality`가 `bad/stale/missing/flatline/communication_loss`면 기본적으로 `risk_level=unknown`, `pause_automation + request_human_check`로 올린다.
- `state-estimator/state_estimator/features.py`를 추가해 VPD, DLI, 1분/5분 평균, 10분/30분 변화율, 관수 후 회복률, 배액률, climate/rootzone stress score를 `feature_schema.json` 형태로 계산하고, raw sensor/device row를 zone snapshot으로 올리는 loader도 함께 제공한다.
- `state-estimator/state_estimator/ingestor_bridge.py`와 `scripts/validate_sensor_to_state_estimator_integration.py`를 추가해 `sensor-ingestor` MQTT outbox에서 zone snapshot/derived feature를 직접 복원하는 통합 경로를 검증했다.
- `llm-orchestrator/llm_orchestrator/service.py`를 추가해 prompt version 선택, local RAG retrieval, JSON recovery, validator 연결까지 포함한 실제 orchestrator facade를 만들었다.
- `llm-orchestrator/llm_orchestrator/tool_registry.py`, `model_registry.py`, `scripts/run_llm_orchestrator_smoke.py`를 추가해 runtime capability catalog, `champion` alias 기반 FT model 해석, stub/openai 공통 smoke 경로를 고정했다.
- `ops-api/ops_api/app.py`를 추가해 `POST /decisions/evaluate-zone`, `GET /zones`, `GET /zones/{zone_id}/history`, `GET /sensors`, `GET /devices`, `GET /policies`, `GET /policies/events`, `POST /actions/approve`, `POST /actions/execute`, `POST /shadow/reviews`, `GET /dashboard`, `GET /dashboard/data`, `GET /alerts`, `GET /robot/tasks`, `POST /robot/tasks`, `GET/POST /runtime/mode`를 제공하는 FastAPI backend를 만들었다.
- `ops-api/ops_api/shadow_mode.py`, `POST /shadow/cases/capture`, `GET /shadow/window`를 추가해 real shadow case 적재와 rolling summary 조회를 운영 API에서 직접 수행할 수 있게 했다.
- backend/database 3단계 보강 완료: `zones/sensors/devices/policies/alerts/robot_candidates/robot_tasks` 스키마와 seed bootstrap, logger/exception handler, catalog/history API를 연결했고 `scripts/bootstrap_ops_api_reference_data.py`, `scripts/validate_ops_api_flow.py`로 검증한다.
- 운영 대시보드는 `zone overview`, `alerts`, `robot tasks`, `execution history`, `decision log`, `shadow review`, `approve/reject`를 한 화면으로 묶는다.
- `ops-api`는 `policy_evaluations`, `operator_reviews`를 별도 저장해 shadow→approval 전환에 필요한 운영자 검토와 validator 결과를 같이 남긴다.
- approval dispatch 경로는 이제 `policy_events`도 저장한다. `zone_state` 제약을 dispatch raw payload로 다시 전파하고, `blocked / approval_required` 이벤트를 `/policies/events`와 dashboard summary에서 바로 볼 수 있다.
- `POST /policies/{policy_id}`와 dashboard의 `Auth Context`/`Policy Management` 패널을 추가해 현재 actor/role 확인과 policy enable/disable 토글까지 운영 화면에서 수행할 수 있게 했다.
- PostgreSQL DDL은 [infra/postgres/001_initial_schema.sql](/home/user/pepper-smartfarm-plan-v2/infra/postgres/001_initial_schema.sql:1), [infra/postgres/002_timescaledb_sensor_readings.sql](/home/user/pepper-smartfarm-plan-v2/infra/postgres/002_timescaledb_sensor_readings.sql:1), [infra/postgres/003_automation_rules.sql](/home/user/pepper-smartfarm-plan-v2/infra/postgres/003_automation_rules.sql:1)로 고정했고, [scripts/ensure_ops_api_postgres_db.py](/home/user/pepper_smartfarm_plan_v2/scripts/ensure_ops_api_postgres_db.py:1), [scripts/apply_ops_api_migrations.py](/home/user/pepper-smartfarm-plan-v2/scripts/apply_ops_api_migrations.py:1), [scripts/bootstrap_ops_api_reference_data.py](/home/user/pepper-smartfarm-plan-v2/scripts/bootstrap_ops_api_reference_data.py:1), [scripts/run_ops_api_postgres_stack.sh](/home/user/pepper_smartfarm_plan_v2/scripts/run_ops_api_postgres_stack.sh:1)로 canonical bootstrap 순서를 자동화했다.
- `.venv` + PostgreSQL 기준 [scripts/validate_ops_api_postgres_smoke.py](/home/user/pepper-smartfarm-plan-v2/scripts/validate_ops_api_postgres_smoke.py:1)와 [scripts/validate_ops_api_server_smoke.py](/home/user/pepper_smartfarm_plan_v2/scripts/validate_ops_api_server_smoke.py:1)가 모두 실전 경로 smoke 기준으로 동작한다.
- `bash -lc "set -a; source .env >/dev/null 2>&1; set +a; python3 scripts/run_llm_orchestrator_smoke.py --provider openai --model-id champion --prompt-version sft_v10"` 기준 OpenAI online smoke도 통과했다. `champion` alias는 현재 `ds_v11` FT model id로 해석되고, retrieval/strict JSON/validator 경로가 실제 응답으로 검증됐다.
- **폐기 (2026-04-17)**: Gemini runtime 경로 (`--provider gemini --model-id gemini_flash_frontier`) 계획 폐기. Phase A~E 실측 기준 Gemini는 결정 경로에 부적합함이 확정됐다. 예시 명령은 문서에서 제거되며, 관련 레지스트리 alias와 `.env` GEMINI 설정도 제거된다.
- `policy-engine/policy_engine/loader.py`, `precheck.py`를 추가해 dispatch 직전 seed policy를 다시 평가하도록 연결했다. 현재 `HSV-04` 관수 경로 degraded block, `HSV-09` fertigation approval escalation이 `execution-gateway` preflight에서 실제로 강제된다.
- batch16 safety reinforcement `30건`을 추가했다. 구성은 `worker_present 10`, `manual_override/safe_mode 10`, `critical readback/comm loss 10`이며, 모두 safety/failure 오판을 직접 겨냥한다.
- validator 시뮬레이션 결과 `ds_v9/prompt_v5_methodfix`는 `extended200 0.51 -> 0.755`, `blind_holdout50 0.32 -> 0.76`까지 개선됐다. blind50 기준 `safety_invariant_pass_rate 0.25 -> 1.0`, `field_usability_pass_rate 0.92 -> 1.0`까지 회복된다.
- 다만 validator를 붙여도 `blind_holdout_pass_rate 0.76 < 0.95`, `shadow_mode_status=not_run`이라 제품화 게이트는 계속 `hold`다.
- blind50 validator 적용 후에도 남는 실패는 `12건`이며, 중심은 `risk_level_match`, `required_action_types_present`, `required_task_types_present`다. 즉 hard safety 외부화만으로는 제품 수준에 도달하지 못한다.
- `scripts/report_validator_residual_failures.py`로 blind50 validator 잔여 실패를 owner 기준으로 다시 분류했다. 현재 잔여 `12건`은 `risk_rubric_and_data 7`, `data_and_model 2`, `robot_contract_and_model 3`이다.
- `docs/blind50_residual_batch14_plan.md`와 batch14 sample `12건`으로 blind50 잔여 `12건`을 직접 학습 보강 대상으로 옮겼다.
- `scripts/build_openai_sft_datasets.py`와 `scripts/report_risk_slice_coverage.py`는 기본 경로 사용 시 stale `combined_training_samples.jsonl`이 아니라 현재 `training_sample_files()` 집합을 직접 읽는다. 새 batch 누락을 조용히 통과시키지 않도록 파이프라인을 고쳤다.
- `ds_v11 / prompt_v5_methodfix_batch14 / eval_v2` run `ftjob-dTfcY631bh5HJJKJnI5Xi0ML`는 `succeeded`로 종료됐다. training `238`, validation `50`이며 결과 model은 `DTryNJg3`다.
- `batch15` hard-case `10건`, batch16 safety reinforcement `30건`, batch17 offline shadow residual `8건`, batch18 synthetic shadow day0 residual `8건`, batch19 real shadow feedback `8건`, batch20 post-validator residual `8건`을 추가해 이후 challenger에서 `safety_policy/failure_response/sensor_fault/robot_task`와 blind residual drift를 train-only oversampling과 함께 증폭할 준비를 마쳤다.
- `llm-orchestrator/llm_orchestrator/runtime.py`는 이제 shadow mode audit row까지 남길 수 있고, `scripts/build_shadow_mode_report.py`, `scripts/validate_shadow_mode_runtime.py`로 shadow report 요약과 승격 판단(`promote / hold / rollback`)을 자동 생성할 수 있다.
- shadow runtime은 이제 `forbidden_action`뿐 아니라 `robot_task_prioritization`도 task-specific 계약으로 비교한다. `ai_robot_task_types_after`와 `operator_robot_task_types`를 함께 남겨 `inspect_crop / skip_area / manual_review` exact enum drift를 shadow report에서 직접 볼 수 있다.
- `artifacts/fine_tuning/challenger_gate_baseline.md`에 후속 challenger가 반드시 따라야 할 공식 비교 게이트를 고정했다.
- 최신 corrective challenger `ds_v10/prompt_v8`는 로컬 manifest 기준 `cancelled` 상태이며, 완료 평가 결과는 없다.
- extended benchmark 최소치 달성 완료: eval 파일 `7종`, eval row `120건`, 분포 `expert 40 / action 16 / forbidden 12 / failure 12 / robot 8 / edge 16 / seasonal 16`
- `scripts/report_eval_set_coverage.py --promotion-baseline extended160` 기준 현재 승격 baseline은 `pass`이며, `core24` 단독 승격은 금지다.
- current champion extended120 baseline 확정: `ds_v5/prompt_v5`를 `120건` 전체에 재평가한 결과 pass rate `0.5417`, strict JSON rate `1.0`, 약한 family는 `safety_policy 0.0`, `robot_task_prioritization 0.25`, `sensor_fault 0.2`였다.
- blind holdout 1차 도입 완료: `evals/blind_holdout_eval_set.jsonl` `24건`, 현재 champion `ds_v5/prompt_v5`는 blind holdout에서도 pass rate `0.5417`로 동일하게 낮게 나왔다.
- 최신 완료 모델 blind 재평가 완료: `ds_v9/prompt_v5_methodfix`는 blind holdout `0.5`, safety invariant pass rate `0.3333`, field usability pass rate `0.9583`이다. 즉 robot contract는 일부 개선했지만 안전 invariant는 더 악화됐다.
- 제품화 게이트 재정의 완료: 승격은 이제 `extended120/160`만이 아니라 `blind holdout >= 0.95`, `safety invariant failed = 0`, `field usability failed = 0`, `shadow mode pass`를 동시에 만족해야 한다.
- 현재 champion 제품화 판정은 `hold`: blind holdout `0.5417`, safety invariant pass rate `0.5`, robot task field usability failure `3건`, shadow mode `not_run`
- 최신 training 통계 재확인 완료: sample `577건`, `safety_hard_block 56`, `sensor_unknown 29`, `evidence_incomplete_unknown 21`, `failure_safe_mode 39`, `robot_contract 65`, training rule failure `none`이다.
- 최신 targeted augmentation 완료: `state_judgement batch11 40건`, `robot_task batch4 20건`, `failure_response batch11 6건`, `state_judgement batch12 8건`, `batch13 gap fix 8건`, `batch14 residual fix 12건`, `batch15 hard-case 10건`, `batch16 safety reinforcement 30건`, `batch17 offline shadow residual 8건`, `batch18 synthetic shadow day0 residual 8건`, `batch19 real shadow feedback 8건`, `batch20 post-validator residual 8건`을 추가해 총 `360건`으로 확장했다.
- `prompt_v9` draft 추가 완료: `scripts/build_openai_sft_datasets.py`와 `scripts/evaluate_fine_tuned_model.py`에 `sft_v9`를 반영했고, OpenAI SFT draft는 train `180`, validation `14`, eval overlap `0`으로 생성됐다.
- `prompt_v9`는 아직 submit하지 않았고, 제품 수준 재평가가 끝날 때까지 다음 corrective round 후보 draft로만 유지한다.
- 제품 수준 재평가 문서화 완료: `docs/model_product_readiness_reassessment.md`에 따라 당분간 새 fine-tuning submit보다 `validation 강화`, `extended200 + blind50` frozen gate, `policy/output validator` 외부화, `failure/safety/sensor` slice 보강을 우선한다.
- `scripts/build_openai_sft_datasets.py`는 이제 `validation_ratio`, `validation_min_per_family`, `validation_selection=spread`를 지원하므로 다음 라운드부터 `validation 14` 고정을 해제할 수 있다.
- `scripts/report_eval_set_coverage.py`는 `product_total 200`과 blind holdout `50` 목표를 함께 점검하도록 보강됐다.
- `docs/risk_level_rubric.md`와 `scripts/report_risk_slice_coverage.py`를 추가해 `risk_level` 정의와 critical slice 라벨 위반을 로컬에서 바로 감사할 수 있게 했다.
- 사용자 지시 보강 완료: `safety_policy 34`, `sensor_fault 26`, `robot_task_prioritization 44`로 모두 `20+`를 넘겼다.
- training critical slice 보강은 완료됐다: `evidence incomplete unknown 10`, `failure safe_mode 16`
- 현재 남은 주요 부족분은 synthetic shadow day0 residual `4건`의 모델 출력 개선, 실제 현장 shadow mode unique case 확보, 그리고 그 이후 submit 후보 재검토다. blind50 validator 잔여 `5건`은 처리 기준이 정리됐고, extended200 validator 잔여 `42건`은 `docs/extended200_residual_priority_plan.md` 기준으로 Batch21A/B/C `42건` corrective sample 생성까지 완료됐다. ops-api seed window report는 경로 검증용이며 실제 현장 pass 근거는 아니다.
- 실제 제출 package와 현재 run 상태: [challenger_candidate_ds_v11_prompt_v5_methodfix_batch14.md](/home/user/pepper-smartfarm-plan-v2/artifacts/fine_tuning/challenger_candidate_ds_v11_prompt_v5_methodfix_batch14.md:1), [challenger_candidate_ds_v12_prompt_v5_methodfix_batch17_hardcase.md](/home/user/pepper-smartfarm-plan-v2/artifacts/fine_tuning/challenger_candidate_ds_v12_prompt_v5_methodfix_batch17_hardcase.md:1), [challenger_candidate_ds_v13_prompt_v5_methodfix_batch18_hardcase.md](/home/user/pepper-smartfarm-plan-v2/artifacts/fine_tuning/challenger_candidate_ds_v13_prompt_v5_methodfix_batch18_hardcase.md:1)
- 센서 수집 계획 상세화: `zone/device/sample_rate` 기준 정리 완료
- 센서 현장형 인벤토리 초안: 설치 수량, protocol, calibration, model_profile 반영 완료
- `sensor-ingestor` 설정 포맷 초안: poller profile, connection, binding group, publish target, health config 반영 완료
- 센서 품질 규칙과 `sensor-ingestor` runtime flow 초안 완료
- 운영 시나리오 14건과 안전 요구사항 문서화 완료
- `sensor-ingestor` 코드 skeleton 추가: dry-run poller, parser, normalizer, `/healthz`, `/metrics` 확인 완료
- `sensor-ingestor` publish backend 추가: file-backed MQTT outbox, timeseries line protocol writer, anomaly alert outbox 검증 완료
- `Device Profile` registry와 `plc-adapter` interface contract 추가 완료
- `plc-adapter` mock skeleton 추가: profile 기반 parameter validation, payload build, readback, ack evaluation 확인 완료
- `site override address map`과 `device_id -> profile -> controller/channel` resolver 추가 완료
- `plc-adapter` runtime endpoint override와 channel ref parser 추가 완료
- `logical channel ref -> Modbus address registry -> transport ref` 해석 경로 추가 완료
- `plc_tag_modbus_tcp` adapter skeleton 추가: transport, codec, timeout/retry, health check, result mapping 확인 완료
- `PymodbusTcpTransport` optional path 검증 완료: fake client 기준 write/readback, reconnect/retry, timeout, health check 확인 완료
- 대표 장치 8건 command mapping 검증 완료: fan, shade, vent, irrigation valve, heater, CO2, fertigation, source water valve
- `execution-gateway -> plc-adapter` 저수준 command contract와 샘플/validator 추가 완료
- `emergency stop` / `manual override` / `safe mode` / `auto re-entry`를 위한 override contract 추가 완료
- `execution-gateway` skeleton 추가: request normalizer, duplicate detector, cooldown manager, approval/policy preflight 확인 완료
- `execution-gateway` dispatcher 추가: control state store, adapter bridge, dispatch audit log 검증 완료
- repeated adapter timeout/fault -> `safe_mode` latch 연결 완료: zone/site scope 차단 검증 완료
- 승인 체계 문서화 완료: 위험도 분류, 승인자 역할, UI 요구사항, timeout, 거절 fallback 정리
- 도메인 데이터 taxonomy/format/curation 기준 추가 완료
- RAG seed chunk: `250개` 구축 완료
- 검색 평가셋: `110개` case로 확장 완료
- smoke test: `98건` 통과
- 검색 방식 검증 완료:
  - keyword-only: hit rate `1.0`, MRR `0.9909`
  - local TF-IDF + SVD: hit rate `1.0`, MRR `1.0`
  - Chroma local: hit rate `1.0`, MRR `0.9955`
  - Chroma OpenAI embedding: hit rate `1.0`, MRR `0.9803`
- ops-api runtime retriever 기본값은 비용 없는 `keyword`다. OpenAI embedding query는 `OPENAI_LIVE_RETRIEVER_SMOKE=1` 또는 retriever type 명시 opt-in일 때만 사용하고, `local_embed`/`local_hybrid`는 비용 없는 후보로 벤치마크 중이다.
- multi-turn contextual retrieval 전략 문서화 완료
- `region / season / cultivar / greenhouse_type` metadata filter가 JSON index와 search path에 실제 반영되도록 수정 완료
- `farm_case` 운영 로그 환류 초안 작성 완료:
  - `docs/farm_case_rag_pipeline.md`
  - `schemas/farm_case_candidate_schema.json`
- `farm_case_candidate` 샘플 10건, event window 규칙, 검증 스크립트 추가 완료:
  - `data/examples/farm_case_candidate_samples.jsonl`
  - `docs/farm_case_event_window_builder.md`
  - `scripts/validate_farm_case_candidates.py`
- 승인된 `farm_case` 후보를 RAG 청크로 변환하는 초안 추가 완료:
  - `scripts/build_farm_case_rag_chunks.py`
  - `data/rag/farm_case_seed_chunks.jsonl`
- `farm_case`가 포함된 혼합 인덱스에서 공식 지침 우선 정렬 가드레일 구현 완료:
  - `scripts/search_rag_index.py`
  - `evals/rag_official_priority_eval_set.jsonl`

## 통합제어 Web UI 실행

`ops-api` 런타임은 이제 `PostgreSQL/TimescaleDB only`다. `SQLite`는 허용하지 않는다.

- 자동 실행: `bash scripts/run_ops_api_postgres_stack.sh`
- 실행 문서: `docs/ops_api_postgres_runbook.md`
- 서비스 상세: `ops-api/README.md`

기본 접속 주소는 아래와 같다.

- health: `http://127.0.0.1:8000/health`
- dashboard: `http://127.0.0.1:8000/dashboard`

## 현재 핵심 산출물

- `data/rag/pepper_expert_seed_chunks.jsonl`: 적고추 전주기 전문가 지식 250개 청크
- `docs/cultivation_stage_subagents_20260415.md`: 재배단계별 서브에이전트 수집 범위와 stage-aware RAG 반영 기준
- `docs/grodan_delta_gt_master_yield_pest_research_20260415.md`: `Grodan Delta`/`GT Master` 기반 적고추 수량·병충해 예방 조사 메모
- `artifacts/rag_index/pepper_expert_index.json`: 로컬 RAG 인덱스
- `docs/rag_indexing_plan.md`: 인덱싱, 검색, 평가 방식
- `docs/project_bootstrap.md`: 코드명, monorepo, 공통 디렉터리 기준
- `docs/git_workflow.md`: 브랜치, PR/Issue, ADR, CHANGELOG, 릴리즈 태깅 규칙
- `docs/development_toolchain.md`: Python 3.12, pip, ruff, black, mypy, pre-commit, env 분리 기준
- `docs/post_construction_sensor_cutover.md`: 공사 완료 후 실센서 연결 전환 절차
- `docs/glossary.md`: 핵심 용어집
- `docs/naming_conventions.md`: zone/sensor/device/robot/event naming 규칙
- `docs/rag_contextual_retrieval_strategy.md`: 최근 3~5일 상태를 반영한 contextual retrieval 전략
- `docs/site_scope_baseline.md`: 대상 온실, 품종 shortlist, 낮/밤 운영 기준
- `docs/seasonal_operation_ranges.md`: 계절별 운전 목표와 위험 우선순위
- `docs/sensor_model_shortlist.md`: 핵심 센서 8종 1차 상용 모델 shortlist
- `docs/device_setpoint_ranges.md`: 장치 명령 파라미터의 최소/최대 범위와 권장 구간
- `docs/device_operation_rules.md`: 장치 운전 SOP와 공통 금지 패턴
- `docs/rag_next_steps.md`: 남은 보강 과제
- `docs/sensor_collection_plan.md`: zone, sensor, device, sample_rate, quality_flag 기준
- `docs/sensor_installation_inventory.md`: zone별 설치 수량, protocol, calibration, model_profile 기준
- `docs/sensor_ingestor_config_spec.md`: `sensor-ingestor` 설정 계약과 poller profile 기준
- `docs/sensor_quality_rules_pseudocode.md`: `quality_flag` 우선순위와 automation gate 규칙
- `docs/sensor_ingestor_runtime_flow.md`: parser -> normalizer -> publish 실행 흐름
- `sensor-ingestor/sensor_ingestor/backends.py`: MQTT/timeseries/object_store outbox backend
- `sensor-ingestor/sensor_ingestor/quality.py`: quality_flag와 anomaly reason 계산기
- `scripts/validate_sensor_ingestor_runtime.py`: publish backend와 anomaly alert 경로 검증
- `docs/device_profile_registry.md`: `model_profile`를 `plc-adapter` 실행 계약으로 쓰는 기준
- `docs/plc_adapter_interface_contract.md`: profile 기반 write/readback/ack 인터페이스 계약
- `docs/plc_site_override_map.md`: profile과 실제 현장 PLC 채널을 분리하는 site override 기준
- `docs/plc_runtime_endpoint_config.md`: controller endpoint를 환경 변수로 주입하는 기준
- `docs/plc_channel_address_registry.md`: logical channel ref를 Modbus 주소로 해석하는 기준
- `docs/plc_modbus_governance.md`: Modbus TCP, write/readback, fault/safe mode 기준
- `docs/plc_tag_modbus_tcp_adapter.md`: `plc_tag_modbus_tcp` adapter skeleton과 제약 사항
- `docs/device_command_mapping_matrix.md`: 장치별 action/parameter/encoder/ack 매핑 기준
- `docs/execution_gateway_command_contract.md`: execution-gateway가 넘기는 device command request 계약
- `docs/execution_gateway_override_contract.md`: override 전용 state transition 계약
- `docs/execution_gateway_flow.md`: execution-gateway 검증 단계와 preflight 기준
- `docs/execution_dispatcher_runtime.md`: dispatcher, control state store, audit log runtime 기준
- `docs/approval_governance.md`: 위험도별 승인 체계와 timeout/fallback 기준
- `docs/runtime_integration_status.md`: orchestrator/state-estimator/API/dashboard 연결 상태와 한계
- `execution-gateway/execution_gateway/dispatch.py`: preflight 통과 요청을 adapter/state transition으로 dispatch
- `execution-gateway/execution_gateway/state.py`: estop/manual_override/safe_mode/auto_mode 상태 저장소
- `scripts/validate_execution_dispatcher.py`: dispatcher와 audit log 경로 검증
- `state-estimator/state_estimator/features.py`: VPD/DLI/trend/rootzone stress feature builder
- `llm-orchestrator/llm_orchestrator/service.py`: prompt + retrieval + JSON recovery + validator facade
- `ops-api/ops_api/app.py`: approval mode backend와 dashboard
- `infra/postgres/001_initial_schema.sql`, `infra/postgres/002_timescaledb_sensor_readings.sql`: 운영 PostgreSQL + TimescaleDB schema
- `scripts/apply_ops_api_migrations.py`: PostgreSQL migration 적용 진입점
- `data/examples/device_profile_registry_seed.json`: 장치 타입별 `Device Profile` seed registry
- `data/examples/device_site_override_seed.json`: `gh-01` 예시 controller/channel binding seed
- `data/examples/device_channel_address_registry_seed.json`: `channel_ref -> Modbus address` seed registry
- `data/examples/device_command_mapping_samples.jsonl`: 장치별 대표 명령 sample 8건
- `data/examples/control_override_request_samples.jsonl`: override 요청 sample 5건
- `docs/operational_scenarios.md`: 정상/이상/안전 이벤트 운영 시나리오 목록
- `docs/safety_requirements.md`: 인터록, estop, 수동/자동 전환, 승인/금지 액션 기준
- `sensor-ingestor/`: `sensor-ingestor` 서비스 skeleton과 dry-run 진입점
- `plc-adapter/`: device profile registry를 읽는 mock adapter skeleton
- `plc-adapter/plc_adapter/resolver.py`: `device_id`에서 profile/controller/channel을 resolve하는 경로
- `plc-adapter/plc_adapter/channel_refs.py`: `plc_tag://...` ref parser
- `plc-adapter/plc_adapter/runtime_config.py`: PLC endpoint runtime override resolver
- `plc-adapter/plc_adapter/channel_address_registry.py`: logical ref를 transport address로 해석하는 registry loader
- `plc-adapter/plc_adapter/plc_tag_modbus_tcp.py`: `plc_tag_modbus_tcp` adapter runtime skeleton
- `plc-adapter/plc_adapter/transports.py`: transport interface, in-memory transport, optional `PymodbusTcpTransport`
- `plc-adapter/plc_adapter/codecs.py`: encoder/decoder registry
- `scripts/validate_plc_modbus_transport.py`: optional Modbus TCP transport write/readback/timeout 검증
- `docs/dataset_taxonomy.md`: 학습/eval 데이터 분류 체계
- `docs/training_data_format.md`: seed JSONL 포맷과 템플릿 기준
- `docs/fine_tuning_objectives.md`: RAG/파인튜닝 역할 분리와 운영형 출력 목표
- `docs/fine_tuning_runbook.md`: base model, 내부 버전, 실험명 규칙
- `docs/openai_fine_tuning_execution.md`: OpenAI SFT 실행, sync, 비교표 경로
- `docs/training_dataset_build.md`: training/eval 합본 생성 절차
- `docs/training_sample_manual_review.md`: class imbalance와 longest sample 수동 검토 기록
- `docs/data_curation_rules.md`: 데이터 정제와 정규화 규칙
- `docs/offline_agent_runner_spec.md`: offline runner 요구사항
- `docs/mlops_registry_design.md`: dataset/prompt/model/eval registry 규칙
- `docs/shadow_mode_report_format.md`: shadow mode 평가 리포트 형식
- `docs/farm_case_rag_pipeline.md`: 운영 로그를 `farm_case` RAG로 승격하는 절차
- `docs/farm_case_event_window_builder.md`: 운영 로그를 사건 단위 `event_window`로 묶는 규칙
- `data/rag/farm_case_seed_chunks.jsonl`: 승인된 `farm_case` 후보를 변환한 RAG 청크 샘플
- `evals/rag_official_priority_eval_set.jsonl`: `farm_case` 혼합 인덱스에서 공식 지침 우선 정렬 회귀셋
- `scripts/build_rag_index.py`, `scripts/search_rag_index.py`: 기본 인덱싱/검색
- `scripts/build_chroma_index.py`: ChromaDB 기반 vector index 생성
- `scripts/evaluate_rag_retrieval.py`, `scripts/run_rag_validation_suite.py`, `scripts/rag_smoke_test.py`: 검색 회귀 검증
- `scripts/validate_training_examples.py`: 학습/eval JSONL 구조 검증
- `scripts/audit_training_data_consistency.py`: 학습 seed 중복/잠재 모순 감사
- `scripts/build_training_jsonl.py`, `scripts/build_eval_jsonl.py`: 학습/eval 합본 JSONL 생성
- `scripts/report_training_sample_stats.py`: task/action/길이 분포 리포트 생성
- `scripts/build_openai_sft_datasets.py`: OpenAI SFT용 train/validation chat JSONL 생성
- `scripts/validate_openai_sft_dataset.py`: OpenAI SFT용 chat JSONL 검증
- `scripts/run_openai_fine_tuning_job.py`: dry-run 또는 실제 fine-tuning job 생성
- `scripts/sync_openai_fine_tuning_job.py`: fine-tuning job status/events sync
- `scripts/render_fine_tuning_comparison_table.py`: run manifest 기반 비교표 생성
- `scripts/evaluate_fine_tuned_model.py`: fine-tuned model 기준 eval JSONL 실행과 요약 리포트 생성
- `artifacts/training/combined_training_samples.jsonl`: 학습 seed 360건 합본
- `artifacts/training/combined_eval_cases.jsonl`: extended eval 200건 합본
- `artifacts/training/blind_holdout_eval_cases.jsonl`: blind holdout 50건 합본
- `artifacts/reports/training_sample_stats.json`: sample 분포/길이 통계 리포트
- `artifacts/fine_tuning/openai_sft_train.jsonl`: OpenAI SFT용 train set 133건
- `artifacts/fine_tuning/openai_sft_validation.jsonl`: OpenAI SFT용 validation set 14건
- `artifacts/fine_tuning/openai_sft_train_prompt_v9.jsonl`: `prompt_v9` OpenAI SFT용 train set 180건
- `artifacts/fine_tuning/openai_sft_validation_prompt_v9.jsonl`: `prompt_v9` OpenAI SFT용 validation set 14건
- `artifacts/fine_tuning/runs/*.json`: fine-tuning run manifest
- `artifacts/fine_tuning/fine_tuning_comparison_table.md`: fine-tuning 비교표
- `artifacts/reports/fine_tuned_model_eval_ds_v5_prompt_v5.md`: 현재 champion ds_v5/prompt_v5의 core24 eval 요약
- `artifacts/reports/fine_tuned_model_eval_ds_v5_prompt_v5.json`: 현재 champion ds_v5/prompt_v5의 core24 eval 상세 리포트
- `artifacts/reports/fine_tuned_model_eval_ds_v5_prompt_v5_extended120.md`: 현재 champion ds_v5/prompt_v5의 extended120 baseline eval 요약
- `artifacts/reports/fine_tuned_model_eval_ds_v5_prompt_v5_extended120.json`: 현재 champion ds_v5/prompt_v5의 extended120 baseline eval 상세 리포트
- `artifacts/reports/fine_tuned_model_eval_legacy_prompt.md`: v1 legacy baseline eval 요약
- `scripts/validate_farm_case_candidates.py`: `farm_case` 후보 JSONL 구조 검증
- `scripts/validate_sensor_ingestor_config.py`: `sensor-ingestor` 설정과 catalog coverage 검증
- `scripts/validate_device_profile_registry.py`: device catalog와 action schema를 기준으로 profile registry 정합성 검증
- `scripts/validate_device_site_overrides.py`: site override가 catalog/profile/controller와 맞는지 검증
- `scripts/build_device_channel_address_registry.py`: site override 기반 placeholder Modbus address map 생성
- `scripts/validate_device_channel_address_registry.py`: channel address registry가 site override와 맞는지 검증
- `scripts/validate_device_command_requests.py`: device command request가 action/catalog/profile 계약과 맞는지 검증
- `scripts/validate_device_command_mappings.py`: 장치별 명령 sample을 실제 adapter 경로로 실행 검증
- `scripts/validate_control_override_requests.py`: override request가 안전 전이 규칙과 맞는지 검증
- `scripts/validate_execution_gateway_flow.py`: normalizer/duplicate/cooldown/approval preflight 검증
- `scripts/validate_execution_safe_mode.py`: repeated timeout/fault 기준 safe mode latch 검증
- `scripts/validate_synthetic_scenarios.py`: 합성 운영 시나리오 JSONL 검증
- `scripts/build_farm_case_rag_chunks.py`: 승인된 `farm_case` 후보를 RAG chunk JSONL로 변환

## 다음 우선순위

1. 실제 운영 shadow case를 `scripts/validate_shadow_cases.py --real-case`로 검증한 뒤 request_id 유니크하게 누적해 `GET /shadow/window` 기준 real window를 채우기
2. `scripts/run_shadow_mode_ops_pipeline.py`로 검증, ops-api 적재, window report, challenger preflight 재계산을 한 번에 실행
3. real window report를 `scripts/build_challenger_submit_preflight.py --real-shadow-report`에 연결해 submit blocker를 재계산. 현재 seed window 연결 결과는 [challenger_submit_preflight_ds_v12_ds_v13_ops_api_seed_window_20260425.md](artifacts/reports/challenger_submit_preflight_ds_v12_ds_v13_ops_api_seed_window_20260425.md) 기준 `real_shadow_mode_status=hold`, `ds_v12/ds_v13 blocked`다.
4. synthetic shadow day0 residual `4건`의 모델 출력 개선 여부를 재평가하고, 재학습 없이 해결 가능한 validator/rubric 경계만 분리
5. `policy-engine` policy source versioning과 blocked/approval event UI를 추가
6. 비용 없는 retriever 후보 `local_embed`/`local_hybrid`는 benchmark만 유지하고, runtime 기본값은 `keyword`로 고정
7. shadow mode 로그가 안정화된 뒤에만 next challenger 또는 장기 데이터셋 증량 프로젝트를 결정

제어 시스템 구현은 센서 수집 계획과 AI 준비가 더 진행된 뒤 시작합니다.
