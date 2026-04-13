#!/usr/bin/env python3
"""Validate ops-api request/response schema models."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from pydantic import ValidationError


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "ops-api"))

from ops_api.api_models import (  # noqa: E402
    ActorModel,
    ApiResponse,
    ErrorResponse,
    EvaluateZoneRequest,
    RobotTaskCreateRequest,
    RuntimeModeRequest,
    ShadowReviewRequest,
)


def _expect_validation_error(errors: list[str], name: str, fn) -> None:
    try:
        fn()
        errors.append(f"{name} should raise ValidationError")
    except ValidationError:
        return


def main() -> int:
    errors: list[str] = []

    valid_eval = EvaluateZoneRequest.model_validate(
        {
            "request_id": "schema-001",
            "zone_id": "gh-01-zone-a",
            "task_type": "action_recommendation",
            "mode": "shadow",
            "retrieval_limit": 6,
        }
    )
    if valid_eval.mode != "shadow" or valid_eval.retrieval_limit != 6:
        errors.append("EvaluateZoneRequest valid payload parsing mismatch")

    _expect_validation_error(
        errors,
        "EvaluateZoneRequest required fields",
        lambda: EvaluateZoneRequest.model_validate({"request_id": "schema-002", "zone_id": "gh-01-zone-a"}),
    )
    _expect_validation_error(
        errors,
        "RuntimeModeRequest invalid mode",
        lambda: RuntimeModeRequest.model_validate({"mode": "auto"}),
    )
    _expect_validation_error(
        errors,
        "ShadowReviewRequest invalid agreement_status",
        lambda: ShadowReviewRequest.model_validate(
            {"decision_id": 1, "actor_id": "operator-01", "agreement_status": "maybe"}
        ),
    )
    _expect_validation_error(
        errors,
        "RobotTaskCreateRequest invalid priority",
        lambda: RobotTaskCreateRequest.model_validate(
            {"zone_id": "gh-01-zone-a", "actor_id": "operator-01", "task_type": "inspect_crop", "reason": "check", "priority": "urgent"}
        ),
    )

    response = ApiResponse.model_validate(
        {
            "data": {"decision_id": 11},
            "meta": {"limit": 10},
            "actor": {"actor_id": "ops-service", "role": "service", "auth_mode": "header_token"},
        }
    )
    if response.actor is None or response.actor.role != "service":
        errors.append("ApiResponse actor parsing mismatch")

    error_response = ErrorResponse.model_validate(
        {
            "error": {
                "code": "http_404",
                "message": "decision not found",
            }
        }
    )
    if error_response.error.code != "http_404":
        errors.append("ErrorResponse parsing mismatch")

    api_schema = ApiResponse.model_json_schema()
    error_schema = ErrorResponse.model_json_schema()
    if not {"data", "meta"}.issubset(set(api_schema.get("properties", {}).keys())):
        errors.append("ApiResponse schema missing required properties")
    if "error" not in error_schema.get("properties", {}):
        errors.append("ErrorResponse schema missing error field")

    actor_schema = ActorModel.model_json_schema()
    if "actor_id" not in actor_schema.get("properties", {}):
        errors.append("ActorModel schema missing actor_id")

    print(
        json.dumps(
            {
                "errors": errors,
                "api_response_schema_fields": sorted(api_schema.get("properties", {}).keys()),
                "error_response_schema_fields": sorted(error_schema.get("properties", {}).keys()),
                "actor_schema_fields": sorted(actor_schema.get("properties", {}).keys()),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
