# A/B/C/D: ds_v11 frozen fine-tune vs gpt-4.1 vs gemini-2.5-flash vs MiniMax-M2.7

- 작성 시점: 2026-04-14 (4-way 확장)
- Phase: A/B/C/D shadow comparison (production 전환 아님)
- 목적: 현재 운영되는 sub-0.8 파인튜닝 baseline(ds_v11)의 실제 대체 후보로
  동일한 eval tranche에 대해 **완전히 동일한 프롬프트·RAG 인라인 조건**에서
  frontier 모델 세 가지(OpenAI gpt-4.1, Google Gemini 2.5 Flash, MiniMax-M2.7)를 직접 비교한다.

## 1. 실험 설정

세 경로 모두 아래 조건은 같다:
- 시스템 프롬프트: `sft_v11_rag_frontier` (rag+hard-safety 통합, 6695자)
- RAG 인덱스: `artifacts/rag_index/pepper_expert_with_farm_case_index.json` (226 chunks)
- retrieved_context 인라인 방식: chunk_id + document_id + source_section + **전체 텍스트 본문 (최대 1400자)**
- temperature: 0.0
- eval 파일: extended200 = default 7개 tranche, blind_holdout50 = blind_holdout_eval_set.jsonl
- output validator 적용 전 raw grading

경로별 차이:

| 항목 | A: frozen fine-tune | B: gpt-4.1 frontier | C: gemini-2.5-flash | D: MiniMax-M2.7 |
|---|---|---|---|---|
| provider | openai | openai | google (gemini SDK) | minimax (OpenAI-compat SDK) |
| model_id | `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v11-...:DTryNJg3` | `gpt-4.1` (base) | `gemini-2.5-flash` | `MiniMax-M2.7` |
| prompt version | `sft_v5` (기존 FT 시점) | `sft_v11_rag_frontier` | `sft_v11_rag_frontier` | `sft_v11_rag_frontier` |
| max_completion_tokens | 1600 | 1600 | 8000 (thinking 여유분) | 3500 (thinking 여유분) |
| thinking mode | N/A | N/A | dynamic 기본값 (ON) | 내장 `<think>` 블록 (항상 ON) |
| response format 강제 | none | none | `response_mime_type=application/json` | none (OpenAI-compat 레벨) |
| base_url | 기본 | 기본 | google-genai 기본 | `https://api.minimax.io/v1` |

> Gemini Flash는 thinking 모델이라 thinking 예산이 max_output_tokens를 잠식한다.
> 초기 스모크에서 `thinking_budget=0`으로 끄니 instruction following이 급락(10건 중 2건)했고,
> 기본 dynamic으로 복원하니 스모크 통과율이 0.5까지 회복됐다. 본 전체 실행도 그 조건으로 통일.
>
> MiniMax M2.7은 reasoning 내용을 `<think>...</think>` 블록으로 content 안에 inline 출력한다.
> 이를 strict JSON 파서가 처리할 수 있도록 `scripts/evaluate_fine_tuned_model.py::strip_thinking_tags`
> 전처리를 추가했다. DeepSeek R1/QwQ 등 동일 패턴의 reasoning 모델에도 재사용 가능한 범용 로직이다.
> 3500 token 한도로도 15/200건(7.5%)이 thinking 완료 전 잘려 strict_json 0.925가 됐다.

## 2. 결과 요약

### 2.1 Extended 200 tranche

| 항목 | A: ds_v11 frozen | B: gpt-4.1 | C: gemini-2.5-flash | D: MiniMax-M2.7 |
|---|---:|---:|---:|---:|
| 통과율 | **0.700** (140/200) | **0.705** (141/200) | 0.370 (74/200) | **0.335** (67/200) |
| strict_json_rate | 1.000 | 1.000 | 1.000 | **0.925** (15건 잘림) |
| request_errors | 0 | 0 | 0 | 0 |
| avg_confidence | 0.812 | 0.786 *(pass 한정)* | **0.890** (과잉) | 0.689 (보수적) |

### 2.2 Blind holdout 50 tranche

| 항목 | A: ds_v11 frozen | B: gpt-4.1 | C: gemini-2.5-flash | D: MiniMax-M2.7 |
|---|---:|---:|---:|---:|
| 통과율 | **0.700** (35/50) | **0.740** (37/50) | 0.500 (25/50) | **0.220** (11/50) |
| strict_json_rate | 1.000 | 1.000 | 0.980 (1건 잘림) | 0.940 (3건 잘림) |
| request_errors | 0 | 0 | 0 | 0 |
| avg_confidence | 0.840 | 0.848 | 0.866 | 0.707 |

### 2.3 카테고리별 통과율 — extended200

| 카테고리 | A ds_v11 | B gpt-4.1 | C gemini | D m2.7 | 1등 |
|---|---:|---:|---:|---:|---|
| action_recommendation (28) | 0.679 | **0.857** | 0.607 | 0.464 | B |
| climate_risk (7) | 0.714 | **1.000** | 0.286 | 0.143 | B |
| edge_case (28) | 0.714 | **0.964** | 0.393 | 0.393 | B |
| failure_response (26) | 0.500 | **0.808** | 0.385 | 0.346 | B |
| forbidden_action (20) | **0.700** | 0.050 | 0.200 | 0.100 | **A** |
| harvest_drying (6) | **1.000** | 0.833 | 0.167 | 0.333 | **A** |
| nutrient_risk (8) | **0.625** | 0.500 | 0.250 | 0.125 | **A** |
| pest_disease_risk (6) | **1.000** | 0.667 | 0.167 | 0.333 | **A** |
| robot_task_prioritization (16) | 0.563 | 0.313 | 0.438 | **0.500** | A > D |
| rootzone_diagnosis (8) | 0.750 | 0.750 | 0.500 | 0.125 | A=B |
| safety_policy (9) | 0.889 | 0.889 | 0.444 | 0.333 | A=B |
| seasonal (24) | 0.667 | **0.750** | 0.208 | 0.417 | B |
| sensor_fault (9) | **1.000** | **1.000** | 0.667 | 0.444 | A=B |
| state_judgement (5) | **0.800** | 0.400 | 0.000 | 0.000 | **A** |

**단독 1위: A 6개, B 6개, 공동 A=B 3개. C와 D는 단독 1위 0개.** D는 `robot_task_prioritization`에서 B(0.31)보다 앞서는 0.50을 기록했으나 A(0.56)보다는 낮음. D가 유일하게 B보다 앞선 카테고리는 `robot_task_prioritization` 하나뿐.

### 2.4 카테고리별 통과율 — blind_holdout50

| 카테고리 | A ds_v11 | B gpt-4.1 | C gemini | D m2.7 | 1등 |
|---|---:|---:|---:|---:|---|
| action_recommendation (7) | 0.714 | **1.000** | 0.857 | 0.429 | B |
| climate_risk (2) | 0.500 | **1.000** | 0.000 | 0.500 | B |
| edge_case (6) | 0.833 | **1.000** | 0.500 | 0.333 | B |
| failure_response (8) | 0.750 | **1.000** | 0.625 | 0.125 | B |
| forbidden_action (8) | **0.750** | 0.000 | 0.375 | 0.000 | **A** |
| harvest_drying (2) | **1.000** | **1.000** | 0.000 | 0.000 | A=B |
| nutrient_risk (2) | 0.500 | **1.000** | 0.500 | 0.000 | B |
| pest_disease_risk (1) | **1.000** | **1.000** | 0.000 | 0.000 | A=B |
| robot_task_prioritization (7) | **0.571** | 0.286 | **0.571** | 0.286 | A=C |
| rootzone_diagnosis (2) | 0.500 | **1.000** | 0.000 | 0.500 | B |
| safety_policy (3) | 0.667 | **1.000** | 0.667 | 0.333 | B |
| sensor_fault (2) | 0.500 | **1.000** | 0.500 | 0.000 | B |

blind holdout에서는 B(gpt-4.1)가 훨씬 더 지배적이다. 12개 카테고리 중 8개 단독 1위,
2개 공동 1위. D(M2.7)는 **6개 카테고리가 0점** (forbidden, harvest_drying, nutrient_risk,
pest_disease_risk, failure_response 0.125, sensor_fault 0). 4-way 전체 최하위.

## 3. 핵심 관찰

### 3.1 C(Gemini 2.5 Flash)와 D(MiniMax M2.7)는 현 조건에서 **명백히 부적합**

두 경로 모두 통과율 0.5 미만이다. A/B 대비 -30점 이상의 격차를 보인다.

**C(Gemini Flash) 주요 실패 원인:**
- **instruction following 약함**: `follow_up`, `citations` 등 "필수" 필드를 빈 배열로 남기거나 누락
- **과잉 확신**: avg_confidence 0.89로 4경로 중 가장 높지만 실제 pass는 낮음.
  실패 케이스에서도 0.9 수준의 confidence를 부여하여 human reviewer가 **잘못된 안심**에 빠질 위험
- **citations_present 실패 36건 (ext200)**: Gemini가 RAG chunk를 읽었으나 citations 필드로
  돌려주지 않음. 인용 hallucination은 아니지만 citation omission이 빈번

**D(MiniMax M2.7) 주요 실패 원인:**
- **`<think>` 블록 토큰 점유**: content 안에 reasoning 텍스트를 inline 출력하며,
  3500 token 한도로도 ext200 15건·blind50 3건이 `</think>` 닫히기 전에 잘림.
  strict_json 0.925/0.940으로 유일하게 1.0 미만
- **`recommended_actions: []` 빈 배열**: 92건 `required_action_types_present` 실패 중 대부분이
  action 배열이 비어 있는 케이스. 모델이 `<think>` 블록에서는 옳은 판단을 도출하지만
  최종 JSON에 옮기지 못함
- **blind50 6개 카테고리 0점**: forbidden, harvest_drying, nutrient_risk, pest_disease_risk,
  sensor_fault 전부 0. 소규모 카테고리에 과적합된 실패 패턴
- **보수적 confidence (0.69)**: C와 달리 과잉 확신은 없음. 이 점 하나는 안전성 측면에서 긍정.
  그러나 절대 pass가 너무 낮아 의미 없음

### 3.2 B(gpt-4.1)는 여전히 자유형 태스크의 강자지만 **forbidden_action은 치명적**

extended200에서 B가 A보다 더 잘한 카테고리 6개의 개선폭은 +17~30점으로 크다.
그러나 `forbidden_action` 1/20, blind50 `forbidden_action` 0/8은 **decision**,
**blocked_action_type** 최상위 필드를 아예 생성하지 않기 때문이며, 프롬프트 수정으로
해결 가능한 영역이다. 이미 전 리포트에서 원인 분석 완료.

### 3.3 A(ds_v11)가 최고 품질을 보이는 영역: `forbidden_action`, `harvest_drying`, `pest_disease_risk`, `state_judgement`, `robot_task_prioritization`

이 카테고리들은 fine-tuning 데이터셋에 **구조 예시가 충분히 포함**된 영역이다.
B는 프롬프트로 구조를 학습해야 하고, C는 그 학습조차 제대로 안 이루어진다.
fine-tuning의 진짜 가치는 "JSON 스키마 암묵 학습"에 있다는 점이 수치로 확인된다.

### 3.4 B와 A의 상보관계

B는 `failure_response`, `climate_risk`, `edge_case`, `action_recommendation` 같이
**자유형 판단 + 도메인 추론**이 필요한 영역에서 강하고,
A는 **정형 스키마를 정확히 따라야 하는** 영역에서 강하다.
이 패턴은 "B를 메인으로, A를 특정 태스크에 특화 fallback으로" 쓰는 2-lane 설계가
이론적으로 가능함을 시사한다. 다만 운영 복잡도가 늘어나므로 추천 우선순위는 낮다.

### 3.5 비용/레이턴시 (실측 + 공식 pricing)

250건 풀 eval 기준 실측 비용/시간:

| 경로 | 실측 소요 시간 | 호출당 input(avg) | 호출당 output(avg) | 호출당 비용 | 250건 총 비용 |
|---|---:|---:|---:|---:|---:|
| A ds_v11 (gpt-4.1-mini ft) | ~8 분 | ~3.5k | ~450 | $0.00159 | **$0.40** |
| B gpt-4.1 | ~13 분 | ~6.5k | ~500 | $0.0208 | **$5.20** |
| C gemini-2.5-flash | ~12 분 (billing on) | ~7.0k | ~500 (+ thinking) | $0.0034 | **$0.86** |
| D MiniMax-M2.7 | ~46 분 | ~6.5k | ~2.3k (+thinking inline) | ~$0.0035 *(unverified pricing)* | **~$0.88** |

- C는 thinking 토큰이 output 예산을 공유하지만 현재 Gemini pricing에서 thinking은 별도 집계되지 않고 billed output에 포함 (공식 문서 기준 2026-04).
- D는 thinking이 content에 inline으로 포함되어 output tokens에 그대로 과금됨. 실제 completion_tokens 평균이 2300+으로 C/B 대비 4~5배. 또 실측 소요 시간이 46분으로 B의 **3.5배**, 레이턴시 민감 용도에 부적합.
- MiniMax 공식 pricing 페이지를 본 리포트에서 확인하지 않았으므로 D의 $/call은 *unverified*. 호출당 비용이 C와 비슷하다고 가정해도 품질 격차를 고려하면 $/pass는 D가 최악.

$/pass 계산 (extended200 기준):

| 경로 | 250건 비용 | pass 수 | $/pass |
|---|---:|---:|---:|
| A | $0.40 | 140 | **$0.0029** ⭐ |
| B | $5.20 | 141 | **$0.0369** |
| C | $0.86 | 74 | **$0.0116** |
| D | ~$0.88 *(unverified)* | 67 | **~$0.0131** |

A는 $/pass 기준 압도적 1위. C/D는 절대 가격은 싸지만 품질 격차가 너무 커서 correct-answer당 비용은 A의 4~5배. 가격만 보고 C/D로 이동하는 판단은 잘못된 결론으로 이어진다.

### 3.6 Thinking 모델 공통 이슈

C와 D 모두 reasoning/thinking 모델이지만 방식이 다르다:
- C Gemini: thinking 토큰이 **별도 영역**에서 소비 (content에 드러나지 않음). 기본 dynamic.
- D MiniMax M2.7: thinking이 **content에 inline**으로 나타남. `<think>...</think>` 블록 필수 제거.
  끌 수 있는 공식 파라미터를 확인하지 못함.

두 경로 모두 **thinking 기반 reasoning이 이 프로젝트의 instruction-following-heavy + JSON-strict 요구에 역효과**로 작용한다는 공통점을 보인다. 모델이 자체 reasoning에 토큰을 소비하는 동안 정작 출력 스키마의 세부 필드를 놓치는 패턴이 반복된다. 이는 o3/o4-mini/DeepSeek R1에 대해 이전 모델 리서치에서 경고한 내용과 일치한다: **"Reasoning 모델은 JSON strict 출력과 궁합이 나쁘고, 본 프로젝트에 구조적으로 부적합"**.

## 4. 결론 및 권고

### 4.1 잠정 결론

1. **Gemini 2.5 Flash와 MiniMax M2.7 모두 현 조건에서 이 프로젝트의 결정 경로에 부적합.**
   두 경로 모두 pass rate가 A/B 대비 -30점 이상 격차. 두 모델의 공통점은 "reasoning/thinking
   모델"이라는 점이며, thinking 예산이 instruction following과 JSON strict 준수를 오히려
   저해하는 패턴이 반복됐다. 가격 $/1M 비교 하나로 내린 1차 추천을 실측이 뒤집는 전형 사례다.

2. **gpt-4.1 frontier+RAG는 자유형 태스크에서 명확히 우세**하지만 forbidden_action 스키마
   문제가 해결되기 전까지는 전체 통과율에서 ds_v11 대비 결정적 우위를 보이지 못한다.

3. **ds_v11 frozen fine-tune은 정형 스키마 태스크에서 최고 품질**이며, $/pass 기준으로는
   압도적이다. "sub-0.8 점수"라는 이유만으로 폐기하는 것은 여전히 성급하다.

### 4.2 권고 (4.1의 우선순위대로)

1. **Gemini 2.5 Flash, MiniMax M2.7은 결정 경로 후보에서 제외.**
   - Gemini: 재평가가 필요하면 (a) 프롬프트에 forbidden_action/robot_task 스키마 스니펫 명시,
     (b) Gemini 2.5 **Pro** 모델로 업그레이드(가격 ~4배), (c) `responseSchema` 기반 structured
     output 강제 세 가지를 동시에 적용한 조건으로만 다시 시도한다.
   - MiniMax: reasoning 모델 + 긴 레이턴시(46분/250건) + 높은 output 토큰 소비(+thinking inline)로
     운영 경로에는 명백히 부적합. 재시도하려면 (a) thinking 끄는 공식 파라미터 확인,
     (b) MiniMax **non-reasoning 모델**(M1이나 abab 시리즈)로 교체한 조건에서만.

2. **gpt-4.1 frontier+RAG를 challenger lane으로 유지.**
   Phase A' (프롬프트에 forbidden_action·robot_task 전용 schema 스니펫 추가)를 실행하고
   재평가. 기대 상한: extended200 ≈ 0.79, blind50 ≈ 0.90. 재평가 비용 ~$6.

3. **ds_v11을 프로덕션 main decision path로 유지.**
   이미 `OPS_API_LLM_PROVIDER=openai` + `OPS_API_MODEL_ID=ft:...ds_v11...`로 배선되어 있다.
   AI 어시스턴트 채팅(`/ai/chat`)은 본 리포트 범위 밖이며, 현재 구현은 별도 chat 모델을 분리하지 않고 같은 LLM 설정 위에서 DB grounding + `task_type="chat"` 입력으로 동작한다.

4. **향후 fine-tuning 데이터셋 진화 방향**: 본 리포트에서 A가 강한 태스크(정형 스키마 영역)를 계속
   강화하고, 약한 태스크(자유형 도메인 추론, failure_response, climate_risk)는 오히려 B에 위임하는
   "fine-tune = 스키마 암기 / frontier = 자유형 판단" 2-lane 설계를 Phase B 운영 shadow에서 검증.

5. **최종 판단은 Phase A' 재평가 + 2주 운영 shadow 누적 이후로 연기한다.**
   현 시점에서 단일 결정은 내리지 않는다.

### 4.3 Reasoning 모델 공통 권고 (C, D 공통)

본 리포트에서 두 번 연속 확인됐으므로 향후 비교에 원칙으로 박아둔다:

> **이 프로젝트의 결정 경로에 reasoning/thinking 모델은 쓰지 않는다.**
>
> 프로젝트 요구사항이 "hard-safety 규칙 20개 + JSON strict + citation discipline"이라는
> **instruction following 집약형**이며, reasoning 모델은 자체 사고 토큰에 예산을 소비하면서
> 정작 출력 스키마의 세부 필드를 놓치는 패턴이 일관되게 나타난다. 이는 o3/o4-mini/DeepSeek R1에도
> 해당하며, 본 실측으로 Gemini 2.5 Flash(dynamic thinking)와 MiniMax M2.7(`<think>` inline)이
> 동일 패턴을 보였다.
>
> AI 어시스턴트 채팅(`/ai/chat`)은 본 원칙의 직접 적용 대상은 아니지만, 현재 구현은 별도 reasoning 모델을 붙이지 않는다.
> 채팅 경로는 같은 LLM 설정 위에서 DB grounding + `task_type="chat"` 구조로 동작하며, 본 원칙은 결정 경로(evaluate_zone, forbidden_action, robot_task_prioritization)에만
> 적용된다.

## 5. 아티팩트

### 본 리포트에서 생성
- extended200:
  - A: `artifacts/reports/fine_tuned_model_eval_ds_v11_prompt_v5_methodfix_batch14_extended200.json`
  - B: `artifacts/reports/frontier_rag_extended200.{json,jsonl,md,log}`
  - C: `artifacts/reports/frontier_gemini_extended200.{json,jsonl,md,log}`
  - D: `artifacts/reports/frontier_minimax_m27_extended200.{json,jsonl,md,log}`
- blind_holdout50:
  - A: `artifacts/reports/fine_tuned_model_eval_ds_v11_prompt_v5_methodfix_batch14_blind_holdout50.json`
  - B: `artifacts/reports/frontier_rag_blind50.{json,jsonl,md,log}`
  - C: `artifacts/reports/frontier_gemini_blind50.{json,jsonl,md,log}`
  - D: `artifacts/reports/frontier_minimax_m27_blind50.{json,jsonl,md,log}`
- 10-case smokes: `frontier_rag_smoke10`, `frontier_gemini_smoke10`,
  `frontier_gemini_smoke10_thinking`, `frontier_minimax_m27_smoke10`
- probe: `frontier_minimax_probe1` (think 태그 패턴 확인용)

### 코드 변경점
- 신규 프롬프트: `scripts/build_openai_sft_datasets.py::SFT_V11_RAG_FRONTIER_SYSTEM_PROMPT`
- 평가 스크립트 확장 (`scripts/evaluate_fine_tuned_model.py`):
  - `load_rag_chunk_lookup`, `inline_retrieved_context`
  - `--rag-index-path`, `--force-rag-inline`
  - `--provider {openai,gemini,minimax}`
  - `--minimax-base-url` (기본: `https://api.minimax.io/v1`)
  - `call_gemini_with_retry` (`response_mime_type=application/json`, thinking config)
  - `--gemini-thinking-budget`, `--pacing-seconds`
  - `strip_thinking_tags` (범용 `<think>...</think>` 제거 전처리 — DeepSeek R1, QwQ, M2.7 대응)
