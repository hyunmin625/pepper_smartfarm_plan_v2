# MLOps Registry Design

이 문서는 Phase -1에서 필요한 `dataset`, `prompt`, `model`, `eval` 버전 관리와 champion/challenger 승격 규칙을 정의한다.

## 관리 대상

1. `dataset registry`
2. `prompt registry`
3. `model registry`
4. `eval set registry`
5. `retrieval profile registry`

## 식별자 규칙

- dataset: `dataset-<type>-<yyyymmdd>-vNNN`
- prompt: `prompt-<task>-<yyyymmdd>-vNNN`
- model: `model-<base>-<yyyymmdd>-vNNN`
- eval set: `eval-<scope>-<yyyymmdd>-vNNN`
- retrieval profile: `retrieval-<backend>-<yyyymmdd>-vNNN`

## Dataset Registry

필수 필드:

- `dataset_id`
- `dataset_type`: `sft`, `preference`, `eval`, `rag_seed`, `farm_case`
- `schema_version`
- `source_refs`
- `row_count`
- `coverage_tags`
- `created_at`
- `owner`
- `approval_status`

## Prompt Registry

필수 필드:

- `prompt_id`
- `task_type`
- `template_hash`
- `tool_contract_version`
- `response_schema_version`
- `rag_profile_id`
- `created_at`
- `owner`

## Model Registry

필수 필드:

- `model_id`
- `base_model`
- `adapter_or_ft_job_id`
- `compatible_prompt_ids`
- `compatible_dataset_ids`
- `status`: `candidate`, `staging`, `champion`, `archived`
- `eval_summary`
- `promotion_note`

## Eval Set Registry

필수 필드:

- `eval_set_id`
- `scope`
- `scenario_count`
- `category_distribution`
- `grading_contract_version`
- `frozen_at`

규칙:

- eval set은 실행 전에 freeze한다.
- 점수 기준을 바꾸면 새 `eval_set_id`를 발급한다.
- 과거 모델 점수는 예전 eval set과 함께 보존한다.

## Retrieval Profile Registry

필수 필드:

- `retrieval_profile_id`
- `vector_backend`
- `embedding_backend`
- `text_match_weight`
- `metadata_match_weight`
- `vector_weight`
- `local_blend_weight`
- `collection_name`

## Champion / Challenger 규칙

승격 최소 기준:

- JSON schema pass rate `>= 0.98`
- forbidden action rate `= 0`
- citation coverage `>= 0.95`
- retrieval hit rate `>= 0.95`
- approval 누락 `= 0`
- shadow mode에서 critical disagreement `= 0`

운영 승격 순서:

1. `candidate`
2. `staging`
3. `champion`

강등 조건:

- 정책 위반 발견
- citation 누락 급증
- shadow mode disagreement 증가
- operator override가 기준치 초과

## 운영 로그 → 학습 후보 변환 규칙

- `sensor_quality=bad` 구간은 기본적으로 학습 후보에서 제외한다.
- `approved + successful outcome` 사례는 `preferred_output` 후보로 변환한다.
- `rejected` 또는 `operator_override` 사례는 금지행동 또는 correction 샘플로 분리한다.
- 같은 오류가 반복되면 preference data보다 policy rule 보강을 먼저 검토한다.

## 저장 위치

- registry 문서: `docs/`
- 실제 registry 메타데이터: 추후 `registry/` 또는 DB 테이블
- artifact: `artifacts/offline_runs/`, `artifacts/rag_index/`, `artifacts/chroma_db/`
