# Training Sample Manual Review

이 문서는 `3.2 데이터 파일 생성`의 `이상 샘플 수동 검토` 기록이다. 기준 리포트는 `artifacts/reports/training_sample_stats.json`이다.

## 1. 검토 범위

- training seed `140건`
- eval seed `24건`
- longest sample 상위 5건
- 낮은 빈도 세부 `task_type`
- `recommended_actions.action_type` 분포

## 2. 자동 점검 결과

- duplicate sample id: `0`
- exact duplicate row: `0`
- potential contradiction: `0`
- task family 기준 balance: 7개 family 모두 `20건`

## 3. 세부 분포 확인

- 세부 `task_type`는 아직 불균형이 있다.
  - `climate_risk 4`
  - `harvest_drying 3`
  - `rootzone_diagnosis 3`
  - `nutrient_risk 2`
  - `pest_disease_risk 2`
  - `safety_policy 2`
  - `sensor_fault 2`
  - `state_judgement 2`
- `recommended_actions.action_type`는 `request_human_check 57`, `create_alert 40`으로 보수적 대응 쪽 비중이 높다.
- 직접 제어 action은 `adjust_fan`, `adjust_vent`, `adjust_heating`, `short_irrigation` 등이 각 1~2건 수준이라 이후 확장이 필요하다.

## 4. 길이 분포 확인

- input chars: `min 137`, `median 224`, `p90 346`, `max 538`
- output chars: `min 276`, `median 516`, `p90 1114`, `max 1242`
- longest sample 상위 5건은 모두 `action_recommendation` 계열이었다.

## 5. longest sample 수동 검토

검토 대상:

- `action-rec-002`
- `action-rec-009`
- `action-rec-001`
- `action-rec-006`
- `action-rec-016`

확인 결과:

- 모두 허용 `action_type`만 사용한다.
- 모두 `follow_up`이 최소 1건 이상 있다.
- 모두 `citations`가 2건씩 포함되어 있다.
- 길이가 긴 이유는 `diagnosis`, `reason`, `expected_effect`를 보수적으로 충분히 적어 둔 데 있다.
- 현재 단계에서는 outlier로 제거할 필요가 없고, 오히려 중위험 이상 action recommendation의 기준 예시로 유지하는 편이 낫다.

## 6. 후속 보강 포인트

1. 직접 제어 action 비중을 늘린다.
2. `sensor_fault`, `pest_disease_risk`, `safety_policy` 세부 sample을 10건 이상으로 늘린다.
3. `alert_report`와 `qa_reference` eval set을 추가한다.
