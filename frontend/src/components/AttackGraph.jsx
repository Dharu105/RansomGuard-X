import { Monitor, Server, User, Cpu } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Background,
  BaseEdge,
  Controls,
  Handle,
  Position,
  ReactFlow,
  ReactFlowProvider,
  getBezierPath,
  useReactFlow,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

const POS = {
  "LAB-PC-21": { x: 70, y: 8 },
  "student.kumar": { x: 70, y: 118 },
  "FAC-PC-07": { x: 70, y: 228 },
  "FILE-SRV-01": { x: 70, y: 338 },
  "BACKUP-SRV-01": { x: 70, y: 448 },
};

function TypeIcon({ type }) {
  const t = String(type || "").toLowerCase();
  const cls = "shrink-0 text-cyan-400";
  if (t.includes("user") || t.includes("account") || t.includes("identity")) return <User size={13} className={cls} aria-hidden="true" />;
  if (t.includes("server") || t.includes("file") || t.includes("backup")) return <Server size={13} className={cls} aria-hidden="true" />;
  if (t.includes("work") || t.includes("end") || t.includes("pc")) return <Monitor size={13} className={cls} aria-hidden="true" />;
  return <Cpu size={13} className={cls} aria-hidden="true" />;
}

function AssetNode({ data }) {
  const status = data.status || "NORMAL";
  const predicted = data.predicted;
  const current = data.isCurrent;
  const atRisk = status === "AT_RISK" || status === "CRITICAL";
  const compromised = status === "COMPROMISED";
  let border = "1px solid #243044";
  if (current) border = "1px solid #22D3EE";
  else if (predicted) border = "1px dashed #818cf8";
  else if (compromised || atRisk) border = "1px solid #F59E0B";
  else if (status === "OBSERVED" || status === "SUSPICIOUS") border = "1px solid #22D3EE";

  return (
    <div className={`rgx-asset w-[210px] rounded-md bg-[#0c1422] px-3 py-2 text-left ${atRisk && !current ? "rgx-node-risk" : ""}`} style={{ border, color: "#E8F0F8" }}>
      <Handle type="target" position={Position.Top} className="!h-2 !w-2 !border-0 !bg-cyan-400" />
      <div className="flex items-start gap-2">
        <TypeIcon type={data.type} />
        <div className="min-w-0">
          <div className="truncate font-mono text-[12px] font-semibold">{data.name || data.id}</div>
          <div className="truncate text-[10px] uppercase tracking-wide text-[#7D8CA0]">{data.type}</div>
        </div>
      </div>
      <div className="mt-1.5 flex items-center gap-1.5 text-[10px] uppercase">
        <span
          className={`h-1.5 w-1.5 rounded-full ${
            current ? "bg-cyan-400" : predicted ? "bg-indigo-400" : compromised || atRisk ? "bg-amber-500" : "bg-slate-500"
          }`}
        />
        <span className={current ? "text-cyan-300" : predicted ? "text-indigo-300" : ""}>
          {current ? "CURRENT" : predicted ? "PREDICTED" : status}
        </span>
      </div>
      <Handle type="source" position={Position.Bottom} className="!h-2 !w-2 !border-0 !bg-cyan-400" />
    </div>
  );
}

function ProgressionEdge({ id, sourceX, sourceY, targetX, targetY, sourcePosition, targetPosition, style, markerEnd, data }) {
  const [edgePath] = getBezierPath({ sourceX, sourceY, sourcePosition, targetX, targetY, targetPosition });
  const observed = Boolean(data?.observed);
  const tick = data?.tick || 0;
  return (
    <>
      <BaseEdge id={id} path={edgePath} style={style} markerEnd={markerEnd} />
      {observed ? (
        <circle key={`${id}-${tick}`} r="3.5" fill="#22D3EE">
          <animateMotion dur="1.4s" repeatCount="1" path={edgePath} />
        </circle>
      ) : null}
    </>
  );
}

const nodeTypes = { asset: AssetNode };
const edgeTypes = { progression: ProgressionEdge };

function GraphCanvas({ graph, predictedTarget, compact, alive }) {
  const { fitView, setViewport } = useReactFlow();
  const [selected, setSelected] = useState(null);
  const nodesIn = graph?.nodes || [];
  const edgesIn = graph?.edges || [];
  const path = graph?.attack_path || [];
  const predictedId = predictedTarget || graph?.predicted_next || null;
  const tick = path.length;

  useEffect(() => {
    if (!path.length) setSelected(null);
  }, [path.length]);

  const nodes = useMemo(
    () =>
      nodesIn.map((n) => {
        const predicted = Boolean(n.is_predicted || n.id === predictedId) && !n.is_current;
        return {
          id: n.id,
          type: "asset",
          position: POS[n.id] || { x: 70, y: 8 },
          className: n.is_current ? "rgx-node-current" : predicted ? "rgx-node-predicted" : n.status === "AT_RISK" ? "rgx-node-risk" : "",
          data: { ...n, predicted, isCurrent: Boolean(n.is_current) },
        };
      }),
    [nodesIn, predictedId]
  );

  const edges = useMemo(
    () =>
      edgesIn.map((e) => {
        const observed = Boolean(e.observed);
        const predicted = !observed && (e.target === predictedId || e.predicted);
        return {
          id: e.id,
          type: "progression",
          source: e.source,
          target: e.target,
          animated: predicted,
          data: { observed, tick },
          style: {
            stroke: e.blocked ? "#22C55E" : observed ? "#22D3EE" : predicted ? "#818cf8" : "#334155",
            strokeDasharray: observed ? undefined : "7 5",
            strokeWidth: observed ? 2.2 : 1.3,
          },
        };
      }),
    [edgesIn, predictedId, tick]
  );

  const onNodeClick = useCallback((_, n) => setSelected(n.id), []);
  const selectedNode = selected ? nodesIn.find((n) => n.id === selected) : null;

  return (
    <div className="map-stage overflow-hidden">
      <div className="relative z-10 flex flex-wrap items-center justify-between gap-2 px-3 py-2">
        <div>
          <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-cyan-400/80">Live attack map</div>
          <div className="font-mono text-[11px] text-soc-muted">
            {graph?.current_node || "no current node"} · risk {graph?.graph_risk ?? 0}
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2 text-[10px] uppercase tracking-wide text-soc-muted">
          <span className="text-cyan-400">● Observed</span>
          <span className="text-indigo-300">┄ Predicted</span>
          <span className="text-violet-300">◆ Simulated</span>
          <span>○ Historical</span>
          <button type="button" className="btn btn-ghost py-0.5 text-[10px]" onClick={() => fitView({ padding: 0.18, duration: 200 })}>
            Fit graph
          </button>
          <button type="button" className="btn btn-ghost py-0.5 text-[10px]" onClick={() => setViewport({ x: 40, y: 10, zoom: 0.95 }, { duration: 200 })}>
            Reset view
          </button>
        </div>
      </div>
      <div className="relative">
        <div className={compact ? "h-[460px] min-h-[300px]" : "h-[540px] min-h-[340px]"}>
          <ReactFlow
            className="h-full w-full"
            nodes={nodes}
            edges={edges}
            nodeTypes={nodeTypes}
            edgeTypes={edgeTypes}
            onNodeClick={onNodeClick}
            fitView
            minZoom={0.5}
            proOptions={{ hideAttribution: true }}
          >
            <Background color="#1D2A3A" gap={20} size={1} />
            <Controls showInteractive={false} />
          </ReactFlow>
        </div>
        {!alive ? (
          <div className="pointer-events-none absolute inset-0 flex items-center justify-center bg-[#030712]/45">
            <div className="text-center">
              <div className="mx-auto mb-3 h-24 w-24 rounded-full border border-cyan-500/20 shadow-[0_0_40px_rgba(34,211,238,0.08)]" />
              <div className="text-[11px] font-semibold uppercase tracking-[0.2em] text-soc-muted">No active threat</div>
              <p className="mt-1 text-sm text-soc-muted">System ready. Run Safe Simulation to observe the path.</p>
            </div>
          </div>
        ) : null}
        {selectedNode ? (
          <aside className="absolute right-3 top-3 z-20 w-[230px] animate-event-in rounded-lg border border-cyan-500/30 bg-[#0b1220]/95 p-3 text-xs shadow-xl backdrop-blur-sm" aria-label="Asset inspector">
            <div className="text-[10px] uppercase tracking-[0.16em] text-cyan-400">Asset inspector</div>
            <div className="mt-1 font-mono text-sm font-semibold">{selectedNode.name}</div>
            <dl className="mt-2 space-y-1">
              <Row k="ID" v={selectedNode.id} />
              <Row k="Type" v={selectedNode.type} />
              <Row k="Status" v={selectedNode.status} />
              <Row k="Criticality" v={selectedNode.criticality} />
              <Row k="Current risk" v={selectedNode.risk} />
              <Row k="Observed events" v={(selectedNode.observed_events || []).join(", ") || "none"} />
            </dl>
            <p className="mt-2 text-[11px] text-soc-muted">
              {selectedNode.is_current
                ? "Why it matters: this is the current observed attack location."
                : selectedNode.id === predictedId
                  ? "Why it matters: forecasted next hop — not observed reality."
                  : "Why it matters: part of the synthetic environment topology."}
            </p>
            <button type="button" className="btn btn-ghost mt-2 w-full py-1 text-[10px]" onClick={() => setSelected(null)}>
              Close
            </button>
          </aside>
        ) : null}
      </div>
    </div>
  );
}

function Row({ k, v }) {
  return (
    <div className="flex justify-between gap-2">
      <span className="text-soc-muted">{k}</span>
      <span className="text-right font-mono">{String(v)}</span>
    </div>
  );
}

export default function AttackGraphView({ graph, predictedTarget, compact = false, alive = true }) {
  return (
    <ReactFlowProvider>
      <GraphCanvas graph={graph} predictedTarget={predictedTarget} compact={compact} alive={alive} />
    </ReactFlowProvider>
  );
}
