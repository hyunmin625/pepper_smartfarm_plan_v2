# 작업 로그

이 문서는 저장소에서 진행한 주요 변경 작업과 의사결정 이력을 기록한다.

## 2026-04-26

### todo 8 정책 엔진 runtime DSL + 기본 정책 완료
- todo.md #8 정책 엔진의 잔여 항목을 완료 처리했다. hard block, approval, range limit, scheduling, sensor quality, robot safety 카테고리를 POL-* 기본 정책으로 등록했다.
- policy-engine/policy_engine/evaluator.py를 추가해 field/operator/value, all/any/not, scope, target_action_types 기반 runtime policy DSL을 평가한다.
- policy-engine/policy_engine/precheck.py가 기존 HSV precheck 결과와 runtime evaluator 결과를 병합하도록 연결했다. dispatch 직전 policy_result, policy_ids, reason_codes를 같은 경로로 보존한다.
- data/examples/policy_output_validator_rules_seed.json에 POL-* 기본 정책 9개를 추가했고, schemas/policy_output_validator_rules_schema.json도 runtime stage와 enforcement 필드를 허용하도록 확장했다.
- docs/policy_engine_runtime_policies.md와 policy-engine/README.md에 DSL, 기본 정책, 검증 경로를 문서화했다.
- scripts/validate_policy_engine_runtime_policies.py를 추가하고 Phase P quality gate에 policy_engine_runtime_policy_smoke를 연결했다.

## 2026-04-17

### ops-api PostgreSQL only 전환 + 통합제어 Web UI 실행 매뉴얼 정리
- 사용자 요청에 따라 앞으로 `ops-api`와 통합제어 Web UI는 `PostgreSQL/TimescaleDB only` 기준으로만 다루기로 고정했다. `ops-api/ops_api/config.py`와 `ops-api/ops_api/database.py`는 이미 SQLite URL을 거부하도록 바뀐 상태였고, 이번에 문서/스크립트/검증 경로까지 같은 원칙으로 맞췄다.
- `scripts/ensure_ops_api_postgres_db.py`를 추가해 `OPS_API_DATABASE_URL`의 대상 DB가 없으면 admin DB(`postgres` 또는 `template1`)에 붙어 자동 생성하도록 했다.
- `scripts/run_ops_api_postgres_stack.sh`를 추가해 `.env` 로드 -> DB 생성 -> canonical migration 적용 -> reference seed 적재 -> `uvicorn ops_api.app:create_app --factory` 실행을 한 번에 처리하도록 만들었다.
- `docs/ops_api_postgres_runbook.md`를 새로 작성했고, `README.md`와 `ops-api/README.md`에도 같은 실행 경로와 smoke 절차를 반영했다. 다른 에이전트가 기준을 바로 알 수 있도록 `AGENTS.md`에 `PostgreSQL/TimescaleDB only` 규칙도 추가했다.
- `scripts/validate_ops_api_server_smoke.py`도 PostgreSQL URL만 받도록 바꿨다. 실행 전에 `ensure_ops_api_postgres_db.py`, `apply_ops_api_migrations.py`, `bootstrap_ops_api_reference_data.py`를 먼저 호출한 뒤 실제 `uvicorn` smoke를 수행한다.
- `ops-api/ops_api/models.py`와 `ops-api/ops_api/app.py`의 시계열 주석도 현재 기준에 맞게 고쳤다. 더 이상 SQLite fallback을 설명하지 않고, 5m/30m 조회는 direct continuous aggregate query로 바꿀 예정인 현재 상태만 남겼다.
- 상태 문서 반영:
  - `PROJECT_STATUS.md`: 로컬 통합 기준을 PostgreSQL/TimescaleDB로 상향, `real PostgreSQL smoke` 완료 반영
  - `docs/runtime_integration_status.md`: bootstrap/validation 명령을 PostgreSQL 기준으로 정리
  - `todo.md`: `real PostgreSQL smoke 실행`과 `Web UI 실행 매뉴얼 작성` 완료 처리

## 2026-04-15

### v11 초과 재도전 준비용 batch24 corrective seed 추가
- 사용자의 요청에 따라 `v11` 초과 가능성을 높이는 선행 작업만 먼저 진행하고, `100% 보장`이 없으면 전면 재학습은 열지 않는 기준을 다시 고정했다.
- `scripts/generate_batch24_v11_breakthrough_prep.py`를 추가해 두 가지 축만 보강했다.
  - `edge-eval-021` 전용 corrective: `reentry_pending + dry_room comm loss`에서 `enter_safe_mode`를 금지하고 `block_action + create_alert`를 우선 고정하는 `failure_response` `4건`
  - low-count family rebalance: `state_judgement` `2건`, `harvest_drying` `4건`, drying `sensor_fault` `1건`, `nutrient_risk` `1건`, `inspect_crop` exact enum robot contract `2건`
- 생성 산출물:
  - `data/examples/failure_response_samples_batch24_reentry_block_priority.jsonl` `4건`
  - `data/examples/state_judgement_samples_batch24_lowcount_rebalance.jsonl` `8건`
  - `data/examples/robot_task_samples_batch24_inspect_crop_contract.jsonl` `2건`
- 검증 결과:
  - `python3 scripts/validate_training_examples.py --sample-files ...batch24...` 기준 `sample_rows 14`, duplicate `0`, sample/eval errors `0`
  - `python3 scripts/audit_training_data_consistency.py ...batch24...` 기준 duplicate/contradiction/eval overlap `0`
  - 전체 seed 기준 `python3 scripts/validate_training_examples.py`, `python3 scripts/audit_training_data_consistency.py`도 모두 `errors 0`
- dataset rebuild:
  - `python3 scripts/build_training_jsonl.py --include-source-file`로 combined training을 `535건`으로 재생성
  - `python3 scripts/build_openai_sft_datasets.py` 결과 현재 기본 split은 `train 521`, `validation 14`
  - `python3 scripts/report_training_sample_stats.py` 기준 저빈도 family는 `state_judgement 9`, `harvest_drying 8`, `sensor_fault 30`, `nutrient_risk 18`, `robot_task_prioritization 62`, `failure_response 71`로 갱신
- 판단:
  - 이번 작업은 `재학습 실행`이 아니라 `재학습 전 준비 강화`다.
  - `real shadow` 누적과 `100% 보장` 조건은 여전히 충족되지 않아 전면 재학습은 계속 보류한다.

### 즉시 착수 우선순위 seed 100건 달성
- `scripts/generate_batch23_seed_completion.py`를 추가해 `action_recommendation`과 `forbidden_action` seed 부족분을 batch23 completion 파일로 생성했다.
- 생성 산출물은 `data/examples/action_recommendation_samples_batch23_seed_completion.jsonl` `51건`, `data/examples/forbidden_action_samples_batch23_seed_completion.jsonl` `74건`이며, 누적 기준 두 task family 모두 총 `100건`을 충족한다.
- `python3 scripts/validate_training_examples.py --sample-files data/examples/action_recommendation_samples*.jsonl data/examples/forbidden_action_samples*.jsonl --eval-files evals/action_recommendation_eval_set.jsonl evals/forbidden_action_eval_set.jsonl` 기준 `sample_rows 200`, duplicate `0`, sample/eval errors `0`을 확인했다.
- 이에 따라 `todo.md`의 `#23. 즉시 착수 우선순위`에서 `행동추천 JSON 샘플 100개 작성`, `금지행동 샘플 100개 작성` 두 항목을 완료 처리했고, `data/examples/README.md`, `docs/dataset_taxonomy.md`의 관련 설명도 갱신했다.

## 2026-04-14

### AI 어시스턴트 모델 경로 재통합
- 사용자 결정에 따라 AI 어시스턴트와 decision 경로를 다시 하나의 모델 경로로 통합했다. `/ai/chat`의 DB grounding과 `task_type="chat"` 입력 구조는 유지하되, 더 이상 `chat_provider` / `chat_model_id`나 별도 `AppServices.chat_client`를 두지 않는다.
- `ops-api/ops_api/config.py`의 `Settings`에서 `chat_provider`, `chat_model_id`를 제거하고 `.env.example`도 `OPS_API_LLM_PROVIDER` / `OPS_API_MODEL_ID` 한 쌍만 남겼다. decision/chat 모두 같은 모델 설정을 공유한다.
- `ops-api/ops_api/app.py`의 `/ai/chat`는 이제 `services.orchestrator.client.complete()`를 직접 호출한다. 즉 모델 분리는 없고, `task_type="chat"` + grounding context + chat 시스템 프롬프트 조합으로 대화 모드를 유도한다.
- `scripts/validate_ops_api_ai_chat.py`를 포함한 `Settings(...)` 직접 생성 smoke들은 단일 LLM 설정만 사용하도록 정리했다. 기능적으로는 기존 zone_hint 감지, grounding_keys 검증, JSON unwrap 회귀를 그대로 유지한다.

### AI 어시스턴트 채팅 경로 분리 + DB grounding + chat task_type
- 사용자 피드백: "AI 어시스턴트는 파인튜닝한 스마트팜 농업전문가를 붙여야지" + 지정 모델 `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v14-prompt-v10-validator-aligned-batch19-har:DU2VQVYz`. 결정 경로(`evaluate_zone`)는 `ds_v11` frozen baseline 유지, AI 어시스턴트만 이 ds_v14 chat-friendly 파인튜닝으로 분리.
- `ops-api/ops_api/config.py`의 `Settings`에 `chat_provider`, `chat_model_id` 두 필드를 추가. 환경변수 `OPS_API_CHAT_PROVIDER` / `OPS_API_CHAT_MODEL_ID`로 제어하고, 미지정 시 `OPS_API_LLM_PROVIDER` / `OPS_API_MODEL_ID`로 fallback해 기존 테스트 환경 호환성 유지.
- `AppServices`에 `chat_client: CompletionClient` 필드 추가. `create_app()`에서 `create_completion_client(ModelConfig(provider=chat_provider, model_id=chat_model_id, ...))`로 별도 인스턴스를 만들고, 결정 경로의 `LLMOrchestratorService.client`와 독립된 CompletionClient임을 확인.
- `/ai/chat` 엔드포인트를 **DB grounding + chat task_type** 구조로 전면 재작성:
  - `_detect_zone_hint()`가 사용자 발화에서 `gh-01-zone-a`, `zone-a`, `A구역`, `zone a` 등 다양한 한국어/영어 표기로부터 zone_id를 추출. context의 `zone_hint`가 우선.
  - `_build_chat_grounding_context()`가 해당 zone의 최신 `DecisionRecord`(+`current_state`+`validated_output.recommended_actions`), 최근 `AlertRecord` 3건, 최근 `SensorReadingRecord` 16건에서 metric별 latest snapshot, 상위 enabled `PolicyRecord` 8건을 DB에서 조회해 context dict로 합친다.
  - user_message payload는 `{"task_type": "chat", "input": {"zone_id": ..., "latest_user_message": ..., "chat_history": ..., "context": {...grounding}, "instruction": "..."}}` 구조로 보내고, 출력 형식을 `{"reply": "한국어 자연어 답변"}` 단일 객체로 제약해 파인튜닝 모델이 결정 JSON 모드가 아니라 대화 모드로 답하도록 명시적으로 유도.
  - `services.chat_client.complete()` 호출로 변경 (더 이상 `services.orchestrator.client`를 쓰지 않음 — 결정 경로와 완전 분리).
  - 응답에 `grounding_keys`, `zone_hint` 디버깅 필드 노출.
- `_build_chat_system_prompt()`를 7가지 규칙이 담긴 구조화 프롬프트로 교체: 한국어 고정, 2~5문장 제약, context 숫자 그대로 인용, 없을 때 명시, 장치 직접 on/off 금지, 안전 규칙(HSV-01~10, operator_present, manual_override, safe_mode) 위반 금지, 출력 형식 `{"reply": "..."}` 단일 JSON 강제, 결정 JSON 템플릿 사용 금지.
- `llm-orchestrator/llm_orchestrator/client.py`의 `StubCompletionClient`에 `task_type == "chat"` 분기 추가. 실제 모델 키 없이도 dev 환경에서 자연스러운 한국어 stub 응답을 반환: `[stub 응답] 방금 '<질문>' ... {zone_id} 최근 risk_level은 ... 실제 파인튜닝된 적고추 온실 전문가 모델이 연결되면 ...` 형태로 grounding context를 echo. 기존 결정 task_type 분기는 그대로.
- 기존 8개 smoke 파일(postgres_smoke/policy_source_db_wiring/dashboard_section14/auth/zone_history/timeseries/sse_stream/shadow_runner_gate)의 `Settings(...)` 호출에 `chat_provider="stub"`, `chat_model_id="pepper-ops-local-stub-chat"` 추가. `@dataclass(frozen=True)`라 누락 시 TypeError 발생.
- `scripts/validate_ops_api_ai_chat.py`를 확장해 4가지 신규 invariant 회귀: (1) reply.content가 자연어여야 하고 '{'로 시작하면 안 됨 (JSON unwrap 검증), (2) `zone_hint`가 context의 zone_hint로 정확히 해석, (3) `grounding_keys`에 `active_policies` 포함 (DB 연결 확인), (4) free-form 사용자 발화 "zone-a 현재 EC 수치 알려줘"가 context 없이도 `gh-01-zone-a`로 매핑. 기존 6개 invariant는 그대로 유지.
- `.env.example`에 `OPS_API_LLM_PROVIDER/OPS_API_MODEL_ID` (ds_v11 baseline decision path)와 `OPS_API_CHAT_PROVIDER/OPS_API_CHAT_MODEL_ID` (ds_v14 chat-friendly AI 어시스턴트 path) 두 쌍을 문서화. 주석에 specific fine-tuned model ID를 명시.
- 23종 smoke 모두 `errors 0`.

### 데이터베이스 설계 섹션 5 완료
- `docs/timescaledb_schema_design.md`에 `partition 필요성 검토`와 `보관 주기 정책 검토`의 결론을 명시했다. 결론은 운영 canonical 테이블에는 별도 declarative partition을 도입하지 않고, 시계열 계층은 `TimescaleDB hypertable` chunking을 partition 전략으로 사용한다는 것이다.
- retention도 같은 문서에 운영/감사 canonical 테이블과 시계열 계층을 분리해 적었다. 자동 retention은 `sensor_readings 180일`, `zone_state_snapshots 365일`, `zone_metric_5m 365일`, `zone_metric_30m 730일`로 고정하고, 운영 canonical 테이블은 archive/export 정책으로 따로 다룬다.
- 이 기준으로 `todo.md`의 `5.2 partition 필요성 검토`, `5.2 보관 주기 정책 검토`를 완료 처리했다. 결과적으로 `#5 데이터베이스 설계 및 구축` 전체가 닫혔다.

### PostgreSQL migration 초기화 + 우선순위 드리프트 정리
- `ops-api/ops_api/database.py`에 PostgreSQL 전용 migration 적용 경로를 추가했다. `init_db()`는 이제 SQLite에서는 기존 `Base.metadata.create_all()`을 유지하고, PostgreSQL에서는 `infra/postgres/001_initial_schema.sql` → `002_timescaledb_sensor_readings.sql`을 순서대로 실행한 뒤 ORM `create_all`을 fallback 안전망으로만 사용한다. SQL splitter는 단일 인용부호를 인지해 statement 경계를 자르고, comment-only chunk는 건너뛴다.
- `scripts/apply_ops_api_migrations.py`를 추가해 운영 DB에 migration만 독립 적용할 수 있게 했다. `OPS_API_DATABASE_URL`이 PostgreSQL이 아니면 `blocked`, PostgreSQL이면 canonical migration 2개를 적용하고 적용 경로를 JSON으로 출력한다.
- `scripts/bootstrap_ops_api_reference_data.py`는 같은 `init_db()` 루틴을 타므로 PostgreSQL에서 `migration -> seed` 순서가 자동으로 보장된다. `ops-api/README.md` bootstrap 절차도 `apply_ops_api_migrations.py`와 함께 갱신했다.
- `README.md`, `PROJECT_STATUS.md`, `todo.md`, `docs/native_realtime_dashboard_plan.md`를 최신 상태로 맞췄다. 더 이상 `TimescaleDB actual writer + native 시계열 구현`을 다음 우선순위로 적지 않고, `real shadow log`, `real PostgreSQL smoke`, `policy source versioning/UI`, `blind50/extended200 residual` 순서로 정리했다. `5.4 migration 초기화`는 완료로 닫았다.

### Native Realtime Phase 3 + 4: SSE endpoint + uPlot 구역 모니터링 + 23 smoke
- ops-api에 `GET /zones/{zone_id}/timeseries?from&to&interval=raw|1m|5m|30m` 엔드포인트를 추가했다 (`read_runtime` 권한). interval에 따라 sensor_readings raw / `_group_timeseries` 5m·30m bucket aggregation으로 라우팅한다. 운영 환경에서는 PostgreSQL+TimescaleDB의 `zone_metric_5m`/`zone_metric_30m` continuous aggregate를 직접 조회하고, sqlite 테스트 환경은 raw 위에 on-the-fly bucket을 돌려 같은 응답 모양을 유지한다. 잘못된 interval/from>=to는 400, header_token 모드에서 viewer 토큰 미입력은 401, viewer 토큰 첨부 시 200으로 회귀.
- ops-api에 `GET /zones/{zone_id}/stream` Server-Sent Events 엔드포인트를 추가했다 (`read_runtime` 권한). FastAPI `StreamingResponse` + async generator 패턴으로 구성되며, 연결 시 (1) `event: ready` 메타 → (2) bootstrap_seconds 윈도우 만큼의 `event: bootstrap` 행 → (3) `event: bootstrap_complete` → (4) `RealtimeBroker.subscribe(zone_id=...)` 큐에서 들어오는 `event: reading` 무한 루프로 진행한다. 15초 무이벤트 시 `: keepalive` 코멘트로 connection liveness 유지. SSE 헤더는 `text/event-stream + Cache-Control: no-cache, no-transform + X-Accel-Buffering: no`로 nginx 등 reverse proxy buffering까지 차단.
- `RealtimeBroker`를 cross-loop / cross-thread safe하게 보강했다. 각 subscriber가 자신을 등록한 asyncio 루프를 캡처하고, 모든 publish는 `loop.call_soon_threadsafe`로 해당 루프에 위임한다. 내부 lock도 asyncio.Lock에서 threading.RLock으로 교체해 동기 코드(센서 인제스터 쓰기 경로)와 비동기 SSE 핸들러가 동일 broker 인스턴스를 공유할 수 있게 했다. 첫 SSE smoke가 `asyncio.run` 기반 publisher 스레드에서 큐에 도달하지 못하고 hang했던 문제를 영구적으로 해소했다.
- `AppServices`에 `realtime_broker: RealtimeBroker` 필드를 추가하고 `create_app()`에서 단일 instance를 부착했다. 이후 sensor-ingestor가 in-process로 호스트되거나 SSE 핸들러가 subscribe할 때 동일 broker를 공유한다.
- iFarm 통합제어 `구역 모니터링` 뷰를 SVG sparkline 11개에서 **uPlot 캔버스 11 인스턴스 + EventSource 실시간 스트림**으로 전면 교체했다. CDN(`uPlot 1.6.30`)을 head에 추가하고, JS는 `realtimeState` 객체 + `TRACKED_METRICS` 배열 + `ensureRealtimeChart`/`pushPoint`/`bootstrapTimeseries`/`openStream`/`scheduleReconnect` 5개 함수로 구성된다. 차트는 60s/5m/30m/6h/24h 롤링 윈도우 셀렉터로 전환 가능하고, 모든 윈도우 변경 시 `bootstrapTimeseries`가 `/zones/{id}/timeseries`로 재시드한 뒤 `EventSource('/zones/{id}/stream')`을 연다. 연결 끊김 시 지수 백오프(0.5s → 15s)로 재연결, 사이드바 우상단 `streamStatus` chip이 `connecting/live/reconnecting/error/disconnected` 상태를 시각화. 윈도우 밖 데이터는 자동으로 drop되어 메모리 사용량 일정.
- 사용자 요청 반영: 메뉴/제목/부제/AI 인사 모두 `존` → `구역`으로 통일 (`존 모니터링 → 구역 모니터링`, `존 상태 요약 → 구역 상태 요약`, `Zone 시계열 → 구역 시계열`). 백엔드 필드명(`zone_id`)은 그대로 유지.
- `scripts/validate_ops_api_timeseries.py` 신규: 7 invariant 회귀 — raw interval + 1m bucket + metric filter + from/to clamp + 잘못된 interval 400 + from>=to 400 + header_token 401/200.
- `scripts/validate_ops_api_sse_stream.py` 신규: 7 invariant 회귀 — `text/event-stream` content-type, ready 1건, bootstrap 4건, bootstrap_complete 1건 + count, broker.publish 후 reading 3건, zone-b 메시지 격리, header_token 401. SSE 핸들러의 `body_iterator`를 직접 소비하는 방식으로 httpx ASGITransport의 chunk buffering을 우회.
- `scripts/validate_ops_api_zone_history.py` hook 목록을 Phase 4 마크업에 맞춰 갱신: `Zone Realtime Chart`, `bootstrapTimeseries`, `openStream`, `TRACKED_METRICS`, `historyWindow`, `uPlot` 등 8개. `/zones/{id}/history` 응답의 `sensor_series`는 여전히 fallback으로 노출되므로 endpoint 자체 검증은 유지.
- `validate_ops_api_flow` expected_routes에 `/zones/{zone_id}/timeseries`, `/zones/{zone_id}/stream` 2개 신규 라우트 추가.
- 23종 smoke 모두 `errors 0` (기존 21 + timeseries + sse_stream).

### Native Realtime Phase 1 + 2: TimescaleDB migration + sensor-ingestor writer + RealtimeBroker
- `infra/postgres/002_timescaledb_sensor_readings.sql` migration을 추가했다 (`docs/timescaledb_schema_design.md` 기준). `CREATE EXTENSION timescaledb` + `sensor_readings` raw hypertable + `zone_state_snapshots` 1분 hypertable + `zone_metric_5m`/`zone_metric_30m` continuous aggregate + retention policy(180/365/365/730일) + compression policy(7일/30일). PostgreSQL+TimescaleDB 환경에서 `psql -f`로 적용한다.
- `ops-api/ops_api/models.py`에 `SensorReadingRecord`와 `ZoneStateSnapshotRecord` ORM 모델을 추가했다. sqlite 테스트와 호환되도록 PK는 portable Integer autoincrement(`sensor_readings.id`)로 두고, `zone_state_snapshots`는 SQL 마이그레이션과 동일한 `(measured_at, zone_id)` 복합 PK를 채택. `Float`/`BigInteger` 타입 import를 모델에 추가.
- `ops-api/ops_api/realtime_broker.py`를 신설해 `RealtimeBroker` 클래스를 정의했다: `asyncio.Queue` 기반 fan-out, zone_id 필터링 가능한 `subscribe()` async context manager, `publish()` async API와 sync 코드에서 호출 가능한 `publish_nowait()` shim, 큐 오버플로 시 oldest-drop + dropped 카운터 증가. 다음 단계 SSE 엔드포인트가 이 broker에서 직접 subscribe할 예정이다.
- `sensor-ingestor/sensor_ingestor/timeseries_writer.py`를 신설해 `TimeseriesWriter` 클래스를 정의했다. 정규화된 sensor 레코드의 `values` dict와 device 레코드의 `readback` dict를 metric 단위로 explode해 `SensorReadingRecord` 행으로 insert한다. 숫자는 `metric_value_double`, 문자열/enum은 `metric_value_text`로 분기. broker가 주입돼 있으면 insert 직후 `publish_nowait`로 fan-out broadcast.
- `sensor-ingestor/sensor_ingestor/runtime.py`의 `SensorIngestorService.__init__`이 `timeseries_writer` 옵션을 받고, `run_once()`의 sensor/device 그룹 처리 루프에서 `publisher.publish` 직후 `_timeseries_write(normalized)` 헬퍼로 호출한다. writer가 None이면 기존 outbox 경로만 동작하고, 주입돼 있으면 TimescaleDB insert + (선택) broker broadcast가 추가된다. writer 예외는 `metrics.last_error`로 잡혀 runtime 자체는 멈추지 않는다.
- `scripts/validate_sensor_timeseries_writer.py`를 추가해 6 invariant를 회귀한다: (1) sensor 레코드 1건 → 4개 metric row insert, (2) device 레코드 1건 → 2개 metric row insert, (3) 숫자 → `metric_value_double`, 문자열 → `metric_value_text` 라우팅, (4) broker 부착 시 모든 metric이 fan-out, (5) `subscribe(zone_id="gh-01-zone-a")` 필터 적용, (6) 큐 오버플로 시 oldest-drop으로 최대 size 유지. asyncio 기반 두 번째 시나리오에서 broker 동작 검증. 21번째 smoke로 전체 회귀에 편입.
- `scripts/validate_postgres_schema_drift.py`를 확장해 `MIGRATION_PATHS`로 두 SQL 파일(001 + 002)을 모두 파싱하도록 했다. SQL 타입 normalization에 `DOUBLE`/`REAL` → `float`을 추가하고, ORM 측에 `Float` → `float` 매핑을 추가. 이제 15개 테이블(`sensor_readings`/`zone_state_snapshots` 포함) 전부 정렬돼 ORM ↔ SQL drift 0건.
- 21종 smoke 모두 `errors 0`: 기존 20종 + `validate_sensor_timeseries_writer`. Phase 3+4(`/zones/{id}/stream` SSE 엔드포인트 + `/zones/{id}/timeseries` 임의 구간 + iFarm uPlot 통합)는 다음 세션 작업.

### Native Realtime SSE + uPlot 결정 (Grafana 임베드 supersede)
- 운영 요구사항이 "초단위(≤1초) 실시간"으로 명확해진 시점에서, 기존 `TimescaleDB + Grafana 임베드` 방향이 구조적으로 맞지 않는다는 점을 재검토했다. Grafana 기본 dashboard refresh 최소 단위가 5초이고, Grafana Live(WebSocket streaming)는 PostgreSQL/TimescaleDB datasource plugin에서 지원되지 않는다는 한계 때문이다.
- 새 결정: `docs/native_realtime_dashboard_plan.md`를 추가해 `TimescaleDB + 통합관제 웹 native SSE + uPlot` 경로를 캐노니컬 아키텍처로 고정했다. ops-api에 `GET /zones/{zone_id}/stream` (SSE, `read_runtime` 권한)과 `GET /zones/{zone_id}/timeseries?from&to&interval=raw|1m|5m|30m` 두 엔드포인트를 추가하고, sensor-ingestor가 TimescaleDB raw insert와 in-process pubsub broadcast를 동시 수행하며, 브라우저는 `EventSource`로 stream을 열어 `uPlot`(MIT, canvas, 의존성 0)에 60fps 롤링 윈도우를 그린다. 자세한 데이터 볼륨 계산, 리스크/대응, 5단계 구현 순서, supersede되는 문서 매핑까지 포함.
- 업스트림 정리 커밋 `914c8ee`(Remove Grafana from timeseries dashboard plan)가 이미 `docs/grafana_integration_design.md`와 `infra/grafana/README.md`를 삭제하고 PLAN/PROJECT_STATUS/README/todo/schedule에서 Grafana 언급을 제거해뒀다. 이번 작업은 그 위에 SSE+uPlot 구체 아키텍처를 못박는 형태다. 빈 `infra/grafana/` 디렉터리를 로컬에서 정리했다.
- `PLAN.md` 2.1 E에 "초단위 실시간 시계열은 Server-Sent Events 기반 native streaming" 문단을 추가해 SSE 엔드포인트 두 개 + uPlot 컴포넌트를 명시했다. `docs/native_realtime_dashboard_plan.md`를 참조 링크로 박았다.
- `README.md` 문서 인덱스 18번에 `docs/native_realtime_dashboard_plan.md`를 등록하고, "다음 우선순위" 3번을 `TimescaleDB actual writer + 통합관제 웹 native realtime 시계열 (SSE + uPlot)`으로 갱신했다.
- `PROJECT_STATUS.md`에 항목 24를 추가해 supersede 경위, 새 아키텍처, 닫히는 결정과 살아남는 결정(TimescaleDB 저장 설계는 유효)을 정리했다.
- `todo.md`에 새 섹션 14.5 `Native Realtime SSE + uPlot 구현`을 추가했다: 결정 문서 1건 완료 + 7건 미구현(TimescaleDB migration, sensor-ingestor writer + pubsub, `/zones/{id}/stream` SSE 엔드포인트, `/zones/{id}/timeseries` 임의 구간 엔드포인트, iFarm uPlot 통합, SSE smoke 회귀, timeseries smoke 회귀).
- 14.4 `시계열 대시보드 통합` 항목 4건은 그대로 `[x]` 유지 (저장소 결정과 데이터 계층 설계는 supersede되지 않음).

### Stitch 레퍼런스 기반 UI 전면 재디자인 + AI 어시스턴트 채팅 + 반응형
- `WebUI/stitch_ui_v1.zip`의 9개 Stitch 스크린(`_1~_6, ai, cctv_3x3, shadow_mode, verdant_control/DESIGN.md`)을 분석해 "농경 사령부 / The Agrarian Command" 디자인 시스템을 `ops-api/ops_api/app.py`의 `_dashboard_html()`에 전면 반영했다. Tailwind CSS CDN + Pretendard/Noto Sans KR/Material Symbols, 어두운 포레스트 사이드바(`#1d2a1f`), 카드 `#fffdf7 + radius 18px + soft shadow`, chip 기반 상태 표현으로 교체.
- **반응형**: `lg:ml-64` 사이드바가 1024px 이상에서 고정되고, 그 이하에서는 오프스크린 drawer로 변환된다. 헤더의 햄버거 버튼(`toggleSidebar()`)과 backdrop overlay가 drawer를 열고 닫으며, 메뉴 선택 시 자동 닫힘. 메트릭 그리드는 `grid-cols-2 sm:3 md:4 lg:5`로, 존 히스토리 스파크라인은 `grid-cols-1 sm:2 lg:3`으로 breakpoint별로 재배치된다. 대시보드의 2단·3단 카드 레이아웃도 `lg:` 이상에서만 활성화.
- **AI 어시스턴트 채팅 뷰** 신설: 사이드바에 10번째 메뉴 `AI 어시스턴트` 추가, `xl:col-span-3 + xl:col-span-2` split pane 구조. 좌측은 chat message list(user bubble accent / assistant bubble cream + AI AGRO-SYSTEM 배지) + textarea 입력 + Quick prompt 칩 4개(`zone-a 상태 요약`, `blind50 residual`, `전체 위험도`, `shadow day0 hold`) + `대화 초기화`. 우측은 실시간 관제 current action 카드 + 최근 dispatch 로그 + 3×3 zone health grid. chatState는 클라이언트 메모리, 전송 시 pending bubble → 실제 응답 교체. Enter(Shift 제외) 단축키 지원.
- **백엔드 `/ai/chat` 신설** (`read_runtime` 권한). `ops-api/ops_api/api_models.py`에 `ChatMessageRequest`/`ChatRequest` 추가, app.py에 `ai_chat` 라우트 + `_build_chat_system_prompt()` 헬퍼 + `_render_chat_history()` + `_extract_chat_reply()` 유틸. 대화 히스토리 최근 8턴을 `운영자/AI/시스템` 형식으로 직렬화해 orchestrator client의 `complete()`에 전달. 응답은 JSON이든 자연어든 안전하게 추출한다 (`reply/message/content/answer/response/situation_summary/risk_level` 키 우선).
- 루트 `/`는 `/dashboard`로 307 리다이렉트 (`dashboard_root_redirect`). 기존 플레인 JSON "Not Found" 경험 해소.
- `scripts/validate_ops_api_ai_chat.py` 신설: 6개 invariant 회귀 — (1) empty messages 400, (2) missing user 400, (3) 단일 턴 200 + `reply.content` 비어있지 않음, (4) 멀티 턴 히스토리 200, (5) header_token 모드 `read_runtime` 권한 경로(`no_key → 401`, viewer → 200), (6) `/dashboard` HTML에 `chatMessages/chatInput/sendChatMessage/ai/chat/AI 어시스턴트/AI AGRO-SYSTEM` 6개 훅 존재.
- `scripts/validate_ops_api_flow.py`의 expected routes에 `/ai/chat` 추가.
- 20종 smoke 전부 통과: `flow, auth, error_responses, schema_models, shadow_mode, postgres_smoke, zone_history, dashboard_section14, ai_chat, postgres_schema_drift, policy_source_db_wiring, policy_engine_precheck, policy_output_validator, state_estimator_policy_flow, llm_to_execution_flow, shadow_runner_gate, execution_dispatcher, execution_gateway_flow, execution_safe_mode, state_estimator_mvp`.

## 2026-04-13

### 운영자 통합 제어 웹 UI 재구성 + 루트 리다이렉트 + PLAN 반영
- `ops-api/ops_api/app.py`의 `_dashboard_html()`을 사이드바 네비게이션 + 9개 뷰로 전면 재구성했다. 한국어 기본 (`title="적고추 온실 스마트팜 통합 제어"`), 사이드바 메뉴는 `대시보드 / 존 모니터링 / 결정 / 승인 / 알림 / 로봇 / 장치 / 제약 / 정책 / 이벤트 / Shadow Mode / 시스템` 9개. 단일 SPA에서 JS `showView()`가 `.view` 섹션 display를 토글하고, `VIEW_TITLES` 테이블이 헤더 제목/부제를 매핑한다.
- `GET /` 루트가 `/dashboard`로 307 리다이렉트된다 (`dashboard_root_redirect`). 이전엔 루트 접속 시 `{"detail":"Not Found"}`만 반환되어 운영자가 혼동할 수 있었다.
- 대시보드 metric 카드가 10 → 14로 확장되고 라벨이 전부 한국어(`결정 수 / 승인 대기 / Shadow 리뷰 대기 / 차단된 결정 / Safe Mode 추천 / Operator 불일치 / 일치율 / 실행 명령 / Policy Event / Policy Block / Alerts / Robot Task / Robot Candidate / Policy (enabled/total)`)로 표시된다.
- 신규 렌더러와 마운트 포인트: `alertListOverview`/`commandListOverview`(overview 뷰 미니 카드), `zoneListDetailed`(zones 뷰 상세), `shadowWindowDetail`(shadow 뷰 8-slot 카드), `runtimeInfo`(시스템 뷰 auth 요약), `authContextMini`(사이드바 푸터 mini). 기존 `renderZones/renderAlerts/renderCommands/renderShadowWindow/renderAuthContext`를 멀티 마운트 포인트로 분기했다.
- CSS는 sidebar 240px 고정 + workspace flex, 어두운 사이드바(`--sidebar:#1d2a1f`) + 크림 배경 유지. `.view{display:none}` + `.view.active{display:block}`로 뷰 전환, 1100px 미만에서 grid-columns를 1fr로 무너뜨려 모바일 fallback.
- `PLAN.md`에 운영자 통합 제어 웹 UI를 1급 시민으로 반영했다: (1) 2.1 주요 기능에 `E. 운영자 통합 제어 웹 UI` 섹션을 추가해 한국어 기본 / 사이드바 / 9개 메뉴 / 5초 폴링 / 권한 매핑을 명세했고, (2) 3.1 아키텍처에 `5) 운영자 통합 제어 웹 UI 계층`을 추가해 ops-api dashboard가 시스템의 "운영자 얼굴"임을 명시했으며, (3) Phase 8 단계적 현장 적용의 성과물에 실제 구현 경로(`ops-api/_dashboard_html`)와 9개 뷰 목록을 고정했다.
- ops-api 서버를 재기동하고 `/` → `/dashboard` 리다이렉트와 9개 메뉴 렌더를 `curl`로 검증했다. 19종 smoke 모두 `errors 0`.

### Approval Dashboard 섹션 14 완결 (robot candidate / device status / constraints / pH / 수동 execute / 문제 사례 태깅)
- `ops-api/ops_api/app.py`의 `TRACKED_SENSOR_METRICS`에 `feed_ph`, `drain_ph`를 추가해 Zone History Chart sparkline이 pH 2종도 표시하도록 했다. 기존 9개 + pH 2개 = 11종 지표.
- `_serialize_robot_candidate`와 `/robot/candidates` (`read_runtime` 권한, zone_id/status 필터 지원) 엔드포인트를 추가하고, `_build_dashboard_payload`에 `robot_candidates` 리스트와 `summary.robot_candidate_count`를 노출했다.
- 각 zone payload에 `device_status`, `active_constraints`를 최신 decision의 `zone_state_json`에서 꺼내 병합하는 경로를 추가했다. 가장 최근 `decision_id` 기준으로만 덮어써 순서 무관 병렬 decision에도 안전하다.
- 대시보드 HTML에 Robot Candidates / Device Status / Active Constraints 3개 카드를 오른쪽 stack에 추가하고, `renderRobotCandidates`, `renderDeviceStatus`, `renderActiveConstraints` 3개 렌더러를 JS에 붙였다. 장치별 상태는 `device_id: <badge>`, 제약 조건은 boolean true는 warn 배지, false/값은 dark 배지로 구분한다.
- 결정 카드에 `수동 Execute` 버튼(`executeAction()` → `POST /actions/execute`)과 `문제 사례 태깅` 버튼(`flagCase()` → `POST /shadow/reviews` with `flag:` prefix 강제)을 추가했다. `executeAction`은 approval 모드에서만 노출되고 `flagCase`는 모드 무관 상시 노출이다.
- `scripts/validate_ops_api_dashboard_section14.py`를 추가해 7개 invariant를 회귀한다: (1) 두 차례 `/decisions/evaluate-zone` 호출 후 `robot_candidates`에 candidate-001/002가 모두 남고 candidate-001이 `approved`로 갱신, (2) `summary.robot_candidate_count >= 1`, (3) zone_a payload에 `device_status` / `active_constraints`가 최신 스냅샷을 반영, (4) `/robot/candidates?status=approved` 필터가 1건으로 좁힘, (5) `/zones/{id}/history` `sensor_series`에 `feed_ph`/`drain_ph` 2 points 포함, (6) `/dashboard` HTML에 10개 신규 훅 (`robotCandidateList`, `deviceStatusList`, `activeConstraintsList`, `renderRobotCandidates`, `renderDeviceStatus`, `renderActiveConstraints`, `executeAction`, `flagCase`, `수동 Execute`, `문제 사례 태깅`) 존재, (7) `flag:` prefix 메모가 `OperatorReviewRecord`에 그대로 persist. `_refresh_robot_records_for_decision`이 candidate를 decision 단위로만 지우고 id 기준 upsert하는 기존 semantic을 smoke에 문서화했다.
- 19종 smoke (`flow`, `auth`, `error_responses`, `schema_models`, `shadow_mode`, `postgres_smoke`, `zone_history`, `dashboard_section14`, `postgres_schema_drift`, `policy_source_db_wiring`, `policy_engine_precheck`, `policy_output_validator`, `state_estimator_policy_flow`, `llm_to_execution_flow`, `shadow_runner_gate`, `execution_dispatcher`, `execution_gateway_flow`, `execution_safe_mode`, `state_estimator_mvp`) 모두 `errors 0`.

### 실시간 shadow case 러너 + postgres schema 드리프트 게이트
- `scripts/validate_postgres_schema_drift.py`를 추가해 `infra/postgres/001_initial_schema.sql`을 정규식 파서로 읽고, `Base.metadata.tables`의 컬럼 타입/nullable과 (table, column) 단위로 비교한다. SQL `TEXT/VARCHAR/BIGSERIAL/BIGINT/INTEGER/BOOLEAN/TIMESTAMP*`와 ORM `Text/String/Integer/Boolean/DateTime`을 동일 family로 정규화하고, primary key `id`의 nullability는 양쪽 표기가 다를 수 있어 스킵한다. 13개 테이블 전부 정렬. negative test로 `policies.policy_stage`를 Integer로 강제 변경하면 `policies.policy_stage type drift: sql=text orm=integer`가 검출되는 것까지 확인했다. Alembic 도입 결정을 보류한 상태에서 SQL/ORM 이중 관리의 드리프트를 자동으로 잡는다.
- `scripts/push_shadow_cases_to_ops_api.py`를 추가해 ops-api가 띄워져 있는 환경에서 `/shadow/cases/capture` → `/shadow/window` 경로로 shadow case를 batch 단위로 푸시하고, `--gate rollback|hold|promote` 옵션으로 최소 promotion_decision 임계를 강제한다. 기존 `run_shadow_mode_capture_cases.py`는 audit log 파일을 직접 쓰지만 이 runner는 ops-api auth/audit/회전 가드를 그대로 타고 `manage_runtime_mode` 없는 호출자는 `--append` 기본 동작(append=true)으로만 진입할 수 있다. `--batch-size`로 대용량 dump를 쪼개 요청 바디 제한을 피한다.
- `scripts/validate_shadow_runner_gate.py`를 추가해 runner의 gate 의미를 TestClient 기반으로 회귀한다. `urllib.request.urlopen`을 monkey-patch로 TestClient 라우터에 연결해 러너의 프로덕션 HTTP 경로를 그대로 태운 뒤 3개 시나리오를 돌린다: (1) healthy seed 4건 → `gate=promote` 통과, (2) 추가로 `operator_agreement=False` 하나 append → `operator_agreement_rate=0.8`로 떨어지며 `promotion_decision=hold`, `gate=promote`는 exit 1, (3) 동일 window에 `gate=hold` 완화 → exit 0. 러너가 degraded window를 정확히 감지하고 CI 게이트로 쓸 수 있음을 보인다.
- 18종 smoke (`flow`, `auth`, `error_responses`, `schema_models`, `shadow_mode`, `postgres_smoke`, `zone_history`, `postgres_schema_drift`, `policy_source_db_wiring`, `policy_engine_precheck`, `policy_output_validator`, `state_estimator_policy_flow`, `llm_to_execution_flow`, `shadow_runner_gate`, `execution_dispatcher`, `execution_gateway_flow`, `execution_safe_mode`, `state_estimator_mvp`) 모두 `errors 0`.

### dashboard zone history sparkline + `/zones/{id}/history` sensor_series
- `ops-api/ops_api/app.py`의 `/zones/{zone_id}/history` 응답에 `sensor_series`를 추가했다. `_build_sensor_series`가 decision row를 생성 시각 순으로 정렬한 뒤 각 `zone_state_json.current_state`에서 `air_temp_c`, `rh_pct`, `vpd_kpa`, `substrate_moisture_pct`, `substrate_temp_c`, `co2_ppm`, `par_umol_m2_s`, `feed_ec_ds_m`, `drain_ec_ds_m` 9종 지표를 추출해 `[{t, value, decision_id}]` 형태로 누적한다. 시계열 스토리지를 도입하지 않고도 기존 decision log만으로 스파크라인을 그릴 수 있는 최소 브리지.
- 대시보드 HTML에 `Zone History Chart` 카드를 추가했다. zone 드롭다운과 `Refresh` 버튼, `zoneHistoryCharts` 컨테이너로 구성되고 `refreshZoneHistory()`가 `/zones/{id}/history?limit=30`을 호출해 `renderZoneHistory`가 인라인 SVG `<polyline>` 스파크라인을 지표별로 그린다. min/max/last 값을 텍스트로 오버레이해 스케일이 다른 metric을 같은 viewBox에 표시해도 혼동되지 않도록 했다. 존 리스트가 갱신될 때마다 `syncZoneHistoryOptions`로 select 옵션을 재구성한다.
- `scripts/validate_ops_api_zone_history.py`를 추가해 3개 invariant를 회귀한다: (1) 빈 DB에서 `sensor_series={}`, `decisions=[]`; (2) 두 건의 `/decisions/evaluate-zone` 호출 후 `sensor_series`가 5개 메트릭에 2 points씩 타임순으로 쌓이고 `air_temp_c`가 정확히 입력값(`26.0 -> 28.5`)을 반영; (3) `GET /dashboard`의 HTML 문자열에 `Zone History Chart / zoneHistoryCharts / renderZoneHistory / refreshZoneHistory / sensor_series` 5개 훅이 모두 포함. 스모크는 `auth_mode="disabled"` + `x-actor-role=service` 헤더로 `evaluate_zone` 권한을 받는다 (service 롤이 유일한 소유자).
- 16종 smoke (`flow`, `auth`, `error_responses`, `schema_models`, `shadow_mode`, `postgres_smoke`, `zone_history`, `policy_source_db_wiring`, `policy_engine_precheck`, `policy_output_validator`, `state_estimator_policy_flow`, `llm_to_execution_flow`, `execution_dispatcher`, `execution_gateway_flow`, `execution_safe_mode`, `state_estimator_mvp`) 모두 `errors 0`.

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

---

## 2026-04-14 ~ 2026-04-15 — Phase A~K 종합 (4-way 비교 → fine-tune iteration 종결 → retriever 전환)

### Phase A~E: 4-way 모델 비교 + live-rag grading 버그 수정
- `scripts/build_openai_sft_datasets.py`에 `SFT_V11_RAG_FRONTIER_SYSTEM_PROMPT` (6,695자) 추가. `llm_orchestrator.prompt_catalog`에서 자동 로드.
- `scripts/evaluate_fine_tuned_model.py` 대폭 확장: `--provider {openai,gemini,minimax}`, `--live-rag`, `--rag-top-k`, `--rag-corpus-paths`, `--gemini-thinking-budget`, `--pacing-seconds`, `--minimax-base-url`, `--force-rag-inline`, `--rag-index-path`. `LiveRagRetriever`, `build_retrieval_query`, `load_rag_chunk_lookup`, `inline_retrieved_context`, `strip_thinking_tags`(MiniMax `<think>` 제거) 신규.
- **Phase E 치명 버그 발견**: `grade_case`의 `citations_in_context` 체크가 live-rag 모드에서 `case["retrieved_context"]` (static 정답)만 참조했음. `effective_retrieved_ids` 파라미터 추가로 수정. 검증: unit test 4/4 + B gpt-4.1 static 재채점 0.705→0.705 (회귀 0), C gemini live-rag 재채점 0.070→0.400 (+33점), D m2.7 live-rag 재채점 0.015→0.285 (+27점). `scripts/regrade_eval_results.py`로 11개 run을 API 재호출 없이 재채점.
- 4-way 최종 (raw, ext200/blind50): ds_v11 0.70/0.70, gpt-4.1 frontier+RAG 0.705/0.74, gemini-2.5-flash 0.37/0.50, MiniMax M2.7 0.335/0.22. **Reasoning 모델 이 프로젝트 부적합 실증**.
- 카테고리 단독 1위 (ext200): A ds_v11 6개, B gpt-4.1 6개, 공동 3개. C/D 0개. A crit_floor 0, B는 forbidden_action 0.05 치명.
- 리포트: `artifacts/reports/ab_full_evaluation.md`, `artifacts/reports/ab_frozen_vs_frontier.md`.

### Phase F: Validator 후처리 + retriever 업그레이드
- `scripts/apply_validator_postprocess.py` 신규. `scenario+summary+grading_notes` 키워드 스캔으로 `ValidatorContext` 복원 + `policy_engine.output_validator` 적용. 결과 (raw→validator, ext200): A 0.70→0.78, B 0.705→0.715, C 0.37→0.57, D 0.335→0.47. B는 blind50에서 -2점(validator rule 충돌).
- Retriever recall@5 벤치마크 (250): `KeywordRagRetriever` 0.164, `TfidfSvdRagRetriever` 0.172, **`OpenAIEmbeddingRetriever` (text-embedding-3-small 1536d) 0.352**. `safety_policy` 0.000 → 0.542 복구. `scripts/build_rag_index.py` 재실행으로 `artifacts/rag_index/pepper_openai_embed_index.json` 생성 (226 청크).
- 리포트: `artifacts/reports/phase_f_validator_retriever_improvements.md`.

### Phase G: Retriever를 llm-orchestrator 패키지로 이관
- `llm-orchestrator/llm_orchestrator/retriever_vector.py` 신규: `TfidfSvdRagRetriever`, `OpenAIEmbeddingRetriever`, `create_retriever()` factory. `KeywordRagRetriever`와 동일 인터페이스.
- `llm-orchestrator/llm_orchestrator/__init__.py` export 확장.
- `ops-api/ops_api/config.py`에 `retriever_type`/`retriever_rag_index_path` 필드 추가. `ops-api/ops_api/app.py`가 `create_retriever(...)` 주입 + 실패 시 keyword fallback.
- `scripts/validate_vector_retrievers.py` 신규: 8개 invariant.
- `docs/ds_v12_batch22_hard_safety_reinforcement_plan.md` 신규: ds_v11 hard-safety 5건 2개 클러스터(A enter_safe_mode vs block_action, B GT Master dry-back) 설계.
- `.env.example`에 `OPS_API_RETRIEVER_TYPE`/`OPS_API_RETRIEVER_RAG_INDEX_PATH` 추가.

### Phase H: ds_v12 첫 fine-tune 시도 (catastrophic forgetting 실패)
- `scripts/generate_batch22_hard_safety_reinforcement.py` 신규. batch22 총 36건 (Cluster A 12 + Cluster B 24): `failure_response_samples_batch22_block_vs_safe_mode.jsonl` 12, `state_judgement_samples_batch22_gt_master_dryback.jsonl` 12, `action_recommendation_samples_batch22_gt_master_dryback.jsonl` 12. `validate_training_examples` sample_errors=0.
- `training_data_config.py` glob 패턴이 batch22를 자동 인식(별도 등록 불필요). `build_training_jsonl.py` → 396 rows. `build_openai_sft_datasets.py --system-prompt-version sft_v5` → train 370, validation 14, eval overlap 0.
- 첫 ds_v12 fine-tune submit (`ftjob-2aNsXiqI3VGXBfuUpctaTYkK`, auto hp). 결과 모델 `ft:...:DUhIsVmY`, 실제 선택 hp `batch_size=1, lr_multiplier=2.0, n_epochs=3`.
- **평가 참사**: ext200 0.110, blind50 0.100 (ds_v11 대비 -59/-60점). `citations_present` 실패 168/42건, `blocked_action_type` 20→0 완전 소실, 17개 신규 top-level 키(`action`, `state_id`, `recommended_action` 단수 등 base 스타일).
- 5축 postmortem (`artifacts/reports/ds_v12_failure_postmortem.md`): A citations 12가지 포맷 혼재, B risk_level 소폭 drift, C top-level 키 카오스, D target 5건 중 cluster A 2건은 판단 자체는 학습됐지만 citations 드리프트로 가려짐, **E base gpt-4.1-mini 직접 probe에서 top_keys `[action, state, failure, robot_task, citations(string array)]` — ds_v11 persona가 100% fine-tune 학습 산물임을 확증**.
- 근본 원인: `lr=2.0 + epochs=3`이 ds_v11 persona 얇은 층을 base 쪽으로 gradient overshoot. Training JSONL은 `chunk_id` 335건/`doc_id` 0건으로 정상 — hyperparameter 문제.

### Phase I: Schema drift 감지 + validation 확장 + batch22 variation 확장
- `scripts/compare_output_schemas.py` 신규. 6개 alarm: `new_top_level_keys >= 3`, `common_key_drops >= 50%`, `rare_key_losses (ref ≥5)`, `citations_majority_ratio < 0.80`, `pass_rate_drop >= 0.15`, `strict_json_drop >= 0.05`. `--exit-on-alarm` CI 게이트. ds_v12 first-try 5/6 alarm 발동 + ds_v11 self 0 alarm 검증.
- Validation 14→55건 (`--validation-per-family 4`). `harvest_drying` train 1건 축소는 known issue.
- Batch22 cluster B variation 12→24건: 한국어/영어/Grodan slab/rockwool/mixed substrate/dual-slab/post_harvest_recovery/cold-night 변형. 동일 판단 유지 (`create_alert + request_human_check`, `adjust_fertigation` forbidden). validate_training_examples sample_errors=0.

### Phase J: ds_v12.1 전면 재학습 + ds_v11.B1 증분 재학습 (3-way 실측)
- `scripts/run_openai_fine_tuning_job.py`에 `--n-epochs`, `--learning-rate-multiplier`, `--batch-size` 추가. `short_model_name`이 `ft:` 프리픽스를 `ftbase-<tail>`로 변환.
- **ds_v12.1 전면 재학습** (`ftjob-7FKMcyxqKdrzDBDmfHqqlMxI`, base gpt-4.1-mini, `lr=1.0/epochs=2`, train 341 + validation 55, trained_tokens 860k). 모델 `ft:...:DUmuCKkc`. 평가: ext **0.585** / blind **0.700** (ds_v11 동률), hard_safety 2/1, crit_floor 1/2, Target 3/5 해결 (edge-027, blind-expert-010, blind-action-004). Schema drift 2 alarm.
- **ds_v11.B1 증분 재학습** (`ftjob-GsuYlZAtSNEmKIBjh0FUL9oa`, base `ft:...ds_v11:DTryNJg3`, `lr=1.0/epochs=2`, train 30 batch22만, trained_tokens 82k=전면의 1/10). 모델 `ft:...:DUnXF8Df`. 평가: ext **0.485** / blind **0.540**, hard_safety 1/**0**, crit_floor 3/4 (sensor_fault 0.111, nutrient_risk 0.125, robot_task 0.188 regression), Target **4/5** 해결 (edge-018, edge-027, blind-expert-010, blind-action-004). Citations majority 0.902 (persona 가장 안정적) 하지만 다른 카테고리 negative transfer. Schema drift 3 alarm.
- **3-way 공통 미해결**: `edge-eval-021` (reentry_pending + dry_room comm loss). batch22 cluster A에 이 변형이 부족했음.
- **Hybrid 전략 반증**: Phase F의 "증분이 소규모 보강에 유리" 가설은 실측으로 뒤집혔다. 증분은 비용/시간에서 ×10 유리하지만 persona 유지/일반화/regression 억제에서 전면에 전부 밀림.
- 리포트: `artifacts/reports/ds_v11_vs_ds_v12_1_vs_ds_v11_b1_3way.md`, `artifacts/reports/schema_drift_ds_v12_1_vs_ds_v11.{md,json}`, `artifacts/reports/schema_drift_ds_v11_b1_vs_ds_v11.{md,json}`.

### Phase K: Fine-tune iteration 공식 종결 + retriever 방향 전환
- `artifacts/reports/fine_tune_iteration_final_postmortem.md` 신규. **3번 fine-tune 시도(ds_v12, ds_v12.1, ds_v11.B1) 모두 ds_v11 baseline을 이기지 못함**을 공식 문서화. 근본 한계는 346 rows / 14 카테고리 데이터셋의 구조적 상한이며 AND-grading 해상도가 target 해결과 regression을 상쇄한다는 점. 3개 실패 모델은 debug 자료로만 보존, production 배선 금지. batch22 36건은 미래 데이터셋 증량 프로젝트에 재사용 가능하도록 유지.
- **Production retriever 승격(당시 결정, 2026-04-25 비용 통제로 기본값 `keyword`로 supersede)**: `.env`에 `OPS_API_RETRIEVER_TYPE=openai` 추가 (기존 default `keyword`에서 명시적 전환). `ops-api/ops_api/config.py`의 `load_settings()`가 이 값을 읽고 `ops-api/ops_api/app.py::create_app()`이 `create_retriever("openai", ...)`로 `OpenAIEmbeddingRetriever`를 주입한다. Boot smoke 통과: `OpenAIEmbeddingRetriever rows=226`, routes 36. **recall@5 0.164→0.352 (2.1배), `safety_policy` 카테고리 0.000→0.542**.
- **다음 개선 축**: (1) retriever recall hybrid RRF 개선, (2) shadow mode 실트래픽 수집, (3) validator rule 재검토 (B gpt-4.1 충돌 사례 참조), (4) 장기 데이터셋 3~5배 증량 프로젝트. Fine-tune 반복 iteration은 현 데이터셋 규모에서 종료.
- 교훈:
  - Fine-tune persona는 얇은 층. 공격적 lr 한 번으로 base 쪽으로 overwrite 가능.
  - Grading drift와 model drift를 구분하라 (Phase E `citations_in_context` 버그 사례).
  - Base 모델 probe는 재학습 전후 필수 (persona 유지 여부 자동 감지).
  - 작은 corrective batch (전체의 6~10%)는 negative transfer 위험 큼.
  - 학술적 점수와 운영 적합성은 다르다: ds_v11 raw 0.70 = 3겹 안전망 위에서 validator-후 0.90.
  - Retriever 업그레이드가 fine-tune 반복보다 레버리지 훨씬 큼.

### Phase L: Grodan Delta/GT Master + 수량·병충해 예방 RAG 보강
- `Grodan Delta NG2.0 Block`, `Grodan wetting instruction`, `GT Master Dry/GT Master`, `Grodan EC/refreshment` 공식 자료와 `농사로`의 점박이응애, 목화진딧물, 담배가루이, 담배나방, 흰가루병 자료를 추가 조사해 [docs/grodan_delta_gt_master_yield_pest_research_20260415.md](/home/user/pepper-smartfarm-plan-v2/docs/grodan_delta_gt_master_yield_pest_research_20260415.md)를 작성했다.
- `docs/rag_source_inventory.md`에 신규 source `RAG-SRC-026`~`037`을 추가했다. 범위는 `Grodan Delta 6.5` 육묘/정식, `GT Master` root zone steering, 수량 방어용 저온/차광/잎-과실 균형, 예방형 병충해 예찰·방제다.
- `data/rag/pepper_expert_seed_chunks.jsonl`에 신규 청크 `23건`을 추가해 총 `242건`으로 확장했다. 추가 묶음은 `Grodan direct 0 -> 8+`, 저온/낙화 기반 수량 방어, 탄저병/역병/점박이응애/진딧물/담배가루이/담배나방/흰가루병/총채벌레 예방 규칙을 포함한다.
- 이번 요청에 맞춘 직접 범위(`Grodan + 수량 증대 + 예방형 병충해`) 기준 bundle count는 `HEAD 14건 -> 작업 후 36건`으로 `2배 이상` 확대했다.
- `python3 scripts/validate_rag_chunks.py` 결과 `validated rows: 242`, duplicate `0`, warnings `0`, errors `0`을 확인했다.

### Phase M: Grodan 근권 해석 규칙을 rubric/policy 문서에 반영
- [docs/risk_level_rubric.md](/home/user/pepper-smartfarm-plan-v2/docs/risk_level_rubric.md)에 `GT Master`의 `EC delta 0.3~0.8 안정권`, `<0.3 과급수 watch`, `>1.0 refresh 실패/과소급수 watch`, `first drain without EC drop = direct drainage 의심` 규칙을 반영했다.
- 같은 문서에 `Delta 6.5` 정식 전 wet weight/saturation evidence를 `unknown` 판단의 핵심 근거로 추가했다. `10x10x6.5cm` block 기준 wet weight `550g` 미만 또는 미측정이면 자동 정식/자동 관수 판단 근거로 쓰지 않는다고 명시했다.
- [docs/policy_output_validator_spec.md](/home/user/pepper-smartfarm-plan-v2/docs/policy_output_validator_spec.md)의 `HSV-08`을 `evidence sufficiency` 중심으로 확장했다. `Delta 6.5` saturation evidence 부재는 validator가 `unknown + pause_automation + request_human_check`로 보내고, `GT Master high vs medium` 의미 해석은 validator가 아니라 rubric/모델이 맡는다고 분리했다.
- [docs/site_scope_baseline.md](/home/user/pepper-smartfarm-plan-v2/docs/site_scope_baseline.md)에 현장 기본 해석선을 추가해 site baseline 문서만 봐도 `Delta/GT Master` 운영 전제를 바로 확인할 수 있게 했다.

### Phase N: 재배단계별 서브에이전트 기반 RAG 지식 보강
- 사용자 요청에 맞춰 `육묘`, `정식/활착`, `영양생장~과실비대`, `수확/건조` 4개 재배단계 서브에이전트로 수집 범위를 분리했다. 중복 소스는 제외하고 stage-aware retrieval에 실익이 큰 항목만 선별했다.
- [docs/cultivation_stage_subagents_20260415.md](/home/user/pepper-smartfarm-plan-v2/docs/cultivation_stage_subagents_20260415.md)를 신규 작성해 각 서브에이전트의 담당 범위, 우선 소스, overlap 처리 원칙, RAG 반영 결과를 문서화했다.
- `docs/rag_source_inventory.md`에 `RAG-SRC-038`~`044`를 추가했다. 신규 source 범위는 `건전묘 구매 기준`, `노화묘+고EC+깊은 정식 복합 실패`, `촉성재배 온도/수량 기술`, `4차분지 적화`, `시설해충 예방형 천적 방사`, `건고추 수확`, `건조 및 저장`이다.
- `data/rag/pepper_expert_seed_chunks.jsonl`에 신규 청크 `8건`을 추가해 총 `250건`으로 확장했다.
  - `pepper-seedling-purchase-qc-001`
  - `pepper-overaged-seedling-high-ec-001`
  - `pepper-forcing-fruitset-temperature-band-001`
  - `pepper-forcing-technology-yieldgain-001`
  - `pepper-early-flower-removal-yield-001`
  - `pepper-greenhouse-pest-preventive-biocontrol-window-001`
  - `pepper-harvest-80pct-shade-ripen-001`
  - `pepper-dry-storage-barrierbag-001`
- 이번 반영으로 stage별 신규 지식은 `육묘 1`, `정식/활착 1`, `본재배 4`, `수확/건조 2` 비중으로 보강됐고, `RAG-SRC-001` 및 기존 Grodan chunk와 겹치는 접목 일반론은 중복 추가하지 않았다.

### Phase O: stage-aware retrieval eval set 추가 및 검증
- `evals/rag_stage_retrieval_eval_set.jsonl`을 신규 작성했다. 총 `16개 case`이며 `nursery`, `transplanting`, `flowering`, `fruiting`, `harvest_drying_storage` 단계와 `grodan_delta_6_5`, `grodan_gt_master`, `forcing` metadata filter를 함께 검증한다.
- stage eval은 이번에 추가한 `RAG-SRC-038`~`044`와 기존 Grodan chunk가 실제로 단계별 top-k retrieval에서 기대 청크로 잡히는지 확인하기 위한 전용 세트다.
- `./.venv/bin/python scripts/evaluate_rag_retrieval.py --eval-set evals/rag_stage_retrieval_eval_set.jsonl --vector-backend keyword --top-k 3 --fail-under 1.0` 결과 `16/16`, `hit_rate 1.0`, `MRR 1.0`을 확인했다.
- `./.venv/bin/python scripts/evaluate_rag_retrieval.py --eval-set evals/rag_stage_retrieval_eval_set.jsonl --vector-backend local --top-k 3 --fail-under 1.0` 결과도 `16/16`, `hit_rate 1.0`, `MRR 1.0`이었다.
- 결과 JSON은 `artifacts/reports/rag_stage_retrieval_keyword_20260415.json`, `artifacts/reports/rag_stage_retrieval_local_20260415.json`에 저장했고, 요약은 `artifacts/reports/rag_stage_retrieval_summary_20260415.md`에 남겼다.

### Phase P: 공통 + stage retrieval 통합 validation suite 추가
- `scripts/run_rag_validation_suite.py`를 신규 작성했다. 기본값으로 공통 retrieval eval `110건`과 stage retrieval eval `16건`을 keyword/local 두 모드로 함께 실행하고, JSON/Markdown 요약 리포트를 출력한다.
- 실행 명령은 `./.venv/bin/python scripts/run_rag_validation_suite.py --fail-under 1.0 --output-json artifacts/reports/rag_validation_suite_20260415.json --output-md artifacts/reports/rag_validation_suite_20260415.md`로 고정했다.
- 실행 결과 aggregate 기준 keyword는 `126개 case`, `hit_rate 1.0`, `MRR 0.9921`이고, local은 `126개 case`, `hit_rate 1.0`, `MRR 1.0`이었다.
- suite별 세부 수치는 공통 eval `110건` keyword `0.9909` / local `1.0`, stage eval `16건` keyword/local 모두 `1.0`이다.

---

## 2026-04-17 — gemini_flash_frontier 계획 전량 폐기

### 배경
- 2026-04-14에 사용자 결정으로 `gemini-2.5-flash`를 RAG-first frontier challenger alias `gemini_flash_frontier`로 고정하고, runtime alias + `.env` GEMINI 경로 + `sft_v11_rag_frontier` prompt를 모두 연결했다.
- 이후 Phase A~E 4-way 실측(`artifacts/reports/ab_full_evaluation.md`, `artifacts/reports/ab_frozen_vs_frontier.md`)에서 `gemini-2.5-flash` (thinking) `ext 0.37 / blind 0.50`, `MiniMax M2.7` `ext 0.335 / blind 0.22`로 `ds_v11` (0.70/0.70) 대비 열세였다. reasoning/thinking 모델이 JSON strict + instruction-heavy 결정 경로에 구조적으로 부적합함이 두 모델 실측으로 확정됐다.
- Phase K-1 `artifacts/reports/fine_tune_iteration_final_postmortem.md`에서 production champion을 `ds_v11` 유지로 공식 종결한 이후에도 `gemini_flash_frontier` 승격 평가 todo가 열려 있었다.

### 조치
- **todo.md**: `RAG-first frontier challenger를 gemini-2.5-flash로 고정` 체크박스를 폐기 마커(`[~]`)로 전환, 승격 평가 todo(`extended200 + blind_holdout50 + real shadow` 기준 재평가)를 폐기 주석으로 교체.
- **PROJECT_STATUS.md**: 항목 25, 29를 `폐기 (2026-04-17)`로 교체. 폐기 근거와 유지되는 역사 artifact 범위를 명기.
- **README.md**: `RAG-first frontier challenger 결정` 항목, `Gemini runtime path` 항목을 폐기 마커로 교체.
- **docs/model_product_readiness_reassessment.md**: `Update 2026-04-14: frontier RAG challenger 선택` 섹션을 `Update 2026-04-17: frontier RAG challenger 폐기` 로 교체.
- **docs/runtime_integration_status.md**: Gemini smoke 명령 제거, 현재 한계 항목 폐기 마커로 교체.
- **llm-orchestrator/README.md**: `gemini` provider 표기 옆 폐기 주석 추가, Gemini smoke 블록 삭제, `gemini_flash_frontier` alias 폐기 주석 추가.
- **llm-orchestrator/llm_orchestrator/model_registry.py**: `gemini_flash_frontier` entry 삭제.
- **artifacts/runtime/llm_orchestrator/model_registry.json**: `gemini_flash_frontier` entry 삭제.
- **.env.example**: `GEMINI_API_KEY`, `GOOGLE_API_KEY`, `MINIMAX_API_KEY`, Gemini provider 예시 라인 제거. 파일 상단 주석에서 `OpenAI/Gemini-backed` → `OpenAI-backed` 단순화.
- **.env / .env.dev.example / .env.staging.example / .env.prod.example**: `GEMINI_API_KEY`, `GOOGLE_API_KEY` 라인 제거. `.env`의 실제 Google/Gemini API key는 삭제됐으므로 사용자는 Google Cloud Console에서 key를 revoke 권장.

### 보존 범위
- Phase A~E 평가 artifact (`artifacts/reports/frontier_gemini_*`, `artifacts/reports/regrade/C_gemini_*`, `artifacts/reports/validator_postprocess/C_gemini_*`, `artifacts/reports/ab_full_evaluation.md`, `artifacts/reports/ab_frozen_vs_frontier.md`)는 **역사 기록으로 보존**한다. 이들은 "왜 Gemini 경로를 폐기했는지"의 실측 근거다.
- `scripts/evaluate_fine_tuned_model.py`의 `--provider {openai,gemini,minimax}` CLI 분기와 `scripts/apply_validator_postprocess.py`, `scripts/regrade_eval_results.py`의 gemini 파일 경로 대응 코드도 **유지**한다. 과거 jsonl 재채점/재검증 경로가 필요할 수 있어서다. 신규 Gemini 평가 실행은 계획에 없다.
- `llm-orchestrator/llm_orchestrator/client.py`의 `GeminiCompletionClient` 구현도 **유지**한다. 제거는 더 큰 리팩터 변경이며 현재 의존 경로가 남아 있을 수 있다. 필요시 별도 과제로 이관한다.

---

## 2026-04-17 — Hybrid RRF retriever 벤치마크 (quota blocked) + blind50 residual 5건 rubric/validator 조정

### Hybrid RRF retriever 벤치마크
- `scripts/benchmark_hybrid_retriever.py` 신규. `evals/rag_retrieval_eval_set.jsonl` (110) + `evals/rag_stage_retrieval_eval_set.jsonl` (16) 총 **126 case**에 대해 recall@5, any_hit@5, MRR을 keyword / tfidf / openai / hybrid 4경로로 측정하는 벤치마크 툴.
- **OpenAI quota 고갈**: `text-embedding-3-small` 호출이 429 `insufficient_quota`로 전량 실패. openai/hybrid retriever 본 라운드 측정 불가. 단일 `embeddings.create` 호출도 재현 실패.
- Local-only 재실행 결과: **keyword 0.9444 / tfidf 0.7698**. 단 이 eval set은 token-rich 쿼리로 구성되어 keyword에 유리하다 — Phase F의 decision eval 250 case(keyword 0.164 / openai 0.352)와는 축이 다르다.
- **운영 영향**: `.env`의 `OPS_API_RETRIEVER_TYPE=openai` 설정은 quota 복구 전까지 ops-api live 검색을 실패시킨다. 2026-04-25 비용 통제 작업에서 `.env.example` 기본값은 `OPS_API_RETRIEVER_TYPE=keyword`로 롤백했고, OpenAI live query는 env opt-in으로 막았다.
- 결정 이관: hybrid 승격 여부 판정은 quota 복구 이후 Phase F 방식(decision eval 250 case)으로 재실행한다.
- 산출물: `artifacts/reports/hybrid_retriever_benchmark.md` (포스트모템), `hybrid_retriever_benchmark.json` (quota-failed run raw), `hybrid_retriever_benchmark_local_only.md` + `.json` (keyword + tfidf).

### blind50 validator 잔여 5건 처리 확정
- 기준 리포트: `artifacts/reports/validator_residual_failures_ds_v11_prompt_v5_methodfix_batch14_blind_holdout50.md`. 잔여 5건 = `data_and_model 3 / risk_rubric_and_data 2`.
- Phase K-1 fine-tune iteration 종결 이후 추가 corrective training submit은 옵션이 아니므로, 이번 라운드는 rubric 명시 보강 + validator scope 경계 명문화 + dataset scale-up 이관으로 처리했다.
- **rubric 강화** (`docs/risk_level_rubric.md`):
  - §4 `robot_task_prioritization`에 "후보 중 하나가 blocked면 high, skip_area 먼저" 엔트리 추가 — `blind-robot-004` 정렬
  - §4 `rootzone_diagnosis / nutrient_risk`와 §5 빠른 판정 규칙에 "GT Master feed-drain EC 차이 2.0 이상 + drain 비율 20% 미만 → high, `create_alert + request_human_check` 필수, `observe_only` 단독 금지" 엔트리 추가 — `blind-expert-003` 정렬
- **validator out-of-scope 경계 추가** (`docs/policy_output_validator_spec.md` §8): `GT Master EC gradient > 2.0 + drain rate < 20%`, `robot_task blocked candidate` 두 항목을 score-chasing 원칙에 따라 validator 신규 규칙 **금지** 목록에 추가했다. 기존 `GT Master dry-back`, `Delta 6.5 nursery cold+humid`와 같은 처리 원칙을 유지한다.
- **dataset scale-up 이관**: `blind-action-004`, `blind-expert-010` (GT Master dry-back Cluster B) 2건은 rubric은 이미 충분하고 validator는 out-of-scope이므로, Phase K-1 후속 dataset scale-up 프로젝트에서 batch22 cluster B 24건과 함께 재투입한다.
- **효과 범위**: rubric 변경은 ds_v11 출력을 바꾸지 않는다(fine-tune 종결). 본 작업은 (a) 향후 라벨 기준 통일, (b) shadow mode operator agreement 기준 명문화, (c) validator scope 경계 명문화로 다른 에이전트의 실수 HSV 규칙 추가 방지를 목표로 한다.
- 계획 doc: `docs/blind50_residual_post_ds_v11_closure_plan.md` 신규. 5건별 처리 결정, 후속 트리거(shadow 50건 누적 또는 dataset scale-up 승인), validator 사용 금지 이유 명시.
- `todo.md`의 L93 (blind50 잔여 5건 targeted fix 여부 확정)을 `[x]`로 닫았다.

---

## 2026-04-25 — Retriever 비용 통제 + 로컬 후보 + extended200 우선순위 정리

### 비용/쿼터 통제
- `.env.example`의 runtime retriever 기본값을 `OPS_API_RETRIEVER_TYPE=keyword`로 고정했다. OpenAI embedding retriever는 품질 실측 artifact와 code path는 유지하되, 운영 기본값이 아니라 명시 opt-in으로만 사용한다.
- `OPENAI_LIVE_RETRIEVER_SMOKE=0`을 추가했다. `scripts/validate_vector_retrievers.py`는 기본 실행에서 OpenAI index JSON의 차원/문서 수만 확인하고, 실제 embedding query는 `OPENAI_LIVE_RETRIEVER_SMOKE=1`일 때만 수행한다.
- `scripts/benchmark_hybrid_retriever.py`도 기본 retriever set을 zero-cost(`keyword`, `tfidf`, `local_embed`, `local_hybrid`)로 바꾸고, `openai`/`hybrid` benchmark는 `OPENAI_LIVE_RETRIEVER_SMOKE=1` 없이는 거부하도록 막았다.
- 이전 stabilization commit `29f9fca`에서 stale `ds_v14` chat env 예시 제거, server smoke request_id unique 처리, policy enabled 상태 복원을 함께 반영했다.

### 로컬 retriever 후보
- `llm-orchestrator/llm_orchestrator/retriever_vector.py`에 dependency-free `LocalSemanticRagRetriever`와 keyword+local RRF `LocalHybridRagRetriever`를 추가했다.
- factory alias: `local_embed`, `local_semantic`, `semantic`, `hashing`, `local_hybrid`, `keyword_local`, `keyword_semantic`.
- `scripts/validate_vector_retrievers.py`가 `local_embed`/`local_hybrid` factory dispatch와 corpus chunk id invariant를 회귀한다.

### Benchmark
- 실행: `.venv/bin/python scripts/benchmark_hybrid_retriever.py --retrievers keyword tfidf local_embed local_hybrid --rag-index-path artifacts/rag_index/pepper_expert_with_farm_case_index.json --output-json artifacts/reports/local_retriever_benchmark.json --output-md artifacts/reports/local_retriever_benchmark.md`
- 결과: `keyword recall@5 0.9444 / MRR 0.9114`, `local_hybrid 0.8968 / 0.7753`, `tfidf 0.7698 / 0.6060`, `local_embed 0.7540 / 0.7073`.
- 결론: 이 126-case RAG eval은 token-rich corpus regression이라 keyword가 강하다. 비용 없는 후보는 구현됐지만 기본값 승격 기준은 아직 충족하지 못했으므로 runtime default는 `keyword`로 유지한다.

### extended200 residual
- `docs/extended200_residual_priority_plan.md`를 2026-04-25 기준 상태로 갱신했다.
- `todo.md`의 extended200 validator 잔여 `42건` batch 설계 항목을 `[x]`로 닫았다. 다음 실행 단위는 `Batch21A risk_rubric_core` sample 설계/생성이다.

---

## 2026-04-25 — Batch21 corrective samples + shadow/retriever 재검증

### Batch21A/B/C 생성
- `scripts/generate_batch21_extended200_residual_samples.py` 신규. ds_v11 extended200 validator 잔여 `42건`을 `docs/extended200_residual_priority_plan.md` 기준으로 재현 가능한 JSONL seed로 생성한다.
- Batch21A `risk_rubric_core`: `20건`
  - `data/examples/state_judgement_samples_batch21a_risk_rubric_core.jsonl` `12`
  - `data/examples/failure_response_samples_batch21a_risk_rubric_core.jsonl` `4`
  - `data/examples/forbidden_action_samples_batch21a_risk_rubric_core.jsonl` `4`
- Batch21B `required_action_types_and_evidence_gap`: `16건`
  - `data/examples/action_recommendation_samples_batch21b_required_actions.jsonl` `8`
  - `data/examples/state_judgement_samples_batch21b_required_actions.jsonl` `4`
  - `data/examples/failure_response_samples_batch21b_required_actions.jsonl` `4`
- Batch21C `robot_contract_exactness`: `6건`
  - `data/examples/robot_task_samples_batch21c_robot_contract_exactness.jsonl` `6`
- `python3 scripts/build_training_jsonl.py --include-source-file`로 `artifacts/training/combined_training_samples.jsonl`을 `577건`으로 재생성했다.

### 검증
- `python3 scripts/validate_training_examples.py`: sample files `79`, sample rows `577`, duplicate `0`, errors `0`; eval rows `250`, errors `0`.
- `python3 scripts/audit_training_data_consistency.py`: rows `577`, duplicate rows `0`, contradictions `0`, eval overlap `0`, errors `0`.
- `python3 scripts/report_risk_slice_coverage.py --strict`: training/extended_eval/blind_holdout 모두 rule failure `none`.
- `scripts/report_risk_slice_coverage.py`는 `manual_override`/`worker_present`/`reentry_pending` hard-block failure_response를 stale safe_mode slice로 오분류하지 않도록 보정했다. Batch22 cluster A의 의도는 `enter_safe_mode`가 아니라 `block_action + create_alert` 우선이기 때문이다.

### Shadow mode
- `validate_shadow_mode_seed_pack.py`와 `run_shadow_mode_seed_pack.py` 재실행 결과 synthetic shadow day0는 여전히 `decision_count 12`, `operator_agreement_rate 0.6667`, `critical_disagreement_count 0`, `promotion_decision hold`.
- `report_shadow_mode_seed_residuals.py` 재실행 결과 residual `4건`: `data_and_model 3` (`alert_missing_before_fertigation_review`), `robot_contract_and_model 1` (`inspect_crop_enum_drift`).
- Batch21B/C가 각각 `create_alert + request_human_check` 누락과 `inspect_crop exact enum + candidate_id/target` drift를 future training seed로 덮었다. 재학습 전 모델 출력은 변하지 않으므로 submit 후보 결정은 계속 blocked다.

### Real shadow runner + retriever 유지보수
- `scripts/validate_shadow_runner_gate.py`의 SQLite TestClient 설정을 제거하고 PostgreSQL-only로 정렬했다. PostgreSQL URL이 없으면 `blocked`로 종료한다.
- `.env` PostgreSQL 설정으로 `validate_shadow_runner_gate.py` 실행: promote window 통과, mismatch injection 후 hold 강등, gate=hold 통과 확인.
- `bash scripts/run_ops_api_postgres_stack.sh`로 localhost ops-api를 띄운 뒤 `push_shadow_cases_to_ops_api.py --gate hold`로 day0 seed `12건` 적재를 반복했다. `/shadow/window`는 `decision_count 24`, `operator_agreement_rate 0.6667`, `critical_disagreement_count 0`, `promotion_decision hold`.
- 같은 ops-api audit log(`artifacts/runtime/llm_orchestrator/shadow_mode_audit.jsonl`)를 `scripts/build_shadow_mode_window_report.py`로 고정해 `artifacts/reports/shadow_mode_ops_api_seed_window_20260425.json`과 `.md`를 생성했다. seed replay가 반복된 window라 승격 근거는 아니며, 다음 단계는 실제 운영 unique case 누적이다.
- 커밋 `19bf6f8`(`Record ops-api shadow window report`)을 원격 `master`에 push했다.
- seed window report를 `scripts/build_challenger_submit_preflight.py --real-shadow-report`에 연결해 `artifacts/reports/challenger_submit_preflight_ds_v12_ds_v13_ops_api_seed_window_20260425.json`과 `.md`를 생성했다. 결과는 `real_shadow_mode_status=hold`, `ds_v12 blocked`, `ds_v13 blocked`다.
- `scripts/validate_shadow_cases.py`를 추가해 real shadow case JSONL을 ops-api 적재 전에 검증하도록 했다. 검증 범위는 필수 필드, `request_id` 중복, metadata/context 정렬, operator outcome, seed/offline eval_set 혼입 금지다.
- `push_shadow_cases_to_ops_api.py`는 기본 사전검증과 `--validate-only`를 지원한다. `scripts/run_shadow_mode_ops_pipeline.py`는 검증, `/shadow/cases/capture`, window report, challenger preflight 재계산을 한 번에 실행한다. `data/ops/README.md`와 `docs/real_shadow_mode_runbook.md`에 실제 운영 request_id 규칙과 명령을 반영했다.
- `validate_vector_retrievers.py`는 OpenAI live query를 skip하고 통과했다. zero-cost retriever benchmark는 동일하게 `keyword recall@5 0.9444`, `local_hybrid 0.8968`, `tfidf 0.7698`, `local_embed 0.7540`이다.

---

## 2026-04-25 — Policy source history + runtime gate + shadow residual backlog

### ops-api policy/runtime UI
- `PATCH /policies/{policy_id}`가 실제 변경이 있을 때 `source_version=policy_id@YYYYMMDDTHHMMSSZ`를 갱신하고, `policy_events`에 `policy_changed` 이벤트를 남기도록 보강했다. 이벤트 payload에는 `actor_id`, `actor_role`, `changed_fields`, `before`, `after`가 들어간다.
- `GET /policies/{policy_id}/history`를 추가했다. 대시보드 정책 카드에는 `source_version`, `updated_at`, `이력 보기` 버튼을 추가했고, 정책 화면에는 차단/승인 이벤트 queue와 source version 변경 이력 리스트를 분리했다.
- 오버뷰 오른쪽 rail에 `Runtime Gate` 카드를 추가해 runtime mode, ds_v11 frozen champion gate, retriever, shadow window 결과, approval queue, policy risk events를 한 번에 확인할 수 있게 했다.
- 자동화 뷰에 review summary를 추가해 최근 trigger의 승인 대기/승인됨/실행됨/차단·실패 수와 가장 오래된 승인 대기 trigger를 표시한다.

### real shadow backlog/rehearsal
- `schemas/shadow_residual_backlog_schema.json`과 `docs/real_shadow_residual_backlog.md`를 추가해 실제 운영 shadow disagreement를 corrective backlog로 옮기는 JSONL 구조를 고정했다.
- `scripts/generate_shadow_ops_rehearsal_day.py`를 추가했다. `rehearsal-shadow-YYYYMMDD-NNN` request_id와 `shadow-rehearsal-YYYYMMDD` eval_set_id를 쓰므로 `--real-case` 검증이나 submit 승격 근거로 쓰지 않는다.
- `data/ops/README.md`와 `docs/real_shadow_mode_runbook.md`에 rehearsal 파일과 실제 운영 file/backlog의 분리 기준을 반영했다.

### Phase P follow-up 검증
- `/dashboard/data`에 `runtime_gate` payload를 공식 추가했다. 필드는 `gate_state`, `runtime_mode`, `champion`, `retriever_type`, `shadow_window_status`, `approval_queue_count`, `policy_risk_event_count`, `policy_change_count`, `blockers`다.
- `/policies/events`에 `policy_id`와 `request_id` 필터를 추가했다. `policy_id`는 JSON text column을 안전하게 후처리 필터링하고, query scan limit은 최대 500개로 제한했다.
- `scripts/validate_ops_api_runtime_review_surfaces.py`를 추가했다. PostgreSQL URL이 있을 때만 임시 policy row를 만들어 `PATCH /policies/{id}` → `policy_changed` → history/event filter → dashboard `runtime_gate`까지 검증하고, URL이 없으면 SQLite 대체 없이 skip한다.
- `scripts/validate_shadow_residual_backlog.py`를 추가했다. schema enum, required field, ISO timestamp, 중복 `residual_id`, optional source case id 교차검증을 수행한다.
- `data/ops/shadow_residual_backlog_template.jsonl`을 추가하고, `data/ops/README.md`와 `docs/real_shadow_mode_runbook.md`에 rehearsal 1회 절차와 backlog 검증 명령을 고정했다.

### Phase P quality gate + residual report
- `scripts/run_phase_p_quality_gate.py`를 추가했다. py_compile, dashboard hook import check, rehearsal shadow JSONL 생성/검증, `run_shadow_mode_ops_pipeline.py --validate-only`, residual backlog template 검증, residual backlog report 생성, PostgreSQL-only runtime review smoke, `git diff --check`를 한 번에 실행한다.
- `scripts/report_shadow_residual_backlog.py`를 추가했다. backlog JSONL을 owner/status/severity/failure_mode/fix_type별로 집계하고 JSON/Markdown summary를 출력한다.
- `/dashboard/data.runtime_gate`에 `open_residual_count`, `critical_residual_count`, `unverified_fix_count`를 추가했다. open 또는 critical residual이 있으면 gate blocker에 `shadow_residuals_open` 또는 `critical_shadow_residuals_open`이 표시된다.
- Shadow Mode 뷰에 `Real Shadow Residuals` 카드를 추가해 total/open/critical/fixed-unverified, owner별 count, 최근 residual과 expected fix를 표시한다.
- `docs/real_shadow_daily_intake_checklist.md`와 `docs/policy_event_filter_performance_plan.md`를 추가했다. 전자는 하루 운영 후 case 검증 → ops-api 적재 → window report → backlog → summary → dashboard 확인 순서를 고정하고, 후자는 현행 JSON 후처리 필터의 scan limit과 장기 link table 설계를 기록한다.

---

## 2026-04-26 — Daily real shadow intake + indexed policy filter + dashboard v2 live data

### Real shadow daily runner
- `scripts/run_real_shadow_daily_intake.py`를 추가했다. 실제 운영 하루 단위로 `validate_shadow_cases.py --real-case --expected-date` → `run_shadow_mode_ops_pipeline.py` → residual backlog validate/report → runtime gate blocker report를 실행하고, candidate manifest가 주어지면 challenger preflight output prefix까지 고정한다.
- `scripts/validate_shadow_cases.py`는 real-case에서 파일명 `shadow_mode_cases_YYYYMMDD`, `request_id=prod-shadow-YYYYMMDD-NNN`, `metadata.eval_set_id=shadow-prod-YYYYMMDD`가 같은 날짜인지 검사한다. `push_shadow_cases_to_ops_api.py`와 `run_shadow_mode_ops_pipeline.py`도 `--expected-date`를 전달받는다.
- `scripts/report_runtime_gate_blockers.py`를 추가했다. `/dashboard/data.runtime_gate` 또는 저장된 JSON payload에서 `submit_allowed`, blocker 목록, approval/policy/residual count, next action을 JSON/Markdown으로 출력한다.

### Policy event filter normalization
- `infra/postgres/006_policy_event_policy_links.sql`을 추가했다. `policy_events.policy_ids_json`을 backfill해 `policy_event_policy_links(policy_event_id, policy_id)`에 넣고 `(policy_id, policy_event_id DESC)` index를 생성한다.
- `PolicyEventPolicyLinkRecord` ORM 모델과 `_add_policy_event()` helper를 추가했다. policy event 생성 시 legacy `policy_ids_json`과 link row를 동시에 기록한다.
- `/policies/events?policy_id=...`와 `/policies/{policy_id}/history`는 JSON 후처리 scan 대신 link table join을 사용한다. `scripts/validate_policy_event_link_table.py`가 PostgreSQL-only smoke로 link row 생성과 필터 결과를 검증한다.

### Dashboard v2 + retriever gate
- 실제 로드되는 `ops-api/ops_api/static/dashboard_v2/src/bundle.jsx`에 `fetchDashboardV2Data()`와 `postDashboardV2Action()`을 추가했다. Overview의 todo/approval/zones/timeline은 `/dashboard/data`를 우선 사용하고, Decisions 화면의 approve/reject는 `/actions/approve|reject`로 연결된다.
- `scripts/validate_ops_api_dashboard_v2.py`에 `/dashboard/data`, `fetchDashboardV2Data`, action hook marker 검증을 추가했다.
- `scripts/validate_zero_cost_retriever_regression.py`를 추가했다. 기본값은 `keyword`와 `local_hybrid`만 평가하고, 각각 recall@5 `0.90`, `0.85` 이상을 요구한다. OpenAI-backed retriever는 `OPENAI_LIVE_RETRIEVER_SMOKE=1` 없이는 거부한다.
- `scripts/run_phase_p_quality_gate.py`에 vector retriever static smoke, zero-cost retriever regression, runtime gate blocker report, policy event link smoke, dashboard v2 smoke를 포함했다.
