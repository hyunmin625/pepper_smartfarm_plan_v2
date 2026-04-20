// chat.jsx — AI Assistant

function GroundingChips({ g }) {
  if (!g) return null;
  return (
    <div className="flex flex-wrap gap-1.5 mt-2">
      {g.zones?.map(z => <span key={z} className="chip chip-brand"><Icon name="place"/>{z}</span>)}
      {g.metrics?.map(m => <span key={m} className="chip chip-info"><Icon name="monitoring"/>{m}</span>)}
      {g.policies?.map(p => <span key={p} className="chip chip-mute"><Icon name="shield"/>{p}</span>)}
    </div>
  );
}

function MessageBubble({ m }) {
  if (m.who === "user") {
    return (
      <div className="flex justify-end mb-4">
        <div style={{ background: "var(--brand)", color: "#fff", padding: "10px 14px", borderRadius: "16px 16px 4px 16px", maxWidth: "72%", fontSize: 14, lineHeight: 1.5 }}>
          {m.text}
          <div className="text-[11px] mt-1" style={{ color: "rgba(255,255,255,.7)" }}>{m.t}</div>
        </div>
      </div>
    );
  }
  // AI
  // Render **bold** simple
  const parts = m.text.split(/(\*\*[^*]+\*\*)/g);
  return (
    <div className="flex items-start gap-3 mb-4">
      <div className="rounded-lg shrink-0 flex items-center justify-center" style={{ width: 36, height: 36, background: "var(--brand-tint)" }}>
        <Icon name="smart_toy" style={{ color: "var(--brand)", fontSize: 20 }} />
      </div>
      <div className="min-w-0" style={{ maxWidth: "80%" }}>
        <div className="flex items-center gap-2 mb-1">
          <span className="chip chip-brand">적고추 전문 AI</span>
          <span className="text-[11px]" style={{ color: "var(--ink-soft)" }}>{m.t}</span>
        </div>
        <div style={{ background: "#fff", border: "1px solid var(--line)", padding: "12px 14px", borderRadius: "4px 16px 16px 16px", fontSize: 14, lineHeight: 1.6, textWrap: "pretty" }}>
          {parts.map((p, i) =>
            p.startsWith("**") ? <b key={i}>{p.slice(2, -2)}</b> : <span key={i}>{p}</span>
          )}
        </div>
        <GroundingChips g={m.grounds} />
      </div>
    </div>
  );
}

function ChatPage({ devViewUnlocked }) {
  const [messages, setMessages] = React.useState(MOCK.chatHistory);
  const [input, setInput] = React.useState("");
  const [typing, setTyping] = React.useState(false);
  const scrollRef = React.useRef(null);

  React.useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages, typing]);

  const send = (txt) => {
    if (!txt.trim()) return;
    const now = new Date();
    const t = `${now.getHours()}:${String(now.getMinutes()).padStart(2,"0")}`;
    setMessages(m => [...m, { who: "user", text: txt, t }]);
    setInput("");
    setTyping(true);
    setTimeout(() => {
      setMessages(m => [...m, {
        who: "ai",
        text: "질문을 확인했어요. 관련된 구역 데이터와 안전 규칙을 함께 살펴보고 답변드릴게요. (데모 응답)",
        grounds: { zones: ["A구역", "B구역"], metrics: ["기온", "습도"], policies: ["HSV-03"] },
        t,
      }]);
      setTyping(false);
    }, 1100);
  };

  const lastAi = [...messages].reverse().find(m => m.who === "ai");

  return (
    <div className="p-6" style={{ height: "calc(100vh - 64px)" }}>
      <div className="grid gap-5 h-full resp-2col" style={{ gridTemplateColumns: "1fr 320px" }}>
        {/* Chat column */}
        <div className="card flex flex-col min-h-0" style={{ background: "var(--surface-low)" }}>
          <div className="px-5 py-3 flex items-center justify-between" style={{ borderBottom: "1px solid var(--line)", background: "#fff", borderRadius: "14px 14px 0 0" }}>
            <div className="flex items-center gap-2">
              <span className="chip chip-brand"><Icon name="smart_toy"/> 적고추 전문 AI</span>
              <span className="text-[12.5px]" style={{ color: "var(--ink-soft)" }}>적고추 온실 제2동에 대해 연결됨</span>
            </div>
            <button className="btn btn-ghost btn-sm"><Icon name="refresh" style={{ fontSize: 16 }} /> 새 대화</button>
          </div>

          <div ref={scrollRef} className="flex-1 overflow-y-auto scroll-clean px-5 py-4 min-h-0">
            {messages.map((m, i) => <MessageBubble key={i} m={m} />)}
            {typing && (
              <div className="flex items-center gap-3 mb-4">
                <div className="rounded-lg shrink-0 flex items-center justify-center" style={{ width: 36, height: 36, background: "var(--brand-tint)" }}>
                  <Icon name="smart_toy" style={{ color: "var(--brand)", fontSize: 20 }} />
                </div>
                <div style={{ background: "#fff", border: "1px solid var(--line)", padding: "12px 14px", borderRadius: 16, display: "flex", gap: 5 }}>
                  <span className="pulse" style={{ width:6, height:6, borderRadius:999, background:"var(--brand)" }}></span>
                  <span className="pulse" style={{ width:6, height:6, borderRadius:999, background:"var(--brand)", animationDelay:".2s" }}></span>
                  <span className="pulse" style={{ width:6, height:6, borderRadius:999, background:"var(--brand)", animationDelay:".4s" }}></span>
                </div>
              </div>
            )}
          </div>

          <div className="px-5 pt-2 pb-3" style={{ background: "#fff", borderTop: "1px solid var(--line)", borderRadius: "0 0 14px 14px" }}>
            <div className="flex flex-wrap gap-1.5 mb-2">
              {MOCK.quickPrompts.map((q, i) => (
                <button key={i} className="btn btn-sm btn-ghost" style={{ background: "var(--surface-low)", border: "1px solid var(--line)" }} onClick={() => send(q)}>{q}</button>
              ))}
            </div>
            <div className="flex items-center gap-2">
              <input
                className="flex-1 px-4 py-3 rounded-xl text-[14px]"
                style={{ border: "1px solid var(--line)", background: "#fff" }}
                placeholder="온실 상태나 규칙에 대해 물어보세요…"
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => { if (e.key === "Enter") send(input); }}
              />
              <button className="btn btn-primary" onClick={() => send(input)}><Icon name="send"/> 보내기</button>
            </div>
            <div className="text-[11px] mt-1.5" style={{ color: "var(--ink-soft)" }}>AI 답변은 참고용입니다. 중요한 결정은 결정·승인 화면에서 검토해주세요.</div>
          </div>
        </div>

        {/* Grounding panel */}
        <aside className="card p-4 overflow-y-auto scroll-clean min-h-0" style={{ height: "100%" }}>
          <div className="text-[12px] font-semibold mb-2" style={{ color: "var(--ink-soft)", letterSpacing: ".06em", textTransform: "uppercase" }}>지금 AI가 본 데이터</div>
          <div className="text-[13px] mb-4" style={{ color: "var(--ink-muted)", lineHeight: 1.5 }}>마지막 답변은 다음 정보를 참조했습니다.</div>

          <div className="mb-4">
            <div className="text-[12px] font-semibold mb-1.5" style={{ color: "var(--ink-soft)" }}>구역</div>
            <div className="flex flex-wrap gap-1.5">
              {lastAi?.grounds?.zones?.map(z => <span key={z} className="chip chip-brand"><Icon name="place"/>{z}</span>)}
            </div>
          </div>
          <div className="mb-4">
            <div className="text-[12px] font-semibold mb-1.5" style={{ color: "var(--ink-soft)" }}>지표</div>
            <div className="flex flex-wrap gap-1.5">
              {lastAi?.grounds?.metrics?.map(m => <span key={m} className="chip chip-info"><Icon name="monitoring"/>{m}</span>)}
            </div>
          </div>
          <div className="mb-4">
            <div className="text-[12px] font-semibold mb-1.5" style={{ color: "var(--ink-soft)" }}>참조한 안전 규칙</div>
            <div className="flex flex-wrap gap-1.5">
              {lastAi?.grounds?.policies?.map(p => (
                <span key={p} className="chip chip-mute"><Icon name="shield"/>{p}</span>
              ))}
            </div>
          </div>

          <div className="card-ghost p-3 mt-5" style={{ background: "var(--brand-tint)", borderColor: "var(--brand-tint-2)" }}>
            <div className="flex items-start gap-2">
              <Icon name="verified" style={{ color: "var(--brand)", fontSize: 18, marginTop: 1 }} />
              <div>
                <div className="font-display font-semibold" style={{ fontSize: 13, color: "var(--brand-700)" }}>적고추 전문 파인튜닝 AI</div>
                <div className="text-[12px] mt-0.5" style={{ color: "var(--brand-700)", lineHeight: 1.5 }}>한국 적고추 재배 생리·환경 데이터로 파인튜닝된 전용 모델입니다.</div>
              </div>
            </div>
          </div>

          {devViewUnlocked && (
            <details className="mt-4" style={{ borderTop: "1px dashed var(--line)", paddingTop: 12 }}>
              <summary className="text-[12px] font-semibold flex items-center gap-1.5" style={{ color: "var(--ink-muted)" }}>
                <Icon name="code" style={{ fontSize: 14 }} /> Grounding Inspector (개발자)
              </summary>
              <pre className="json mt-2" style={{ fontSize: 11 }}>{JSON.stringify({
                model_label: "pepper-ds_v11",
                provider: "openai:ft",
                prompt_version: "sft_v10",
                chat_system_prompt_id: "sp_pepper_v3",
                grounding_keys: ["zones.A", "metrics.humidity_pct", "policies.HSV-04"],
                retriever: "openai",
              }, null, 2)}</pre>
            </details>
          )}
        </aside>
      </div>
    </div>
  );
}

Object.assign(window, { ChatPage, GroundingChips });
