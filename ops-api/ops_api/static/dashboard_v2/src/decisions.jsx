// decisions.jsx — Decisions/Approval queue + detail modal

function ConfidenceBar({ value }) {
  const pct = Math.round(value * 100);
  return (
    <div className="flex items-center gap-2">
      <div style={{ width: 120, height: 6, borderRadius: 999, background: "var(--line-soft)", overflow: "hidden" }}>
        <div style={{ width: `${pct}%`, height: "100%", background: "linear-gradient(90deg, var(--brand-500), var(--brand-700))" }}></div>
      </div>
      <div className="text-[12.5px] tnum" style={{ color: "var(--ink-muted)", fontWeight: 600 }}>{pct}%</div>
    </div>
  );
}

function DecisionCard({ d, onOpen, onApprove, onReject, style }) {
  // style: "list" | "stack" | "split"
  return (
    <div className={`card p-5 rail-${d.risk === "ok" ? "ok" : "warn"}`}>
      <div className="flex items-start gap-4">
        <div className="rounded-lg flex items-center justify-center shrink-0" style={{ width: 44, height: 44, background: "var(--brand-tint)" }}>
          <Icon name="smart_toy" style={{ color: "var(--brand)", fontSize: 22 }} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1.5 flex-wrap">
            <span className="chip chip-brand"><Icon name="place" />{d.zone}</span>
            <StatusChip state={d.risk === "ok" ? "ok" : "warn"}>{d.risk === "ok" ? "안전" : "주의"}</StatusChip>
            <span className="chip chip-mute"><Icon name="schedule" /> {d.createdAt}</span>
            <span className="chip chip-mute" title="AI 신뢰도">
              <Icon name="insights" /> 신뢰도 {Math.round(d.confidence*100)}%
            </span>
          </div>
          <div className="font-display" style={{ fontSize: 17, fontWeight: 600, lineHeight: 1.4, textWrap: "pretty" }}>{d.summary}</div>

          <div className="mt-3">
            <div className="text-[12px] font-semibold mb-1.5" style={{ color: "var(--ink-soft)", letterSpacing: ".04em", textTransform: "uppercase" }}>근거</div>
            <div className="flex flex-wrap gap-1.5">
              {d.reasons.map((r,i) => <span key={i} className="chip chip-mute" style={{ maxWidth: "100%" }}>{r}</span>)}
            </div>
          </div>

          <div className="mt-4" style={{ background: "var(--surface-low)", border: "1px solid var(--line)", borderRadius: 10, padding: 12 }}>
            <div className="text-[12px] font-semibold mb-1.5" style={{ color: "var(--ink-soft)", letterSpacing: ".04em", textTransform: "uppercase" }}>승인 시 실행</div>
            <div className="space-y-1.5">
              {d.plan.map((p,i) => (
                <div key={i} className="flex items-center gap-2 text-[13.5px]">
                  <Icon name="arrow_right" style={{ fontSize: 18, color: "var(--brand)" }} />
                  <span style={{ fontWeight: 600 }}>{p.device}</span>
                  <span style={{ color: "var(--ink-muted)" }}>— {p.action}</span>
                  <span className="ml-auto text-[12px]" style={{ color: "var(--ink-soft)" }}>{p.etc}</span>
                </div>
              ))}
            </div>
            <div className="hairline mt-2.5 pt-2.5 text-[12.5px] flex items-center gap-1.5" style={{ color: "var(--ink-muted)" }}>
              <Icon name="auto_graph" style={{ fontSize: 14 }} />
              예상 결과: {d.impact}
            </div>
          </div>
        </div>
      </div>

      <div className="hairline mt-4 pt-3 flex items-center gap-2">
        <button className="btn btn-primary" onClick={() => onApprove(d)}>
          <Icon name="check" style={{ fontSize: 18 }} /> 승인하고 실행
        </button>
        <button className="btn btn-danger" onClick={() => onReject(d)}>
          <Icon name="close" style={{ fontSize: 18 }} /> 거절
        </button>
        <button className="btn btn-ghost ml-auto" onClick={() => onOpen(d)}>
          상세 근거 보기 <Icon name="arrow_forward" style={{ fontSize: 16 }} />
        </button>
      </div>
    </div>
  );
}

function DecisionDetailModal({ d, open, onClose, onApprove, onReject, devViewUnlocked }) {
  if (!d) return null;
  const devJson = devViewUnlocked ? {
    decision_id: d.id === "dec-3" ? 3 : 4,
    request_id: "automation-42-" + d.id,
    runtime_mode_gate: "approval",
    parsed_output_json: {
      action: d.plan.map(p => ({ target: p.device, op: p.action })),
      reasons: d.reasons,
    },
    validator_reason_codes_json: ["HSV-01:pass", "HSV-03:pass", "HSV-07:pass"],
    model_family: "ds_v11", prompt_version: "sft_v10",
    confidence: d.confidence,
  } : null;

  return (
    <Modal
      open={open} onClose={onClose} maxWidth={760}
      title="AI 권고 상세"
      subtitle={d.zone + " · " + d.createdAt}
      footer={
        <>
          <button className="btn" onClick={onClose}>취소</button>
          <button className="btn btn-danger" onClick={() => { onReject(d); onClose(); }}><Icon name="close"/> 거절</button>
          <button className="btn btn-primary" onClick={() => { onApprove(d); onClose(); }}><Icon name="check"/> 승인하고 실행</button>
        </>
      }
      devJson={devJson}
    >
      <div className="card-ghost p-4 rail-warn mb-4">
        <div className="flex items-center gap-2 mb-1">
          <Icon name="smart_toy" style={{ color: "var(--brand)" }} />
          <span className="chip chip-brand">적고추 전문 AI</span>
        </div>
        <div className="font-display" style={{ fontSize: 18, fontWeight: 600, lineHeight: 1.4 }}>{d.summary}</div>
      </div>

      <div className="grid gap-4" style={{ gridTemplateColumns: "1fr 1fr" }}>
        <div>
          <div className="text-[12px] font-semibold mb-2" style={{ color: "var(--ink-soft)", letterSpacing: ".04em", textTransform: "uppercase" }}>왜 이 권고인가</div>
          <ul className="space-y-2">
            {d.reasons.map((r,i) => (
              <li key={i} className="flex items-start gap-2 text-[13.5px]" style={{ lineHeight: 1.5 }}>
                <Icon name="fiber_manual_record" style={{ fontSize: 8, color: "var(--brand)", marginTop: 8 }} />
                <span>{r}</span>
              </li>
            ))}
          </ul>
        </div>
        <div>
          <div className="text-[12px] font-semibold mb-2" style={{ color: "var(--ink-soft)", letterSpacing: ".04em", textTransform: "uppercase" }}>안전 검증</div>
          <div className="space-y-2">
            {[
              { lbl: "AI 응답 형식", state: "ok" },
              { lbl: "정책 규칙 (EC/온도/풍속)", state: "ok" },
              { lbl: "장치 잠금 및 쿨다운", state: "ok" },
              { lbl: "실행 권한", state: "ok" },
            ].map((c,i) => (
              <div key={i} className="flex items-center gap-2 text-[13px]" style={{ padding: "6px 10px", background: "var(--ok-tint)", border: "1px solid #bde5d2", borderRadius: 8 }}>
                <Icon name="verified" style={{ color: "var(--ok)", fontSize: 16 }} /> {c.lbl}
              </div>
            ))}
          </div>
          <div className="mt-3 text-[12px]" style={{ color: "var(--ink-muted)" }}>AI 신뢰도</div>
          <div className="mt-1"><ConfidenceBar value={d.confidence} /></div>
        </div>
      </div>

      <div className="hairline mt-5 pt-4">
        <div className="text-[12px] font-semibold mb-2" style={{ color: "var(--ink-soft)", letterSpacing: ".04em", textTransform: "uppercase" }}>실행 계획</div>
        <div className="card-ghost" style={{ padding: 2 }}>
          {d.plan.map((p, i) => (
            <div key={i} className="flex items-center gap-3 px-3 py-2.5" style={{ borderBottom: i < d.plan.length-1 ? "1px solid var(--line-soft)" : "none" }}>
              <div className="rounded-md flex items-center justify-center" style={{ width: 32, height: 32, background: "var(--brand-tint)" }}>
                <Icon name="settings_remote" style={{ color: "var(--brand)", fontSize: 18 }} />
              </div>
              <div className="flex-1">
                <div className="text-[13.5px]" style={{ fontWeight: 600 }}>{p.device}</div>
                <div className="text-[12.5px]" style={{ color: "var(--ink-muted)" }}>{p.action}</div>
              </div>
              <div className="text-[12px]" style={{ color: "var(--ink-soft)" }}>{p.etc}</div>
            </div>
          ))}
        </div>
        <div className="mt-2 text-[13px] flex items-center gap-1.5" style={{ color: "var(--ink-muted)" }}>
          <Icon name="auto_graph" style={{ fontSize: 16 }} />
          예상 결과: <span style={{ color: "var(--ink)" }}>{d.impact}</span>
        </div>
      </div>
    </Modal>
  );
}

function DecisionsPage({ devViewUnlocked, tweaks }) {
  const [openItem, setOpenItem] = React.useState(null);
  const [toast, setToast] = React.useState(null);
  const [filter, setFilter] = React.useState("all");
  const items = MOCK.pending;

  const handle = (action) => (d) => {
    setToast({ kind: action, zone: d.zone });
    setTimeout(() => setToast(null), 2800);
  };

  return (
    <div className="p-6">
      <SectionHeader
        title="결정 · 승인"
        sub="AI가 권고한 조치. 한 문장으로 요약하고, 근거와 실행 계획을 함께 보여줍니다."
        right={
          <div className="flex items-center gap-2">
            {[["all","전체",items.length],["warn","주의",1],["ok","안전",1],["mine","내 담당",2]].map(([k,l,n]) => (
              <button key={k} onClick={()=>setFilter(k)} className={`btn btn-sm ${filter===k ? "" : "btn-ghost"}`}>
                {l} <span className="tnum" style={{ color: "var(--ink-soft)", marginLeft: 4 }}>{n}</span>
              </button>
            ))}
          </div>
        }
      />

      <div className="space-y-3 max-w-[920px]">
        {items.map(d => (
          <DecisionCard key={d.id} d={d}
            onOpen={setOpenItem}
            onApprove={handle("approved")}
            onReject={handle("rejected")}
            style={tweaks.approvalStyle}
          />
        ))}

        <div className="card p-6 text-center" style={{ borderStyle: "dashed", background: "transparent" }}>
          <Icon name="task_alt" style={{ fontSize: 28, color: "var(--ok)" }} />
          <div className="font-display font-semibold mt-2" style={{ fontSize: 15 }}>모든 권고를 확인했습니다</div>
          <div className="text-[13px]" style={{ color: "var(--ink-soft)" }}>새 권고가 도착하면 여기에 표시됩니다.</div>
        </div>
      </div>

      <DecisionDetailModal
        d={openItem} open={!!openItem} onClose={() => setOpenItem(null)}
        onApprove={handle("approved")} onReject={handle("rejected")}
        devViewUnlocked={devViewUnlocked}
      />

      {toast && (
        <div style={{ position: "fixed", bottom: 24, left: "50%", transform: "translateX(-50%)", zIndex: 60 }}>
          <div className="sheet" style={{ background: toast.kind === "approved" ? "var(--ok)" : "var(--ink)", color: "#fff", padding: "12px 18px", borderRadius: 10, boxShadow: "var(--shadow-float)", display: "flex", alignItems: "center", gap: 10, fontSize: 14, fontWeight: 600 }}>
            <Icon name={toast.kind === "approved" ? "check_circle" : "cancel"} />
            {toast.zone} 권고를 {toast.kind === "approved" ? "승인했습니다. 실행 중…" : "거절했습니다."}
          </div>
        </div>
      )}
    </div>
  );
}

Object.assign(window, { DecisionsPage, DecisionCard, DecisionDetailModal, ConfidenceBar });
