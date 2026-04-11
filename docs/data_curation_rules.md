# Data Curation Rules

이 문서는 `2.4 데이터 정제`를 위해 seed/eval JSONL 작성 시 지켜야 할 정규화 규칙을 정의한다.

## 1. 기본 정제 절차

1. JSONL 파싱 검증
2. `sample_id` 또는 `eval_id` 중복 확인
3. `task_type`와 필수 필드 확인
4. 용어, 단위, zone, growth stage, risk label 정규화
5. citation 누락 여부 확인
6. 모순 샘플은 `review_needed` 목록으로 분리

## 2. 정규화 규칙

- 장치명: `circulation_fan`, `vent_window`, `shade_curtain`, `irrigation_valve`, `heater`, `co2_doser`
- 단위: `degC`, `pct`, `ppm`, `dS_m`, `pH`, `umol_m2_s`, `W_m2`, `L`
- zone 표기: `gh-01-zone-a` 같은 `zone_id` 또는 평가용 `zone-a`, `zone-b`를 혼용하지 말고 파일 내 한 방식으로 통일
- 생육 단계: `schemas/state_schema.json`의 enum만 사용
- 위험도: `low`, `medium`, `high`, `critical`, `unknown`
- follow_up check_type: `sensor_recheck`, `visual_inspection`, `device_readback`, `operator_confirm`, `trend_review`, `lab_test`, `other`

## 3. 서술 스타일

- `situation_summary`: 현재 상태를 한두 문장으로 요약
- `reason`: 왜 그 행동을 추천하거나 차단하는지 직접 설명
- `follow_up.description`: 현장에서 바로 확인 가능한 문장으로 작성
- citation이 필요한 판단은 `chunk_id`, `document_id`를 함께 적는다.

## 4. 중복과 모순 처리

- 같은 `sample_id`는 허용하지 않는다.
- 같은 입력인데 서로 다른 `preferred_output`이 있으면 `trust_level`과 source를 비교해 하나만 남긴다.
- 공식 지침과 현장 사례가 충돌하면 공식 지침을 우선하고, 현장 사례는 `farm_case`나 note로 분리한다.

## 5. 현재 적용 범위

이 규칙은 아래 파일군에 우선 적용한다.

- `data/examples/*.jsonl`
- `evals/*_eval_set.jsonl`

검증은 `scripts/validate_training_examples.py`로 수행한다.
