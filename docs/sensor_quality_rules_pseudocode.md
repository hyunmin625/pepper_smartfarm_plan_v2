# Sensor Quality Rules Pseudocode

이 문서는 `sensor-ingestor`가 raw 수집값에 `quality_flag`를 부여하는 최소 규칙을 pseudocode 수준으로 고정한다. 목적은 학습/판단 입력에서 `good`, `partial`, `bad`를 일관되게 만드는 것이다.

## 1. 입력

- `now`
- `sensor_id`, `sensor_type`, `zone_id`
- `current_value`, `previous_value`
- `last_seen_at`, `last_good_at`
- `sample_interval_seconds`
- `quality_rule_set`
- `calibration_due`
- `readback_expected`, `readback_actual`
- `redundancy_group`의 다른 센서 상태

## 2. 우선순위

낮은 단계가 아니라 아래 순서대로 먼저 걸린 규칙이 우선한다.

1. `missing`
2. `communication_loss`
3. `stale`
4. `calibration_due`
5. `outlier`
6. `jump`
7. `flatline`
8. `readback_mismatch`
9. `good`

## 3. 센서 규칙 pseudocode

```text
if current_value is None:
    quality_flag = "bad"
    reason = "missing"
elif now - last_seen_at > bad_after_seconds:
    quality_flag = "bad"
    reason = "stale"
elif transport_status == "down":
    quality_flag = "bad"
    reason = "communication_loss"
elif calibration_due is True:
    quality_flag = "partial"
    reason = "calibration_due"
elif allowed_range exists and current_value outside allowed_range:
    quality_flag = "bad"
    reason = "outlier"
elif previous_value exists and abs(current_value - previous_value) / max(abs(previous_value), epsilon) * 100 > jump_threshold_pct:
    quality_flag = "partial"
    reason = "jump"
elif same_value_count * sample_interval_seconds >= flatline_window_seconds:
    quality_flag = "partial"
    reason = "flatline"
else:
    quality_flag = "good"
    reason = "within_expected_range"
```

## 4. 장치 readback 규칙

```text
if command_issued and now - command_issued_at > response_timeout_seconds and readback_actual != expected_state:
    quality_flag = "bad"
    reason = "readback_mismatch"
elif plc_fault is True or estop is True:
    quality_flag = "bad"
    reason = "device_fault"
else:
    quality_flag = "good"
```

## 5. Redundancy 그룹 병합

```text
if same redundancy_group has 2+ sensors:
    if all sensors == "bad":
        merged_quality = "bad"
    elif one sensor == "bad" and another sensor == "good":
        merged_quality = "partial"
    else:
        merged_quality = best available quality
```

## 6. AI 입력 게이트

```text
if must_have sensor merged_quality == "bad":
    automation_allowed = false
    overall_quality = "unsafe"
elif must_have sensor merged_quality == "partial":
    automation_allowed = false
    overall_quality = "degraded"
elif only should_have/optional sensors are partial or bad:
    automation_allowed = true
    overall_quality = "degraded"
else:
    automation_allowed = true
    overall_quality = "good"
```

## 7. 출력 연결

- `sensor-ingestor` 내부 출력: `good`, `partial`, `bad`
- `schemas/sensor_quality_schema.json` 보고 출력: `overall_quality`, `automation_allowed`, 세부 `sensor_flags`
- `farm_case` 후보와 학습 후보에는 기본적으로 `bad` 구간을 제외한다.
