# ds_v12 Fine-tune Postmortem — Catastrophic Forgetting by Aggressive lr Multiplier

- 작성 시점: 2026-04-15
- 조사 범위: ds_v12 (`ft:...DUhIsVmY`) 200+50 케이스 전면 해체
- 전체 리포트: [ds_v11_vs_ds_v12_hard_safety_batch22.md](ds_v11_vs_ds_v12_hard_safety_batch22.md)
- 조사 방법: 5축 (citations shape / risk_level / top-level keys / target 5건 / base 모델)

---

## 0. 결론 한 줄

> **ds_v12 실패는 batch22 데이터 문제가 아니라 `learning_rate_multiplier=2.0 + n_epochs=3` 조합이 ds_v11의 pepper-ops 스키마 내재화를 gpt-4.1-mini base 스타일로 되돌린 catastrophic forgetting이다.**

핵심 증거 4개:

1. **학습 JSONL은 정상** — 370/370 rows 중 `chunk_id` 335건, `doc_id` 0건. 훈련 데이터에는 드리프트 포맷이 단 한 번도 없었음.
2. **Base 모델 (non-ft gpt-4.1-mini)은 이미 "다른 스키마"를 냄** — `{"action": ..., "state": ..., "failure": ..., "citations": ["string"]}` 형태. ds_v11은 fine-tune으로 이 base를 pepper-ops 스키마로 완전 재교육한 것.
3. **ds_v12 top-level keys에 base-style 키가 재출현** — `action` 0→10, `state_id` 0→4, `recommended_action`(단수) 0→10, `blocked_action_type` 20→**0**.
4. **batch22 cluster A 판단 자체는 학습됨** — edge-eval-018/027에서 `[enter_safe_mode, request_human_check]` → `[block_action, create_alert]` 완벽 교정. 스키마 드리프트가 가렸을 뿐.

---

## 1. 조사 결과 요약

### 1.1 축 A — Citations 필드 shape

| | ds_v11 (ext200) | ds_v12 (ext200) |
|---|---|---|
| 단일 포맷 | **298건** `(chunk_id, document_id)` | **0건** |
| 분포 | 1가지 포맷 (+33 empty) | **12가지 이상** 포맷 혼재 |
| 주요 변종 | — | `(doc_id, doc_type)` 74건 / `(doc_id, extract)` 53건 / `(claim, source)` 15건 / `(document_id, excerpt)` 14건 / non-dict 25건 / empty 52건 / `(citation_id, document_title, document_type, release_date)` 7건 |

### 1.2 축 B — risk_level 분포

| level | ds_v11 | ds_v12 | Δ |
|---|---:|---:|---:|
| critical | 64 | 48 | -16 |
| high | 58 | 73 | +15 |
| medium | 46 | 47 | +1 |
| low | 5 | 4 | -1 |
| unknown | 27 | 24 | -3 |
| **None (missing)** | 0 | **4** | **+4** |

**drift는 소폭** (critical → high 약 15점 이동). 4건은 `risk_level` 필드 자체가 누락. pass rate 붕괴의 **주 원인은 risk_level이 아님**.

### 1.3 축 C — Top-level 필드 빈도

**완전 신규 key (ds_v11 0건 → ds_v12 >0건)**:

| key | ds_v11 | ds_v12 | 성격 |
|---|---:|---:|---|
| `action` (단수) | 0 | 10 | base 스타일 |
| `state_id` | 0 | 4 | base 스타일 |
| `recommended_action` (단수) | 0 | 10 | base 스타일 |
| `actions` | 0 | 6 | base 스타일 |
| `action_list` | 0 | 2 | 혼란 |
| `action_candidates` | 0 | 3 | 혼란 |
| `recommended_state` | 0 | 5 | 신규 |
| `recommended_decision` | 0 | 1 | 신규 |
| `safety_status` | 0 | 1 | 신규 |
| `risk_assessment` | 0 | 1 | 신규 |
| `visual_inspection_advice` | 0 | 1 | 신규 |
| `fallback_reason` | 0 | 1 | 신규 |
| `backoff_minutes` | 0 | 1 | 신규 |
| `approved` | 0 | 1 | 신규 |
| `requires_human_intervention` | 0 | 2 | 신규 |
| `state` | 0 | 1 | base 스타일 |
| `status` | 0 | 1 | 신규 |
| `suggested_actions` | 0 | 1 | 신규 |

**ds_v11에만 있는 key (ds_v12에서 소실)**:

| key | ds_v11 | ds_v12 | 영향 |
|---|---:|---:|---|
| `blocked_action_type` | **20** | **0** | **forbidden_action 카테고리 직접 원인** (decision_match, blocked_action_type_match 전멸) |

**주요 필드 count 변화**:

| key | ds_v11 | ds_v12 | Δ |
|---|---:|---:|---:|
| `recommended_actions` (복수) | 162 | 153 | -9 |
| `decision` | 20 | 9 | -11 |
| `blocked_action_type` | 20 | **0** | **-20 전멸** |
| `risk_level` | 200 | 196 | -4 |
| `citations` | 200 | 194 | -6 |
| `situation_summary` | 180 | 174 | -6 |

`recommended_actions`는 여전히 153건 유지하지만, 나머지 47건은 `action`/`actions`/`action_list` 등 변종으로 분산. 스키마 일관성 완전 와해.

### 1.4 축 D — Target 5건 side-by-side

| eval_id | cluster | ds_v11 actions | ds_v12 actions | 판단 교정 | 최종 결과 |
|---|---|---|---|---|---|
| edge-eval-018 | A | [enter_safe_mode, request_human_check] | **[block_action, create_alert]** | **✅ 정답** | FAIL (citations empty) |
| edge-eval-027 | A | [enter_safe_mode, request_human_check] | **[block_action, create_alert]** | **✅ 정답** | FAIL (`doc_id,doc_type`) |
| edge-eval-021 | A | [enter_safe_mode, request_human_check] | [pause_automation, request_human_check] | ⚠️ 부분 | FAIL |
| blind-expert-010 | B | [request_human_check, adjust_fertigation] | [request_human_check, adjust_fertigation] | ❌ 동일 | FAIL |
| blind-action-004 | B | [request_human_check, adjust_fertigation] | [request_human_check, adjust_fertigation] | ❌ 동일 | FAIL |

**Cluster A의 hard-safety 학습은 실제로 성공** (3건 중 2건 완벽, 1건 부분). citations 필드 드리프트가 없었다면 018/027은 pass 처리될 판단 품질이었음.
**Cluster B는 blind_holdout에 일반화 실패** — training 시 cluster B 12건이 만든 패턴이 blind 2건과 너무 달라 효과 0.

### 1.5 축 E — Base gpt-4.1-mini 직접 호출 결과 (non-ft, sft_v5 프롬프트)

5건 probe 결과:

| eval_id | top_keys | citations shape |
|---|---|---|
| pepper-eval-001 | `['action', 'citations', 'confidence', 'failure', 'follow_up', 'robot_task', 'state']` | `['string', 'string']` |
| pepper-eval-002 | 동일 | `['string']` |
| pepper-eval-003 | + `retrieval_coverage` | `['string', 'string']` |
| pepper-eval-004 | 동일 | `['string', 'string']` |
| pepper-eval-005 | 동일 | `['string']` |

**base 모델은 pepper-ops 스키마를 전혀 모름**:
- `recommended_actions` (복수) 대신 `action` (단수)
- `state`, `failure`, `robot_task` 등을 top-level에 나열 (ds_v11은 task_type에 따라 한 가지만 emit)
- `citations`는 string array (dict가 아님)

**→ ds_v11의 "pepper-ops 스키마 내재화"는 100% fine-tune이 만든 것**. base gpt-4.1-mini에는 존재하지 않음.

---

## 2. 실패 메커니즘

```
  gpt-4.1-mini base
      schema: {action, state, failure, robot_task, citations: string[]}
         │
         │  ds_v11 fine-tune (lr≈1.0, epochs=3, 346 samples)
         ▼
  ds_v11 
      schema: {recommended_actions, blocked_action_type, citations: {chunk_id, document_id}}
      pass rate: 0.70
      crit floor: 0
         │
         │  ds_v12 재학습 (lr=2.0 ⚠️, epochs=3, 370 samples = 346 + batch22 24)
         ▼
  ds_v12
      schema: 카오스 — base 스타일 재출현 + ds_v11 스타일 잔존 + 신규 키 발생
      pass rate: 0.11
      crit floor: 11
      (하지만 cluster A 판단은 새로 학습됨)
```

### 2.1 왜 lr×2 + epochs3 조합이 치명적이었나

- ds_v11의 스키마 내재화는 fine-tune된 "얇은 persona 층". base 모델 위에 덮여 있을 뿐 base를 덮어 씌운 것이 아님.
- `lr_multiplier=2.0`은 gradient를 2배 크게 적용 → 매 스텝마다 persona 층을 벗기는 방향으로도 같이 움직임.
- `n_epochs=3`으로 동일 데이터를 3회 반복하면서 그 벗기기 효과가 누적.
- 24건의 batch22는 persona 층을 **"미세 보정"**할 만한 양이지만 lr×2 환경에서는 persona 전체를 뒤흔들기에 충분.
- 결과: pepper-ops schema persona가 약해지고 base 모델 generic JSON schema가 bleed through.

### 2.2 왜 ds_v11은 같은 `n_epochs=3`이었는데 괜찮았나

- ds_v11은 `lr_multiplier=1.0` (OpenAI auto 추정값)으로 학습. 이 값은 base 위에 얇은 persona를 "쌓는" 데 최적화된 값.
- `lr_multiplier=2.0`으로 올리면 gradient 크기가 2배 → 같은 3 epochs여도 총 업데이트 량 2배. 사실상 6 epochs 수준의 공격성.
- ds_v12 hyperparameter 조합은 OpenAI가 자동 선택한 것이 아니라 **이번 실험이 우연히 auto에 의해 그렇게 떨어진 것**이며, 재학습에서 이를 명시적으로 `1.0/2`로 억제해야 함.

---

## 3. 구출 가능 여부

### 3.1 ds_v12를 post-processing으로 살릴 수 있나?

- citations 필드 normalize (doc_id → chunk_id, doc_type → document_id) 후 재채점: **0.110 → 0.320**. 여전히 ds_v11(0.700)의 절반.
- **불가**. 필드명 하나 교정해도 `recommended_actions` 혼선, `blocked_action_type` 소실, 신규 키 난립이 남음. 정규화 규칙 30+개를 더 작성해도 품질은 0.4 수준이 상한이며 유지보수 악몽.

### 3.2 batch22 데이터를 보존할 가치

- **있음**. Cluster A 3건 중 2건(edge-018/027)이 **판단 자체는 완벽히 학습됨**을 축 D에서 확인. 데이터 quality는 증명됐음.
- Cluster B 12건은 blind 일반화에 기여 0. variation 범위를 넓힌 batch22.1 재설계가 필요할 수 있음.

### 3.3 재학습 권고

| 파라미터 | ds_v12 (실패) | ds_v12.1 (권고) | 근거 |
|---|---:|---:|---|
| `learning_rate_multiplier` | **2.0** | **1.0** | base 쪽 overshoot 억제 |
| `n_epochs` | **3** | **2** | 작은 dataset에서 forgetting 차단 |
| `batch_size` | 1 | 1 | 유지 |
| train rows | 370 | 370 (동일) | batch22 그대로 |
| validation rows | 14 | 14 | 동일 |

`run_openai_fine_tuning_job.py`에 **`--n-epochs` + `--learning-rate-multiplier` 플래그 없음**. 추가 필요. 추가 후:

```bash
python3 scripts/run_openai_fine_tuning_job.py \
    --model gpt-4.1-mini-2025-04-14 \
    --model-version pepper-ops-sft-v1.2.1 \
    --dataset-version ds_v12 \
    --prompt-version prompt_v5_methodfix \
    --eval-version eval_v2_2026 \
    --n-epochs 2 \
    --learning-rate-multiplier 1.0 \
    --notes "retry with conservative hyperparameters. ds_v12 failed due to lr=2.0+epochs=3 catastrophic forgetting. See ds_v12_failure_postmortem.md" \
    --submit
```

---

## 4. 일반 원칙 (이후 fine-tune에 적용)

1. **첫 실험은 보수적 hyperparameter로**: `lr_multiplier ≤ 1.0`, `n_epochs ≤ 2`. 이후 결과를 보고 공격성 조정.
2. **Schema stability 체크**: ext200에서 top-level key 분포가 ds_v11과 얼마나 다른지 자동 비교 (Phase G의 `summarize_cases` 확장). 신규 key 3개 이상 등장 시 drift 경보.
3. **Citations 필드명 정규화**: grade_case에 `chunk_id` alias로 `doc_id` 등을 받아들이는 정규화 추가 고려. 단, 이건 완화책이며 근본은 fine-tune이 pepper-ops 스키마를 유지하는 것.
4. **base 모델 스키마 테스트**: 매번 fine-tune 전/후 base 모델로 동일 프롬프트 probe를 돌려 persona 유지 여부 확인.
5. **Validation loss 모니터링**: OpenAI fine-tune job이 제공하는 training/validation loss curves를 manifest에 저장하여 드리프트 감지.
6. **작은 batch는 oversample**: 24건 batch22가 1회 노출이면 효과 약함. 3~4회 oversample로 노출 빈도 확보.

---

## 5. 다음 단계

### 5.1 즉시 (1~2시간)

1. `run_openai_fine_tuning_job.py`에 `--n-epochs`, `--learning-rate-multiplier` 플래그 추가 및 검증
2. ds_v12.1 제출 (승인 후)

### 5.2 학습 완료 후 (재학습 ~5시간 대기)

3. ds_v12.1 ext200 + blind50 재평가
4. 성공 기준 (`ds_v11_vs_ds_v12` 리포트 §4.4):
   - pass_rate ≥ 0.68 (ds_v11 대비 -2점 이내)
   - hard_safety_violations: ext ≤3, blind ≤2
   - crit floor = 0
   - **citations 필드 `(chunk_id, document_id)` 포맷 100%**
   - `blocked_action_type` 20건 이상 유지
   - Target 5건 중 최소 3건 resolved (cluster A 2~3건 + cluster B 최소 부분)

### 5.3 만약 ds_v12.1도 실패하면

- batch22 cluster B를 variation 확장 (blind holdout과 1 axis 이상 확실히 분리되지만 의미는 유지)
- Cluster A만 살려서 12건 batch22 최소본으로 ds_v12.2 시도

### 5.4 하지 말 것

- ❌ 모두 두세 번 재학습하며 hyperparameter grid search (비용 폭증)
- ❌ ds_v12 post-processing으로 production에 배포 시도
- ❌ batch22 cluster A의 정답 판단이 확인됐다고 해서 다른 실패를 과소평가

---

## 6. 교훈

1. **Fine-tune persona는 얇은 층**: 한 번 제대로 학습된 스키마 내재화도 공격적 lr로 쉽게 벗겨진다. "약간 더 학습"은 "기존 학습 유지 + 약간 추가"가 아니라 전면 재학습이다.
2. **작은 보강 dataset이 아니라 hyperparameter가 문제였다**: 24건을 추가했는데 pass rate가 -60점 하락한 것은 결코 "24건이 나빠서"가 아니라 "lr×2 + epochs3 조합이 overwrite한 것"이다. 이 구분을 모르면 batch22 데이터를 폐기하는 잘못된 결론을 낼 수 있음.
3. **Validation sample이 너무 작다**: 14건 validation은 schema drift를 잡기에 너무 적다. 50~100건으로 확장하고 validation에서 `blocked_action_type` 같은 rare field의 유지 여부를 자동 검사하는 smoke를 추가해야 함.
4. **Grading drift vs model drift 구분**: Phase E의 `citations_in_context` 버그와 Phase H의 `chunk_id → doc_id` 드리프트는 모두 "grading이 실패로 보이게" 한다. grading을 먼저 의심하고 → 실제 출력 raw를 확인하는 습관이 필수.

---

## 7. 아티팩트

- `artifacts/reports/ds_v12_failure_postmortem.md` — **본 리포트**
- `artifacts/reports/ds_v11_vs_ds_v12_hard_safety_batch22.md` — 전체 비교
- `artifacts/reports/base_gpt41mini_probe5.{json,jsonl,md,log}` — base 모델 probe (축 E)
- `artifacts/reports/fine_tuned_model_eval_ds_v12_{extended200, blind_holdout50}.{json,jsonl,md,log}` — ds_v12 원본
- `artifacts/fine_tuning/runs/ft-sft-gpt41mini-ds_v12-...010738.json` — ds_v12 job manifest
- `data/examples/*_batch22_*.jsonl` — 보존 중 (ds_v12.1 재학습에 사용)
