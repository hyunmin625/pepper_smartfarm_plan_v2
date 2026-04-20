// policies.jsx + robot.jsx merged page components

function PolicyRow({ p }) {
  return (
    <div className={`card p-4 rail-${p.state}`}>
      <div className="flex items-center gap-4">
        <label className="relative inline-flex items-center cursor-pointer shrink-0">
          <input type="checkbox" defaultChecked={p.enabled} className="sr-only peer" />
          <div className="w-11 h-6 rounded-full" style={{ background: p.enabled ? "var(--brand)" : "#cfd6d1" }}>
            <div className="w-5 h-5 rounded-full bg-white shadow-sm" style={{ transform: `translate(${p.enabled ? 22 : 2}px, 2px)` }}></div>
          </div>
        </label>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-0.5">
            <div className="font-display font-semibold" style={{ fontSize: 14.5 }}>{p.name}</div>
            <span className="chip chip-mute" title="내부 식별자" style={{ fontFamily: "ui-monospace, monospace", fontSize: 11 }}>{p.id}</span>
          </div>
          <div className="text-[12.5px]" style={{ color: "var(--ink-muted)" }}>{p.desc}</div>
        </div>
        <div className="text-right shrink-0">
          <div className="text-[11.5px]" style={{ color: "var(--ink-soft)" }}>지난 24h 발동</div>
          <div className="font-display tnum" style={{ fontSize: 18, fontWeight: 700 }}>{p.triggers24h}<span className="text-[11px] font-normal ml-0.5" style={{ color: "var(--ink-soft)" }}>회</span></div>
        </div>
      </div>
    </div>
  );
}

function PoliciesPage() {
  return (
    <div className="p-6">
      <SectionHeader title="정책 · 이벤트" sub="안전 규칙의 현재 상태와 최근 트리거 이력." />
      <div className="grid gap-5 resp-2col" style={{ gridTemplateColumns: "1.4fr 1fr" }}>
        <div>
          <div className="text-[12px] font-semibold mb-2" style={{ color: "var(--ink-soft)", letterSpacing: ".06em", textTransform: "uppercase" }}>활성 안전 규칙</div>
          <div className="space-y-3">
            {MOCK.policies.map(p => <PolicyRow key={p.id} p={p} />)}
          </div>
        </div>
        <div>
          <div className="text-[12px] font-semibold mb-2" style={{ color: "var(--ink-soft)", letterSpacing: ".06em", textTransform: "uppercase" }}>최근 이벤트</div>
          <div className="card px-4">
            {MOCK.policyEvents.map((e, i) => (
              <div key={i} className="flex items-start gap-3 py-3" style={{ borderBottom: i < MOCK.policyEvents.length - 1 ? "1px solid var(--line-soft)" : "none" }}>
                <div className="rounded-full flex items-center justify-center shrink-0" style={{ width: 30, height: 30, background: e.state === "warn" ? "var(--warn-tint)" : "var(--ok-tint)" }}>
                  <Icon name="shield" style={{ fontSize: 16, color: e.state === "warn" ? "var(--warn)" : "var(--ok)" }} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-[13.5px]" style={{ fontWeight: 600 }}>{e.title}</div>
                  <div className="text-[11.5px] mt-0.5 flex items-center gap-2" style={{ color: "var(--ink-soft)" }}>
                    <span>{e.t}</span> · <span className="chip chip-mute" style={{ fontSize: 10.5, padding: "1px 6px" }}>{e.policy}</span> · <span>{e.zone}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// ——— Robot ———
function RobotPage() {
  const r = MOCK.robotTasks;
  return (
    <div className="p-6">
      <SectionHeader title="로봇" sub="현재 실행 중인 작업과 대기 큐, 오늘 완료 이력." right={
        <div className="flex items-center gap-2">
          <button className="btn btn-sm"><Icon name="pause"/> 일시정지</button>
          <button className="btn btn-sm btn-primary"><Icon name="add"/> 작업 추가</button>
        </div>
      } />

      <div className="grid gap-5 resp-2col" style={{ gridTemplateColumns: "1.3fr 1fr" }}>
        {/* Now running */}
        <div className="card p-5 rail-brand">
          <div className="flex items-center gap-2 mb-2">
            <span className="chip chip-brand"><Icon name="sync"/> 실행 중</span>
            <span className="text-[11.5px] font-mono" style={{ color: "var(--ink-soft)" }}>{r.now.id}</span>
          </div>
          <div className="font-display font-semibold" style={{ fontSize: 18 }}>{r.now.name} · {r.now.zone}</div>
          <div className="text-[13px] mt-0.5" style={{ color: "var(--ink-muted)" }}>로봇 {r.now.robot} · {r.now.started} 시작 · 예상 남은 시간 {r.now.eta}</div>

          <div className="mt-4">
            <div className="flex items-center justify-between text-[12.5px] mb-1" style={{ color: "var(--ink-muted)" }}>
              <span>진행률</span>
              <span className="tnum font-semibold">{Math.round(r.now.progress * 100)}%</span>
            </div>
            <div style={{ height: 10, borderRadius: 999, background: "var(--line-soft)", overflow: "hidden" }}>
              <div style={{ width: `${r.now.progress * 100}%`, height: "100%", background: "linear-gradient(90deg, var(--brand-500), var(--brand))" }}></div>
            </div>
          </div>

          <div className="hairline mt-4 pt-3 flex items-center gap-2">
            <button className="btn btn-sm"><Icon name="pause"/> 일시정지</button>
            <button className="btn btn-sm btn-danger"><Icon name="stop_circle"/> 중단</button>
            <button className="btn btn-ghost btn-sm ml-auto">작업 상세 <Icon name="arrow_forward" style={{fontSize:16}}/></button>
          </div>
        </div>

        {/* Queue */}
        <div>
          <div className="text-[12px] font-semibold mb-2" style={{ color: "var(--ink-soft)", letterSpacing: ".06em", textTransform: "uppercase" }}>대기 큐 · {r.queue.length}건</div>
          <div className="card" style={{ padding: 2 }}>
            {r.queue.map((q, i) => (
              <div key={q.id} className="flex items-center gap-3 px-3 py-3" style={{ borderBottom: i < r.queue.length - 1 ? "1px solid var(--line-soft)" : "none" }}>
                <div className="rounded-md flex items-center justify-center" style={{ width: 28, height: 28, background: "var(--surface-low)", color: "var(--ink-muted)", fontWeight: 700, fontSize: 13 }}>{i+1}</div>
                <div className="flex-1 min-w-0">
                  <div className="text-[13.5px] font-semibold">{q.name} · {q.zone}</div>
                  <div className="text-[11.5px] flex items-center gap-2" style={{ color: "var(--ink-soft)" }}>
                    <span>예상 {q.eta}</span> · <span className={`chip ${q.priority === "높음" ? "chip-warn" : q.priority === "낮음" ? "chip-mute" : "chip-info"}`} style={{ fontSize: 10.5, padding: "1px 6px" }}>{q.priority}</span>
                  </div>
                </div>
                <button className="btn btn-ghost btn-sm"><Icon name="drag_indicator" style={{ fontSize: 18 }} /></button>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="mt-5">
        <SectionHeader title="오늘 완료 이력" right={<button className="btn btn-ghost btn-sm">전체 이력</button>} />
        <div className="card px-4">
          {r.done.map((d, i) => (
            <div key={d.id} className="flex items-center gap-3 py-3" style={{ borderBottom: i < r.done.length - 1 ? "1px solid var(--line-soft)" : "none" }}>
              <div className="rounded-full flex items-center justify-center shrink-0" style={{ width: 30, height: 30, background: "var(--ok-tint)" }}>
                <Icon name="check_circle" style={{ color: "var(--ok)", fontSize: 18 }} />
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-[13.5px]"><b>{d.name}</b> · {d.zone}</div>
                <div className="text-[11.5px]" style={{ color: "var(--ink-soft)" }}>{d.ended} · {d.result}</div>
              </div>
              <span className="text-[11px] font-mono" style={{ color: "var(--ink-soft)" }}>{d.id}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { PoliciesPage, PolicyRow, RobotPage });
