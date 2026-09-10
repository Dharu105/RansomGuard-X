import { Navigate, Route, Routes } from "react-router-dom";
import AppLayout from "./layouts/AppLayout.jsx";
import CommandCenter from "./pages/CommandCenter.jsx";
import LiveDefense from "./pages/LiveDefense.jsx";
import AttackGraph from "./pages/AttackGraph.jsx";
import InterventionWindow from "./pages/InterventionWindow.jsx";
import CounterfactualReplay from "./pages/CounterfactualReplay.jsx";
import AlternateReality from "./pages/AlternateReality.jsx";
import DefenseIntelligence from "./pages/DefenseIntelligence.jsx";
import LearningPlaybooks from "./pages/LearningPlaybooks.jsx";
import IncidentHistory from "./pages/IncidentHistory.jsx";
import AIInvestigator from "./pages/AIInvestigator.jsx";
import Settings from "./pages/Settings.jsx";
import Evaluation from "./pages/Evaluation.jsx";

export default function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route path="/" element={<CommandCenter />} />
        <Route path="/live" element={<LiveDefense />} />
        <Route path="/graph" element={<AttackGraph />} />
        <Route path="/intervention" element={<InterventionWindow />} />
        <Route path="/counterfactual" element={<CounterfactualReplay />} />
        <Route path="/alternate" element={<AlternateReality />} />
        <Route path="/intelligence" element={<DefenseIntelligence />} />
        <Route path="/evaluation" element={<Evaluation />} />
        <Route path="/playbooks" element={<LearningPlaybooks />} />
        <Route path="/history" element={<IncidentHistory />} />
        <Route path="/investigator" element={<AIInvestigator />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
