# AI 모델 준비 및 MLOps 계획

이 문서는 온실이 아직 공사 중인 상황에서 먼저 진행할 AI 모델 준비, 센서 수집 계획, 학습 반영 체계, 모델 진화 방법을 정리한다.

## 전제

- 현재는 실측 온실 데이터가 없다.
- 따라서 초기 단계는 장치 제어 구현이 아니라 AI 판단 체계, 데이터 스키마, RAG 지식베이스, 평가셋, MLOps 루프 구축이 우선이다.
- 실제 센서 데이터가 들어오기 전까지는 재배 매뉴얼, 현장 SOP 초안, 시뮬레이션 데이터, 합성 시나리오, 공개 자료 기반 평가셋으로 모델을 준비한다.
- 현재 기준 사이트는 `gh-01`, `300평 연동형 비닐온실 1동`이며 주 설비는 대형 온실 1개다.
- 현재 품종 운영 범위는 `건고추/고춧가루용 적고추`이며 1차 shortlist는 `왕조`, `칼탄열풍`, `조생강탄`이다.
- 재배 환경 조건은 육묘용 `Grodan Delta 6.5` block, 본재배용 `Grodan GT Master` slab를 기준으로 고정한다.

## Phase -1 진행 현황

현재 Phase -1은 **설계 산출물 기준으로 완료 상태**로 본다. 아직 구현되지 않은 항목은 runner 실행 코드와 실제 센서 연동이며, 이는 다음 단계로 넘긴다.

| 목표 | 상태 | 근거 산출물 |
|---|---|---|
| AI 판단 체계 선행 준비 | 완료 | `schemas/state_schema.json`, `schemas/feature_schema.json`, `schemas/action_schema.json`, `schemas/sensor_quality_schema.json` |
| 적고추 전주기 전문가 지식 구조화 | 완료 | `docs/expert_knowledge_map.md`, `docs/sensor_judgement_matrix.md`, `EXPERT_AI_AGENT_PLAN.md` |
| RAG 지식베이스 설계와 품질 기준 수립 | 완료 | `docs/rag_indexing_plan.md`, `docs/rag_source_inventory.md`, `schemas/rag_chunk_schema.json`, `data/rag/pepper_expert_seed_chunks.jsonl` |
| 파인튜닝 seed와 평가셋 준비 | 완료 | `data/examples/*_samples.jsonl`, `data/examples/*_samples_batch2.jsonl`, `data/examples/*_samples_batch3.jsonl`, `evals/expert_judgement_eval_set.jsonl`, `evals/rag_retrieval_eval_set.jsonl` |
| OpenAI SFT submit 경로 검증 | 완료 | 1차 job `ftjob-2UERXn8JN2B0SDUXL1tukptl` 실패(`invalid_file_format`) 후 `messages` only 포맷으로 수정했다. 현재 frozen baseline은 `ds_v11/prompt_v5_methodfix_batch14` model `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v11-prompt-v5-methodfix-batch14-eval-v2-2026:DTryNJg3`이고, 최신 corrective candidate `ds_v14/prompt_v10_validator_aligned_batch19_hardcase` run `ftjob-37TzJb1FtgGUghjfyaGqAxkA`는 `succeeded`였지만 `ds_v11`보다 낮아 승격 실패로 닫았다. `ds_v12`/`ds_v13`은 dry-run blocked challenger이며 현재 in-flight submit은 없다. |
| 모델/프롬프트/데이터셋 버전 관리 체계 설계 | 완료 | `docs/mlops_registry_design.md` |
| offline runner 설계 | 완료 | `docs/offline_agent_runner_spec.md`, `data/examples/synthetic_sensor_scenarios.jsonl` |
| shadow mode 보고 체계 정의 | 완료 | `docs/shadow_mode_report_format.md` |
| 운영 로그 환류 설계 | 완료 | `docs/farm_case_rag_pipeline.md`, `schemas/farm_case_candidate_schema.json` |
| `farm_case` 샘플과 event window 규칙 | 완료 | `data/examples/farm_case_candidate_samples.jsonl`, `docs/farm_case_event_window_builder.md`, `scripts/validate_farm_case_candidates.py` |
| 승인된 `farm_case` 후보의 RAG chunk 변환 초안 | 완료 | `scripts/build_farm_case_rag_chunks.py`, `data/rag/farm_case_seed_chunks.jsonl` |
| `farm_case` 혼합 인덱스에서 공식 지침 우선 정렬 규칙 | 완료 | `scripts/search_rag_index.py`, `evals/rag_official_priority_eval_set.jsonl` |
| `sensor-ingestor` 설정 계약과 poller profile 초안 | 완료 | `docs/sensor_ingestor_config_spec.md`, `schemas/sensor_ingestor_config_schema.json`, `data/examples/sensor_ingestor_config_seed.json`, `scripts/validate_sensor_ingestor_config.py` |
| 센서 품질 규칙과 runtime flow 초안 | 완료 | `docs/sensor_quality_rules_pseudocode.md`, `docs/sensor_ingestor_runtime_flow.md` |
| 운영 시나리오와 안전 요구사항 정리 | 완료 | `data/examples/synthetic_sensor_scenarios.jsonl`, `docs/operational_scenarios.md`, `docs/safety_requirements.md`, `scripts/validate_synthetic_scenarios.py` |
| `sensor-ingestor` MVP skeleton | 완료 | `sensor-ingestor/main.py`, `sensor-ingestor/sensor_ingestor/runtime.py`, `sensor-ingestor/sensor_ingestor/config.py` |

## Phase -1 완료 판정

- 설계 문서, 스키마, seed dataset, eval set, registry 규칙, shadow report 포맷이 모두 존재한다.
- 따라서 **실측 데이터 없는 상태에서 AI 준비 구축과 MLOps 기반 설계는 완료**로 판정한다.
- 다음 단계의 중심은 문서 설계보다 `real shadow window` 누적, blind50 validator 잔여 `5건` 축소, extended200 validator 잔여 `42건` 우선순위 batch 설계, synthetic shadow `day0` residual `4건` 해소다.
- `24건` eval은 append-only `core24` 회귀셋으로 유지하고, `extended120` minimum benchmark와 `extended200 + blind_holdout50` frozen coverage는 이미 확보했다.
- 후속 challenger 비교는 `core24 + extended120 + extended160 + extended200 + blind_holdout50 + raw/validator gate` 묶음으로만 수행한다.
- 현재 frozen baseline은 `ds_v11`이며 결과는 `core24 0.9167`, `extended120 0.7667`, `extended160 0.75`, `extended200 0.7`, `blind_holdout50 raw 0.7`, `blind_holdout50 validator 0.9`, `strict_json_rate 1.0`이다.
- 최신 corrective candidate `ds_v14`는 `core24 0.8333`, `extended120 0.7167`, `extended160 0.6937`, `extended200 0.695`, `blind_holdout50 validator 0.9`로 `ds_v11` baseline을 넘지 못해 승격 실패다.
- `risk_level` 기준은 `docs/risk_level_rubric.md`로 분리했고, critical slice 감사는 `python3 scripts/report_risk_slice_coverage.py`로 수행한다.
- 현재 in-flight fine-tuning job은 없다. `docs/model_product_readiness_reassessment.md` 기준 submit freeze를 유지한다.
- `ds_v12`/`ds_v13`은 real shadow mode 부재와 synthetic shadow `day0 hold` 때문에 blocked challenger로만 유지한다.
- 남은 제품화 blocker는 blind50 validator 잔여 `5건`, extended200 validator 잔여 `42건`, synthetic shadow `day0` residual `4건`, real shadow mode `not_run`이다.
- 즉 공개 benchmark 개선과 제품 게이트 통과는 분리되어 있고, 후속 challenger도 반드시 같은 frozen gate와 real shadow 조건으로만 비교해야 한다.

## 개정 개발 순서

1. AI 준비 구축
2. 센서 수집 계획 보강
3. 센서 수집 구현
4. 통합 제어 시스템 개발 계획
5. 통합 제어 시스템 구현
6. 사용자 UI 대시보드 개발
7. AI 모델과 통합 제어 시스템 연결

## 1. AI 준비 구축

- 적고추/건고추 재배 지식 문서 수집: 재배 매뉴얼, 건조 기준, 수확 기준, 병해 조건, 온실 운영 SOP
- RAG 지식베이스 설계: 문서 chunking, 메타데이터, vector store, citation 저장 구조
- 파인튜닝 데이터 설계: 상태 해석, 행동 추천, 금지 행동, 실패 대응, follow_up, confidence
- 평가셋 구축: JSON 형식 준수, 금지 행동 차단, 근거 문서 반영률, 보수적 응답, hallucination
- 평가셋 운영 원칙: 현재 `24건`은 core regression set으로 동결하고, 후속 challenger 비교는 `core24 + extended120 + extended160 + extended200 + blind_holdout50 + raw/validator gate` 묶음으로 수행한다.
- 제품화 운영 원칙: `extended200 + blind_holdout50`뿐 아니라 `blind_holdout >= 0.95`, safety invariant fail `0`, field usability fail `0`, real shadow mode pass가 동시에 필요하다.
- 모델/프롬프트 버전 관리: prompt version, model version, dataset version, eval version
- 의사결정 시뮬레이터: 실제 온실 없이도 센서 상태 JSON을 넣고 LLM 판단을 검증하는 offline runner

현재 연결 문서:

- `docs/offline_agent_runner_spec.md`
- `docs/agent_tool_design.md`
- `docs/mlops_registry_design.md`
- `docs/fine_tuning_objectives.md`
- `docs/fine_tuning_runbook.md`
- `docs/openai_fine_tuning_execution.md`
- `docs/shadow_mode_report_format.md`
- `data/examples/synthetic_sensor_scenarios.jsonl`
- `docs/post_construction_sensor_cutover.md`

## 2. 센서 수집 계획 보강

수집 센서는 AI 학습과 제어 판단에 직접 연결되도록 분류한다.

현재 상세 문서:

- `docs/site_scope_baseline.md`
- `docs/seasonal_operation_ranges.md`
- `docs/sensor_model_shortlist.md`
- `docs/device_setpoint_ranges.md`
- `docs/device_operation_rules.md`
- `docs/sensor_collection_plan.md`
- `docs/sensor_installation_inventory.md`
- `schemas/sensor_catalog_schema.json`
- `data/examples/sensor_catalog_seed.json`
- `docs/sensor_ingestor_config_spec.md`
- `schemas/sensor_ingestor_config_schema.json`
- `data/examples/sensor_ingestor_config_seed.json`
- `docs/sensor_quality_rules_pseudocode.md`
- `docs/sensor_ingestor_runtime_flow.md`

- 환경 센서: 온도, 상대습도, CO2, 광량/PAR, 일사량
- 배지/양액 센서: 배지 함수율, EC, pH, 배액량, 배액 EC/pH, 양액 온도
- 외기 센서: 외기 온도, 외기 습도, 풍속, 강우, 외부 일사
- 장치 상태: 순환팬, 차광커튼, 환기창, 관수 밸브, 난방기, CO2 공급기, 제습기
- 비전 데이터: 작물 이미지, 과실 숙도, 병징 의심, 잎 상태, 수확 후보
- 운영 이벤트: 관수 실행, 차광 변경, 환기 변경, 작업자 개입, 알람, 수동 override

각 데이터는 `zone_id`, `sensor_id`, `timestamp`, `value`, `unit`, `quality_flag`, `source`, `calibration_version`을 포함한다.

현재 단계에서는 zone 구조, naming 규칙, sample_rate, quality_flag 기준, must_have/should_have 우선순위에 더해 설치 수량 가정, protocol, calibration 주기, model_profile, poller profile, connection, binding group, publish target까지 문서화했다. 배지 조건은 `Grodan Delta 6.5` 육묘 block과 `Grodan GT Master` 본재배 slab를 기본 전제로 두고, 근권 센서/배액 판단/관수 펄스 정책도 이 환경을 기준으로 설계한다. 핵심 센서 8종의 1차 상용 모델 shortlist는 `docs/sensor_model_shortlist.md`에 정리했고, 최종 발주 모델과 PLC 주소 체계는 다음 구현 단계에서 확정한다.

## 3. 센서 데이터 분석 및 AI 학습 반영

센서 데이터가 들어오면 다음 흐름으로 학습에 반영한다.

1. Raw data 저장
2. 품질 검사: missing, stale, outlier, jump, calibration error
3. 특징량 생성: VPD, DLI, trend, stress_score, 배지 회복률, 배액률
4. 이벤트 정렬: 센서 변화와 장치 명령, 수동 조작, 알람을 시간축으로 연결
5. 라벨링: 좋은 판단, 나쁜 판단, 차단된 행동, 승인 거절, 센서 이상, 작물 반응
6. 평가셋 갱신: edge case, 계절별 케이스, 센서 장애 케이스 추가
7. RAG 갱신: 새 SOP, 운영 노하우, 실패 사례 문서화 후 인덱싱
8. 파인튜닝 후보 생성: 반복되는 판단 패턴과 출력 형식 오류를 학습 데이터로 변환
9. 모델 평가: 기존 champion 모델과 후보 모델 비교
10. 승인 후 배포: shadow mode에서 검증 후 제한 적용

이 단계에서 model 승격과 추가 fine-tuning 재개는 아래 게이트를 먼저 통과해야 한다. 현재 minimum gate와 frozen coverage는 이미 확보했지만, 제품 수준 재개 기준은 아직 real shadow와 residual 축소까지 포함해 미충족 상태다.

- `python3 scripts/report_eval_set_coverage.py --enforce-minimums`
- total eval rows `>= 120`
- `forbidden_action >= 12`
- `failure_response >= 12`
- `edge_case >= 16`
- `seasonal >= 16`
- 다음 fine-tuning 재개 전 목표:
  - blind50 validator 잔여 `5건`에 대해 `risk_rubric_and_data 2`, `data_and_model 3` 기준 targeted fix 여부 확정
  - extended200 validator 잔여 `42건`에 대해 `risk_rubric_and_data 34`, `data_and_model 13`, `robot_contract_and_model 2` 우선순위 batch 설계
  - synthetic shadow `day0` residual `4건`(`create_alert` 누락 `3`, `inspect_crop` enum drift `1`) 해소
  - real shadow case를 누적해 실제 `promotion_decision` window를 채우고 submit preflight에 연결
  - `ds_v12` frozen dry-run package와 `ds_v13` next-only candidate 중 실제 submit 후보 결정

## 4. MLOps 루프

MLOps는 다음 폐쇄 루프로 운영한다.

```text
데이터 수집
→ 품질 검증
→ 특징량 생성
→ 라벨링/사례 분류
→ RAG 문서 갱신
→ 파인튜닝 데이터 후보 생성
→ eval 실행
→ 모델/프롬프트/정책 버전 등록
→ shadow 배포
→ 운영 로그 모니터링
→ 재학습 후보 축적
```

모델 레지스트리는 최소한 `candidate`, `staging`, `champion`, `archived` 상태를 가진다. 운영 투입은 eval 기준과 shadow mode 기준을 모두 통과한 버전만 가능하다.

## 5. AI 진화 전략

- 1단계: RAG 기반 재배 지식 검색 + 규칙 기반 안전 정책 + LLM structured output
- 2단계: 행동 추천/금지 행동 데이터로 supervised fine-tuning
- 3단계: 센서 이벤트와 운영자 승인/거절 로그를 이용해 평가셋 확대
- 4단계: 생육 단계, 계절, 품종, 온실 구역별 추천 성능 비교
- 5단계: 이상 탐지, 수확 예측, 병해 위험 예측 등 보조 ML 모델 추가
- 6단계: champion/challenger 방식으로 모델을 지속 비교하고 안전한 모델만 승격

## 6. 통합 전 게이트

- 센서 스키마와 품질 플래그가 정의되어야 한다.
- RAG 검색 결과가 citation으로 decision log에 남아야 한다.
- LLM 출력은 JSON schema를 통과해야 한다.
- 정책 엔진이 hard block과 approval 판단을 수행해야 한다.
- 모델 변경은 eval 결과와 버전 기록 없이 운영에 반영하지 않는다.
- AI 모델은 통합 제어 시스템 구현 후, shadow mode부터 연결한다.
- `24건` core regression만으로 challenger를 승격하지 않는다.
- frozen gate와 real shadow window가 확보되기 전에는 새 fine-tuning spend보다 잔여 실패 축소와 shadow 검증을 우선한다.

## 참고 근거

- OpenAI Evaluation best practices: https://platform.openai.com/docs/guides/evaluation-best-practices
- OpenAI Evals API: https://platform.openai.com/docs/api-reference/evals
- OpenAI Retrieval guide: https://platform.openai.com/docs/guides/retrieval
- OpenAI Fine-tuning guide: https://platform.openai.com/docs/guides/fine-tuning
- MLflow Model Registry: https://mlflow.org/docs/latest/ml/model-registry/
- Kubeflow Pipelines: https://www.kubeflow.org/docs/components/pipelines/overview/
