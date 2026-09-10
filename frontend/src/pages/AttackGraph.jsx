import AttackGraphView from "../components/AttackGraph.jsx";
import { PageHeader, MetaBadge } from "../components/ui.jsx";
import { useSimulation } from "../hooks/useSimulation.jsx";

export default function AttackGraph() {
  const { state } = useSimulation();
  if (!state) return <div className="text-soc-muted">Connecting to simulation…</div>;
  return (
    <div className="space-y-4">
      <PageHeader
        title="Attack Graph"
        subtitle="Generated from live simulation events. Future hops stay uncompromised until observed."
        badges={<MetaBadge tone="cyan">Synthetic Simulation</MetaBadge>}
      />
      <AttackGraphView
        graph={state.attack_graph}
        predictedTarget={state.prediction?.predicted_target}
        alive={(state.events || []).length > 0}
      />
    </div>
  );
}
