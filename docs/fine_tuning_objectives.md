# Fine-tuning Objectives

이 문서는 `3.1 학습 목표 재정의`의 기준 문서다. 목적은 RAG와 파인튜닝의 역할을 분리하고, 운영형 모델이 반드시 지켜야 할 출력 계약을 고정하는 것이다.

## 1. 역할 구분

### 지식형 계층

- 최신 재배 기준, 품종 차이, 병해 조건, SOP, 정책 근거는 RAG가 담당한다.
- 수치 기준이 자주 바뀌거나 출처 추적이 필요한 내용은 파인튜닝으로 암기시키지 않는다.
- 근거가 필요한 설명은 citation이 있는 retrieved context를 우선 사용한다.

### 운영형 계층

- 파인튜닝은 JSON 출력 안정화와 운영 행동 양식을 담당한다.
- 같은 입력에서 일관된 `action_type`, `requires_human_approval`, `follow_up`, `confidence`를 내는 것이 목표다.
- 위험 상황에서는 적극적 제어보다 보수적 거절, 승인 요청, 재확인을 우선한다.

## 2. 파인튜닝 목표

- `schemas/action_schema.json`을 안정적으로 만족하는 구조화 출력을 생성한다.
- 허용된 `action_type`만 사용한다.
- 센서 품질과 retrieval 근거가 부족하면 자동 실행 추천을 축소한다.
- 위험도가 높을수록 승인 요구와 후속 확인을 명확히 남긴다.
- 검색 근거가 있을 때는 `citations`와 `retrieval_coverage`를 빠뜨리지 않는다.

## 3. 구조화 출력 목표

운영형 모델의 기본 출력 목표는 `schemas/action_schema.json` 기준이며, 핵심 필수 필드는 아래와 같다.

- `schema_version`
- `decision_id`
- `created_at`
- `farm_id`
- `zone_id`
- `situation_summary`
- `risk_level`
- `recommended_actions`
- `requires_human_approval`
- `follow_up`
- `confidence`
- `retrieval_coverage`
- `citations`

`robot_tasks`는 필요 없으면 빈 배열을 허용하지만, `follow_up`은 항상 비우지 않는다.

## 4. 허용 action_type

현재 허용 목록은 아래로 고정한다.

- `observe_only`
- `create_alert`
- `request_human_check`
- `adjust_fan`
- `adjust_shade`
- `adjust_vent`
- `short_irrigation`
- `adjust_fertigation`
- `adjust_heating`
- `adjust_co2`
- `pause_automation`
- `enter_safe_mode`
- `create_robot_task`
- `block_action`

이 목록 밖의 action은 출력하면 안 된다. 새로운 action은 schema, policy, execution-gateway 계약이 먼저 추가된 뒤에만 허용한다.

## 5. confidence 요구

- `0.85 ~ 1.00`: 센서 품질이 양호하고, 최근 이벤트와 retrieval 근거가 충분하며, 추천 행동이 저위험 또는 검증된 패턴일 때만 사용
- `0.60 ~ 0.84`: 상황 해석은 가능하지만 일부 센서 품질 저하, 부분 근거, 추가 확인이 필요한 경우
- `0.00 ~ 0.59`: 근거가 부족하거나 충돌할 때. 이 구간에서는 위험 장치 제어보다 `observe_only`, `create_alert`, `request_human_check`를 우선

confidence는 위험도와 별개다. `high` risk라도 근거가 명확하면 confidence가 높을 수 있고, `low` risk라도 센서 품질이 나쁘면 confidence는 낮아질 수 있다.

## 6. follow_up 요구

- 모든 출력은 최소 1개의 `follow_up`을 포함한다.
- `sensor_fault`, `failure_response` 계열은 `sensor_recheck` 또는 `operator_confirm`를 반드시 포함한다.
- 장치 제어 추천이 있으면 `device_readback` 또는 `trend_review`를 포함한다.
- `due_in_minutes`는 즉시 대응이면 `0~5`, 상태 추적이면 `10~60`, 장기 점검이면 `60+`를 사용한다.

## 7. citations / retrieval_coverage 요구

- RAG를 사용한 판단은 `citations`를 비워 두지 않는다.
- `retrieval_coverage`는 아래 네 값만 허용한다.
  - `sufficient`
  - `partial`
  - `insufficient`
  - `not_used`
- `retrieval_coverage=insufficient`이면 중위험 이상 장치 제어를 바로 추천하지 않는다.
- `retrieval_coverage=not_used`는 운영형 행동 양식만 필요한 내부 포맷 변환이나 보고서 생성처럼 근거 문서가 없는 경우에만 사용한다.

## 8. 구현 연결점

- task taxonomy: `docs/dataset_taxonomy.md`
- seed/eval 포맷: `docs/training_data_format.md`
- 출력 schema: `schemas/action_schema.json`
- 안전 요구사항: `docs/safety_requirements.md`
- 장치 운전 규칙: `docs/device_operation_rules.md`

## 9. prompt_v3 초안

`prompt_v3`는 ds_v2/prompt_v2 eval에서 남은 9개 실패 패턴을 직접 겨냥한다.

- `sensor_fault`: 핵심 제어 센서 stale/missing/calibration fault면 `risk_level=unknown`을 우선하고, `pause_automation + request_human_check`를 강제한다.
- `pest_disease_risk`: 비전 score와 고온다습만으로는 확진하지 않고 `risk_level=medium`, `create_alert + request_human_check`를 기본 조합으로 둔다.
- `harvest_drying`: 수확/건조 계획형 케이스에서는 `request_human_check`를 필수로 두고, `create_robot_task`는 사람 확인 뒤 보조로만 허용한다.
- `safety_policy`: `worker_present`, `manual_override`, `safe_mode`가 active면 `block_action + create_alert`를 우선한다.
- `manual_override + safe_mode`: 이미 safe mode가 걸린 상태에서는 `enter_safe_mode` 반복보다 `block_action`을 우선한다.
- `spring transplant`: 정식 직후 `cold_night + overwet` 조합은 `risk_level=medium`을 기본으로 두고 `short_irrigation`은 금지한다.
- `drying/storage humidity`: 고습·재흡습 우려는 곰팡이/결로 확정 전까지 `risk_level=medium`으로 둔다.
- `flowering heat + strong radiation`: 개화기 고온·강광은 `risk_level=high`를 기본으로 둔다.
- `forbidden_action.adjust_fertigation`: EC/pH·배액 근거가 깨졌지만 hard interlock은 아니면 `decision=approval_required`를 기본으로 둔다.

## 10. prompt_v4 초안

`prompt_v4`는 ds_v3/prompt_v3 eval에서 남은 8개 실패 패턴을 직접 겨냥한다.

- `sensor_fault`: 핵심 제어 센서 stale/missing/inconsistent면 `risk_level=unknown`을 우선하고 `pause_automation + request_human_check`를 필수 조합으로 둔다. `create_alert`는 대체 수단이 아니다.
- `pest_disease_risk`: 비전 의심과 고온다습만으로는 확진하지 않고 `risk_level=medium`, `create_alert + request_human_check`를 기본으로 둔다. 의심 단계에서는 `create_robot_task`를 금지한다.
- `worker_present`: 작업자 존재 시 `block_action + create_alert`를 필수로 두고 `request_human_check`는 보조로만 허용한다.
- `manual_override + safe_mode`: 이미 safe mode가 latch된 상태에서는 `enter_safe_mode` 반복보다 `block_action + create_alert`를 우선한다.
- `dry-room communication_loss`: 건조실/저장실 장치 통신 손실은 `risk_level=critical`, `enter_safe_mode + request_human_check`를 기본 조합으로 둔다. `pause_automation`만으로 끝내지 않는다.
- `winter nursery`: 겨울 육묘기의 저온과 저광량은 `risk_level=high`, `create_alert + request_human_check`를 기본으로 두고 `adjust_heating`은 승인 후 보조로만 붙인다.
- `spring transplant + Grodan slab overwet`: 정식 직후 저온과 암면 슬래브 과습은 `risk_level=medium`, `request_human_check`를 기본으로 두고 `short_irrigation`은 금지한다.
- `flowering heat + strong radiation`: 개화기 고온·강광은 `risk_level=high`, `create_alert + request_human_check`를 필수로 두고 `adjust_vent/fan/shade`는 보조 대응으로만 붙인다.
