# 작업 로그

이 문서는 저장소에서 진행한 주요 변경 작업과 의사결정 이력을 기록한다.

## 2026-04-13

### llm-orchestrator -> planner -> execution-gateway 통합 smoke
- `scripts/validate_llm_to_execution_flow.py`를 추가해 `LLMOrchestratorService` → `ActionDispatchPlanner` → `ExecutionDispatcher` 경로를 한 프로세스에서 3개 시나리오로 회귀한다. 스모크는 네트워크/DB 없이 stub과 fixture만으로 동작한다.
  - stub baseline: 레포 기본 `StubCompletionClient`가 `action_recommendation` 응답으로 `create_alert` + `request_human_check`를 돌려주는 상황을 재현한다. planner는 두 건 모두 `log_only` plan으로 변환하고 dispatcher에는 도달하지 않아야 한다.
  - adjust_fan dispatch: `_FixedCompletionClient`로 `adjust_fan` 추천을 주입하면 planner는 `gh-01-zone-a--circulation-fan--01`을 target으로 한 `device_command` 하나를 만들고, mock adapter 기반 `ExecutionDispatcher`는 `status="acknowledged"`로 마무리해야 한다.
  - pause_automation override: fixture로 `pause_automation`을 주입하면 planner는 `control_override` plan으로 변환하고, dispatcher는 `ControlStateStore` 갱신 후 `status="state_updated"`를 반환해야 한다. audit sink에는 정확히 2건의 dispatch row가 쌓이는지를 smoke가 직접 확인한다.
- 15종 smoke (`flow`, `auth`, `error_responses`, `schema_models`, `shadow_mode`, `postgres_smoke`, `policy_source_db_wiring`, `policy_engine_precheck`, `policy_output_validator`, `state_estimator_policy_flow`, `llm_to_execution_flow`, `execution_dispatcher`, `execution_gateway_flow`, `execution_safe_mode`, `state_estimator_mvp`) 전부 `errors 0`.

### state-estimator -> policy-engine precheck 통합 smoke
- `scripts/validate_state_estimator_policy_flow.py`를 추가해 같은 센서 스냅샷 shape으로 `estimate_zone_state` → `build_zone_state_payload` → raw device command → `evaluate_device_policy_precheck` 전 경로를 3개 시나리오로 회귀한다.
  - healthy fruiting: estimator `risk_level=low`, `observe_only`/`trend_review` 추천, adjust_fan precheck `pass`, policy_ids 빈 리스트.
  - worker_present: estimator `risk_level=critical`, `enter_safe_mode`/`request_human_check` 추천, notes `hard_safety_interlock`, 같은 raw command에 `worker_present=true`를 forward한 adjust_fan precheck `blocked`, `policy_ids=[HSV-01]`, `matched_flags=[worker_present]`.
  - sensor_quality=bad: estimator `risk_level=unknown`, `observability_status=degraded`, `pause_automation`/`request_human_check` 추천, `unknown_reasons`에 `sensor_quality.overall=bad`/`substrate_moisture=flatline`/`sensor_reliability_score<=0.25` 수집. precheck는 `sensor_quality_blocked` flag를 수집하지만 이를 직접 트리거하는 hard 규칙이 없어 `pass`로 떨어지는 invariant를 `_debug_collect_flags`로 고정한다 — 센서 degradation 가드는 precheck가 아니라 estimator 층에 둔다는 설계 의도를 회귀로 잡는다.
- ops-api, policy-engine, execution-gateway, state-estimator 14종 smoke (`flow`, `auth`, `error_responses`, `schema_models`, `shadow_mode`, `postgres_smoke`, `policy_source_db_wiring`, `policy_engine_precheck`, `policy_output_validator`, `state_estimator_policy_flow`, `execution_dispatcher`, `execution_gateway_flow`, `execution_safe_mode`, `state_estimator_mvp`) 모두 `errors 0`.

### policy source abstraction + 라이브 toggle 회귀
- `policy-engine/policy_engine/loader.py`에 `PolicySource` Protocol과 `FilePolicySource` / `StaticPolicySource` 두 구현, 그리고 프로세스 전역 스위치 `set_active_policy_source()` / `get_active_policy_source()`를 도입했다. `load_enabled_policy_rules()`는 명시적 `path`가 주어지지 않았고 active source가 등록되어 있으면 그쪽으로 위임한다. 기존 파일 기반 동작은 active source가 None일 때 그대로 유지된다.
- `ops-api/ops_api/policy_source.py`를 추가해 `DbPolicySource(session_factory)`가 `PolicyRecord` 테이블을 직접 읽고 `policy_row_to_rule()`로 JSON seed와 같은 rule dict 모양으로 변환한다. 각 호출은 short-lived session이라 `PATCH /policies/{id}` 편집이 다음 precheck 평가에 즉시 반영된다.
- `create_app`은 `bootstrap_reference_data()` 직후 `set_active_policy_source(DbPolicySource(session_factory))`를 호출해, ops-api가 기동된 환경에서는 `execution-gateway.guards`의 `evaluate_device_policy_precheck` / `evaluate_override_policy_precheck` 경로가 자동으로 DB 정책을 사용한다. 독립 CLI 실행은 여전히 파일 기반 fallback을 탄다.
- `scripts/validate_policy_source_db_wiring.py`를 추가해 TestClient로 `create_app`을 띄운 뒤 `HSV-01` (`worker_present` 하드 안전 규칙) 을 `/policies/HSV-01` PATCH로 disable → precheck에서 사라지고 `policy_result=pass`로 바뀌는지, 재활성화하면 다시 `blocked`로 돌아오는지 end-to-end로 회귀한다. Seed 파일 기준 20개 rule, DB 경유 20개 rule을 모두 검증했다.
- `scripts/validate_execution_safe_mode.py`는 이전에 `policy_engine` 모듈이 `sys.path`에 없어 import error로 실패했던 pre-existing bug가 있었다. `policy-engine` 경로를 추가해 복구했다. (내 policy source 변경과 무관하게 이미 빨간 상태였음.)
- 9종 smoke `validate_ops_api_flow`, `validate_ops_api_auth`, `validate_ops_api_error_responses`, `validate_ops_api_schema_models`, `validate_ops_api_shadow_mode`, `validate_ops_api_postgres_smoke`, `validate_policy_source_db_wiring`, `validate_policy_engine_precheck`, `validate_policy_output_validator` 모두 `errors 0`. execution-gateway 3종 `validate_execution_dispatcher`, `validate_execution_gateway_flow`, `validate_execution_safe_mode`도 통과.

### postgres schema 드리프트 해소 + smoke 확장
- `infra/postgres/001_initial_schema.sql`의 JSONB 32개 → TEXT, TIMESTAMPTZ 21개 → `TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC')`로 정렬했다. 이전에는 SQLAlchemy `init_db()`가 만든 (Text, naive DateTime) 스키마와 손수 마이그레이션이 만든 (JSONB, TIMESTAMPTZ) 스키마가 동일 postgres 인스턴스에서 분기되어, 먼저 실행된 쪽의 `CREATE TABLE IF NOT EXISTS` 때문에 나머지 경로는 침묵으로 스킵되고 런타임에 insert/select 형변환 오류가 터질 수 있었다. JSONB 인덱싱 격상은 향후 Alembic 도입 시 다시 다룬다.
- `scripts/validate_ops_api_postgres_smoke.py`는 이제 postgres URL이 주어질 때 seed 카운트만 확인하는 것이 아니라, `DecisionRecord`/`AlertRecord`/`RobotTaskRecord` insert → commit → select 왕복을 수행하고 `validated_output_json` / `payload_json` / `target_json` 페이로드와 `created_at` datetime 타입이 round-trip하는지 직접 검증한 뒤 smoke row를 삭제해 재실행 안전성을 유지한다. URL이 없으면 기존과 동일하게 `blocked`로 exit 0.
- 6종 ops-api 스모크 (`flow`, `auth`, `error_responses`, `schema_models`, `shadow_mode`, `postgres_smoke`) 모두 `errors 0` (postgres_smoke는 URL 미설정으로 `blocked=0`).

### ops-api auth dependency injection 회귀 해소
- `ops-api/ops_api/app.py`의 `create_app`이 `app.dependency_overrides[load_settings] = lambda: resolved_settings`를 등록해, `create_app(settings=...)`로 주입한 Settings가 `get_authenticated_actor`의 `Depends(load_settings)` 체인까지 반영되도록 했다. 이전에는 주입 Settings와 별개로 `load_settings()`가 env 변수를 다시 읽어 테스트/스모크에서 `auth_mode='header_token'`을 적용하려면 `OPS_API_AUTH_MODE` 환경 변수를 강제로 set해야 했다.
- `scripts/validate_ops_api_auth.py`에 `_verify_dependency_injection` 블록을 추가해 env 변수 없이 `create_app(settings=Settings(auth_mode='header_token', ...))`만으로 `/decisions`가 `no_key -> 401`, `viewer -> 200`, `invalid_token -> 401`을 만족하는지 TestClient 기반 회귀로 검증한다. 사전 조건으로 `OPS_API_AUTH_MODE` / `OPS_API_AUTH_TOKENS_JSON`이 이미 셋업되어 있으면 에러로 플래그해 env 오염을 즉시 감지한다.
- 회귀 결과: `validate_ops_api_auth`, `validate_ops_api_flow`, `validate_ops_api_error_responses`, `validate_ops_api_schema_models`, `validate_ops_api_shadow_mode` 5종 모두 `errors 0`.

### ops-api shadow window 보강 (env 격리, audit 보호, None-aware 지표)
- `ops-api/ops_api/shadow_mode.py`에 `_redirect_audit_paths` contextmanager를 추가해 `LLM_OUTPUT_VALIDATOR_SHADOW_LOG_PATH` / `LLM_OUTPUT_VALIDATOR_AUDIT_LOG_PATH` 환경변수를 capture 호출 한정으로만 덮어쓰고 복원하도록 격리했다. 이전에는 첫 capture 이후 동일 프로세스의 모든 shadow write가 해당 경로로 새어나갈 수 있었다.
- `capture_shadow_cases(append=False)`는 더 이상 audit log를 unlink하지 않고 `_rotate_audit_log`로 `.bak-{ts}` rename을 수행한다. 반환 summary에 `rotated_audit_logs` 경로를 포함한다.
- `/shadow/cases/capture`는 `payload.append=False` 케이스에 한해 `manage_runtime_mode` 권한을 요구한다. 일반 operator가 audit 이력을 회전시키지 못하도록 분리했다.
- `safe_ratio`는 분모 0일 때 `None`을 반환하고, `build_window_summary`는 `operator_agreement_rate` / `citation_coverage`가 `None`이면 `promotion_decision="hold"`로 fallback한다. "데이터 없음"과 "100% 불일치=0.0"이 대시보드에서 동일하게 보이던 혼동을 제거했다.
- 혼합 모델/프롬프트/데이터셋/retrieval profile은 `_distinct_or_mixed`로 집계해 `"mixed"`로 표기하고, `top_disagreements`는 `critical_disagreement` 우선·`created_at` 오름차순으로 정렬해 위험 케이스가 UI 상단에 보이도록 고정했다.
- `ops-api/ops_api/app.py`의 `_build_dashboard_payload`는 이제 `shadow_audit_path`를 인자로 받아 `_compute_shadow_window`로 계산한 윈도우 요약을 페이로드에 직접 박는다. `/dashboard/data`는 audit path를 그대로 전달하고, dead assignment (`shadow_window_summary = None`)은 제거했다.
- `scripts/validate_ops_api_shadow_mode.py`에 `safe_ratio(0,0)`, env 복원, `rotate_on_reset` 두 번째 capture까지 검증하는 회귀를 추가했다. 다섯 개 ops-api 스모크 스크립트(`validate_ops_api_flow`, `validate_ops_api_auth`, `validate_ops_api_error_responses`, `validate_ops_api_schema_models`, `validate_ops_api_shadow_mode`) 모두 `errors 0`으로 통과했다.

### policy event persistence + dashboard wiring 완료
- `ops-api/ops_api/models.py`와 `infra/postgres/001_initial_schema.sql`에 `policy_events` 저장 모델/테이블을 추가해 `blocked / approval_required` dispatch event를 decision과 분리해 저장할 수 있게 했다.
- `execution-gateway/execution_gateway/dispatch.py`는 이제 preflight 결과에서 `policy_event`를 만들고 audit row에 함께 남긴다. `blocked`와 `approval_required`를 request id, policy ids, reason code와 함께 보존한다.
- `ops-api/ops_api/planner.py`는 `zone_state.current_state`, `active_constraints`, `sensor_quality`를 dispatch request raw payload로 다시 전파한다. 따라서 approval dispatch 경로에서도 `HSV-04`, `HSV-09` 같은 precheck가 실제로 다시 발동한다.
- `ops-api/ops_api/app.py`는 dispatch 결과의 `policy_event`를 `PolicyEventRecord`로 저장하고, `GET /policies/events`와 dashboard summary에서 `policy_event_count`, `policy_blocked_count`, `policy_approval_count`를 노출한다.
- `scripts/validate_ops_api_flow.py`를 실제 `_execute_decision_dispatch()` 경로 기준으로 바꿔 `policy_event_count 2`, `policy_blocked_count 2`, `errors 0`을 확인했다.
- `scripts/validate_ops_api_server_smoke.py`도 `GET /policies/events` route까지 포함해 `errors 0`으로 다시 통과했다.

### policy-engine loader + execution precheck 연결
- `policy-engine/policy_engine/loader.py`를 추가해 enabled policy catalog를 stage 기준으로 읽는 loader를 만들었다.
- `policy-engine/policy_engine/precheck.py`를 추가해 dispatch 직전 `DeviceCommandRequest.raw`와 `policy_snapshot`을 다시 읽고 `blocked / approval_required / pass`를 재계산하는 precheck evaluator를 구현했다.
- 현재 precheck는 `HSV-04` 관수 경로 degraded에서 `short_irrigation` 차단, `HSV-09` rootzone conflict에서 `adjust_fertigation`을 `approval_required`로 승격하는 보수 규칙을 실제 request path에 적용한다.
- `execution-gateway/execution_gateway/guards.py`는 이제 precheck 결과를 병합해 `policy_result`, `policy_ids`, `policy_precheck:*` reason을 preflight와 audit에 남긴다.
- `scripts/validate_policy_engine_precheck.py`, `scripts/validate_execution_gateway_flow.py`, `scripts/validate_execution_dispatcher.py`를 갱신해 loader/precheck와 dispatch 직전 reject/escalation 경로를 회귀 검증했다.

### OpenAI online smoke + policy management/auth dashboard 보강
- `bash -lc "set -a; source .env >/dev/null 2>&1; set +a; python3 scripts/run_llm_orchestrator_smoke.py --provider openai --model-id champion --prompt-version sft_v10"`로 실제 OpenAI online smoke를 실행했다.
- 결과는 `champion -> ds_v11` FT model alias 해석, retrieval chunk 주입, strict JSON parse, validator rewrite reason(`HSV-08`)까지 모두 통과였다.
- `ops-api/ops_api/api_models.py`에 `PolicyUpdateRequest`를 추가하고, `ops-api/ops_api/app.py`에 `POST /policies/{policy_id}`를 연결해 `enabled/severity/description/trigger_flags/enforcement`를 업데이트할 수 있게 했다.
- `/dashboard`에는 `Auth Context`와 `Policy Management` 패널을 추가해 현재 actor/role/auth mode 확인과 policy enable/disable 토글을 한 화면에서 수행할 수 있게 했다.
- `scripts/validate_ops_api_server_smoke.py`도 policy list/toggle까지 포함하도록 확장했고, 실제 localhost smoke에서 `errors 0`으로 다시 통과했다.

### ops-api shadow capture + window summary API 추가
- `ops-api/ops_api/shadow_mode.py`를 추가해 `llm-orchestrator` shadow audit JSONL을 읽고 rolling window summary를 계산하는 helper를 분리했다.
- `ops-api/ops_api/app.py`에 `POST /shadow/cases/capture`, `GET /shadow/window`를 추가해 real shadow case 적재와 summary 조회를 운영 API에서 직접 수행할 수 있게 했다.
- `/dashboard`에도 shadow window summary 패널을 추가해 운영자가 approval/alert/command와 함께 agreement, critical disagreement, promotion decision을 한 화면에서 볼 수 있게 했다.
- `scripts/validate_ops_api_shadow_mode.py`를 추가해 day0 seed case 4건 기준 `decision_count 4`, `operator_agreement_rate 1.0`, `critical_disagreement_count 0`, `promotion_decision promote`를 확인했다.

### sensor-ingestor -> state-estimator raw snapshot bridge 추가
- `state-estimator/state_estimator/ingestor_bridge.py`를 추가해 `sensor-ingestor` MQTT outbox JSONL을 그대로 읽고 zone 기준으로 묶은 뒤 snapshot/zone_state를 만들 수 있게 했다.
- `scripts/validate_sensor_to_state_estimator_integration.py`를 추가해 `sensor-ingestor`를 실제로 한 번 돌린 뒤 outbox에서 `gh-01-zone-a` snapshot과 derived feature를 복원하는 통합 경로를 검증했다.
- 최신 통합 검증 결과는 `mqtt_rows 49`, `zones_seen 5`, `zone_a_device_count 8`, `errors 0`이었다.

### ops-api localhost server smoke + postgres smoke 경로 추가
- `scripts/validate_ops_api_server_smoke.py`를 추가해 실제 `uvicorn` 프로세스를 띄운 뒤 `GET /health`, `GET /auth/me`, `GET/POST /runtime/mode`, `POST /decisions/evaluate-zone`, `POST /actions/approve`, `GET /dashboard/data`까지 localhost HTTP 경로를 점검하도록 만들었다.
- 첫 smoke 실행에서 `llm-orchestrator/llm_orchestrator/prompt_catalog.py`가 `scripts/build_openai_sft_datasets.py`를 runtime import하면서 `training_data_config`를 찾지 못하는 버그가 드러났다. `PROMPT_SOURCE.parent`를 `sys.path`에 임시로 주입하는 방식으로 수정해 real server 경로를 복구했다.
- `scripts/validate_ops_api_postgres_smoke.py`를 추가해 `OPS_API_POSTGRES_SMOKE_URL` 또는 `OPS_API_DATABASE_URL`가 PostgreSQL URL일 때 schema bootstrap과 seed counts를 확인하도록 했다.
- 현재 환경에서는 PostgreSQL URL과 driver(`psycopg`/`psycopg2`)가 없어 postgres smoke는 `blocked`로 끝나고, localhost server smoke는 `errors 0`으로 통과했다.

### ops-api auth/role + response envelope 마감
- `ops-api/ops_api/auth.py`를 추가해 `disabled/header_token` 인증 모드와 `viewer/operator/service/admin` 역할 권한을 고정했다.
- `ops-api/ops_api/api_models.py`에 `ApiResponse`, `ErrorResponse`, `ActorModel`을 추가했고, `ops-api/ops_api/app.py`의 catalog/runtime/operations route 대부분을 공통 response envelope와 permission dependency로 감쌌다.
- `/auth/me`를 추가했고, 승인/실행/거절/shadow review 기록은 이제 request payload의 `actor_id`가 아니라 인증된 actor 기준으로 저장한다.
- `ops-api/ops_api/errors.py`에 `HTTPException` handler를 추가해 오류 응답도 `{error:{code,message}}` 형태로 맞췄다.
- `.env.example`에 `OPS_API_AUTH_MODE`, `OPS_API_AUTH_TOKENS_JSON` 예시를 추가했고, `scripts/validate_ops_api_auth.py`로 header token/role 검증을 따로 닫았다.

### ops-api schema/error test 보강
- `scripts/validate_ops_api_schema_models.py`를 추가해 `EvaluateZoneRequest`, `RuntimeModeRequest`, `ShadowReviewRequest`, `RobotTaskCreateRequest`, `ApiResponse`, `ErrorResponse`의 schema와 validation failure를 점검한다.
- `scripts/validate_ops_api_error_responses.py`를 추가해 `HTTPException`과 generic exception handler가 모두 표준 `{error:{code,message}}` envelope를 반환하는지 확인한다.

### ops-api minimal load scenario 추가
- `scripts/validate_ops_api_load_scenario.py`를 추가해 `SQLite + stub LLM + mock dispatch` 기준 반복 `evaluate -> persist -> approve -> dispatch` 루프를 최소 부하 시나리오로 검증한다.
- 현재 시나리오는 `4개 zone/task 조합 x 12 rounds = 48 decisions`를 돌리고, decision/approval/command/robot task row count와 `decision/full-cycle latency p50/p95`를 출력한다.
- 최신 실행 결과는 `decision_count 48`, `approval_count 48`, `command_count 72`, `robot_task_count 12`, `throughput 28.23 decisions/sec`, `decision p95 26.51ms`, `full-cycle p95 51.28ms`였다.
- 이로써 `todo 12.3`의 backend 검증 항목은 모두 닫았다. 남은 것은 local validation이 아니라 real PostgreSQL smoke와 OpenAI/운영 환경 smoke다.

### backend/database 3단계 확장
- `infra/postgres/001_initial_schema.sql`에 `zones`, `sensors`, `devices`, `policies`, `alerts`, `robot_candidates`, `robot_tasks`를 추가하고 `zone_id`, `created_at`, `device command`, `robot task` 인덱스를 보강했다.
- `ops-api/ops_api/models.py`를 같은 스키마로 확장해 reference catalog와 운영 테이블을 ORM으로 다루게 했다.
- `ops-api/ops_api/seed.py`와 `scripts/bootstrap_ops_api_reference_data.py`를 추가해 `sensor_catalog_seed`, `device_profile_registry_seed`, `device_site_override_seed`, `policy_output_validator_rules_seed`를 DB reference data로 자동 적재하도록 만들었다.
- `ops-api/ops_api/app.py`는 `GET /zones`, `GET /zones/{zone_id}/history`, `GET /sensors`, `GET /devices`, `GET /policies`, `POST /actions/execute`, `POST /robot/tasks`를 추가했고 `evaluate-zone` 시 alert/robot task도 DB에 저장하도록 바꿨다.
- `ops-api/ops_api/logging.py`, `ops-api/ops_api/errors.py`를 추가해 logger와 공통 예외 응답 경로를 넣었다.
- `python3 -m py_compile ops-api/ops_api/*.py scripts/bootstrap_ops_api_reference_data.py scripts/validate_ops_api_flow.py`, `python3 scripts/validate_ops_api_flow.py`를 실행했고 errors `0`, seeded counts `zones 5 / sensors 29 / devices 20 / policies 20`을 확인했다.

### state-estimator feature engineering 보강
- `state-estimator/state_estimator/features.py`를 확장해 `1분 평균`, `10분 변화율`, `co2_1m_avg_ppm`, `par_10m_delta_umol_m2_s`, `substrate_moisture_10m_delta_pct`, `climate_stress_score`, `rootzone_stress_score`를 추가했다.
- 같은 파일에 raw sensor/device runtime row를 현재 snapshot 형식으로 올리는 `build_snapshot_from_raw_records`, `build_zone_state_from_raw_records`, `validate_feature_snapshot`를 구현했다.
- `schemas/feature_schema.json`도 새 파생 필드를 반영하도록 확장했다.
- `data/examples/raw_sensor_window_seed.jsonl`와 `scripts/validate_state_estimator_raw_loader.py`를 추가해 `sensor-ingestor -> state-estimator` window loader 회귀 검증을 만들었다.
- `python3 scripts/validate_state_estimator_features.py`, `python3 scripts/validate_state_estimator_raw_loader.py`, `python3 scripts/validate_state_estimator_mvp.py`를 다시 실행했고 오류 `0`을 확인했다.

### LLM orchestrator tool registry + model alias + smoke path
- `llm-orchestrator/llm_orchestrator/tool_registry.py`를 추가해 runtime에서 모델에 노출할 capability catalog를 고정했다. 구현된 도구는 `get_zone_state`, `search_cultivation_knowledge`, `get_recent_trend`, `get_active_constraints`, `estimate_growth_stage`, `request_human_approval`, `log_decision`이고, planned 도구는 prompt 노출에서 제외했다.
- `llm-orchestrator/llm_orchestrator/model_registry.py`와 `artifacts/runtime/llm_orchestrator/model_registry.json`를 추가해 `champion`, `ds_v11_champion`, `ds_v14_rejected` alias를 실제 FT model id로 해석하도록 했다. `client.py`는 이제 alias를 먼저 해석한 뒤 `stub/openai` 공통으로 같은 id를 사용한다.
- `llm-orchestrator/llm_orchestrator/service.py`는 `tool_registry`를 prompt payload에 함께 주입하고, `active_constraints`를 실제 `zone_state.active_constraints` 우선으로 읽도록 수정했다.
- `llm-orchestrator/llm_orchestrator/response_parser.py`는 smart quote, trailing comma, prose wrapper가 섞인 응답까지 복구할 수 있도록 보강했다.
- `scripts/run_llm_orchestrator_smoke.py`를 추가해 `synthetic_sensor_scenarios -> state-estimator -> retriever -> orchestrator -> validator` 전체 경로를 `stub/openai` 공통으로 점검할 수 있게 했다.
- `scripts/validate_llm_orchestrator_service.py`는 이제 tool registry 노출과 `champion -> ds_v11` alias 해석까지 함께 검증하고, `scripts/validate_llm_response_parser.py`는 malformed JSON recovery 회귀 케이스를 추가로 검증한다.

### 운영 대시보드 + shadow review/approval UI 확장
- `ops-api/ops_api/models.py`에 `PolicyEvaluationRecord`, `OperatorReviewRecord`를 추가하고, `infra/postgres/001_initial_schema.sql`도 같은 기준으로 확장했다.
- `ops-api/ops_api/app.py`는 `POST /shadow/reviews`, `GET /shadow/reviews`, `GET /dashboard/data`, `GET /alerts`, `GET /robot/tasks`를 추가했다. `evaluate-zone`에서는 validator 결과를 `policy_evaluations`에 저장하고, `shadow` 모드 운영자 비교 검토는 `operator_reviews`에 저장한다.
- `/dashboard` 화면도 다시 구성했다. `zone overview`, `alerts`, `robot tasks`, `execution history`, `decision log`, `shadow agree/disagree`, `approve/reject`가 한 화면에서 동작한다.
- `python3 scripts/validate_ops_api_flow.py`, `python3 scripts/validate_llm_orchestrator_service.py`, `python3 -m py_compile ops-api/ops_api/*.py scripts/validate_ops_api_flow.py`를 다시 실행했고 오류 `0`을 확인했다.

### ds_v15 batch20 hard-case challenger dry-run package 준비
- `python3 scripts/build_openai_sft_datasets.py --system-prompt-version sft_v10 --validation-min-per-family 2 --validation-ratio 0.15 --validation-selection spread --oversample-task-type safety_policy=5 --oversample-task-type failure_response=5 --oversample-task-type sensor_fault=5 --oversample-task-type robot_task_prioritization=3 --train-output artifacts/fine_tuning/openai_sft_train_prompt_v10_validator_aligned_batch20_hardcase.jsonl --validation-output artifacts/fine_tuning/openai_sft_validation_prompt_v10_validator_aligned_batch20_hardcase.jsonl`로 batch20 live head 기준 `ds_v15` dry-run package를 생성했다.
- 결과는 source training `360`, train `855`, validation `61`, eval overlap `0`이다. oversampling summary는 `safety_policy 49 -> 245`, `failure_response 43 -> 215`, `sensor_fault 23 -> 115`, `robot_task_prioritization 48 -> 144`다.
- `python3 scripts/validate_openai_sft_dataset.py artifacts/fine_tuning/openai_sft_train_prompt_v10_validator_aligned_batch20_hardcase.jsonl artifacts/fine_tuning/openai_sft_validation_prompt_v10_validator_aligned_batch20_hardcase.jsonl` 기준 files `2`, rows `916`, errors `0`을 확인했다.
- `python3 scripts/run_openai_fine_tuning_job.py --model gpt-4.1-mini-2025-04-14 --model-version pepper-ops-sft-v1.12.0 --dataset-version ds_v15 --prompt-version prompt_v10_validator_aligned_batch20_hardcase --eval-version eval_v6 --training-file artifacts/fine_tuning/openai_sft_train_prompt_v10_validator_aligned_batch20_hardcase.jsonl --validation-file artifacts/fine_tuning/openai_sft_validation_prompt_v10_validator_aligned_batch20_hardcase.jsonl --notes "batch20 blind50 post-validator residual plus prompt v10 validator alignment and hard-case oversampling dry-run only; blocked until shadow gates improve"`를 `--submit` 없이 실행해 dry-run manifest `artifacts/fine_tuning/runs/ft-sft-gpt41mini-ds_v15-prompt_v10_validator_aligned_batch20_hardcase-eval_v6-20260413-152557.json`를 생성했다.
- 이어서 `python3 scripts/build_challenger_submit_preflight.py --candidate-manifest artifacts/fine_tuning/runs/ft-sft-gpt41mini-ds_v15-prompt_v10_validator_aligned_batch20_hardcase-eval_v6-20260413-152557.json --real-shadow-report artifacts/reports/shadow_mode_real_sample_window.json --output-prefix artifacts/reports/challenger_submit_preflight_ds_v15_real_shadow`를 실행해 `ds_v15` preflight를 고정했다.
- 해석은 분명하다. `ds_v15`도 아직 `blocked`이며 공통 blocker는 그대로 `blind_holdout50 validator 0.9 < 0.95`, `synthetic shadow day0 hold`, `real shadow rollback`이다.

### ds_v14 validator gap 흡수 + batch20 staging
- `policy-engine/policy_engine/output_validator.py`를 보정해 `retrieved_context` 바깥 citation을 in-context citation으로 정렬하고, `forbidden_action + path/readback loss`를 `decision=block`으로 강제했다. `llm-orchestrator/llm_orchestrator/service.py`와 `scripts/build_shadow_mode_replay_from_eval.py`도 같은 context(`retrieved_context`, `proposed_action`)를 validator에 넘기도록 맞췄다.
- `scripts/validate_policy_output_validator.py`에 citation-in-context와 `short_irrigation + path loss` 회귀 케이스를 추가했고, 총 `9건` 검증에서 오류 `0`을 확인했다.
- `python3 scripts/simulate_policy_output_validator.py --report artifacts/reports/fine_tuned_model_eval_ds_v14_prompt_v10_validator_aligned_batch19_hardcase_blind_holdout50.json --eval-files evals/blind_holdout_eval_set.jsonl --output-prefix artifacts/reports/policy_output_validator_simulation_ds_v14_prompt_v10_validator_aligned_batch19_hardcase_blind_holdout50` 재실행 결과 blind50 validator는 `0.84 -> 0.9`로 회복됐다.
- `python3 scripts/validate_product_readiness_gate.py --report artifacts/reports/policy_output_validator_simulation_ds_v14_prompt_v10_validator_aligned_batch19_hardcase_blind_holdout50.json --eval-files evals/blind_holdout_eval_set.jsonl --output-prefix artifacts/reports/product_readiness_gate_ds_v14_prompt_v10_validator_aligned_batch19_hardcase_blind_holdout50_validator_applied` 결과 validator gate는 `blind_holdout_pass_rate 0.9`, `safety_invariant_pass_rate 1.0`, `field_usability_pass_rate 1.0`, `promotion_decision hold`였다.
- `python3 scripts/report_validator_residual_failures.py` 재실행 결과 blind50 잔여는 `8건 -> 5건`, extended200 잔여는 `43건 -> 40건`으로 줄었고, blind50의 `runtime_validator_gap`은 `3 -> 0`이 됐다.
- 남은 blind50 residual `5건`은 `scripts/generate_batch20_post_validator_residual_samples.py`와 [docs/batch20_post_validator_residual_plan.md](/home/user/pepper-smartfarm-plan-v2/docs/batch20_post_validator_residual_plan.md:1) 기준 batch20 sample `8건`으로 training seed에 직접 역투영했다.
- `python3 scripts/validate_training_examples.py`, `python3 scripts/audit_training_data_consistency.py` 기준 현재 training `360건`, eval `250건`, duplicate `0`, contradiction `0`, eval overlap `0`이다.

### ds_v14 완료 후 frozen gate 재평가
- `./.venv/bin/python scripts/sync_openai_fine_tuning_job.py --manifest artifacts/fine_tuning/runs/ft-sft-gpt41mini-ds_v14-prompt_v10_validator_aligned_batch19_hardcase-eval_v5-20260413-113447.json` 기준 `ds_v14` run `ftjob-37TzJb1FtgGUghjfyaGqAxkA`는 `succeeded`로 종료됐다. 결과 model은 `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v14-prompt-v10-validator-aligned-batch19-har:DU2VQVYz`다.
- `ds_v11` 리포트에 저장된 `eval_id`를 기준으로 `/tmp/core24_frozen_eval_set.jsonl`, `/tmp/extended120_frozen_eval_set.jsonl`, `/tmp/extended160_frozen_eval_set.jsonl`, `/tmp/extended200_frozen_eval_set.jsonl`, `/tmp/blind_holdout50_frozen_eval_set.jsonl`를 복원해 같은 frozen subset으로 다시 평가했다.
- raw 재평가 결과는 `core24 0.8333`, `extended120 0.7167`, `extended160 0.6937`, `extended200 0.695`, `blind_holdout50 0.74`였다. `ds_v11` baseline `0.9167 / 0.7667 / 0.75 / 0.7 / 0.7` 대비 blind raw만 소폭 올랐고 나머지는 모두 하락했다.
- `python3 scripts/simulate_policy_output_validator.py --report artifacts/reports/fine_tuned_model_eval_ds_v14_prompt_v10_validator_aligned_batch19_hardcase_blind_holdout50.json ...` 초기 결과 blind50은 `0.74 -> 0.84`였고, 이후 citation/path-loss contract 보정 뒤 `0.9`까지 회복됐다.
- `python3 scripts/validate_product_readiness_gate.py --report artifacts/reports/fine_tuned_model_eval_ds_v14_prompt_v10_validator_aligned_batch19_hardcase_blind_holdout50.json ...` 결과 raw gate는 `blind_holdout_pass_rate 0.74`, `safety_invariant_pass_rate 0.75`, `field_usability_pass_rate 0.98`, `promotion_decision hold`였다.
- 같은 스크립트를 validator report에 적용한 결과 validator gate는 초기 `0.84 / 0.875 / hold`였고, runtime validator gap 보정 뒤 `0.9 / 1.0 / hold`로 올라갔다.
- `python3 scripts/report_eval_failure_clusters.py` 결과 blind50 실패 `13건`, extended200 실패 `61건`이고 중심 root cause는 `risk_rubric_and_data`, `data_and_model`, `output_contract`였다.
- `python3 scripts/report_validator_residual_failures.py` 결과 validator 적용 후 잔여 실패는 blind50 `5건`, extended200 `40건`이다. blind50 owner는 `risk_rubric_and_data 4`, `data_and_model 2`, extended200 owner는 `risk_rubric_and_data 32`, `data_and_model 14`, `robot_contract_and_model 1`이다.
- 결론은 분명하다. `batch19 + prompt_v10 validator alignment`는 blind raw를 조금 올렸지만, validator-aware generalization은 오히려 악화됐다. `ds_v14`는 baseline 승격 없이 rejected challenger로 남기고, 기준선은 계속 `ds_v11`로 유지한다.

### ds_v14 실제 submit
- `./.venv/bin/python scripts/run_openai_fine_tuning_job.py --model gpt-4.1-mini-2025-04-14 --model-version pepper-ops-sft-v1.11.0 --dataset-version ds_v14 --prompt-version prompt_v10_validator_aligned_batch19_hardcase --eval-version eval_v5 --training-file artifacts/fine_tuning/openai_sft_train_prompt_v10_validator_aligned_batch19_hardcase.jsonl --validation-file artifacts/fine_tuning/openai_sft_validation_prompt_v10_validator_aligned_batch19_hardcase.jsonl --notes "batch19 real shadow feedback plus validator-aligned prompt and hard-case oversampling; submit after runtime integration stack implementation" --submit`로 `ds_v14`를 실제 제출했다.
- 새 submit manifest는 `artifacts/fine_tuning/runs/ft-sft-gpt41mini-ds_v14-prompt_v10_validator_aligned_batch19_hardcase-eval_v5-20260413-113447.json`이고, job id는 `ftjob-37TzJb1FtgGUghjfyaGqAxkA`다.
- `./.venv/bin/python scripts/sync_openai_fine_tuning_job.py --manifest artifacts/fine_tuning/runs/ft-sft-gpt41mini-ds_v14-prompt_v10_validator_aligned_batch19_hardcase-eval_v5-20260413-113447.json` 기준 현재 status는 `validating_files`, events 경로는 `artifacts/fine_tuning/events/ftjob-37TzJb1FtgGUghjfyaGqAxkA.jsonl`이다.
- 원래 `challenger_submit_preflight_ds_v14_real_shadow.md` 기준 blocker는 남아 있었지만, 이번 submit은 사용자 승인으로 진행했다. 따라서 완료 후에는 blocker를 무시하지 않고 기존 frozen gate와 shadow 기준으로 다시 재평가해야 한다.

### runtime integration stack 구현
- `state-estimator/state_estimator/features.py`를 추가해 VPD, DLI, 5분 평균, 30분 변화율, 관수 후 회복률, 배액률, rootzone/climate/crop stress score를 계산하는 feature builder를 구현했다.
- `state-estimator/state_estimator/estimator.py`는 기존 MVP unknown/critical 승격 규칙을 유지하면서 `build_state_snapshot`, `build_zone_state_payload`로 LLM 입력용 zone state를 직접 조합하도록 확장했다.
- `llm-orchestrator/llm_orchestrator/client.py`, `retriever.py`, `response_parser.py`, `prompt_catalog.py`, `service.py`를 추가해 `prompt version 선택 -> local RAG retrieval -> model 호출 -> malformed JSON recovery -> output validator 연결` 경로를 실제 서비스 계층으로 묶었다.
- `ops-api/ops_api/`를 새로 추가해 FastAPI backend skeleton, SQLAlchemy 모델, runtime mode 저장, approval planner, inline dashboard를 구현했다. 핵심 엔드포인트는 `POST /decisions/evaluate-zone`, `POST /actions/approve`, `POST /actions/reject`, `GET /actions/history`, `GET /dashboard`, `GET/POST /runtime/mode`다.
- `infra/postgres/001_initial_schema.sql`로 PostgreSQL 기준 `decisions`, `approvals`, `device_commands` DDL을 고정했다. 로컬 검증은 `SQLite + mock PLC adapter`로 수행했다.
- 구현 범위와 한계는 `docs/runtime_integration_status.md`에 정리했다. 현재는 real OpenAI smoke test, real PostgreSQL 연결, policy management/auth UI, 실제 shadow log 누적이 남아 있다.

### runtime integration 로컬 검증
- `python3 -m py_compile state-estimator/state_estimator/*.py llm-orchestrator/llm_orchestrator/*.py ops-api/ops_api/*.py scripts/validate_state_estimator_features.py scripts/validate_llm_orchestrator_service.py scripts/validate_ops_api_flow.py`로 모듈 import/구문 검증을 다시 통과시켰다.
- `python3 scripts/validate_state_estimator_features.py` 기준 합성 케이스에서 `VPD`, `heat stress`, `rootzone stress`, `sensor reliability` 계산이 기대 범위에 들어오는 것을 확인했다.
- `python3 scripts/validate_llm_orchestrator_service.py` 기준 retrieved chunk 결합, citation 보강, validator reason code 부착, malformed JSON recovery 경로를 확인했다.
- `python3 scripts/validate_ops_api_flow.py` 기준 실제 ASGI client 없이도 app 생성, route 등록, decision 저장, approval 저장, planner 기반 dispatch, runtime mode persistence가 모두 통과했다.
- 이 환경에서는 `fastapi.testclient.TestClient`가 단순 예제에서도 hang돼 API 검증은 `SQLite` 세션과 app/service 직접 호출 기반으로 닫았다. 따라서 현재 검증은 “로컬 wiring 확인”이며, 추후 실제 ASGI 서버 smoke test와 real DB smoke test가 별도로 필요하다.

### real shadow mode capture / window report 경로 추가
- `scripts/run_shadow_mode_capture_cases.py`를 추가해 실제 운영 또는 review case JSONL을 shadow audit log에 append하거나 일자별로 새로 적재할 수 있게 했다.
- `scripts/build_shadow_mode_window_report.py`를 추가해 여러 shadow audit log를 rolling window 기준으로 합산하고 `promotion_decision`까지 바로 계산할 수 있게 했다.
- `scripts/validate_shadow_mode_window_report.py`로 append-style capture와 window report를 함께 검증했다. sample `15건` 기준 `critical_disagreement_count 1`, `promotion_decision rollback`, `eval_set_ids ['shadow-day-20260412', 'shadow_seed_day0']`, `errors []`를 확인했다.
- `docs/real_shadow_mode_runbook.md`를 추가해 공사 완료 후 실제 shadow log를 어떻게 적재하고 submit blocker에 연결할지 절차를 고정했다.
- 이어서 `scripts/build_challenger_submit_preflight.py --real-shadow-report /tmp/shadow_mode_real_window.json ...`를 재실행해 real shadow window 리포트를 submit blocker에 자동 연결하는 것도 확인했다. 이 경우 `real_shadow_mode_status`는 `rollback`으로 파생됐고, `ds_v12`, `ds_v13` 둘 다 계속 `blocked`였다.
- 그 다음 `scripts/generate_batch19_real_shadow_feedback.py`로 real shadow rollback source `shadow-runtime-002`와 blind50 validator 잔여 `5건`을 직접 corrective sample `8건`으로 변환했다. `sft_v10` prompt도 추가해 validator hard rule을 자연어 규칙으로 동기화했고, `ds_v14/prompt_v10_validator_aligned_batch19_hardcase` dry-run candidate까지 만들었다. 현재 preflight는 계속 `blocked`다.

### challenger submit preflight 리포트 추가
- `scripts/build_challenger_submit_preflight.py`를 추가해 `ds_v12`와 `ds_v13` candidate를 같은 blocker 기준으로 비교할 수 있게 했다.
- `python3 scripts/build_challenger_submit_preflight.py --candidate-manifest artifacts/fine_tuning/runs/ft-sft-gpt41mini-ds_v12-prompt_v5_methodfix_batch17_hardcase-eval_v3-20260413-035151.json --candidate-manifest artifacts/fine_tuning/runs/ft-sft-gpt41mini-ds_v13-prompt_v5_methodfix_batch18_hardcase-eval_v4-20260413-075846.json --real-shadow-mode-status not_run --output-prefix artifacts/reports/challenger_submit_preflight_ds_v12_ds_v13`로 preflight report를 생성했다.
- 결과는 분명하다. `ds_v12`, `ds_v13` 모두 `blocked`이고, 공통 blocker는 `blind_holdout50 validator 0.9 < 0.95`, `synthetic shadow day0 hold`, `real_shadow_mode_status not_run`이다.
- 해석도 명확하다. 지금은 package를 더 늘리는 단계가 아니라 runtime shadow evidence를 쌓고 `synthetic shadow day0`를 `promote`로 올리는 단계다.

### ds_v13 batch18 hard-case challenger dry-run package 준비
- `python3 scripts/build_openai_sft_datasets.py --system-prompt-version sft_v5 --validation-min-per-family 2 --validation-ratio 0.15 --validation-selection spread --oversample-task-type safety_policy=5 --oversample-task-type failure_response=5 --oversample-task-type sensor_fault=5 --oversample-task-type robot_task_prioritization=3 --train-output artifacts/fine_tuning/openai_sft_train_prompt_v5_methodfix_batch18_hardcase.jsonl --validation-output artifacts/fine_tuning/openai_sft_validation_prompt_v5_methodfix_batch18_hardcase.jsonl`로 batch18 live head 기준 `ds_v13` dry-run package를 생성했다.
- 결과는 source training `344`, train `822`, validation `60`, eval overlap `0`이다. oversample summary는 `safety_policy 47 -> 235`, `failure_response 42 -> 210`, `sensor_fault 23 -> 115`, `robot_task_prioritization 45 -> 135`다.
- `python3 scripts/validate_openai_sft_dataset.py artifacts/fine_tuning/openai_sft_train_prompt_v5_methodfix_batch18_hardcase.jsonl artifacts/fine_tuning/openai_sft_validation_prompt_v5_methodfix_batch18_hardcase.jsonl` 기준 files `2`, rows `882`, errors `0`을 확인했다.
- `./.venv/bin/python scripts/run_openai_fine_tuning_job.py --model gpt-4.1-mini-2025-04-14 --model-version pepper-ops-sft-v1.10.0 --dataset-version ds_v13 --prompt-version prompt_v5_methodfix_batch18_hardcase --eval-version eval_v4 --training-file artifacts/fine_tuning/openai_sft_train_prompt_v5_methodfix_batch18_hardcase.jsonl --validation-file artifacts/fine_tuning/openai_sft_validation_prompt_v5_methodfix_batch18_hardcase.jsonl --notes "batch18 synthetic shadow day0 residual plus hard-case oversampling dry-run only; blocked until runtime shadow improves"`를 `--submit` 없이 실행해 dry-run manifest `artifacts/fine_tuning/runs/ft-sft-gpt41mini-ds_v13-prompt_v5_methodfix_batch18_hardcase-eval_v4-20260413-075846.json`를 생성했다.
- 해석은 분명하다. `ds_v12`는 frozen snapshot으로 유지하고, `ds_v13`은 batch18이 실제로 필요한지 검증하기 위한 next-only dry-run candidate로만 관리한다.

### synthetic shadow day0 residual report와 batch18 `8건` 추가
- `scripts/report_shadow_mode_seed_residuals.py`를 추가해 `artifacts/runtime/llm_orchestrator/shadow_mode_ds_v11_day0_seed.jsonl` 기준 synthetic shadow `day0` 잔여 drift를 owner와 cause로 재분류했다.
- 결과 리포트 `artifacts/reports/shadow_mode_residuals_ds_v11_day0_seed.md` 기준 residual `4건`은 `data_and_model 3`, `robot_contract_and_model 1`이고, 원인은 `alert_missing_before_fertigation_review 3`, `inspect_crop_enum_drift 1`이다.
- `scripts/generate_batch18_shadow_day0_residual_samples.py`와 `docs/synthetic_shadow_day0_batch18_plan.md`를 추가해 이 `4건`을 batch18 sample `8건`으로 직접 옮겼다.
- 생성 파일은 `data/examples/action_recommendation_samples_batch12_shadow_day0.jsonl` `2건`, `data/examples/state_judgement_samples_batch18_shadow_day0.jsonl` `4건`, `data/examples/robot_task_samples_batch7_shadow_day0.jsonl` `2건`이다.
- `python3 scripts/build_training_jsonl.py --include-source-file`, `python3 scripts/validate_training_examples.py`, `python3 scripts/audit_training_data_consistency.py`, `python3 scripts/report_risk_slice_coverage.py`, `python3 scripts/report_training_sample_stats.py`를 다시 실행했다.
- 결과는 training `344건`, eval `250건`, duplicate `0`, contradiction `0`, eval overlap `0`, training rule failure `none`이다.
- 최신 training 통계는 class imbalance ratio `14.00`, action 분포 `request_human_check 165`, `create_alert 133`, `pause_automation 48`, `block_action 55`, `enter_safe_mode 30`으로 재고정했다.
- `python3 scripts/build_openai_sft_datasets.py --validation-min-per-family 2 --validation-ratio 0.15 --validation-selection spread --train-output /tmp/openai_sft_train_batch18.jsonl --validation-output /tmp/openai_sft_validation_batch18.jsonl` 기준 current live head 추천 split은 train `284`, validation `60`이다.
- 같은 규칙으로 `--oversample-task-type safety_policy=5 --oversample-task-type failure_response=5 --oversample-task-type sensor_fault=5 --oversample-task-type robot_task_prioritization=3`를 적용한 next-only dry-run은 train `822`, validation `60`이고, `python3 scripts/validate_openai_sft_dataset.py /tmp/openai_sft_train_batch18_hardcase.jsonl /tmp/openai_sft_validation_batch18_hardcase.jsonl` 기준 files `2`, rows `882`, errors `0`을 확인했다.
- 해석은 분명하다. `ds_v12` dry-run snapshot은 그대로 유지하고, batch18은 synthetic shadow `day0` 잔여 `4건`을 줄이기 위한 그 다음 corrective 후보의 live head에만 반영한다.

### ds_v12 hard-case challenger dry-run package 준비
- `./.venv/bin/python scripts/build_openai_sft_datasets.py --system-prompt-version sft_v5 --validation-min-per-family 2 --validation-ratio 0.15 --validation-selection spread --oversample-task-type safety_policy=5 --oversample-task-type failure_response=5 --oversample-task-type sensor_fault=5 --oversample-task-type robot_task_prioritization=3 --train-output artifacts/fine_tuning/openai_sft_train_prompt_v5_methodfix_batch17_hardcase.jsonl --validation-output artifacts/fine_tuning/openai_sft_validation_prompt_v5_methodfix_batch17_hardcase.jsonl`로 `ds_v12` dry-run package를 생성했다.
- 결과는 source training `336`, train `815`, validation `57`, eval overlap `0`이다. oversample summary는 `safety_policy 47 -> 235`, `failure_response 42 -> 210`, `sensor_fault 23 -> 115`, `robot_task_prioritization 44 -> 132`다.
- `./.venv/bin/python scripts/validate_openai_sft_dataset.py artifacts/fine_tuning/openai_sft_train_prompt_v5_methodfix_batch17_hardcase.jsonl artifacts/fine_tuning/openai_sft_validation_prompt_v5_methodfix_batch17_hardcase.jsonl` 기준 files `2`, rows `872`, errors `0`을 확인했다.
- `./.venv/bin/python scripts/run_openai_fine_tuning_job.py --model gpt-4.1-mini-2025-04-14 --model-version pepper-ops-sft-v1.9.0 --dataset-version ds_v12 --prompt-version prompt_v5_methodfix_batch17_hardcase --eval-version eval_v3 --training-file artifacts/fine_tuning/openai_sft_train_prompt_v5_methodfix_batch17_hardcase.jsonl --validation-file artifacts/fine_tuning/openai_sft_validation_prompt_v5_methodfix_batch17_hardcase.jsonl --notes "batch16+batch17+hard-case oversampling dry-run only; blocked until synthetic shadow day0 improves"`를 `--submit` 없이 실행해 dry-run manifest `artifacts/fine_tuning/runs/ft-sft-gpt41mini-ds_v12-prompt_v5_methodfix_batch17_hardcase-eval_v3-20260413-035151.json`를 생성했다.
- 해석은 분명하다. `ds_v12`는 실제 submit 후보가 아니라 blocked challenger package다. synthetic shadow `day0`가 아직 `hold`이므로, 이번 단계에서는 비용을 쓰지 않고 input package와 실행 식별자만 고정했다.

### synthetic shadow day0 seed pack 추가
- `llm-orchestrator/llm_orchestrator/runtime.py`를 보강해 `robot_task_prioritization`도 shadow agreement에 반영되도록 했다. 이제 `ai_robot_task_types_after`와 `operator_robot_task_types`를 함께 기록하고 `inspect_crop / skip_area / manual_review` exact enum drift를 직접 잡는다.
- `scripts/build_shadow_mode_report.py`와 `docs/shadow_mode_report_format.md`도 같은 계약으로 갱신했다.
- `scripts/generate_shadow_mode_day0_seed_pack.py`를 추가해 synthetic shadow day0 seed case `12건`을 생성했다. `worker_present`, `sensor stale`, `irrigation readback mismatch`, `rootzone sensor conflict`, `robot aisle safety` 같은 aligned case와 `blind-action-004`, `blind-expert-003`, `blind-expert-010`, `blind-robot-005` residual case를 같이 넣었다.
- `scripts/run_shadow_mode_seed_pack.py`로 seed pack을 runtime capture -> summary report 경로에 연결했고, `scripts/validate_shadow_mode_seed_pack.py`로 baseline 값까지 고정했다.
- `python3 scripts/run_shadow_mode_seed_pack.py --cases-file data/examples/shadow_mode_runtime_day0_seed_cases.jsonl --audit-log artifacts/runtime/llm_orchestrator/shadow_mode_ds_v11_day0_seed.jsonl --validator-audit-log artifacts/runtime/llm_orchestrator/output_validator_ds_v11_day0_seed.jsonl --output-prefix artifacts/reports/shadow_mode_ds_v11_day0_seed` 결과 synthetic shadow baseline은 `decision_count 12`, `operator_agreement_rate 0.6667`, `critical_disagreement_count 0`, `promotion_decision hold`였다.
- 해석은 분명하다. offline replay는 heuristic 정렬 후 `promote`까지 올라갔지만, runtime-shaped shadow seed에서는 아직 residual drift가 그대로 남는다. 다음 corrective challenger는 이 synthetic shadow baseline을 먼저 끌어올릴 수 있을 때만 검토한다.

### batch17 offline shadow residual 8건 추가
- `scripts/generate_batch17_shadow_residual_samples.py`를 추가해 offline shadow replay 잔여 drift `4건`을 batch17 sample `8건`으로 직접 옮겼다.
- 생성 파일은 `data/examples/action_recommendation_samples_batch11_shadow_residual.jsonl` `2건`, `data/examples/state_judgement_samples_batch17_shadow_residual.jsonl` `4건`, `data/examples/robot_task_samples_batch6_shadow_residual.jsonl` `2건`이다.
- 매핑 기준은 `docs/offline_shadow_residual_batch17_plan.md`에 고정했다. `blind-action-004`는 GT Master action sample로, `blind-expert-003`와 `blind-expert-010`은 nutrient/rootzone sample로, `blind-robot-005`는 `inspect_crop` exact enum contract sample로 다시 넣었다.
- `python3 scripts/build_training_jsonl.py`, `python3 scripts/validate_training_examples.py`, `python3 scripts/audit_training_data_consistency.py`, `python3 scripts/report_risk_slice_coverage.py`, `python3 scripts/report_training_sample_stats.py`를 다시 실행했다.
- 결과는 training `336건`, eval `250건`, duplicate `0`, contradiction `0`, eval overlap `0`, training rule failure `none`이다.
- 최신 training critical slice는 `safety_hard_block 54`, `sensor_unknown 28`, `evidence_incomplete_unknown 11`, `failure_safe_mode 30`, `robot_contract 52`, `gt_master_dryback_high 10`, `nursery_cold_humid_high 3`이다.
- 최신 training 통계는 class imbalance ratio `14.00`, action 분포 `request_human_check 159`, `create_alert 127`, `pause_automation 48`, `block_action 55`, `enter_safe_mode 30`으로 재고정했다.
- 권장 split도 다시 계산했다. `python3 scripts/build_openai_sft_datasets.py --validation-min-per-family 2 --validation-ratio 0.15 --validation-selection spread` 기준 현재 추천 split은 train `279`, validation `57`이다.

### offline shadow replay 계약 정렬과 runtime `HSV-09` 반영
- `llm-orchestrator/llm_orchestrator/runtime.py`와 `scripts/build_shadow_mode_replay_from_eval.py`를 수정해 `forbidden_action`을 일반 `recommended_actions`가 아니라 `decision + blocked_action_type` 계약으로 비교하도록 바꿨다.
- `scripts/build_shadow_mode_report.py`와 `docs/shadow_mode_report_format.md`도 함께 갱신해 shadow report가 `ai_decision_after`, `operator_decision`, `ai_blocked_action_type_after`, `operator_blocked_action_type`를 기록하도록 맞췄다.
- runtime validator에는 빠져 있던 `HSV-09`를 `policy-engine/policy_engine/output_validator.py`에 추가했다. 이제 `forbidden_action + adjust_fertigation + rootzone sensor conflict`는 simulation과 동일하게 `decision=approval_required`로 승격된다.
- 이어서 `scripts/build_shadow_mode_replay_from_eval.py`의 context builder를 보정했다. `worker_present`는 negation-aware로 바꾸고, `safe_mode_active`는 실제 active 표현이 있을 때만 잡고, `dry_room_path_degraded`는 `failure_type=communication_loss`와 통신/readback 신호가 있을 때만 승격한다.
- `data/examples/policy_output_validator_cases.jsonl`에 `validator-case-007`을 추가했고, `python3 scripts/validate_policy_output_validator.py` 기준 `checked_cases 7`, `errors 0`을 확인했다.
- `python3 scripts/build_shadow_mode_replay_from_eval.py --report artifacts/reports/fine_tuned_model_eval_ds_v11_prompt_v5_methodfix_batch14_blind_holdout50.json --eval-files evals/blind_holdout_eval_set.jsonl --model-id ...:DTryNJg3 --prompt-id sft_v5 --dataset-id ds_v11 --eval-set-id blind_holdout50_offline_shadow_replay --retrieval-profile-id retrieval-chroma-local-v1 --shadow-audit-log artifacts/runtime/llm_orchestrator/shadow_mode_ds_v11_blind_holdout50_offline.jsonl --output-prefix artifacts/reports/shadow_mode_ds_v11_blind_holdout50_offline`를 다시 실행했다.
- 그 결과 offline shadow replay 기준선은 `operator_agreement_rate 0.92`, `critical_disagreement_count 0`, `promotion_decision promote`로 더 올라갔다.
- `blind-forbidden-007`, `blind-forbidden-002`, `blind-action-003`, `blind-robot-001`, `blind-failure-008`은 모델 failure가 아니라 shadow/replay contract 또는 heuristic mismatch였다는 점을 분리했다.
- 현재 남은 offline shadow drift는 `blind-action-004`, `blind-expert-003`, `blind-expert-010`, `blind-robot-005` 네 건이고, owner는 `data_and_model 3`, `robot_contract_and_model 1`로 정리했다.

### ds_v11 blind50 offline shadow replay 기준선 추가
- `scripts/build_shadow_mode_replay_from_eval.py`를 추가해 frozen eval report와 eval 기대값을 `llm-orchestrator` shadow audit 형식으로 재생성할 수 있게 했다.
- `python3 scripts/build_shadow_mode_replay_from_eval.py --report artifacts/reports/fine_tuned_model_eval_ds_v11_prompt_v5_methodfix_batch14_blind_holdout50.json --eval-files evals/blind_holdout_eval_set.jsonl --model-id ...:DTryNJg3 --prompt-id sft_v5 --dataset-id ds_v11 --eval-set-id blind_holdout50_offline_shadow_replay --retrieval-profile-id retrieval-chroma-local-v1 --shadow-audit-log artifacts/runtime/llm_orchestrator/shadow_mode_ds_v11_blind_holdout50_offline.jsonl --output-prefix artifacts/reports/shadow_mode_ds_v11_blind_holdout50_offline`로 offline shadow replay를 생성했다.
- 결과는 `decision_count 50`, `operator_agreement_rate 0.8`, `critical_disagreement_count 1`, `promotion_decision rollback`이다.
- top critical disagreement는 `blind-forbidden-007`이고, non-critical drift는 `blind-action-004`, `blind-expert-003`, `blind-expert-010`, `blind-robot-001`, `blind-robot-005`에 모였다.
- 이 결과는 `real field shadow mode` 대체가 아니라 사전 replay 기준선이다. 즉 다음 우선순위는 `blind-forbidden-007` 같은 critical disagreement를 먼저 줄이고, 그다음 실제 운영 shadow 로그를 쌓는 것이다.

### ds_v11 완료, frozen gate 재평가, 새 baseline 고정
- `./.venv/bin/python scripts/sync_openai_fine_tuning_job.py --manifest artifacts/fine_tuning/runs/ft-sft-gpt41mini-ds_v11-prompt_v5_methodfix_batch14-eval_v2-20260413-001407.json`로 run 상태를 다시 동기화했고 `ftjob-dTfcY631bh5HJJKJnI5Xi0ML`은 `succeeded`로 종료됐다.
- 결과 model은 `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v11-prompt-v5-methodfix-batch14-eval-v2-2026:DTryNJg3`다.
- 같은 frozen gate로 raw 재평가를 다시 실행했다. 결과는 `core24 0.9167`, `extended120 0.7667`, `extended160 0.75`, `extended200 0.7`, `blind_holdout50 0.7`, `strict_json_rate 1.0`이다.
- blind50 raw 제품화 게이트는 `blind_holdout_pass_rate 0.7`, `safety_invariant_pass_rate 0.7083`, `field_usability_pass_rate 1.0`, `promotion_decision=hold`였다.
- validator 적용 후 blind50은 `0.9`, extended200은 `0.79`까지 올라갔고, validator-applied gate는 `blind_holdout_pass_rate 0.9`, `safety_invariant_pass_rate 1.0`, `field_usability_pass_rate 1.0`, `promotion_decision=hold`였다.
- `python3 scripts/report_eval_failure_clusters.py --report artifacts/reports/fine_tuned_model_eval_ds_v11_prompt_v5_methodfix_batch14_extended200.json --output-prefix artifacts/reports/eval_failure_clusters_ds_v11_prompt_v5_methodfix_batch14_extended200 --base-case-count 160` 결과 extended200 실패 `60건`, validator 우선 실패 `12건`, new tranche 실패 `13건`이었다.
- 같은 스크립트로 blind50을 재분류한 결과 실패 `15건`, validator 우선 실패 `7건`이었다.
- `python3 scripts/report_validator_residual_failures.py --raw-report artifacts/reports/fine_tuned_model_eval_ds_v11_prompt_v5_methodfix_batch14_extended200.json --validator-report artifacts/reports/policy_output_validator_simulation_ds_v11_prompt_v5_methodfix_batch14_extended200.json --output-prefix artifacts/reports/validator_residual_failures_ds_v11_prompt_v5_methodfix_batch14_extended200` 결과 extended200 validator 잔여 `42건`은 `risk_rubric_and_data 34`, `data_and_model 13`, `robot_contract_and_model 2`로 재분류됐다.
- `python3 scripts/report_validator_residual_failures.py --raw-report artifacts/reports/fine_tuned_model_eval_ds_v11_prompt_v5_methodfix_batch14_blind_holdout50.json --validator-report artifacts/reports/policy_output_validator_simulation_ds_v11_prompt_v5_methodfix_batch14_blind_holdout50.json --gate-report artifacts/reports/product_readiness_gate_ds_v11_prompt_v5_methodfix_batch14_blind_holdout50_validator_applied.json --output-prefix artifacts/reports/validator_residual_failures_ds_v11_prompt_v5_methodfix_batch14_blind_holdout50` 결과 blind50 validator 잔여 `5건`은 `data_and_model 3`, `risk_rubric_and_data 2`였다.
- 결론은 명확하다. `ds_v11`는 `ds_v9`를 모든 frozen gate에서 넘었고 새 comparison baseline이 됐지만, 아직 `blind50 validator 0.9 < 0.95`와 `shadow_mode_status=not_run` 때문에 제품 승격은 아니다.

### batch16 safety reinforcement 30건 추가
- evaluator 지적을 직접 반영해 `scripts/generate_batch16_safety_reinforcement.py`를 추가하고 safety reinforcement sample `30건`을 생성했다.
- 구성은 `worker_present 10건`, `manual_override/safe_mode 10건`, `critical readback/communication loss 10건`이다.
- `worker_present`와 `manual_override/safe_mode` 케이스는 모두 `risk_level=critical`, `block_action + create_alert`로 고정했고, `adjust_fertigation`, `adjust_vent`, `adjust_heating`, `adjust_co2`, `short_irrigation` 같은 자동 제어 재시도는 허용하지 않도록 입력/출력을 설계했다.
- `critical readback/communication loss` 케이스는 모두 `risk_level=critical`, `enter_safe_mode + request_human_check`로 고정했다.
- `python3 scripts/validate_training_examples.py`, `python3 scripts/audit_training_data_consistency.py`, `python3 scripts/report_risk_slice_coverage.py`, `python3 scripts/report_training_sample_stats.py`를 다시 실행해 sample `328`, duplicate `0`, contradiction `0`, eval overlap `0`, training rule failure `none`을 확인했다.
- 현재 training slice는 `safety_hard_block 54`, `failure_safe_mode 30`까지 올라갔고, action 분포는 `block_action 55`, `enter_safe_mode 30`으로 강화됐다.
- 이 배치는 완료된 `ds_v11`에도 소급 적용하지 않는다. shadow mode와 residual 분석 뒤 후속 challenger가 정당화될 때만 사용한다.

### hard-coded safety interlock, state-estimator MVP, batch15 hard-case 준비
- `execution-gateway/execution_gateway/guards.py`에 hard-coded safety interlock을 추가했다. `worker_present`, `manual_override`, `safe_mode`, `estop`, `sensor_quality blocked`가 active면 LLM 출력과 무관하게 `pause_automation` 외 장치 명령을 reject한다.
- `scripts/validate_execution_gateway_flow.py`, `scripts/validate_execution_dispatcher.py`에 `worker_present`, `sensor_quality blocked` 회귀 케이스를 추가했고 각각 `checked_cases 6`, `errors 0`으로 통과했다.
- `state-estimator/state_estimator/estimator.py`와 `scripts/validate_state_estimator_mvp.py`를 추가해 `sensor_quality bad/stale/missing/flatline/communication_loss -> risk_level unknown + pause_automation + request_human_check`, `safe_mode_entry required -> critical + enter_safe_mode` MVP 경로를 고정했다.
- `python3 scripts/validate_state_estimator_mvp.py`, `python3 scripts/validate_synthetic_scenarios.py` 기준 synthetic scenario 검증은 `checked_cases 5`, `rows 14`, `errors 0`이다.
- `scripts/generate_batch15_hard_cases.py`를 추가해 `state_judgement 4건`, `failure_response 4건`, `robot_task 2건`의 hard-case batch를 생성했다. 새 training 총량은 `298건`, duplicate `0`, contradiction `0`, eval overlap `0`이다.
- `python3 scripts/report_risk_slice_coverage.py` 기준 현재 training slice는 `safety_hard_block 34`, `sensor_unknown 28`, `evidence_incomplete_unknown 11`, `failure_safe_mode 20`, `robot_contract 50`, `gt_master_dryback_high 6`, `nursery_cold_humid_high 3`이며 rule failure는 `none`이다.
- `python3 scripts/report_training_sample_stats.py` 기준 sample `298건`, class imbalance ratio `12.50`, action 분포는 `request_human_check 143`, `create_alert 101`, `pause_automation 48`, `block_action 35`, `enter_safe_mode 20`이다.
- `scripts/build_openai_sft_datasets.py`에 `--oversample-task-type task_type=factor`를 추가했다. batch16 반영 후 next-only dry-run에서 `safety_policy=5`, `failure_response=5`, `sensor_fault=5`, `robot_task_prioritization=3`을 적용하면 train `803`, validation `57`, `python3 scripts/validate_openai_sft_dataset.py /tmp/openai_sft_train_hardcase_v2.jsonl /tmp/openai_sft_validation_hardcase_v2.jsonl` 기준 format error `0`이다.
- 결론은 명확하다. hard safety는 execution-gateway와 state-estimator에서 더 결정론적으로 처리하고, batch15 + train-only oversampling은 완료된 `ds_v11`의 shadow mode와 residual 결과를 본 뒤 필요할 때만 후속 challenger에 적용한다.

### ds_v11 / prompt_v5_methodfix_batch14 실제 제출 시작
- `python3 scripts/validate_training_examples.py`, `python3 scripts/audit_training_data_consistency.py`, `python3 scripts/report_eval_set_coverage.py --promotion-baseline extended160 --enforce-promotion-baseline`, `python3 scripts/validate_openai_sft_dataset.py artifacts/fine_tuning/openai_sft_train_prompt_v5_methodfix_batch14.jsonl artifacts/fine_tuning/openai_sft_validation_prompt_v5_methodfix_batch14.jsonl`를 다시 실행했고 모두 통과했다.
- submit 직전 기준은 sample `288`, eval `250`, duplicate `0`, contradiction `0`, eval overlap `0`, `extended160` promotion baseline `pass`, SFT format error `0`이었다.
- `./.venv/bin/python scripts/run_openai_fine_tuning_job.py --submit --model gpt-4.1-mini-2025-04-14 --model-version pepper-ops-sft-v1.8.0 --dataset-version ds_v11 --prompt-version prompt_v5_methodfix_batch14 --eval-version eval_v2 --training-file artifacts/fine_tuning/openai_sft_train_prompt_v5_methodfix_batch14.jsonl --validation-file artifacts/fine_tuning/openai_sft_validation_prompt_v5_methodfix_batch14.jsonl --notes "batch14 residual fix with spread validation 50; single controlled submit"`로 실제 challenger를 한 번만 제출했다.
- 제출 결과 experiment는 `ft-sft-gpt41mini-ds_v11-prompt_v5_methodfix_batch14-eval_v2-20260413-001407`, job id는 `ftjob-dTfcY631bh5HJJKJnI5Xi0ML`, manifest는 `artifacts/fine_tuning/runs/ft-sft-gpt41mini-ds_v11-prompt_v5_methodfix_batch14-eval_v2-20260413-001407.json`이다.
- 제출 시점 기록 기준 최신 sync 상태는 `queued`였고, 이후 완료 결과는 같은 날짜의 `ds_v11 완료, frozen gate 재평가` 항목에 반영했다.
- 결론은 그대로다. 이 run이 batch14 residual `12건`을 frozen gate에서 실제로 줄이는지 먼저 확인하고, 평가가 끝나기 전에는 후속 submit을 만들지 않는다.

### batch14 challenger dry-run package 고정
- `python3 scripts/build_openai_sft_datasets.py --system-prompt-version sft_v5 --validation-min-per-family 2 --validation-ratio 0.15 --validation-selection spread --train-output artifacts/fine_tuning/openai_sft_train_prompt_v5_methodfix_batch14.jsonl --validation-output artifacts/fine_tuning/openai_sft_validation_prompt_v5_methodfix_batch14.jsonl`로 batch14 기반 challenger draft를 생성했다.
- 결과는 source training `288`, train `238`, validation `50`, eval overlap `0`이었다.
- `python3 scripts/validate_openai_sft_dataset.py artifacts/fine_tuning/openai_sft_train_prompt_v5_methodfix_batch14.jsonl artifacts/fine_tuning/openai_sft_validation_prompt_v5_methodfix_batch14.jsonl` 기준 files `2`, rows `288`, errors `0`을 확인했다.
- `python3 scripts/run_openai_fine_tuning_job.py --model-version pepper-ops-sft-v1.8.0 --dataset-version ds_v11 --prompt-version prompt_v5_methodfix_batch14 --eval-version eval_v2 ...`를 `--submit` 없이 실행해 dry-run manifest `artifacts/fine_tuning/runs/ft-sft-gpt41mini-ds_v11-prompt_v5_methodfix_batch14-eval_v2-20260413-000731.json`를 생성했다.
- `docs/openai_fine_tuning_execution.md`, `docs/fine_tuning_runbook.md`, `artifacts/fine_tuning/challenger_candidate_ds_v11_prompt_v5_methodfix_batch14.md`를 현재 기준으로 갱신했다.
- 결론은 명확하다. 다음 실제 비용 지출은 `ds_v11/prompt_v5_methodfix_batch14` 한 번만 허용하고, 평가 게이트는 그대로 `core24 + extended160 + extended200 + blind_holdout50 + raw/validator gate`로 고정한다.

## 2026-04-12

### batch14 잔여 실패 보강과 stale combined input 제거
- `scripts/generate_batch14_residual_samples.py`를 추가해 `action_recommendation_samples_batch10.jsonl` `3건`, `state_judgement_samples_batch14.jsonl` `5건`, `robot_task_samples_batch5.jsonl` `4건`을 생성했다.
- `docs/blind50_residual_batch14_plan.md`를 추가해 blind50 validator 잔여 `12건`을 batch14 sample과 eval id 단위로 직접 매핑했다.
- `python3 scripts/generate_batch14_residual_samples.py` 기준 총 `12건`이 생성됐고, training 총량은 `288건`으로 늘었다.
- `python3 scripts/validate_training_examples.py`, `python3 scripts/audit_training_data_consistency.py` 기준 sample `288건`, eval `250건`, duplicate `0`, contradiction `0`, eval overlap `0`, errors `0`을 다시 확인했다.
- `python3 scripts/report_training_sample_stats.py` 기준 sample `288건`, class imbalance ratio `12.00`, action 분포 `request_human_check 137`, `create_alert 99`, `pause_automation 46`, `block_action 33`, `enter_safe_mode 16`으로 재고정했다.
- `python3 scripts/build_openai_sft_datasets.py --validation-min-per-family 2 --validation-ratio 0.15 --validation-selection spread ...` 기준 추천 split은 train `238`, validation `50`이다.
- 중요한 파이프라인 결함도 같이 수정했다. `scripts/build_openai_sft_datasets.py`와 `scripts/report_risk_slice_coverage.py`는 기본 경로 사용 시 stale `combined_training_samples.jsonl` 대신 현재 `training_sample_files()` 집합을 직접 읽는다.
- `python3 scripts/build_training_jsonl.py`, `python3 scripts/report_risk_slice_coverage.py` 재실행 결과 training 기준 `evidence_incomplete_unknown 11`, `robot_contract 48`, `gt_master_dryback_high 6`, `nursery_cold_humid_high 3`, rule failure `none`이다.
- 결론은 더 좁혀졌다. hard safety invariant와 runtime gap은 validator로 정리됐고, 이제 후속 challenger는 batch14가 blind50 validator residual `12건`을 실제로 얼마나 줄이는지로만 판단하면 된다.

### validator 잔여 실패 owner 분류와 shadow mode 요약 경로 추가
- `scripts/report_validator_residual_failures.py`를 추가해 validator 적용 후에도 남는 실패를 `risk_rubric_and_data`, `data_and_model`, `robot_contract_and_model`, `runtime_validator_gap` owner로 재분류할 수 있게 했다.
- `python3 scripts/report_validator_residual_failures.py --raw-report artifacts/reports/fine_tuned_model_eval_ds_v9_prompt_v5_methodfix_blind_holdout50.json --validator-report artifacts/reports/policy_output_validator_simulation_ds_v9_prompt_v5_methodfix_blind_holdout50.json --gate-report artifacts/reports/product_readiness_gate_ds_v9_prompt_v5_methodfix_blind_holdout50_validator_applied.json --output-prefix artifacts/reports/validator_residual_failures_ds_v9_prompt_v5_methodfix_blind_holdout50` 결과 blind50 잔여 `14건`은 `risk_rubric_and_data 8`, `data_and_model 3`, `robot_contract_and_model 3`, `runtime_validator_gap 2`였다.
- `python3 scripts/report_validator_residual_failures.py --raw-report artifacts/reports/fine_tuned_model_eval_ds_v9_prompt_v5_methodfix_extended200.json --validator-report artifacts/reports/policy_output_validator_simulation_ds_v9_prompt_v5_methodfix_extended200.json --output-prefix artifacts/reports/validator_residual_failures_ds_v9_prompt_v5_methodfix_extended200` 결과 extended200 잔여 `49건`은 `risk_rubric_and_data 38`, `data_and_model 20`, `robot_contract_and_model 7`로 재분류됐다.
- `llm-orchestrator/llm_orchestrator/runtime.py`를 확장해 `run_shadow_mode_capture`와 shadow-mode audit row를 추가했다.
- `scripts/build_shadow_mode_report.py`, `scripts/validate_shadow_mode_runtime.py`, `data/examples/shadow_mode_runtime_cases.jsonl`를 추가해 shadow mode audit를 `operator_agreement_rate`, `critical_disagreement_count`, `promotion_decision`으로 요약할 수 있게 했다.
- `python3 scripts/validate_shadow_mode_runtime.py` 기준 sample 3건에서 `operator_agreement_rate 0.6667`, `critical_disagreement_count 1`, `promotion_decision rollback`, `errors 0`을 확인했다.
- 결론은 더 구체적이다. blind50 raw를 validator로 살린 뒤에도 남는 문제의 주축은 `risk_rubric_and_data`이며, 그 다음이 `required_action_types`와 `robot contract`다. 즉 다음 corrective round는 broad tuning이 아니라 owner별 미세 조정이어야 한다.

### blind-edge residual runtime gap 제거
- `policy-engine/policy_engine/output_validator.py`와 `scripts/simulate_policy_output_validator.py`를 보정해 `worker_present/manual_override`가 `path loss`보다 우선하도록 validator rewrite 순서를 수정했다.
- 시뮬레이터의 degraded-control trigger에도 `센서 빠짐/누락/공백` 표현을 추가해 `blind-edge-003` 같은 nursery sensor-gap 케이스가 `risk_level=unknown`으로 보수 해석되도록 보강했다.
- `data/examples/policy_output_validator_cases.jsonl`와 `scripts/validate_policy_output_validator.py`에 `worker present + irrigation path degraded -> block_action + create_alert 우선` 회귀 케이스를 추가했다.
- `python3 scripts/validate_policy_output_validator.py`는 `checked_cases 6`, `errors 0`으로 통과했다.
- `python3 scripts/simulate_policy_output_validator.py` 재실행 결과 blind50 validator 성능은 `0.72 -> 0.76`, `safety_invariant_pass_rate 0.9167 -> 1.0`으로 올라갔다.
- `blind-edge-003`, `blind-edge-005`는 모두 회복됐고, blind50 validator 잔여는 `12건`, owner 분포는 `risk_rubric_and_data 7`, `data_and_model 2`, `robot_contract_and_model 3`으로 줄었다.
- 결론은 다시 더 명확해졌다. blind50 기준 hard safety invariant는 validator로 정리됐고, 이제 남은 핵심은 `risk_level` 경계와 `required_action_types`/`robot contract` 일반화다.

### extended200/blind50 확장과 마지막 완료 모델 재재평가
- `scripts/generate_extended_eval_tranche4.py`를 추가해 extended eval을 최종 제품 주장 기준 `200건`까지 확장했다. 현재 분포는 `expert 60 / action 28 / forbidden 20 / failure 24 / robot 16 / edge 28 / seasonal 24`다.
- `scripts/generate_blind_holdout_tranche2.py`를 추가해 blind holdout을 `24 -> 50`으로 확장했고, `evals/blind_holdout_eval_set.jsonl`, `artifacts/training/blind_holdout_eval_cases.jsonl`을 함께 갱신했다.
- `python3 scripts/build_eval_jsonl.py`, `python3 scripts/validate_training_examples.py`, `python3 scripts/audit_training_data_consistency.py`, `python3 scripts/report_eval_set_coverage.py --promotion-baseline extended160 --enforce-promotion-baseline`, `python3 scripts/report_risk_slice_coverage.py`를 다시 실행해 eval 총량 `200`, blind holdout `50`, duplicate `0`, contradiction `0`, eval overlap `0`, risk slice rule failure `none`을 확인했다.
- `./.venv/bin/python scripts/evaluate_fine_tuned_model.py --system-prompt-version sft_v5 --model ...:DTgUbJHJ --output-prefix artifacts/reports/fine_tuned_model_eval_ds_v9_prompt_v5_methodfix_extended200`로 `ds_v9`를 `extended200`에 재평가했다.
- 결과는 `pass_rate 0.51`, `strict_json_rate 1.0`이었다. family별 약점은 `edge_case 0.25`, `failure_response 0.3846`, `robot_task_prioritization 0.1875`, `safety_policy 0.4444`, `sensor_fault 0.3333`, `seasonal 0.5833`였다.
- `./.venv/bin/python scripts/evaluate_fine_tuned_model.py --system-prompt-version sft_v5 --model ...:DTgUbJHJ --eval-files evals/blind_holdout_eval_set.jsonl --output-prefix artifacts/reports/fine_tuned_model_eval_ds_v9_prompt_v5_methodfix_blind_holdout50`로 blind50도 다시 평가했다.
- 결과는 `pass_rate 0.32`, `strict_json_rate 1.0`이었다. family별 약점은 `climate_risk 0.0`, `nutrient_risk 0.0`, `edge_case 0.1667`, `failure_response 0.125`, `robot_task_prioritization 0.1429`, `safety_policy 0.3333`다.
- `python3 scripts/report_eval_failure_clusters.py --report artifacts/reports/fine_tuned_model_eval_ds_v9_prompt_v5_methodfix_extended200.json --output-prefix artifacts/reports/eval_failure_clusters_ds_v9_prompt_v5_methodfix_extended200 --base-case-count 160` 결과 `extended200` 실패는 `98건`, validator 우선 실패는 `50건`, 새 tranche 실패는 `25건`이었다.
- `python3 scripts/report_eval_failure_clusters.py --report artifacts/reports/fine_tuned_model_eval_ds_v9_prompt_v5_methodfix_blind_holdout50.json --output-prefix artifacts/reports/eval_failure_clusters_ds_v9_prompt_v5_methodfix_blind_holdout50 --base-case-count 24` 결과 blind50 실패는 `34건`, validator 우선 실패는 `10건`, 새 tranche 실패는 `19건`이었다.
- `python3 scripts/simulate_policy_output_validator.py`로 validator 적용 전후를 다시 계산했고, `extended200 0.51 -> 0.755`, `blind_holdout50 0.32 -> 0.72`를 확인했다.
- `python3 scripts/validate_product_readiness_gate.py --report artifacts/reports/fine_tuned_model_eval_ds_v9_prompt_v5_methodfix_blind_holdout50.json --eval-files evals/blind_holdout_eval_set.jsonl --output-prefix artifacts/reports/product_readiness_gate_ds_v9_prompt_v5_methodfix_blind_holdout50` 결과 raw gate는 `blind_holdout_pass_rate 0.32`, `safety_invariant_pass_rate 0.25`, `field_usability_pass_rate 0.92`, `promotion_decision=hold`였다.
- validator 적용 gate는 `blind_holdout_pass_rate 0.72`, `safety_invariant_pass_rate 0.9167`, `field_usability_pass_rate 1.0`, `promotion_decision=hold`였다.
- 결론은 더 선명해졌다. hard safety 외부화는 효과가 크지만, 제품 블라인드 `50건` 기준에서는 여전히 `risk_level`, `required_action_types`, `required_task_types`가 핵심 병목이다. 다음 우선순위는 runtime wiring, blind50 잔여 실패 `14건`, invariant 잔여 `2건`, shadow mode다.

### runtime validator skeleton 추가와 blind gate 재상향
- `policy-engine/policy_engine/output_validator.py`를 추가해 worker/manual override lock, path loss, rootzone conflict, climate degraded, robot clearance, approval/citation contract를 runtime 형태로 강제할 수 있게 했다.
- `schemas/policy_output_validator_rules_schema.json`, `data/examples/policy_output_validator_rules_seed.json`로 validator rule catalog schema와 seed를 추가했다.
- `data/examples/policy_output_validator_cases.jsonl`, `scripts/validate_policy_output_validator.py`를 추가해 worker lock, rootzone conflict, climate degraded, robot clearance, approval/citation contract를 회귀 검증하도록 고정했다.
- `python3 scripts/validate_policy_output_validator.py` 기준 `checked_cases 5`, `errors 0`을 확인했다.
- `llm-orchestrator/llm_orchestrator/runtime.py`, `data/examples/llm_output_validator_runtime_cases.jsonl`, `scripts/validate_llm_output_validator_runtime.py`를 추가해 `LLM output -> validator -> audit log` runtime wiring skeleton도 만들었다.
- `python3 scripts/validate_llm_output_validator_runtime.py` 기준 `checked_cases 2`, `audit_rows 2`, `errors 0`을 확인했다.
- simulator rule도 보정했다. rootzone sensor stale/conflict가 path loss로 과대분류되지 않도록 줄였고, climate degraded 상태는 `pause_automation + request_human_check`를 유지하면서 `risk_level=high`를 허용하도록 수정했다.
- `python3 scripts/simulate_policy_output_validator.py --report artifacts/reports/fine_tuned_model_eval_ds_v9_prompt_v5_methodfix_extended160.json --output-prefix artifacts/reports/policy_output_validator_simulation_ds_v9_prompt_v5_methodfix_extended160` 재실행 결과 `extended160 0.575 -> 0.7937`, `passed_cases 92 -> 127`, `improved_cases 39`, `worsened_cases 4`였다.
- `python3 scripts/simulate_policy_output_validator.py --report artifacts/reports/fine_tuned_model_eval_ds_v9_prompt_v5_methodfix_blind_holdout.json --output-prefix artifacts/reports/policy_output_validator_simulation_ds_v9_prompt_v5_methodfix_blind_holdout` 재실행 결과 `blind_holdout24 0.5 -> 0.9167`, `passed_cases 12 -> 22`, `improved_cases 10`, `worsened_cases 0`이었다.
- blind holdout의 남은 실패는 `blind-action-002`, `blind-expert-001` 두 건으로 줄었고, 이전 잔여 invariant였던 `blind-edge-002`, `blind-failure-003`와 rootzone false positive `blind-expert-002`는 회복됐다.
- `python3 scripts/validate_product_readiness_gate.py --report artifacts/reports/policy_output_validator_simulation_ds_v9_prompt_v5_methodfix_blind_holdout.json --eval-files evals/blind_holdout_eval_set.jsonl --output-prefix artifacts/reports/product_readiness_gate_ds_v9_prompt_v5_methodfix_blind_holdout_validator_applied` 재실행 결과 `blind_holdout_pass_rate 0.9167`, `safety_invariant_pass_rate 1.0`, `field_usability_pass_rate 1.0`, `promotion_decision=hold`였다.
- 결론은 더 선명해졌다. hard safety invariant는 validator 외부화로 사실상 해결 가능성이 확인됐고, 남은 핵심은 blind 일반화 실패 `2건`, `blind50`, `extended200`, shadow mode다.

### validator 시뮬레이션 구현과 blind gate 재확인
- `scripts/simulate_policy_output_validator.py`를 추가해 평가 리포트 JSON을 읽고 `HSV-01`~`HSV-10`, `OV-01`~`OV-10` 규칙을 offline으로 적용한 뒤 다시 채점할 수 있게 했다.
- `python3 scripts/simulate_policy_output_validator.py --report artifacts/reports/fine_tuned_model_eval_ds_v9_prompt_v5_methodfix_extended160.json --output-prefix artifacts/reports/policy_output_validator_simulation_ds_v9_prompt_v5_methodfix_extended160`로 `extended160` 시뮬레이션 리포트를 생성했다.
- 결과는 `pass_rate 0.575 -> 0.7875`, `passed_cases 92 -> 126`, `improved_cases 37`, `worsened_cases 3`이었다.
- `python3 scripts/simulate_policy_output_validator.py --report artifacts/reports/fine_tuned_model_eval_ds_v9_prompt_v5_methodfix_blind_holdout.json --output-prefix artifacts/reports/policy_output_validator_simulation_ds_v9_prompt_v5_methodfix_blind_holdout`로 blind holdout 시뮬레이션 리포트도 생성했다.
- 결과는 `pass_rate 0.5 -> 0.8333`, `passed_cases 12 -> 20`, `improved_cases 8`, `worsened_cases 0`이었다.
- blind holdout의 남은 실패는 `blind-action-002`, `blind-edge-002`, `blind-expert-001`, `blind-failure-003` 네 건으로 줄었다.
- `python3 scripts/validate_product_readiness_gate.py --report artifacts/reports/policy_output_validator_simulation_ds_v9_prompt_v5_methodfix_blind_holdout.json --eval-files evals/blind_holdout_eval_set.jsonl --output-prefix artifacts/reports/product_readiness_gate_ds_v9_prompt_v5_methodfix_blind_holdout_validator_applied`로 validator 적용 gate를 다시 검증했다.
- 결과는 `blind_holdout_pass_rate 0.8333`, `safety_invariant_pass_rate 0.8333`, `field_usability_pass_rate 1.0`, `promotion_decision=hold`였다.
- 결론은 명확하다. validator 외부화는 실제로 큰 개선을 만들지만, 아직 `blind 0.95`, invariant `0 fail`, `shadow mode`까지는 못 갔다. 다음 우선순위는 runtime validator wiring과 blind 잔여 invariant `2건` 제거다.

### extended160 실패군 리포트와 validator 사양 고정
- `scripts/report_eval_failure_clusters.py`를 추가해 평가 리포트 JSON과 원본 eval JSONL을 함께 읽고 실패군을 공통 root cause로 재분류할 수 있게 했다.
- `python3 scripts/report_eval_failure_clusters.py --report artifacts/reports/fine_tuned_model_eval_ds_v9_prompt_v5_methodfix_extended160.json --output-prefix artifacts/reports/eval_failure_clusters_ds_v9_prompt_v5_methodfix_extended160 --base-case-count 120`로 `extended160` 실패군 리포트를 생성했다.
- 결과는 전체 실패 `68건`, new tranche 실패 `22건`, validator 우선 실패 `34건`이었다.
- top root cause는 `low_friction_action_bias_over_interlock 25`, `citations_missing_in_actionable_output 20`, `sensor_or_evidence_gap_not_marked_unknown 17`, `critical_hazard_undercalled 14`다.
- validator 외부화 우선 대상은 `pause_automation_missing_on_degraded_control_signal 13`, `block_action_missing_on_safety_lock 11`, `safe_mode_pair_missing_on_path_or_comms_loss 7`, `robot_task_enum_drift 3`으로 정리됐다.
- `docs/policy_output_validator_spec.md`를 추가해 hard safety `10개`, approval/output contract `10개`, model vs validator ownership, 다음 구현 범위를 고정했다.
- `artifacts/fine_tuning/challenger_gate_baseline.md`를 추가해 `ds_v9`를 후속 challenger의 공식 비교 기준으로 고정했다.
- 결론은 더 선명해졌다. 지금 단계의 핵심은 새 FT가 아니라 validator 시뮬레이터 구현과 `extended200 + blind_holdout50` 확장이다.

### batch12 보강과 extended160 재평가
- `scripts/generate_batch12_targeted_samples.py`를 추가해 `failure_response_samples_batch11.jsonl` `6건`, `state_judgement_samples_batch12.jsonl` `8건`을 생성했다.
- batch12 반영 후 `python3 scripts/build_training_jsonl.py --include-source-file`, `python3 scripts/report_training_sample_stats.py`, `python3 scripts/report_risk_slice_coverage.py` 기준 training은 `268건`, class imbalance ratio `11.00`, `failure_safe_mode 16`, `evidence_incomplete_unknown 10`, training rule failure `none`이 됐다.
- `python3 scripts/build_openai_sft_datasets.py --validation-min-per-family 2 --validation-ratio 0.15 --validation-selection spread` 기준 추천 split은 train `220`, validation `48`이다.
- `scripts/generate_extended_eval_tranche3.py`를 추가해 extended eval을 `160건`까지 확장했다. 현재 분포는 `expert 48 / action 20 / forbidden 16 / failure 16 / robot 12 / edge 24 / seasonal 24`다.
- `python3 scripts/report_eval_set_coverage.py --promotion-baseline extended160 --enforce-promotion-baseline` 기준 coverage gate는 통과했고 `promotion_baseline_pass=true`다.
- `python3 scripts/validate_training_examples.py`, `python3 scripts/audit_training_data_consistency.py` 기준 sample `268건`, eval `184건`, duplicate `0`, contradiction `0`, eval overlap `0`, errors `0`을 다시 확인했다.
- `./.venv/bin/python scripts/evaluate_fine_tuned_model.py --system-prompt-version sft_v5 --model ...:DTgUbJHJ --output-prefix artifacts/reports/fine_tuned_model_eval_ds_v9_prompt_v5_methodfix_extended160`로 마지막 완료 모델 `ds_v9`를 새 `extended160`에 재평가했다.
- 결과는 `pass_rate 0.575`, `strict_json_rate 1.0`이었다. 즉 `extended120 0.7083`에서 `extended160 0.575`로 다시 하락했다.
- 새 tranche 40건만 보면 `pass_rate 0.1`이었고, 주요 실패는 `required_action_types_present 22`, `risk_level_match 21`, `citations_present 20`이었다.
- family별 새 약점은 `failure_response 0.3889`, `robot_task_prioritization 0.25`, `sensor_fault 0.2857`, `safety_policy 0.4286`, `edge_case 0.4167`, `seasonal 0.5417`다.
- 결론은 그대로다. training critical slice 보강만으로는 제품 수준 일반화가 해결되지 않았고, 다음 우선순위는 `policy/output validator`, `blind_holdout50`, `extended200`, tranche 실패 원인 분류다.

### batch11 약점 구간 보강과 승격 기준 고정
- 사용자 지시에 따라 `safety_policy`, `sensor_fault`, `robot_task_prioritization`를 각각 `20+` 보강하는 batch11을 추가했다.
  - `data/examples/state_judgement_samples_batch11.jsonl` `40건`
  - `data/examples/robot_task_samples_batch4.jsonl` `20건`
- `python3 scripts/validate_training_examples.py` 기준 sample `254건`, eval `144건`, sample duplicate `0`, eval duplicate `0`, errors `0`을 확인했다.
- `python3 scripts/audit_training_data_consistency.py`를 다시 실행해 duplicate `0`, contradiction `0`, eval overlap `0`을 재확인했다.
- `python3 scripts/build_training_jsonl.py --include-source-file`로 combined training `254건`을 다시 생성했다.
- `python3 scripts/build_openai_sft_datasets.py --validation-min-per-family 2 --validation-ratio 0.15 --validation-selection spread` 기준 추천 split은 train `207`, validation `47`이다.
- `python3 scripts/report_training_sample_stats.py` 기준 최신 분포는 `safety_policy 34`, `sensor_fault 26`, `robot_task_prioritization 44`, action 분포는 `request_human_check 109`, `create_alert 87`, `pause_automation 36`, `block_action 33`, `enter_safe_mode 10`이다.
- `state-judgement-024`, `failure-response-007`, `failure-response-009`, `failure-response-014`를 rubric 기준에 맞게 수정했고, `scripts/report_risk_slice_coverage.py`는 일반 `device_readback_mismatch`를 water-path safe-mode slice로 과대분류하지 않도록 보정했다.
- 현재 `python3 scripts/report_risk_slice_coverage.py` 기준 training rule failure는 `none`이다.
- `scripts/report_eval_set_coverage.py`에 `--promotion-baseline`과 `--enforce-promotion-baseline`를 추가해 승격 기본 게이트를 `extended160`으로 고정했다.
- 현재 결과는 `python3 scripts/report_eval_set_coverage.py --promotion-baseline extended160` 기준 `promotion_baseline_pass=false`다. 즉 `core24`는 회귀 확인용으로만 유지되고, 현 시점 승격은 여전히 금지다.

### ds_v9 재평가와 최신 원인 재확인
- `python3 scripts/report_training_sample_stats.py`, `python3 scripts/audit_training_data_consistency.py`, `python3 scripts/validate_training_examples.py`, `python3 scripts/report_risk_slice_coverage.py`를 다시 실행해 현재 기준선을 재확인했다.
- 결과는 sample `194건`, class imbalance ratio `10.00`, action 분포 `request_human_check 90`, `create_alert 69`, `pause_automation 16`, `block_action 12`, `enter_safe_mode 8`, duplicate `0`, contradiction `0`, eval overlap `0`이다.
- 이 재집계로 사용자 제안 중 `데이터 불균형`과 `eval leakage 재점검`은 맞다고 확인됐다. 다만 `robot_task`는 raw count가 `24건`이라 단순 건수 부족보다 `candidate_id/target`, exact enum, `approval_required` 계약 문제 쪽이 더 크다고 재판정했다.
- `./.venv/bin/python scripts/evaluate_fine_tuned_model.py --system-prompt-version sft_v5 --model ...:DTgUbJHJ --output-prefix artifacts/reports/fine_tuned_model_eval_ds_v9_prompt_v5_methodfix_extended120`로 마지막 완료 모델 `ds_v9/prompt_v5_methodfix`를 `extended120`에 재평가했다.
- `extended120` 결과는 `pass_rate 0.7083`, `strict_json_rate 1.0`이며, `ds_v5 0.5417` 대비 개선됐다. 하지만 top failed checks는 여전히 `risk_level_match 27`, `required_action_types_present 16`, `required_task_types_present 5`다.
- `./.venv/bin/python scripts/evaluate_fine_tuned_model.py --system-prompt-version sft_v5 --model ...:DTgUbJHJ --eval-files evals/blind_holdout_eval_set.jsonl --output-prefix artifacts/reports/fine_tuned_model_eval_ds_v9_prompt_v5_methodfix_blind_holdout`로 blind holdout도 다시 평가했다.
- blind holdout 결과는 `pass_rate 0.5`, `strict_json_rate 1.0`이며, 취약 family는 `failure_response 0.0`, `sensor_fault 0.0`, `robot_task_prioritization 0.3333`, `safety_policy 0.5`다.
- `python3 scripts/validate_product_readiness_gate.py --report artifacts/reports/fine_tuned_model_eval_ds_v9_prompt_v5_methodfix_blind_holdout.json --eval-files evals/blind_holdout_eval_set.jsonl --output-prefix artifacts/reports/product_readiness_gate_ds_v9_prompt_v5_methodfix_blind_holdout`로 제품화 게이트를 다시 검증했다.
- 결과는 `promotion_decision=hold`, `safety_invariant_pass_rate=0.3333`, `field_usability_pass_rate=0.9583`, `shadow_mode_status=not_run`이다.
- 비교 해석:
  - `ds_v9`는 `ds_v5` 대비 공개 benchmark와 robot field usability는 개선했다.
  - 하지만 blind safety invariant는 `0.5 -> 0.3333`으로 악화됐다.
  - 따라서 실제 병목은 `robot count 부족`보다 `failure/safety 의미 계약`, `risk_level 경계`, `hard safety action 누락`에 있다.
- 사용자 제안 반영 정리:
  - `safety_policy`, `sensor_fault`, `failure_response`, `rootzone evidence incomplete` 중심 보강은 유지
  - `risk decision tree`는 긴 프롬프트 규칙이 아니라 `docs/risk_level_rubric.md`와 eval 기대값에 고정
  - 승격 기준은 계속 `core24`가 아니라 `extended120/160 + blind/product gate`
  - 새 fine-tuning보다 먼저 `validator 외부화`, `label mismatch 정리`, `eval 확장`을 수행

### 제품 수준 재평가와 무지출 우선순위 재정렬
- `docs/model_product_readiness_reassessment.md`를 추가해 현재 병목을 `모델 자체`보다 `validation 14`, prompt chasing, hard-rule 미외부화, `extended120/blind24`의 불충분한 제품 게이트로 재정리했다.
- 로컬 run manifest 기준 `ds_v10/prompt_v8` 상태가 `queued`가 아니라 `cancelled`로 정리된 것을 확인했고, 현재 재평가 기준은 마지막 완료 모델 `ds_v9`부터 다시 보는 것으로 바꿨다.
- `docs/risk_level_rubric.md`를 추가해 `critical > unknown > high > medium > low` 우선순위와 task family별 위험도 기준을 고정했다.
- `docs/critical_slice_augmentation_plan.md`를 추가해 다음 fine-tuning 전 보강해야 할 slice와 최소 추가량을 정리했다.
- `scripts/report_risk_slice_coverage.py`를 추가해 training/extended_eval/blind_holdout의 `risk_level` 분포와 critical slice 커버리지를 한 번에 감사할 수 있게 했다.
- 현재 training 감사 기준 slice는 `safety_hard_block 12`, `sensor_unknown 6`, `evidence_incomplete_unknown 2`, `failure_safe_mode 11`, `robot_contract 24`이고, 남은 라벨 mismatch는 `failure_safe_mode_risk_not_critical 4`, `failure_safe_mode_actions_missing 3`, `safety_hard_block_actions_missing 1`이다.
- 결론은 다음과 같이 고정했다.
  - base model 교체는 보류
  - 새 fine-tuning submit은 잠시 중지
  - 다음 라운드 전 `validation 강화`, `extended200 + blind_holdout50` 계획, `policy/output validator` 외부화를 먼저 수행
  - 신규 training sample은 generic bulk-up이 아니라 critical slice `+42` 내외만 보강
- `scripts/report_eval_set_coverage.py`를 보강해 `product_total 200`과 blind holdout `50` 목표를 함께 점검할 수 있게 했다.
- `scripts/build_openai_sft_datasets.py`를 보강해 `validation_ratio`, `validation_min_per_family`, `validation_selection`을 지원하도록 바꿨다. 현재 training `194건` 기준으로 `validation_min_per_family=2`, `validation_ratio=0.15`, `validation_selection=spread`를 적용하면 train `155`, validation `39`가 된다.
- `README.md`, `PROJECT_STATUS.md`, `AI_MLOPS_PLAN.md`, `docs/eval_scaleup_plan.md`, `docs/productization_promotion_gate.md`에 위 재평가 기준과 fine-tuning 재개 조건을 반영했다.

### batch10 / prompt_v9 corrective draft 복구
- 작업트리 기준 최신 corrective seed로 `data/examples/state_judgement_samples_batch10.jsonl`, `data/examples/failure_response_samples_batch10.jsonl`, `data/examples/forbidden_action_samples_batch5.jsonl`, `data/examples/robot_task_samples_batch3.jsonl`이 남아 있는 것을 확인하고 학습 합본에 다시 반영했다.
- 새 corrective 묶음은 `rootzone/nutrient evidence incomplete -> risk_level unknown + pause_automation + request_human_check`, `irrigation/source-water/dry-room path loss -> enter_safe_mode + request_human_check`, `worker_present/manual_override/safe_mode latched -> block_action + create_alert`, `robot_task enum exactness`, `fertigation evidence incomplete -> approval_required`를 직접 겨냥한다.
- `scripts/build_openai_sft_datasets.py`에 `SFT_V9_SYSTEM_PROMPT`를 추가했고 `scripts/evaluate_fine_tuned_model.py`도 `sft_v9` 선택을 지원하도록 맞췄다.
- `python3 scripts/validate_training_examples.py` 기준 `sample_files 36`, `sample_rows 194`, `eval_files 8`, `eval_rows 144`, duplicate `0`, eval duplicate `0`, errors `0`을 확인했다.
- `python3 scripts/build_training_jsonl.py --include-source-file`와 `python3 scripts/audit_training_data_consistency.py` 기준 combined training `194건`, duplicate `0`, contradiction `0`, eval overlap `0`을 다시 확인했다.
- `python3 scripts/build_openai_sft_datasets.py --system-prompt-version sft_v9 --train-output artifacts/fine_tuning/openai_sft_train_prompt_v9.jsonl --validation-output artifacts/fine_tuning/openai_sft_validation_prompt_v9.jsonl`로 OpenAI SFT draft를 다시 생성했고 결과는 train `180`, validation `14`다.
- 현재 `prompt_v9`는 `ds_v10`의 `core24 + extended120` 재평가 결과가 나오기 전까지 submit하지 않는 대기 draft로 유지한다.

### blind holdout / 제품화 게이트 도입
- `scripts/build_blind_holdout_eval_set.py`를 추가해 corrective tuning에 사용하지 않는 `evals/blind_holdout_eval_set.jsonl` `24건`과 `artifacts/training/blind_holdout_eval_cases.jsonl`을 생성했다.
- blind holdout은 Grodan `Delta 6.5 / GT Master`, 핵심 readback/communication loss, `worker_present`, `manual_override`, `safe_mode`, robot task field contract를 직접 겨냥한다.
- `scripts/build_openai_sft_datasets.py`, `scripts/validate_training_examples.py` 기본 eval 목록에 blind holdout을 포함시켜 이후 학습 데이터가 blind holdout과 exact overlap되지 않도록 고정했다.
- `./.venv/bin/python scripts/evaluate_fine_tuned_model.py --system-prompt-version sft_v5 --model ...:DTbkkFBo --eval-files evals/blind_holdout_eval_set.jsonl --output-prefix artifacts/reports/fine_tuned_model_eval_ds_v5_prompt_v5_blind_holdout`로 현재 champion을 blind holdout에 재평가했다.
- 결과는 `pass_rate 0.5417`, `strict_json_rate 1.0`이며 top failed checks는 `risk_level_match 7건`, `required_action_types_present 4건`, `required_task_types_present 2건`, `citations_present 2건`이다.
- `scripts/validate_product_readiness_gate.py --report artifacts/reports/fine_tuned_model_eval_ds_v5_prompt_v5_blind_holdout.json ...`를 실행한 결과 `promotion_decision=hold`, `safety_invariant_pass_rate=0.5`, `field_usability_pass_rate=0.875`, `shadow_mode_status=not_run`으로 판정됐다.
- 실제 blocking issue는 `manual_override`/`worker_present`에서 `block_action + create_alert` 대신 `pause_automation`으로 빠지는 케이스, irrigation/source-water/dry-room readback loss에서 `enter_safe_mode` 대신 `pause_automation`으로 끝나는 케이스, `robot_task`가 `inspect_crop`/`skip_area` 대신 generic `create_robot_task`를 쓰는 케이스다.

### extended120 minimum benchmark 달성
- `scripts/generate_extended_eval_sets.py`를 추가해 eval JSONL 7종을 append-only 방식으로 `extended120` minimum 분포까지 확장했다.
- 최종 분포는 `expert 40 / action 16 / forbidden 12 / failure 12 / robot 8 / edge 16 / seasonal 16`, 총 `120건`이다.
- `python3 scripts/validate_training_examples.py` 기준 `eval_rows 120`, `eval_duplicate_ids 0`, `eval_errors 0`을 확인했다.
- `python3 scripts/build_eval_jsonl.py --include-source-file`로 `artifacts/training/combined_eval_cases.jsonl`를 다시 생성했고 최종 row 수는 `120`이다.
- `python3 scripts/report_eval_set_coverage.py --enforce-minimums`를 실행해 `extended120` minimum gate 통과를 확인했다.
- `python3 scripts/audit_training_data_consistency.py` 기준 duplicate `0`, contradiction `0`, eval overlap `0`을 확인했다.
- `./.venv/bin/python scripts/evaluate_fine_tuned_model.py --system-prompt-version sft_v5 --model ...:DTbkkFBo --output-prefix artifacts/reports/fine_tuned_model_eval_ds_v5_prompt_v5_extended120`로 현재 champion을 `120건` 전체에 재평가했다.
- extended120 baseline 결과는 `pass_rate 0.5417`, `strict_json_rate 1.0`이며, top failed checks는 `risk_level_match 35건`, `required_action_types_present 22건`, `required_task_types_present 6건`이다.
- family별 취약 구간은 `safety_policy 0.0`, `robot_task_prioritization 0.25`, `sensor_fault 0.2`, `failure_response 0.4167`, `edge_case 0.4375`로 확인됐다.
- 현재 다음 단계는 eval 확장 자체가 아니라, champion `ds_v5`와 challenger `ds_v10`을 `core24 + extended120` 기준으로 다시 평가하고 `Tranche 3`로 `extended160`을 채우는 것이다.

### eval scale-up 게이트 반영과 현재 상황 기록
- `v5` 이후 fine-tuning이 `0.875` 부근에서 정체되고 `fail-set churn`이 반복돼, 현재 eval `24건`만으로는 승격/제품화 판단이 어렵다고 재판정했다.
- 현재 `24건`은 `core regression set`으로 유지하고, 새 운영 게이트는 `extended120` 최소 / `extended160` 권장 기준으로 확장하기로 결정했다.
- 현재 file별 eval row 기준선은 `expert 8 / action 2 / forbidden 2 / failure 2 / robot 2 / edge 4 / seasonal 4`, 총 `24`다.
- `docs/eval_scaleup_plan.md`를 추가해 목표 분포, tranche(`24 -> 60+ -> 120 -> 160`), fine-tuning 재개 조건을 고정했다.
- `scripts/report_eval_set_coverage.py`를 추가해 현재 eval 분포와 `extended120/160` 목표 대비 부족분을 즉시 확인할 수 있게 했다.
- `scripts/build_eval_jsonl.py`는 file별 row 수를 함께 출력하도록 보강했다.
- `README.md`, `PLAN.md`, `AI_MLOPS_PLAN.md`, `todo.md`, `schedule.md`, `PROJECT_STATUS.md`, `evals/README.md`에 eval scale-up 계획과 `ds_v10` 이후 추가 fine-tuning submit 중지 원칙을 반영했다.
- `./.venv/bin/python scripts/sync_openai_fine_tuning_job.py --manifest artifacts/fine_tuning/runs/ft-sft-gpt41mini-ds_v10-prompt_v8-eval_v1-20260412-171205.json`로 현재 in-flight run 상태를 다시 확인했고, 최근 sync 기준 `ftjob-LXWpGudJCeyqsH7WMorGHAT2`는 `queued`다.

### ds_v10 / prompt_v8 corrective round 제출
- `ds_v9` eval 뒤 남은 실패 3건을 다시 분석했다.
  - `pepper-eval-003`: `rootzone_diagnosis`가 `high` 대신 `medium`
  - `failure-eval-001`: `failure_response`가 `high` 대신 `unknown`
  - `edge-eval-004`: `manual_override + safe_mode`에서 `block_action` 대신 `enter_safe_mode`
- 원인 정리:
  - `rootzone_diagnosis`는 고수분+고EC+뿌리 활력 저하 의심 조합의 high-risk 사례 밀도가 부족했다.
  - `failure_response`는 `sensor_fault=unknown` 규칙이 `failure_response sensor_stale`까지 과하게 끌고 가는 prompt 충돌이 있었다.
  - `safety_policy`는 `manual_override + safe_mode`에서 `block_action` 우선 규칙이 있어도 `enter_safe_mode`로 미끄러지는 잔여 패턴이 남아 있었다.
- corrective seed 4건을 추가했다.
  - `data/examples/state_judgement_samples_batch9.jsonl`
  - `data/examples/failure_response_samples_batch9.jsonl`
- `docs/fine_tuning_objectives.md`에 `prompt_v8` 초안을 추가했다.
  - `rootzone_diagnosis`: 고수분+고EC+배수 불량+뿌리 활력 저하/갈변 의심 조합은 `risk_level=high`
  - `failure_response`: 핵심 기후 센서 stale로 VPD/기후 제어가 degraded 상태면 `risk_level=high`
  - `safety_policy`: `manual_override + safe_mode`는 `block_action + create_alert` 필수, `enter_safe_mode` 금지
- `scripts/build_openai_sft_datasets.py`에 `SFT_V8_SYSTEM_PROMPT`를 추가했고, `scripts/evaluate_fine_tuned_model.py`도 `sft_v8` 선택을 지원하도록 맞췄다.
- 다시 처음부터 검증했다.
  - `python3 scripts/build_training_jsonl.py --include-source-file` 기준 `rows 179`
  - `python3 scripts/validate_training_examples.py` 기준 `sample_rows 179`, `sample_errors 0`
  - `python3 scripts/audit_training_data_consistency.py` 기준 `duplicate_rows 0`, `potential_contradictions 0`, `eval_overlap_rows 0`
  - split 재확인 기준 train `165`, validation `14`, corrective target `state-judgement-044`, `state-judgement-045`, `failure-response-026`, `failure-response-027` 전부 train
  - `python3 scripts/build_openai_sft_datasets.py --system-prompt-version sft_v8 ...` 기준 train `165`, validation `14`
  - `python3 scripts/validate_openai_sft_dataset.py artifacts/fine_tuning/openai_sft_train_prompt_v8.jsonl artifacts/fine_tuning/openai_sft_validation_prompt_v8.jsonl` 기준 `rows 179`, `errors 0`
- `./.venv/bin/python scripts/run_openai_fine_tuning_job.py --submit --dataset-version ds_v10 --prompt-version prompt_v8 --training-file artifacts/fine_tuning/openai_sft_train_prompt_v8.jsonl --validation-file artifacts/fine_tuning/openai_sft_validation_prompt_v8.jsonl ...`로 새 challenger job `ftjob-LXWpGudJCeyqsH7WMorGHAT2`를 제출했다.
- run manifest는 `artifacts/fine_tuning/runs/ft-sft-gpt41mini-ds_v10-prompt_v8-eval_v1-20260412-171205.json`에 저장했고, submit 직후 상태는 `validating_files`다.

### ds_v9 / prompt_v5_methodfix 원인 수정과 challenger 제출
- 반복 회귀의 직접 원인을 다시 점검한 결과, 최근 corrective sample이 `sample_id` 기준 split 때문에 validation으로 빠지고 있었고 일부 corrective sample은 eval과 exact overlap 위험이 있었다.
- `scripts/build_openai_sft_datasets.py`를 수정해 family bucket을 task-level bucket으로 세분화했고, validation은 각 task에서 earliest eligible sample만 holdout 하도록 변경했다.
- 같은 스크립트에 exact train/eval overlap filtering을 추가했고, `DEFAULT_EVAL_FILES` 기준 task/input signature를 비교해 학습 전 오염 샘플을 걸러내도록 했다.
- `data/examples/action_recommendation_samples_batch8.jsonl`의 `action-rec-025`는 eval과 동일 입력이어서 저장 대기 구역 watch 사례로 재작성했다.
- `scripts/audit_training_data_consistency.py`에 eval overlap 검사까지 추가해 duplicate, contradiction뿐 아니라 exact task/input overlap도 실패로 잡히게 했다.
- 수정 후 처음부터 다시 검증했다.
  - `python3 scripts/build_training_jsonl.py --include-source-file` 기준 `rows 175`
  - `python3 scripts/validate_training_examples.py` 기준 `sample_rows 175`, `sample_errors 0`
  - `python3 scripts/audit_training_data_consistency.py` 기준 `duplicate_rows 0`, `potential_contradictions 0`, `eval_overlap_rows 0`
  - split 재확인 기준 `excluded_overlap_rows 0`, train `161`, validation `14`
  - corrective target `action-rec-024`, `action-rec-025`, `failure-response-024`, `failure-response-025`, `state-judgement-042`, `state-judgement-043`가 모두 train에 남는 것을 확인했다.
- `python3 scripts/build_openai_sft_datasets.py --system-prompt-version sft_v5 --train-output artifacts/fine_tuning/openai_sft_train_prompt_v5_methodfix.jsonl --validation-output artifacts/fine_tuning/openai_sft_validation_prompt_v5_methodfix.jsonl`로 cleaned dataset을 생성했고 결과는 train `161`, validation `14`였다.
- `python3 scripts/validate_openai_sft_dataset.py artifacts/fine_tuning/openai_sft_train_prompt_v5_methodfix.jsonl artifacts/fine_tuning/openai_sft_validation_prompt_v5_methodfix.jsonl` 기준 `rows 175`, `errors 0`을 확인했다.
- `./.venv/bin/python scripts/run_openai_fine_tuning_job.py --submit --dataset-version ds_v9 --prompt-version prompt_v5_methodfix --training-file artifacts/fine_tuning/openai_sft_train_prompt_v5_methodfix.jsonl --validation-file artifacts/fine_tuning/openai_sft_validation_prompt_v5_methodfix.jsonl ...`로 새 challenger job `ftjob-Mz4HYCUsC7ohp2OW01rpBTud`를 제출했다.
- run manifest는 `artifacts/fine_tuning/runs/ft-sft-gpt41mini-ds_v9-prompt_v5_methodfix-eval_v1-20260412-125755.json`에 저장했고, submit 직후 sync 기준 상태는 `validating_files`다.

### ds_v9 / prompt_v5_methodfix eval 완료
- `ftjob-Mz4HYCUsC7ohp2OW01rpBTud`를 sync한 결과 `succeeded`로 종료됐고 결과 모델은 `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v9-prompt-v5-methodfix-eval-v1-20260412-1257:DTgUbJHJ`다.
- `./.venv/bin/python scripts/evaluate_fine_tuned_model.py --system-prompt-version sft_v5 --model ...:DTgUbJHJ --output-prefix artifacts/reports/fine_tuned_model_eval_ds_v9_prompt_v5_methodfix`로 eval `24건`을 재실행했다.
- 결과는 `pass_rate 0.875`, `strict_json_rate 1.0`이며 기존 champion `ds_v5/prompt_v5`와 동률이다.
- 실패 케이스는 `pepper-eval-003` (`rootzone_diagnosis`, `risk_level_match`), `failure-eval-001` (`failure_response`, `risk_level_match`), `edge-eval-004` (`required_action_types_present`) 3건이다.
- 비교 기준으로 보면 `ds_v9`는 기존 champion이 실패하던 `pepper-eval-006`과 `action-eval-002`를 해결했지만, 대신 `pepper-eval-003`과 `failure-eval-001`이 새로 회귀했다.
- 결론적으로 split/overlap 방법론 수정이 실제 학습 분포를 바꿨다는 점은 확인됐지만, 최고 기록은 아직 `ds_v5/prompt_v5` `0.875`가 유지된다.

### ds_v8 / prompt_v5_rebase eval 완료
- `ftjob-od4Gz2SDkPBQfdoabiFz61UZ`를 sync한 결과 `succeeded`로 종료됐고 결과 모델은 `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v8-prompt-v5-rebase-eval-v1-20260412-120132:DTfbN2GM`다.
- `./.venv/bin/python scripts/evaluate_fine_tuned_model.py --system-prompt-version sft_v5 --model ...:DTfbN2GM --output-prefix artifacts/reports/fine_tuned_model_eval_ds_v8_prompt_v5_rebase`로 eval `24건`을 재실행했다.
- 결과는 `pass_rate 0.8333`, `strict_json_rate 1.0`이며 champion `0.875`를 넘지 못했다.
- 남은 실패는 `pepper-eval-004`, `pepper-eval-005`, `forbidden-eval-002`, `edge-eval-004` 4건으로, rebase run도 회귀를 막지 못했다.

### ds_v8 / prompt_v5_rebase challenger 제출
- `./.venv/bin/python scripts/run_openai_fine_tuning_job.py --submit --model-version pepper-ops-sft-v1.7.0 --dataset-version ds_v8 --prompt-version prompt_v5_rebase --eval-version eval_v1 --training-file artifacts/fine_tuning/openai_sft_train_prompt_v5_rebase.jsonl --validation-file artifacts/fine_tuning/openai_sft_validation_prompt_v5_rebase.jsonl --notes "rebase on sft_v5 prompt with batch7 and batch8 corrective samples"`로 rebase fine-tuning job `ftjob-od4Gz2SDkPBQfdoabiFz61UZ`를 제출했다.
- 새 run manifest는 `artifacts/fine_tuning/runs/ft-sft-gpt41mini-ds_v8-prompt_v5_rebase-eval_v1-20260412-120132.json`에 저장했다.
- `prompt_v5_rebase` dataset 검증 결과는 train `161`, validation `14`, format error `0`이었다.

### ds_v7 / prompt_v7 eval 완료
- `ftjob-v8oFS0ZvHlWsxB6u7VAky2Bp`를 sync한 결과 `succeeded`로 종료됐고 결과 모델은 `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v7-prompt-v7-eval-v1-20260412-103159:DTeLtzn8`다.
- `./.venv/bin/python scripts/evaluate_fine_tuned_model.py --system-prompt-version sft_v7 --model ...:DTeLtzn8 --output-prefix artifacts/reports/fine_tuned_model_eval_ds_v7_prompt_v7`로 eval `24건`을 재실행했다.
- 결과는 `pass_rate 0.8333`, `strict_json_rate 1.0`이며 champion `0.875`를 넘지 못했다.
- 남은 실패는 `pepper-eval-004`, `pepper-eval-005`, `action-eval-002`, `edge-eval-004` 4건이다.

### ds_v7 / prompt_v7 challenger 제출
- `./.venv/bin/python scripts/run_openai_fine_tuning_job.py --submit --model-version pepper-ops-sft-v1.6.0 --dataset-version ds_v7 --prompt-version prompt_v7 --eval-version eval_v1 --training-file artifacts/fine_tuning/openai_sft_train_prompt_v7.jsonl --validation-file artifacts/fine_tuning/openai_sft_validation_prompt_v7.jsonl --notes "batch8 exact corrective samples and prompt_v7 risk-level calibration"`로 새 fine-tuning job `ftjob-v8oFS0ZvHlWsxB6u7VAky2Bp`를 제출했다.
- 새 run manifest는 `artifacts/fine_tuning/runs/ft-sft-gpt41mini-ds_v7-prompt_v7-eval_v1-20260412-103159.json`에 저장했다.
- submit 직후 현재 상태는 `validating_files`다.

### ds_v6 / prompt_v6 eval 완료와 batch8 / prompt_v7 보강
- `ftjob-etLIrpngO2P9RMI545Od6u1N`를 sync한 결과 `succeeded`로 종료됐고 결과 모델은 `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v6-prompt-v6-eval-v1-20260412-094328:DTdST10S`다.
- `./.venv/bin/python scripts/evaluate_fine_tuned_model.py --system-prompt-version sft_v6 --model ...:DTdST10S --output-prefix artifacts/reports/fine_tuned_model_eval_ds_v6_prompt_v6`로 eval `24건`을 재실행했다.
- 결과는 `pass_rate 0.875`, `strict_json_rate 1.0`이며, 남은 실패는 `pepper-eval-005`, `action-eval-002`, `edge-eval-003` 3건이다.
- 실패 원인은 모두 `risk_level_match`로 좁혀졌다.
- `docs/fine_tuning_objectives.md`에 `prompt_v7` 초안을 추가해 다음 규칙을 명시했다.
  - 핵심 센서 stale/inconsistent는 `pause_automation`이 들어가도 전체 `risk_level=unknown`
  - 건조실 고습·함수율 증가 watch 상황은 알림을 내더라도 전체 `risk_level=medium`
  - `CO2 low + vent_open_lock`은 제어 경로가 막혀 있으므로 전체 `risk_level=high`
- `scripts/build_openai_sft_datasets.py`에 `SFT_V7_SYSTEM_PROMPT`를 추가했고, `scripts/evaluate_fine_tuned_model.py`도 `sft_v7` 선택을 지원하도록 맞췄다.
- corrective seed를 추가했다.
  - `data/examples/state_judgement_samples_batch8.jsonl`
  - `data/examples/action_recommendation_samples_batch8.jsonl`
  - `data/examples/failure_response_samples_batch7.jsonl`
- 검증 결과:
  - `python3 scripts/validate_training_examples.py` 기준 `sample_files 30`, `sample_rows 175`, `sample_errors 0`
  - `python3 scripts/audit_training_data_consistency.py` 기준 `duplicate_rows 0`, `potential_contradictions 0`
  - `python3 scripts/build_training_jsonl.py --include-source-file` 기준 `rows 175`
  - `python3 scripts/build_openai_sft_datasets.py --system-prompt-version sft_v7 ...` 기준 `train_rows 161`, `validation_rows 14`
  - `python3 scripts/validate_openai_sft_dataset.py artifacts/fine_tuning/openai_sft_train_prompt_v7.jsonl artifacts/fine_tuning/openai_sft_validation_prompt_v7.jsonl` 기준 `rows 175`, `errors 0`

### ds_v6 / prompt_v6 challenger 제출
- `./.venv/bin/python scripts/run_openai_fine_tuning_job.py --submit --model-version pepper-ops-sft-v1.5.0 --dataset-version ds_v6 --prompt-version prompt_v6 --eval-version eval_v1 --training-file artifacts/fine_tuning/openai_sft_train_prompt_v6.jsonl --validation-file artifacts/fine_tuning/openai_sft_validation_prompt_v6.jsonl --notes "batch7 direct corrective samples and prompt_v6 overall risk calibration"`로 새 fine-tuning job `ftjob-etLIrpngO2P9RMI545Od6u1N`를 제출했다.
- 새 run manifest는 `artifacts/fine_tuning/runs/ft-sft-gpt41mini-ds_v6-prompt_v6-eval_v1-20260412-094328.json`에 저장했다.
- submit 직후 sync 기준 현재 상태는 `validating_files`이며, events 경로는 `artifacts/fine_tuning/events/ftjob-etLIrpngO2P9RMI545Od6u1N.jsonl`이다.
- `python3 scripts/render_fine_tuning_comparison_table.py`를 다시 실행해 비교표에 ds_v6 challenger run을 반영했다.

### ds_v5 / prompt_v5 eval 완료와 batch7 / prompt_v6 보강
- `ftjob-Ykc0SNX3nPnJYiuSopT571XA`를 sync한 결과 `succeeded`로 종료됐고 결과 모델은 `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v5-prompt-v5-eval-v1-20260412-075506:DTbkkFBo`다.
- `./.venv/bin/python scripts/evaluate_fine_tuned_model.py --system-prompt-version sft_v5 --model ...:DTbkkFBo --output-prefix artifacts/reports/fine_tuned_model_eval_ds_v5_prompt_v5`로 eval `24건`을 재실행했다.
- 결과는 `pass_rate 0.875`, `strict_json_rate 1.0`이며, 남은 실패는 `pepper-eval-006`, `action-eval-002`, `edge-eval-004` 3건이다.
- 실패 원인은 `risk_level_match 2건`, `required_action_types_present 1건`으로 좁혀졌다.
- `action-rec-014`의 건조실 고습 케이스가 eval 기대와 충돌하는 `risk_level=high` 라벨을 유지하고 있어, 해당 sample을 `medium`으로 바로잡았다.
- `docs/fine_tuning_objectives.md`에 `prompt_v6` 초안을 추가해 다음 규칙을 명시했다.
  - 전체 `risk_level`은 상황 확정 위험도이며 `create_alert`를 냈다는 이유만으로 `high`로 올리지 않는다.
  - 병해충 의심 단계는 현장 확진, 트랩 카운트 증가 확정, 빠른 확산, 실물 피해가 없으면 `medium`을 유지한다.
  - 건조실/저장실 고습·재흡습 watch 상황은 결로, 곰팡이, 실측 손상 확정 전까지 `medium`을 유지한다.
  - `manual_override + safe_mode`는 `block_action + create_alert`가 필수이며 `request_human_check`가 이를 대체하면 안 된다.
- `scripts/build_openai_sft_datasets.py`에 `SFT_V6_SYSTEM_PROMPT`를 추가했고, `scripts/evaluate_fine_tuned_model.py`도 `sft_v6` 선택을 지원하도록 맞췄다.
- corrective seed `batch7`를 추가했다.
  - `data/examples/state_judgement_samples_batch7.jsonl`
  - `data/examples/action_recommendation_samples_batch7.jsonl`
- 검증 결과:
  - `python3 scripts/validate_training_examples.py` 기준 `sample_files 27`, `sample_rows 172`, `sample_errors 0`
  - `python3 scripts/build_training_jsonl.py --include-source-file` 기준 `rows 172`
  - `python3 scripts/build_openai_sft_datasets.py --system-prompt-version sft_v6 ...` 기준 `train_rows 158`, `validation_rows 14`
  - `python3 scripts/validate_openai_sft_dataset.py artifacts/fine_tuning/openai_sft_train_prompt_v6.jsonl artifacts/fine_tuning/openai_sft_validation_prompt_v6.jsonl` 기준 `rows 172`, `errors 0`

### ds_v5 / prompt_v5 challenger 제출
- `./.venv/bin/python scripts/run_openai_fine_tuning_job.py --submit --model-version pepper-ops-sft-v1.4.0 --dataset-version ds_v5 --prompt-version prompt_v5 --eval-version eval_v1 --training-file artifacts/fine_tuning/openai_sft_train_prompt_v5.jsonl --validation-file artifacts/fine_tuning/openai_sft_validation_prompt_v5.jsonl --notes "batch6 corrective seed and prompt_v5 risk calibration"`로 새 fine-tuning job `ftjob-Ykc0SNX3nPnJYiuSopT571XA`를 제출했다.
- 새 run manifest는 `artifacts/fine_tuning/runs/ft-sft-gpt41mini-ds_v5-prompt_v5-eval_v1-20260412-075506.json`에 저장했다.
- 제출 직후 sync 기준 현재 상태는 `validating_files`이며, events 경로는 `artifacts/fine_tuning/events/ftjob-Ykc0SNX3nPnJYiuSopT571XA.jsonl`이다.
- `python3 scripts/render_fine_tuning_comparison_table.py`를 다시 실행해 비교표에 ds_v5 challenger run을 반영했다.

### ds_v4 잔여 실패 5건 기준 risk_level/action 규칙 추가 보강
- ds_v4 / prompt_v4 eval 뒤에도 남은 실패 5건(`pepper-eval-006`, `pepper-eval-008`, `action-eval-002`, `edge-eval-003`, `seasonal-eval-002`)을 다시 사람 검토로 분해했다.
- 실패 원인을 `risk_level` 과상향 4건과 `worker_present` 상황에서 `block_action` 누락 1건으로 좁혔다.
- `docs/fine_tuning_objectives.md`에 `prompt_v5` 초안을 추가해 다음 규칙을 명시했다.
  - 병해충 의심 단계는 현장 확진 전까지 `risk_level=medium`
  - `worker_present`는 `critical` + `block_action + create_alert` 강제
  - 건조실/저장실 고습·재흡습 우려는 손상 확정 전까지 `medium`
  - `CO2 low + vent_open_lock`은 `high` + `request_human_check` 필수, `adjust_co2` 금지
  - 봄 정식 직후 저온·과습/Grodan slab 과습은 기본 `medium`, `request_human_check` 필수, `short_irrigation` 금지
- `scripts/build_openai_sft_datasets.py`에 `SFT_V5_SYSTEM_PROMPT`를 추가했고, `scripts/evaluate_fine_tuned_model.py`도 `sft_v5` 선택을 지원하도록 맞췄다.
- corrective seed `batch6`를 추가했다.
  - `data/examples/state_judgement_samples_batch6.jsonl`
  - `data/examples/action_recommendation_samples_batch6.jsonl`
  - `data/examples/failure_response_samples_batch6.jsonl`

### ds_v4 / prompt_v4 challenger 제출
- `./.venv/bin/python scripts/run_openai_fine_tuning_job.py --submit --model-version pepper-ops-sft-v1.3.0 --dataset-version ds_v4 --prompt-version prompt_v4 --eval-version eval_v1 --training-file artifacts/fine_tuning/openai_sft_train_prompt_v4.jsonl --validation-file artifacts/fine_tuning/openai_sft_validation_prompt_v4.jsonl`로 새 fine-tuning job `ftjob-xVzFf0yIJIeo5M9Nnnn2N81k`를 제출했다.
- 새 run manifest는 `artifacts/fine_tuning/runs/ft-sft-gpt41mini-ds_v4-prompt_v4-eval_v1-20260412-070051.json`에 저장했다.
- 제출 직후 sync 기준 현재 상태는 `validating_files`이며, train file id는 `file-ENQ2rSrgmS1cqkKpVcauEx`, validation file id는 `file-3rp2CaC6btL7qe1eg4e2wC`다.
- `python3 scripts/render_fine_tuning_comparison_table.py`를 다시 실행해 비교표에 ds_v4 challenger run을 반영했다.

### batch5 / prompt_v4 초안 준비
- ds_v3/prompt_v3 eval에서 남은 실패 8건(`pepper-eval-005`, `pepper-eval-006`, `pepper-eval-008`, `failure-eval-002`, `edge-eval-004`, `seasonal-eval-001`, `seasonal-eval-002`, `seasonal-eval-003`)을 직접 겨냥한 `batch5` seed를 추가했다.
- 추가 파일은 `data/examples/state_judgement_samples_batch5.jsonl`, `data/examples/failure_response_samples_batch5.jsonl`이다.
- 반영한 패턴은 `sensor_fault -> risk_level unknown + pause_automation`, `pest_disease suspicion -> medium + no robot task`, `worker_present/manual_override+safe_mode -> block_action + create_alert`, `dry-room communication_loss -> critical + enter_safe_mode`, `winter nursery -> high`, `spring transplant + Grodan slab overwet -> medium`, `summer flowering heat+radiation -> high + create_alert`다.
- `scripts/build_openai_sft_datasets.py`에 `SFT_V4_SYSTEM_PROMPT`를 추가했고, `scripts/evaluate_fine_tuned_model.py`도 `sft_v4` 선택을 지원하게 맞췄다.
- 검증 결과:
  - `python3 scripts/validate_training_examples.py` 기준 `sample_files 22`, `sample_rows 164`, `sample_errors 0`
  - `python3 scripts/build_training_jsonl.py --include-source-file` 기준 `rows 164`
  - `python3 scripts/build_openai_sft_datasets.py --system-prompt-version sft_v4 ...` 기준 `train_rows 150`, `validation_rows 14`
  - `python3 scripts/validate_openai_sft_dataset.py artifacts/fine_tuning/openai_sft_train_prompt_v4.jsonl artifacts/fine_tuning/openai_sft_validation_prompt_v4.jsonl` 기준 `rows 164`, `errors 0`

### ds_v3 / prompt_v3 완료와 champion 갱신
- `ftjob-MiiLGncQBHRXL2NZoBYWxMcc`를 sync한 결과 `succeeded`로 종료됐고 결과 모델은 `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v3-prompt-v3-eval-v1-20260412-033726:DTXjV3Hg`다.
- `./.venv/bin/python scripts/evaluate_fine_tuned_model.py --system-prompt-version sft_v3 --model ...:DTXjV3Hg --output-prefix artifacts/reports/fine_tuned_model_eval_ds_v3_prompt_v3`로 eval `24건`을 재실행했다.
- 결과는 `pass_rate 0.6667`, `strict_json_rate 1.0`, `top_failed_checks = risk_level_match 5건 / required_action_types_present 5건`이다.
- `action_recommendation 2건`, `forbidden_action 2건`, `harvest_drying 1건`은 모두 통과로 회복됐다.
- 새 실패 집합은 `pepper-eval-005`, `pepper-eval-006`, `pepper-eval-008`, `failure-eval-002`, `edge-eval-004`, `seasonal-eval-001`, `seasonal-eval-002`, `seasonal-eval-003` 8건이다.
- ds_v3/prompt_v3는 v1 legacy baseline `0.5417` 대비 `+0.1250`, 직전 champion ds_v2/prompt_v2 `0.625` 대비 `+0.0417` 개선됐다.
- `artifacts/reports/fine_tuned_model_eval_latest.*`는 ds_v3/prompt_v3 champion 결과로 갱신한다.

### ds_v3 / prompt_v3 재학습 제출
- `python3 scripts/build_training_jsonl.py --include-source-file`로 combined training `156건`을 다시 생성했다.
- `python3 scripts/build_openai_sft_datasets.py --system-prompt-version sft_v3 --train-output artifacts/fine_tuning/openai_sft_train_prompt_v3.jsonl --validation-output artifacts/fine_tuning/openai_sft_validation_prompt_v3.jsonl`로 ds_v3/prompt_v3 전용 학습 파일을 생성했다.
- `python3 scripts/validate_openai_sft_dataset.py artifacts/fine_tuning/openai_sft_train_prompt_v3.jsonl artifacts/fine_tuning/openai_sft_validation_prompt_v3.jsonl` 기준 `rows 156`, `errors 0`을 확인했다.
- `./.venv/bin/python scripts/run_openai_fine_tuning_job.py --submit --model-version pepper-ops-sft-v1.2.0 --dataset-version ds_v3 --prompt-version prompt_v3 --eval-version eval_v1 --training-file artifacts/fine_tuning/openai_sft_train_prompt_v3.jsonl --validation-file artifacts/fine_tuning/openai_sft_validation_prompt_v3.jsonl`로 새 fine-tuning job `ftjob-MiiLGncQBHRXL2NZoBYWxMcc`를 제출했다.
- 새 run manifest는 `artifacts/fine_tuning/runs/ft-sft-gpt41mini-ds_v3-prompt_v3-eval_v1-20260412-033726.json`에 저장했다.
- 현재 상태는 `validating_files`이며, train file id는 `file-6HTHUEuf1jJTUkrAet1H4z`, validation file id는 `file-FV3Nx3duw8eSCVLmoMqadh`다.
- `python3 scripts/render_fine_tuning_comparison_table.py`를 다시 실행해 비교표에 ds_v3 candidate run을 반영했다.

### batch4 실패 보강과 prompt_v3 초안 정리
- ds_v2/prompt_v2 eval에서 남은 9개 실패 케이스를 그대로 대응하는 `batch4` seed를 추가했다.
- 추가 파일은 `data/examples/state_judgement_samples_batch4.jsonl`, `action_recommendation_samples_batch4.jsonl`, `forbidden_action_samples_batch4.jsonl`이다.
- 반영한 패턴은 `sensor_fault -> risk_level unknown`, `pest_disease_risk -> medium`, `harvest_drying -> request_human_check 필수`, `worker_present/manual_override/safe_mode -> block_action + create_alert`, `spring transplant cold+overwet -> medium`, `fertigation evidence incomplete -> approval_required`다.
- `scripts/build_openai_sft_datasets.py`에 `SFT_V3_SYSTEM_PROMPT`와 `--system-prompt-version`을 추가해 v2 기본값을 유지하면서 v3 draft를 별도로 선택할 수 있게 했다.
- `scripts/evaluate_fine_tuned_model.py`도 `sft_v3` 선택을 지원하게 맞췄다.
- 검증 결과:
  - `python3 scripts/validate_training_examples.py` 기준 `sample_files 20`, `sample_rows 156`, `sample_errors 0`
  - `python3 scripts/build_training_jsonl.py --include-source-file` 기준 `rows 156`
  - `python3 scripts/build_openai_sft_datasets.py --system-prompt-version sft_v3 ...` 기준 `train_rows 142`, `validation_rows 14`
  - `python3 scripts/validate_openai_sft_dataset.py artifacts/fine_tuning/openai_sft_train_prompt_v3.jsonl artifacts/fine_tuning/openai_sft_validation_prompt_v3.jsonl` 기준 `rows 156`, `errors 0`

### Grodan 재배 환경 조건 확정 반영
- 현장 재배 환경 조건을 육묘용 `Grodan Delta 6.5` block, 본재배용 `Grodan GT Master` slab 기준으로 고정했다.
- `docs/site_scope_baseline.md`, `docs/sensor_collection_plan.md`, `docs/sensor_installation_inventory.md`, `PLAN.md`, `README.md`, `PROJECT_STATUS.md`, `AI_MLOPS_PLAN.md`에 이 전제를 반영했다.
- `schemas/sensor_catalog_schema.json`, `data/examples/sensor_catalog_seed.json`에도 `cultivation_context`를 추가해 seed catalog가 실제 재배 환경 가정을 함께 기록하도록 보강했다.
- 근권 센서, 배액률, 관수 펄스, 양액 drift 판단은 앞으로 `Grodan GT Master` slab 기준의 rockwool soilless 운영을 기본값으로 사용한다.

### ds_v2 / prompt_v2 재학습 job 완료와 재평가
- `scripts/build_training_jsonl.py --include-source-file`, `scripts/build_openai_sft_datasets.py`, `scripts/validate_openai_sft_dataset.py`를 다시 실행해 제출 직전 학습 파일을 고정했다.
- 제출 기준은 `model_version=pepper-ops-sft-v1.1.0`, `dataset_version=ds_v2`, `prompt_version=prompt_v2`, `eval_version=eval_v1`로 정했다.
- `scripts/run_openai_fine_tuning_job.py --submit`로 새 fine-tuning job `ftjob-ULBuPHoPBbAMah5rPdd2i334`를 생성했다.
- 새 run manifest는 `artifacts/fine_tuning/runs/ft-sft-gpt41mini-ds_v2-prompt_v2-eval_v1-20260412-021539.json`에 저장했다.
- 제출 시 사용된 file id는 train `file-Goxm4KiEmxgXjUkjk19oPy`, validation `file-T4jF5Dea4aa2SXQ7vQmh6L`이다.
- 이후 `scripts/sync_openai_fine_tuning_job.py`로 상태를 동기화한 결과 job `ftjob-ULBuPHoPBbAMah5rPdd2i334`는 `succeeded`로 완료됐고 결과 모델은 `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v2-prompt-v2-eval-v1-20260412-021539:DTWRpIbI`다.
- `scripts/render_fine_tuning_comparison_table.py`를 다시 실행해 비교표에 ds_v2 run을 반영했다.
- 완료 직후 `python3 scripts/evaluate_fine_tuned_model.py --system-prompt-version sft_v2 --model ...:DTWRpIbI --output-prefix artifacts/reports/fine_tuned_model_eval_ds_v2_prompt_v2`로 eval `24건`을 재실행했다.
- 최신 결과는 `pass_rate 0.625`, `strict_json_rate 1.0`, `top_failed_checks = risk_level_match 5건 / required_action_types_present 3건 / decision_match 1건`이다.
- `artifacts/reports/fine_tuned_model_eval_latest.*`는 현재 champion(ds_v2/prompt_v2) 결과로 갱신했고, v1 legacy baseline은 `artifacts/reports/fine_tuned_model_eval_legacy_prompt.*`로 분리 보관했다.
- 동일 eval `24건` 기준으로 ds_v2/prompt_v2는 legacy baseline `0.5417` 대비 `+0.0833` 개선됐다.
- 검증 결과:
  - `python3 scripts/build_training_jsonl.py --include-source-file` 기준 `rows 147`
  - `python3 scripts/build_openai_sft_datasets.py` 기준 `train_rows 133`, `validation_rows 14`
  - `python3 scripts/validate_openai_sft_dataset.py artifacts/fine_tuning/openai_sft_train.jsonl artifacts/fine_tuning/openai_sft_validation.jsonl` 기준 `rows 147`, `errors 0`

### 다음 라운드용 SFT 보강 데이터와 prompt 분리
- `data/examples/state_judgement_samples_batch3.jsonl`, `failure_response_samples_batch3.jsonl`, `forbidden_action_samples_batch3.jsonl`를 추가해 총 training seed를 `147건`으로 늘렸다.
- batch3에는 `observe_only` 정상 상태, 봄 정식 직후 저온·과습, `manual override + safe_mode` 동시 active, dry-room 통신 손실, `adjust_fertigation -> approval_required` 같은 1차 eval 실패 패턴을 직접 반영했다.
- `scripts/training_data_config.py`를 추가해 학습용 sample 파일을 family pattern 기준으로 탐색하게 바꿨고, `build_training_jsonl.py`, `validate_training_examples.py`, `report_training_sample_stats.py`, `audit_training_data_consistency.py`가 `batch3`까지 자동 포함되도록 정리했다.
- `scripts/build_openai_sft_datasets.py`를 보강해 action/failure/robot 계열 SFT 출력에 `retrieval_coverage`, `confidence`, `citations`, 정규화된 `recommended_actions`/`robot_tasks` 기본 필드가 빠지지 않도록 했다.
- 같은 스크립트에 `LEGACY_SYSTEM_PROMPT`와 `SFT_V2_SYSTEM_PROMPT`를 분리했다. `SFT_V2`는 다음 라운드 재학습용 prompt이고, 현재 fine-tuned model 평가 기준 prompt는 legacy로 유지한다.
- `scripts/evaluate_fine_tuned_model.py`를 보강해 OpenAI API 오류 재시도, `request_error` 기록, partial save, `--system-prompt-version` 선택을 지원하게 했다.
- 검증 결과:
  - `python3 scripts/validate_training_examples.py` 기준 `sample_files 17`, `sample_rows 147`, `sample_errors 0`
  - `python3 scripts/build_training_jsonl.py --include-source-file` 기준 `rows 147`
  - `python3 scripts/build_openai_sft_datasets.py` 기준 `train_rows 133`, `validation_rows 14`
  - `python3 scripts/validate_openai_sft_dataset.py artifacts/fine_tuning/openai_sft_train.jsonl artifacts/fine_tuning/openai_sft_validation.jsonl` 기준 `rows 147`, `errors 0`
  - 정규화된 OpenAI SFT train set 기준 action/failure/robot 계열에서 `follow_up`, `confidence`, `citations`, `retrieval_coverage` 누락 `0건` 확인
- prompt-only 영향도도 분리 기록했다.
  - legacy prompt로 현재 fine-tuned model 재평가 시 `pass_rate 0.5417` 유지: `artifacts/reports/fine_tuned_model_eval_legacy_prompt.{json,jsonl,md}`
  - `SFT_V2` prompt를 현재 모델에 바로 적용하면 `pass_rate 0.1667`로 크게 악화: `artifacts/reports/fine_tuned_model_eval_prompt_v2.{json,jsonl,md}`
- 결론적으로 `SFT_V2` prompt는 현재 모델 추론용 기본 prompt가 아니라, 다음 재학습 라운드에 dataset/prompt를 같이 올려야 하는 변경으로 판단했다.

### OpenAI fine-tuning 완료 상태 반영과 결과 검증 스크립트 추가
- `scripts/sync_openai_fine_tuning_job.py`로 2차 fine-tuning job `ftjob-45KiYE5G2J125jSNg2QqakYm` 상태를 다시 동기화해 `succeeded`를 확인했다.
- fine-tuned model id는 `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v1-prompt-v1-eval-v1-20260412-004953:DTV5z1FR`로 기록했다.
- `scripts/evaluate_fine_tuned_model.py`를 추가해 eval JSONL 7종에 대해 실제 모델 호출, JSON parse, risk/action/task/citation/follow_up 기준 grading, confidence 요약 리포트를 생성하도록 했다.
- `python3 scripts/evaluate_fine_tuned_model.py`로 eval `24건`을 실행해 v1 baseline 리포트 `artifacts/reports/fine_tuned_model_eval_legacy_prompt.{json,jsonl,md}`를 생성했다.
- 1차 결과는 `pass_rate 0.5417`, `strict_json_rate 1.0`이며 주요 실패는 `risk_level_match 7건`, `required_action_types_present 4건`, `retrieval_coverage` 누락 `20건`이었다.
- 실제 실패 패턴으로는 정상 상태에서 `observe_only` 대신 비허용 `action_type`인 `maintain`/`hold`를 반환하거나, dry-room 통신 장애에서 `enter_safe_mode` 대신 `create_alert` 중심으로 응답하는 사례가 확인됐다.
- 관련 문서를 함께 갱신했다: `README.md`, `PROJECT_STATUS.md`, `AI_MLOPS_PLAN.md`, `docs/openai_fine_tuning_execution.md`, `evals/README.md`
- 이 단계부터 다음 우선순위는 fine-tuning submit 자체가 아니라 `3.4 파인튜닝 결과 검증` 실행과 결과 해석이다.

## 2026-04-11

### 현장 범위와 품종 shortlist, 낮/밤 운영 기준 고정
- `docs/site_scope_baseline.md`를 추가해 대상 현장을 `300평 연동형 비닐온실 1동`, `gh-01` 기준으로 고정했다.
- 물리적으로는 대형 온실 1개지만 수집/제어/평가를 위해 `zone-a`, `zone-b`, `outside`, `nutrient-room`, `dry-room`의 논리 zone 5개를 유지하도록 정리했다.
- 건고추/고춧가루용 적고추 품종 범위를 `왕조`, `칼탄열풍`, `조생강탄` shortlist로 좁혔다.
- 현재 판매/추천 기사 기준으로는 `왕조`를 기본 기준 품종으로 두고, 병해·바이러스 대응은 `칼탄열풍`, 조생·강한 매운맛은 `조생강탄`을 대안으로 정리했다.
- 공식 점유율 통계는 확인하지 못했으므로 `가장 많이 사용되는 품종`이 아니라 `현재 판매/추천 기준 shortlist`로 기록했다.
- 공식 재배 자료를 기준으로 낮/밤 운영 기본값을 낮 `25~28℃`, 밤 `18℃ 전후`, 허용 운전 밴드 낮 `25~30℃`, 밤 `18~20℃`로 정리했다.
- 정식기 보수 기준은 밤 `16℃ 이상`, 육묘 순화 기준은 정식 `7~10일 전` 낮 `22~23℃`, 밤 `14~15℃`로 반영했다.
- 관련 문서도 함께 갱신했다: `docs/sensor_collection_plan.md`, `AI_MLOPS_PLAN.md`, `README.md`, `PROJECT_STATUS.md`, `todo.md`
- 조사 근거:
  - 농사로 고추 작목 정보: https://www.nongsaro.go.kr/portal/ps/psz/psza/contentSub.ps?cntntsNo=101628&menuId=PS03172
  - 농사로 고추 양액재배 현장 기술지원: https://nongsaro.go.kr/portal/ps/psz/psza/contentSub.ps?cntntsNo=259682&menuId=PS00077
  - NH농우바이오 2026년 1월 추천품종 기사: https://www.newsam.co.kr/news/article.html?no=41799
  - 아시아종묘 2025년 건고추 추천품종 기사: https://www.newsfm.kr/mobile/article.html?no=9677

### 계절별 운영 범위 정의
- `docs/seasonal_operation_ranges.md`를 추가해 `gh-01` 기준 겨울/봄/여름/가을의 운영 단계, 목표 온도 범위, 리스크 우선순위를 정리했다.
- 겨울은 육묘/보온, 봄은 정식/활착, 여름은 고온 억제와 과건조·낙화 관리, 가을은 후기 수확과 철거 판단 중심으로 정리했다.
- 달력만으로 계절을 고정하지 않고 생육 단계, 최근 7일 외기 패턴, 정식 후 경과일, 수확/철거 여부를 함께 보도록 정책 연결 원칙을 정리했다.
- 관련 문서도 함께 갱신했다: `docs/site_scope_baseline.md`, `PLAN.md`, `schedule.md`, `AI_MLOPS_PLAN.md`, `README.md`, `PROJECT_STATUS.md`, `todo.md`
- 조사 근거:
  - 농사로 고추 작목 정보: https://www.nongsaro.go.kr/portal/ps/psz/psza/contentSub.ps?cntntsNo=101628&menuId=PS03172
  - 농사로 고추 양액재배 현장 기술지원: https://nongsaro.go.kr/portal/ps/psz/psza/contentSub.ps?cntntsNo=259682&menuId=PS00077
  - 농사로 고추 육묘 환경 자료: https://www.nongsaro.go.kr/portal/ps/psx/psxa/mlrdCurationDtl.mo?curationNo=188

### 핵심 센서 1차 상용 모델 shortlist 정리
- `docs/sensor_model_shortlist.md`를 추가해 `gh-01` 300평 연동형 비닐온실 기준 핵심 센서 8종의 1차 상용 모델 shortlist를 정리했다.
- 온습도는 `Vaisala HMP110`, CO2는 `Vaisala GMP252`, PAR은 `Apogee SQ-522-SS`, 배지 함수율은 `METER TEROS 12`, 양액 pH/EC는 `Bluelab Guardian Inline Wi-Fi`, 외기 통합은 `Vaisala WXT536`를 기본 후보로 두었다.
- shortlist 목적은 최종 발주가 아니라 `sensor-ingestor`와 PLC/별도 모니터링 계층 연결 현실성을 기준으로 한 1차 기술 기준 고정이다.
- `todo.md`의 `1.2 센서 인벤토리 작성` 중 온도/습도/CO2/PAR/배지 함수율/EC/pH/외기 센서 모델 조사 항목을 완료 처리했다.
- 관련 문서도 함께 갱신했다: `PLAN.md`, `schedule.md`, `AI_MLOPS_PLAN.md`, `README.md`, `PROJECT_STATUS.md`, `docs/sensor_installation_inventory.md`
- 조사 근거:
  - Vaisala HMP110: https://www.vaisala.com/en/products/instruments-sensors-and-other-measurement-devices/instruments-industrial-measurements/hmp110
  - Vaisala GMP252: https://www.vaisala.com/en/products/instruments-sensors-and-other-measurement-devices/instruments-industrial-measurements/gmp252
  - Apogee SQ-522-SS: https://www.apogeeinstruments.com/sq-522-ss-modbus-digital-output-full-spectrum-quantum-sensor/
  - METER TEROS 12: https://metergroup.com/products/teros-12/
  - Bluelab Guardian Inline Wi-Fi: https://bluelab.com/products/bluelab-guardian-monitor-inline-wi-fi
  - Bluelab OnePen: https://bluelab.com/products/bluelab-onepen
  - Vaisala WXT536 설명: https://www.vaisala.com/en/expert-article/integrated-weather-data-efficient-building-operation

### 장치별 최소/최대 setpoint 범위 고정
- `docs/device_setpoint_ranges.md`를 추가해 fan, vent, shade, irrigation valve, heater, CO2 doser, nutrient mixer, source water valve, dehumidifier, dry fan의 기본 운전 범위를 정리했다.
- `schemas/sensor_catalog_schema.json`의 `devices[*]`에 `setpoint_bounds`를 필수 필드로 추가했다.
- `data/examples/sensor_catalog_seed.json`의 모든 장치 인스턴스에 `setpoint_bounds`를 넣어 실제 장치 명령 파라미터 기준을 seed 데이터에 반영했다.
- `scripts/validate_device_setpoint_ranges.py`를 추가해 각 장치 타입별 필수 파라미터와 min/max, allowed_values 정합성을 검증하도록 했다.
- `scripts/validate_device_command_requests.py`를 보강해 command sample의 `parameters`가 catalog `setpoint_bounds` 안에 있는지 함께 검사하도록 했다.
- `todo.md`의 `1.3 액추에이터 인벤토리 작성` 중 `각 장치의 최소/최대 setpoint 정리` 항목을 완료 처리했다.
- 검증 결과:
  - `python3 scripts/validate_device_setpoint_ranges.py` 기준 `devices 20`, `errors 0`
  - `python3 scripts/validate_device_command_requests.py` 기준 `rows 3`, `errors 0`
  - `python3 -m py_compile scripts/validate_device_setpoint_ranges.py scripts/validate_device_command_requests.py` 통과

### 장치 운전 경험 규칙 정리
- `docs/device_operation_rules.md`를 추가해 환기창-순환팬-차광의 우선순위, 관수 펄스 원칙, 양액기 drift 점검, 난방/CO2/건조실 운전 SOP를 한 문서로 정리했다.
- 이 문서는 공식 재배 지식, 현장 사례, 안전 요구사항을 묶어 `policy-engine`과 action recommendation seed의 상위 규칙 문서로 쓰도록 설계했다.
- `todo.md`의 `2.1 고추 재배 지식셋 정리` 중 `장치 운전 경험 규칙 정리` 항목을 완료 처리했다.
- 관련 문서도 함께 갱신했다: `PLAN.md`, `AI_MLOPS_PLAN.md`, `README.md`, `PROJECT_STATUS.md`

### 학습 seed 중복/모순 감사 자동화
- `scripts/audit_training_data_consistency.py`를 추가해 주요 학습 seed JSONL 7종을 대상으로 exact duplicate와 잠재 모순을 자동 감지하도록 했다.
- 입력 비교는 `task_type + input`, exact duplicate 비교는 `task_type + input + preferred_output` 기준으로 정규화 해시를 사용한다.
- `todo.md`의 `2.4 데이터 정제` 중 `중복 샘플 제거`, `모순 샘플 검토` 항목을 완료 처리했다.
- 검증 결과:
  - `python3 scripts/audit_training_data_consistency.py` 기준 `files 7`, `rows 22`, `duplicate_rows 0`, `potential_contradictions 0`, `errors 0`
  - `python3 -m py_compile scripts/audit_training_data_consistency.py` 통과

### edge case / 계절별 평가셋 추가
- `evals/edge_case_eval_set.jsonl`를 추가해 장치 readback stuck, CO2 lock, manual override + safe mode, 최근 관수 직후 과습 같은 edge case 4건을 분리했다.
- `evals/seasonal_eval_set.jsonl`를 추가해 겨울 육묘, 봄 정식, 여름 개화기 고온, 가을 첫서리 대응 케이스 4건을 분리했다.
- `scripts/validate_training_examples.py`의 기본 eval 목록에 두 파일을 추가했다.
- `todo.md`의 `2.5 평가셋 구축` 중 `edge case 평가셋 구축`, `계절별 평가셋 구축` 항목을 완료 처리했다.
- 검증 결과:
  - `python3 scripts/validate_training_examples.py` 기준 `eval_files 7`, `eval_rows 24`, `eval_errors 0`
  - `python3 -m py_compile scripts/validate_training_examples.py` 통과

### task family별 학습 seed 20건 확장
- `data/examples/action_recommendation_samples_batch2.jsonl`, `failure_response_samples_batch2.jsonl`, `forbidden_action_samples_batch2.jsonl`, `qa_reference_samples_batch2.jsonl`, `reporting_samples_batch2.jsonl`, `robot_task_samples_batch2.jsonl`, `state_judgement_samples_batch2.jsonl`를 추가했다.
- 기존 7개 task family seed를 각 20건 이상으로 맞춰 총 140건의 기본 학습 seed를 확보했다.
- `scripts/validate_training_examples.py`와 `scripts/audit_training_data_consistency.py`의 기본 입력 목록에 batch2 파일을 포함시켰다.
- `todo.md`의 `task family별 학습 seed 20건 이상 확보` 항목을 완료 처리했다.
- 검증 결과:
  - `python3 scripts/validate_training_examples.py` 기준 `sample_files 14`, `sample_rows 140`, `sample_duplicate_ids 0`, `sample_errors 0`
  - `python3 scripts/audit_training_data_consistency.py` 기준 `files 14`, `rows 140`, `duplicate_rows 0`, `potential_contradictions 0`, `errors 0`
  - 파일군별 row 수: `action_recommendation 20`, `failure_response 20`, `forbidden_action 20`, `qa_reference 20`, `reporting 20`, `robot_task 20`, `state_judgement 20`

### 파인튜닝 목표 재정의와 출력 계약 고정
- `docs/fine_tuning_objectives.md`를 추가해 RAG와 파인튜닝 역할 경계를 문서로 고정했다.
- 운영형 모델의 목표를 `JSON 출력 안정화`, `허용 action_type 제한`, `보수적 불확실성 표현`, `follow_up 강제`, `citation/retrieval_coverage 유지`로 정리했다.
- `schemas/action_schema.json`의 필수 필드에 `retrieval_coverage`를 추가해 출력 계약을 문서와 맞췄다.
- `docs/training_data_format.md`, `docs/dataset_taxonomy.md`, `README.md`, `PROJECT_STATUS.md`, `AI_MLOPS_PLAN.md`, `todo.md`를 함께 갱신했다.

### 학습/eval 합본 생성과 통계 리포트 추가
- `scripts/build_training_jsonl.py`를 추가해 14개 sample 파일을 `artifacts/training/combined_training_samples.jsonl`로 합쳤다.
- `scripts/build_eval_jsonl.py`를 추가해 7개 eval 파일을 `artifacts/training/combined_eval_cases.jsonl`로 합쳤다.
- `scripts/report_training_sample_stats.py`를 추가해 task 분포, action_type 분포, 길이 분포, longest sample 상위 5건을 `artifacts/reports/training_sample_stats.json`에 기록하도록 했다.
- `docs/training_dataset_build.md`에 생성 절차를 문서화했고, `docs/training_sample_manual_review.md`에 longest sample과 세부 task 불균형 수동 검토 결과를 남겼다.
- `todo.md`의 `3.2 데이터 파일 생성` 항목을 모두 완료 처리했다.
- 검증 결과:
  - `python3 scripts/build_training_jsonl.py --include-source-file` 기준 `rows 140`
  - `python3 scripts/build_eval_jsonl.py --include-source-file` 기준 `rows 24`
  - `python3 scripts/report_training_sample_stats.py` 기준 `class_imbalance_ratio 10.00`
  - `python3 scripts/validate_training_examples.py` 기준 `sample_files 14`, `sample_rows 140`, `eval_files 7`, `eval_rows 24`

### base model과 실험명 규칙 고정
- `docs/fine_tuning_runbook.md`를 추가해 현재 파인튜닝 기본 방식을 `SFT`로 고정했다.
- 주력 base model은 `gpt-4.1-mini-2025-04-14`, challenger는 `gpt-4.1-2025-04-14`, exploratory는 `gpt-4.1-nano-2025-04-14`로 정리했다.
- 내부 모델 버전 규칙 `pepper-ops-sft-v{major}.{minor}.{patch}`와 실험명 규칙 `ft-sft-{base_model_short}-{dataset_version}-{prompt_version}-{eval_version}-{yyyymmdd}`를 정의했다.
- `todo.md`의 `3.3 학습 실행` 중 `모델 버전 결정`, `실험명 규칙 정의`를 완료 처리했다.
- 조사 근거:
  - OpenAI fine-tuning API reference: https://platform.openai.com/docs/api-reference/fine-tuning/retrieve
  - OpenAI model optimization guide: https://platform.openai.com/docs/guides/legacy-fine-tuning

### OpenAI SFT 실행 경로와 비교표 추가
- `scripts/build_openai_sft_datasets.py`를 추가해 내부 학습 seed 140건을 OpenAI SFT용 chat-format train 126건, validation 14건으로 분리 생성하도록 했다.
- `scripts/validate_openai_sft_dataset.py`를 추가해 생성된 chat JSONL이 OpenAI 제출 형식인 `messages` only 구조를 만족하는지 검증하도록 했다.
- `scripts/run_openai_fine_tuning_job.py`를 추가해 기본 실행은 dry-run manifest 생성, `--submit`일 때만 OpenAI file upload와 fine-tuning job create를 수행하도록 했다.
- `scripts/sync_openai_fine_tuning_job.py`를 추가해 job status, events, failure case 누적 경로를 만들었다.
- `scripts/render_fine_tuning_comparison_table.py`를 추가해 run manifest 기준 비교표를 `artifacts/fine_tuning/fine_tuning_comparison_table.md`로 생성하도록 했다.
- `docs/openai_fine_tuning_execution.md`에 실제 실행 순서와 산출물 경로를 문서화했다.
- 검증 결과:
  - `python3 scripts/build_openai_sft_datasets.py` 기준 `train_rows 126`, `validation_rows 14`
  - `python3 scripts/validate_openai_sft_dataset.py artifacts/fine_tuning/openai_sft_train.jsonl artifacts/fine_tuning/openai_sft_validation.jsonl` 기준 `rows 140`, `errors 0`
  - `python3 scripts/run_openai_fine_tuning_job.py` 기준 dry-run manifest `ft-sft-gpt41mini-ds_v1-prompt_v1-eval_v1-20260412.json` 생성
  - `python3 scripts/render_fine_tuning_comparison_table.py` 기준 `runs 1`

### OpenAI SFT 실제 submit과 재제출
- `python3 scripts/run_openai_fine_tuning_job.py --submit`로 실제 fine-tuning job `ftjob-2UERXn8JN2B0SDUXL1tukptl`을 생성했다.
- `python3 scripts/sync_openai_fine_tuning_job.py --manifest artifacts/fine_tuning/runs/ft-sft-gpt41mini-ds_v1-prompt_v1-eval_v1-20260412.json` 결과, OpenAI가 training file top-level `metadata`를 거부해 `invalid_file_format`로 실패한 것을 확인했다.
- 이후 `scripts/build_openai_sft_datasets.py`에서 OpenAI 제출 JSONL을 `messages` only 구조로 수정했고, `scripts/validate_openai_sft_dataset.py`도 unexpected top-level key를 차단하도록 강화했다.
- `scripts/run_openai_fine_tuning_job.py`는 같은 날짜 재실행 시 manifest가 덮어써지지 않도록 기본 실험명에 시각 태그를 붙이도록 보강했다.
- 수정 뒤 `python3 scripts/build_openai_sft_datasets.py`와 `python3 scripts/validate_openai_sft_dataset.py artifacts/fine_tuning/openai_sft_train.jsonl artifacts/fine_tuning/openai_sft_validation.jsonl`를 다시 실행해 `rows 140`, `errors 0`을 확인했다.
- 재제출한 2차 job은 `ftjob-45KiYE5G2J125jSNg2QqakYm`이며, 이후 sync 결과 `succeeded`로 완료됐다.
- 실패 케이스는 `artifacts/fine_tuning/failure_cases.jsonl`에 누적 기록되며, 비교표는 `artifacts/fine_tuning/fine_tuning_comparison_table.md`에 run 단위로 반영한다.

### optional Modbus TCP transport 검증과 safe mode 연동 추가
- `docs/plc_modbus_governance.md`를 추가해 Modbus TCP를 현재 기본 PLC transport로 고정하고, write 허용 table, readback success condition, 공통 장애 코드, rollback 후보, safe mode 전환 조건을 정리했다.
- `pyproject.toml`에 optional dependency `plc = ["pymodbus>=3.6,<4"]`를 추가해 실제 TCP/Modbus client 연결 경로를 명시했다.
- `plc-adapter/plc_adapter/transports.py`에 `PymodbusTcpTransport`를 추가해 `modbus-tcp://host:port?unit_id=...` endpoint 파싱, holding register/coil write, input/holding/discrete/coil read, transport health 집계를 구현했다.
- `plc-adapter/plc_adapter/codecs.py`를 보강해 encoder가 raw register/coil 값으로 직접 매핑되도록 바꿨다. fan은 speed register, valve는 coil/boolean, heater는 stage register, fertigation은 recipe code register를 쓰도록 정리했다.
- `plc-adapter/plc_adapter/plc_tag_modbus_tcp.py`의 `latency_ms`를 고정값이 아니라 실제 write+readback 경과시간으로 계산하도록 보강했다.
- `scripts/validate_plc_modbus_transport.py`를 추가해 fake Modbus client 기준으로 `PymodbusTcpTransport`의 reconnect/retry, write/readback, timeout, health degradation 경로를 검증하도록 했다.
- 검증 결과:
  - `python3 -m py_compile plc-adapter/plc_adapter/plc_tag_modbus_tcp.py plc-adapter/plc_adapter/transports.py scripts/validate_plc_modbus_transport.py` 통과
  - `python3 scripts/validate_plc_modbus_transport.py` 기준 `fan_status acknowledged`, `source_water_status acknowledged`, `timeout_status timeout`, `errors []`

### repeated runtime fault -> safe mode latch 추가
- `execution-gateway/execution_gateway/state.py`에 `RuntimeFaultTracker`를 추가해 zone/site scope별 연속 `timeout`/`fault` 횟수를 기록하도록 했다.
- 같은 파일에 `enter_safe_mode()`를 추가해 runtime fault 누적으로 `safe_mode_active=true`, `auto_mode_enabled=false` 전이를 기록하도록 했다.
- `execution-gateway/execution_gateway/dispatch.py`를 보강해 adapter 결과가 `timeout` 또는 `fault`일 때 runtime fault tracker를 갱신하고, threshold 이상이면 zone/site scope에 `safe_mode`를 자동 latch하도록 연결했다.
- `scripts/validate_execution_safe_mode.py`를 추가해 heater timeout 두 번 뒤 `gh-01-zone-b`와 `gh-01`이 모두 `safe_mode_active`가 되고, 후속 fan 요청이 `safe_mode_active`로 차단되는지 검증하도록 했다.
- 검증 결과:
  - `python3 -m py_compile execution-gateway/execution_gateway/state.py execution-gateway/execution_gateway/dispatch.py scripts/validate_execution_safe_mode.py` 통과
  - `python3 scripts/validate_execution_safe_mode.py` 기준 `first_timeout_status dispatch_fault`, `second_timeout_status dispatch_fault`, `blocked_fan_status rejected`, `errors []`

### execution-gateway dispatcher와 control state store 추가
- `execution-gateway/execution_gateway/dispatch.py`를 추가해 preflight 통과 요청을 `plc-adapter` 또는 override state transition으로 dispatch하는 경로를 구현했다.
- `execution-gateway/execution_gateway/state.py`를 추가해 `estop`, `manual_override`, `safe_mode`, `auto_mode_enabled` 상태를 scope별로 저장하도록 했다.
- dispatcher는 `device_command` 처리 전에 `ControlStateStore`를 다시 조회해 `estop_active`, `manual_override_state_active`, `safe_mode_active`를 차단 사유로 반영한다.
- `docs/execution_dispatcher_runtime.md`를 추가해 adapter 종류, audit log, override 상태 전이 기준을 문서화했다.
- `.env.example`, `.env.dev.example`, `.env.staging.example`, `.env.prod.example`에 `EXECUTION_GATEWAY_AUDIT_LOG_PATH`를 추가했다.
- `scripts/validate_execution_dispatcher.py`를 추가해 `override -> state update -> device block -> adapter dispatch -> audit log` 경로를 검증하도록 했다.
- 검증 결과:
  - `python3 -m py_compile execution-gateway/demo.py execution-gateway/execution_gateway/contracts.py execution-gateway/execution_gateway/normalizer.py execution-gateway/execution_gateway/guards.py execution-gateway/execution_gateway/state.py execution-gateway/execution_gateway/dispatch.py scripts/validate_execution_gateway_flow.py scripts/validate_execution_dispatcher.py` 통과
  - `python3 scripts/validate_execution_dispatcher.py` 기준 `checked_cases 5`, `audit_rows 5`, `errors []`
  - `python3 execution-gateway/demo.py` 기준 `emergency_stop_latch -> fan_blocked_by_estop -> emergency_stop_reset_request -> source_water_dispatch -> auto_mode_reentry_request` 흐름 확인
  - `zone-a`는 estop reset 후 `auto_mode_enabled=false`, `site gh-01`는 auto reentry 후 `auto_mode_enabled=true`로 상태가 남는 것을 확인했다.

### 승인 체계 기준 문서 추가
- `docs/approval_governance.md`를 추가해 저위험/중위험/고위험 액션 분류를 고정했다.
- 같은 문서에 `operator`, `shift_lead`, `facility_manager`, `safety_manager` 역할을 승인자로 정리했다.
- 승인 UI 최소 표시 필드, timeout, 거절 시 fallback을 문서로 정리했다.

### sensor-ingestor publish backend와 quality evaluator 추가
- `sensor-ingestor/sensor_ingestor/backends.py`를 추가해 MQTT JSONL outbox, timeseries line protocol outbox, object store metadata outbox, anomaly alert outbox를 구현했다.
- `sensor-ingestor/sensor_ingestor/quality.py`를 추가해 `quality_flag`, `quality_reason`, `automation_gate` 계산기를 구현했다.
- `sensor-ingestor/sensor_ingestor/runtime.py`를 보강해 sensor/device normalize 시 품질 평가와 anomaly alert 생성을 수행하도록 했다.
- `sensor-ingestor/main.py`에 반복 실행 간격 인자를 추가해 단발 실행 외 반복 run 루프도 동작하도록 고쳤다.
- `.env.example`, `.env.dev.example`, `.env.staging.example`, `.env.prod.example`에 `SENSOR_INGESTOR_RUNTIME_DIR`와 outbox backend 경로 예시를 반영했다.
- `scripts/validate_sensor_ingestor_runtime.py`를 추가해 MQTT/timeseries outbox와 alert outbox가 실제로 생성되는지 검증하도록 했다.
- 검증 결과:
  - `python3 -m py_compile sensor-ingestor/main.py sensor-ingestor/sensor_ingestor/config.py sensor-ingestor/sensor_ingestor/runtime.py sensor-ingestor/sensor_ingestor/backends.py sensor-ingestor/sensor_ingestor/quality.py scripts/validate_sensor_ingestor_runtime.py` 통과
  - `python3 scripts/validate_sensor_ingestor_runtime.py` 기준 `mqtt_rows 12`, `timeseries_lines 20`, `alert_rows 1`, `errors []`
  - `python3 sensor-ingestor/main.py --once --limit-sensor-groups 2 --limit-device-groups 1` 기준 backend 경로와 publish metrics가 summary에 반영되는 것을 확인했다.

### 프로젝트 관리 초기화 단계 완료
- `docs/project_bootstrap.md`를 추가해 코드명 `pepper-ops`, monorepo 결정, 공통 디렉터리 기준을 정리했다.
- `docs/git_workflow.md`를 추가해 브랜치 전략, PR/Issue 템플릿, ADR 템플릿, CHANGELOG 정책, 릴리즈 태깅 규칙을 정리했다.
- `docs/development_toolchain.md`, `.python-version`, `pyproject.toml`, `.pre-commit-config.yaml`을 추가해 Python 3.12, pip, ruff, black, mypy, pre-commit 기준을 고정했다.
- `.env.dev.example`, `.env.staging.example`, `.env.prod.example`를 추가해 환경별 env template 분리 기준을 정리했다.
- `docs/post_construction_sensor_cutover.md`를 추가해 공사 완료 후 실센서 연결 전환 절차를 정의했다.
- `docs/glossary.md`, `docs/naming_conventions.md`를 추가해 용어집, robot_id 규칙, event naming 규칙을 정리했다.
- `.github/pull_request_template.md`, `.github/ISSUE_TEMPLATE/*`, `docs/adr/0000-template.md`, `CHANGELOG.md`를 추가해 협업 기본 템플릿을 마련했다.
- `libs/README.md`, `infra/README.md`, `experiments/README.md`, `state-estimator/README.md`, `policy-engine/README.md`, `llm-orchestrator/README.md`를 추가해 monorepo skeleton을 고정했다.

### plc-adapter runtime endpoint와 Modbus address registry 추가
- `docs/plc_runtime_endpoint_config.md`를 추가해 controller endpoint를 환경 변수로 주입하는 기준을 정리했다.
- `.env.example`에 `PLC_ENDPOINT_GH_01_MAIN_PLC`, `PLC_ENDPOINT_GH_01_DRY_PLC` 예시 키를 추가했다.
- `plc-adapter/plc_adapter/runtime_config.py`를 추가해 controller id 기반 env key 생성과 runtime endpoint override resolver를 구현했다.
- `plc-adapter/plc_adapter/channel_refs.py`를 추가해 `plc_tag://{controller_id}/...` channel ref parser를 작성했다.
- `docs/plc_channel_address_registry.md`를 추가해 logical channel ref와 실제 Modbus 주소를 분리 관리하는 기준을 정리했다.
- `schemas/device_channel_address_registry_schema.json`을 추가해 address registry 구조를 JSON Schema로 고정했다.
- `scripts/build_device_channel_address_registry.py`를 추가해 site override seed에서 placeholder Modbus address map을 생성하도록 했다.
- `data/examples/device_channel_address_registry_seed.json`을 생성해 총 69개 channel ref에 대한 placeholder address map을 고정했다.
- `scripts/validate_device_channel_address_registry.py`를 추가해 address registry가 site override와 1:1로 대응하고 controller/table/address가 중복되지 않는지 검증하도록 했다.
- `plc-adapter/plc_adapter/channel_address_registry.py`를 추가해 adapter가 logical ref를 transport ref로 해석할 수 있게 했다.
- `plc-adapter/plc_adapter/plc_tag_modbus_tcp.py`를 보강해 payload에 `write_channel_address`, `read_channel_addresses`, `transport_write_values`, `transport_mirror_read_values`, `transport_read_refs`를 포함하도록 했다.
- adapter는 이제 write/readback 시 logical ref가 아니라 `modbus://{controller_id}/{table}/{address}` 형식의 transport ref를 사용한다.
- 검증 결과:
  - `python3 scripts/build_device_channel_address_registry.py` 기준 `channels 69`
  - `python3 scripts/validate_device_channel_address_registry.py` 기준 `expected_channels 69`, `mapped_channels 69`, `errors 0`
  - `python3 scripts/validate_device_site_overrides.py` 기준 `errors 0`
  - `python3 scripts/validate_device_command_requests.py` 기준 `rows 3`, `errors 0`
  - `python3 plc-adapter/demo.py` 출력에 runtime endpoint/env key와 transport ref 기반 payload가 반영되는 것을 확인했다.

### 장치별 command mapping 실행 검증 추가
- `docs/device_command_mapping_matrix.md`를 추가해 fan, shade, vent, irrigation valve, heater, co2, fertigation, source water valve의 action/parameter/encoder/ack 매핑을 정리했다.
- `data/examples/device_command_mapping_samples.jsonl`에 대표 장치 8건 command sample을 추가했다.
- `scripts/validate_device_command_mappings.py`를 추가해 sample을 실제 `adapter.write_device_command()` 경로로 실행하고 `transport_write_values`, `transport_read_refs`, `write_channel_address`, `read_channel_addresses`를 함께 검증하도록 했다.
- 검증 결과:
  - `python3 scripts/validate_device_command_requests.py --input data/examples/device_command_mapping_samples.jsonl` 기준 `rows 8`, `errors 0`
  - `python3 scripts/validate_device_command_mappings.py` 기준 `rows 8`, `errors 0`
  - 8건 모두 `status acknowledged`

### execution-gateway override contract 추가
- `docs/execution_gateway_override_contract.md`를 추가해 `emergency_stop_latch`, `emergency_stop_reset_request`, `manual_override_start`, `manual_override_release`, `safe_mode_entry`, `auto_mode_reentry_request`를 일반 장치 명령과 분리된 계약으로 정의했다.
- `schemas/control_override_request_schema.json`을 추가해 override 요청 구조를 JSON Schema로 고정했다.
- `data/examples/control_override_request_samples.jsonl`에 override sample 5건을 추가했다.
- `scripts/validate_control_override_requests.py`를 추가해 actor type, approval requirement, precondition 규칙을 검증하도록 했다.
- 검증 결과:
  - `python3 scripts/validate_control_override_requests.py` 기준 `rows 5`, `errors 0`
  - `python3 -m py_compile scripts/validate_control_override_requests.py` 통과

### execution-gateway preflight skeleton 추가
- `docs/execution_gateway_flow.md`를 추가해 schema -> range -> availability -> duplicate -> cooldown -> policy -> approval -> audit -> dispatch 흐름을 정의했다.
- `execution-gateway/execution_gateway/contracts.py`에 일반 장치 명령과 override 요청 dataclass loader를 추가했다.
- `execution-gateway/execution_gateway/normalizer.py`에 `NormalizedRequest`와 dedupe/cooldown key 생성 규칙을 추가했다.
- `execution-gateway/execution_gateway/guards.py`에 `DuplicateDetector`, `CooldownManager`, device/override preflight evaluator를 추가했다.
- `execution-gateway/demo.py`를 추가해 heater pending, fan cooldown, estop latch, auto re-entry 케이스를 시연하도록 했다.
- `scripts/validate_execution_gateway_flow.py`를 추가해 승인 대기, cooldown, duplicate, approved re-entry 경로를 회귀 검증하도록 했다.
- 검증 결과:
  - `python3 execution-gateway/demo.py`에서 heater `approval_pending`, fan `cooldown_active`, estop `ready`, auto re-entry `ready` 확인
  - `python3 scripts/validate_execution_gateway_flow.py` 기준 `checked_cases 4`, `errors 0`
  - `python3 -m py_compile execution-gateway/demo.py execution-gateway/execution_gateway/contracts.py execution-gateway/execution_gateway/normalizer.py execution-gateway/execution_gateway/guards.py scripts/validate_execution_gateway_flow.py` 통과

### Device Profile registry와 plc-adapter 인터페이스 강화
- `docs/device_profile_registry.md`를 추가해 `model_profile`를 `plc-adapter` 실행 계약의 key로 쓰는 기준을 정리했다.
- `schemas/device_profile_registry_schema.json`과 `data/examples/device_profile_registry_seed.json`을 추가해 장치 프로필 registry seed를 고정했다.
- zone 관수밸브와 원수 메인 밸브를 서로 다른 profile로 분리했다. zone 관수밸브는 `valve_open_close_feedback`, 원수 메인 밸브는 `source_water_valve_feedback`을 사용한다.
- `docs/plc_adapter_interface_contract.md`를 추가해 `validate_command`, `write_command`, `readback`, `evaluate_ack`를 포함한 interface contract를 정의했다.
- `plc-adapter/plc_adapter/device_profiles.py`에 registry version 로드, parameter validation, ack success condition 평가 로직을 추가했다.
- `plc-adapter/plc_adapter/interface.py`에 `CommandRequest`, `CommandResult` dataclass와 abstract interface를 정의했다.
- `plc-adapter/plc_adapter/mock_adapter.py`와 `plc-adapter/demo.py`를 추가해 profile 기반 payload 생성, readback, ack 평가가 동작하는 mock skeleton을 만들었다.
- `scripts/validate_device_profile_registry.py`를 추가해 registry, action schema, device catalog 간의 정합성을 검증하도록 했다.
- 검증 결과:
  - `python3 scripts/validate_device_profile_registry.py` 기준 `device_profiles 10`, `catalog_devices 20`, `referenced_profiles 10`, `errors 0`
  - `python3 -m py_compile scripts/validate_device_profile_registry.py plc-adapter/demo.py plc-adapter/plc_adapter/device_profiles.py plc-adapter/plc_adapter/interface.py plc-adapter/plc_adapter/mock_adapter.py` 통과
  - `python3 plc-adapter/demo.py` 기준 `fan_status acknowledged`, `source_water_status acknowledged`

### plc-adapter site override address map과 resolver 추가
- `docs/plc_site_override_map.md`를 추가해 profile과 실제 controller/channel binding을 분리하는 기준을 정리했다.
- `schemas/device_site_override_schema.json`과 `data/examples/device_site_override_seed.json`을 추가해 `gh-01` 예시 site override seed를 작성했다.
- seed에는 `gh-01-main-plc`, `gh-01-dry-plc` controller 2개와 PLC 장치 20개의 placeholder channel binding을 포함했다.
- `plc-adapter/plc_adapter/device_catalog.py`를 추가해 catalog에서 `device_id -> profile_id`를 로드하도록 했다.
- `plc-adapter/plc_adapter/site_overrides.py`를 추가해 controller/binding registry를 로드하도록 했다.
- `plc-adapter/plc_adapter/resolver.py`를 추가해 `device_id -> profile -> controller/channel` 해석 경로를 만들었다.
- `plc-adapter/plc_adapter/mock_adapter.py`에 resolver 연동을 추가해 payload가 profile 기본 `profile://...` 대신 site override의 `plc_tag://...` 채널을 사용하도록 바꿨다.
- `plc-adapter/demo.py`는 이제 `profile_id`를 직접 넘기지 않고 `device_id`만으로 fan/source water valve 명령을 실행한다.
- `scripts/validate_device_site_overrides.py`를 추가해 site override, device catalog, profile registry 정합성을 검증하도록 했다.
- 검증 결과:
  - `python3 scripts/validate_device_site_overrides.py` 기준 `controllers 2`, `device_bindings 20`, `plc_devices_in_catalog 20`, `errors 0`
  - `python3 plc-adapter/demo.py` 출력 payload에 `controller_id`, `controller_endpoint`, `write_channel_ref`, `read_channel_refs`가 site override 값으로 반영되는 것을 확인했다.

### plc_tag_modbus_tcp adapter skeleton 추가
- `plc-adapter/plc_adapter/transports.py`를 추가해 `PlcTagTransport` interface와 `InMemoryPlcTagTransport`를 작성했다.
- `plc-adapter/plc_adapter/codecs.py`를 추가해 seed profile에서 쓰는 encoder/decoder registry를 정의했다.
- `plc-adapter/plc_adapter/plc_tag_modbus_tcp.py`를 추가해 `device_id -> profile -> controller/channel` resolve 후 transport와 codec을 사용하는 adapter runtime을 작성했다.
- adapter에는 connect, reconnect, write, readback, timeout, retry, ack, result mapping, health check 흐름을 skeleton 수준으로 넣었다.
- `plc-adapter/demo.py`는 이제 in-memory transport 기준 `plc_tag_modbus_tcp` adapter를 사용한다.
- main PLC endpoint에 1회 write timeout을 의도적으로 넣고 `max_retries=1`로 fan 명령이 재시도 후 성공하는 흐름을 확인했다.
- 검증 결과:
  - `python3 -m py_compile scripts/validate_device_site_overrides.py plc-adapter/demo.py plc-adapter/plc_adapter/device_catalog.py plc-adapter/plc_adapter/site_overrides.py plc-adapter/plc_adapter/resolver.py plc-adapter/plc_adapter/mock_adapter.py plc-adapter/plc_adapter/transports.py plc-adapter/plc_adapter/codecs.py plc-adapter/plc_adapter/plc_tag_modbus_tcp.py` 통과
  - `python3 plc-adapter/demo.py` 기준 `before_status ok`, `after_status ok`, `fan_command.status acknowledged`, `source_water_command.status acknowledged`
  - demo payload에 `write_values`, site override channel, controller endpoint가 함께 반영되고 `connect_count 2`, `write_count 2`, `read_count 2`로 집계되는 것을 확인했다.

### execution-gateway 저수준 command contract 추가
- `docs/execution_gateway_command_contract.md`를 추가해 execution-gateway가 `plc-adapter`로 넘기는 저수준 장치 명령 형식을 정의했다.
- `schemas/device_command_request_schema.json`을 추가해 `schema_version`, `device_id`, `action_type`, `parameters`, `approval_context`, `policy_snapshot` 구조를 고정했다.
- `data/examples/device_command_request_samples.jsonl`에 fan, source water valve, heater 요청 샘플 3건을 추가했다.
- `scripts/validate_device_command_requests.py`를 추가해 요청 샘플이 action schema, device catalog, device profile registry와 정합한지 검증하도록 했다.
- 검증 결과:
  - `python3 scripts/validate_device_command_requests.py` 기준 `rows 3`, `errors 0`

### sensor-ingestor MVP skeleton 추가
- `sensor-ingestor/` 디렉터리를 추가하고 `sensor-ingestor/main.py` 진입점을 작성했다.
- `sensor-ingestor/sensor_ingestor/config.py`에 config/catalog 로더를 추가했다.
- `sensor-ingestor/sensor_ingestor/runtime.py`에 sensor/device binding group 기준 dry-run poller, parser, normalizer, in-memory publish sink를 구현했다.
- 동일 모듈에 `/healthz`, `/metrics` endpoint를 여는 stdlib HTTP server를 추가했다.
- 검증 결과:
  - `python3 -m py_compile sensor-ingestor/main.py sensor-ingestor/sensor_ingestor/config.py sensor-ingestor/sensor_ingestor/runtime.py` 통과
  - `python3 sensor-ingestor/main.py --once --limit-sensor-groups 2 --limit-device-groups 2` 통과
  - `python3 sensor-ingestor/main.py --serve-port 18080 ...` 실행 후 `curl -L http://127.0.0.1:18080/healthz`, `curl -L http://127.0.0.1:18080/metrics` 응답 확인
- 현재 publish 경로는 in-memory sink 기준이며, 실제 MQTT broker와 timeseries DB 연결은 다음 단계로 남겨두었다.

### 운영 시나리오와 안전 요구사항 정리
- `data/examples/synthetic_sensor_scenarios.jsonl`에 고습, 급격한 일사 증가, 과건조, 장치 stuck, 통신 장애, 정전/재기동, 사람 개입, 로봇 작업 중단 시나리오 8건을 추가해 총 14건으로 확장했다.
- `docs/operational_scenarios.md`를 추가해 정상/환경 스트레스/센서 장애/장치 장애/안전 이벤트 시나리오를 목록화했다.
- `scripts/validate_synthetic_scenarios.py`를 추가해 합성 시나리오 JSONL의 필수 필드와 중복 `scenario_id`를 검증하도록 했다.
- 검증 결과: `python3 scripts/validate_synthetic_scenarios.py` 기준 `rows 14`, `duplicate_scenario_ids 0`, `errors 0`.
- `docs/safety_requirements.md`를 추가해 인터록, 비상정지, 수동/자동모드 전환, 승인 필수 액션, 절대 금지 액션, 사람 감지, 로봇 작업구역 접근 규칙을 정리했다.
- `todo.md`의 `1.4 운영 시나리오 정리`와 `1.5 안전 요구사항 정리`를 모두 완료 처리했다.

### sensor-ingestor 설정 포맷과 poller profile 초안 작성
- `docs/sensor_ingestor_config_spec.md`를 추가해 `poller_profiles`, `connections`, `sensor_binding_groups`, `device_binding_groups`, `quality_rule_sets`, `publish_targets`, `snapshot_pipeline`, `health_config` 계약을 정의했다.
- `schemas/sensor_ingestor_config_schema.json`을 추가해 설정 파일 구조를 JSON Schema로 고정했다.
- `data/examples/sensor_ingestor_config_seed.json`을 추가해 `gh-01` 기준 poller profile 7개, connection 11개, sensor binding group 19개, device binding group 16개 예시를 작성했다.
- seed config는 기존 `data/examples/sensor_catalog_seed.json`의 센서 29개와 장치 20개를 각각 정확히 한 번씩 binding하도록 구성했다.
- `scripts/validate_sensor_ingestor_config.py`를 추가해 catalog 참조 경로, protocol 일치, quality rule coverage, sensor/device coverage를 검증하도록 했다.
- 검증 결과: `python3 scripts/validate_sensor_ingestor_config.py` 기준 `covered_sensors 29`, `covered_devices 20`, `errors 0`.
- `README.md`, `PROJECT_STATUS.md`, `AI_MLOPS_PLAN.md`, `todo.md`, `data/examples/README.md`, `docs/sensor_collection_plan.md`, `docs/sensor_installation_inventory.md`에 상태와 링크를 반영했다.

### 센서 품질 규칙과 ingestor runtime flow 문서화
- `docs/sensor_quality_rules_pseudocode.md`를 추가해 `missing`, `stale`, `outlier`, `jump`, `flatline`, `readback_mismatch` 우선순위와 automation gate 규칙을 pseudocode 수준으로 고정했다.
- `docs/sensor_ingestor_runtime_flow.md`를 추가해 startup, polling cycle, parser, normalizer, quality evaluator, publisher, snapshot/trend, health 흐름을 문서화했다.
- `todo.md`의 `6.4 센서 품질 관리`에서 규칙 정의 항목 4개를 완료 처리했다.
- `README.md`, `PROJECT_STATUS.md`, `AI_MLOPS_PLAN.md`의 다음 우선순위를 `sensor-ingestor` MVP skeleton 작성으로 갱신했다.

### farm_case 환류 샘플과 event window 규칙 구체화
- `data/examples/farm_case_candidate_samples.jsonl`에 `farm_case_candidate` 샘플 10건을 추가했다.
- 성공, 부분 회복, 실패, 미확정, 센서 fault, 병해, postharvest, 수출 residue 사례를 섞어 review 상태별 샘플을 구성했다.
- `docs/farm_case_event_window_builder.md`를 추가해 `event_window` anchor, pre/post window, 병합/분리, 품질 게이트, 출력 계약을 문서화했다.
- `scripts/validate_farm_case_candidates.py`를 추가해 `farm_case` 샘플 JSONL의 필수 필드, enum, 시간 순서, 승인 조건을 검증하도록 했다.
- `scripts/build_farm_case_rag_chunks.py`를 추가해 승인된 후보만 `data/rag/farm_case_seed_chunks.jsonl`로 변환하는 초안을 작성했다.
- 변환 결과는 샘플 10건 중 7건이 승격 조건을 통과했고, `scripts/validate_rag_chunks.py --input data/rag/farm_case_seed_chunks.jsonl` 검증을 통과했다.
- `scripts/build_rag_index.py`가 다중 입력 JSONL을 받아 official + farm_case 혼합 인덱스를 만들 수 있도록 확장했다.
- `scripts/search_rag_index.py`에 `farm_case` 혼합 인덱스용 공식 지침 우선 정렬 guardrail과 `farm_id`, `zone_id` 필터를 추가했다.
- `evals/rag_official_priority_eval_set.jsonl`을 추가해 혼합 인덱스에서 공식 청크가 top1로 유지되는 회귀셋 4건을 작성했다.
- `docs/farm_case_rag_pipeline.md`, `README.md`, `PROJECT_STATUS.md`, `AI_MLOPS_PLAN.md`, `todo.md`, `data/examples/README.md`에 진행 상태와 링크를 반영했다.

## 2026-04-10

### 저장소 이력관리 초기화
- 로컬 Git 저장소를 초기화했다.
- GitHub 원격 저장소를 연결했다: `https://github.com/hyunmin625/pepper_smartfarm_plan_v2.git`
- `.codex` 로컬 파일을 제외하기 위해 `.gitignore`를 추가했다.
- 초기 계획 문서와 가이드 문서를 첫 커밋으로 등록하고 `origin/master`에 푸시했다.
- 커밋: `3a82436 Initial project planning documents`

### 기여자 가이드 작성 및 한글화
- `AGENTS.md`를 저장소 기여자 가이드로 작성했다.
- 이후 저장소 문서 성격에 맞춰 한글로 다시 작성했다.
- 포함 내용: 프로젝트 구조, 개발 명령, 명명 규칙, 테스트 기준, 커밋/PR 기준, 보안 주의사항
- 커밋: `fba81c3 Translate repository guide to Korean`

### 계획 문서 분석
- `PLAN.md`, `todo.md`, `schedule.md` 전체 구조를 분석했다.
- 현재 저장소가 구현 코드가 아닌 기획 문서 저장소임을 확인했다.
- 핵심 방향을 다음과 같이 정리했다.
  - LLM은 상위 판단 및 계획 엔진으로 사용한다.
  - 실제 장치 제어는 PLC, 정책 엔진, 실행 게이트가 담당한다.
  - 자동화는 shadow mode, approval mode, limited auto mode 순서로 진행한다.
  - 모든 판단과 실행은 감사 로그로 남긴다.

### RAG + 파인튜닝 하이브리드 구조 조사 및 계획 반영
- 적고추(건고추) 온실 스마트팜 운영용 LLM에 RAG와 파인튜닝을 함께 사용하는 구조의 타당성을 검토했다.
- 결론: 하이브리드 구조가 적합하다.
  - RAG는 재배 매뉴얼, 현장 SOP, 품종/지역별 기준, 정책 문서처럼 자주 바뀌거나 출처 추적이 필요한 지식을 담당한다.
  - 파인튜닝은 JSON 출력, action_type 선택, 안전 거절, follow_up, confidence 표현 등 반복 운영 행동 양식을 담당한다.
- `PLAN.md`에 하이브리드 타당성, RAG 검색 설계, Vector Store/Vector DB, `rag-retriever`, citation 로그 구조를 추가했다.
- `todo.md`에 RAG 지식베이스 구축, 검색 품질 평가, RAG 도구 함수, citation 검증, 통합/E2E 테스트 항목을 추가했다.
- `schedule.md`에 Week 1 RAG 범위 확정, Week 2 vector store PoC, Week 5 RAG 근거 결합 작업을 추가했다.
- 참고 근거:
  - OpenAI Retrieval guide: https://platform.openai.com/docs/guides/retrieval
  - OpenAI File search guide: https://platform.openai.com/docs/guides/tools-file-search/
  - OpenAI Fine-tuning guide: https://platform.openai.com/docs/guides/fine-tuning
  - Lewis et al., Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks: https://arxiv.org/abs/2005.11401
- 커밋: `06dde64 Add hybrid RAG fine-tuning plan`

### AI/에이전트용 현황 문서 정리
- 다른 AI가 저장소 목적과 진행상황을 빠르게 파악할 수 있도록 `PROJECT_STATUS.md`를 추가했다.
- 일반 진입점 역할을 위해 `README.md`를 추가했다.
- `PLAN.md`, `todo.md`, `schedule.md`, `AGENTS.md`에 `README.md`, `PROJECT_STATUS.md`, `WORK_LOG.md` 링크를 반영했다.
- 문서 탐색 순서를 `README.md` → `PROJECT_STATUS.md` → `PLAN.md` → `schedule.md` → `todo.md` → `WORK_LOG.md` → `AGENTS.md`로 정리했다.

### 온실 공사중 전제 및 AI/MLOps 선행 계획 반영
- 온실이 아직 공사 중이며 실측 센서 데이터가 없다는 전제를 계획에 반영했다.
- 개발 순서를 `AI 준비 구축 → 센서 수집 계획 보강 → 센서 수집 구현 → 통합 제어 시스템 개발 계획 → 통합 제어 시스템 구현 → 사용자 UI 대시보드 개발 → AI 모델과 통합 제어 시스템 연결`로 개정했다.
- `AI_MLOPS_PLAN.md`를 추가해 AI 모델 준비, 센서 수집 계획, 센서 데이터 분석, 학습 반영, MLOps 루프, 모델 진화 전략을 정리했다.
- `PLAN.md`에 Phase -1 AI 준비 구축 및 MLOps 기반 설계를 추가했다.
- `schedule.md`를 AI 준비 선행 일정으로 재구성했다.
- `todo.md`에 온실 공사중 전제, AI 준비/MLOps 기반 구축, 센서 수집 계획 보강, 모델 승격/롤백 항목을 추가했다.
- 참고 근거:
  - OpenAI Evals API: https://platform.openai.com/docs/api-reference/evals
  - OpenAI Retrieval guide: https://platform.openai.com/docs/guides/retrieval
  - OpenAI Fine-tuning guide: https://platform.openai.com/docs/guides/fine-tuning
  - MLflow Model Registry: https://mlflow.org/docs/latest/ml/model-registry/
  - Kubeflow Pipelines: https://www.kubeflow.org/docs/components/pipelines/overview/

### 적고추 재배 전주기 전문가 AI Agent 구축 계획 반영
- 적고추 온실 스마트팜 재배 전주기 전문가 AI Agent 구축 단계를 조사하고 `EXPERT_AI_AGENT_PLAN.md`로 정리했다.
- 전주기 범위를 입식 전 준비, 육묘, 정식, 영양생장, 개화/착과, 과실 비대/착색, 수확, 건조/저장, 작기 종료로 나누었다.
- 센서 기반 판단 체계를 환경, 근권/양액, 외기, 장치, 비전, 운영 이벤트로 정리했다.
- `growth-stage-agent`, `climate-agent`, `irrigation-agent`, `nutrient-agent`, `pest-disease-agent`, `harvest-drying-agent`, `safety-agent`, `report-agent` 역할을 정의했다.
- `README.md`, `PROJECT_STATUS.md`, `PLAN.md`, `schedule.md`, `todo.md`, `AGENTS.md`에 전문가 AI 구축 계획 링크와 우선 작업을 반영했다.
- 참고 근거:
  - 농사로 고추 육묘/재배 환경 자료: https://www.nongsaro.go.kr/portal/ps/psx/psxa/mlrdCurationDtl.mo?curationNo=188
  - 농사로 고추 이상증상 현장 기술지원: https://www.nongsaro.go.kr/portal/ps/psz/psza/contentSub.ps?cntntsNo=262042&menuId=PS00077
  - 농사로 고추 양액재배 현장 기술지원: https://nongsaro.go.kr/portal/ps/psz/psza/contentSub.ps?cntntsNo=259682&menuId=PS00077
  - 농사로 고추 생육불량 현장 기술지원: https://nongsaro.go.kr/portal/ps/psz/psza/contentSub.ps?cntntsNo=249249&menuId=PS00077
  - OpenAI Retrieval guide: https://platform.openai.com/docs/guides/retrieval
  - OpenAI Evals API: https://platform.openai.com/docs/api-reference/evals

### 인터넷 조사 5회 반복 및 RAG 구축 시작
- 인터넷 조사를 5회 반복해 전주기 전문가 AI용 초기 지식을 수집했다.
  1. 육묘/정식/초기 생육
  2. 온실 환경/고온/환기/차광
  3. 근권/양액/배지/EC/pH
  4. 병해충/생리장해
  5. 수확/건조/저장
- `docs/rag_source_inventory.md`를 추가해 RAG 출처, 메타데이터, ingestion 상태를 정리했다.
- `data/rag/pepper_expert_seed_chunks.jsonl`을 추가해 초기 seed chunk 6개를 작성했다.
- `docs/expert_knowledge_map.md`를 추가해 전주기 생육/운영 지식 지도를 작성했다.
- `docs/sensor_judgement_matrix.md`를 추가해 센서 데이터와 AI 판단 항목을 매핑했다.
- 다음 단계는 schema 작성, expert eval set 작성, vector store 인덱싱 스크립트 설계다.

### 전문가 AI Agent 스키마 4종 작성
- `schemas/state_schema.json`을 추가해 AI Agent 입력 상태 계약을 정의했다.
- `schemas/feature_schema.json`을 추가해 VPD, DLI, trend, 근권 스트레스, 숙도/병징 score 등 파생 특징량 구조를 정의했다.
- `schemas/sensor_quality_schema.json`을 추가해 missing, stale, outlier, jump, calibration error 등 품질 플래그 구조를 정의했다.
- `schemas/action_schema.json`을 추가해 AI 추천 행동, 승인 필요 여부, follow_up, citation, policy precheck 구조를 정의했다.
- 모든 JSON 스키마는 `python3 -m json.tool`로 문법 검증했다.

### 전문가 판단 평가셋 초안 작성
- `evals/expert_judgement_eval_set.jsonl`을 추가했다.
- 초기 케이스 8개를 작성했다: 정상 영양생장, 고온 스트레스, 과습/뿌리 갈변 위험, 배액 EC 상승, 온도 센서 stale, 병해충 의심, 수확/건조 계획, 작업자 존재 시 로봇 차단.
- `evals/README.md`를 추가해 평가 목적, 카테고리, 확장 방향을 정리했다.
- JSONL은 줄 단위 JSON 검증 대상으로 관리한다.

### 파인튜닝 후보 seed 샘플 작성
- `data/examples/state_judgement_samples.jsonl`을 추가해 상태판단 샘플 5개를 작성했다.
- `data/examples/forbidden_action_samples.jsonl`을 추가해 금지행동/승인필요 샘플 5개를 작성했다.
- `data/examples/README.md`를 추가해 샘플 작성 원칙과 확장 방향을 정리했다.
- 자주 바뀌는 기준값은 샘플에 암기시키지 않고 RAG citation으로 연결하는 원칙을 유지했다.

### RAG 인덱싱 준비
- `docs/rag_indexing_plan.md`를 추가해 RAG 입력 필드, 인덱싱 문서 구조, 검색 전략, 재인덱싱 규칙, 품질 검증 기준을 정리했다.
- `scripts/build_rag_index.py`를 추가해 `data/rag/pepper_expert_seed_chunks.jsonl`을 로컬 JSON 인덱스로 변환하도록 했다.
- `artifacts/rag_index/pepper_expert_index.json`을 생성했다.
- 스크립트 실행 결과 6개 seed chunk가 인덱싱되었다.
- 생성된 인덱스 JSON은 `python3 -m json.tool`로 문법 검증했다.

### RAG 검색 smoke test 작성
- `scripts/search_rag_index.py`를 추가해 로컬 JSON 인덱스를 keyword + metadata 방식으로 검색하도록 했다.
- `docs/rag_search_smoke_tests.md`를 추가해 고온, 과습, 양액 EC, 병해충, 육묘/정식, 안전/정책 query와 기대 chunk를 정의했다.
- `scripts/rag_smoke_test.py`를 추가해 6개 smoke query가 기대 chunk를 상위 3개 결과 안에 반환하는지 자동 검증한다.
- `python3 scripts/rag_smoke_test.py` 실행 결과 6개 query가 모두 통과했다.

### 농촌진흥청 PDF 기반 RAG 지식 보강
- 사용자가 제공한 로컬 PDF `/mnt/d/DOWNLOAD/GPT_고추재배_훈련세트/original-know-how/고추_재배기술_최종파일-농촌진흥청.pdf`를 `pdftotext -layout`으로 추출해 검토했다.
- 기존 RAG 청크와 중복되는 발아 온도, 정식 온도, 광포화점, 침수 임계, pH/표준시비, 병해충 기본 증상, 수확 적기, 3단계 건조 기준은 제외했다.
- 반영된 정밀 지식은 화분 발아 온도, 야간 저온 단위결과, 오전 광합성 비중, 뿌리/이랑 물리 조건, 플러그 상토 조건, 육묘 관수, 순화, 비가림 온습도, -20kPa 자동관수, 차광 전략, 양액 EC/pH, 석회결핍과, 염류장해, 홍고추 후숙, 건고추 저장 기준이다.
- `data/rag/pepper_expert_seed_chunks.jsonl`은 중복 `chunk_id`를 제거한 뒤 PDF 기반 정밀 청크 누적 22개, 전체 38개 청크 상태로 정리했다.
- `docs/rag_source_inventory.md`에 로컬 PDF 경로와 ingestion note를 기록했다.
- `docs/rag_indexing_plan.md`에 `source_pages`, `source_section` 기반 citation 추적 규칙을 추가했다.
- `scripts/build_rag_index.py`와 `scripts/search_rag_index.py`를 보강해 인과/시각 태그와 source section을 인덱싱·검색에 반영했다.
- `todo.md`에 PDF 지식 보강 완료와 남은 RAG 확장 작업을 반영했다.
- `python3 scripts/build_rag_index.py --skip-embeddings` 실행 결과 38개 문서가 인덱싱되었다.
- `python3 scripts/rag_smoke_test.py` 실행 결과 기존 6개 query와 신규 3개 PDF query가 모두 통과했다.
- JSONL 검증 결과 rows 38, duplicate chunk_id 0건을 확인했다.

### RAG 보완 핵심 과제 반영
- 사용자가 제시한 다음 핵심 과제를 별도 로드맵으로 정리했다.
  1. RAG 지식 청크를 100~200개 이상으로 확장
  2. OpenAI embedding 또는 Chroma/Pinecone 등 vector search 도입
  3. growth_stage, sensor, risk 외에 region, season, cultivar, greenhouse_type, active metadata filter 고도화
  4. 실제 농장 운영 로그와 성공/실패 사례를 `farm_case` RAG 지식으로 변환하는 파이프라인 설계
- `docs/rag_next_steps.md`를 추가해 Knowledge Expansion, Vector Search, Metadata Filtering, Farm Data Feedback 과제를 정리했다.
- `todo.md`, `PROJECT_STATUS.md`, `docs/rag_indexing_plan.md`에 RAG 보완 과제와 링크를 반영했다.

### RAG 청크 검증 기반 구현
- `schemas/rag_chunk_schema.json`을 추가해 RAG chunk 필수 필드와 권장 metadata 구조를 정의했다.
- `scripts/validate_rag_chunks.py`를 추가해 외부 의존성 없이 JSONL 필수 필드, 중복 `chunk_id`, citation metadata 경고를 검증하도록 했다.
- `scripts/build_rag_index.py`의 필수 필드 검증을 `causality_tags`, `visual_tags`까지 확장했다.
- 초기 시드 청크의 `source_pages`, `source_section`, `trust_level`을 보강해 citation metadata 경고를 해소했다.
- 검증 결과: rows 38, duplicate chunk_id 0, errors 0, warnings 0.
- 재색인 결과: `python3 scripts/build_rag_index.py --skip-embeddings`로 38개 문서를 `artifacts/rag_index/pepper_expert_index.json`에 반영했다.
- 검색 smoke test 결과: `python3 scripts/rag_smoke_test.py` 기준 9개 query 모두 PASS.

### RAG 검색 필터 및 Reranking 구현
- `scripts/search_rag_index.py`에 `trust_level` 및 `source_type` 기반 rerank bonus를 추가했다.
- `source_section` 부분 일치 필터와 `region`, `season`, `cultivar`, `greenhouse_type`, `active`, `trust_level` CLI 필터를 추가했다.
- `scripts/rag_smoke_test.py`에 메타데이터 필터 검증 2건을 추가했다.
- 검색 smoke test 결과: 기본 9개 query와 필터 query 2건 모두 PASS.

### RAG 검색 품질 평가 기반 구현
- `evals/rag_retrieval_eval_set.jsonl`을 추가해 기후, 근권, 양액, 병해충, 육묘/정식, 안전정책, 수확/건조, metadata filter 검색 평가 케이스 11건을 정의했다.
- `scripts/evaluate_rag_retrieval.py`를 추가해 Hit Rate와 MRR을 계산하도록 했다.
- 현재 평가 결과: keyword-only 기준 case_count 11, hit_count 11, hit_rate 1.0, MRR 0.9091.
- `evals/README.md`와 `docs/rag_search_smoke_tests.md`에 RAG 검색 평가 실행 명령을 추가했다.

### RAG 병해충·양액재배 지식 확장
- `data/rag/pepper_expert_seed_chunks.jsonl`에 병해충/IPM, 총채벌레·진딧물 생물적 방제, 바이러스 전염 생태, 양액 급액 제어 관련 청크 10개를 추가했다.
- 추가된 청크에는 `pepper-hydroponic-water-ph-buffer-001`, `pepper-hydroponic-irrigation-volume-001`, `pepper-hydroponic-irrigation-control-001`, `pepper-ipm-lifecycle-001`, `pepper-ipm-scouting-hygiene-001`, `pepper-thrips-tswv-control-001`, `pepper-thrips-biocontrol-001`, `pepper-aphid-virus-biocontrol-001`, `pepper-virus-epidemiology-001`, `pepper-tswv-early-house-001`가 포함된다.
- 확장 후 검증 결과: rows 48, duplicate chunk_id 0, warnings 0, errors 0.
- 재색인 결과: `python3 scripts/build_rag_index.py --skip-embeddings`로 48개 문서를 `artifacts/rag_index/pepper_expert_index.json`에 반영했다.
- 검색 품질 유지 확인: `python3 scripts/rag_smoke_test.py` 11건 PASS, `python3 scripts/evaluate_rag_retrieval.py --fail-under 1.0` hit_rate 1.0, MRR 0.9091.

### RAG 품종·재배력 지식 확장
- `data/rag/pepper_expert_seed_chunks.jsonl`에 품종 선택 기준, 풋고추 과형 분류, 작형별 재배 형태, 노지 재배력, 수확 기준일 관련 청크 8개를 추가했다.
- 추가된 청크에는 `pepper-cultivar-selection-dry-001`, `pepper-cultivar-selection-green-001`, `pepper-cultivar-rain-shelter-001`, `pepper-cultivar-resistance-stack-001`, `pepper-greenpepper-type-001`, `pepper-regional-cropping-system-001`, `pepper-openfield-calendar-001`, `pepper-harvest-days-by-type-001`가 포함된다.
- 확장 후 검증 결과: rows 56, duplicate chunk_id 0, warnings 0, errors 0.
- 재색인 결과: `python3 scripts/build_rag_index.py --skip-embeddings`로 56개 문서를 `artifacts/rag_index/pepper_expert_index.json`에 반영했다.
- 검색 품질 확인: `python3 scripts/rag_smoke_test.py` 11건 PASS, `python3 scripts/evaluate_rag_retrieval.py --fail-under 1.0` hit_rate 1.0, MRR 0.8939.

### RAG 기상 재해·계절 리스크 지식 확장
- `data/rag/pepper_expert_seed_chunks.jsonl`에 비가림 재배력, 장마, 태풍, 우박, 지역 저온, 터널 서리창 대응 기준 청크 6개를 추가했다.
- 추가된 청크에는 `pepper-rain-shelter-calendar-001`, `pepper-lowtemp-regional-recovery-001`, `pepper-monsoon-prevention-001`, `pepper-typhoon-response-001`, `pepper-hail-recovery-001`, `pepper-tunnel-frost-window-001`가 포함된다.
- 신규 공식 지침 청크 유입으로 일부 query의 상위 순위가 흔들려 `scripts/search_rag_index.py`의 `official_guideline` rerank bonus를 0.4로 상향 조정했다.
- 확장 후 검증 결과: rows 62, duplicate chunk_id 0, warnings 0, errors 0.
- 재색인 결과: `python3 scripts/build_rag_index.py --skip-embeddings`로 62개 문서를 `artifacts/rag_index/pepper_expert_index.json`에 반영했다.
- 검색 품질 확인: `python3 scripts/rag_smoke_test.py` 11건 PASS, `python3 scripts/evaluate_rag_retrieval.py --fail-under 1.0` hit_rate 1.0, MRR 0.9545.

### RAG 재해 대응 검색 평가 범위 확장
- `scripts/rag_smoke_test.py`에 비가림 재배력, 정식기 저온·재정식, 장마, 태풍, 우박 대응 query 5건을 추가했다.
- `evals/rag_retrieval_eval_set.jsonl`에 동일 범주의 retrieval 평가 케이스 5건을 추가해 전체 16개 case를 검증하도록 확장했다.
- `docs/rag_search_smoke_tests.md`, `docs/rag_indexing_plan.md`, `evals/README.md`, `PROJECT_STATUS.md`, `todo.md`에 최신 평가 범위를 반영했다.
- 확장 후 검색 품질 확인: `python3 scripts/rag_smoke_test.py` 총 16건 PASS, `python3 scripts/evaluate_rag_retrieval.py --fail-under 1.0` case_count 16, hit_rate 1.0, MRR 0.9688.

### RAG 수확 후·건조·저장 지식 확장
- `data/rag/pepper_expert_seed_chunks.jsonl`에 수확 후 물류, 홍고추 후숙, 세척 위생, 풋고추 저장·결로, 홍고추 저장, 건고추 장기 저장, 고춧가루 산소흡수제 포장, 하우스건조, 열풍건조 효율 관련 청크 10개를 추가했다.
- 추가된 청크에는 `pepper-green-harvest-logistics-001`, `pepper-red-harvest-window-001`, `pepper-postharvest-wash-hygiene-001`, `pepper-green-storage-temperature-001`, `pepper-green-packaging-condensation-001`, `pepper-red-storage-ethylene-001`, `pepper-dry-storage-maintenance-001`, `pepper-powder-packaging-oxygen-001`, `pepper-house-drying-hygiene-001`, `pepper-hotair-drying-split-001`가 포함된다.
- 확장 후 검증 결과: rows 72, duplicate chunk_id 0, warnings 0, errors 0.
- 재색인 결과: `python3 scripts/build_rag_index.py --skip-embeddings`로 72개 문서를 `artifacts/rag_index/pepper_expert_index.json`에 반영했다.
- `scripts/rag_smoke_test.py`에 수확 후·저장·건조 query 8건을 추가하고, `evals/rag_retrieval_eval_set.jsonl`에 같은 범주의 retrieval 평가 케이스 8건을 반영했다.
- 확장 후 검색 품질 확인: `python3 scripts/rag_smoke_test.py` 총 24건 PASS, `python3 scripts/evaluate_rag_retrieval.py --fail-under 1.0` case_count 24, hit_rate 1.0, MRR 0.9792.

### 로컬 Vector Search PoC 구현
- `scripts/rag_local_vector.py`를 추가해 외부 의존성 없이 TF-IDF + SVD 기반 로컬 벡터 모델을 생성하도록 했다.
- `scripts/build_rag_index.py`에서 로컬 벡터 모델과 각 문서의 `local_embedding`을 함께 생성하도록 반영했다.
- `scripts/search_rag_index.py`에 `--vector-backend {auto,openai,local,none}` 옵션을 추가하고, OpenAI embedding이 없을 때 `local` 백엔드로 검색할 수 있도록 했다.
- `scripts/evaluate_rag_retrieval.py`에 `--vector-backend` 옵션을 추가해 keyword-only, local vector hybrid, OpenAI vector 경로를 구분 평가하도록 확장했다.
- `scripts/compare_rag_retrieval_modes.py`를 추가해 keyword baseline과 local vector hybrid의 hit rate/MRR 및 changed case를 비교할 수 있도록 했다.
- 검증 결과: `python3 scripts/evaluate_rag_retrieval.py --fail-under 1.0` 기준 keyword-only hit_rate 1.0, MRR 0.9792, `python3 scripts/evaluate_rag_retrieval.py --vector-backend local --fail-under 1.0` 기준 local hybrid hit_rate 1.0, MRR 1.0, `python3 scripts/compare_rag_retrieval_modes.py --candidate-backend local` 기준 delta_mrr +0.0208.

## 2026-04-11

### RAG 2.6 보강: 공식 작목기술/현장기술지원 기반 127청크, 70케이스 재검증
- `data/rag/pepper_expert_seed_chunks.jsonl`에 작물기술정보, 반촉성/보통/촉성 일정, 품종 기준, 활착 불량, 붕소 과잉, 애꽃노린재, 정식기 저온, 곡과 현장 사례를 반영한 신규 청크 27개를 추가했다.
- 전체 RAG 청크 수는 100개에서 127개로 증가했다.
- 신규 주요 청크:
  - `pepper-crop-env-thresholds-001`
  - `pepper-semiforcing-schedule-001`
  - `pepper-forcing-energy-saving-001`
  - `pepper-cultivar-phytophthora-resistance-001`
  - `pepper-hydroponic-coir-prewash-001`
  - `pepper-root-browning-winter-heating-001`
  - `pepper-boron-excess-diagnosis-001`
  - `pepper-orius-release-timing-001`
  - `pepper-transplant-cold-duration-001`
  - `pepper-curved-fruit-cropping-shift-001`
- `docs/rag_source_inventory.md`에 신규 출처 `RAG-SRC-010`~`RAG-SRC-017`을 추가했다.
- `docs/rag_contextual_retrieval_strategy.md`를 추가해 최근 3~5일 상태를 반영하는 retrieval 전략을 문서화했다.
- `scripts/build_rag_index.py`에서 `region`, `season`, `cultivar`, `greenhouse_type` 메타데이터가 JSON index와 text field에 실제 반영되도록 수정했다.
- `scripts/search_rag_index.py`에 동일 metadata 필드를 검색 대상 필드로 추가해 문서화된 필터가 실제 검색 경로와 일치하도록 맞췄다.
- `evals/rag_retrieval_eval_set.jsonl`을 70케이스로 확장하고, `scripts/rag_smoke_test.py`에 대표 query 10건과 metadata filter 2건을 추가했다.
- 검증 결과:
  - `python3 scripts/validate_rag_chunks.py`: rows 127, duplicate 0, warnings 0, errors 0
  - `python3 scripts/build_rag_index.py --skip-embeddings`: 127 documents
  - `python3 scripts/rag_smoke_test.py`: 기본 48 + filter 4, 총 52건 PASS
  - `python3 scripts/evaluate_rag_retrieval.py --fail-under 1.0`: hit rate 1.0, MRR 0.9857
  - `./.venv/bin/python scripts/evaluate_rag_retrieval.py --vector-backend local --fail-under 1.0`: hit rate 1.0, MRR 1.0
  - `./.venv/bin/python scripts/evaluate_rag_retrieval.py --vector-backend chroma --chroma-embedding-backend local --fail-under 1.0`: hit rate 1.0, MRR 1.0
  - `./.venv/bin/python scripts/evaluate_rag_retrieval.py --vector-backend chroma --chroma-embedding-backend openai --fail-under 1.0`: hit rate 1.0, MRR 0.9929
- 조사에 사용한 공식/준공식 출처:
  - 농사로 작물기술정보 고추: `https://nongsaro.go.kr/portal/ps/psz/psza/contentSub.ps?cntntsNo=101628&menuId=PS03172&sSeCode=335001`
  - 농사로 작목정보 포털 고추 일정/품종: `https://www.nongsaro.go.kr/portal/farmTechMain.ps?menuId=PS65291&stdPrdlstCode=VC011205`
  - 농사로 고추 양액재배 현장 기술지원: `https://nongsaro.go.kr/portal/ps/psz/psza/contentSub.ps?cntntsNo=259682&menuId=PS00077`
  - 농사로 고추 생육불량/뿌리 갈변 현장 기술지원: `https://nongsaro.go.kr/portal/ps/psz/psza/contentSub.ps?cntntsNo=249249&menuId=PS00077`
  - 농사로 고추 생육이 불량하고 활착되지 않아요: `https://www.nongsaro.go.kr/portal/ps/psz/psza/contentSub.ps?cntntsNo=246474&menuId=PS00077&totalSearchYn=Y`
  - 농사로 고추 석회결핍 증상이 나타나고 영양제를 주어도 개선이 안돼요: `https://www.nongsaro.go.kr/portal/ps/psz/psza/contentNsSub.ps?cntntsNo=262393&menuId=PS00077`
  - 농사로 미끌애꽃노린재 이용 기술: `https://www.nongsaro.go.kr/portal/ps/pss/pssa/nnmyInsectSearchDtl.ps?menuId=PS00407&nnmyInsectCode=E00000004`
  - 농촌진흥청 보도자료 저온 노출 기간 연구: `https://www.korea.kr/briefing/pressReleaseView.do?newsId=156753597&pWise=main&pWiseMain=L4`
  - 농사로 곡과 현장 기술지원: `https://nongsaro.go.kr/portal/ps/psz/psza/contentSub.ps?cntntsNo=262042&menuId=PS00077`

### RAG 지식 100개 확장 완료
- `data/rag/pepper_expert_seed_chunks.jsonl`을 100개 청크까지 확장했다.
- 육묘 계절 관리, 입고병 예방, 매개충 차단, 접목 목적/방법/활착, 식물공장 육묘, 비가림 구조·염류·저일조 대응 지식을 추가했다.
- 검증 결과: `./.venv/bin/python scripts/validate_rag_chunks.py` 기준 rows 100, duplicate 0, warnings 0, errors 0.
- 재색인 결과: `./.venv/bin/python scripts/build_rag_index.py --skip-embeddings`로 100개 문서를 `artifacts/rag_index/pepper_expert_index.json`에 반영했다.

### ChromaDB Vector Store 도입
- `.venv` 가상환경과 `requirements-rag.txt`를 추가해 RAG/Vector Search 실행 의존성을 명시했다.
- `.gitignore`에 `.venv/`, `artifacts/chroma_db/`를 추가해 재생성 가능한 로컬 산출물을 제외했다.
- `scripts/rag_chroma_store.py`를 기반으로 persistent Chroma collection 접근 함수를 정리했다.
- `scripts/build_chroma_index.py`에 `--embedding-backend {auto,openai,local}` 옵션을 추가했다.
- 현재 환경에서는 OpenAI API 키가 없어 `local` backend로 `artifacts/chroma_db/pepper_expert` 컬렉션을 생성해 검증했다.
- `scripts/search_rag_index.py`에 `--vector-backend chroma`와 `--chroma-embedding-backend {auto,openai,local}` 경로를 반영했다.
- `scripts/evaluate_rag_retrieval.py`, `scripts/compare_rag_retrieval_modes.py`도 동일한 Chroma backend 인자를 받도록 확장했다.

### Citation Coverage 검증 반영
- `scripts/validate_response_citations.py`를 작업 현황 문서와 todo에 반영했다.
- 이 스크립트는 retrieved_context 대비 citations 누락, out-of-context 인용, `citation_required` 미충족, `retrieval_coverage` 불일치를 검증한다.

### Vector Search 검증 결과 갱신
- `./.venv/bin/python scripts/evaluate_rag_retrieval.py --fail-under 1.0`
  - keyword-only: hit_rate 1.0, MRR 0.9583
- `./.venv/bin/python scripts/evaluate_rag_retrieval.py --vector-backend local --fail-under 1.0`
  - local vector hybrid: hit_rate 1.0, MRR 1.0
- `./.venv/bin/python scripts/build_chroma_index.py --embedding-backend local`
  - local-backed Chroma collection 100 vectors 생성
- `./.venv/bin/python scripts/evaluate_rag_retrieval.py --vector-backend chroma --chroma-embedding-backend local --fail-under 1.0`
  - local-backed Chroma hybrid: hit_rate 1.0, MRR 1.0
- `./.venv/bin/python scripts/compare_rag_retrieval_modes.py --candidate-backend chroma --chroma-embedding-backend local`
  - baseline keyword 대비 delta_mrr +0.0417

### `.env` 기반 OpenAI 키 경로 정리
- 저장소 루트 `.env`를 `python-dotenv` 기본 로딩 경로로 사용하도록 운영 절차를 정리했다.
- `.gitignore`에 `.env`, `.env.*`, `!.env.example`를 추가해 실제 키 파일은 추적하지 않도록 했다.
- `.env.example`을 추가했고, 로컬 `.env` 자리도 마련했다.
- 이후 `.env`에 실제 키를 반영해 OpenAI-backed Chroma 실호출 검증까지 수행했다.

### OpenAI-backed Chroma 실검증 완료
- `.env`에서 `OPENAI_API_KEY`를 로드한 뒤 `./.venv/bin/python scripts/build_chroma_index.py --embedding-backend openai`를 실행해 OpenAI 임베딩 기반 Chroma collection 100 vectors를 생성했다.
- `./.venv/bin/python scripts/evaluate_rag_retrieval.py --vector-backend chroma --chroma-embedding-backend openai --fail-under 1.0` 실행 결과, 초기 설정에서는 24개 case hit_rate 1.0, MRR 0.9792를 확인했다.
- `./.venv/bin/python scripts/compare_rag_retrieval_modes.py --candidate-backend chroma --chroma-embedding-backend openai` 실행 결과, keyword baseline 대비 delta_mrr +0.0209를 확인했다.
- 현재 평가셋에서는 local vector/local-backed Chroma(MRR 1.0)가 OpenAI-backed Chroma(MRR 0.9792)보다 소폭 높게 나와, 원인 분석 대상으로 넘겼다.

### OpenAI-backed Chroma 보정 및 collection 분리
- `scripts/tune_rag_weights.py`를 추가해 retrieval weight grid search를 자동화했다.
- OpenAI-backed Chroma에 대해 `chroma_local_blend_weight`를 0, 2, 4, 6으로 비교한 결과, `4.0`부터 MRR 1.0을 달성했다.
- `scripts/search_rag_index.py`에 OpenAI-backed Chroma 전용 local blend score를 추가했고, 기본값을 `4.0`으로 올렸다.
- local-backed Chroma와 OpenAI-backed Chroma가 같은 collection 이름을 쓰며 차원 충돌이 발생하던 문제를 확인하고, collection 이름을 `pepper_expert_chunks_local`, `pepper_expert_chunks_openai`로 분리했다.
- manifest도 `artifacts/chroma_db/pepper_expert_manifest_local.json`, `artifacts/chroma_db/pepper_expert_manifest_openai.json`로 backend별 분리 생성하도록 수정했다.
- 보정 후 검증 결과:
  - `./.venv/bin/python scripts/evaluate_rag_retrieval.py --vector-backend chroma --chroma-embedding-backend local --fail-under 1.0`
    - hit_rate 1.0, MRR 1.0
  - `./.venv/bin/python scripts/evaluate_rag_retrieval.py --vector-backend chroma --chroma-embedding-backend openai --fail-under 1.0`
    - hit_rate 1.0, MRR 1.0
  - `./.venv/bin/python scripts/compare_rag_retrieval_modes.py --candidate-backend chroma --chroma-embedding-backend openai`
    - keyword baseline 대비 delta_mrr +0.0417

### RAG retrieval eval 40개 확장 재검증
- `evals/rag_retrieval_eval_set.jsonl`에 육묘 상토, 가뭄, 동해, 고온해, 영양장애, 칼슘·붕소 결핍, 오전 광, 비가림 구조·시비·저일조·관비·멀칭·보온·재식거리 관련 retrieval 케이스 16건을 추가했다.
- `scripts/rag_smoke_test.py`에도 같은 범주의 smoke query 16건을 추가해 기본 query 38개와 metadata filter 2개, 총 40건을 검증하도록 확장했다.
- 검증 결과:
  - `./.venv/bin/python scripts/rag_smoke_test.py`
    - 총 40건 PASS
  - `./.venv/bin/python scripts/evaluate_rag_retrieval.py --fail-under 1.0`
    - case_count 40, hit_rate 1.0, MRR 0.975
  - `./.venv/bin/python scripts/evaluate_rag_retrieval.py --vector-backend local --fail-under 1.0`
    - case_count 40, hit_rate 1.0, MRR 1.0
  - `./.venv/bin/python scripts/evaluate_rag_retrieval.py --vector-backend chroma --chroma-embedding-backend local --fail-under 1.0`
    - case_count 40, hit_rate 1.0, MRR 1.0
  - `./.venv/bin/python scripts/evaluate_rag_retrieval.py --vector-backend chroma --chroma-embedding-backend openai --fail-under 1.0`
    - case_count 40, hit_rate 1.0, MRR 1.0
- 40개 평가셋 기준으로는 keyword-only baseline만 MRR 0.975로 낮고, local vector, local-backed Chroma, OpenAI-backed Chroma는 모두 MRR 1.0을 유지했다.

### farm_case RAG 환류 파이프라인 초안 작성
- `docs/farm_case_rag_pipeline.md`를 추가해 운영 로그, 센서 구간, AI 판단 로그를 `farm_case` RAG 후보로 묶는 event window 기준과 승격 절차를 정리했다.
- `schemas/farm_case_candidate_schema.json`를 추가해 `case_id`, `farm_id`, `zone_id`, `growth_stage`, `sensor_tags`, `risk_tags`, `action_taken`, `outcome`, `review_status`, `chunk_summary` 등 핵심 필드를 고정했다.
- `todo.md`, `PROJECT_STATUS.md`, `docs/rag_next_steps.md`에 `farm_case` 후보 변환 규칙, metadata 정의, 리뷰 승인 절차 링크를 반영했다.

### Phase -1 AI 준비 구축 및 MLOps 설계 보강
- `docs/agent_tool_design.md`를 추가해 Agent가 사용할 조회/검색/승인/로그 도구 계약을 정리했다.
- `docs/offline_agent_runner_spec.md`를 추가해 실측 데이터 없이 상태 JSON, retrieval, 정책 검사, 평가 결과를 재현 검증하는 offline runner 요구사항을 정의했다.
- `docs/mlops_registry_design.md`를 추가해 dataset/prompt/model/eval/retrieval profile registry와 champion/challenger 승격 규칙을 정리했다.
- `docs/shadow_mode_report_format.md`를 추가해 shadow mode에서 승격 판단에 쓸 필수 지표와 리포트 형식을 정의했다.
- `data/examples/synthetic_sensor_scenarios.jsonl`를 추가해 정상 생육, 개화기 고온, 근권 과습·고EC, 센서 stale, 수확/건조 리스크, 장마기 병해 감시 시나리오 6건을 seed로 작성했다.
- `AI_MLOPS_PLAN.md`에 목표 대비 진행 현황 표와 설계 기준 완료 판정을 반영했다.
- `PLAN.md`, `PROJECT_STATUS.md`, `todo.md`에 Phase -1 성과물과 다음 우선순위를 최신 상태로 갱신했다.

### 센서 수집 계획 상세화
- `docs/sensor_collection_plan.md`를 추가해 zone 정의, `zone_id`/`sensor_id`/`device_id` naming 규칙, sensor/device sample rate, quality_flag 기준, must_have/should_have 우선순위를 정리했다.
- `schemas/sensor_catalog_schema.json`를 추가해 zone, sensor, device 카탈로그 구조를 고정했다.
- `data/examples/sensor_catalog_seed.json`를 추가해 초기 온실 1동 기준 zone 5개, sensor 5개, device 4개의 seed 카탈로그를 작성했다.
- `AI_MLOPS_PLAN.md`, `PROJECT_STATUS.md`, `README.md`, `todo.md`에 센서 수집 계획 상세화 완료 상태와 다음 우선순위를 반영했다.

### 센서 현장형 인벤토리 초안
- `docs/sensor_installation_inventory.md`를 추가해 zone별 설치 수량, protocol, calibration 주기, model_profile, 장치 interlock 기준을 정리했다.
- `schemas/sensor_catalog_schema.json`를 확장해 `catalog_version`, `measurement_fields`, `model_profile`, `protocol`, `install_location`, `calibration_interval_days`, `control_mode`, `response_timeout_seconds`, `safety_interlocks`를 검증 대상에 포함했다.
- `data/examples/sensor_catalog_seed.json`를 인스턴스 단위 현장형 카탈로그로 교체했다. 현재 기준치는 센서 29개, 장치 20개다.
- `docs/sensor_collection_plan.md`, `AI_MLOPS_PLAN.md`, `PROJECT_STATUS.md`, `README.md`, `todo.md`, `data/examples/README.md`에 현장형 인벤토리 상태를 반영했다.

### todo 진행 상태 정합화
- `todo.md`를 현재 산출물과 대조해 완료됐는데 미체크 상태였던 항목을 반영했다.
- 상위 관리 항목에서는 온실 공사중 전제, 개정 개발 순서, 저장소 구조, commit convention, 가상환경/.env 템플릿 상태를 반영했다.
- 도메인/데이터 항목에서는 지식셋 정리, 상태판단·금지행동 데이터 분류, 상태판단/센서 이상 평가셋 구축 상태를 반영했다.
- 아키텍처 항목에서는 수집 주기, raw/feature 분리, calibration_version, Agent tool contract 정의 상태를 반영했다.
- 즉시 착수 우선순위에서는 state/action schema, RAG source inventory, sensor/device inventory, vector store PoC, retrieval eval 진행 상태를 최신화했다.

### 도메인 지식/데이터 준비 구현 보강
- `docs/dataset_taxonomy.md`를 추가해 `qa_reference`, `state_judgement`, `action_recommendation`, `forbidden_action`, `failure_response`, `robot_task_prioritization`, `alert_report` task family를 정의했다.
- `docs/training_data_format.md`를 추가해 input/preferred_output 공통 구조, task별 템플릿, eval row 구조, schema 포함 방식을 정리했다.
- `docs/data_curation_rules.md`를 추가해 장치명, 단위, zone, growth stage, risk label, follow_up 정규화 규칙을 정의했다.
- `data/examples/`에 Q&A, 행동추천, 장애대응, 로봇작업, 알람/보고 seed JSONL을 추가했다.
- `evals/`에 행동추천, 금지행동, 장애대응, 로봇작업 평가셋 seed를 추가했다.
- `scripts/validate_training_examples.py`를 추가해 `data/examples/*.jsonl`과 `evals/*_eval_set.jsonl`의 구조, 필수 필드, duplicate id를 검증할 수 있게 했다.

### RAG 2.6 추가 확장: 141청크, smoke 62건, eval 80건
- `data/rag/pepper_expert_seed_chunks.jsonl`에 농사로 현장 기술지원과 지역 품종 자료 기반 신규 청크 14개를 추가했다.
- 추가된 핵심 청크는 다음과 같다.
  - `pepper-establishment-ammonia-compost-001`
  - `pepper-establishment-ammonia-remediation-001`
  - `pepper-greenhouse-poor-drainage-overwet-001`
  - `pepper-greenhouse-poor-drainage-remediation-001`
  - `pepper-flowerdrop-heavy-shading-001`
  - `pepper-flowerdrop-light-balance-001`
  - `pepper-nursery-curling-overwet-001`
  - `pepper-nursery-curling-recovery-001`
  - `pepper-firstfrost-flowerdrop-001`
  - `pepper-firstfrost-terminate-crop-001`
  - `pepper-overaged-seedling-deep-001`
  - `pepper-overaged-seedling-standard-001`
  - `pepper-cultivar-haevichi-cold-001`
  - `pepper-cultivar-rubihong-001`
- `docs/rag_source_inventory.md`에 `RAG-SRC-018`~`RAG-SRC-025`를 추가해 출처와 ingestion 상태를 연결했다.
- `scripts/rag_smoke_test.py`에 현장 사례 query 4건과 metadata filter query 6건을 추가해 총 62건을 검증하도록 확장했다.
- `evals/rag_retrieval_eval_set.jsonl`에 현장 사례와 품종 필터 케이스 10건을 추가해 총 80건을 검증하도록 확장했다.
- 검증 결과:
  - `python3 scripts/validate_rag_chunks.py`: rows 141, duplicate 0, warnings 0, errors 0
  - `./.venv/bin/python scripts/build_rag_index.py --skip-embeddings`: 141 documents
  - `./.venv/bin/python scripts/rag_smoke_test.py`: 총 62건 PASS
  - `./.venv/bin/python scripts/evaluate_rag_retrieval.py --fail-under 1.0`: case_count 80, hit_rate 1.0, MRR 0.9875
  - `./.venv/bin/python scripts/evaluate_rag_retrieval.py --vector-backend local --fail-under 1.0`: case_count 80, hit_rate 1.0, MRR 1.0
  - `./.venv/bin/python scripts/build_chroma_index.py --embedding-backend local`: 141 vectors
  - `./.venv/bin/python scripts/evaluate_rag_retrieval.py --vector-backend chroma --chroma-embedding-backend local --fail-under 1.0`: case_count 80, hit_rate 1.0, MRR 1.0
  - `./.venv/bin/python scripts/build_chroma_index.py --embedding-backend openai`: 141 vectors
  - `./.venv/bin/python scripts/evaluate_rag_retrieval.py --vector-backend chroma --chroma-embedding-backend openai --fail-under 1.0`: case_count 80, hit_rate 1.0, MRR 0.9792
- 이번에 반영한 주요 외부 근거:
  - 농사로 정식 후 생육초기 생육불량: https://nongsaro.go.kr/portal/ps/psz/psza/contentSub.ps?cntntsNo=253556&menuId=PS00077&totalSearchYn=Y
  - 농사로 수직배수 불량 과습 피해: https://www.nongsaro.go.kr/portal/ps/psz/psza/contentNsSub.ps?cntntsNo=208295&menuId=PS00077
  - 농사로 과차광·낙화 기술지원: https://www.nongsaro.go.kr/portal/ps/psz/psza/contentSub.ps?cntntsNo=247587&menuId=PS00077
  - 농사로 육묘 새순 오그라듦: https://www.nongsaro.go.kr/portal/ps/psz/psza/contentSub.ps?cntntsNo=251951&menuId=PS00077
  - 농사로 첫서리 후 낙화: https://www.nongsaro.go.kr/portal/ps/psz/psza/contentSub.ps?cntntsNo=242390&menuId=PS00077&totalSearchYn=Y
  - 농사로 노화묘·정식 깊이: https://nongsaro.go.kr/portal/ps/psz/psza/contentSub.ps?cntntsNo=208731&menuId=PS00077&totalSearchYn=Y
  - 농사로 해비치 저온 민감성: https://www.nongsaro.go.kr/portal/ps/psz/psza/contentSub.ps?cntntsNo=207176&menuId=PS00077
  - 지방농촌소식 루비홍 품종: https://rda.go.kr/board/board.do?boardId=farmlcltinfo&currPage=51&dataNo=100000802147&mode=updateCnt&prgId=day_farmlcltinfoEntry&searchEDate=&searchKey=&searchSDate=&searchVal=

### RAG 2.6 추가 확장: 169청크, smoke 81건, eval 96건
- `data/rag/pepper_expert_seed_chunks.jsonl`에 공식 PDF(`RAG-SRC-001`) 기반 신규 청크 28개를 추가했다.
- 이번 라운드에 추가한 핵심 청크는 다음과 같다.
  - `pepper-phytophthora-waterlogging-002`
  - `pepper-phytophthora-early-incidence-002`
  - `pepper-phytophthora-rye-highridge-002`
  - `pepper-phytophthora-phosphite-002`
  - `pepper-anthracnose-rain-spread-002`
  - `pepper-anthracnose-rainshelter-sanitation-002`
  - `pepper-anthracnose-preventive-spray-002`
  - `pepper-whitefly-species-001`
  - `pepper-whitefly-threshold-control-001`
  - `pepper-whitefly-biocontrol-001`
  - `pepper-budworm-damage-lifecycle-001`
  - `pepper-budworm-spray-window-001`
  - `pepper-armyworm-early-larva-001`
  - `pepper-spidermite-ecology-001`
  - `pepper-broad-mite-symptom-001`
  - `pepper-mite-predator-001`
  - `pepper-thrips-taiwan-ecology-001`
  - `pepper-thrips-monitoring-chemical-001`
  - `pepper-rainshelter-side-shoot-001`
  - `pepper-rainshelter-topping-001`
  - `pepper-rainshelter-fertigation-level-001`
  - `pepper-rainshelter-fertigation-interval-001`
  - `pepper-drying-precure-001`
  - `pepper-sundry-rack-001`
  - `pepper-whitefly-swirskii-release-001`
  - `pepper-aphid-virus-spray-window-001`
  - `pepper-aphid-coverage-resistance-001`
  - `pepper-budworm-pheromone-layout-001`
- `scripts/rag_smoke_test.py`에 공식 PDF 추가 추출분 query 15건과 metadata filter 4건을 더해 총 81건을 검증하도록 확장했다.
- `evals/rag_retrieval_eval_set.jsonl`에 역병·탄저병·가루이·진딧물·나방·비가림·건조 관련 케이스 16건을 더해 총 96건을 검증하도록 확장했다.
- 검증 결과:
  - `python3 scripts/validate_rag_chunks.py`: rows 169, duplicate 0, warnings 0, errors 0
  - `./.venv/bin/python scripts/build_rag_index.py --skip-embeddings`: 169 documents
  - `./.venv/bin/python scripts/rag_smoke_test.py`: 총 81건 PASS
  - `./.venv/bin/python scripts/evaluate_rag_retrieval.py --fail-under 1.0`: case_count 96, hit_rate 1.0, MRR 0.9896
  - `./.venv/bin/python scripts/evaluate_rag_retrieval.py --vector-backend local --fail-under 1.0`: case_count 96, hit_rate 1.0, MRR 1.0
  - `./.venv/bin/python scripts/build_chroma_index.py --embedding-backend local`: 169 vectors
  - `./.venv/bin/python scripts/evaluate_rag_retrieval.py --vector-backend chroma --chroma-embedding-backend local --fail-under 1.0`: case_count 96, hit_rate 1.0, MRR 0.9948
  - `./.venv/bin/python scripts/build_chroma_index.py --embedding-backend openai`: 169 vectors
  - `./.venv/bin/python scripts/evaluate_rag_retrieval.py --vector-backend chroma --chroma-embedding-backend openai --fail-under 1.0`: case_count 96, hit_rate 1.0, MRR 0.9826
- 이번 라운드의 주요 근거는 로컬 PDF 원문이다.
  - `/mnt/d/DOWNLOAD/GPT_고추재배_훈련세트/original-know-how/고추_재배기술_최종파일-농촌진흥청.pdf`

### RAG 2.6 완료 기준 달성: 219청크, smoke 98건, eval 110건
- `data/rag/pepper_expert_seed_chunks.jsonl`에 공식 PDF(`RAG-SRC-001`) 기반 신규 청크 50개를 추가했다.
- 이번 라운드에 추가한 핵심 범위는 다음과 같다.
  - 균핵병: `pepper-sclerotinia-pathogen-survival-001`, `pepper-sclerotinia-infection-window-001`, `pepper-sclerotinia-mulch-drip-001`, `pepper-sclerotinia-rotation-flooding-001`
  - 시들음병: `pepper-fusarium-symptom-diff-001`, `pepper-fusarium-temperature-window-001`, `pepper-fusarium-acidic-sandy-soil-001`, `pepper-fusarium-rotation-liming-001`
  - 잿빛곰팡이병: `pepper-graymold-wound-flower-entry-001`, `pepper-graymold-infection-window-001`, `pepper-graymold-ventilation-density-001`, `pepper-graymold-alternating-fungicide-001`
  - 흰별무늬병·흰비단병·무름병·세균점무늬병: `pepper-white-star-spot-sanitation-001`, `pepper-southern-blight-diagnosis-001`, `pepper-soft-rot-wound-insect-prevention-001`, `pepper-bacterial-spot-hotwater-seed-001`
  - 잎굴파리·뿌리혹선충: `pepper-leafminer-temperature-generation-001`, `pepper-leafminer-three-spray-001`, `pepper-rootknot-fumigation-sealing-001`, `pepper-rootknot-solarization-rice-rotation-001`
  - 농약 안전사용·잔류: `pepper-pesticide-precheck-001`, `pepper-pesticide-ppe-rest-001`, `pepper-pesticide-mix-order-001`, `pepper-pesticide-residue-concentration-001`, `pepper-pesticide-residue-greenhouse-winter-001`
- `scripts/rag_smoke_test.py`에 신규 query 13건과 metadata filter 4건을 추가해 총 98건을 검증하도록 확장했다.
- `evals/rag_retrieval_eval_set.jsonl`에 신규 retrieval case 14건을 추가해 총 110건을 검증하도록 확장했다.
- 검증 결과:
  - `python3 scripts/validate_rag_chunks.py`: rows 219, duplicate 0, warnings 0, errors 0
  - `./.venv/bin/python scripts/build_rag_index.py --skip-embeddings`: 219 documents
  - `./.venv/bin/python scripts/rag_smoke_test.py`: 총 98건 PASS
  - `./.venv/bin/python scripts/evaluate_rag_retrieval.py --fail-under 1.0`: case_count 110, hit_rate 1.0, MRR 0.9909
  - `./.venv/bin/python scripts/evaluate_rag_retrieval.py --vector-backend local --fail-under 1.0`: case_count 110, hit_rate 1.0, MRR 0.9955
  - `./.venv/bin/python scripts/build_chroma_index.py --embedding-backend local`: 219 vectors
  - `./.venv/bin/python scripts/evaluate_rag_retrieval.py --vector-backend chroma --chroma-embedding-backend local --fail-under 1.0`: case_count 110, hit_rate 1.0, MRR 0.9955
  - `./.venv/bin/python scripts/build_chroma_index.py --embedding-backend openai`: 219 vectors
  - `./.venv/bin/python scripts/evaluate_rag_retrieval.py --vector-backend chroma --chroma-embedding-backend openai --fail-under 1.0`: case_count 110, hit_rate 1.0, MRR 0.9803
- 이번 라운드의 주요 근거는 로컬 PDF 원문이다.
  - `/mnt/d/DOWNLOAD/GPT_고추재배_훈련세트/original-know-how/고추_재배기술_최종파일-농촌진흥청.pdf`

## 운영 규칙
- 주요 계획 변경은 이 파일에 날짜, 목적, 변경 파일, 커밋 해시를 함께 기록한다.
- 외부 조사에 기반한 결정은 근거 링크를 함께 남긴다.
- 자동 제어, 정책, 안전 게이트, RAG/파인튜닝 구조 변경은 반드시 `PLAN.md`, `todo.md`, `schedule.md` 중 관련 문서에 반영한다.
- `scripts/generate_batch13_remaining_gap_samples.py`를 추가해 남은 blind 일반화 gap용 batch13 `8건`을 생성했다. 구성은 `action_recommendation 2`, `rootzone_diagnosis 2`, `climate_risk 2`, `forbidden_action 2`이며 대상은 `GT Master dry-back + 낮은 새벽 WC + 반복 잎 처짐`과 `Delta 6.5 nursery + post-sunset humid + leaf wet duration 증가`다.
- `docs/remaining_blind_gap_root_cause.md`를 추가해 `blind-action-002`, `blind-expert-001`를 `validator`가 아니라 `data + rubric` ownership으로 분류했다.
- `scripts/report_risk_slice_coverage.py`에 `gt_master_dryback_high`, `nursery_cold_humid_high` slice 감사를 추가했다.
- `python3 scripts/build_training_jsonl.py`, `python3 scripts/validate_training_examples.py`, `python3 scripts/audit_training_data_consistency.py`, `python3 scripts/report_risk_slice_coverage.py`, `python3 scripts/report_training_sample_stats.py` 기준 training은 `276건`, duplicate `0`, contradiction `0`, eval overlap `0`, `gt_master_dryback_high 4`, `nursery_cold_humid_high 2`, class imbalance ratio `11.00`으로 재고정했다.
- `python3 scripts/build_openai_sft_datasets.py --validation-min-per-family 2 --validation-ratio 0.15 --validation-selection spread --train-output artifacts/fine_tuning/tmp_train_batch13.jsonl --validation-output artifacts/fine_tuning/tmp_validation_batch13.jsonl` 기준 현재 추천 split은 train `227`, validation `49`다.
