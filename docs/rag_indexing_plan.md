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
- `chunk_summary`
- `agent_use`
- `citation_required`

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
    "agent_use": ["irrigation-agent"],
    "citation_required": true
  }
}
```

## 검색 전략

초기 검색은 hybrid 구조를 목표로 한다.

- semantic search: chunk text embedding 기반 검색
- metadata filtering: 생육 단계, 센서, 위험, agent 기준 필터
- keyword fallback: `risk_tags`, `sensor_tags`, `operation_tags` 문자열 검색

## 재인덱싱 규칙

- `chunk_id`는 안정적으로 유지한다.
- 원문이나 요약이 바뀌면 `updated_at` 또는 `source_version`을 추가한다.
- 삭제 대신 `active: false` metadata를 사용한다.
- 공식 자료와 보조 자료는 `source_type`으로 구분한다.

## 품질 검증

초기 RAG 품질은 다음 기준으로 본다.

- 필수 필드 누락 0건
- 중복 `chunk_id` 0건
- 생육 단계별 최소 1개 이상 chunk 확보
- 위험 태그별 검색 hit 여부 확인
- citation_required chunk는 source_url 존재

## 다음 구현

1. `scripts/build_rag_index.py` 작성
2. JSONL 필수 필드 검증
3. `artifacts/rag_index/pepper_expert_index.json` 생성
4. 검색 smoke test 쿼리 작성
5. 향후 OpenAI Vector Store 또는 별도 Vector DB 연결
