# Policy Event Filter Performance Plan

현재 `/policies/events`는 `event_type`, `request_id`를 SQL 필터로 처리하고, `policy_id`는 `policy_event_policy_links` 정규화 테이블을 join해 처리한다. `policy_ids_json`은 API 응답 호환성과 audit payload 보존을 위해 유지한다.

## 현재 단기 기준

- `event_type` 필터는 DB index를 사용한다.
- `request_id` 필터는 DB index를 사용한다.
- `policy_id` 필터는 `policy_event_policy_links(policy_id, policy_event_id DESC)` index를 사용한다.
- dashboard는 최근 event queue/이력 확인용으로만 사용하고, 장기 감사 리포트는 별도 export/report 스크립트에서 처리한다.

## 운영 한계 신호

아래 중 하나가 확인되면 추가 index 또는 materialized reporting table을 검토한다.

- `/policies/events?policy_id=...`가 최근 변경 이력을 놓친다.
- policy event row가 `500,000건`을 넘는다.
- dashboard policy history 조회 p95가 `500ms`를 넘는다.
- 감사 리포트에서 policy별 집계가 자주 필요해진다.

## 정규화 설계

`policy_event_policy_links` 테이블을 추가한다.

```text
policy_event_policy_links
- id
- policy_event_id -> policy_events.id
- policy_id
- created_at
```

권장 index:

- `(policy_id, policy_event_id DESC)`
- `(policy_event_id)`

적용 순서:

1. `infra/postgres/006_policy_event_policy_links.sql`로 새 테이블과 index 추가
2. 기존 `policy_events.policy_ids_json`을 backfill
3. `PolicyEventRecord` 생성 시 link row 동시 insert
4. `/policies/events`와 `/policies/{policy_id}/history`를 link table join으로 전환
5. `policy_ids_json`은 backward compatibility용 read model로 유지

## 현재 결정

2026-04-26 기준 1차 정규화는 적용됐다. 회귀 검증은 `scripts/validate_policy_event_link_table.py`와 `scripts/validate_ops_api_runtime_review_surfaces.py`가 담당한다.
