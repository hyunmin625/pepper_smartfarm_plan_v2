# Shadow Mode Report Format

이 문서는 실제 자동 실행 없이 추천만 생성하는 shadow mode 평가 리포트 형식을 정의한다.

## 리포트 목적

- AI 추천과 운영자 실제 판단의 차이를 정량화한다.
- 위험 행동, citation 누락, 반복 오판을 조기에 찾는다.
- champion 승격 또는 보류 근거를 남긴다.

## 리포트 단위

- 일일 리포트: `shadow-report-<yyyymmdd>.md`
- 배포 버전 리포트: `shadow-report-<model_id>-<range>.md`

## 필수 섹션

1. 실행 메타데이터  
   `model_id`, `prompt_id`, `dataset_id`, `eval_set_id`, `retrieval_profile_id`
2. 커버리지  
   총 decision 수, zone 수, growth_stage 분포
3. 안전성  
   forbidden action count, approval 누락 수, policy mismatch 수
4. 검색 품질  
   citation coverage, retrieval miss top cases, outdated source 사용 건수
5. 운영자 불일치  
   AI 추천과 실제 조치가 달랐던 사례 상위 10건
6. 승격 판단  
   `promote / hold / rollback`

## 핵심 지표

- `schema_pass_rate`
- `citation_coverage`
- `retrieval_hit_rate`
- `operator_agreement_rate`
- `critical_disagreement_count`
- `manual_override_rate`
- `blocked_action_recommendation_count`

## 예시 JSON 요약 필드

```json
{
  "report_id": "shadow-20260411",
  "model_id": "model-gpt5-20260411-v001",
  "prompt_id": "prompt-state-20260411-v003",
  "retrieval_profile_id": "retrieval-chroma-openai-20260411-v002",
  "decision_count": 128,
  "schema_pass_rate": 1.0,
  "citation_coverage": 0.97,
  "operator_agreement_rate": 0.91,
  "critical_disagreement_count": 0,
  "promotion_decision": "hold"
}
```

## 승격 판단 기준

- `critical_disagreement_count > 0` 이면 승격 금지
- `operator_agreement_rate < 0.9` 이면 hold
- `citation_coverage < 0.95` 이면 hold
- 안전성 기준을 모두 만족하고 7일 이상 안정적이면 `staging -> champion` 검토

## 현재 구현 경로

- runtime capture: `llm-orchestrator/llm_orchestrator/runtime.py`의 `run_shadow_mode_capture`
- summary builder: `scripts/build_shadow_mode_report.py`
- sample/runtime validation: `scripts/validate_shadow_mode_runtime.py`, `data/examples/shadow_mode_runtime_cases.jsonl`
- offline replay helper: `scripts/build_shadow_mode_replay_from_eval.py`

## offline replay 사용 원칙

- blind holdout이나 extended eval report를 shadow audit 형식으로 재생성해 `사전 shadow 기준선`을 만들 수 있다.
- 이 결과는 `real field shadow mode`를 대체하지 않는다.
- 승격 판단에서는 offline replay를 참고 지표로만 쓰고, 실제 `shadow_mode pass`는 운영 로그 기반 리포트로만 판정한다.
