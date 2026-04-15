# 자동화 규칙 엔진 (Automation Rules) 런타임 스펙

- 범위: 운영자가 UI에서 정의한 `sensor_key → operator → threshold → device action` 규칙을 실시간 센서 스냅샷에 매칭해 장치 제어 제안을 생성하는 엔진.
- 목표: LLM 의사결정 경로와 동일한 안전 파이프라인(`policy_engine.output_validator` → `execution_gateway.guards` → `runtime_mode` 게이트)을 타면서 저지연 threshold 기반 자동화를 제공한다.
- 대상 독자: ops-api / llm-orchestrator / execution-gateway 개발자 + 현장 운영자.

## 1. 대상 장치

| target_device_type | 설명 | 예시 target_action |
|---|---|---|
| `roof_vent` | 천장 개폐기 (ceiling vent actuator) | `adjust_vent`, `close_vent` |
| `hvac_geothermal` | 지하수 활용 냉난방기 | `adjust_heating`, `adjust_cooling` |
| `humidifier` | 가습기 | `adjust_humidifier` |
| `fertigation_mixer` | 양액 비율 조정 | `adjust_fertigation` |
| `irrigation_pump` | 관수 펌프 | `short_irrigation` |
| `shade_curtain` | 차광 커튼 | `adjust_shade` |
| `fan_circulation` | 순환팬 | `adjust_fan` |
| `co2_injector` | CO₂ 공급기 | `adjust_co2` |

`target_action` 값은 `execution-gateway` / 기존 LLM action_type enum과 일관되게 유지한다. 엔진은 `proposed_action.action_type` 필드에 이 값을 그대로 담아 LLM 결정 파이프라인과 동일한 validator 체크를 거친다.

## 2. 센서 키 카탈로그

### 2.1 외부 기상
- `ext_air_temp_c` — 외부 공기 온도 (℃)
- `ext_rh_pct` — 외부 상대습도 (%)
- `ext_wind_dir_deg` — 외부 풍향 (0~360°)
- `ext_wind_speed_m_s` — 외부 풍속 (m/s)
- `ext_rainfall_mm` — 강우량 (mm, 누적 또는 window rate)

### 2.2 내부 기상
- `air_temp_c`, `rh_pct`, `co2_ppm`, `vpd_kpa`, `par_umol_m2_s`

### 2.3 배지 — Grodan Delta
- `substrate_delta_temp_c` — 슬래브 온도 (℃)
- `substrate_delta_moisture_pct` — 슬래브 수분 함량 (%)
- `substrate_delta_ph` — 배지 pH

### 2.4 배지 — GT Master
- `substrate_gt_master_temp_c`
- `substrate_gt_master_moisture_pct`
- `substrate_gt_master_ph`

### 2.5 공통 근권 (재배 통합)
- `substrate_temp_c`, `substrate_moisture_pct`
- `feed_ec_ds_m`, `drain_ec_ds_m`
- `feed_ph`, `drain_ph`

허용 집합은 `ops-api/ops_api/api_models.py::AUTOMATION_SENSOR_KEYS`에 고정되어 있다. UI 드롭다운과 API Literal 검증이 동일 집합을 참조한다.

## 3. 매칭 연산자

| operator | 의미 | 필드 |
|---|---|---|
| `gt` | value > threshold | `threshold_value` |
| `gte` | value ≥ threshold | `threshold_value` |
| `lt` | value < threshold | `threshold_value` |
| `lte` | value ≤ threshold | `threshold_value` |
| `eq` | value == threshold (부동소수점 1e-9) | `threshold_value` |
| `between` | `threshold_min` ≤ value ≤ `threshold_max` | `threshold_min`, `threshold_max` |

`hysteresis_value` 는 Phase O-3 스펙에 포함돼 있지만 첫 구현은 미사용(cooldown 기반 re-trigger 억제로 대체). 향후 noise suppression 시 활용 예정.

## 4. Runtime Mode Gate

각 규칙은 `runtime_mode_gate ∈ {shadow, approval, execute}` 필드를 가진다.
엔진은 규칙 게이트와 전역 `runtime_mode` 중 **더 엄격한 쪽**을 따른다.

| 규칙 게이트 | 전역 runtime_mode | 실제 동작 |
|---|---|---|
| shadow | 무관 | `shadow_logged` (trigger만 기록) |
| approval | shadow | `shadow_logged` |
| approval | approval 이상 | `approval_pending` (승인 대기 decision 생성 예정) |
| execute | execute | `dispatched` (execution_gateway 요청) |
| execute | approval | `approval_pending` |
| execute | shadow | `shadow_logged` |

→ 신규 규칙은 먼저 `approval` 게이트로 등록해 실증 기간을 두고, 현장 확인 후 `execute`로 승격하는 것이 기본 흐름이다.

## 5. 안전 파이프라인

모든 매칭 trigger는 다음 순서를 통과해야 실행 후보가 된다.

```
sensor snapshot
    │
    ▼
evaluate_rules(session, runtime_mode, snapshot)
    │
    ├─ cooldown check (같은 규칙이 최근 cooldown_minutes 내 fire 여부)
    │
    ├─ policy_engine.output_validator.apply_output_validator
    │     - HSV/OV 20개 hard-safety 규칙 교정
    │     - citation 정책, worker_present/manual_override/safe_mode 체크
    │
    ├─ execution_gateway.guards.check (구현 예정)
    │     - 작업자 재실, zone clearance, sensor_quality degraded 차단
    │
    └─ runtime_mode gate (shadow / approval / execute)
        → automation_rule_triggers.status 에 기록
```

현재 첫 구현은 **stateless matching + runtime_mode gate + cooldown + 트리거 로깅**까지 포함한다. validator / guard 호출 통합은 Phase P에서 추가 예정 (엔진은 `_build_proposed_action`이 pepper-ops 스키마와 호환되는 dict를 만들기 때문에 기존 validator에 바로 흘릴 수 있다).

## 6. API 엔드포인트

| 메서드 | 경로 | 권한 | 설명 |
|---|---|---|---|
| GET | `/automation/rules` | `read_runtime` | 전체 규칙 목록 (priority ASC) |
| POST | `/automation/rules` | `manage_automation` | 신규 규칙 생성 |
| GET | `/automation/rules/{rule_id}` | `read_runtime` | 단일 규칙 조회 |
| PATCH | `/automation/rules/{rule_id}` | `manage_automation` | 규칙 부분 수정 |
| DELETE | `/automation/rules/{rule_id}` | `manage_automation` | 규칙 삭제 |
| PATCH | `/automation/rules/{rule_id}/toggle` | `manage_automation` | enabled 플래그만 토글 |
| GET | `/automation/triggers?limit=N` | `read_runtime` | 최근 trigger 조회 (default 50, max 200) |
| POST | `/automation/evaluate` | `read_runtime` | sensor_snapshot dry-run (persist=False) |

`manage_automation` 권한은 `operator`/`admin` 역할이 가진다. `viewer`는 규칙 조회만 가능.

## 7. 데이터 모델

### 7.1 `automation_rules`

```
rule_id              VARCHAR(128) UNIQUE
name                 VARCHAR(200)
description          TEXT
zone_id              VARCHAR(128) NULL        -- NULL이면 전 구역 대상
sensor_key           VARCHAR(64)              -- §2 카탈로그
operator             VARCHAR(16)              -- §3 enum
threshold_value      DOUBLE PRECISION NULL
threshold_min        DOUBLE PRECISION NULL
threshold_max        DOUBLE PRECISION NULL
hysteresis_value     DOUBLE PRECISION NULL    -- Phase P 예정
cooldown_minutes     INTEGER DEFAULT 15
target_device_type   VARCHAR(64)              -- §1 enum
target_device_id     VARCHAR(128) NULL
target_action        VARCHAR(64)              -- pepper-ops action_type
action_payload_json  TEXT                     -- 디바이스별 파라미터
priority             INTEGER DEFAULT 100
enabled              INTEGER (0/1)
runtime_mode_gate    VARCHAR(16) DEFAULT 'approval'
owner_role           VARCHAR(32) DEFAULT 'operator'
created_by / created_at / updated_at
```

### 7.2 `automation_rule_triggers`

```
rule_id              INTEGER REFERENCES automation_rules(id) ON DELETE CASCADE
triggered_at         TIMESTAMP
zone_id              VARCHAR(128) NULL
sensor_key           VARCHAR(64)
matched_value        DOUBLE PRECISION
sensor_snapshot_json TEXT
proposed_action_json TEXT
status               VARCHAR(32)   -- shadow_logged | approval_pending | dispatched
                                     | blocked_validator | blocked_guard | cooldown_skipped
runtime_mode         VARCHAR(16)
decision_id          INTEGER NULL  -- LLM decisions 연결 (approval/execute 경로에서)
note                 TEXT
```

## 8. UI (대시보드 · 자동화 뷰)

- 사이드바 10번째 메뉴 `자동화` (material-symbols `rule`)
- **규칙 목록 카드**: 각 규칙을 `IF sensor operator threshold THEN action @ device` 한 줄로 표시, enabled/gate/priority 칩 + 활성화/편집/삭제 액션
- **최근 trigger 카드**: 최근 25개 trigger, status 별 chip(`dispatched`→enabled, `approval_pending`→warn, `blocked_*`→critical, `shadow_logged/cooldown_skipped`→dark)
- **생성/편집 모달**: rule_id / name / description / zone_id / priority / cooldown / sensor_key 드롭다운(optgroup 5개) / operator / threshold 입력(between 시 min/max 행 토글) / target_device_type 드롭다운 / target_device_id / target_action / action_payload JSON / runtime_mode_gate / enabled
- **Runtime Mode chip**: 현재 전역 runtime_mode를 컬러로 노출(`shadow`→green, `approval`→warn, `execute`→critical)
- **안전 배너**: "runtime_mode_gate와 전역 runtime_mode 중 더 엄격한 쪽을 따릅니다. 신규 규칙은 approval로 시작해 검증 후 execute로 승격하세요."

## 9. 사용 예시

### 9.1 강우 시 천장 닫기
```json
{
  "rule_id": "rain-close-vent",
  "name": "강우 시 천장 닫기",
  "description": "강우량이 10분당 0.5mm를 넘으면 천장을 즉시 닫는다",
  "sensor_key": "ext_rainfall_mm",
  "operator": "gt",
  "threshold_value": 0.5,
  "target_device_type": "roof_vent",
  "target_action": "close_vent",
  "action_payload": {"target_position_pct": 0},
  "runtime_mode_gate": "execute",
  "priority": 10,
  "cooldown_minutes": 5
}
```

### 9.2 GT Master dry-back 과다 시 경고만 (양액 자동 조정 금지)
```json
{
  "rule_id": "gt-master-dryback-alert",
  "name": "GT Master dry-back 과다 경고",
  "sensor_key": "substrate_gt_master_moisture_pct",
  "operator": "lt",
  "threshold_value": 55,
  "target_device_type": "fertigation_mixer",
  "target_action": "create_alert",
  "runtime_mode_gate": "approval",
  "priority": 50,
  "cooldown_minutes": 30
}
```

Phase H 실험에서 확인된 것처럼 GT Master dry-back에는 `adjust_fertigation`를 자동으로 걸지 않는다. 규칙은 `create_alert`만 내고 현장 확인을 기다린다.

### 9.3 외부 풍속 10m/s 초과 시 차광 전개
```json
{
  "rule_id": "wind-shade-deploy",
  "name": "강풍 시 차광 커튼 전개",
  "sensor_key": "ext_wind_speed_m_s",
  "operator": "gte",
  "threshold_value": 10,
  "target_device_type": "shade_curtain",
  "target_action": "adjust_shade",
  "action_payload": {"target_position_pct": 80},
  "runtime_mode_gate": "approval",
  "priority": 40,
  "cooldown_minutes": 20
}
```

## 10. 로드맵

- ✅ Phase O-1: 데이터 모델 + migration
- ✅ Phase O-2: API + 권한
- ✅ Phase O-3: Rule engine evaluator (matching + cooldown + gate + trigger 로그)
- ✅ Phase O-4: UI (목록 + 모달 + trigger 로그)
- ✅ Phase O-5: 본 문서 + smoke + 커밋/푸시
- ⏭️ Phase P: `policy_engine.output_validator` + `execution_gateway.guards` 통합, 백그라운드 센서 루프, hysteresis, approval queue 연결
- ⏭️ Phase Q: `AutomationRuleRecord ↔ DecisionRecord` 양방향 FK, shadow_window 편입

## 11. 관련 파일

- `ops-api/ops_api/models.py` — `AutomationRuleRecord`, `AutomationRuleTriggerRecord`
- `ops-api/ops_api/api_models.py` — `AutomationRule*Request`, `AUTOMATION_*` enum
- `ops-api/ops_api/automation.py` — `evaluate_rules`, `RuleMatch`, `EvaluationReport`, `serialize_rule`, `serialize_trigger`
- `ops-api/ops_api/app.py` — 7 엔드포인트 + 대시보드 view / modal / JS 로직
- `infra/postgres/003_automation_rules.sql` — Postgres 스키마
- `scripts/validate_ops_api_automation_rules.py` — 회귀 smoke
- `docs/automation_rules_runtime.md` — **본 문서**
