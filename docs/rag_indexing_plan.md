# RAG Indexing Plan

이 문서는 적고추 전문가 AI Agent의 RAG 지식베이스를 vector store 또는 vector DB로 인덱싱하기 위한 계획이다.

## 목표

- `data/rag/pepper_expert_seed_chunks.jsonl`을 RAG 인덱싱 입력 표준으로 사용한다.
- 각 chunk에 검색용 텍스트와 metadata를 분리해 저장한다.
- 출처, 생육 단계, 센서, 위험, 작업 태그로 필터링 가능한 구조를 만든다.
- 같은 문서를 재인덱싱해도 chunk id 기준으로 추적 가능하게 한다.

## 입력

현재 입력 파일:

- `data/rag/pepper_expert_seed_chunks.jsonl`

필수 필드:

- `chunk_id`
- `document_id`
- `source_url`
- `source_type`
- `crop_type`
- `growth_stage`
- `cultivation_type`
- `sensor_tags`
- `risk_tags`
- `operation_tags`
- `causality_tags`
- `visual_tags`
- `chunk_summary`
- `agent_use`
- `citation_required`

권장 추적 필드:

- `source_pages`
- `source_section`
- `trust_level`
- `version`
- `effective_date`
- `active`

## 인덱싱 문서 구조

각 chunk는 다음 구조로 변환한다.

```json
{
  "id": "pepper-rootzone-001",
  "text": "검색 대상 본문",
  "metadata": {
    "document_id": "RAG-SRC-004",
    "source_url": "...",
    "source_type": "field_case",
    "crop_type": "red_pepper",
    "growth_stage": ["vegetative_growth"],
    "sensor_tags": ["soil_moisture", "ec"],
    "risk_tags": ["overwet", "root_damage"],
    "operation_tags": ["irrigation"],
    "causality_tags": ["high_moisture -> root_rot"],
    "visual_tags": ["root_browning"],
    "source_pages": [140, 141],
    "source_section": "제5장 재배 기술 비가림 하우스재배 습도 및 수분관리",
    "trust_level": "high",
    "agent_use": ["irrigation-agent"],
    "citation_required": true
  }
}
```

## 검색 전략

검색 엔진은 단순히 텍스트를 찾는 것을 넘어, 스마트팜의 현재 상황(생육 단계, 센서 값)을 인지하고 필터링하는 **Hybrid + Context-Aware** 구조를 지향한다.

현재 구현 상태:

- keyword search: 구현됨
- OpenAI embedding score: `scripts/build_rag_index.py`와 `scripts/search_rag_index.py`에 1차 구조 있음
- metadata hard filter: `growth_stage`, `crop_type`, `source_type`, `sensor_tags`, `risk_tags` 1차 구현
- chunk validation: `schemas/rag_chunk_schema.json`, `scripts/validate_rag_chunks.py` 1차 구현
- vector DB: ChromaDB persistent collection 구현 및 local/openai backend 검증 완료

1. **Metadata Hard Filtering (1순위)**
    - AI Agent의 현재 컨텍스트(예: `growth_stage: nursery`)를 기반으로 검색 범위를 사전에 제한한다.
    - 이를 통해 다른 생육 단계의 부적절한 지식이 혼입되는 것을 원천 차단한다.
    - 센서 기반 질의는 `sensor_tags`, `risk_tags`, `source_section`을 함께 필터링한다.

2. **Semantic Search (2순위)**
    - OpenAI `text-embedding-3-small` 또는 로컬 SentenceTransformer를 사용하여 청크 요약과 쿼리의 의미적 유사도를 계산한다.
    - 단순히 단어가 겹치지 않아도 "배지 과습"과 "뿌리 갈변" 사이의 연관성을 파악할 수 있게 한다.

3. **Keyword Fallback (3순위)**
    - `risk_tags`, `sensor_tags` 등 전문 용어에 대한 정확한 일치가 필요한 경우 키워드 검색을 병행한다.

4. **Reranking & Selection**
    - 검색된 결과 중 `source_type: official_guideline`에 가중치를 부여한다.
    - 상충하는 지식이 발견될 경우 가장 최신(`version`, `effective_date`) 문서를 우선한다.
    - 동일 출처 내에서는 `source_pages`와 `source_section`이 있는 청크를 우선하여 citation 추적성을 높인다.

## 재인덱싱 및 관리 규칙

- **Vector Store**: 초기 PoC는 ChromaDB 또는 단순 Numpy 벡터 연산으로 구현하고, 데이터 확충 시 관리형 DB(Pinecone 등) 고려.
- **Embedding 모델**: 모델 변경 시 모든 기존 청크를 재임베딩해야 하므로 버전 관리가 필수적임.
- **Chunk 관리**: `chunk_id`는 안정적으로 유지하며, 내용 변경 시 `updated_at` 필드를 갱신한다.
- **비활성화**: 삭제 대신 `active: false` metadata를 사용하여 과거 로그와의 참조 무결성을 유지한다.

## 품질 검증

초기 RAG 품질은 다음 기준으로 본다.

- 필수 필드 누락 0건
- 중복 `chunk_id` 0건
- 생육 단계별 최소 1개 이상 chunk 확보
- 위험 태그별 검색 hit 여부 확인
- citation_required chunk는 source_url 존재

기본 검증 명령:

벡터 검색과 평가 스크립트는 아래 환경 준비 후 실행한다.

```bash
python3 -m venv .venv
./.venv/bin/pip install -r requirements-rag.txt
```

OpenAI embedding 경로를 쓰려면 저장소 루트 `.env`에 `OPENAI_API_KEY`를 둔다. 스크립트는 `python-dotenv`로 `.env`를 자동 로드한다.

```bash
./.venv/bin/python scripts/validate_rag_chunks.py
./.venv/bin/python scripts/build_rag_index.py --skip-embeddings
./.venv/bin/python scripts/rag_smoke_test.py
./.venv/bin/python scripts/evaluate_rag_retrieval.py --fail-under 1.0
./.venv/bin/python scripts/build_chroma_index.py --embedding-backend local
./.venv/bin/python scripts/evaluate_rag_retrieval.py --vector-backend chroma --chroma-embedding-backend local --fail-under 1.0
./.venv/bin/python scripts/build_chroma_index.py --embedding-backend openai
./.venv/bin/python scripts/evaluate_rag_retrieval.py --vector-backend chroma --chroma-embedding-backend openai --fail-under 1.0
./.venv/bin/python scripts/tune_rag_weights.py --vector-backend chroma --chroma-embedding-backend openai --vector-weights 10 --chroma-local-blend-weights 0,2,4,6
```

현재 검증 상태:

- rows: 219
- duplicate chunk_id: 0
- validation errors: 0
- warnings: 0
- smoke tests: 기본 query 80개, metadata filter query 18개 PASS
- retrieval eval(keyword): 110개 case, hit rate 1.0, MRR 0.9909
- retrieval eval(local vector hybrid): 110개 case, hit rate 1.0, MRR 0.9955
- retrieval eval(local-backed Chroma hybrid): 110개 case, hit rate 1.0, MRR 0.9955
- retrieval eval(OpenAI-backed Chroma hybrid): 110개 case, hit rate 1.0, MRR 0.9803

현재 검색 기능:

- keyword search: chunk text와 주요 metadata 필드 검색
- metadata hard filter: `growth_stage`, `crop_type`, `source_type`, `sensor_tags`, `risk_tags`
- 확장 metadata filter: `source_section` 부분 일치, `trust_level`, `region`, `season`, `cultivar`, `greenhouse_type`, `active`
- index metadata 반영: `region`, `season`, `cultivar`, `greenhouse_type`, `farm_id`, `zone_id`, `outcome`를 JSON index metadata와 text field에 포함
- reranking: `trust_level`과 `source_type` 기반 bonus를 적용해 공식/고신뢰 출처를 우선 노출
- `farm_case`가 포함된 혼합 인덱스에서는 공식 지침과 `farm_case`가 동시에 맞는 경우 공식 지침을 먼저 정렬하는 guardrail을 적용
- local vector search: TF-IDF + SVD 기반 로컬 latent vector를 index에 포함하고 keyword score와 결합
- optional OpenAI vector search: `OPENAI_API_KEY`가 있고 embedding이 있으면 OpenAI embedding 검색을 keyword score와 결합
- ChromaDB vector store: `scripts/build_chroma_index.py`로 persistent collection을 만들고 `--vector-backend chroma`로 hybrid retrieval 실행
- Chroma embedding backend: `--embedding-backend local|openai`, `--chroma-embedding-backend local|openai`로 컬렉션/쿼리 임베딩 경로를 맞춤
- collection 분리: local은 `pepper_expert_chunks_local`, openai는 `pepper_expert_chunks_openai`, manifest도 backend별로 분리 생성
- OpenAI-backed Chroma는 local latent vector blend 4.0을 기본 적용해도 현재 평가셋에서는 MRR 0.9803으로 local/local-backed Chroma보다 낮다.

## 다음 구현

1. `data/rag/pepper_expert_seed_chunks.jsonl`을 250개 수준까지 확장하거나 `farm_case` 계층을 별도 증설
2. `RAG-SRC-001` PDF의 풋마름병, 저장·건조 세부와 양액재배/시설재배 잔여 장 추가 추출
3. retrieval 결과를 주기별 고정 리포트로 남기는 자동화 보강
4. `text` vs `chunk_summary` 임베딩 입력과 hybrid 가중치 재검토
5. Semantic + Keyword 하이브리드 검색 가중치 최적화
6. `docs/rag_contextual_retrieval_strategy.md` 기준으로 최근 3~5일 컨텍스트를 retrieval query builder에 실제 반영
7. 운영 로그와 센서 구간을 `farm_case` RAG 후보로 변환하는 파이프라인 설계
