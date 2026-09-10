import { useEffect, useMemo, useState } from "react";
import { Menu, Pause, Play, RotateCcw, SkipForward } from "lucide-react";
import { useSimulation } from "../hooks/useSimulation.jsx";

const SCENARIO_LABELS = {
  "SCN-001": "PROGRESSIVE RANSOMWARE",
  "SCN-002": "EARLY DETECTION",
  "SCN-003": "CREDENTIAL-FIRST ATTACK",
  "SCN-004": "LATERAL MOVEMENT ATTACK",
  "SCN-005": "HIGH ADAPTATION PATH",
  "SCN-006": "BENIGN FALSE-POSITIVE",
};

export default function TopBar({ onMenu }) {
  const { state, status, error, busy, actions, wsConnected } = useSimulation();
  const demo = state?.demo || {};
  const simOnline = status === "ok" && Boolean(state);
  const sid = state?.scenario_id || "SCN-001";
  const [clock, setClock] = useState(() => new Date().toLocaleTimeString());

  useEffect(() => {
    const t = setInterval(() => setClock(new Date().toLocaleTimeString()), 1000);
    return () => clearInterval(t);
  }, []);

  return (
    <>
      <header className="grid grid-cols-1 items-center gap-2 border-b border-soc-border bg-soc-panel/90 px-4 py-2.5 backdrop-blur-sm lg:grid-cols-3 lg:px-5">
        <div className="flex min-w-0 items-center gap-3">
          <button type="button" className="btn btn-ghost p-2 lg:hidden" onClick={onMenu} aria-label="Open navigation">
            <Menu size={16} />
          </button>
          <span className="inline-flex items-center gap-1.5 text-[11px] uppercase tracking-wide text-soc-muted">
            <span className={`h-1.5 w-1.5 rounded-full ${simOnline ? "animate-pulse-dot bg-soc-good" : "bg-soc-crit"}`} />
            {simOnline ? "System online" : "System offline"}
          </span>
          <span className="hidden items-center gap-1.5 text-[11px] uppercase tracking-wide text-soc-muted sm:inline-flex">
            <span className={`h-1.5 w-1.5 rounded-full ${wsConnected ? "animate-pulse-dot bg-cyan-500" : "bg-soc-warn"}`} />
            {wsConnected ? "WebSocket connected" : "WebSocket reconnecting"}
          </span>
        </div>
        <div className="text-center">
          <div className="font-mono text-xs font-semibold">{sid}</div>
          <div className="text-[10px] uppercase tracking-[0.14em] text-cyan-400">{SCENARIO_LABELS[sid] || state?.current_stage || "STANDBY"}</div>
          <div className="text-[10px] uppercase tracking-wide text-soc-muted">Synthetic environment</div>
        </div>
        <div className="flex flex-wrap items-center justify-end gap-1.5">
          <span className="hidden font-mono text-[11px] text-soc-muted xl:inline">{clock}</span>
          {busy ? <span className="text-[11px] text-soc-warn">Working: {busy}</span> : null}
          <button className="btn btn-primary py-1.5 text-xs" onClick={() => actions.start("SCN-001")} disabled={!!busy} aria-label="Run safe simulation">
            <Play size={13} aria-hidden="true" /> Run Safe Simulation
          </button>
          <button className="btn btn-ghost py-1.5 text-xs" onClick={() => actions.nextEvent()} disabled={!!busy} aria-label="Next event">
            <SkipForward size={13} aria-hidden="true" /> Next Event
          </button>
          <button className="btn btn-ghost py-1.5 text-xs" onClick={() => actions.reset()} disabled={!!busy} aria-label="Reset simulation">
            <RotateCcw size={13} aria-hidden="true" /> Reset
          </button>
          <button className="btn btn-ghost py-1.5 text-xs" onClick={() => actions.demo("START")} disabled={!!busy} aria-label="Start three minute demo">
            Demo
          </button>
          {demo.running ? (
            <button className="btn btn-ghost py-1.5 text-xs" onClick={() => actions.demo("PAUSE")} aria-label="Pause demo">
              <Pause size={13} aria-hidden="true" /> Pause
            </button>
          ) : null}
        </div>
      </header>
      {status === "error" || error ? (
        <div className="flex items-center gap-2 border-b border-soc-crit/40 bg-soc-crit/10 px-5 py-2 text-sm text-soc-crit" role="alert">
          <div>
            <div className="font-semibold">Connection interrupted</div>
            <div className="text-xs text-soc-muted">{error || "Unable to receive live simulation updates."}</div>
          </div>
          <button className="btn btn-ghost ml-auto py-1 text-xs" onClick={() => actions.refresh()}>
            Retry
          </button>
        </div>
      ) : null}
    </>
  );
}
