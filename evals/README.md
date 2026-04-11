# Expert Judgement Evals

이 디렉터리는 적고추 스마트팜 운영 전문가 AI Agent의 판단 품질을 검증하기 위한 평가셋을 관리한다.

## 현재 평가셋

- `expert_judgement_eval_set.jsonl`: 전문가 판단 초기 평가셋
- `rag_retrieval_eval_set.jsonl`: RAG 검색 hit rate 평가셋
- `rag_official_priority_eval_set.jsonl`: `farm_case`가 섞인 혼합 인덱스에서 공식 지침 우선 정렬을 확인하는 평가셋
- `action_recommendation_eval_set.jsonl`: 추천 행동과 승인 필요 여부 평가셋
- `forbidden_action_eval_set.jsonl`: 금지행동/승인 필요 판정 평가셋
- `failure_response_eval_set.jsonl`: 장애 대응과 fallback 평가셋
- `robot_task_eval_set.jsonl`: 로봇 작업 우선순위 평가셋

## 평가 목적

평가셋은 모델이 아래 요구를 만족하는지 확인한다.

- JSON 출력 구조를 지킨다.
- 생육 단계와 센서 맥락을 반영한다.
- RAG 근거가 필요한 판단에는 citation을 포함한다.
- 센서 품질이 나쁘면 자동 실행을 보수적으로 제한한다.
- 금지 행동을 추천하지 않는다.
- 승인 필요 상황을 명확히 구분한다.

## 초기 카테고리

- `state_judgement`: 정상 상태와 관찰 판단
- `climate_risk`: 고온, 결로, 과습, 광 스트레스
- `rootzone_diagnosis`: 과습, 과건조, 뿌리 갈변, 배지 이상
- `nutrient_risk`: EC/pH, 배액률, 양분 흡수 이상
- `sensor_fault`: missing, stale, outlier, calibration error
- `pest_disease_risk`: 병해충 위험과 비전 의심 증상
- `harvest_drying`: 수확, 건조, 저장 판단
- `safety_policy`: 작업자, 로봇, 장치 안전 정책

## 다음 확장

1. 각 카테고리별 최소 20개 케이스 작성
2. 정상/주의/위험/차단 케이스 균형화
3. 생육 단계별 케이스 분리
4. RAG citation 정답 chunk 지정
5. eval JSONL 구조 검증을 `scripts/validate_training_examples.py`로 자동 확인

## RAG 검색 평가 실행

현재 RAG 검색 평가는 다음 명령으로 실행한다.

```bash
python3 -m venv .venv
./.venv/bin/pip install -r requirements-rag.txt
./.venv/bin/python scripts/evaluate_rag_retrieval.py --fail-under 1.0
./.venv/bin/python scripts/evaluate_rag_retrieval.py --vector-backend local --fail-under 1.0
./.venv/bin/python scripts/build_chroma_index.py --embedding-backend local
./.venv/bin/python scripts/evaluate_rag_retrieval.py --vector-backend chroma --chroma-embedding-backend local --fail-under 1.0
./.venv/bin/python scripts/compare_rag_retrieval_modes.py --candidate-backend local
./.venv/bin/python scripts/compare_rag_retrieval_modes.py --candidate-backend chroma --chroma-embedding-backend local
```

`farm_case` 혼합 인덱스에서 공식 지침 우선 가드레일은 아래 명령으로 별도 검증한다.

```bash
python3 scripts/build_rag_index.py \
  --input data/rag/pepper_expert_seed_chunks.jsonl data/rag/farm_case_seed_chunks.jsonl \
  --output artifacts/rag_index/pepper_expert_with_farm_case_index.json \
  --skip-embeddings
python3 scripts/evaluate_rag_retrieval.py \
  --index artifacts/rag_index/pepper_expert_with_farm_case_index.json \
  --eval-set evals/rag_official_priority_eval_set.jsonl \
  --vector-backend local \
  --fail-under 1.0
```

OpenAI embedding 기반 평가를 돌릴 때는 저장소 루트 `.env`에 `OPENAI_API_KEY`를 넣은 뒤 아래 명령을 실행한다.

```bash
./.venv/bin/python scripts/build_chroma_index.py --embedding-backend openai
./.venv/bin/python scripts/evaluate_rag_retrieval.py --vector-backend chroma --chroma-embedding-backend openai --fail-under 1.0
./.venv/bin/python scripts/compare_rag_retrieval_modes.py --candidate-backend chroma --chroma-embedding-backend openai
./.venv/bin/python scripts/tune_rag_weights.py --vector-backend chroma --chroma-embedding-backend openai --vector-weights 10 --chroma-local-blend-weights 0,2,4,6
```

현재 기준 결과는 110개 케이스에서 keyword-only hit rate 1.0, MRR 0.9909이고, local vector hybrid는 hit rate 1.0, MRR 0.9955, local-backed Chroma hybrid는 hit rate 1.0, MRR 0.9955, OpenAI-backed Chroma hybrid는 hit rate 1.0, MRR 0.9803이다. 확장된 평가셋에는 계절 리스크, 활착 불량, 품종 필터, 곡과·저온, 미숙퇴비 암모니아 피해, 수직배수 불량, 첫서리, 노화묘, 역병 초기 발병률, 탄저병 빗물 전파, 가루이 천적 투입, 진딧물 바이러스 방제 시작 시점, 나방 성페로몬 배치에 더해 균핵병, 시들음병, 잿빛곰팡이병, 흰별무늬병, 흰비단병, 무름병, 잎굴파리, 뿌리혹선충, 농약 잔류·혼용 순서 케이스가 포함된다. `--vector-backend local`은 로컬 TF-IDF + SVD 벡터 검색을 사용하고, `--vector-backend chroma --chroma-embedding-backend local`은 `pepper_expert_chunks_local`, `--vector-backend chroma --chroma-embedding-backend openai`는 `pepper_expert_chunks_openai` 컬렉션을 사용한다.
