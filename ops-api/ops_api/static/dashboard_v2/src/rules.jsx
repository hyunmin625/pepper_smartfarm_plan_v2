// rules.jsx — Automation rules list + 3-step wizard

function RuleRow({ r, onEdit, onToggle }) {
  // Optimistic toggle: flip locally first, then PATCH; on error revert.
  // Passing onToggle is optional so MOCK-only callers still render.
  const [enabled, setEnabled] = React.useState(r.enabled);
  const [pending, setPending] = React.useState(false);
  React.useEffect(() => { setEnabled(r.enabled); }, [r.enabled]);
  const modeChip = {
    shadow:   <span className="chip chip-mute"><Icon name="visibility"/> 섀도우</span>,
    approval: <span className="chip chip-warn"><Icon name="how_to_reg"/> 승인 필요</span>,
    execute:  <span className="chip chip-ok"><Icon name="bolt"/> 자동 실행</span>,
  }[r.mode];

  const handleToggle = async (e) => {
    const next = e.target.checked;
    if (!onToggle) { setEnabled(next); return; }
    setEnabled(next);
    setPending(true);
    try {
      await onToggle(r.rule_id || r.id, next);
    } catch (err) {
      setEnabled(!next); // revert on failure
      alert("규칙 상태 변경 실패: " + (err.message || err));
    } finally {
      setPending(false);
    }
  };

  return (
    <div className={`card p-4 ${enabled ? "" : "opacity-70"}`}>
      <div className="flex items-center gap-4">
        <label className="relative inline-flex items-center cursor-pointer shrink-0" onClick={(e) => e.stopPropagation()}>
          <input
            type="checkbox"
            checked={enabled}
            onChange={handleToggle}
            disabled={pending}
            className="sr-only peer"
          />
          <div className="w-11 h-6 rounded-full transition-colors" style={{ background: enabled ? "var(--brand)" : "#cfd6d1", opacity: pending ? 0.6 : 1 }}>
            <div className="w-5 h-5 rounded-full bg-white shadow-sm transition-transform" style={{ transform: `translate(${enabled ? 22 : 2}px, 2px)` }}></div>
          </div>
        </label>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <div className="font-display font-semibold" style={{ fontSize: 15 }}>{r.name}</div>
            {modeChip}
          </div>
          <div className="text-[13px] flex items-center gap-1.5 flex-wrap" style={{ color: "var(--ink-muted)" }}>
            <Icon name="sensors" style={{ fontSize: 14 }} />
            <span>{r.when}</span>
            <Icon name="arrow_right_alt" style={{ fontSize: 16 }} />
            <Icon name="settings_remote" style={{ fontSize: 14 }} />
            <span>{r.then}</span>
          </div>
        </div>

        <div className="text-right shrink-0">
          <div className="text-[12px] tnum" style={{ color: "var(--ink-soft)" }}>지난 24h</div>
          <div className="font-display tnum" style={{ fontSize: 18, fontWeight: 700 }}>{r.runs24h}<span className="text-[11px] font-normal" style={{ color: "var(--ink-soft)", marginLeft: 2 }}>회 실행</span></div>
          <div className="text-[11.5px]" style={{ color: "var(--ink-soft)" }}>마지막 {r.last}</div>
        </div>

        <button className="btn btn-ghost btn-sm" onClick={() => onEdit(r)}><Icon name="edit" style={{ fontSize: 18 }} /></button>
      </div>
    </div>
  );
}

function WizardStepper({ step, labels }) {
  return (
    <div className="flex items-center gap-2 mb-6">
      {labels.map((l, i) => {
        const n = i + 1;
        const active = step === n;
        const done = step > n;
        return (
          <React.Fragment key={i}>
            <div className="flex items-center gap-2">
              <div className="rounded-full flex items-center justify-center tnum" style={{
                width: 28, height: 28, fontWeight: 700, fontSize: 13,
                background: done ? "var(--brand)" : active ? "var(--brand-tint)" : "var(--surface-low)",
                color: done ? "#fff" : active ? "var(--brand-700)" : "var(--ink-soft)",
                border: `1px solid ${done ? "var(--brand)" : active ? "var(--brand-tint-2)" : "var(--line)"}`,
              }}>
                {done ? <Icon name="check" style={{ fontSize: 16 }} /> : n}
              </div>
              <div className={`text-[13.5px] ${active ? "font-semibold" : ""}`} style={{ color: active ? "var(--ink)" : done ? "var(--brand-700)" : "var(--ink-soft)" }}>{l}</div>
            </div>
            {i < labels.length - 1 && <div style={{ flex: 1, height: 1, background: done ? "var(--brand)" : "var(--line)" }}></div>}
          </React.Fragment>
        );
      })}
    </div>
  );
}

function RuleWizard({ open, onClose, editing }) {
  const [step, setStep] = React.useState(1);
  const [form, setForm] = React.useState({
    name: editing?.name || "",
    sensor: "air_humid", op: "gte", value: 85, duration: 10, zone: "all",
    device: "vent_roof", action: "close", actionValue: 20,
    mode: "approval", cooldown: 15,
  });
  React.useEffect(() => { if (open) setStep(1); }, [open]);

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const Summary = () => (
    <div className="card-ghost p-4" style={{ background: "var(--surface-low)" }}>
      <div className="text-[12px] font-semibold mb-2" style={{ color: "var(--ink-soft)", letterSpacing: ".04em", textTransform: "uppercase" }}>요약 미리보기</div>
      <div className="font-display" style={{ fontSize: 15, lineHeight: 1.5, textWrap: "pretty" }}>
        <b>{form.zone === "all" ? "모든 구역" : form.zone + "구역"}</b>에서{" "}
        <span className="chip chip-mute">{MOCK.sensors.find(s=>s.key===form.sensor)?.label}</span>이{" "}
        <span className="chip chip-mute">{MOCK.operators.find(o=>o.key===form.op)?.label} {form.value}</span>{" "}
        상태가 <b>{form.duration}분</b> 지속되면, <span className="chip chip-brand">{MOCK.devices.find(d=>d.key===form.device)?.label}</span>을(를){" "}
        <b>{form.action === "close" ? `${form.actionValue}%로 닫고` : form.action === "open" ? `${form.actionValue}%로 열고` : "작동하고"}</b>
        {" "}그 다음은 <span className="chip chip-warn"><Icon name="how_to_reg"/>{form.mode === "execute" ? "자동 실행" : form.mode === "approval" ? "승인 대기" : "섀도우 기록"}</span>입니다.
      </div>
    </div>
  );

  return (
    <Modal
      open={open} onClose={onClose} maxWidth={780}
      title={editing ? "규칙 편집" : "새 자동화 규칙 만들기"}
      subtitle="3단계로 간단하게. 개발자 도움 없이 직접 만들 수 있어요."
      footer={
        <>
          <button className="btn" onClick={onClose}>취소</button>
          {step > 1 && <button className="btn" onClick={() => setStep(step-1)}><Icon name="arrow_back" style={{ fontSize: 16 }}/> 이전</button>}
          {step < 3
            ? <button className="btn btn-primary" onClick={() => setStep(step+1)}>다음 <Icon name="arrow_forward" style={{ fontSize: 16 }}/></button>
            : <button className="btn btn-primary" onClick={onClose}><Icon name="check"/> 규칙 저장</button>}
        </>
      }
    >
      <WizardStepper step={step} labels={["언제", "무엇을", "안전"]} />

      {step === 1 && (
        <div className="space-y-4">
          <div>
            <label className="text-[13px] font-semibold">규칙 이름</label>
            <input className="mt-1.5 w-full px-3 py-2.5 rounded-lg text-[14px]" style={{ border: "1px solid var(--line)" }} placeholder="예: 습도 높을 때 제습팬 켜기" value={form.name} onChange={e=>set("name", e.target.value)} />
          </div>
          <div className="grid gap-3" style={{ gridTemplateColumns: "2fr 1fr 1fr" }}>
            <div>
              <label className="text-[13px] font-semibold">어떤 센서를?</label>
              <select className="mt-1.5 w-full px-3 py-2.5 rounded-lg text-[14px]" style={{ border: "1px solid var(--line)" }} value={form.sensor} onChange={e=>set("sensor", e.target.value)}>
                {MOCK.sensors.map(s => <option key={s.key} value={s.key}>{s.label}</option>)}
              </select>
            </div>
            <div>
              <label className="text-[13px] font-semibold">조건</label>
              <select className="mt-1.5 w-full px-3 py-2.5 rounded-lg text-[14px]" style={{ border: "1px solid var(--line)" }} value={form.op} onChange={e=>set("op", e.target.value)}>
                {MOCK.operators.map(o => <option key={o.key} value={o.key}>{o.label}</option>)}
              </select>
            </div>
            <div>
              <label className="text-[13px] font-semibold">값</label>
              <input type="number" className="mt-1.5 w-full px-3 py-2.5 rounded-lg text-[14px] tnum" style={{ border: "1px solid var(--line)" }} value={form.value} onChange={e=>set("value", +e.target.value)} />
            </div>
          </div>
          <div className="grid gap-3" style={{ gridTemplateColumns: "1fr 1fr" }}>
            <div>
              <label className="text-[13px] font-semibold">지속 시간 (분)</label>
              <input type="number" className="mt-1.5 w-full px-3 py-2.5 rounded-lg text-[14px] tnum" style={{ border: "1px solid var(--line)" }} value={form.duration} onChange={e=>set("duration", +e.target.value)} />
              <div className="text-[11.5px] mt-1" style={{ color: "var(--ink-soft)" }}>짧은 센서 튐을 거르기 위해 최소 1분 이상 권장</div>
            </div>
            <div>
              <label className="text-[13px] font-semibold">적용 구역</label>
              <select className="mt-1.5 w-full px-3 py-2.5 rounded-lg text-[14px]" style={{ border: "1px solid var(--line)" }} value={form.zone} onChange={e=>set("zone", e.target.value)}>
                <option value="all">모든 구역</option>
                <option value="A">A구역</option><option value="B">B구역</option><option value="C">C구역</option><option value="D">D구역</option>
              </select>
            </div>
          </div>
          <Summary />
        </div>
      )}

      {step === 2 && (
        <div className="space-y-4">
          <div>
            <label className="text-[13px] font-semibold">어떤 장치를 움직일까요?</label>
            <div className="mt-2 grid gap-2" style={{ gridTemplateColumns: "repeat(4, 1fr)" }}>
              {MOCK.devices.map(d => (
                <button key={d.key} onClick={() => set("device", d.key)}
                  className="card-ghost p-3 text-center"
                  style={{ cursor: "pointer", borderColor: form.device === d.key ? "var(--brand)" : "var(--line)", background: form.device === d.key ? "var(--brand-tint)" : "#fff", borderWidth: form.device === d.key ? 2 : 1 }}>
                  <Icon name={
                    d.key === "vent_roof" ? "unfold_less" :
                    d.key === "fan_dehum" ? "mode_fan" :
                    d.key === "irrigation" ? "water_drop" :
                    d.key === "grow_light" ? "wb_incandescent" :
                    d.key === "co2_inject" ? "co2" :
                    d.key === "heater" ? "local_fire_department" :
                    d.key === "cooler" ? "ac_unit" : "blinds"
                  } style={{ fontSize: 24, color: form.device === d.key ? "var(--brand)" : "var(--ink-muted)" }} />
                  <div className="text-[12.5px] mt-1" style={{ fontWeight: form.device === d.key ? 700 : 500 }}>{d.label}</div>
                </button>
              ))}
            </div>
          </div>
          <div className="grid gap-3" style={{ gridTemplateColumns: "1fr 1fr" }}>
            <div>
              <label className="text-[13px] font-semibold">동작</label>
              <select className="mt-1.5 w-full px-3 py-2.5 rounded-lg text-[14px]" style={{ border: "1px solid var(--line)" }} value={form.action} onChange={e=>set("action", e.target.value)}>
                <option value="close">닫기 (%)</option>
                <option value="open">열기 (%)</option>
                <option value="level">단계 설정</option>
                <option value="on">켜기</option>
                <option value="off">끄기</option>
              </select>
            </div>
            <div>
              <label className="text-[13px] font-semibold">값 ({form.action === "level" ? "단계" : "%"})</label>
              <input type="number" className="mt-1.5 w-full px-3 py-2.5 rounded-lg text-[14px] tnum" style={{ border: "1px solid var(--line)" }} value={form.actionValue} onChange={e=>set("actionValue", +e.target.value)} />
            </div>
          </div>
          <Summary />
        </div>
      )}

      {step === 3 && (
        <div className="space-y-4">
          <div>
            <label className="text-[13px] font-semibold">실행 방식</label>
            <div className="mt-2 space-y-2">
              {[
                { key: "shadow",   title: "섀도우 기록", desc: "실제로 실행하지 않고 기록만. 신규 규칙 안전 테스트에 권장.", icon: "visibility" },
                { key: "approval", title: "승인 대기",   desc: "조건 충족 시 관리자가 확인 후 승인. 가장 안전.", icon: "how_to_reg" },
                { key: "execute",  title: "자동 실행",   desc: "조건 충족 시 즉시 실행. 검증된 규칙만 사용하세요.", icon: "bolt" },
              ].map(o => (
                <label key={o.key} className="card-ghost p-3 flex items-start gap-3 cursor-pointer"
                  style={{ borderColor: form.mode === o.key ? "var(--brand)" : "var(--line)", background: form.mode === o.key ? "var(--brand-tint)" : "#fff", borderWidth: form.mode === o.key ? 2 : 1 }}>
                  <input type="radio" name="mode" checked={form.mode === o.key} onChange={() => set("mode", o.key)} className="mt-1" style={{ accentColor: "var(--brand)" }} />
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <Icon name={o.icon} style={{ fontSize: 18, color: "var(--brand)" }} />
                      <div className="font-semibold" style={{ fontSize: 14 }}>{o.title}</div>
                    </div>
                    <div className="text-[12.5px] mt-1" style={{ color: "var(--ink-muted)" }}>{o.desc}</div>
                  </div>
                </label>
              ))}
            </div>
          </div>

          <div>
            <label className="text-[13px] font-semibold">재발 방지 간격 (쿨다운)</label>
            <div className="mt-1.5 flex items-center gap-3">
              <input type="range" min="1" max="60" value={form.cooldown} onChange={e => set("cooldown", +e.target.value)} style={{ flex: 1, accentColor: "var(--brand)" }} />
              <div className="tnum font-display font-semibold" style={{ minWidth: 70, textAlign: "right" }}>{form.cooldown}<span style={{ fontWeight: 400, color: "var(--ink-soft)", fontSize: 13, marginLeft: 3 }}>분</span></div>
            </div>
            <div className="text-[11.5px] mt-1" style={{ color: "var(--ink-soft)" }}>규칙이 한 번 실행된 뒤 재실행까지 대기할 시간</div>
          </div>

          <div className="card-ghost p-3 flex items-start gap-3" style={{ background: "var(--info-tint)", borderColor: "#c4d6ef" }}>
            <Icon name="shield" style={{ color: "var(--info)", fontSize: 20, marginTop: 2 }} />
            <div className="text-[13px]" style={{ color: "#143f7a", lineHeight: 1.5 }}>
              이 규칙은 <b>3단 안전 파이프라인</b>을 거쳐 실행됩니다. AI 형식 검증 → 정책 검증(EC 상한 등 HSV 규칙) → 실행 게이트웨이의 장치 잠금 확인.
            </div>
          </div>

          <Summary />
        </div>
      )}
    </Modal>
  );
}

// Phase T-2b: human-readable label tables so server enums render
// naturally in the "when / then" sentence. Keep them lightweight and
// fall back to the raw key when unseen, since the server catalogue
// (21 sensors × 8 device types × 6 operators) can grow.
const RULES_SENSOR_LABELS = {
  air_temp_c: "기온 (°C)", rh_pct: "습도 (%)", vpd_kpa: "VPD (kPa)",
  co2_ppm: "CO₂ (ppm)", par_umol_m2_s: "광량 (μmol)",
  substrate_moisture_pct: "근권 수분 (%)", substrate_temp_c: "근권 온도 (°C)",
  substrate_ec_ds_m: "근권 EC (dS/m)",
  feed_ec_ds_m: "공급 EC (dS/m)", drain_ec_ds_m: "배액 EC (dS/m)",
  outside_rain_mm_10min: "외부 강우 (mm/10min)",
  outside_wind_ms: "외부 풍속 (m/s)",
  outside_temp_c: "외기 (°C)",
};
const RULES_OPERATOR_LABELS = {
  gt: ">", gte: "≥", lt: "<", lte: "≤", eq: "=",
  between: "범위", ne: "≠",
};
const RULES_DEVICE_LABELS = {
  roof_vent: "천장 개폐기", vent_window: "천장 개폐기",
  hvac_geothermal: "냉난방기", humidifier: "제습/가습기",
  fertigation_mixer: "양액 혼합기", irrigation_pump: "관수 밸브",
  shade_curtain: "차광막", fan_circulation: "순환팬",
  fan_dehum: "제습팬", co2_injector: "CO₂ 주입기",
  grow_light: "보광등", heater: "난방기",
};
const RULES_ACTION_LABELS = {
  adjust_vent: "개폐 조정", close_vent: "닫기", open_vent: "열기",
  set_level: "단계 설정", turn_on: "켜기", turn_off: "끄기",
};

function adaptServerRule(sr) {
  // Turn server serialize_rule() output → the shape RuleRow expects.
  const sensor = RULES_SENSOR_LABELS[sr.sensor_key] || sr.sensor_key || "";
  const op = RULES_OPERATOR_LABELS[sr.operator] || sr.operator || "";
  const threshold = sr.threshold_value != null
    ? sr.threshold_value
    : (sr.threshold_min != null && sr.threshold_max != null
        ? `${sr.threshold_min} ~ ${sr.threshold_max}`
        : "—");
  const device = RULES_DEVICE_LABELS[sr.target_device_type] || sr.target_device_type || "";
  const action = RULES_ACTION_LABELS[sr.target_action] || sr.target_action || "";
  return {
    id: sr.id,
    rule_id: sr.rule_id,
    name: sr.name || sr.rule_id,
    enabled: !!sr.enabled,
    when: `${sensor} ${op} ${threshold}`,
    then: `${device} ${action}`.trim(),
    mode: sr.runtime_mode_gate || "approval",
    runs24h: 0,   // Phase T-2c will aggregate /automation/triggers
    last: "—",
  };
}

async function fetchAutomationRules() {
  const res = await fetch("/automation/rules", { credentials: "same-origin" });
  if (!res.ok) throw new Error(`GET /automation/rules ${res.status}`);
  const body = await res.json();
  const rules = (body?.data?.rules) || [];
  return rules.map(adaptServerRule);
}

async function toggleAutomationRuleServer(ruleId, enabled) {
  const res = await fetch(`/automation/rules/${encodeURIComponent(ruleId)}/toggle`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    credentials: "same-origin",
    body: JSON.stringify({ enabled }),
  });
  if (!res.ok) {
    const msg = await res.text().catch(() => "");
    throw new Error(`PATCH toggle ${res.status} ${msg.slice(0, 120)}`);
  }
}

function RulesPage() {
  const [wizardOpen, setWizardOpen] = React.useState(false);
  const [editing, setEditing] = React.useState(null);
  const [rules, setRules] = React.useState(null);   // null = loading
  const [loadError, setLoadError] = React.useState(null);
  const [filter, setFilter] = React.useState("all");

  const load = React.useCallback(() => {
    setLoadError(null);
    fetchAutomationRules()
      .then(setRules)
      .catch(err => {
        setLoadError(err.message || String(err));
        setRules(MOCK.rules);  // fall back to mock so the page stays usable
      });
  }, []);
  React.useEffect(() => { load(); }, [load]);

  const handleToggle = async (ruleId, enabled) => {
    await toggleAutomationRuleServer(ruleId, enabled);
    setRules(prev => (prev || []).map(r => (r.rule_id === ruleId ? { ...r, enabled } : r)));
  };

  const all = rules || [];
  const counts = {
    all: all.length,
    on: all.filter(r => r.enabled).length,
    off: all.filter(r => !r.enabled).length,
    approval: all.filter(r => r.mode === "approval").length,
  };
  const filters = [
    { k: "all", label: "전체", n: counts.all },
    { k: "on", label: "켜짐", n: counts.on },
    { k: "off", label: "꺼짐", n: counts.off },
    { k: "approval", label: "승인 필요", n: counts.approval },
  ];
  const visible = all.filter(r => {
    if (filter === "on") return r.enabled;
    if (filter === "off") return !r.enabled;
    if (filter === "approval") return r.mode === "approval";
    return true;
  });

  return (
    <div className="p-6">
      <SectionHeader
        title="환경설정 · 자동화 규칙"
        sub="센서 값이 조건을 넘으면 장치를 자동으로 움직이도록 규칙을 만드세요."
        right={<button className="btn btn-primary" onClick={() => { setEditing(null); setWizardOpen(true); }}><Icon name="add"/> 새 규칙 만들기</button>}
      />

      {loadError && (
        <div className="card-ghost p-3 mb-4 flex items-start gap-3" style={{ background: "var(--warn-tint)", borderColor: "#f4d79a" }}>
          <Icon name="cloud_off" style={{ color: "var(--warn)", fontSize: 20 }} />
          <div className="flex-1 text-[13px]" style={{ color: "#8a5200" }}>
            규칙을 서버에서 불러오지 못했습니다 — 샘플 데이터를 표시합니다. ({loadError})
          </div>
          <button className="btn btn-sm" onClick={load}><Icon name="refresh" style={{ fontSize: 16 }}/> 다시 시도</button>
        </div>
      )}

      <div className="flex items-center gap-2 mb-4">
        {filters.map(f => (
          <button key={f.k} onClick={() => setFilter(f.k)}
            className={`btn btn-sm ${filter === f.k ? "" : "btn-ghost"}`}>
            {f.label} <span className="tnum ml-1" style={{ color: "var(--ink-soft)" }}>{f.n}</span>
          </button>
        ))}
      </div>

      {rules === null ? (
        <div className="card p-8 text-center text-[13px]" style={{ color: "var(--ink-soft)" }}>
          <Icon name="hourglass_empty" style={{ fontSize: 24 }} /> 규칙을 불러오는 중…
        </div>
      ) : visible.length === 0 ? (
        <div className="card p-8 text-center text-[13px]" style={{ color: "var(--ink-soft)" }}>
          {filter === "all" ? "등록된 규칙이 없습니다." : "이 필터에 해당하는 규칙이 없습니다."}
        </div>
      ) : (
        <div className="space-y-3 max-w-[960px]">
          {visible.map(r => (
            <RuleRow key={r.rule_id || r.id} r={r}
              onEdit={(r)=>{ setEditing(r); setWizardOpen(true); }}
              onToggle={loadError ? null : handleToggle} />
          ))}
        </div>
      )}

      <RuleWizard open={wizardOpen} onClose={() => setWizardOpen(false)} editing={editing} />
    </div>
  );
}

Object.assign(window, { RulesPage, RuleWizard, RuleRow, WizardStepper });
