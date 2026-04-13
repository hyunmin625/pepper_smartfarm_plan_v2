# state-estimator

센서 raw/feature 데이터를 받아 zone state와 risk score를 계산하는 서비스다.

## 현재 MVP 범위

- 합성 센서 시나리오 기반 zone state 추정
- `feature_schema.json` 형태의 derived feature snapshot 생성
- raw sensor/device runtime row -> state snapshot loader
- `sensor_quality`가 신뢰 불가이면 `risk_level=unknown`으로 승격
- `pause_automation + request_human_check` 같은 보수적 기본 조합 반환
- `safe_mode_entry required`, `robot_safety_breach` 같은 강한 시그널은 `critical` 유지

## 현재 구현 파일

- `state-estimator/state_estimator/estimator.py`
- `state-estimator/state_estimator/features.py`
- `scripts/validate_state_estimator_mvp.py`
- `scripts/validate_state_estimator_features.py`
- `scripts/validate_state_estimator_raw_loader.py`
- `data/examples/synthetic_sensor_scenarios.jsonl`
- `data/examples/raw_sensor_window_seed.jsonl`

## 검증 명령

```bash
python3 scripts/validate_state_estimator_mvp.py
python3 scripts/validate_state_estimator_features.py
python3 scripts/validate_state_estimator_raw_loader.py
python3 scripts/validate_synthetic_scenarios.py
```

## MVP 판단 원칙

- `sensor_quality.overall=bad` 또는 핵심 센서 `stale/missing/flatline/communication_loss`면 자동으로 `unknown`
- `unknown` 상태에서는 `pause_automation`, `request_human_check`를 우선
- 재부팅 후 state sync 미완료, robot safety breach처럼 명확한 강위험은 `critical`
- VPD, DLI, 1분/5분 평균, 10분/30분 변화율, 관수 후 회복률, 배액률, climate/rootzone stress score를 함께 계산해 LLM 입력용 snapshot을 만든다.
- `sensor-ingestor`에서 나온 raw row를 바로 snapshot으로 올릴 수 있도록 window loader를 유지한다.
