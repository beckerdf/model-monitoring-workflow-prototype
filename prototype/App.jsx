import React, { useState } from "react";
import {
  Mail, Inbox, Users, ClipboardList, Activity, CheckCircle2, Clock,
  AlertTriangle, ArrowRight, Zap, UserCog, Bell, RotateCcw
} from "lucide-react";

const RED = "#E60012";
const BLACK = "#1A1A1A";
const NOW = new Date(2026, 6, 20); // July 20, 2026 — fixed "today" for the demo

function fmt(d) {
  if (!d) return "—";
  const dt = typeof d === "string" ? new Date(d) : d;
  return dt.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}
function daysBetween(a, b) {
  return Math.round((new Date(b) - new Date(a)) / 86400000);
}
function isUnavailable(person) {
  if (!person.unavailStart || !person.unavailEnd) return false;
  return NOW >= new Date(person.unavailStart) && NOW <= new Date(person.unavailEnd);
}

const initialQueue = [
  { id: "ds1", last: "Nguyen", first: "Priya", email: "priya.nguyen@tfs.com", active: true, unavailStart: "", unavailEnd: "", lastAssigned: "2026-06-02" },
  { id: "ds2", last: "Klein", first: "Marcus", email: "marcus.klein@tfs.com", active: true, unavailStart: "", unavailEnd: "", lastAssigned: "2026-05-18" },
  { id: "ds3", last: "Patel", first: "Rohan", email: "rohan.patel@tfs.com", active: true, unavailStart: "2026-07-14", unavailEnd: "2026-07-25", lastAssigned: "2026-06-20" },
  { id: "ds4", last: "O'Brien", first: "Sean", email: "sean.obrien@tfs.com", active: true, unavailStart: "", unavailEnd: "", lastAssigned: "2026-06-28" },
  { id: "ds5", last: "Ahmed", first: "Sara", email: "sara.ahmed@tfs.com", active: true, unavailStart: "", unavailEnd: "", lastAssigned: "2026-07-05" },
  { id: "ds6", last: "Torres", first: "Diego", email: "diego.torres@tfs.com", active: false, unavailStart: "", unavailEnd: "", lastAssigned: "2026-04-11" },
];

const initialReviews = [
  { id: "r1", modelNo: "MFS-0981", modelName: "Loss Forecast Overlay", dsId: "ds2", start: "2026-06-01", due: "2026-07-10", status: "Not Started", completed: null, assignedBy: "Auto" },
  { id: "r2", modelNo: "MFS-1010", modelName: "Delinquency Trigger Model", dsId: "ds5", start: "2026-06-15", due: "2026-07-25", status: "In Progress", completed: null, assignedBy: "Auto" },
];

const pendingEmailsSeed = [
  { id: "e1", modelNo: "MFS-1032", modelName: "Return Rate Model 2.1 – MFS", start: "2026-06-22", due: "2026-08-10" },
  { id: "e2", modelNo: "MFS-1045", modelName: "Recovery Income", start: "2026-07-06", due: "2026-08-24" },
  { id: "e3", modelNo: "MFS-1046", modelName: "Service Ops Credit Loss", start: "2026-07-06", due: "2026-08-24" },
];

const STEPS = ["Parsing email", "Checking rotation queue", "Assigning reviewer", "Logging & notifying"];

export default function Prototype() {
  const [tab, setTab] = useState("inbox");
  const [queue, setQueue] = useState(initialQueue);
  const [reviews, setReviews] = useState(initialReviews);
  const [pending, setPending] = useState(pendingEmailsSeed);
  const [log, setLog] = useState([
    { id: 0, text: "System initialized. 2 open reviews carried over from prior cycle.", icon: "info" },
  ]);
  const [processing, setProcessing] = useState(false);
  const [stepIdx, setStepIdx] = useState(-1);

  const nextLogId = () => log.length ? Math.max(...log.map(l => l.id)) + 1 : 1;

  const pushLog = (entries) => {
    setLog(prev => {
      let id = prev.length ? Math.max(...prev.map(l => l.id)) + 1 : 1;
      const withIds = entries.map(e => ({ ...e, id: id++ }));
      return [...withIds, ...prev];
    });
  };

  const eligiblePerson = (excludeId) => {
    const pool = queue.filter(p => p.active && !isUnavailable(p) && p.id !== excludeId);
    if (!pool.length) return null;
    return [...pool].sort((a, b) => new Date(a.lastAssigned) - new Date(b.lastAssigned))[0];
  };

  const wait = (ms) => new Promise(r => setTimeout(r, ms));

  const processNext = async () => {
    if (!pending.length || processing) return;
    setProcessing(true);
    const email = pending[0];

    for (let i = 0; i < STEPS.length; i++) {
      setStepIdx(i);
      await wait(550);
    }

    const person = eligiblePerson();
    if (!person) {
      pushLog([{ text: `No eligible data scientist available for ${email.modelName}. Manager alerted.`, icon: "warn" }]);
      setProcessing(false);
      setStepIdx(-1);
      return;
    }

    const newReview = {
      id: "r" + Date.now(),
      modelNo: email.modelNo,
      modelName: email.modelName,
      dsId: person.id,
      start: email.start,
      due: email.due,
      status: "Not Started",
      completed: null,
      assignedBy: "Auto",
    };

    setReviews(prev => [newReview, ...prev]);
    setQueue(prev => prev.map(p => p.id === person.id ? { ...p, lastAssigned: fmtISO(NOW) } : p));
    setPending(prev => prev.slice(1));
    pushLog([
      { text: `Parsed ${email.modelNo} — ${email.modelName} (due ${fmt(email.due)}).`, icon: "info" },
      { text: `Auto-assigned to ${person.first} ${person.last} (oldest last-assigned date in rotation).`, icon: "assign" },
      { text: `Notification sent to ${person.first} ${person.last}, CC National Manager and DB.`, icon: "mail" },
    ]);
    setProcessing(false);
    setStepIdx(-1);
  };

  const fmtISO = (d) => d.toISOString().slice(0, 10);

  const updateStatus = (id, status) => {
    setReviews(prev => prev.map(r => {
      if (r.id !== id) return r;
      const completed = status === "Complete" ? fmtISO(NOW) : null;
      return { ...r, status, completed };
    }));
    const r = reviews.find(x => x.id === id);
    const person = queue.find(p => p.id === r?.dsId);
    if (status === "Complete") {
      pushLog([{ text: `${person?.first} ${person?.last} marked ${r?.modelName} complete. Governance notified.`, icon: "done" }]);
    } else {
      pushLog([{ text: `${r?.modelName} status updated to "${status}".`, icon: "info" }]);
    }
  };

  const reassign = (reviewId, newDsId) => {
    const r = reviews.find(x => x.id === reviewId);
    const oldPerson = queue.find(p => p.id === r.dsId);
    const newPerson = queue.find(p => p.id === newDsId);
    setReviews(prev => prev.map(x => x.id === reviewId ? { ...x, dsId: newDsId, assignedBy: "Manager Override" } : x));
    setQueue(prev => prev.map(p => p.id === newDsId ? { ...p, lastAssigned: fmtISO(NOW) } : p));
    pushLog([{ text: `Manager override: ${r.modelName} reassigned from ${oldPerson?.first} ${oldPerson?.last} to ${newPerson?.first} ${newPerson?.last}.`, icon: "override" }]);
  };

  const toggleActive = (id) => {
    setQueue(prev => prev.map(p => p.id === id ? { ...p, active: !p.active } : p));
  };
  const setUnavail = (id, field, val) => {
    setQueue(prev => prev.map(p => p.id === id ? { ...p, [field]: val } : p));
  };

  const overdueCount = reviews.filter(r => r.status !== "Complete" && new Date(r.due) < NOW).length;
  const dueSoonCount = reviews.filter(r => r.status !== "Complete" && new Date(r.due) >= NOW && daysBetween(NOW, r.due) <= 7).length;
  const inProgressCount = reviews.filter(r => r.status === "In Progress").length;
  const completeCount = reviews.filter(r => r.status === "Complete").length;

  const tabs = [
    { id: "inbox", label: "Governance Inbox", icon: Inbox },
    { id: "queue", label: "Rotation Queue", icon: Users },
    { id: "inventory", label: "Review Inventory", icon: ClipboardList },
    { id: "log", label: "Activity Log", icon: Activity },
  ];

  return (
    <div style={{ fontFamily: "'Segoe UI', system-ui, sans-serif", background: "#F4F4F5", minHeight: "100vh" }}>
      {/* Header */}
      <div style={{ background: BLACK, color: "white", padding: "20px 28px", borderBottom: `4px solid ${RED}` }}>
        <div style={{ fontSize: 12, letterSpacing: 2, color: "#B0B0B0", textTransform: "uppercase", marginBottom: 4 }}>
          Model Monitoring · Assignment Automation
        </div>
        <div style={{ fontSize: 24, fontWeight: 700 }}>Live Prototype Walkthrough</div>
      </div>

      {/* Stat strip */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, padding: "20px 28px 0" }}>
        {[
          { label: "Overdue", value: overdueCount, color: RED, Icon: AlertTriangle },
          { label: "Due within 7 days", value: dueSoonCount, color: "#B45309", Icon: Clock },
          { label: "In Progress", value: inProgressCount, color: "#2563EB", Icon: Activity },
          { label: "Completed", value: completeCount, color: "#15803D", Icon: CheckCircle2 },
        ].map(s => (
          <div key={s.label} style={{ background: "white", borderRadius: 8, padding: "14px 16px", boxShadow: "0 1px 2px rgba(0,0,0,0.08)", display: "flex", alignItems: "center", gap: 12 }}>
            <s.Icon size={20} color={s.color} />
            <div>
              <div style={{ fontSize: 20, fontWeight: 700, color: BLACK }}>{s.value}</div>
              <div style={{ fontSize: 12, color: "#6B7280" }}>{s.label}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div style={{ display: "flex", gap: 4, padding: "18px 28px 0", borderBottom: "1px solid #E5E7EB" }}>
        {tabs.map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            style={{
              display: "flex", alignItems: "center", gap: 6,
              padding: "10px 16px", border: "none", cursor: "pointer",
              background: "transparent", fontSize: 14, fontWeight: 600,
              color: tab === t.id ? RED : "#6B7280",
              borderBottom: tab === t.id ? `3px solid ${RED}` : "3px solid transparent",
            }}
          >
            <t.icon size={16} /> {t.label}
            {t.id === "inbox" && pending.length > 0 && (
              <span style={{ background: RED, color: "white", borderRadius: 999, fontSize: 11, padding: "1px 7px", marginLeft: 2 }}>
                {pending.length}
              </span>
            )}
          </button>
        ))}
      </div>

      <div style={{ padding: 28 }}>
        {tab === "inbox" && (
          <div>
            <div style={{ display: "flex", gap: 20, alignItems: "flex-start" }}>
              <div style={{ flex: 1, background: "white", borderRadius: 10, padding: 22, boxShadow: "0 1px 2px rgba(0,0,0,0.08)" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 14 }}>
                  <Mail size={18} color={RED} />
                  <div style={{ fontWeight: 700, fontSize: 15 }}>Next Governance Email</div>
                </div>

                {pending.length === 0 ? (
                  <div style={{ color: "#6B7280", fontSize: 14, padding: "20px 0" }}>Inbox clear — no pending assignments.</div>
                ) : (
                  <>
                    <div style={{ border: "1px solid #E5E7EB", borderRadius: 8, padding: 16, marginBottom: 16, background: "#FAFAFA" }}>
                      <div style={{ fontSize: 13, color: "#6B7280", marginBottom: 6 }}>From: model.governance@tfs.com</div>
                      <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 10 }}>{pending[0].modelName}</div>
                      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, fontSize: 13 }}>
                        <div><span style={{ color: "#6B7280" }}>Archer Model #:</span> {pending[0].modelNo}</div>
                        <div><span style={{ color: "#6B7280" }}>Start in Archer:</span> {fmt(pending[0].start)}</div>
                        <div><span style={{ color: "#6B7280" }}>Final Due Date:</span> {fmt(pending[0].due)}</div>
                      </div>
                    </div>

                    <button
                      onClick={processNext}
                      disabled={processing}
                      style={{
                        display: "flex", alignItems: "center", gap: 8, border: "none",
                        background: processing ? "#9CA3AF" : RED, color: "white",
                        padding: "10px 18px", borderRadius: 8, fontWeight: 700, fontSize: 14,
                        cursor: processing ? "default" : "pointer",
                      }}
                    >
                      <Zap size={16} /> {processing ? "Processing…" : "Process This Email"}
                    </button>

                    {processing && (
                      <div style={{ marginTop: 18 }}>
                        {STEPS.map((s, i) => (
                          <div key={s} style={{ display: "flex", alignItems: "center", gap: 10, padding: "6px 0", fontSize: 13, color: i <= stepIdx ? BLACK : "#C0C0C0" }}>
                            {i < stepIdx ? <CheckCircle2 size={16} color="#15803D" /> : i === stepIdx ? <Clock size={16} color={RED} /> : <div style={{ width: 16, height: 16, borderRadius: 999, border: "2px solid #E5E7EB" }} />}
                            {s}
                          </div>
                        ))}
                      </div>
                    )}
                  </>
                )}
              </div>

              <div style={{ width: 260, background: "white", borderRadius: 10, padding: 18, boxShadow: "0 1px 2px rgba(0,0,0,0.08)" }}>
                <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 10, color: "#6B7280", textTransform: "uppercase", letterSpacing: 1 }}>
                  Queued After This
                </div>
                {pending.slice(1).length === 0 ? (
                  <div style={{ fontSize: 13, color: "#9CA3AF" }}>Nothing else queued.</div>
                ) : pending.slice(1).map(e => (
                  <div key={e.id} style={{ fontSize: 13, padding: "8px 0", borderBottom: "1px solid #F3F4F6" }}>
                    <div style={{ fontWeight: 600 }}>{e.modelName}</div>
                    <div style={{ color: "#9CA3AF" }}>{e.modelNo} · due {fmt(e.due)}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {tab === "queue" && (
          <div style={{ background: "white", borderRadius: 10, padding: 20, boxShadow: "0 1px 2px rgba(0,0,0,0.08)" }}>
            <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 4 }}>Rotation Queue</div>
            <div style={{ fontSize: 13, color: "#6B7280", marginBottom: 16 }}>National managers maintain this list directly. Assignment always reads it live — try toggling someone inactive or unavailable, then process an email.</div>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
              <thead>
                <tr style={{ borderBottom: `2px solid ${RED}`, textAlign: "left" }}>
                  {["Data Scientist", "Email", "Active", "Unavailable From", "Unavailable To", "Last Assigned", "Status"].map(h => (
                    <th key={h} style={{ padding: "8px 10px", color: "#6B7280", fontWeight: 600 }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {queue.map(p => {
                  const unavail = isUnavailable(p);
                  return (
                    <tr key={p.id} style={{ borderBottom: "1px solid #F3F4F6" }}>
                      <td style={{ padding: "10px" }}>{p.last}, {p.first}</td>
                      <td style={{ padding: "10px", color: "#6B7280" }}>{p.email}</td>
                      <td style={{ padding: "10px" }}>
                        <input type="checkbox" checked={p.active} onChange={() => toggleActive(p.id)} />
                      </td>
                      <td style={{ padding: "10px" }}>
                        <input type="date" value={p.unavailStart} onChange={e => setUnavail(p.id, "unavailStart", e.target.value)} style={{ fontSize: 12, border: "1px solid #E5E7EB", borderRadius: 4, padding: 3 }} />
                      </td>
                      <td style={{ padding: "10px" }}>
                        <input type="date" value={p.unavailEnd} onChange={e => setUnavail(p.id, "unavailEnd", e.target.value)} style={{ fontSize: 12, border: "1px solid #E5E7EB", borderRadius: 4, padding: 3 }} />
                      </td>
                      <td style={{ padding: "10px" }}>{fmt(p.lastAssigned)}</td>
                      <td style={{ padding: "10px" }}>
                        {!p.active ? (
                          <span style={{ color: "#9CA3AF" }}>Inactive</span>
                        ) : unavail ? (
                          <span style={{ color: "#B45309" }}>Unavailable</span>
                        ) : (
                          <span style={{ color: "#15803D" }}>Eligible</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {tab === "inventory" && (
          <div style={{ background: "white", borderRadius: 10, padding: 20, boxShadow: "0 1px 2px rgba(0,0,0,0.08)" }}>
            <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 4 }}>Review Inventory</div>
            <div style={{ fontSize: 13, color: "#6B7280", marginBottom: 16 }}>DS updates status directly. Managers can override the assignment at any time — the reassignment is logged automatically.</div>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
              <thead>
                <tr style={{ borderBottom: `2px solid ${RED}`, textAlign: "left" }}>
                  {["Model", "Assigned To", "Start", "Due", "Status", "Time to Complete", "Assigned By", "Reassign"].map(h => (
                    <th key={h} style={{ padding: "8px 10px", color: "#6B7280", fontWeight: 600 }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {[...reviews].sort((a, b) => new Date(a.due) - new Date(b.due)).map(r => {
                  const person = queue.find(p => p.id === r.dsId);
                  const overdue = r.status !== "Complete" && new Date(r.due) < NOW;
                  const soon = r.status !== "Complete" && !overdue && daysBetween(NOW, r.due) <= 7;
                  return (
                    <tr key={r.id} style={{ borderBottom: "1px solid #F3F4F6", background: overdue ? "#FEF2F2" : soon ? "#FFFBEB" : "white" }}>
                      <td style={{ padding: "10px" }}>
                        <div style={{ fontWeight: 600 }}>{r.modelName}</div>
                        <div style={{ color: "#9CA3AF", fontSize: 12 }}>{r.modelNo}</div>
                      </td>
                      <td style={{ padding: "10px" }}>{person ? `${person.first} ${person.last}` : "—"}</td>
                      <td style={{ padding: "10px" }}>{fmt(r.start)}</td>
                      <td style={{ padding: "10px", fontWeight: overdue ? 700 : 400, color: overdue ? RED : "inherit" }}>
                        {fmt(r.due)}{overdue && " (overdue)"}
                      </td>
                      <td style={{ padding: "10px" }}>
                        <select value={r.status} onChange={e => updateStatus(r.id, e.target.value)} style={{ fontSize: 12, border: "1px solid #E5E7EB", borderRadius: 4, padding: "4px 6px" }}>
                          <option>Not Started</option>
                          <option>In Progress</option>
                          <option>Complete</option>
                        </select>
                      </td>
                      <td style={{ padding: "10px" }}>{r.completed ? `${daysBetween(r.start, r.completed)} days` : "—"}</td>
                      <td style={{ padding: "10px" }}>
                        <span style={{
                          fontSize: 11, fontWeight: 600, padding: "2px 8px", borderRadius: 999,
                          background: r.assignedBy === "Auto" ? "#EEF2FF" : "#FEF3C7",
                          color: r.assignedBy === "Auto" ? "#3730A3" : "#92400E",
                        }}>{r.assignedBy}</span>
                      </td>
                      <td style={{ padding: "10px" }}>
                        <select
                          value=""
                          onChange={e => e.target.value && reassign(r.id, e.target.value)}
                          style={{ fontSize: 12, border: "1px solid #E5E7EB", borderRadius: 4, padding: "4px 6px" }}
                        >
                          <option value="">Reassign…</option>
                          {queue.filter(p => p.active && p.id !== r.dsId).map(p => (
                            <option key={p.id} value={p.id}>{p.first} {p.last}</option>
                          ))}
                        </select>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {tab === "log" && (
          <div style={{ background: "white", borderRadius: 10, padding: 20, boxShadow: "0 1px 2px rgba(0,0,0,0.08)" }}>
            <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 4 }}>Activity Log</div>
            <div style={{ fontSize: 13, color: "#6B7280", marginBottom: 16 }}>Every assignment, notification, override, and completion — the audit trail the current process doesn't have.</div>
            <div>
              {log.map(l => (
                <div key={l.id} style={{ display: "flex", gap: 10, padding: "10px 0", borderBottom: "1px solid #F3F4F6", fontSize: 13 }}>
                  <LogIcon type={l.icon} />
                  <div>{l.text}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function LogIcon({ type }) {
  const map = {
    info: <ArrowRight size={15} color="#6B7280" />,
    assign: <UserCog size={15} color="#2563EB" />,
    mail: <Bell size={15} color="#B45309" />,
    done: <CheckCircle2 size={15} color="#15803D" />,
    override: <RotateCcw size={15} color="#92400E" />,
    warn: <AlertTriangle size={15} color="#E60012" />,
  };
  return <div style={{ marginTop: 1 }}>{map[type] || map.info}</div>;
}
