# Automation Trigger Review Runbook (Phase P-3)

`AutomationRunner` (Phase P-2)가 `sensor_readings`를 주기적으로 스캔해 규칙을 평가하고, `runtime_mode=approval` + `runtime_mode_gate=approval` 조건이 교차하면 trigger row가 `status=approval_pending` 으로 남는다. Phase P-3은 그 pending 목록을 운영자가 승인 / 거부할 수 있는 API를 제공한다.

실제 장치 dispatch 연결은 Phase Q에서 `DecisionRecord ↔ AutomationRuleTriggerRecord` FK가 확장된 뒤 이뤄진다. Phase P-3에서의 "approved"는 **운영자가 해당 trigger를 실행해도 된다고 공식 기록을 남긴 상태**이며, 명령은 Phase Q 이후에 자동 발행된다.

## 1. 전제 조건

| 조건 | 확인 방법 |
|---|---|
| `OPS_API_AUTOMATION_ENABLED=true` + `OPS_API_DATABASE_URL` Postgres | `GET /health` 200 → dashboard 기동 확인 |
| `runtime_mode=approval` | `GET /runtime-mode` → `mode=approval` |
| 대상 규칙 `runtime_mode_gate=approval` 이상 | `GET /automation/rules` → `runtime_mode_gate` 확인 |
| 해당 zone `sensor_readings` 흐름 활성 | 최근 `automation_snapshot_window_sec`(기본 120s) 안에 metric row 존재 |

위 조건이 모두 충족되면 tick마다 `automation_rule_triggers`에 `status=approval_pending` 행이 쌓인다.

## 2. API 흐름

### 2.1 Pending 목록 조회

```
GET /automation/triggers?status=approval_pending&zone_id=gh-01-zone-a&limit=50
```

응답은 `data.triggers[]` 배열. 각 row는 다음 필드를 포함한다.

| 필드 | 설명 |
|---|---|
| `id` | trigger row primary key. approve/reject 경로에서 사용. |
| `rule_id` | `AutomationRuleRecord.id` (FK). 정책을 재확인하려면 `GET /automation/rules` 의 `id` 매칭. |
| `sensor_key`, `matched_value` | 어떤 센서값이 threshold를 넘었는지. |
| `proposed_action` | 실행 시 전송될 명령 스키마(device_type, action, target 등). |
| `runtime_mode`, `status` | 현재 trigger가 적용받는 farm-wide 모드와 상태. |
| `reviewed_by`, `reviewed_at`, `review_reason` | Phase P-3 승인/거부 이력. pending 상태에서는 모두 null/`""`. |

### 2.2 승인

```
POST /automation/triggers/{id}/approve
Content-Type: application/json
{ "reason": "야간 환기 허용 — co2 420ppm 초과 확인" }
```

- 권한: `approve_actions`.
- 상태 전이: `approval_pending → approved`.
- 응답 `data` 에 승인된 trigger 전체가 반환되고 `meta.reviewed = "approved"`.

### 2.3 거부

```
POST /automation/triggers/{id}/reject
{ "reason": "센서 보정 미완 — 이번 주기 스킵" }
```

- 권한: `approve_actions`.
- 상태 전이: `approval_pending → rejected`.

### 2.4 오류 코드

| 코드 | 원인 | 조치 |
|---|---|---|
| 404 | trigger_id 없음 (삭제됐거나 오타). | 목록에서 id 재확인. |
| 409 | 이미 approved/rejected/dispatched/… — `approval_pending` 아님. | 상태 재조회, 필요하면 신규 tick 대기. |
| 403 | 호출자가 `approve_actions` 권한 미보유. | `/auth/token` 또는 `OPS_API_AUTH_MODE` 점검. |

## 3. 운영 의사결정 체크리스트

운영자는 승인 전에 다음을 확인한다.

1. **규칙 의도 재확인** — `proposed_action.reason` 필드에 `automation_rule:{rule_id} → {sensor_key} {op}` 가 찍혀 있다. 규칙 id 가 예상한 것인지, 의도와 현재 상황이 일치하는지.
2. **센서값 재현성** — `matched_value` 가 일시적 spike 였는지, window 안에서 반복 관측되는지. `GET /metrics/sensor-readings?zone_id=...&metric_name=...` (또는 Grafana 대시보드)로 교차 검증.
3. **충돌 규칙 확인** — 같은 device_type 에 대해 정반대 방향 규칙이 동시에 pending 인지. 있으면 우선순위 높은 한쪽만 승인하고 나머지는 reject.
4. **시간대 제약** — 야간/장마/강풍 시 고위험 액션(`adjust_heating`, `adjust_fertigation`)은 `approval_governance.md §2 중위험/고위험` 원칙을 따른다. 의심되면 거부 후 수동 `/actions/execute` 경로로 처리.

## 4. 대시보드 연동 (예정)

- 현재 `/dashboard` Approvals 패널은 LLM DecisionRecord 기반이며 automation trigger는 별도 렌더링이 안 된다.
- Phase P-3 API가 열렸으므로 대시보드에 `Automation Pending` 탭을 추가하는 것이 다음 작업. 구현 시 `GET /automation/triggers?status=approval_pending` 결과를 주기적으로 폴링해 rule 이름/센서값/proposed_action 요약과 "승인/거부" 버튼을 노출한다.

## 5. 점검용 수동 호출 예시

로컬 `.env` + `OPS_API_AUTH_MODE=disabled` 기준:

```bash
# 1) pending 조회
curl -s 'http://localhost:8000/automation/triggers?status=approval_pending&limit=20' | jq '.data.triggers[] | {id,rule_id,sensor_key,matched_value,proposed_action}'

# 2) 승인 (trigger id=42 예시)
curl -sX POST http://localhost:8000/automation/triggers/42/approve \
  -H 'Content-Type: application/json' \
  -d '{"reason":"runbook §3 체크 완료"}' | jq .

# 3) 거부
curl -sX POST http://localhost:8000/automation/triggers/42/reject \
  -H 'Content-Type: application/json' \
  -d '{"reason":"센서 보정 필요"}' | jq .
```

## 6. 후속 연결

- **Phase Q**: `approved` trigger를 DeviceCommandRecord 로 flush 하는 dispatcher 추가. `status = approved → dispatched` 전이.
- **P-3.5 (선택)**: 대시보드 `Automation Pending` UI. `/dashboard` 에서 `approvals` 카드 옆에 병렬 배치.
- **모니터링**: Phase O-M 의 trigger 통계 API(`GET /automation/triggers?status=…`)를 그대로 사용해 approval / rejection 비율을 관찰한다.
