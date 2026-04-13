from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy import desc, select
from sqlalchemy.orm import Session, sessionmaker

from .api_models import ApprovalRequest, EvaluateZoneRequest, RuntimeModeRequest
from .bootstrap import configure_repo_paths
from .config import Settings, load_settings
from .database import build_session_factory, init_db
from .models import ApprovalRecord, DecisionRecord, DeviceCommandRecord
from .planner import ActionDispatchPlanner
from .runtime_mode import load_runtime_mode, save_runtime_mode

configure_repo_paths()

from execution_gateway.contracts import ControlOverrideRequest, DeviceCommandRequest  # noqa: E402
from execution_gateway.dispatch import ExecutionDispatcher  # noqa: E402
from llm_orchestrator import LLMOrchestratorService, ModelConfig, OrchestratorRequest  # noqa: E402
from state_estimator import build_zone_state_payload, estimate_zone_state  # noqa: E402


@dataclass
class AppServices:
    settings: Settings
    session_factory: sessionmaker[Session]
    orchestrator: LLMOrchestratorService
    dispatcher: ExecutionDispatcher
    planner: ActionDispatchPlanner


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or load_settings()
    session_factory = build_session_factory(resolved_settings.database_url)
    init_db(session_factory)
    current_mode = load_runtime_mode(resolved_settings.runtime_mode_path)
    save_runtime_mode(
        resolved_settings.runtime_mode_path,
        mode=current_mode.mode,
        actor_id=current_mode.actor_id,
        reason=current_mode.reason,
    )
    services = AppServices(
        settings=resolved_settings,
        session_factory=session_factory,
        orchestrator=LLMOrchestratorService.from_model_config(
            ModelConfig(
                provider=resolved_settings.llm_provider,
                model_id=resolved_settings.llm_model_id,
                timeout_seconds=resolved_settings.llm_timeout_seconds,
                max_retries=resolved_settings.llm_max_retries,
            )
        ),
        dispatcher=ExecutionDispatcher.default(adapter_kind="mock"),
        planner=ActionDispatchPlanner(),
    )

    app = FastAPI(title="Pepper Smartfarm Ops API", version="0.1.0")
    app.state.services = services

    def get_services():
        return app.state.services

    def get_session(services=Depends(get_services)):
        session = services.session_factory()
        try:
            yield session
        finally:
            session.close()

    @app.get("/health")
    def health(services=Depends(get_services)) -> dict[str, Any]:
        mode_state = load_runtime_mode(services.settings.runtime_mode_path)
        return {"status": "ok", "runtime_mode": mode_state.as_dict()}

    @app.get("/runtime/mode")
    def get_runtime_mode(services=Depends(get_services)) -> dict[str, Any]:
        return load_runtime_mode(services.settings.runtime_mode_path).as_dict()

    @app.post("/runtime/mode")
    def set_runtime_mode(
        payload: RuntimeModeRequest,
        services=Depends(get_services),
    ) -> dict[str, Any]:
        state = save_runtime_mode(
            services.settings.runtime_mode_path,
            mode=payload.mode,
            actor_id=payload.actor_id,
            reason=payload.reason,
        )
        return {"runtime_mode": state.as_dict()}

    @app.post("/decisions/evaluate-zone")
    def evaluate_zone(
        payload: EvaluateZoneRequest,
        session: Session = Depends(get_session),
        services=Depends(get_services),
    ) -> dict[str, Any]:
        mode_state = load_runtime_mode(services.settings.runtime_mode_path)
        effective_mode = payload.mode or mode_state.mode
        snapshot = {
            "zone_id": payload.zone_id,
            "growth_stage": payload.growth_stage,
            "current_state": payload.current_state,
            "history": payload.history,
            "sensor_quality": payload.sensor_quality,
            "device_status": payload.device_status,
            "weather_context": payload.weather_context,
            "constraints": payload.constraints,
        }
        state_estimate = estimate_zone_state(snapshot)
        zone_state = build_zone_state_payload(snapshot)
        zone_state["active_constraints"] = payload.constraints
        zone_state["current_state"]["summary"] = (
            zone_state["current_state"].get("summary")
            or f"{state_estimate.risk_level} risk; recommended {', '.join(state_estimate.recommended_action_types)}"
        )
        zone_state["state_estimate"] = state_estimate.as_dict()

        result = services.orchestrator.evaluate(
            OrchestratorRequest(
                request_id=payload.request_id,
                zone_id=payload.zone_id,
                task_type=payload.task_type,
                zone_state=zone_state,
                prompt_version=payload.prompt_version,
                retrieval_limit=payload.retrieval_limit,
                mode=effective_mode,
            )
        )

        decision = DecisionRecord(
            request_id=payload.request_id,
            zone_id=payload.zone_id,
            task_type=payload.task_type,
            runtime_mode=effective_mode,
            status="evaluated",
            model_id=result.model_id,
            prompt_version=payload.prompt_version,
            raw_output_json=json.dumps({"raw_text": result.raw_text}, ensure_ascii=False),
            parsed_output_json=json.dumps(result.parsed_output, ensure_ascii=False),
            validated_output_json=json.dumps(result.validated_output, ensure_ascii=False),
            zone_state_json=json.dumps(zone_state, ensure_ascii=False),
            citations_json=json.dumps(result.validated_output.get("citations", []), ensure_ascii=False),
            retrieval_context_json=json.dumps([chunk.as_prompt_dict() for chunk in result.retrieval_chunks], ensure_ascii=False),
            audit_path=result.audit_path,
            validator_reason_codes_json=json.dumps(result.validator_reason_codes, ensure_ascii=False),
        )
        session.add(decision)
        session.commit()
        session.refresh(decision)
        return {
            "decision_id": decision.id,
            "runtime_mode": effective_mode,
            "state_estimate": state_estimate.as_dict(),
            "validated_output": result.validated_output,
            "citations": result.validated_output.get("citations", []),
            "retrieval_context": [chunk.as_prompt_dict() for chunk in result.retrieval_chunks],
            "validator_reason_codes": result.validator_reason_codes,
        }

    @app.get("/decisions")
    def list_decisions(
        limit: int = 30,
        session: Session = Depends(get_session),
    ) -> dict[str, Any]:
        rows = session.execute(select(DecisionRecord).order_by(desc(DecisionRecord.id)).limit(limit)).scalars().all()
        return {
            "items": [
                {
                    "decision_id": row.id,
                    "request_id": row.request_id,
                    "zone_id": row.zone_id,
                    "task_type": row.task_type,
                    "runtime_mode": row.runtime_mode,
                    "status": row.status,
                    "model_id": row.model_id,
                    "validated_output": json.loads(row.validated_output_json),
                    "citations": json.loads(row.citations_json),
                    "created_at": row.created_at.isoformat(),
                }
                for row in rows
            ]
        }

    @app.get("/zones/{zone_id}/state")
    def get_zone_state(zone_id: str, session: Session = Depends(get_session)) -> dict[str, Any]:
        row = session.execute(
            select(DecisionRecord)
            .where(DecisionRecord.zone_id == zone_id)
            .order_by(desc(DecisionRecord.id))
            .limit(1)
        ).scalar_one_or_none()
        if row is None:
            raise HTTPException(status_code=404, detail="zone state not found")
        return {
            "zone_id": zone_id,
            "zone_state": json.loads(row.zone_state_json),
            "decision_id": row.id,
            "updated_at": row.updated_at.isoformat(),
        }

    @app.get("/actions/history")
    def action_history(limit: int = 50, session: Session = Depends(get_session)) -> dict[str, Any]:
        rows = session.execute(select(DeviceCommandRecord).order_by(desc(DeviceCommandRecord.id)).limit(limit)).scalars().all()
        return {
            "items": [
                {
                    "id": row.id,
                    "decision_id": row.decision_id,
                    "command_kind": row.command_kind,
                    "target_id": row.target_id,
                    "action_type": row.action_type,
                    "status": row.status,
                    "payload": json.loads(row.payload_json),
                    "adapter_result": json.loads(row.adapter_result_json),
                    "created_at": row.created_at.isoformat(),
                }
                for row in rows
            ]
        }

    @app.post("/actions/approve")
    def approve_action(
        payload: ApprovalRequest,
        session: Session = Depends(get_session),
        services=Depends(get_services),
    ) -> dict[str, Any]:
        runtime_mode = load_runtime_mode(services.settings.runtime_mode_path)
        if runtime_mode.mode != "approval":
            raise HTTPException(status_code=409, detail="runtime mode must be approval to execute actions")
        decision = session.get(DecisionRecord, payload.decision_id)
        if decision is None:
            raise HTTPException(status_code=404, detail="decision not found")
        if decision.status == "rejected":
            raise HTTPException(status_code=409, detail="decision already rejected")

        approval = ApprovalRecord(
            decision_id=decision.id,
            actor_id=payload.actor_id,
            approval_status="approved",
            reason=payload.reason,
            approval_payload_json=json.dumps(payload.model_dump(), ensure_ascii=False),
        )
        session.add(approval)

        validated_output = json.loads(decision.validated_output_json)
        plans = services.planner.plan(
            decision_id=decision.id,
            request_id=decision.request_id,
            zone_id=decision.zone_id,
            validated_output=validated_output,
            actor_id=payload.actor_id,
        )
        dispatch_results: list[dict[str, Any]] = []
        for plan in plans:
            if plan.kind == "device_command":
                dispatch_result = services.dispatcher.dispatch_device_command(DeviceCommandRequest.from_dict(plan.payload)).as_dict()
            elif plan.kind == "control_override":
                dispatch_result = services.dispatcher.dispatch_control_override(ControlOverrideRequest.from_dict(plan.payload)).as_dict()
            else:
                dispatch_result = {"status": "logged_only", "allow_dispatch": False, "reasons": ["non_dispatchable_action"]}
            dispatch_results.append(dispatch_result)
            session.add(
                DeviceCommandRecord(
                    decision_id=decision.id,
                    command_kind=plan.kind,
                    target_id=plan.target_id,
                    action_type=plan.action_type,
                    status=str(dispatch_result.get("status") or "logged_only"),
                    payload_json=json.dumps(plan.payload, ensure_ascii=False),
                    adapter_result_json=json.dumps(dispatch_result, ensure_ascii=False),
                )
            )

        decision.status = "approved_executed"
        session.commit()
        return {
            "decision_id": decision.id,
            "approval_status": "approved",
            "dispatch_results": dispatch_results,
        }

    @app.post("/actions/reject")
    def reject_action(
        payload: ApprovalRequest,
        session: Session = Depends(get_session),
    ) -> dict[str, Any]:
        decision = session.get(DecisionRecord, payload.decision_id)
        if decision is None:
            raise HTTPException(status_code=404, detail="decision not found")
        approval = ApprovalRecord(
            decision_id=decision.id,
            actor_id=payload.actor_id,
            approval_status="rejected",
            reason=payload.reason,
            approval_payload_json=json.dumps(payload.model_dump(), ensure_ascii=False),
        )
        session.add(approval)
        decision.status = "rejected"
        session.commit()
        return {"decision_id": decision.id, "approval_status": "rejected"}

    @app.get("/dashboard", response_class=HTMLResponse)
    def dashboard() -> str:
        return _dashboard_html()

    return app


def _dashboard_html() -> str:
    return """<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <title>Pepper Smartfarm Approval Dashboard</title>
  <style>
    :root { --bg:#f4f1e8; --ink:#1d2a1f; --card:#fffdf7; --line:#d8d1c3; --accent:#456b4f; --warn:#8a4a2f; }
    body { margin:0; font-family: 'Noto Sans KR', sans-serif; background:linear-gradient(180deg,#f0eadf 0%,#f7f4ec 100%); color:var(--ink); }
    header { padding:24px 28px; border-bottom:1px solid var(--line); background:rgba(255,255,255,0.6); backdrop-filter: blur(8px); }
    main { display:grid; grid-template-columns: 420px 1fr; gap:20px; padding:20px; }
    .card { background:var(--card); border:1px solid var(--line); border-radius:18px; padding:18px; box-shadow:0 8px 30px rgba(44,60,47,0.06); }
    h1,h2,h3 { margin:0 0 12px; }
    label { display:block; font-size:13px; margin:8px 0 4px; color:#4a5b4d; }
    input, select, textarea, button { width:100%; box-sizing:border-box; border-radius:12px; border:1px solid var(--line); padding:10px 12px; font:inherit; }
    textarea { min-height:120px; resize:vertical; }
    button { background:var(--accent); color:white; cursor:pointer; border:none; margin-top:10px; }
    button.secondary { background:#657d6a; }
    .mode { display:inline-block; padding:6px 10px; border-radius:999px; background:#e3ecd9; color:#28523a; font-weight:700; }
    .decision { padding:14px; border:1px solid var(--line); border-radius:14px; margin-bottom:12px; }
    .decision pre { white-space:pre-wrap; word-break:break-word; background:#f6f3ea; padding:10px; border-radius:10px; }
    .meta { font-size:12px; color:#5b685e; margin-bottom:8px; }
    .row { display:flex; gap:8px; }
    .row > * { flex:1; }
  </style>
</head>
<body>
  <header>
    <h1>Approval Dashboard</h1>
    <div>현재 모드: <span id="modeBadge" class="mode">loading</span></div>
  </header>
  <main>
    <section class="card">
      <h2>Decision Request</h2>
      <label>Zone</label>
      <input id="zoneId" value="gh-01-zone-a" />
      <label>Task</label>
      <select id="taskType">
        <option value="state_judgement">state_judgement</option>
        <option value="action_recommendation">action_recommendation</option>
        <option value="failure_response">failure_response</option>
        <option value="robot_task_prioritization">robot_task_prioritization</option>
        <option value="forbidden_action">forbidden_action</option>
      </select>
      <label>Growth Stage</label>
      <input id="growthStage" value="fruiting" />
      <label>Current State JSON</label>
      <textarea id="currentState">{ "air_temp_c": 31.5, "rh_pct": 88.0, "substrate_moisture_pct": 24.0, "ripe_fruit_count": 72 }</textarea>
      <label>Sensor Quality JSON</label>
      <textarea id="sensorQuality">{ "overall": "good" }</textarea>
      <div class="row">
        <button onclick="submitDecision()">Evaluate</button>
        <button class="secondary" onclick="toggleMode()">Toggle Mode</button>
      </div>
    </section>
    <section class="card">
      <h2>Real-time Decisions</h2>
      <div id="decisionList"></div>
    </section>
  </main>
  <script>
    async function loadMode() {
      const res = await fetch('/runtime/mode');
      const data = await res.json();
      document.getElementById('modeBadge').textContent = data.mode;
    }
    async function toggleMode() {
      const res = await fetch('/runtime/mode');
      const current = await res.json();
      const next = current.mode === 'shadow' ? 'approval' : 'shadow';
      await fetch('/runtime/mode', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ mode: next, actor_id:'dashboard', reason:'dashboard toggle'}) });
      await loadMode();
    }
    async function submitDecision() {
      const body = {
        request_id: 'dashboard-' + Date.now(),
        zone_id: document.getElementById('zoneId').value,
        task_type: document.getElementById('taskType').value,
        growth_stage: document.getElementById('growthStage').value,
        current_state: JSON.parse(document.getElementById('currentState').value),
        sensor_quality: JSON.parse(document.getElementById('sensorQuality').value),
      };
      await fetch('/decisions/evaluate-zone', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body) });
      await refreshDecisions();
    }
    async function approve(decisionId) {
      await fetch('/actions/approve', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ decision_id: decisionId, actor_id:'dashboard-operator', reason:'dashboard approve'}) });
      await refreshDecisions();
    }
    async function reject(decisionId) {
      await fetch('/actions/reject', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ decision_id: decisionId, actor_id:'dashboard-operator', reason:'dashboard reject'}) });
      await refreshDecisions();
    }
    async function refreshDecisions() {
      const res = await fetch('/decisions?limit=20');
      const data = await res.json();
      const html = data.items.map(item => `
        <div class="decision">
          <div class="meta">#${item.decision_id} · ${item.zone_id} · ${item.task_type} · ${item.status}</div>
          <pre>${JSON.stringify(item.validated_output, null, 2)}</pre>
          <div class="meta">citations: ${item.citations.map(c => c.chunk_id).join(', ') || 'none'}</div>
          <div class="row">
            <button onclick="approve(${item.decision_id})">승인</button>
            <button class="secondary" onclick="reject(${item.decision_id})">거절</button>
          </div>
        </div>
      `).join('');
      document.getElementById('decisionList').innerHTML = html || '<div>아직 decision이 없습니다.</div>';
      await loadMode();
    }
    refreshDecisions();
    setInterval(refreshDecisions, 5000);
  </script>
</body>
</html>"""
