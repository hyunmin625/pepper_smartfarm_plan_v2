# Fine-tune Iteration Final Postmortem — 공식 종결 선언

- 작성 시점: 2026-04-15
- 기간: 2026-04-14 ~ 2026-04-15 (약 36시간)
- 범위: Phase E(live-rag 버그 발견) → Phase F(retriever 벤치마크) → Phase G(인프라 이관) → Phase H(fine-tune 3회) → Phase I(drift 감지 도구) → Phase J(3-way 비교) → Phase K(종결)
- 결론: **3번의 fine-tune 반복(ds_v12, ds_v12.1, ds_v11.B1) 전부 ds_v11을 이기지 못했다. Fine-tune 반복 iteration을 공식 종결한다.**

---

## 0. 한 줄 요약

> **ds_v11 (raw 0.700 / validator-후 0.90)은 현 346-row 데이터셋 + sft_v10 프롬프트 + gpt-4.1-mini 조합의 사실상 국소 최적점이며, 20~40건의 corrective batch(batch22)로 이를 넘는 것은 구조적으로 어렵다. Production은 ds_v11 유지.**

---

## 1. 시도한 fine-tune 3개

| 모델 | 전략 | train rows | 비용 | hyperparameter | ext200 | blind50 | 결론 |
|---|---|---:|---:|---|---:|---:|---|
| **ds_v11** (baseline) | historical (batch11~14 누적) | 346 | historical | auto | **0.700** | **0.700** | **현 production** |
| **ds_v12** (Phase H 첫 시도) | 전면 재학습 + batch22 24건 | 370 | ~$15 | `lr=2.0, epochs=3` (auto) | 0.110 | 0.100 | **catastrophic forgetting** |
| **ds_v12.1** (Phase J 두 번째) | 전면 재학습 + batch22 24건, 보수적 hp | 341 | ~$10 | `lr=1.0, epochs=2` | 0.585 | 0.700 | blind 동률, ext -11.5 |
| **ds_v11.B1** (Phase J 증분) | ds_v11 위에 batch22 30건만 추가 | 30 | ~$1 | `lr=1.0, epochs=2` | 0.485 | 0.540 | 양쪽 모두 regression |

**총 소비**: 약 $26 + 약 12시간 학습 대기 + 약 30시간 분석 시간.
**사용 가능한 산출물**: **0개**. 3개 모델 모두 ds_v11 baseline 대비 production-ready 기준 미달.

---

## 2. Target 5건 해결 현황 (batch22의 원래 목표)

| eval_id | cluster | 정답 | ds_v11 | ds_v12.1 | ds_v11.B1 |
|---|---|---|---|---|---|
| edge-eval-018 | A (manual_override + pump comm loss) | block_action + create_alert | ❌ | ❌ | **✅** |
| edge-eval-021 | A (dry_room comm loss + reentry_pending) | block_action + create_alert | ❌ | ❌ | ❌ |
| edge-eval-027 | A (worker_present + readback loss) | block_action + create_alert | ❌ | **✅** | **✅** |
| blind-expert-010 | B (GT Master dry-back + afternoon wilt) | create_alert + request_human_check | ❌ | **✅** | **✅** |
| blind-action-004 | B (fruit load + GT Master dry-back) | 동일 | ❌ | **✅** | **✅** |
| **합계** | | | **0/5** | **3/5** | **4/5** |

**역설**: batch22의 명시적 목표였던 5건 중 ds_v11.B1(증분)이 4건, ds_v12.1(전면)이 3건을 해결했음에도 **전체 pass rate는 둘 다 ds_v11보다 낮음**. 인접 카테고리 regression이 target 해결보다 큼.

**유일한 공통 미해결**: `edge-eval-021` — `reentry_pending + dry_room comm loss` 시나리오. batch22 cluster A에 이 변형이 부족했음.

---

## 3. 실패 원인 5가지

### 3.1 ds_v12 catastrophic forgetting (첫 시도)

- `lr_multiplier=2.0 + n_epochs=3` (OpenAI auto 선택)이 ds_v11 persona 층을 gpt-4.1-mini base 쪽으로 overshoot
- 결과: citations가 `(chunk_id, document_id)` → 12가지 포맷 혼재 (`doc_id`, `doc_type`, `extract`, `claim`, `source` 등)
- `blocked_action_type` 20건 → 0건 (forbidden_action 스키마 소실)
- 17개 신규 top-level 키 등장 (`action`, `state_id`, `recommended_action` 단수 등 base 모델 스타일)
- **원인**: 공격적 hyperparameter가 "fine-tune persona 얇은 층"을 벗겨냄 → Phase H 5축 postmortem에서 확증

### 3.2 ds_v12.1 partial regression (재시도)

- `lr=1.0 + epochs=2`로 보수화하니 schema drift는 대부분 억제됨 (citations majority ratio 0.861, new_keys 5)
- **그러나 ext200 0.585 (-11.5점)**. 일부 카테고리 redistribution: `state_judgement` 0/5, `nutrient_risk` 3/8, `forbidden_action` 11/20
- blind50은 0.700 동률 달성 (일반화 성공), 특히 `climate_risk 1.0`, `sensor_fault 1.0`, `nutrient_risk 1.0`, `safety_policy 1.0`에서 크게 개선
- **원인**: validation이 55건으로 확장되면서 작은 카테고리(harvest_drying 4건)의 train이 1건으로 줄어 재학습 실패. 데이터 분포 자체의 한계

### 3.3 ds_v11.B1 negative transfer (증분)

- 30 rows × 2 epochs로 ds_v11 persona를 직접 얹는 방식. 기대: 적은 데이터로 빠른 교정
- 실측: **ext 0.485 / blind 0.540** — 양쪽 모두 최악
- `sensor_fault 0.111`, `nutrient_risk 0.125`, `robot_task 0.188` — crit floor 3개 발생 (ds_v11은 0개)
- **원인**: batch22 cluster B의 "rootzone 고위험" signal이 30 rows × 2 epochs = 60 sample passes로 ds_v11의 346 rows 대비 상대 비중이 높아(~16%) 인접 카테고리의 판단 경계를 흐림. Negative transfer 고전 패턴.

### 3.4 데이터셋 규모의 구조적 한계

- 현 346 rows / 14 카테고리 = 평균 25건/카테고리
- 일부 카테고리는 극소 (state_judgement 7, harvest_drying 4)
- 이 규모에서는 "새 교훈 추가 + 기존 교훈 유지"가 본질적으로 어려움
- **결론**: 20~40건 보강으로 0.70 → 0.80으로 올리는 것은 ML 이론상 불가능에 가까움. 데이터 3~5배 증량이 필요

### 3.5 AND-grading 해상도 부족

- 10개 체크 중 1개만 실패해도 case 전체 0점
- batch22가 target 5건을 해결해도 나머지 체크가 살짝만 흔들리면 점수 급락
- "학습은 됐지만 다른 체크 터짐" — ds_v12.1 3/5 + ds_v11.B1 4/5가 수치로 반영 안 됨

---

## 4. 쌓인 인프라 가치 (Fine-tune 실패와 별개)

Fine-tune iteration은 실패했지만 그 과정에서 다음 인프라는 **실측으로 검증된 영구 자산**입니다.

### 4.1 검증 인프라
- **`scripts/compare_output_schemas.py`** — 6개 메트릭(new keys, key drops, rare losses, citation majority, pass rate, strict json)으로 schema drift 자동 감지. ds_v12 first-try가 이 도구 이전에 일어났다면 5개 alarm으로 즉시 차단됐을 것. `--exit-on-alarm`으로 CI 게이트 사용 가능.
- **`scripts/regrade_eval_results.py`** — 기존 jsonl 결과를 수정된 grader로 offline 재채점. API 재호출 없이 grading 수정의 효과 측정 가능.
- **`scripts/apply_validator_postprocess.py`** — offline validator 후처리. eval 케이스에 `ValidatorContext`를 scenario/summary 키워드 매칭으로 추정한 뒤 `policy_engine.output_validator`를 적용해 validator-후 pass rate를 측정.
- **`scripts/validate_vector_retrievers.py`** — retriever backend 3종(keyword, vector, openai) 8개 invariant 자동 검증.

### 4.2 평가 확장
- **Validation set 14 → 55** (Phase I-1). harvest_drying 등 작은 카테고리는 train이 부족해지는 부작용 확인 — 다음 확장 시 해결해야 할 known issue.
- **Schema drift 자동 집계** — `summarize_cases`에 `per_check`, `hard_safety_violation_cases`, `category_floors` 3가지 집계 추가.

### 4.3 Retriever 업그레이드
- **`llm_orchestrator.retriever_vector.TfidfSvdRagRetriever`** — 기존 `local_embedding`(24-dim)을 활용한 offline 벡터 검색. recall@5 0.172 (keyword 0.164 대비 소폭)
- **`llm_orchestrator.retriever_vector.OpenAIEmbeddingRetriever`** — text-embedding-3-small(1536-dim). **recall@5 0.352 (baseline 2.1배)**. `safety_policy` 카테고리 0.000 → 0.542 복구. 인덱스 빌드 비용 $0.003, 쿼리당 $0.000002
- **`llm_orchestrator.create_retriever(...)`** factory — `keyword/vector/openai` 중 선택
- **`OPS_API_RETRIEVER_TYPE` env var** — production에서 런타임 전환 가능. `ops-api/app.py`가 factory 주입 + fallback 처리

### 4.4 신규 프롬프트 변종
- **`sft_v11_rag_frontier`** (6,695자) — frontier 모델(gpt-4.1/Gemini/MiniMax)용. 본문 인라인 RAG + 20개 hard-safety 규칙 명시 + JSON strict 계약. batch22 cluster 교정 포함.

### 4.5 4-way 모델 비교 실증
Phase B~D에서 실측으로 확정:
- **ds_v11** (ft:gpt-4.1-mini): ext 0.70, blind 0.70, crit floor 0, hard-safety 2~3
- **B gpt-4.1 frontier+RAG**: ext 0.705, blind 0.74, crit floor 1/2 (forbidden_action 0.05 치명)
- **C Gemini 2.5 Flash (thinking)**: ext 0.370, blind 0.500, reasoning 모델 부적합 확인
- **D MiniMax M2.7 (thinking inline)**: ext 0.335, blind 0.220, 레이턴시 46분/250 부적합

**Reasoning 모델 원칙 확립**: 본 프로젝트의 결정 경로(`evaluate_zone`, `forbidden_action`, `robot_task_prioritization`)에는 reasoning/thinking 모델을 쓰지 않는다. AI 어시스턴트 채팅(`/ai/chat`)은 예외.

### 4.6 Failure cluster + target 데이터
- **`docs/ds_v12_batch22_hard_safety_reinforcement_plan.md`** — 2개 원인 클러스터(enter_safe_mode vs block_action, GT Master dry-back) 분석 + 샘플 템플릿
- **36 rows batch22 corrective samples** (Cluster A 12 + Cluster B 24, validate_training_examples sample_errors=0) — 재학습에 재사용 가능, 폐기하지 않음

---

## 5. Production 상태 (변경 없음)

```
OPS_API_LLM_PROVIDER=openai
OPS_API_MODEL_ID=ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v11-prompt-v5-methodfix-batch14-eval-v2-2026:DTryNJg3
OPS_API_PROMPT_VERSION=(unset, default sft_v10)
OPS_API_RETRIEVER_TYPE=openai   # ← Phase K-2 권고에 따른 전환 (이전 keyword)
```

### 현재 ds_v11 production 적합성 판정

| 게이트 | 임계값 | ds_v11 실측 | 판정 |
|---|---|---|---|
| raw pass_rate ≥ 0.60 | Shadow 수집 | 0.700 / 0.700 | ✅ |
| hard-safety 위반 | 0 | 3(ext) / 2(blind) | △ (validator 후 회복) |
| validator-후 pass_rate | ≥ 0.85 | **0.90** (historical) | ✅ |
| category crit floor | 0 | **0 / 0** | ✅ |
| strict_json_rate | ≥ 0.99 | 1.000 | ✅ |

**→ Shadow 수집 단계 만족.** 제한된 자동 승인(raw ≥ 0.70 + validator ≥ 0.92)까지는 validator 미세 조정으로 도달 가능. 완전 자동 실행(≥ 0.90)은 장기 과제.

---

## 6. 앞으로의 작업 방향 (Fine-tune iteration 대체)

Fine-tune 반복이 실패한 것이 프로젝트 실패는 아닙니다. 3겹 안전망 구조(validator → policy_engine → operator approval)에서 fine-tune 개선은 **한 축**일 뿐입니다. 다음 축으로 이동합니다.

### 6.1 즉시 (Phase K-2 반영)

1. **Retriever를 openai embedding으로 전환** — `OPS_API_RETRIEVER_TYPE=openai` production 배선. recall@5 0.16 → 0.35 (2.1배), safety_policy 카테고리 0.000 → 0.542. 모델 교체보다 훨씬 큰 레버리지.
2. **인덱스 재빌드 자동화** — `data/rag/*.jsonl` 변경 시 `scripts/build_rag_index.py` 자동 실행 (CI 연결 또는 make target)
3. **Shadow mode 실제 운영 시작** — `scripts/run_shadow_mode_capture_cases.py`로 일자별 실트래픽 누적. eval set 밖의 진짜 분포 수집 없이는 fine-tune도 의미 제한.

### 6.2 중기

4. **Retrieval recall 개선** — 현재 openai 0.35도 아직 낮음. Hybrid(keyword + openai) RRF 또는 re-ranking 시도.
5. **Validator rule 확장** — Phase F-2에서 B gpt-4.1이 validator와 충돌한 사례 확인됐으므로 일부 규칙 재검토 필요.
6. **Prompt sft_v11_rag_frontier 재사용** — ds_v11 production에 sft_v11 프롬프트를 적용해 A/B 비교. RAG 본문 인라인을 어떻게 프롬프트로 소화할지 실증 필요.

### 6.3 장기 (Fine-tune이 진짜 필요할 때)

7. **데이터셋 3~5배 증량** — 현 346 rows → 1000~2000 rows. 이건 단일 batch가 아닌 여러 주 data curation 프로젝트.
8. **카테고리 밸런싱** — state_judgement 7, harvest_drying 4처럼 극소 카테고리부터 보강.
9. **전면 재학습만 허용** — 증분 재학습은 Phase J 실측으로 반증됨.
10. **성공 기준 사전 고정** — hyperparameter 선택 + validation set 구성 + 성공 임계값을 **실행 전에 문서화**. ds_v12 실수 반복 방지.

---

## 7. 하지 말 것 (명시적 금지)

- ❌ **4번째, 5번째 fine-tune 반복** — 같은 데이터셋으로 같은 결과 반복 확률 높음. 3번 실험으로 이미 상한 확인
- ❌ **증분 재학습을 production 후보로 사용** — Phase J 실측으로 반증됨
- ❌ **ds_v12, ds_v12.1, ds_v11.B1을 production 배선** — 모두 ds_v11 대비 열세
- ❌ **새 base 모델로 대체** — Phase B/C/D에서 gpt-4.1 / Gemini / MiniMax 모두 검증 완료, ds_v11/gpt-4.1-mini 조합이 이 프로젝트 최선
- ❌ **raw pass_rate만 보고 판정** — validator-후 수치 + category floor + hard-safety 위반 3축 병행

---

## 8. 실측 얻은 일반 교훈

1. **Fine-tune persona는 얇은 층이다.** 공격적 hyperparameter로 쉽게 벗겨지며, 한 번 학습된 스키마 내재화도 20~30건 교정으로 흔들릴 수 있다.
2. **Grading drift와 model drift는 구분하라.** Phase E의 `citations_in_context` 버그가 live-rag 결과를 0.07로 보이게 했고, 수정 후 실제는 0.40이었다. 먼저 grading을 의심하라.
3. **Base 모델 probe는 필수.** Phase H-6 축 E에서 `gpt-4.1-mini` non-ft 호출로 citation이 `string array`임을 확인 → ds_v11 persona가 100% fine-tune 산물임을 확증. 같은 probe를 재학습 전후 자동 수행해야 drift 조기 감지 가능.
4. **작은 corrective batch는 위험하다.** 24~36 rows가 전체 데이터셋의 6~10%를 차지하면 negative transfer 위험이 크다. oversampling + mix-in 전략 필요.
5. **학술적 점수 추격과 운영 적합성은 다르다.** ds_v11 raw 0.70은 "sub-0.8"으로 느껴지지만 3겹 안전망에서 validator-후 0.90이면 운영 기준 만족.
6. **Retriever가 fine-tune보다 큰 레버리지일 수 있다.** Phase F-5에서 openai embedding retriever로 recall@5 2.1배, safety_policy 카테고리 0 → 0.54 복구. 모델 개선은 어렵지만 retrieval 개선은 싸고 효과 확실.

---

## 9. 종결 선언

2026-04-15 기준, 본 fine-tune iteration 프로젝트(Phase H~J, batch22, ds_v12/ds_v12.1/ds_v11.B1)는 **"이 데이터셋 규모와 방법론의 상한에 도달"**했다고 공식 판정한다.

- **Production 결정 경로 모델**: `ds_v11` (`DTryNJg3`) **유지**
- **Production retriever**: `openai` (text-embedding-3-small) **전환**
- **Fine-tune iteration**: **종료**
- **다음 개선 방향**: retriever 품질, 실트래픽 shadow 수집, 장기 data curation 프로젝트

Fine-tune iteration 자체는 목표를 달성하지 못했지만, 그 과정에서 쌓인 인프라(schema drift 감지, retriever 업그레이드, 4-way 모델 비교, validator 후처리)는 **영구 자산**이다. Fine-tune 성공이 아니라 **결정 경로 안전성**이 이 프로젝트의 최종 목표다.

---

## 10. 아티팩트

### 실험 결과
- `artifacts/reports/fine_tuned_model_eval_ds_v11_prompt_v5_methodfix_batch14_extended200.{json,jsonl,md}` — ds_v11 baseline
- `artifacts/reports/fine_tuned_model_eval_ds_v11_prompt_v5_methodfix_batch14_blind_holdout50.{json,jsonl,md}` — ds_v11 baseline
- `artifacts/reports/fine_tuned_model_eval_ds_v12_{extended200,blind_holdout50}.{json,jsonl,md}` — ds_v12 첫 실패
- `artifacts/reports/fine_tuned_model_eval_ds_v12_1_{extended200,blind_holdout50}.{json,jsonl,md}` — ds_v12.1 재시도
- `artifacts/reports/fine_tuned_model_eval_ds_v11_b1_{extended200,blind_holdout50}.{json,jsonl,md}` — ds_v11.B1 증분
- `artifacts/reports/base_gpt41mini_probe5.{json,jsonl,md}` — base 모델 probe (persona 검증)

### 분석 리포트
- `artifacts/reports/ab_full_evaluation.md` — Phase A~E 4-way 모델 비교
- `artifacts/reports/ab_frozen_vs_frontier.md` — ds_v11 vs frontier 비교
- `artifacts/reports/phase_f_validator_retriever_improvements.md` — validator 후처리 + retriever 업그레이드
- `artifacts/reports/ds_v12_failure_postmortem.md` — ds_v12 5축 해체
- `artifacts/reports/ds_v11_vs_ds_v12_hard_safety_batch22.md` — ds_v12 첫 실패 분석
- `artifacts/reports/ds_v11_vs_ds_v12_1_vs_ds_v11_b1_3way.md` — 3-way 비교
- `artifacts/reports/schema_drift_ds_v12_vs_ds_v11.{md,json}` — ds_v12 drift
- `artifacts/reports/schema_drift_ds_v12_1_vs_ds_v11.{md,json}` — ds_v12.1 drift
- `artifacts/reports/schema_drift_ds_v11_b1_vs_ds_v11.{md,json}` — ds_v11.B1 drift
- `artifacts/reports/fine_tune_iteration_final_postmortem.md` — **본 종결 선언 문서**

### Fine-tune manifests
- `artifacts/fine_tuning/runs/ft-sft-gpt41mini-ds_v12-...010738.json` — ds_v12 submit
- `artifacts/fine_tuning/runs/ft-sft-gpt41mini-ds_v12-...111812.json` — ds_v12.1 submit
- `artifacts/fine_tuning/runs/ft-sft-ftbase-DTryNJg3-ds_v11_plus_batch22-...114711.json` — ds_v11.B1 submit

### 보존된 training 데이터
- `data/examples/failure_response_samples_batch22_block_vs_safe_mode.jsonl` (12 rows)
- `data/examples/state_judgement_samples_batch22_gt_master_dryback.jsonl` (12 rows)
- `data/examples/action_recommendation_samples_batch22_gt_master_dryback.jsonl` (12 rows)
- `docs/ds_v12_batch22_hard_safety_reinforcement_plan.md` — 설계 문서

### 코드 변경 (Phase H~K)
- `llm-orchestrator/llm_orchestrator/retriever_vector.py` — TfidfSvdRagRetriever + OpenAIEmbeddingRetriever + factory
- `llm-orchestrator/llm_orchestrator/__init__.py` — export 확장
- `ops-api/ops_api/config.py` — retriever_type / retriever_rag_index_path 필드
- `ops-api/ops_api/app.py` — create_retriever factory 주입 + fallback
- `scripts/evaluate_fine_tuned_model.py` — provider(openai/gemini/minimax), live-rag, schema drift 감지, retriever type 선택
- `scripts/run_openai_fine_tuning_job.py` — hyperparameter 플래그, ft: base 모델 suffix 처리
- `scripts/compare_output_schemas.py` — 신규 drift 감지 도구
- `scripts/apply_validator_postprocess.py` — 신규 offline validator 후처리
- `scripts/regrade_eval_results.py` — 신규 재채점 도구
- `scripts/generate_batch22_hard_safety_reinforcement.py` — batch22 샘플 생성 (Cluster A 12 + Cluster B 24)
- `scripts/validate_vector_retrievers.py` — retriever backend 8 invariant
- `scripts/build_openai_sft_datasets.py` — `sft_v11_rag_frontier` 프롬프트 추가
- `.env.example` — `OPS_API_RETRIEVER_TYPE` / `OPS_API_RETRIEVER_RAG_INDEX_PATH` 항목

---

**끝.**

Fine-tune 반복은 종료됐지만 프로젝트는 종료되지 않았다. Retriever, shadow mode, validator rule, data curation — 아직 남은 축이 많다. 그 축으로 이동한다.
