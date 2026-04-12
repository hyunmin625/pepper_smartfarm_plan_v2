# Training Sample Manual Review

이 문서는 `3.2 데이터 파일 생성`의 `이상 샘플 수동 검토` 기록이다. 기준 리포트는 `artifacts/reports/training_sample_stats.json`이다.

## 1. 검토 범위

- training seed `194건`
- 기본 validation 기준 eval `144건`
- longest sample 상위 5건
- 낮은 빈도 세부 `task_type`
- `recommended_actions.action_type` 분포

## 2. 자동 점검 결과

- duplicate sample id: `0`
- exact duplicate row: `0`
- potential contradiction: `0`
- eval overlap row: `0`
- class imbalance ratio: `10.00`

## 3. 세부 분포 확인

- 세부 `task_type`는 아직 불균형이 있다.
  - `rootzone_diagnosis 5`
  - `harvest_drying 4`
  - `nutrient_risk 3`
  - `climate_risk 6`
  - `pest_disease_risk 6`
  - `safety_policy 14`
  - `sensor_fault 6`
  - `state_judgement 7`
- `recommended_actions.action_type`는 `request_human_check 90`, `create_alert 69`로 보수적 대응 쪽 비중이 매우 높다.
- 반면 실제 hard-block 계열은 `block_action 12`, `enter_safe_mode 8`, `pause_automation 16`으로 여전히 얇다.
- 직접 제어 action은 `adjust_fan 1`, `adjust_fertigation 2`, `adjust_heating 4`, `adjust_shade 3`, `adjust_vent 3`, `short_irrigation 1` 수준이라 이후 확장이 필요하다.

## 4. 길이 분포 확인

- input chars: `min 137`, `median 236`, `p90 350`, `max 538`
- output chars: `min 276`, `median 655`, `p90 1277`, `max 1620`
- longest sample 상위 5건은 모두 `state_judgement` corrective 계열이었다.

## 5. longest sample 수동 검토

검토 대상:

- `state-judgement-045`
- `state-judgement-035`
- `state-judgement-037`
- `state-judgement-042`
- `state-judgement-040`

확인 결과:

- 모두 허용 `action_type`만 사용한다.
- 모두 `follow_up`과 `citations`가 포함되어 있다.
- 길이가 긴 이유는 `rootzone evidence incomplete`, `manual_override`, `failure safe_mode` 같은 경계 조건을 동시에 설명하기 때문이다.
- 현재 단계에서는 outlier로 제거할 필요가 없고, 오히려 `risk_level unknown/critical` 경계 사례의 기준 예시로 유지하는 편이 낫다.

## 6. 후속 보강 포인트

1. 직접 제어 action 비중을 늘린다.
2. `sensor_fault`, `failure_response safe_mode`, `safety_policy hard block`, `rootzone evidence incomplete`를 우선 보강한다.
3. `block_action`과 `enter_safe_mode` 비중을 늘리되, `robot_task`는 건수보다 계약 품질을 먼저 보강한다.
