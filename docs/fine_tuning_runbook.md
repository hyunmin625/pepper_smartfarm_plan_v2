# Fine-tuning Runbook

이 문서는 `3.3 학습 실행`의 기준 문서다. 목적은 현재 seed/eval 상태에서 사용할 base model, 내부 버전 규칙, 실험명 규칙을 고정하는 것이다.

## 1. 현재 선택

### 1.1 파인튜닝 방식

- 현재 단계의 기본 방식은 `SFT`다.
- 이유:
  - 목표가 structured JSON 출력 안정화, 허용 `action_type` 제한, 안전 거절, `follow_up` 일관화에 있기 때문이다.
  - 아직 운영자 선호/거절 로그가 충분하지 않아 `DPO`는 다음 단계로 미룬다.
  - 현재 과제는 고난도 reasoning 보강보다 운영형 출력 교정이 중심이므로 `RFT` 대상이 아니다.

### 1.2 base model 결정

- 주력 SFT base model: `gpt-4.1-mini-2025-04-14`
- 비교용 challenger base model: `gpt-4.1-2025-04-14`
- 비용 점검용 exploratory base model: `gpt-4.1-nano-2025-04-14`

선정 이유:

- OpenAI 공식 문서 기준으로 위 세 모델이 현재 `SFT`를 지원한다.
- `gpt-4.1-mini-2025-04-14`는 구조화 출력 안정화와 반복 zone 평가를 함께 고려할 때 현재 저장소 목적에 가장 현실적인 기본값이다.
- `gpt-4.1-2025-04-14`는 더 높은 품질이 필요한 비교 기준으로 유지한다.
- `gpt-4.1-nano-2025-04-14`는 저비용 후보이지만, 실제 승격은 eval 통과 전까지 금지한다.

## 2. 내부 모델 버전 규칙

- 형식: `pepper-ops-sft-v{major}.{minor}.{patch}`
- 예:
  - `pepper-ops-sft-v1.0.0`
  - `pepper-ops-sft-v1.1.0`
  - `pepper-ops-sft-v2.0.0`

증분 기준:

- `major`: 출력 계약, 허용 `action_type`, 정책 연동 방식이 바뀔 때
- `minor`: dataset/eval/prompt 보강으로 성능이 개선될 때
- `patch`: 데이터 정제, 로그 수정, 메타데이터 수정처럼 동작 의미가 바뀌지 않을 때

## 3. 실험명 규칙

- 형식:
  - `ft-sft-{base_model_short}-{dataset_version}-{prompt_version}-{eval_version}-{yyyymmdd}`
- 예:
  - `ft-sft-gpt41mini-ds_v1-prompt_v1-eval_v1-20260411`
  - `ft-sft-gpt41-ds_v2-prompt_v1-eval_v2-20260418`

권장 약어:

- `gpt-4.1-mini-2025-04-14` -> `gpt41mini`
- `gpt-4.1-2025-04-14` -> `gpt41`
- `gpt-4.1-nano-2025-04-14` -> `gpt41nano`

## 4. 실행 전 게이트

- `artifacts/training/combined_training_samples.jsonl` 생성 완료
- `artifacts/training/combined_eval_cases.jsonl` 생성 완료
- `artifacts/reports/training_sample_stats.json` 검토 완료
- `docs/training_sample_manual_review.md` 검토 완료
- `schemas/action_schema.json` 필수 필드와 `docs/fine_tuning_objectives.md`가 일치해야 함

## 5. 현재까지 완료된 항목

- 실제 fine-tuning job 실행 완료
- run log 보관 완료
- 실패 케이스 기록 완료
- 결과 비교표 작성 완료

현재 champion은 `ds_v3/prompt_v3` 조합이며, 다음 제출 전에는 challenger 데이터셋과 prompt draft만 다시 고정하면 된다.

## 6. 다음 candidate

- 다음 후보 버전은 `pepper-ops-sft-v1.3.0`로 둔다.
- 기준 조합:
  - `dataset_version=ds_v4`
  - `prompt_version=prompt_v4`
  - `eval_version=eval_v1`
- `ds_v4`에는 batch5 실패 보강 8건을 포함한다.
- 현재 seed 총량은 `164건`이고, `prompt_v4` 전용 OpenAI SFT draft 파일은 train `150`, validation `14`다.
- `prompt_v4`는 ds_v3/prompt_v3 eval에서 남은 `risk_level_match 5건`, `required_action_types_present 5건`을 직접 겨냥한 draft다.
