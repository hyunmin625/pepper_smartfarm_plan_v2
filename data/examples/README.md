# Training Example Seeds

이 디렉터리는 적고추 전문가 AI Agent의 파인튜닝 후보 데이터를 관리한다.

## 파일

- `qa_reference_samples.jsonl`: citation이 필요한 질의응답형 설명 seed
- `qa_reference_samples_batch2.jsonl`: `qa_reference` seed를 총 20건으로 확장하는 추가 묶음
- `state_judgement_samples.jsonl`: 센서 상태와 RAG 문맥을 보고 상태를 판단하는 예시
- `state_judgement_samples_batch2.jsonl`: 상태판단 계열 seed를 총 20건으로 확장하는 추가 묶음
- `state_judgement_samples_batch4.jsonl`: ds_v2 eval 실패(state/safety 6건)를 직접 반영한 추가 묶음
- `action_recommendation_samples.jsonl`: 추천 행동과 승인 필요 여부를 구조화해 출력하는 예시
- `action_recommendation_samples_batch2.jsonl`: 행동추천 seed를 총 20건으로 확장하는 추가 묶음
- `action_recommendation_samples_batch4.jsonl`: ds_v2 eval 실패(action 2건)의 위험도 보정용 추가 묶음
- `forbidden_action_samples.jsonl`: 위험하거나 승인 없이는 실행하면 안 되는 행동을 차단하는 예시
- `forbidden_action_samples_batch2.jsonl`: 금지행동 seed를 총 20건으로 확장하는 추가 묶음
- `forbidden_action_samples_batch4.jsonl`: ds_v2 eval 실패(decision 1건)의 승인 요구 보정용 추가 묶음
- `failure_response_samples.jsonl`: 센서/장치/통신 장애 시 fallback과 안전 대응을 생성하는 예시
- `failure_response_samples_batch2.jsonl`: 장애대응 seed를 총 20건으로 확장하는 추가 묶음
- `robot_task_samples.jsonl`: 수확/점검 후보의 로봇 작업 우선순위를 정하는 예시
- `robot_task_samples_batch2.jsonl`: 로봇작업 seed를 총 20건으로 확장하는 추가 묶음
- `state_judgement_samples_batch15_hard_cases.jsonl`: `worker_present`, `manual_override`, noisy sensor, rootzone evidence loss 같은 hard-case 전용 추가 묶음
- `failure_response_samples_batch15_hard_cases.jsonl`: 통신 단절, 장치 stuck, reboot recovery 같은 safe-mode hard-case 전용 추가 묶음
- `robot_task_samples_batch6_hard_cases.jsonl`: `worker_present`, `estop_active` 아래 robot task 차단 hard-case 추가 묶음
- `state_judgement_samples_batch16_safety_reinforcement.jsonl`: `worker_present`, `manual_override`, `safe_mode`에서 `critical + block_action + create_alert`를 강제하는 safety reinforcement 묶음
- `failure_response_samples_batch16_safety_reinforcement.jsonl`: 핵심 밸브/팬/heater/양액기 readback·통신 소실에서 `critical + enter_safe_mode`를 강제하는 reinforcement 묶음
- `reporting_samples.jsonl`: 운영자 알람과 보고서 문구를 생성하는 예시
- `reporting_samples_batch2.jsonl`: 보고/알람 seed를 총 20건으로 확장하는 추가 묶음
- `synthetic_sensor_scenarios.jsonl`: 실측 데이터가 없을 때 offline runner와 eval에 넣을 합성 센서 상태 시나리오
- `sensor_catalog_seed.json`: zone별 설치 위치, protocol, calibration, model_profile까지 포함한 현장형 수집 카탈로그 seed
- `sensor_ingestor_config_seed.json`: poller profile, connection, binding group, publish target을 포함한 `sensor-ingestor` 설정 seed
- `farm_case_candidate_samples.jsonl`: 운영 로그를 `farm_case` RAG 후보로 승격하기 전 검토하는 성공/실패 사례 샘플

## 작성 원칙

- 자주 바뀌는 기준값은 샘플에 고정하지 않고 RAG citation으로 연결한다.
- 출력은 구조화된 JSON을 유지한다.
- 위험 상황에서는 자동 실행보다 보수적 판단, 승인 요청, follow_up을 우선한다.
- 센서 품질이 나쁘면 장치 제어 추천을 제한한다.
- 현재 학습 seed 기본선은 `batch4` 기준 총 `156건`이다.
- 합성 시나리오는 실제 운영 이벤트와 유사한 추세/센서 품질 문제를 재현해야 한다.
- `synthetic_sensor_scenarios.jsonl`은 정상, 환경 스트레스, 센서 장애, 장치 stuck, 정전/재기동, 사람 개입, 로봇 중단까지 포함해야 한다.
- 카탈로그 seed는 실제 장비 선정 전까지 수집 계약과 `sensor-ingestor` 설정 초안의 기준점 역할을 한다.
- `sensor_ingestor_config_seed.json`은 catalog의 센서/장치를 빠짐없이 한 번씩 binding하는 것을 기본 원칙으로 둔다.
- seed 검증은 `python3 scripts/validate_training_examples.py`로 수행한다.
- 합본 training JSONL 생성은 `python3 scripts/build_training_jsonl.py --include-source-file`로 수행한다.
- 샘플 통계 리포트 생성은 `python3 scripts/report_training_sample_stats.py`로 수행한다.
- `farm_case` 샘플 검증은 `python3 scripts/validate_farm_case_candidates.py`로 수행한다.
- `sensor-ingestor` 설정 검증은 `python3 scripts/validate_sensor_ingestor_config.py`로 수행한다.
- 합성 시나리오 검증은 `python3 scripts/validate_synthetic_scenarios.py`로 수행한다.

## 다음 확장

1. 행동추천/금지행동 샘플을 100건 수준으로 확장
2. 품종별/계절별 행동추천 샘플 추가
3. 운영자 승인/거절 로그가 생기면 preference pair로 확장
4. 합성 센서 시나리오를 계절/재배형태별로 30건 이상으로 확장
