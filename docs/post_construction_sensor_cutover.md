# Post Construction Sensor Cutover

이 문서는 온실 공사 완료 후 문서/합성 데이터 기반 준비 상태에서 실제 센서 연결 운영으로 전환하는 절차를 정의한다.

## 1. 전환 전 조건

- `sensor_catalog_seed.json`과 `sensor_ingestor_config_seed.json`이 최신 상태여야 한다.
- zone, sensor, device naming 규칙이 확정돼 있어야 한다.
- PLC controller id와 장치 profile이 catalog와 일치해야 한다.
- 필수 센서 보정 상태가 확인돼야 한다.

## 2. 전환 순서

1. 설치 확인
   - zone별 센서/장치 실제 수량과 catalog를 대조한다.
2. 통신 확인
   - 각 센서/PLC endpoint 연결 여부를 개별 확인한다.
3. 보정 확인
   - `calibration_version`, 보정일, 기준 장비를 기록한다.
4. dry-run 수집
   - `sensor-ingestor`를 publish-only shadow 모드로 실행한다.
5. 품질 점검
   - missing, stale, jump, flatline, readback mismatch를 점검한다.
6. 병렬 운영
   - 합성/문서 기반 판단과 실측 기반 판단을 함께 비교한다.
7. feature 파이프라인 전환
   - VPD, DLI, rootzone trend를 실제 데이터 기준으로 재계산한다.
8. AI 입력 전환
   - `shadow mode`에서 실측 데이터만 사용한 판단 로그를 축적한다.
   - `scripts/run_shadow_mode_capture_cases.py`로 일자별 shadow audit를 적재한다.
   - `scripts/build_shadow_mode_window_report.py`로 2일 이상 rolling window 요약을 만든다.
9. rollback 준비
   - 품질 기준 미달 시 `.env`와 config를 이전 shadow-only 설정으로 되돌린다.

## 3. 완료 기준

- must-have 센서 품질 `good` 또는 승인된 `partial`
- 주요 장치 readback 정상
- 24시간 이상 연속 수집 성공
- feature 생성 실패율 1% 이하
- shadow report에 blocking issue 없음

## 4. 연결 파일

- `docs/sensor_collection_plan.md`
- `docs/sensor_installation_inventory.md`
- `docs/sensor_ingestor_config_spec.md`
- `docs/sensor_ingestor_runtime_flow.md`
- `docs/shadow_mode_report_format.md`
- `docs/real_shadow_mode_runbook.md`
