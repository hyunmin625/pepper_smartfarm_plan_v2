#!/usr/bin/env python3
"""Verify expected chunks are returned by local RAG search queries."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from search_rag_index import load_index, search


SMOKE_TESTS = [
    ("heat_stress temperature flowering", "pepper-climate-001"),
    ("overwet root_damage soil_moisture", "pepper-rootzone-001"),
    ("feed_ec drain_ec drain_rate", "pepper-hydroponic-001"),
    ("thrips anthracnose vision_symptom", "pepper-pest-001"),
    ("nursery transplanting temperature", "pepper-lifecycle-001"),
    ("decision_support approval audit", "pepper-agent-001"),
    ("화분 착과 야간 13도 18도", "pepper-flowering-pollen-001"),
    ("-20kPa 자동관수 석회결핍 일소 열과", "pepper-irrigation-tensiometer-001"),
    ("건고추 저장 함수율 18% 곰팡이 갈변", "pepper-dry-storage-001"),
    ("비가림 하우스 늦서리 첫서리 작부체계", "pepper-rain-shelter-calendar-001"),
    ("정식기 저온 13도 18도 재정식 동해", "pepper-lowtemp-regional-recovery-001"),
    ("장마 역병 탄저병 선수확 배수", "pepper-monsoon-prevention-001"),
    ("태풍 도복 낙과 지주 보강 배수", "pepper-typhoon-response-001"),
    ("우박 측지 유인 재정식 경제성", "pepper-hail-recovery-001"),
    ("풋고추 저장 7도 95 종자갈변", "pepper-green-storage-temperature-001"),
    ("풋고추 결로 천공필름 팬 30분 꼭지 무름", "pepper-green-packaging-condensation-001"),
    ("홍고추 저장 5도 10도 에틸렌 사과 토마토", "pepper-red-storage-ethylene-001"),
    ("건고추 7월 8월 함수율 18 훈증 UV 포장", "pepper-dry-storage-maintenance-001"),
    ("고춧가루 나일론 PE 산소흡수제 색도 매운맛", "pepper-powder-packaging-oxygen-001"),
    ("하우스 건조 35 40도 결로 제습 환기", "pepper-house-drying-hygiene-001"),
    ("반절 열풍건조 60도 건조시간 절반 캡산틴", "pepper-hotair-drying-split-001"),
    ("수확 후 큐어링 세척기 세척솔 곰팡이 오염", "pepper-postharvest-wash-hygiene-001"),
    ("플러그 상토 pH 6.0 6.5 EC 0.5 1.2 분형근", "pepper-plug-substrate-001"),
    ("가뭄 pF 2.0 2.5 점적관수 멀칭", "pepper-drought-001"),
    ("동해 -0.7 -1.85 10% 50% 재정식", "pepper-cold-injury-001"),
    ("30도 40도 일소 낙화 생장점", "pepper-heat-injury-001"),
    ("하위엽 황화 EC 높음 질소 과잉 칼리 과다", "pepper-nutrient-diagnosis-001"),
    ("석회결핍과 붕소결핍 함몰 흑갈색 생장점 정지", "pepper-calcium-boron-001"),
    ("석과 열과 일소과 화분관 신장 토양수분 급변", "pepper-physiological-disorders-001"),
    ("오전 광합성 70 80 커튼 골재 차광", "pepper-morning-light-001"),
    ("비가림 폭 7.0m 높이 3.5m 고깔형 천창", "pepper-rainshelter-structure-001"),
    ("비가림 990㎡ 질소 19.0kg 토양 EC 0.3", "pepper-rainshelter-fertilizer-ec-001"),
    ("정식 후 26일 저온 저일조 첫 수확 10일 지연", "pepper-rainshelter-lowlight-yield-001"),
    ("저온 저일조 캡사이신 디하이드로캡사이신 매운맛", "pepper-rainshelter-lowlight-pungency-001"),
    ("관비 분할공급 토양 EC 상승 속도 연작 비가림", "pepper-rainshelter-fertigation-salinity-001"),
    ("투명 멀칭 2 3도 흑색 멀칭 담수 세척 3회", "pepper-rainshelter-mulch-leaching-001"),
    ("부직포 보온 덮개 -4.9도 26 28% 증수", "pepper-rainshelter-frost-cover-001"),
    ("재식거리 100 120cm 20 35cm 밀식 약제 도달성", "pepper-rainshelter-density-001"),
    ("25 28도 pH 6.0 5.0 역병 기형과", "pepper-crop-env-thresholds-001"),
    ("반촉성 12월 하순 1월 중순 파종 2월 중순 정식 5월 중순 수확", "pepper-semiforcing-schedule-001"),
    ("촉성재배 8월 중하순 파종 다겹 보온커튼 46 연료 절감", "pepper-forcing-energy-saving-001"),
    ("코코피트 EC 0.5 이하 수분 40 50 정식 전 세척", "pepper-hydroponic-coir-prewash-001"),
    ("수분 37.4 41.7 EC 1.85 1.91 뿌리 갈변", "pepper-root-browning-overwet-profile-001"),
    ("붕소 포함 NK 칼슘 비료 신엽 황화 위로 굽는 잎 수정 불량", "pepper-boron-excess-diagnosis-001"),
    ("미끌애꽃노린재 50cm 총채벌레 피해 전 방사", "pepper-orius-release-timing-001"),
    ("15 10도 7일 광합성 효율 44 증산 57", "pepper-transplant-cold-duration-001"),
    ("33.9도 환풍기 불완전 코이어 수분 28.2 36.8 굽은과", "pepper-curved-fruit-heat-rootzone-001"),
    ("6월 파종 8월 하순 정식 10 12월 수확 50 50 코이어", "pepper-curved-fruit-cropping-shift-001"),
    ("미숙 퇴비 암모니아 가스 부정근", "pepper-establishment-ammonia-compost-001"),
    ("차광량 90 장마 낙화 웃자람", "pepper-flowerdrop-heavy-shading-001"),
    ("첫서리 외기 0 1.2 상부 2 3마디 낙화 검은 씨", "pepper-firstfrost-flowerdrop-001"),
    ("105일 노화묘 깊게 심기 지제부 새뿌리", "pepper-overaged-seedling-deep-001"),
    ("장마 전 초기 발병률 10% 장마 후 75%", "pepper-phytophthora-early-incidence-002"),
    ("호밀 혼화 고휴재배 역병 60%", "pepper-phytophthora-rye-highridge-002"),
    ("아인산 pH 5.5 6.5 7 14일 간격", "pepper-phytophthora-phosphite-002"),
    ("탄저병 99% 빗물 전파 4일 10일 잠복", "pepper-anthracnose-rain-spread-002"),
    ("비가림 탄저병 85 95 병든 과실 즉시 제거", "pepper-anthracnose-rainshelter-sanitation-002"),
    ("담배가루이 10마리 7일 간격 2회 그을음병", "pepper-whitefly-threshold-control-001"),
    ("지중해이리응애 80 120마리 1주 후 2 3마리", "pepper-whitefly-swirskii-release-001"),
    ("진딧물 5월 하순 CMV 보독 비래 살포 시작", "pepper-aphid-virus-spray-window-001"),
    ("진딧물 잎 뒷면 진하게 소량 살포 약해 저항성", "pepper-aphid-coverage-resistance-001"),
    ("성페로몬 10a 6개 80 20 온실 안팎", "pepper-budworm-pheromone-layout-001"),
    ("비가림 측지 30 50 70일 3회 제거", "pepper-rainshelter-side-shoot-001"),
    ("초장 2m 1.5m 적심", "pepper-rainshelter-topping-001"),
    ("비가림 관비 2주 1회 노동력", "pepper-rainshelter-fertigation-interval-001"),
    ("45 50일 홍고추 1 2일 음지 예건", "pepper-drying-precure-001"),
    ("천일건조 40 50cm 건조대", "pepper-sundry-rack-001"),
    ("균핵병 2 3일 습기 20도 무가온", "pepper-sclerotinia-infection-window-001"),
    ("균핵병 전면 멀칭 점적관수", "pepper-sclerotinia-mulch-drip-001"),
    ("시들음병 역병보다 느림 껍질 벗겨짐", "pepper-fusarium-symptom-diff-001"),
    ("시들음병 pH 6.5 7.0 석회 5년 윤작", "pepper-fusarium-rotation-liming-001"),
    ("잿빛곰팡이병 24도 6시간 포화습도", "pepper-graymold-infection-window-001"),
    ("흰별무늬병 흰색 중심 스프링클러 자제", "pepper-white-star-spot-sanitation-001"),
    ("흰비단병 비단 같은 균사 배추씨 균핵", "pepper-southern-blight-diagnosis-001"),
    ("무름병 물에 데친 것처럼 8월 담배나방", "pepper-soft-rot-wound-insect-prevention-001"),
    ("잎굴파리 30도 11 13일 15회 발생", "pepper-leafminer-temperature-generation-001"),
    ("잎굴파리 5 7일 3회 황색점착리본", "pepper-leafminer-three-spray-001"),
    ("뿌리혹선충 3 4주 전 훈증 5 7일 밀봉", "pepper-rootknot-fumigation-sealing-001"),
    ("농약 농도 2배 잔류량 2배 물량 배량", "pepper-pesticide-residue-concentration-001"),
    ("수화제 WG SC 유제 액제 혼용 순서", "pepper-pesticide-mix-order-001"),
]

FILTER_TESTS = [
    (
        "정식 야간 온도",
        {"growth_stage": "transplanting", "trust_level": "high"},
        "pepper-transplant-001",
    ),
    (
        "건고추 65℃ 건조",
        {"source_section": "열풍 건조"},
        "pepper-drying-001",
    ),
    (
        "역병 저항성",
        {"cultivar": "wongang_1"},
        "pepper-cultivar-phytophthora-resistance-001",
    ),
    (
        "야간 최저온 18도",
        {"cultivar": "cheongyang", "season": "winter"},
        "pepper-root-browning-winter-heating-001",
    ),
    (
        "표토 10cm 관수 비료 중단 TSWV 제거",
        {"region": "chungnam_boryeong", "season": "spring"},
        "pepper-establishment-ammonia-remediation-001",
    ),
    (
        "경반층 30 40cm 관수 5일 후 수분 25 30",
        {"cultivar": "cheongyang", "season": "winter", "greenhouse_type": "plastic_house"},
        "pepper-greenhouse-poor-drainage-overwet-001",
    ),
    (
        "1회 관수량 줄이고 15 20일 과실 수확 심토파쇄",
        {"cultivar": "cheongyang", "season": "winter", "greenhouse_type": "plastic_house"},
        "pepper-greenhouse-poor-drainage-remediation-001",
    ),
    (
        "새순 오그라듦 과습 약해형 장해",
        {"greenhouse_type": "nursery_house", "season": "spring"},
        "pepper-nursery-curling-overwet-001",
    ),
    (
        "해비치 5월 5일 이후 정식",
        {"cultivar": "haevichi", "season": "spring"},
        "pepper-cultivar-haevichi-cold-001",
    ),
    (
        "루비홍 ASTA color 146 생과중 20.4g",
        {"cultivar": "rubihong", "greenhouse_type": "rain_shelter"},
        "pepper-cultivar-rubihong-001",
    ),
    (
        "지중해이리응애 80 120마리",
        {"greenhouse_type": "plastic_house"},
        "pepper-whitefly-swirskii-release-001",
    ),
    (
        "5월 하순 CMV 보독 진딧물",
        {"season": "spring"},
        "pepper-aphid-virus-spray-window-001",
    ),
    (
        "2주 1회 관비",
        {"greenhouse_type": "rain_shelter"},
        "pepper-rainshelter-fertigation-interval-001",
    ),
    (
        "건조대 40 50cm",
        {"source_section": "천일건조"},
        "pepper-sundry-rack-001",
    ),
    (
        "겨울 시설 잔류농약",
        {"season": "winter"},
        "pepper-pesticide-residue-greenhouse-winter-001",
    ),
    (
        "균핵 2년 생존 20 22도",
        {"source_section": "균핵병"},
        "pepper-sclerotinia-pathogen-survival-001",
    ),
    (
        "시들음병 26 30도 산성 토양",
        {"source_section": "시들음병"},
        "pepper-fusarium-acidic-sandy-soil-001",
    ),
    (
        "흰비단병 흰 균사 77.5 89.4",
        {"source_section": "흰비단병"},
        "pepper-southern-blight-early-fungicide-001",
    ),
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", default="artifacts/rag_index/pepper_expert_index.json")
    parser.add_argument("--limit", type=int, default=3)
    args = parser.parse_args()

    index = load_index(Path(args.index))
    failures = []
    for query, expected_id in SMOKE_TESTS:
        results = search(index, query, args.limit)
        result_ids = [item["id"] for item in results]
        if expected_id not in result_ids:
            failures.append((query, expected_id, result_ids))
            print(f"FAIL {query!r}: expected {expected_id}, got {result_ids}")
        else:
            print(f"PASS {query!r}: found {expected_id}")

    for query, filters, expected_id in FILTER_TESTS:
        results = search(index, query, args.limit, filters=filters)
        result_ids = [item["id"] for item in results]
        if expected_id not in result_ids:
            failures.append((query, expected_id, result_ids))
            print(f"FAIL {query!r} filters={filters}: expected {expected_id}, got {result_ids}")
        else:
            print(f"PASS {query!r} filters={filters}: found {expected_id}")

    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
