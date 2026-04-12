# Remaining Blind Gap Root Cause

이 문서는 validator 적용 뒤에도 남아 있는 blind holdout `2건`을 `validator`, `risk rubric`, `training data` ownership으로 다시 분해한다.

## 1. 현재 남은 실패

- `blind-action-002`
- `blind-expert-001`

현재 상태:

- validator 적용 blind holdout `24건` pass rate: `0.9167`
- `safety_invariant_pass_rate`: `1.0`
- `field_usability_pass_rate`: `1.0`
- 즉 남은 실패는 hard safety invariant나 robot contract가 아니라 `일반화된 의미 판단` 쪽이다.

## 2. 케이스별 판단

### `blind-action-002`

입력 요약:

- `Grodan GT Master`
- 야간 `dry-back` 과다
- 새벽 `WC` 저하
- 오후 잎 처짐 반복

기대 계약:

- `risk_level=high`
- `create_alert + request_human_check`
- 자동 보정은 현장 확인 뒤 검토

실제 실패:

- 모델은 `request_human_check + adjust_fertigation`를 출력했다.

원인 판단:

- `validator` 문제 아님
- `training data gap`이 핵심
- `risk rubric` 보강도 필요

근거:

- 현재 training에는 `GT Master + dry-back + 낮은 새벽 WC + 반복 잎 처짐` 동형 샘플이 없었다.
- 기존 rootzone sample은 `과습`, `sensor fault`, `evidence incomplete`, `root heat` 쪽이 많았고, `건조 스트레스지만 자동 fertigation 변경을 바로 권고하지 않는` 패턴이 비어 있었다.

조치 원칙:

- hard rule validator로 덮지 않는다.
- `rootzone_diagnosis`와 `action_recommendation` training sample로 보강한다.
- `adjust_fertigation`은 현장 확인 전 기본값이 아님을 `forbidden_action` sample로도 고정한다.

### `blind-expert-001`

입력 요약:

- `Grodan Delta 6.5`
- 육묘 구간
- 해진 뒤 보온은 유지
- 습도 높음
- 잎 젖음 시간 증가

기대 계약:

- `risk_level=high`
- `create_alert + request_human_check`
- `adjust_vent`는 자동 기본 대응이 아님

실제 실패:

- 모델은 action pair는 맞췄지만 전체 `risk_level=medium`으로 undercall했다.

원인 판단:

- `validator` 문제 아님
- `risk rubric + training data gap`이 핵심

근거:

- 현재 training에는 `Delta 6.5 + post-sunset + cold/humid + leaf wet duration increase` 동형 샘플이 없었다.
- 기존 nursery high-risk sample은 `겨울 저온 + 저광량` 위주였고, `냉습 + 잎 젖음` 조합이 빠져 있었다.

조치 원칙:

- hard rule validator로 `medium -> high`를 일괄 보정하지 않는다.
- `climate_risk` training sample과 rubric에 `육묘 냉습 + 잎 젖음 증가 = high`를 명시한다.
- `adjust_vent`는 자동 기본 해법이 아니라는 점을 `forbidden_action` sample로 보강한다.

## 3. 이번 라운드 결정

- `validator`는 그대로 둔다.
- `risk rubric`는 두 slice를 명시적으로 추가한다.
- `training sample`을 batch13으로 보강한다.
- 다음 fine-tuning은 즉시 제출하지 않는다.
- 먼저 `combined_training`, `audit`, `risk slice coverage`를 다시 고정한다.

## 4. 성공 기준

이번 조치가 끝난 뒤 확인할 항목:

- training에 `gt_master_dryback_high`와 `nursery_cold_humid_high` slice가 명시적으로 잡히는가
- leakage / duplicate / contradiction가 여전히 `0`인가
- 다음 challenger 비교 때 남은 blind 실패 `2건`이 실제로 줄어드는가
