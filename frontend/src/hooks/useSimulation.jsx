import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { api, wsUrl } from "../services/api.js";

const SimulationContext = createContext(null);

export function SimulationProvider({ children }) {
  const [state, setState] = useState(null);
  const [status, setStatus] = useState("loading");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState("");
  const [wsConnected, setWsConnected] = useState(false);
  const wsRef = useRef(null);

  const apply = (payload) => {
    if (payload?.state) setState(payload.state);
    else if (payload && payload.scenario_id) setState(payload);
  };

  const refresh = useCallback(async () => {
    try {
      const data = await api.state();
      apply(data);
      setStatus("ok");
      setError("");
    } catch (err) {
      setStatus("error");
      setError(err.message || "Backend unavailable");
    }
  }, []);

  const run = useCallback(async (label, fn) => {
    setBusy(label);
    setError("");
    try {
      const data = await fn();
      apply(data);
      setStatus("ok");
      return data;
    } catch (err) {
      setError(err.message || "Request failed");
      setStatus("error");
      throw err;
    } finally {
      setBusy("");
    }
  }, []);

  useEffect(() => {
    refresh();
    let ws;
    let closed = false;
    let retry;
    const connect = () => {
      if (closed) return;
      try {
        ws = new WebSocket(wsUrl());
        wsRef.current = ws;
        ws.onopen = () => setWsConnected(true);
        ws.onmessage = (ev) => {
          try {
            const msg = JSON.parse(ev.data);
            if (msg.state) {
              setState(msg.state);
              setStatus("ok");
              setError("");
            }
          } catch {
            /* ignore malformed frames */
          }
        };
        ws.onerror = () => {
          setWsConnected(false);
          setError((prev) => prev || "Live event stream interrupted");
        };
        ws.onclose = () => {
          setWsConnected(false);
          if (closed) return;
          retry = setTimeout(connect, 2000);
        };
      } catch {
        setError("WebSocket unavailable; using polling");
      }
    };
    connect();
    const poll = setInterval(refresh, 8000);
    return () => {
      closed = true;
      clearInterval(poll);
      clearTimeout(retry);
      ws?.close();
    };
  }, [refresh]);

  const actions = useMemo(
    () => ({
      refresh,
      start: (id) => run("start", () => api.start(id)),
      nextEvent: () => run("next", () => api.nextEvent()),
      reset: () => run("reset", () => api.reset()),
      recommend: () => run("recommend", () => api.recommend()),
      reviewDefense: (action) => run("review", () => api.reviewDefense(action)),
      approveDefense: (payload) => run("approve", () => api.approveDefense(payload)),
      rejectDefense: (payload) => run("reject", () => api.rejectDefense(payload)),
      approve: (payload) => run("approve", () => api.approve(payload)),
      simulateDefense: (payload) => run("simulate", () => api.simulateDefense(payload)),
      counterfactual: (payload) => run("counterfactual", () => api.counterfactual(payload)),
      robustness: (payload) => run("robustness", () => api.robustness(payload)),
      dropEvent: (t) => run("drop", () => api.dropEvent(t)),
      intervention: (index) => run("intervention", () => api.intervention(index)),
      replay: (payload) => run("replay", () => api.replay(payload)),
      demo: (command) => run("demo", () => api.demo(command)),
      investigate: (q) => api.investigate(q),
      approvePlaybook: (payload) => run("playbook", () => api.approvePlaybook(payload)),
      approvePlaybookChange: (payload) =>
        run("playbook-approve", () => api.approvePlaybookChange(payload)),
      rejectPlaybookChange: (payload) =>
        run("playbook-reject", () => api.rejectPlaybookChange(payload)),
      runEvaluation: (scenario_id) => run("evaluation", () => api.runEvaluation(scenario_id)),
      resetEvaluation: () => run("evaluation-reset", () => api.resetEvaluation()),
    }),
    [refresh, run]
  );

  return (
    <SimulationContext.Provider value={{ state, status, error, busy, actions, wsConnected }}>
      {children}
    </SimulationContext.Provider>
  );
}

export function useSimulation() {
  const ctx = useContext(SimulationContext);
  if (!ctx) throw new Error("useSimulation must be used within provider");
  return ctx;
}
