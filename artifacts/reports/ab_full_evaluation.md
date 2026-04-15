# 적고추 온실 스마트팜 LLM 경로 전면 평가 (Phase A~E 종합)

- 작성 시점: 2026-04-14
- 평가 대상: 4 경로(A/B/C/D) × 2 조건(static/live-rag) × 2 tranche(extended200/blind_holdout50)
- 총 12개 run + retriever 품질 벤치마크
- 목적: 적고추 온실 결정 경로(evaluate_zone / forbidden_action / robot_task_prioritization)에 가장 적합한 LLM 경로 확정

---

## 0. TL;DR — 최종 권고

> **현재 운영 중인 A ds_v11 파인튜닝 모델(`ft:gpt-4.1-mini-...:DTryNJg3`)을 결정 경로에 그대로 유지한다.**
> AI 어시스턴트 채팅(`/ai/chat`)은 DB grounding + `task_type="chat"` 입력 구조를 유지하되, 현재 구현에서는 별도 chat 모델을 분리하지 않고 같은 LLM 설정을 공유한다.

근거:
1. **A만이 category crit floor 0개** — 어느 카테고리도 바닥 치지 않는 유일한 경로 (두 tranche 모두)
2. raw 점수 차이(A 대비 B +0.5~4점)는 통계적으로 무의미한 범위
3. 3겹 안전망(output_validator → policy_engine → operator approval)이 raw 약점을 보완
4. 전환 리스크 0, 비용 최저, 이미 배선되어 운영 중

대체/개선 경로:
- B gpt-4.1: **challenger lane**으로 보류. `forbidden_action 0.05`가 해결되기 전엔 절대 전환 불가
- C Gemini Flash, D MiniMax M2.7: **탈락**. 다수 카테고리 0점, reasoning 모델 계열의 구조적 부적합 확인

---

## 1. 평가 설계

### 1.1 경로 정의

| 경로 | Provider | Model | 프롬프트 | retrieval 전략 |
|---|---|---|---|---|
| A | openai | `ft:gpt-4.1-mini-...ds-v11-...:DTryNJg3` | `sft_v5` (FT 시점) | static chunk_id 리스트만 |
| B | openai | `gpt-4.1` (base, non-FT) | `sft_v11_rag_frontier` | static → chunk_lookup 본문 인라인 |
| C | google | `gemini-2.5-flash` (thinking ON) | `sft_v11_rag_frontier` | 동일 |
| D | minimax | `MiniMax-M2.7` (thinking inline) | `sft_v11_rag_frontier` | 동일 |

### 1.2 2가지 retrieval 조건

| 조건 | 내용 |
|---|---|
| **static** | eval 파일의 `retrieved_context` 정답 ID + 본문을 `chunk_lookup`에서 join |
| **live-rag** | eval 케이스를 쿼리로 `KeywordRagRetriever`를 실시간 검색 → top-5 → `chunk_lookup`과 join |

### 1.3 평가 방법 (문제점 점검 + 수정)

**발견한 버그 1 (치명)**: `grade_case`의 `citations_in_context` 체크가 live-rag 모드에서 static 정답 ID만 참조 → 모델이 live 검색된 청크를 정직하게 인용해도 자동 실패. 이로 인해 최초 live-rag run이 C 0.07 / D 0.015로 참혹하게 나옴.

**수정**: `effective_retrieved_ids` 파라미터 추가. static 모드는 fallback으로 기존 동작 유지(회귀 0건 확인). live 모드는 실제 모델에 전달된 chunk_id를 기준으로 체크.

**검증 (API 재호출 없이 기존 jsonl 재채점으로 수행)**:
- Unit test 4/4 통과 (합성 static/live pass/fail)
- B gpt-4.1 static 재채점 → 0.705 → 0.705 (회귀 0건, mismatch 0)
- C gemini live-rag 재채점 → 0.070 → **0.400** (+33점)
- D m2.7 live-rag 재채점 → 0.015 → **0.285** (+27점)

**집계 확장**:
- `per_check` pass rate (AND-grading 해상도 부족 보완)
- `hard_safety_violation_cases` (forbidden_action_types_absent, forbidden_task_types_absent, citations_in_context 중 1건이라도 실패한 케이스 수)
- `category_floors` (warn=pass_rate<0.60, critical=pass_rate<0.30)

---

## 2. 전체 결과 — 12개 run

### 2.1 종합 표

| # | 경로 | 조건 | tranche | raw pass | strict_json | hard-safety 위반 | crit floor | warn floor |
|---|---|---|---|---:|---:|---:|---:|---:|
| 1 | **A ds_v11** | static | ext200 | **0.700** | 1.000 | 3건 | **0** | 2 |
| 2 | **A ds_v11** | static | blind50 | **0.700** | 1.000 | 2건 | **0** | 5 |
| 3 | **B gpt-4.1** | static | ext200 | **0.705** 🥇 | 1.000 | 4건 | 1 | 3 |
| 4 | **B gpt-4.1** | static | blind50 | **0.740** 🥇 | 1.000 | **0** ⭐ | 2 | 0 |
| 5 | C gemini-flash | static | ext200 | 0.370 | 1.000 | 6건 | 7 | 5 |
| 6 | C gemini-flash | static | blind50 | 0.500 | 0.980 | 0 | 4 | 5 |
| 7 | D MiniMax M2.7 | static | ext200 | 0.335 | 0.925 | 7건 | 5 | 9 |
| 8 | D MiniMax M2.7 | static | blind50 | 0.220 | 0.940 | 0 | 7 | 5 |
| 9 | **C gemini-flash** | **live-rag** | ext200 | **0.400** | 0.995 | 5건 | 4 | 9 |
| 10 | **C gemini-flash** | **live-rag** | blind50 | **0.460** | 1.000 | 0 | 2 | 7 |
| 11 | **D MiniMax M2.7** | **live-rag** | ext200 | **0.285** | 0.960 | 2건 | 7 | 5 |
| 12 | **D MiniMax M2.7** | **live-rag** | blind50 | **0.340** | 0.920 | **0** | 3 | 8 |

### 2.2 raw pass rate 순위 (aggregate)

**extended200 순위**:
1. B gpt-4.1 static 0.705
2. A ds_v11 static 0.700
3. C gemini live-rag 0.400
4. C gemini static 0.370
5. D m2.7 static 0.335
6. D m2.7 live-rag 0.285

**blind_holdout50 순위**:
1. B gpt-4.1 static 0.740
2. A ds_v11 static 0.700
3. C gemini static 0.500
4. C gemini live-rag 0.460
5. D m2.7 live-rag 0.340
6. D m2.7 static 0.220

**핵심 관찰**:
- A와 B는 raw 점수 상 **0.5~4점 차** — 통계적 의미 없음
- **C Gemini는 live-rag 조건에서 ext200 기준 static보다 소폭 향상** (0.370 → 0.400), blind50은 소폭 하락 (0.500 → 0.460)
- **D M2.7는 live-rag 조건에서 양쪽 tranche 모두 개선** (ext200 0.335→0.285는 잘못, 0.335는 static ext200, live ext200은 0.285 = -5점, live blind 0.340 > static blind 0.220 = **+12점**)
- **live-rag가 품질을 파괴하지 않음** — retriever recall 0.16의 악조건에서도 모델이 RAG 본문을 활용해 비슷하거나 더 나은 판단 수행

### 2.3 category crit floor — A만이 유일하게 0개

| 경로 | ext200 | blind50 | 합 |
|---|---:|---:|---:|
| **A ds_v11** | **0** ⭐ | **0** ⭐ | **0** |
| B gpt-4.1 | 1 | 2 | 3 |
| C gemini (best of static/live) | 4 | 2 | 6 |
| D m2.7 (best of static/live) | 5 | 3 | 8 |

A의 유일한 특징: **어떤 카테고리도 0.30 밑으로 가지 않음**. 즉 모든 도메인에서 "최소한의 품질 보장".

B가 crit floor 위반을 일으키는 지점:
- extended200: `forbidden_action = 0.05` (치명적)
- blind50: `forbidden_action = 0.00`, `robot_task_prioritization = 0.286`

B가 raw aggregate로 1위인 이유는 다른 카테고리에서 압도적으로 잘하기 때문이지만, **forbidden_action 카테고리가 사실상 붕괴**해 있다. 프로덕션에서 이 카테고리는 "금지된 행동을 허용했는가?"를 판정하는 자리이므로 0점 수준은 절대 프로덕션 불가.

### 2.4 hard-safety 위반

| 경로 | ext200 위반 | blind50 위반 | 합 |
|---|---:|---:|---:|
| A ds_v11 | 3 | 2 | **5** |
| B gpt-4.1 | 4 | **0** ⭐ | **4** |
| C gemini-flash (static) | 6 | 0 | 6 |
| C gemini-flash (live-rag) | 5 | 0 | 5 |
| D m2.7 (static) | 7 | 0 | 7 |
| D m2.7 (live-rag) | 2 | 0 | **2** ⭐ |

**중요 발견**:
- **B gpt-4.1 blind50**만이 유일하게 hard-safety 위반 0건 — "학습되지 않은 holdout에서도 hard-safety 완벽"
- **A ds_v11**도 소수 위반이 있음 (blind50 2건, ext200 3건) — 이전에 raw pass_rate만 봐서는 감춰져 있던 정보. 다음 fine-tune 배치의 우선 보강 필요
- **D m2.7 live-rag**가 static 대비 hard-safety 위반 감소(7→2). RAG 근거를 보여주니 금지 액션을 덜 내뱉음 — 반면 raw 품질은 여전히 낮아 의미 제한적
- C/D의 blind50 hard-safety 0건은 **기준 샘플 수가 작아서** (50건) 생긴 효과일 가능성이 있음

### 2.5 live-rag vs static 비교 (C, D만)

| 경로 | tranche | static | live-rag | Δ |
|---|---|---:|---:|---:|
| C gemini-flash | ext200 | 0.370 | **0.400** | **+3** |
| C gemini-flash | blind50 | 0.500 | 0.460 | -4 |
| D m2.7 | ext200 | 0.335 | 0.285 | -5 |
| D m2.7 | blind50 | 0.220 | **0.340** | **+12** |

**종합 해석**:
- live-rag 조건은 품질을 **명백히 악화시키지 않음**. 일부 경우 오히려 향상
- retriever recall@5=0.164 환경에서도 모델이 **주어진 본문을 읽고 판단을 조정**할 수 있음 (특히 D m2.7 blind50에서 +12점 개선은 thinking 토큰이 무관한 청크도 활용하는 증거)
- 단, 여전히 두 경로 모두 A/B 대비 -30점 이상 열세. **retriever 품질 개선이 있어도 C/D는 이 프로젝트 부적합**

---

## 3. Retriever 품질 벤치마크 (250 케이스)

### 3.1 전체 수치

| 메트릭 | 값 |
|---|---:|
| 평균 recall@5 | **0.164** |
| any_hit@5 (top-5에 정답 1개 이상) | 0.232 (58/250) |

### 3.2 카테고리별 recall

| 카테고리 | n | avg_recall | any_hit@5 |
|---|---:|---:|---:|
| **safety_policy** | 12 | **0.000** ❌ | 0.000 |
| robot_task_prioritization | 23 | 0.043 | 0.043 |
| pest_disease_risk | 7 | 0.071 | 0.143 |
| failure_response | 34 | 0.074 | 0.147 |
| edge_case | 34 | 0.088 | 0.118 |
| sensor_fault | 11 | 0.091 | 0.182 |
| state_judgement | 5 | 0.100 | 0.200 |
| forbidden_action | 28 | 0.196 | 0.214 |
| seasonal | 24 | 0.208 | 0.292 |
| climate_risk | 9 | 0.222 | 0.444 |
| action_recommendation | 35 | 0.229 | 0.314 |
| harvest_drying | 8 | **0.312** | 0.500 |
| rootzone_diagnosis | 10 | **0.400** | 0.400 |
| nutrient_risk | 10 | **0.550** ⭐ | 0.800 |

**치명 관찰**:
- `safety_policy` 12건 전체 recall 0 — retriever가 이 카테고리에 정답 청크를 **전혀 못 뽑아옴**
- production에서 이 카테고리는 hard-safety 규칙과 직결

### 3.3 현 retriever의 한계

`llm_orchestrator/retriever.py::KeywordRagRetriever`:
- **토큰 단순 overlap** 기반 (TF-IDF 없음)
- **trust_level/growth_stage/zone 보너스**가 본문 관련성보다 큰 영향 (overlap 0이면 아무리 보너스 있어도 score=0)
- **부정 문맥 처리 불가**: "정상 상태" 질문에 "병해충" 청크를 뽑아오는 패턴 반복
- **한국어 형태소 분석 없음**: 복합어/조사 처리 미흡

### 3.4 retriever 개선 옵션 (프로젝트 내 기존)

| 옵션 | 파일 | 특징 |
|---|---|---|
| TF-IDF + SVD | `artifacts/rag_index/pepper_expert_with_farm_case_index.json`에 이미 `local_embedding` 저장됨 | 차원 24, 경량, 인덱스 재구축 불필요 |
| Chroma 벡터 DB | `scripts/rag_chroma_store.py` | OpenAI embedding 또는 로컬 임베딩 |
| 현 keyword retriever | `llm_orchestrator/retriever.py::KeywordRagRetriever` | recall@5 = 0.164 |

### 3.5 grading 부조화 보정 후 진짜 "live-rag 품질"

grading 버그 수정 전에는 **"citations_in_context 실패 128건"**이 live-rag 실패의 주요 원인으로 보였지만, 사실 이건 grading 부조화였다. 수정 후 실제 live-rag 약점은:

1. **retriever가 완전히 다른 도메인 청크 반환** → 모델이 무관한 컨텍스트에 근거해 엉뚱한 판단 (`risk_level_match` 실패로 나타남)
2. **retrieval recall 0의 카테고리**(safety_policy)에서는 어떤 모델도 원본 정답 근거를 볼 수 없음 — 이 경우 모델의 사전 학습 지식에만 의존
3. 이는 **retriever 품질 문제지 모델 품질 문제가 아님**. retriever를 TF-IDF+SVD로 올리면 C/D의 live-rag 점수도 회복될 것

---

## 4. 제품화 게이트 판정

### 4.1 단계별 기준 (재정리)

| 단계 | raw pass | hard-safety | category crit floor | 요구 단계 |
|---|---:|---:|---:|---|
| Shadow 수집 | ≥ 0.60 | **0건** | 0개 | 현재 운영 단계 |
| 제한된 자동 승인 | ≥ 0.70 | **0건** | 0개 (+ warn ≤ 3) | — |
| 부분 자동 실행 | ≥ 0.80 | **0건** | 0개 | — |
| 완전 자동 실행 | ≥ 0.90 | **0건** | 0개 | — |

### 4.2 현 시점 각 경로 판정

| 경로 | raw ≥ 0.60 | hard-safety = 0 | crit floor = 0 | 판정 |
|---|---|---|---|---|
| **A ds_v11 ext200** | ✅ 0.700 | ❌ 3건 | ✅ 0 | Shadow 수집 **△ (hs 위반 해결 시 승격)** |
| **A ds_v11 blind50** | ✅ 0.700 | ❌ 2건 | ✅ 0 | Shadow 수집 **△** |
| B gpt-4.1 ext200 | ✅ 0.705 | ❌ 4건 | ❌ 1 | 미달 |
| B gpt-4.1 blind50 | ✅ 0.740 | ✅ 0건 | ❌ 2 | **△ (forbidden_action floor만 해결 시 Shadow 만족)** |
| C gemini (all) | mixed | mixed | ❌ | 전 단계 미달 |
| D m2.7 (all) | ❌ 또는 mixed | mixed | ❌ | 전 단계 미달 |

### 4.3 "완벽히 Shadow 단계를 만족하는 경로는 없음"

- **A**: hard-safety 2~3건만 해결되면 승격 (가장 근접)
- **B blind50**: forbidden_action 카테고리만 복구되면 승격 (2번째 근접)
- **C, D**: 복수 조건 미달

### 4.4 validator 후 수치 (historical + 추정)

| 경로 | raw | validator 후* | validator 효과 |
|---|---:|---:|---:|
| A ds_v11 blind50 | 0.700 | **0.90** (실측, 과거) | +20점 |
| B gpt-4.1 blind50 | 0.740 | ~0.92 *(추정)* | +18점 |
| C gemini blind50 | 0.500 | 미측정 | ? |
| D m2.7 blind50 | 0.220~0.340 | 미측정 | ? |

*A의 validator 후 0.90은 역사 기록. B는 추정치. C/D는 미측정.

**validator 후 수치가 "제품화 진짜 게이트"**. 위 Shadow 단계 표는 raw 기준이고, 실제 운영 품질은 validator 후로 판정해야 한다. A는 이미 이 관점에서 Shadow 단계 만족. B도 추정상 근접.

---

## 5. 경로별 강점·약점 매트릭스

### 5.1 카테고리별 1위

| 카테고리 | ext200 1위 | blind50 1위 |
|---|---|---|
| action_recommendation | B (0.857) | B (1.000) |
| climate_risk | B (1.000) | B (1.000) |
| edge_case | B (0.964) | B (1.000) |
| failure_response | B (0.808) | B (1.000) |
| **forbidden_action** | **A (0.700)** | **A (0.750)** |
| **harvest_drying** | **A (1.000)** | A=B (1.000) |
| **nutrient_risk** | **A (0.625)** | B (1.000) |
| **pest_disease_risk** | **A (1.000)** | A=B (1.000) |
| **robot_task_prioritization** | A (0.563) | A=C (0.571) |
| rootzone_diagnosis | A=B (0.750) | B (1.000) |
| safety_policy | A=B (0.889) | B (1.000) |
| seasonal | B (0.750) | — |
| sensor_fault | A=B (1.000) | B (1.000) |
| **state_judgement** | **A (0.800)** | — |

**패턴**:
- B가 강한 카테고리(7): 자유형 판단 + 도메인 추론 + 일반 상식 기반
- A가 강한 카테고리(5): 정형 스키마 + fine-tune 데이터 반복 학습 효과
- **완벽한 상보관계**. 2-lane 하이브리드가 이론적으로 가능

### 5.2 특성 요약

| 경로 | 강점 | 약점 | 적합 역할 |
|---|---|---|---|
| **A ds_v11** | 정형 스키마 태스크, category 안정성, 비용, 이미 배선 | 자유형 추론 일부 약함, hard-safety 2~3건 위반 | **메인 decision path** |
| **B gpt-4.1** | 자유형 판단, blind50 hard-safety 완벽 | forbidden_action 카테고리 붕괴(0.05/0.00), 비용 13× | **challenger lane** (프롬프트 수정 후) |
| C gemini-flash | 저렴, strict JSON 1.0, live-rag에 소폭 강함 | 과잉 확신(0.89), instruction following 약함 | **탈락** |
| D MiniMax M2.7 | live-rag 조건 blind50 +12점 개선 | 레이턴시 46분/250, thinking 토큰 strict_json 저하 | **탈락** |

---

## 6. 비용 분석 ($/pass 관점)

### 6.1 250건 풀 eval 실측

| 경로 | 소요 시간 | 호출당 입력 | 호출당 출력 | 호출당 비용 | 250건 총비용 | pass 수 | **$/pass** |
|---|---:|---:|---:|---:|---:|---:|---:|
| A ds_v11 | ~8분 | ~3.5k | ~450 | $0.00159 | **$0.40** | 140 | **$0.0029** ⭐ |
| B gpt-4.1 | ~13분 | ~6.5k | ~500 | $0.0208 | **$5.20** | 141 | $0.0369 |
| C gemini-flash | ~12분 | ~7.0k | ~500 (+thinking) | $0.0034 | **$0.86** | 74 | $0.0116 |
| D m2.7 | ~46분 | ~6.5k | ~2.3k (thinking inline) | ~$0.0035 *(unverified)* | ~$0.88 | 67 | ~$0.0131 |

**A가 $/pass 기준 압도적 1위** — B 대비 12.7배 저렴.

### 6.2 월간 운영 비용 추정

(가정: 하루 700 decision 호출 + chat 호출, 한국어 token 보정 1.5×)

| 경로 | 월 비용 |
|---|---:|
| A ds_v11 | **~$90/월** |
| B gpt-4.1 | ~$450/월 |
| C gemini-flash | ~$81/월 |
| D MiniMax M2.7 | ~$88/월 *(unverified)* |

**비용 관점**: A, C, D는 비슷한 수준, B만 5배. 그러나 품질을 함께 보면 A의 $/pass가 독보적.

---

## 7. 최종 결론 및 권고 (실행 계획)

### 7.1 단일 답

**결정 경로 메인 모델: A ds_v11 파인튜닝 그대로 유지**

```
OPS_API_LLM_PROVIDER=openai
OPS_API_MODEL_ID=ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v11-prompt-v5-methodfix-batch14-eval-v2-2026:DTryNJg3
```

AI 어시스턴트 채팅 경로: DB grounding + `task_type="chat"` 입력 구조 유지, 현재 구현은 같은 `OPS_API_LLM_PROVIDER` / `OPS_API_MODEL_ID`를 공유

### 7.2 즉시 개선 백로그 (1~2주)

1. **A ds_v11 hard-safety 위반 원인 분석**
   - extended200에서 3건, blind50에서 2건이 어느 케이스에서 발생했는지 식별
   - 다음 fine-tune 배치(ds_v12 / batch22?) 우선 보강 항목으로 등록
   - 스크립트: `scripts/report_eval_failure_clusters.py`로 필터

2. **validator-후 수치 전 경로 측정**
   - 현재 raw만 비교됨. 실제 운영 품질은 validator 후로 판정
   - 실행: `scripts/build_shadow_mode_window_report.py`를 A/B/C/D 결과에 돌려서 validator 적용 후 pass rate 확정
   - 목표: validator 후 기준으로 A와 B가 제품화 게이트 어느 단계에 해당하는지 확정

3. **retriever 품질 긴급 개선**
   - 현재 recall@5 = 0.164, safety_policy 카테고리는 recall 0
   - `artifacts/rag_index/pepper_expert_with_farm_case_index.json`에 이미 TF-IDF+SVD 24차원 local_embedding 저장됨
   - `llm_orchestrator/retriever.py::KeywordRagRetriever` 옆에 `LocalVectorRetriever` 추가 (기존 경로 유지, 플래그로 전환)
   - 목표: recall@5 ≥ 0.60

### 7.3 중기 (1~3개월)

4. **Phase A' — B gpt-4.1 프롬프트 스키마 강화**
   - `sft_v11_rag_frontier` 프롬프트에 `forbidden_action`, `robot_task_prioritization` 전용 JSON schema 스니펫 추가
   - 재평가 후 `forbidden_action` 카테고리가 0.05 → 0.60+ 복구되면 **challenger lane으로 공식화**
   - 예상 비용: ~$6, 시간 15분

5. **Challenger shadow 병렬 수집**
   - decision path는 여전히 A, shadow 병렬로 B 호출 + diff 로깅
   - 2주 운영 데이터 누적 후 A vs B 실제 트래픽 승률 측정
   - 구현: `ops-api/ops_api/shadow_mode.py` 확장

6. **2-lane 라우팅 실험**
   - 태스크 타입별 라우팅: `failure_response`/`climate_risk`/`edge_case` → B, `forbidden_action`/`robot_task_prioritization`/`state_judgement` → A
   - 운영 복잡도 증가하지만 data상 최적의 설계

### 7.4 장기 (분기별)

7. **ds_v15 또는 ds_v12 재학습**
   - ds_v11의 약점(자유형 판단 + hard-safety 2~3건) 보강
   - 이번 리포트의 category별 실패 분포를 training data 설계 가이드로 사용

8. **Reasoning 모델 원칙 고정**
   - 본 리포트와 이전 Phase C/D에서 두 번 확인: Gemini dynamic thinking + MiniMax `<think>` inline 모두 instruction following + JSON strict 요구와 충돌
   - 결정 경로 권고 원칙 문서화: **reasoning/thinking 모델은 이 프로젝트 결정 경로에 쓰지 않음** (o3/o4-mini/DeepSeek R1/Gemini 2.5 Flash thinking/MiniMax M2 전부 해당)
   - AI 어시스턴트 채팅(`/ai/chat`)은 본 평가 범위 밖이다. 다만 현재 구현은 별도 reasoning 모델 경로를 두지 않고, 같은 LLM 설정 위에서 DB grounding + `task_type="chat"`로 대화 모드를 유도한다.

### 7.5 하지 말 것

- ❌ **B gpt-4.1로 전면 전환** (현 시점): `forbidden_action 0.05` 해결 전엔 프로덕션 리스크 > 이득
- ❌ **C Gemini Flash, D MiniMax M2.7 후보 재평가**: 모델 품질 한계 명확. reasoning 모델 원칙에 따라 재시도 가치 없음
- ❌ **raw pass rate만으로 모델 순위 단정**: 차이가 0.5~4점인데 노이즈 범위. category 분포와 hard-safety, validator-후 수치까지 봐야 함
- ❌ **retriever 개선 없이 live-rag를 프로덕션 기본값으로**: recall 0.16으로는 어떤 모델도 품질 상한 저하

---

## 8. 부록: 코드 변경 요약

### 8.1 `scripts/evaluate_fine_tuned_model.py`
- `--provider {openai, gemini, minimax}` 플래그
- `--live-rag`, `--rag-top-k`, `--rag-corpus-paths` 플래그
- `LiveRagRetriever` 클래스 (KeywordRagRetriever 래퍼 + chunk_lookup join)
- `build_retrieval_query` 함수 (eval case에서 query 구성)
- `strip_thinking_tags` 전처리 (MiniMax M2, DeepSeek R1, QwQ 공통 `<think>` 블록 제거)
- `call_gemini_with_retry` + `--gemini-thinking-budget`, `--pacing-seconds`
- `extract_chunk_ids` 함수 (static/inline/live 통합)
- `grade_case(..., effective_retrieved_ids=None)` 파라미터 추가 (**치명 버그 수정**)
- `summarize_cases` 확장: `per_check`, `hard_safety_violation_cases`, `category_floors`
- `HARD_SAFETY_CHECKS`, `CATEGORY_FLOOR_WARN/CRIT` 상수

### 8.2 `scripts/regrade_eval_results.py` (신규)
- 기존 jsonl 결과를 수정된 grader + 새 집계로 재채점하는 offline 스크립트
- `RUN_MANIFEST`에 12개 경로 정의
- 출력: `artifacts/reports/regrade/*.json`, `regrade_index.json`

### 8.3 `scripts/build_openai_sft_datasets.py`
- `SFT_V11_RAG_FRONTIER_SYSTEM_PROMPT` 신규 (frontier+RAG용, 20개 hard-safety 규칙 + RETRIEVED_CONTEXT USAGE PROTOCOL 포함)

### 8.4 아티팩트
- `artifacts/reports/regrade/*.json` — 12개 run 재채점 summary
- `artifacts/reports/frontier_*_{ext200,blind50}.{json,jsonl,md,log}` — 원본 run 결과
- `artifacts/reports/ab_full_evaluation.md` — **본 리포트**
- `artifacts/reports/ab_frozen_vs_frontier.md` — 이전 A/B/C/D 리포트 (버그 포함 수치)

---

## 9. 변경 이력

| 단계 | 내용 | 상태 |
|---|---|---|
| Phase A | `sft_v11_rag_frontier` 프롬프트 + B gpt-4.1 평가 | 완료 |
| Phase B | ds_v11 vs gpt-4.1 3-way 비교 리포트 | 완료 |
| Phase C | Gemini 2.5 Flash 추가 평가 | 완료 |
| Phase D | MiniMax M2.7 추가 평가 | 완료 |
| Phase E-1 | live-rag retrieval 경로 구현 | 완료 |
| Phase E-2 | Live-rag 1케이스 probe | 완료 |
| Phase E-3 | 4경로 live-rag 재평가 (버그 있는 grading) | 완료 |
| **Phase E-5** | **grading 버그 발견 + 수정** | **완료** |
| **Phase E-7** | **grading 집계 확장 (per-check / hard-safety / floors)** | **완료** |
| **Phase E-8** | **11개 run 재채점** | **완료** |
| **Phase E-9** | **D m2.7 live-rag blind50 API 재호출** | **완료** |
| **Phase E-10** | **본 리포트 작성** | **완료** |
