# Policy Event Filter Performance Plan

현재 `/policies/events`는 `event_type`, `request_id`는 SQL 필터로 처리하고, `policy_id`는 `policy_ids_json` 텍스트를 읽은 뒤 JSON 후처리로 필터링한다. 이 방식은 현재 운영/검증 규모에서는 충분하지만, policy event가 수만 건 이상 누적되면 scan limit에 걸릴 수 있다.

## 현재 단기 기준

- `event_type` 필터는 DB index를 사용한다.
- `request_id` 필터는 DB index를 사용한다.
- `policy_id` 필터는 최근 `500건` 이내에서만 후처리한다.
- dashboard는 최근 event queue/이력 확인용으로만 사용하고, 장기 감사 리포트는 별도 export/report 스크립트에서 처리한다.

## 운영 한계 신호

아래 중 하나가 확인되면 정규화 마이그레이션으로 넘어간다.

- `/policies/events?policy_id=...`가 최근 변경 이력을 놓친다.
- policy event row가 `50,000건`을 넘는다.
- dashboard policy history 조회 p95가 `500ms`를 넘는다.
- 감사 리포트에서 policy별 집계가 자주 필요해진다.

## 장기 설계

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

마이그레이션 순서:

1. 새 테이블과 index 추가
2. 기존 `policy_events.policy_ids_json`을 backfill
3. `PolicyEventRecord` 생성 시 link row 동시 insert
4. `/policies/events`와 `/policies/{policy_id}/history`를 link table join으로 전환
5. `policy_ids_json`은 backward compatibility용 read model로 유지

## 현재 결정

2026-04-25 기준은 정규화 전 단계다. 실제 운영 event volume이 적고, dashboard 조회는 최근 운영 판단용이므로 JSON 후처리 필터 + scan limit으로 유지한다.
