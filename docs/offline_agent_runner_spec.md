# Offline Agent Runner Spec

이 문서는 실측 센서가 없는 상태에서 적고추 전문가 AI Agent를 검증하기 위한 offline runner 요구사항을 정의한다.

## 목적

- 합성 센서 상태와 RAG 문맥으로 판단 품질을 반복 검증한다.
- 모델, 프롬프트, 검색 설정, 정책 설정을 같은 입력으로 재현 가능하게 비교한다.
- 실제 장치 제어 없이 JSON 출력, citation, 정책 위반 여부를 확인한다.

## 실행 단위

- 1회 실행 단위: `run_id`
- 입력 단위: `scenario_id`
- 비교 단위: `model_version`, `prompt_version`, `dataset_version`, `eval_set_version`, `retrieval_profile`

## 입력

1. 상태 입력  
   `schemas/state_schema.json` 기준의 zone state JSON
2. 합성 시나리오  
   [synthetic_sensor_scenarios.jsonl](/home/user/pepper-smartfarm-plan-v2/data/examples/synthetic_sensor_scenarios.jsonl)
3. 검색 설정  
   `vector_backend`, metadata filter, top_k
4. 정책 설정  
   hard block, approval rule, cooldown rule 버전

## 처리 단계

1. 입력 JSON schema 검증
2. `sensor_quality`와 `active_constraints` 사전 검사
3. RAG retrieval 실행
4. Agent 판단 생성
5. `action_schema.json` 검증
6. citation coverage 검증
7. 정책 위반 검사
8. 평가셋과 비교해 grade 산출
9. run artifact 저장

## 출력 산출물

- `decision.json`: Agent 출력 원문
- `retrieval.json`: retrieved chunk, score, filters
- `policy_check.json`: block/approval 결과
- `eval_result.json`: schema pass, forbidden action, citation coverage, expected match
- `run_summary.md`: 사람이 보는 요약 리포트

권장 저장 경로:

```text
artifacts/offline_runs/<run_id>/
```

## 필수 검증 항목

- JSON schema pass rate
- forbidden action count
- approval required 누락 여부
- citation coverage
- retrieval coverage
- risk_level 일치율
- operator follow_up 적정성

## 완료 기준

- 같은 `scenario_id`에 대해 재실행 시 동일 설정이면 동일 결과를 재현할 수 있다.
- 실측 데이터 없이도 최소 `normal / climate / rootzone / nutrient / sensor_fault / harvest` 6개 범주를 검증할 수 있다.
- 결과가 [mlops_registry_design.md](/home/user/pepper-smartfarm-plan-v2/docs/mlops_registry_design.md)의 registry 항목에 기록될 수 있어야 한다.

## Phase -1 범위

현재 단계에서는 구현이 아니라 스펙 확정이 목표다. 실제 실행 스크립트는 다음 단계에서 `scripts/run_farm_ai.py` 또는 별도 replay runner로 구현한다.
