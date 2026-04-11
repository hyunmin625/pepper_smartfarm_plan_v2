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
