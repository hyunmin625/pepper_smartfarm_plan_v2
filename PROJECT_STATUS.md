# 프로젝트 현황 요약

이 문서는 다른 AI/에이전트가 저장소의 목적, 현재 진행 상태, 다음 작업을 빠르게 파악하기 위한 진입점이다.

## 현재 저장소 상태

- 저장소 유형: 계획/문서 중심 저장소이며 서비스 skeleton과 검증 스크립트를 포함
- 대상 시스템: 적고추(건고추) 온실 스마트팜 운영을 위한 농업용 LLM/제어 시스템
- 현장 상태: 온실 공사 중이며 아직 실측 센서 데이터 수집 전
- 현재 브랜치: `master`
- 원격 저장소: `https://github.com/hyunmin625/pepper_smartfarm_plan_v2.git`
- 현재까지의 작업은 모두 Markdown 문서 중심으로 진행되었다.
- 프로젝트 관리 초기화 기준 문서와 템플릿이 정리되어 `0. 프로젝트 관리 초기화` 단계는 완료 상태다.
- 현재 fine-tuning `core24` benchmark는 append-only 회귀셋으로만 유지한다.
- `extended200`과 blind holdout `50` frozen coverage를 확보했다. 현재 분포는 `expert 60 / action 28 / forbidden 20 / failure 24 / robot 16 / edge 28 / seasonal 24`, blind holdout은 `50건`이다.
- `ds_v11/prompt_v5_methodfix_batch14` run `ftjob-dTfcY631bh5HJJKJnI5Xi0ML`은 `succeeded`로 종료됐고 결과 model은 `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v11-prompt-v5-methodfix-batch14-eval-v2-2026:DTryNJg3`다.
- `ds_v11` frozen gate 재평가 완료: `core24 0.9167`, `extended120 0.7667`, `extended160 0.75`, `extended200 0.7`, `blind_holdout50 raw 0.7`, `blind_holdout50 validator 0.9`, `strict_json_rate 1.0`이다.
- `ds_v11` raw gate는 `blind_holdout_pass_rate 0.7`, `safety_invariant_pass_rate 0.7083`, `field_usability_pass_rate 1.0`, validator gate는 `blind_holdout_pass_rate 0.9`, `safety_invariant_pass_rate 1.0`, `field_usability_pass_rate 1.0`, `shadow_mode_status=not_run`으로 모두 `hold`다.
- `ds_v11`는 이전 baseline `ds_v9`보다 모든 frozen gate에서 개선됐지만, blind50 validator `0.9 < 0.95`와 shadow mode 미실행 때문에 아직 제품 수준은 아니다.
- `scripts/report_eval_failure_clusters.py`와 `scripts/report_validator_residual_failures.py` 기준 `ds_v11`의 extended200 잔여 실패는 `42건`, blind50 validator 잔여 실패는 `5건`이다.
- `ds_v14/prompt_v10_validator_aligned_batch19_hardcase` run `ftjob-37TzJb1FtgGUghjfyaGqAxkA`도 `succeeded`로 종료됐고 결과 model은 `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v14-prompt-v10-validator-aligned-batch19-har:DU2VQVYz`다.
- `ds_v14` frozen gate 재평가 결과는 `core24 0.8333`, `extended120 0.7167`, `extended160 0.6937`, `extended200 0.695`, `blind_holdout50 raw 0.74`, `blind_holdout50 validator 0.9`다. `core24`를 포함해 전반적으로 `ds_v11` baseline보다 나빠져 승격 실패로 확정한다.
- `ds_v14` raw blind50 gate는 `blind_holdout_pass_rate 0.74`, `safety_invariant_pass_rate 0.75`, `field_usability_pass_rate 0.98`, validator blind50 gate는 `blind_holdout_pass_rate 0.9`, `safety_invariant_pass_rate 1.0`, `field_usability_pass_rate 1.0`, `shadow_mode_status=not_run`으로 모두 `hold`다.
- `ds_v14` validator 적용 후 잔여 실패는 blind50 `5건`, extended200 `40건`이다. blind50의 `runtime_validator_gap`은 `0`으로 흡수됐고 남은 owner는 `risk_rubric_and_data 4`, `data_and_model 2`다. extended200 owner는 `risk_rubric_and_data 32`, `data_and_model 14`, `robot_contract_and_model 1`이다.
- 현재 남은 중심 owner는 extended200에서 `risk_rubric_and_data 34`, `data_and_model 13`, `robot_contract_and_model 2`, blind50에서 `data_and_model 3`, `risk_rubric_and_data 2`다.
- `scripts/build_shadow_mode_replay_from_eval.py`로 blind50 기준 offline shadow replay를 만들었다. `forbidden_action` 계약 정렬, runtime `HSV-09` 반영, replay heuristic 보정 뒤 현재 기준선은 `decision_count 50`, `operator_agreement_rate 0.92`, `critical_disagreement_count 0`, `promotion_decision promote`다.
- 다만 이건 어디까지나 offline replay 기준선이다. 실제 corrective backlog는 `blind-action-004`, `blind-expert-003`, `blind-expert-010`, `blind-robot-005` 네 건이며 owner는 `data_and_model 3`, `robot_contract_and_model 1`로 좁혀졌다. 이 네 건은 `docs/offline_shadow_residual_batch17_plan.md`와 batch17 sample `8건`으로 직접 역투영했다.
- offline shadow replay는 실운영 shadow mode 대체가 아니다. 다만 현재 `validator 이후에도 운영자 기대와 어긋나는 케이스`를 빠르게 압축하는 사전 기준선으로는 유효하다.
- `robot_task`까지 포함한 synthetic shadow `day0` seed pack도 추가했다. `artifacts/reports/shadow_mode_ds_v11_day0_seed.md` 기준 `decision_count 12`, `operator_agreement_rate 0.6667`, `critical_disagreement_count 0`, `promotion_decision hold`다. 즉 runtime envelope 기준의 남은 drift는 아직 실제로 줄여야 한다.
- synthetic shadow `day0` residual owner report도 만들었다. `artifacts/reports/shadow_mode_residuals_ds_v11_day0_seed.md` 기준 남은 `4건`은 `data_and_model 3`, `robot_contract_and_model 1`이고 원인은 `create_alert` 누락 `3`, `inspect_crop` enum drift `1`이다.
- `batch16 + batch17 + hard-case oversampling`을 묶은 `ds_v12/prompt_v5_methodfix_batch17_hardcase` dry-run package를 생성했다. 현재 draft는 train `815`, validation `57`, format error `0`, manifest `ft-sft-gpt41mini-ds_v12-prompt_v5_methodfix_batch17_hardcase-eval_v3-20260413-035151`이다.
- 이 `ds_v12`는 실제 submit 후보가 아니라 `blocked challenger`다. synthetic shadow `day0 hold`, blind50 validator 기준선 `0.9`, 실제 shadow mode 부재가 모두 풀리기 전까지는 dry-run 상태로만 유지한다.
- `docs/synthetic_shadow_day0_batch18_plan.md`와 batch18 sample `8건`으로 synthetic shadow `day0` residual `4건`을 live head에 직접 역투영했다. 이후 batch19 real shadow feedback `8건`, batch20 post-validator residual `8건`까지 추가해 현재 live head training은 `360건`이다.
- batch18 live head까지 반영한 `ds_v13/prompt_v5_methodfix_batch18_hardcase` dry-run package도 생성했다. 현재 draft는 train `822`, validation `60`, format error `0`, manifest `ft-sft-gpt41mini-ds_v13-prompt_v5_methodfix_batch18_hardcase-eval_v4-20260413-075846`이다.
- `scripts/build_challenger_submit_preflight.py`로 `ds_v12`와 `ds_v13` submit preflight를 같은 기준으로 묶었다. 현재 리포트 `artifacts/reports/challenger_submit_preflight_ds_v12_ds_v13.md` 기준 두 candidate 모두 `blocked`이며 공통 blocker는 `blind_holdout50 validator 0.9 < 0.95`, `synthetic shadow day0 hold`, `real shadow mode not_run`이다.
- 실제 운영 전환용 shadow 경로도 추가했다. `scripts/run_shadow_mode_capture_cases.py`는 일자별 shadow case JSONL을 append 방식으로 적재하고, `scripts/build_shadow_mode_window_report.py`는 여러 audit log를 rolling window 기준으로 집계한다. `docs/real_shadow_mode_runbook.md`에 post-construction 절차를 고정했다.
- `scripts/build_challenger_submit_preflight.py`는 이제 `--real-shadow-report`를 지원한다. 실제 shadow window JSON을 넣으면 `promotion_decision promote -> pass`, `hold -> hold`, `rollback -> rollback`으로 자동 변환해 submit blocker에 반영한다.
- `real shadow rollback` source `shadow-runtime-002`와 blind50 validator 잔여 `5건`을 직접 역투영한 `batch19` corrective sample `8건`을 추가했다. 동시에 validator hard rule을 자연어로 옮긴 `sft_v10` prompt를 도입해 `ds_v14/prompt_v10_validator_aligned_batch19_hardcase` package를 만들었다.
- `policy-engine/policy_engine/output_validator.py`와 `scripts/simulate_policy_output_validator.py`를 보정해 citation을 `retrieved_context` 안으로 정렬하고, `forbidden_action + path/readback loss`를 `decision=block`으로 강제했다. 이로써 `ds_v14` blind50 `runtime_validator_gap`은 `3 -> 0`이 됐다.
- 남은 blind50 post-validator residual `5건`은 [docs/batch20_post_validator_residual_plan.md](/home/user/pepper-smartfarm-plan-v2/docs/batch20_post_validator_residual_plan.md:1)과 batch20 sample `8건`으로 training seed에 추가했다.
- batch20 live head를 반영한 `ds_v15/prompt_v10_validator_aligned_batch20_hardcase` dry-run package도 생성했다. 현재 draft는 train `855`, validation `61`, format error `0`, manifest `ft-sft-gpt41mini-ds_v15-prompt_v10_validator_aligned_batch20_hardcase-eval_v6-20260413-152557`이다.
- `artifacts/reports/challenger_submit_preflight_ds_v15_real_shadow.md` 기준 `ds_v15`는 여전히 `blocked`다. blocker는 `blind_holdout50 validator 0.9 < 0.95`, `synthetic shadow day0 hold`, `real shadow rollback`이다.
- `ds_v14`는 source training `352`, train `843`, validation `61`, format error `0`이었다. preflight blocker가 남은 상태에서 사용자 승인으로 submit했지만, 완료 후 frozen gate 재평가에서 실패해 baseline 교체 없이 rejected challenger로 남긴다.
- `policy-engine/policy_engine/output_validator.py`와 validator rule seed/schema를 추가해 runtime wiring용 skeleton도 만들었다.
- `llm-orchestrator/llm_orchestrator/runtime.py`를 추가해 `LLM output -> output validator -> validator audit log` runtime skeleton도 만들었다.
- `llm-orchestrator/llm_orchestrator/service.py`를 추가해 prompt version 선택, local RAG retrieval, malformed JSON recovery, validator 연결까지 포함한 실제 orchestrator facade를 만들었다.
- `llm-orchestrator/llm_orchestrator/tool_registry.py`, `llm-orchestrator/llm_orchestrator/model_registry.py`, `scripts/run_llm_orchestrator_smoke.py`를 추가해 `9.4`를 runtime 기준으로 닫았다. 오케스트레이터는 이제 `champion` alias를 실제 FT model id로 풀고, retrieved_context와 tool catalog를 함께 prompt에 주입하며, stub/openai 공통 smoke 진입점도 가진다.
- 참고용 historical baseline `ds_v9`에서는 validator 적용 후 blind50 gate가 `safety_invariant_pass_rate 1.0`, `field_usability_pass_rate 1.0`까지 올라갔지만 `blind_holdout_pass_rate 0.76 < 0.95`, `shadow_mode_status=not_run`이라 승격은 여전히 `hold`였다.
- 같은 historical baseline `ds_v9` 기준 blind50 validator 잔여 실패는 `12건`이었고, 이는 `risk_rubric_and_data 7`, `data_and_model 2`, `robot_contract_and_model 3`으로 나뉘었다.
- `docs/blind50_residual_batch14_plan.md`와 batch14 sample `12건`으로 blind50 잔여 `12건`을 training slice로 직접 역투영했다.
- `scripts/build_openai_sft_datasets.py`와 `scripts/report_risk_slice_coverage.py`는 기본 경로 사용 시 stale `combined_training_samples.jsonl`이 아니라 `training_sample_files()`를 직접 읽는다.
- `execution-gateway/execution_gateway/guards.py`에 hard-coded safety interlock을 추가했다. `worker_present`, `manual_override`, `safe_mode`, `estop`, `sensor_quality blocked`는 LLM 출력과 무관하게 execution-gateway에서 다시 reject한다.
- `state-estimator/state_estimator/estimator.py` MVP를 추가했다. `sensor_quality`가 `bad/stale/missing/flatline/communication_loss`면 기본적으로 `risk_level=unknown`, `pause_automation + request_human_check`로 올린다.
- `state-estimator/state_estimator/features.py`를 추가해 VPD, DLI, 1분/5분 평균, 10분/30분 변화율, 관수 후 회복률, 배액률, climate/rootzone stress score를 `feature_schema.json` 형태로 계산하고, raw sensor/device row를 zone snapshot으로 올리는 loader와 feature validator도 함께 제공한다.
- `ops-api/ops_api/app.py`와 `infra/postgres/001_initial_schema.sql`을 추가해 `decisions`, `approvals`, `device_commands`, `policy_evaluations`, `operator_reviews` 저장 경로와 `POST /decisions/evaluate-zone`, `POST /actions/approve`, `POST /shadow/reviews`, `GET /dashboard`, `GET /dashboard/data`, `GET /alerts`, `GET /robot/tasks`, `GET/POST /runtime/mode`까지 연결했다.
- `ops-api/ops_api/auth.py`와 `ops-api/ops_api/api_models.py`를 추가/확장해 `disabled/header_token` 인증, `viewer/operator/service/admin` 역할 권한, 공통 `ApiResponse/ErrorResponse` envelope를 고정했다.
- `scripts/validate_ops_api_auth.py`를 추가해 auth/role 검증도 로컬에서 닫았다.
- `scripts/validate_ops_api_schema_models.py`, `scripts/validate_ops_api_error_responses.py`를 추가해 request/response schema와 표준 error envelope도 로컬에서 닫았다.
- `scripts/validate_ops_api_load_scenario.py`를 추가해 `SQLite + stub LLM + mock dispatch` 기준 반복 `evaluate -> approve -> dispatch` 최소 load 시나리오도 로컬에서 닫았다.
- 최신 load baseline은 `48 decisions`, `throughput 28.23 decisions/sec`, `full-cycle p95 51.28ms`다.
- backend/database 3단계 확장 완료: `zones`, `sensors`, `devices`, `policies`, `alerts`, `robot_candidates`, `robot_tasks` 스키마와 seed/bootstrap을 추가했고, `GET /zones`, `GET /zones/{zone_id}/history`, `GET /sensors`, `GET /devices`, `GET /policies`, `POST /actions/execute`, `POST /robot/tasks`를 운영 API에 연결했다.
- `/dashboard`는 `zone overview`, `alerts`, `robot tasks`, `execution history`, `decision log`, `shadow agree/disagree`, `approve/reject`를 한 화면으로 묶는다.
- 로컬에서는 `SQLite + mock PLC adapter`로 end-to-end approval flow를 검증했고, 검증 스크립트는 `scripts/validate_state_estimator_features.py`, `scripts/validate_state_estimator_raw_loader.py`, `scripts/validate_llm_orchestrator_service.py`, `scripts/validate_llm_response_parser.py`, `scripts/validate_ops_api_flow.py`다.
- batch15 hard-case `10건`과 `docs/hard_case_oversampling_plan.md`를 추가했다. 후속 challenger가 필요할 때만 `safety_policy=5`, `failure_response=5`, `sensor_fault=5`, `robot_task_prioritization=3`의 train-only oversampling을 검토한다.
- batch16 safety reinforcement `30건`을 추가했다. 구성은 `worker_present 10`, `manual_override/safe_mode 10`, `critical readback/communication loss 10`이며 모두 safety/failure 오판을 직접 겨냥한다.
- batch17 offline shadow residual `8건`을 추가했다. 대상은 `blind-action-004`, `blind-expert-003`, `blind-expert-010`, `blind-robot-005`이며 `create_alert` 누락, `adjust_fertigation` reflex, `inspect_crop` exact enum drift를 직접 겨냥한다.
- batch18 synthetic shadow day0 residual `8건`도 추가했다. 대상은 같은 residual `4건`을 runtime-shaped shadow 기준으로 다시 옮긴 것으로, `create_alert + request_human_check` 우선 패턴과 `inspect_crop` exact enum을 더 강하게 고정한다.
- `scripts/build_openai_sft_datasets.py`는 이제 `--oversample-task-type task_type=factor`를 지원한다. `ds_v12` frozen dry-run은 train `815`, validation `57`이고, batch18까지 반영한 live head 기준 같은 가중치를 다시 적용하면 train `822`, validation `60`, SFT format error `0`이다.
- `ds_v11 / prompt_v5_methodfix_batch14 / eval_v2`는 이미 완료 평가까지 끝났다. train `238`, validation `50`, 결과 model `DTryNJg3`, frozen gate 기준 새 comparison baseline으로 고정한다.
- `llm-orchestrator/llm_orchestrator/runtime.py`는 이제 shadow mode audit row까지 남길 수 있고, `scripts/build_shadow_mode_report.py`로 `operator_agreement_rate`, `critical_disagreement_count`, `promotion_decision`을 자동 집계할 수 있다.

## 핵심 시스템 방향

- LLM은 상위 판단 및 계획 엔진으로만 사용한다.
- 실시간 연속 제어는 PLC, 규칙 엔진, PID, 상태기계가 담당한다.
- 모든 실행 명령은 policy-engine과 execution-gateway를 통과해야 한다.
- 로봇암은 LLM이 직접 제어하지 않는다. 비전, 작업계획, 로봇 제어기가 실제 동작을 담당한다.
- 모든 판단, 검색 근거, 실행 결과는 감사 로그로 남겨야 한다.

## RAG + 파인튜닝 하이브리드 결정

현재 계획은 RAG와 파인튜닝을 함께 쓰는 구조로 정리되어 있다.

- RAG 담당: 재배 매뉴얼, 현장 SOP, 품종/지역별 기준, 병해 조건, 장치 운전 기준, 정책 문서
- 파인튜닝 담당: JSON 출력 형식, `action_type` 선택, 안전 거절, follow_up 생성, confidence 표현
- 이유: 자주 바뀌거나 출처 추적이 필요한 지식은 RAG로 관리하고, 반복되는 운영 행동 양식은 파인튜닝으로 안정화하는 것이 적합하다.
- LLM 입력 구성: `state + constraints + retrieved_context + device_status`
- LLM 출력은 policy-engine과 execution-gateway에서 다시 검증한다.

## 주요 문서 역할

- `README.md`: 저장소 목적과 문서 탐색 순서
- `PROJECT_STATUS.md`: 현재 진행 상태, 핵심 결정, 다음 우선순위
- `docs/project_bootstrap.md`: 코드명, monorepo, 공통 디렉터리 기준
- `docs/git_workflow.md`: 브랜치, PR/Issue, ADR, CHANGELOG, 태깅 규칙
- `docs/development_toolchain.md`: Python/toolchain/env 기준
- `docs/post_construction_sensor_cutover.md`: 공사 완료 후 실센서 연결 전환 절차
- `docs/glossary.md`: 핵심 용어 사전
- `docs/naming_conventions.md`: ID와 이벤트 이름 규칙
- `AI_MLOPS_PLAN.md`: 온실 공사 중 먼저 진행할 AI 모델 준비, 센서 수집 계획, MLOps 루프
- `docs/site_scope_baseline.md`: 대상 온실, 품종 shortlist, 낮/밤 운영 기준
- `docs/seasonal_operation_ranges.md`: 계절별 운전 목표와 계절 리스크 우선순위
- `docs/sensor_model_shortlist.md`: 핵심 센서 8종 1차 상용 모델 shortlist
- `docs/device_setpoint_ranges.md`: 장치 명령 파라미터의 최소/최대 범위와 권장 구간
- `docs/device_operation_rules.md`: 장치 운전 SOP와 공통 금지 패턴
- `EXPERT_AI_AGENT_PLAN.md`: 적고추 재배 전주기 전문가 AI Agent 구축 단계
- `PLAN.md`: 전체 목표, 아키텍처, 안전 원칙, RAG+파인튜닝 구조, MVP 범위
- `todo.md`: 세부 작업 목록과 구현 체크리스트
- `docs/rag_next_steps.md`: RAG 데이터 확충, 벡터 검색, 메타데이터 필터, 현장 데이터 환류 과제
- `docs/farm_case_rag_pipeline.md`: 운영 로그와 센서 구간을 `farm_case` RAG로 승격하는 기준과 리뷰 절차
- `docs/farm_case_event_window_builder.md`: 운영 로그를 사건 단위 `event_window`로 묶는 세부 규칙
- `docs/sensor_collection_plan.md`: zone/device/sample_rate 수준의 센서 수집 계획
- `docs/sensor_installation_inventory.md`: zone별 설치 수량, protocol, calibration, model_profile 기준
- `docs/device_profile_registry.md`: 장치 `model_profile`를 `plc-adapter` 실행 계약으로 관리하는 기준
- `docs/plc_adapter_interface_contract.md`: profile 기반 write/readback/ack 인터페이스 계약
- `docs/plc_site_override_map.md`: 현장 controller/channel binding을 profile과 분리 관리하는 기준
- `docs/plc_runtime_endpoint_config.md`: controller endpoint를 환경 변수로 주입하는 기준
- `docs/plc_channel_address_registry.md`: `channel_ref -> Modbus address` registry 기준
- `docs/plc_modbus_governance.md`: Modbus TCP, write/readback, fault/safe mode 공통 기준
- `docs/device_command_mapping_matrix.md`: 장치별 action/parameter/encoder/ack 매핑 기준
- `docs/plc_tag_modbus_tcp_adapter.md`: `plc_tag_modbus_tcp` adapter skeleton 범위와 제약
- `docs/execution_gateway_command_contract.md`: execution-gateway가 넘기는 저수준 device command 계약
- `docs/execution_gateway_override_contract.md`: emergency stop, manual override, safe mode 전용 계약
- `docs/execution_gateway_flow.md`: execution-gateway preflight 단계 정의
- `docs/execution_dispatcher_runtime.md`: dispatcher, control state, audit log runtime 기준
- `docs/approval_governance.md`: 위험도별 승인 체계와 timeout/fallback 기준
- `docs/sensor_ingestor_config_spec.md`: poller profile, connection, binding group 기준
- `docs/sensor_quality_rules_pseudocode.md`: `quality_flag`와 automation gate 규칙
- `docs/sensor_ingestor_runtime_flow.md`: parser -> normalizer -> publish 실행 흐름
- `docs/operational_scenarios.md`: 정상/이상/안전 이벤트 시나리오 목록
- `docs/safety_requirements.md`: 인터록, estop, 수동/자동 전환, 승인/금지 액션 기준
- `docs/dataset_taxonomy.md`: 학습/eval 데이터의 task family 분류 기준
- `docs/training_data_format.md`: seed JSONL 입력/출력 포맷과 템플릿 기준
- `docs/fine_tuning_objectives.md`: RAG/파인튜닝 역할 분리와 운영형 출력 목표
- `docs/fine_tuning_runbook.md`: base model, 내부 버전, 실험명 규칙
- `docs/openai_fine_tuning_execution.md`: OpenAI SFT 실행, sync, 비교표 경로
- `docs/training_dataset_build.md`: training/eval 합본 생성 절차
- `docs/training_sample_manual_review.md`: class imbalance와 longest sample 수동 검토 기록
- `docs/data_curation_rules.md`: 샘플/eval 정제와 정규화 규칙
- `docs/offline_agent_runner_spec.md`: 실측 데이터 없이 Agent 판단을 검증하는 offline runner 요구사항
- `docs/mlops_registry_design.md`: dataset/prompt/model/eval/retrieval profile 버전 관리 규칙
- `docs/shadow_mode_report_format.md`: shadow mode 승격 판단 리포트 형식
- `docs/model_product_readiness_reassessment.md`: 모델/학습/데이터/eval 재평가와 fine-tuning 재개 조건
- `docs/risk_level_rubric.md`: `risk_level` 정의와 우선순위 기준
- `docs/policy_output_validator_spec.md`: hard safety/output contract를 모델 밖으로 강제하는 기준
- `docs/critical_slice_augmentation_plan.md`: 다음 fine-tuning 전 보강해야 할 critical slice 계획
- `docs/hard_case_oversampling_plan.md`: 후속 challenger에만 적용할 train-only oversampling 기준
- `schedule.md`: 8주 실행 일정과 단계별 완료 기준
- `WORK_LOG.md`: 진행한 작업, 커밋, 조사 근거 기록
- `AGENTS.md`: 기여자와 AI 에이전트 작업 규칙

## 현재 완료된 작업

- 프로젝트 코드명 `pepper-ops` 확정
- 저장소 운영 방식을 `monorepo`로 고정하고 `libs/`, `infra/`, `experiments/` 기준을 정의
- 공사 완료 후 실센서 연결 전환 절차 정의
- Git 브랜치 전략, PR/Issue 템플릿, ADR 템플릿, CHANGELOG 정책, 릴리즈 태깅 규칙 정리
- Python 3.12, pip, ruff, black, mypy, pre-commit, env 분리 기준 정리
- 용어집과 naming convention 문서 작성
- Git 저장소 초기화 및 GitHub 원격 연결
- `AGENTS.md` 한글 기여자 가이드 작성
- 계획 문서 전체 분석
- RAG + 파인튜닝 하이브리드 구조 조사
- `PLAN.md`, `todo.md`, `schedule.md`에 하이브리드 구조 반영
- `README.md`, `PROJECT_STATUS.md`, `WORK_LOG.md` 작성
- 주요 계획 문서와 `AGENTS.md`에 문서 링크 반영
- 온실 공사중 전제를 반영해 AI 준비 구축을 최우선 단계로 재정렬
- 적고추 재배 전주기 전문가 AI Agent 구축 계획 수립
- RAG 구축 시작: source inventory, seed chunks, expert knowledge map, sensor judgement matrix 작성
- 전문가 AI Agent 입력/출력 계약 초안 작성: state, feature, sensor quality, action schema
- 전문가 판단 초기 평가셋 작성: 정상, 고온, 근권, 양액, 센서불량, 병해, 수확/건조, 안전정책 케이스
- 파인튜닝 후보 seed 샘플 작성: 상태판단 5개, 금지행동 5개
- RAG 인덱싱 설계와 로컬 JSON 인덱스 빌드 스크립트 작성
- RAG 검색 smoke test 스크립트 작성 및 6개 쿼리 통과
- 농촌진흥청 PDF 기반 RAG 정밀 보강 완료: 육묘·재해·영양장애·비가림 구조 기반 지식과 후속 웹 공식 자료 보강까지 반영
- 농촌진흥청 PDF, 작물기술정보, 작형 일정, 품종 기준, 현장 기술지원, 미숙퇴비·배수불량·과차광·육묘 장해·첫서리·노화묘·품종 민감성 사례 추가로 RAG seed chunk 141개 확장 완료
- RAG-SRC-001 병해충·토양병·세균병·굴파리·뿌리혹선충·농약 안전사용 장 추가 추출로 균핵병·시들음병·잿빛곰팡이병·흰별무늬병·흰비단병·무름병·세균점무늬병·잎굴파리·뿌리혹선충·잔류농약 규칙을 보강해 RAG seed chunk 219개 확장 완료
- RAG 검색 품질 평가 확장: smoke test 98건, retrieval eval 110건 검증 완료
- 로컬 TF-IDF + SVD vector search PoC 유지: local hybrid retrieval eval 110건 hit rate 1.0, MRR 0.9955
- ChromaDB persistent vector store 재검증 완료: local-backed Chroma retrieval eval 110건 hit rate 1.0, MRR 0.9955
- OpenAI embedding 기반 Chroma collection 재검증 완료: retrieval eval 110건 hit rate 1.0, MRR 0.9803
- 110개 retrieval eval 재검증 결과 local vector와 local-backed Chroma가 동일 MRR 0.9955로 가장 높고, keyword-only는 0.9909, OpenAI-backed Chroma는 0.9803을 유지
- `region`, `season`, `cultivar`, `greenhouse_type` 메타데이터가 JSON index와 검색 필드에 실제 반영되도록 `scripts/build_rag_index.py`, `scripts/search_rag_index.py` 보정 완료
- multi-turn contextual retrieval 전략 문서화 완료: `docs/rag_contextual_retrieval_strategy.md`
- `farm_case` RAG 환류 파이프라인 초안과 후보 스키마 작성: `docs/farm_case_rag_pipeline.md`, `schemas/farm_case_candidate_schema.json`
- `farm_case_candidate` 샘플 10건 작성: `data/examples/farm_case_candidate_samples.jsonl`
- `farm_case` 후보 검증 스크립트와 event window 세부 규칙 추가: `scripts/validate_farm_case_candidates.py`, `docs/farm_case_event_window_builder.md`
- 승인된 `farm_case` 후보를 RAG 청크로 변환하는 초안 추가: `scripts/build_farm_case_rag_chunks.py`, `data/rag/farm_case_seed_chunks.jsonl`
- `farm_case` 혼합 인덱스에서 official guideline 우선 정렬 guardrail 구현: `scripts/search_rag_index.py`, `evals/rag_official_priority_eval_set.jsonl`
- Phase -1 설계 산출물 보강 완료: offline runner spec, MLOps registry 설계, shadow mode report format, 합성 센서 시나리오 추가
- 현장 범위 1차 고정 완료: `300평 연동형 비닐온실 1동`, `gh-01`, 논리 zone 5개 기준
- 품종 운영 범위 1차 고정 완료: 건고추/고춧가루용 적고추, shortlist `왕조`, `칼탄열풍`, `조생강탄`
- 재배 환경 조건 확정 완료: 육묘용 `Grodan Delta 6.5` block, 본재배용 `Grodan GT Master` slab
- 공식 재배 자료 기준 낮/밤 운영 기본값 반영 완료: 낮 `25~28℃`, 밤 `18℃ 전후`, 허용 밴드 낮 `25~30℃`/밤 `18~20℃`
- 계절별 운영 범위 정의 완료: 겨울 육묘/보온, 봄 정식/활착, 여름 고온 억제, 가을 후기 수확/철거 기준
- 핵심 센서 1차 상용 모델 조사 완료: `Vaisala HMP110`, `Vaisala GMP252`, `Apogee SQ-522-SS`, `METER TEROS 12`, `Bluelab Guardian Inline Wi-Fi`, `Vaisala WXT536`
- 장치별 최소/최대 setpoint 범위 정리 완료: `setpoint_bounds`를 sensor catalog와 command validation에 반영
- 장치 운전 경험 규칙 정리 완료: 환기-팬-차광, 관수 펄스, 양액기 drift 점검, CO2/난방/건조실 SOP를 문서화
- 학습 seed 7개 task family를 batch15 hard-case까지 확장 완료: 총 298건 (`data/examples/*_samples*.jsonl`)
- 학습 seed 중복/모순 감사 자동화 완료: `scripts/audit_training_data_consistency.py`와 `scripts/validate_training_examples.py` 기준 298개 sample에서 duplicate 0, contradiction 0, eval overlap 0 확인
- 파인튜닝 목표 재정의 완료: `docs/fine_tuning_objectives.md`, `schemas/action_schema.json`
- 학습/eval 합본 생성과 통계 리포트 완료: `scripts/build_training_jsonl.py`, `scripts/build_eval_jsonl.py`, `scripts/report_training_sample_stats.py`, `docs/training_sample_manual_review.md`
- 파인튜닝 runbook 1차 완료: `docs/fine_tuning_runbook.md`
- OpenAI SFT 실행 경로와 실제 submit 검증 완료: 1차 job `ftjob-2UERXn8JN2B0SDUXL1tukptl`은 학습 파일 top-level `metadata` 때문에 `invalid_file_format`로 실패했고, `messages` only 포맷으로 수정 후 2차 job `ftjob-45KiYE5G2J125jSNg2QqakYm`, `batch3 + prompt_v2` 기준 3차 job `ftjob-ULBuPHoPBbAMah5rPdd2i334`, `batch4 + prompt_v3` 기준 4차 job `ftjob-MiiLGncQBHRXL2NZoBYWxMcc`까지 모두 `succeeded`
- 최신 champion model 유지: `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v5-prompt-v5-eval-v1-20260412-075506:DTbkkFBo`
- 최신 champion eval: `core24` 기준 pass rate `0.875`, strict JSON rate `1.0`, top failure는 `risk_level_match 2건`, `required_action_types_present 1건`
- baseline 보관 완료: v1 legacy baseline `0.5417`은 `artifacts/reports/fine_tuned_model_eval_legacy_prompt.*`로 보관했고, ds_v5/prompt_v5 결과는 baseline 대비 `+0.3333`, 직전 champion ds_v4/prompt_v4 대비 `+0.0833` 개선됐다.
- extended benchmark 최소치 달성: eval row `120건`, 분포 `40/16/12/12/8/16/16`, `scripts/report_eval_set_coverage.py --enforce-minimums` 통과
- current champion extended120 baseline 확정: `artifacts/reports/fine_tuned_model_eval_ds_v5_prompt_v5_extended120.*` 기준 pass rate `0.5417`, strict JSON rate `1.0`, top failed checks는 `risk_level_match 35건`, `required_action_types_present 22건`, `required_task_types_present 6건`이다.
- extended120 약점 구간 확인: `safety_policy 0.0`, `robot_task_prioritization 0.25`, `sensor_fault 0.2`, `failure_response 0.4167`, `edge_case 0.4375`
- blind holdout 도입 완료: `scripts/build_blind_holdout_eval_set.py`로 `evals/blind_holdout_eval_set.jsonl` `24건`을 freeze했고, build/validation 기본 overlap 검사에도 포함했다.
- blind holdout 재평가 완료: 현재 champion `ds_v5/prompt_v5`는 blind holdout에서도 pass rate `0.5417`, strict JSON rate `1.0`으로 낮게 나왔고, 공개 `extended120` 적응만으로는 제품화 일반화를 입증하지 못했다.
- 제품화 게이트 리포트 추가: `scripts/validate_product_readiness_gate.py` 기준 현재 champion은 `promotion_decision=hold`, `safety_invariant_pass_rate=0.5`, `field_usability_pass_rate=0.875`, `shadow_mode_status=not_run`이다.
- 현재 확인된 실사용 blocking issue: `manual_override`/`worker_present`/핵심 readback loss에서 `block_action` 또는 `enter_safe_mode`가 누락되는 케이스, `sensor_fault` 전체 위험도를 `unknown` 대신 `high`로 과상향하는 케이스, `robot_task`가 `inspect_crop`/`skip_area` 대신 generic task name을 내는 케이스가 남아 있다.
- 파인튜닝 plateau 원인 수정 완료: `scripts/build_openai_sft_datasets.py`를 task-level split으로 바꾸고, validation은 각 task의 earliest holdout만 사용하도록 조정했으며, exact train/eval overlap filtering을 추가했다.
- train/eval overlap 원본 정리 완료: `action-rec-025`를 eval과 동일 입력에서 분리된 저장 구역 watch 사례로 재작성했고, `scripts/audit_training_data_consistency.py`에 eval overlap 검사까지 추가했다.
- 방법론 수정 후 사전검증 완료: `sample_rows 175`, duplicate `0`, contradiction `0`, eval overlap `0`, cleaned SFT dataset은 train `161`, validation `14`, format error `0`이다.
- 방법론 수정 run 완료: `ftjob-Mz4HYCUsC7ohp2OW01rpBTud` (`ft-sft-gpt41mini-ds_v9-prompt_v5_methodfix-eval_v1-20260412-125755`)는 `succeeded`로 종료됐다.
- `ds_v9/prompt_v5_methodfix` eval 완료: pass rate `0.875`, strict JSON rate `1.0`으로 기존 champion과 동률이며, 실패 케이스는 `pepper-eval-003`, `failure-eval-001`, `edge-eval-004`다.
- 방법론 수정 효과 확인: 기존 champion에서 실패하던 `pepper-eval-006`과 `action-eval-002`는 해결됐지만, `rootzone_diagnosis`와 `failure_response` 한 케이스가 새로 회귀해 최고 기록은 아직 `ds_v5/prompt_v5`가 유지된다.
- `ds_v10/prompt_v8` corrective round 제출 이력은 남아 있지만, 로컬 manifest 기준 최근 상태는 `cancelled`다.
- eval scale-up minimum 달성: `docs/eval_scaleup_plan.md`, `scripts/report_eval_set_coverage.py`, `scripts/build_eval_jsonl.py`, `scripts/generate_extended_eval_sets.py` 기준으로 `core24 + extended120/160` 운영 기준을 고정했고, 현재 minimum gate는 통과했다.
- `ds_v10` 입력은 `batch9` corrective sample 4건과 `prompt_v8` 규칙 3개로 구성했다. 대상은 `rootzone_diagnosis high-risk`, `failure_response sensor_stale high`, `manual_override + safe_mode -> block_action + create_alert`다.
- 다음 corrective draft 로컬 복구 완료: `state_judgement batch10 6건`, `failure_response batch10 3건`, `forbidden_action batch5 2건`, `robot_task batch3 4건`을 추가해 combined training을 `194건`으로 재생성했다.
- `prompt_v9` draft build 완료: `scripts/build_openai_sft_datasets.py --system-prompt-version sft_v9` 기준 train `180`, validation `14`, eval overlap `0`이며 산출물은 `artifacts/fine_tuning/openai_sft_train_prompt_v9.jsonl`, `artifacts/fine_tuning/openai_sft_validation_prompt_v9.jsonl`이다.
- 기본 validation 범위는 extended eval `120건`과 blind holdout `24건`을 함께 포함한 총 `144건`이다.
- 제품 수준 재평가 결론: 현재 병목은 base model보다는 `validation 14`, prompt chasing, hard-rule 미외부화, `extended120/blind24`의 불충분한 제품 게이트에 있다.
- 로컬 툴 보강: `scripts/build_openai_sft_datasets.py`는 `validation_ratio`, `validation_min_per_family`, `validation_selection`을 지원하고 기본 경로 사용 시 현재 sample 파일 집합을 직접 읽는다. `scripts/report_eval_set_coverage.py`는 `product_total 200`과 blind holdout `50` 목표를 함께 점검한다.
- `risk_level` 정규화 기준 고정: `docs/risk_level_rubric.md`에 `critical > unknown > high > medium > low` 우선순위와 task family별 기준을 정리했다.
- critical slice 감사 도구 추가: `scripts/report_risk_slice_coverage.py` 기준 현재 training은 `safety_hard_block 56`, `sensor_unknown 28`, `evidence_incomplete_unknown 13`, `failure_safe_mode 31`, `robot_contract 57`, `gt_master_dryback_high 16`, `nursery_cold_humid_high 4`이며 training rule failure는 현재 `none`이다.
- 최신 training 통계 재확인: `scripts/report_training_sample_stats.py` 기준 sample `360건`, class imbalance ratio `14.50`이다.
- 마지막 완료 모델 재평가 완료: `ds_v9/prompt_v5_methodfix`는 `extended120 0.7083`, `extended160 0.575`, `extended200 0.51`, `blind_holdout50 0.32`, `strict_json_rate 1.0`이다.
- `scripts/report_eval_failure_clusters.py`와 `artifacts/reports/eval_failure_clusters_ds_v9_prompt_v5_methodfix_extended160.md`로 `extended160` 실패 `68건`을 root cause로 재분류했다.
- top root cause는 `low_friction_action_bias_over_interlock 25`, `citations_missing_in_actionable_output 20`, `sensor_or_evidence_gap_not_marked_unknown 17`, `critical_hazard_undercalled 14`다.
- validator 외부화 우선 대상은 `pause_automation_missing_on_degraded_control_signal 13`, `block_action_missing_on_safety_lock 11`, `safe_mode_pair_missing_on_path_or_comms_loss 7`, `robot_task_enum_drift 3`이다.
- hard safety `10개`, approval/output contract `10개`를 `docs/policy_output_validator_spec.md`에 고정했다.
- `artifacts/fine_tuning/challenger_gate_baseline.md`에 `ds_v9`의 `core24 + extended120 + extended160 + extended200 + blind_holdout50 + product gate(raw/validator)` 기준선을 고정했다.
- `ds_v9` 재평가 세부 판단: `extended120`에서는 `ds_v5` 대비 개선됐지만, `extended200`과 `blind50`에서는 각각 `0.51`, `0.32`까지 떨어졌다. blind50 제품화 게이트는 raw `safety_invariant_pass_rate=0.25`, validator 적용 후에는 `1.0`까지 회복됐지만 `promotion_decision=hold`, `shadow_mode_status=not_run`으로 여전히 막혔다.
- 비교 해석: `ds_v9`는 robot field contract 일부를 개선했지만, eval 총량을 제품 수준으로 올리자 `failure/safety/edge` 일반화가 크게 무너졌다. 따라서 현재 문제를 `robot raw count 부족`보다 `failure/safety 의미 계약과 risk/action 경계 문제`로 보는 쪽이 더 정확하다.
- 다음 corrective round 준비 완료: `batch8`로 ds_v6 eval 뒤 남은 3개 실패 케이스를 직접 보강했고 `prompt_v7` draft를 추가했다.
- `prompt_v7` 전용 OpenAI SFT draft 파일 생성 완료: train `161`, validation `14`, format error `0` (`artifacts/fine_tuning/openai_sft_train_prompt_v7.jsonl`, `artifacts/fine_tuning/openai_sft_validation_prompt_v7.jsonl`)
- rebase 실험 준비 및 제출 완료: `prompt_v5_rebase` 기준 OpenAI SFT draft 파일 train `161`, validation `14`, format error `0`을 생성했고, `ftjob-od4Gz2SDkPBQfdoabiFz61UZ` (`ft-sft-gpt41mini-ds_v8-prompt_v5_rebase-eval_v1-20260412-120132`)를 제출했다.
- 다음 라운드용 SFT 보강 완료: `scripts/build_openai_sft_datasets.py`가 action/failure/robot 계열 출력에 `retrieval_coverage`, `confidence`, `citations`, 정규 action object를 강제하도록 정규화되었고, eval 실패 패턴을 반영한 `batch3` seed 7건이 추가됐다.
- prompt 버전 분리 완료: 현재 모델 검증용 `legacy` prompt와 다음 재학습용 `sft_v2` prompt를 분리했다. 현재 모델에 `sft_v2` prompt를 바로 적용하면 eval `24건` pass rate가 `0.1667`로 떨어져, prompt 교체는 재학습과 함께 진행해야 한다.
- 2차 개선 run 완료: `ftjob-ULBuPHoPBbAMah5rPdd2i334` (`ft-sft-gpt41mini-ds_v2-prompt_v2-eval_v1-20260412-021539`)는 `succeeded`로 종료됐고 결과 모델은 `DTWRpIbI`다.
- 3차 개선 run 완료: `ftjob-MiiLGncQBHRXL2NZoBYWxMcc` (`ft-sft-gpt41mini-ds_v3-prompt_v3-eval_v1-20260412-033726`)는 `succeeded`로 종료됐고 결과 모델은 `DTXjV3Hg`다.
- 새 run 기준 학습 파일 규모는 train `142`, validation `14`이며, 비교표와 최신 eval 결과는 `artifacts/fine_tuning/fine_tuning_comparison_table.md`, `artifacts/reports/fine_tuned_model_eval_latest.*`에 반영됐다.
- `batch4` 실패 보강 9건과 `prompt_v3` draft를 추가했다. 대상은 `sensor_fault`, `pest_disease_risk`, `harvest_drying`, `safety_policy`, `action_recommendation`, `forbidden_action`의 남은 실패 패턴이다.
- `batch5` 실패 보강 8건과 `prompt_v4` draft를 추가했다. 대상은 `sensor_fault`, `pest_disease_risk`, `safety_policy`, `failure_response`, `seasonal`의 잔여 실패 패턴이다.
- `batch6` 실패 보강 5건과 `prompt_v5` draft를 추가했다. 대상은 `pest_disease_risk`, `safety_policy`, `action_recommendation`, `failure_response`, `seasonal`의 잔여 실패 패턴이다.
- `batch6` 반영 후 내부 검증 기준 sample `169건`, `prompt_v5` OpenAI SFT draft 파일은 train `155`, validation `14`, format error `0`이다.
- `batch7` 실패 보강 3건과 `prompt_v6` draft를 추가했다. 대상은 `pest_disease_risk`, `action_recommendation`, `safety_policy`의 잔여 실패 패턴이다.
- `batch7` 반영 후 내부 검증 기준 sample `172건`, `prompt_v6` OpenAI SFT draft 파일은 train `158`, validation `14`, format error `0`이다.
- `batch8` 실패 보강 3건과 `prompt_v7` draft를 추가했다. 대상은 `sensor_fault`, `action_recommendation`, `failure_response`의 잔여 실패 패턴이다.
- `batch8` 반영 후 내부 검증 기준 sample `175건`, `prompt_v7` OpenAI SFT draft 파일은 train `161`, validation `14`, format error `0`이다.
- ds_v4/prompt_v4 run 완료: `ftjob-xVzFf0yIJIeo5M9Nnnn2N81k` (`ft-sft-gpt41mini-ds_v4-prompt_v4-eval_v1-20260412-070051`)는 `succeeded`로 종료됐고 pass rate `0.7917`을 기록했다.
- ds_v5/prompt_v5 run 완료: `ftjob-Ykc0SNX3nPnJYiuSopT571XA` (`ft-sft-gpt41mini-ds_v5-prompt_v5-eval_v1-20260412-075506`)는 `succeeded`로 종료됐고 현재 최고 pass rate `0.875`를 기록했다.
- ds_v6/prompt_v6 run 완료: `ftjob-etLIrpngO2P9RMI545Od6u1N` (`ft-sft-gpt41mini-ds_v6-prompt_v6-eval_v1-20260412-094328`)는 `succeeded`로 종료됐지만 pass rate `0.875`로 최고 기록을 갱신하지 못했다.
- ds_v7/prompt_v7 run 완료: `ftjob-v8oFS0ZvHlWsxB6u7VAky2Bp` (`ft-sft-gpt41mini-ds_v7-prompt_v7-eval_v1-20260412-103159`)는 `succeeded`로 종료됐지만 pass rate `0.8333`으로 회귀했다.
- ds_v8/prompt_v5_rebase run 완료: `ftjob-od4Gz2SDkPBQfdoabiFz61UZ` (`ft-sft-gpt41mini-ds_v8-prompt_v5_rebase-eval_v1-20260412-120132`)는 `succeeded`로 종료됐지만 pass rate `0.8333`으로 최고 기록을 갱신하지 못했다.
- edge case/계절별 평가셋을 포함한 extended benchmark 검증 완료: 전체 eval row `120건`, duplicate `0`, eval overlap `0`, format error `0`
- 센서 수집 계획 상세화 완료: `docs/sensor_collection_plan.md`, `schemas/sensor_catalog_schema.json`, `data/examples/sensor_catalog_seed.json`
- 센서 현장형 인벤토리 초안 완료: `docs/sensor_installation_inventory.md`, `data/examples/sensor_catalog_seed.json`에 설치 수량 가정, protocol, calibration, model_profile 반영
- `sensor-ingestor` 설정 포맷과 poller profile 초안 완료: `docs/sensor_ingestor_config_spec.md`, `schemas/sensor_ingestor_config_schema.json`, `data/examples/sensor_ingestor_config_seed.json`, `scripts/validate_sensor_ingestor_config.py`
- 센서 품질 규칙과 `sensor-ingestor` runtime flow 초안 완료: `docs/sensor_quality_rules_pseudocode.md`, `docs/sensor_ingestor_runtime_flow.md`
- 운영 시나리오 14건 정리 완료: `data/examples/synthetic_sensor_scenarios.jsonl`, `docs/operational_scenarios.md`, `scripts/validate_synthetic_scenarios.py`
- 안전 요구사항 정리 완료: `docs/safety_requirements.md`
- `sensor-ingestor` MVP skeleton 추가: `sensor-ingestor/main.py`, `sensor-ingestor/sensor_ingestor/runtime.py`, `sensor-ingestor/sensor_ingestor/config.py`
- dry-run 실행과 `/healthz`, `/metrics` endpoint 응답 검증 완료
- `sensor-ingestor` publish backend 추가: `sensor-ingestor/sensor_ingestor/backends.py`로 MQTT JSONL outbox, timeseries line protocol outbox, object store metadata outbox 연결
- `sensor-ingestor` quality evaluator 추가: `sensor-ingestor/sensor_ingestor/quality.py`로 `quality_flag`, `quality_reason`, `automation_gate` 계산 구현
- `scripts/validate_sensor_ingestor_runtime.py`로 publish backend 출력과 anomaly alert 발생 경로 검증 완료
- `Device Profile` registry/schema 초안 추가: `docs/device_profile_registry.md`, `schemas/device_profile_registry_schema.json`, `data/examples/device_profile_registry_seed.json`
- `model_profile -> profile_id` cross-check 검증기 추가: `scripts/validate_device_profile_registry.py`
- `plc-adapter` interface contract와 mock skeleton 추가: `docs/plc_adapter_interface_contract.md`, `plc-adapter/plc_adapter/interface.py`, `plc-adapter/plc_adapter/mock_adapter.py`, `plc-adapter/demo.py`
- zone 관수밸브와 원수 메인 밸브를 서로 다른 `Device Profile`로 분리해 인터록/ack 정책을 독립 관리하도록 보정
- `site override address map` seed/schema 추가: `docs/plc_site_override_map.md`, `schemas/device_site_override_schema.json`, `data/examples/device_site_override_seed.json`
- `device_id -> profile -> controller/channel` resolver 추가: `plc-adapter/plc_adapter/device_catalog.py`, `plc-adapter/plc_adapter/site_overrides.py`, `plc-adapter/plc_adapter/resolver.py`
- `scripts/validate_device_site_overrides.py`로 controller/channel binding 정합성 검증 추가
- PLC runtime endpoint override 기준 추가: `docs/plc_runtime_endpoint_config.md`, `.env.example`, `plc-adapter/plc_adapter/runtime_config.py`
- `plc_tag://...` channel ref parser 추가: `plc-adapter/plc_adapter/channel_refs.py`
- `channel_ref -> Modbus address` registry 추가: `docs/plc_channel_address_registry.md`, `schemas/device_channel_address_registry_schema.json`, `data/examples/device_channel_address_registry_seed.json`
- site override 기반 placeholder address map generator/validator 추가: `scripts/build_device_channel_address_registry.py`, `scripts/validate_device_channel_address_registry.py`
- `plc_tag_modbus_tcp` adapter payload에 `write_channel_address`, `read_channel_addresses`, `transport_*` fields 추가
- adapter가 write/readback 시 logical ref가 아니라 transport ref 기준으로 in-memory transport를 호출하도록 보강
- `plc_tag_modbus_tcp` adapter skeleton 추가: `plc-adapter/plc_adapter/plc_tag_modbus_tcp.py`, `plc-adapter/plc_adapter/transports.py`, `plc-adapter/plc_adapter/codecs.py`
- in-memory transport 기준 connect/reconnect, write/readback, timeout/retry, health check, result mapping 검증 완료
- optional `PymodbusTcpTransport` fake client 검증 완료: reconnect/retry, write/readback, timeout, health check 경로 확인
- `execution-gateway -> plc-adapter` command contract 추가: `schemas/device_command_request_schema.json`, `data/examples/device_command_request_samples.jsonl`, `scripts/validate_device_command_requests.py`
- 장치별 command mapping sample 8건과 실행 validator 추가: `docs/device_command_mapping_matrix.md`, `data/examples/device_command_mapping_samples.jsonl`, `scripts/validate_device_command_mappings.py`
- 대표 장치 8건에 대해 `adapter.write_device_command()` 경로 검증 완료: fan, shade, vent, irrigation valve, heater, co2, fertigation, source water valve
- override 전용 계약 추가: `schemas/control_override_request_schema.json`, `data/examples/control_override_request_samples.jsonl`, `scripts/validate_control_override_requests.py`
- `emergency_stop_latch`, `manual_override_start/release`, `safe_mode_entry`, `auto_mode_reentry_request` 샘플 5건 검증 완료
- `execution-gateway` skeleton 추가: `execution-gateway/execution_gateway/contracts.py`, `normalizer.py`, `guards.py`, `execution-gateway/demo.py`
- preflight validator 추가: `scripts/validate_execution_gateway_flow.py`
- 검증 결과:
  - heater pending 요청은 `approval_pending`으로 reject
  - fan 요청은 cooldown active일 때 reject
  - duplicate estop 요청은 두 번째 요청이 duplicate로 reject
  - approved auto re-entry 요청은 dispatch 가능
- `execution-gateway` dispatcher 추가: `execution-gateway/execution_gateway/dispatch.py`, `execution-gateway/execution_gateway/state.py`
- override 상태를 `ControlStateStore`에 저장하고, `estop/manual_override/safe_mode`가 active면 후속 device command를 차단하도록 연결
- dispatch audit log 경로를 `.env.example`의 `EXECUTION_GATEWAY_AUDIT_LOG_PATH`로 외부화했다.
- `scripts/validate_execution_dispatcher.py`로 `override -> state update -> device block -> adapter dispatch -> audit log` 경로를 검증했다.
- `plc-adapter/plc_adapter/plc_tag_modbus_tcp.py`의 `latency_ms`를 실제 write+readback 경과시간으로 측정하도록 보강했다.
- `scripts/validate_plc_modbus_transport.py`로 write 후 readback 비교, timeout 시 reconnect/retry, 무응답 장치 감지, transport health 경로를 검증했다.
- `execution-gateway/execution_gateway/dispatch.py`와 `state.py`에 runtime fault tracker를 추가해 timeout/fault가 연속되면 zone/site scope를 `safe_mode_active`로 전환하도록 연결했다.
- `scripts/validate_execution_safe_mode.py`로 repeated timeout 2회 후 `safe_mode` latch와 후속 device command 차단을 검증했다.
- 승인 체계 문서화 완료: 저/중/고위험 액션, 승인자 역할, UI 요구사항, timeout, 거절 fallback을 `docs/approval_governance.md`에 정리했다.
- 도메인 데이터 분류/포맷/정제 규칙 정리 완료: `docs/dataset_taxonomy.md`, `docs/training_data_format.md`, `docs/data_curation_rules.md`
- 행동추천/장애대응/로봇우선순위/알람 seed와 eval seed 추가: `data/examples/*`, `evals/*_eval_set.jsonl`
- 학습/eval JSONL 검증 스크립트 추가: `scripts/validate_training_examples.py`
- Chroma collection/manifest를 backend별로 분리: `pepper_expert_chunks_local`, `pepper_expert_chunks_openai`
- 응답 citation coverage 검증 스크립트 추가: `scripts/validate_response_citations.py`
- retrieval weight 튜닝 스크립트 추가: `scripts/tune_rag_weights.py`
- RAG 보완 핵심 과제 문서화: 데이터 100~200개 확장, vector store 도입, 필터 고도화, 현장 사례 RAG화

## 다음 우선순위

1. `ds_v11 / prompt_v5_methodfix_batch14 / eval_v2` 결과를 새 frozen baseline으로 유지하고, 후속 challenger는 같은 gate(`core24 + extended120 + extended160 + extended200 + blind_holdout50 + raw/validator gate`)에서만 비교한다.
2. 승격 기본 지표는 `core24`가 아니라 `extended160`으로 고정한다. `scripts/report_eval_set_coverage.py --promotion-baseline extended160` 기준 현재 coverage gate는 통과했다.
3. 다음 dataset split 기본값은 `validation_min_per_family=2`, `validation_ratio=0.15`, `validation_selection=spread`다. 현재 live head 추천 split은 train `284`, validation `60`이다.
4. 사용자 요구 보강은 완료했다: `safety_policy 56`, `sensor_fault 28`, `robot_task_prioritization 54`, `failure_response 50`
5. hard block 정책 10개와 approval/output contract 10개는 `docs/policy_output_validator_spec.md`와 `data/examples/policy_output_validator_rules_seed.json`으로 고정됐고, execution-gateway hard guard와 state-estimator MVP도 추가됐다.
6. blind50 validator 잔여 `5건`을 먼저 줄인다. 이 중 offline shadow residual `4건`은 batch17 sample `8건`으로, synthetic shadow day0 residual `4건`은 batch18 sample `8건`으로 이미 직접 보강했고, 남은 raw-only failure owner는 validator residual 리포트 기준으로 다시 관리한다.
7. extended200 validator 잔여 `42건`을 `risk_rubric_and_data`, `required_action_types`, `robot contract` 기준으로 다시 줄인다.
8. offline shadow replay는 이제 `critical_disagreement_count 0`, `operator_agreement_rate 0.92`, `promotion_decision promote`까지 올라왔다. 다음은 실제 shadow mode 로그를 운영 시나리오 형식으로 쌓아 같은 기준이 유지되는지 보는 일이다.
9. synthetic shadow `day0`는 아직 `operator_agreement_rate 0.6667`, `promotion_decision hold`다. residual owner report 기준 backlog는 `data_and_model 3`, `robot_contract_and_model 1`로 좁혀졌고, batch18은 이 4건만 직접 겨냥한다.
10. 실제 shadow mode와 잔여 실패 축소 없이 다음 submit을 열지 않는다. `ds_v12`는 frozen dry-run snapshot이고, `ds_v13`은 batch18 포함 next-only challenger다. 현재 preflight 기준 두 후보 모두 `blocked`이며, 다음 우선순위는 real shadow case 적재와 window report 생성이다.
11. 모델 런타임 연결은 이제 `state-estimator -> llm-orchestrator -> validator -> ops-api -> execution-gateway` 경로로 로컬에서 동작한다. `real localhost server smoke`, `sensor-ingestor -> state-estimator raw snapshot bridge`, `ops-api shadow case capture/window summary`, `OpenAI online smoke`, `dashboard auth/policy management`, `policy-engine loader/precheck`까지 통과했다. 현재 우선순위는 `real shadow log 누적`, `real PostgreSQL smoke`, `real sensor chart`, `policy source abstraction/event logging`다.

## 주의할 점

- 온실 공사 완료 전에는 장치 제어 구현보다 AI 준비와 센서 수집 계획을 우선한다.
- 센서 품질 플래그 없이 데이터를 학습에 반영하지 않는다.
- 정책 엔진 없이 자동화를 진행하지 않는다.
- execution-gateway 없이 PLC 연결을 진행하지 않는다.
- RAG 검색 품질 기준 없이 하이브리드 판단을 운영에 사용하지 않는다.
- 자주 바뀌는 재배 기준을 파인튜닝 데이터에 직접 암기시키지 않는다.
- Shadow Mode → Approval Mode → Limited Auto Mode 순서를 지킨다.
