import { NavLink, useLocation } from "react-router-dom";
import {
  Activity,
  BarChart3,
  BookOpen,
  Clock,
  GitBranch,
  History,
  LayoutDashboard,
  MessageSquare,
  Settings as SettingsIcon,
  Shield,
  Shuffle,
  Sparkles,
  Split,
  Workflow,
} from "lucide-react";

const groups = [
  {
    id: "command",
    label: "Command",
    items: [{ to: "/", label: "Command Center", icon: LayoutDashboard, end: true }],
  },
  {
    id: "analyze",
    label: "Analyze",
    items: [
      { to: "/graph", label: "Attack Graph", icon: GitBranch },
      { to: "/?tab=predict", label: "Predictions", icon: Sparkles, match: "predict" },
      { to: "/investigator", label: "AI Investigator", icon: MessageSquare },
      { to: "/intervention", label: "Intervention Window", icon: Clock },
      { to: "/counterfactual", label: "Counterfactual Replay", icon: Shuffle },
      { to: "/alternate", label: "Alternate Reality", icon: Workflow },
    ],
  },
  {
    id: "defend",
    label: "Defend",
    items: [
      { to: "/intelligence", label: "Defense Intelligence", icon: Activity },
      { to: "/?tab=forks", label: "Attack Fork Lab", icon: Split, match: "forks" },
      { to: "/?tab=adapt", label: "Adaptation", icon: Shield, match: "adapt" },
      { to: "/live", label: "Live Defense", icon: Shield },
    ],
  },
  {
    id: "learn",
    label: "Learn",
    items: [
      { to: "/history", label: "Incident Memory", icon: History },
      { to: "/playbooks", label: "Playbook Evolution", icon: BookOpen },
      { to: "/evaluation", label: "Evaluation", icon: BarChart3 },
    ],
  },
];

function linkActive(item, pathname, search) {
  const params = new URLSearchParams(search);
  const tab = params.get("tab");
  if (item.match) return pathname === "/" && tab === item.match;
  if (item.end) return pathname === "/" && !tab;
  return pathname === item.to;
}

export default function Sidebar({ onNavigate }) {
  const loc = useLocation();

  return (
    <aside className="flex h-full w-[240px] shrink-0 flex-col border-r border-soc-border bg-soc-panel">
      <div className="border-b border-soc-border px-4 py-4">
        <div className="text-[11px] font-semibold uppercase tracking-[0.22em] text-white">RansomGuard-X</div>
        <div className="mt-1 text-[11px] font-medium uppercase leading-snug tracking-[0.08em] text-soc-muted">
          Cyber Resilience Command Center
        </div>
        <div className="mt-2 text-[11px] leading-snug text-soc-muted">See the Threat. Shape the Defense.</div>
      </div>
      <nav className="flex-1 overflow-y-auto px-2 py-3">
        {groups.map((group) => (
          <div key={group.id} className="mb-3">
            <div className="px-3 pb-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-soc-muted">
              {group.label}
            </div>
            <div className="mb-2 border-b border-soc-border/80" />
            {group.items.map((item) => {
              const Icon = item.icon;
              const active = linkActive(item, loc.pathname, loc.search);
              return (
                <NavLink
                  key={item.to + item.label}
                  to={item.to}
                  end={item.end}
                  onClick={onNavigate}
                  className={`mb-0.5 flex items-center gap-2 rounded-lg border-l-2 px-3 py-1.5 text-[13px] transition duration-200 ${
                    active
                      ? "border-cyan-400 bg-cyan-500/10 text-white shadow-[0_0_16px_rgba(34,211,238,0.12)]"
                      : "border-transparent text-soc-muted hover:bg-soc-raised hover:text-white"
                  }`}
                >
                  <Icon size={15} aria-hidden="true" />
                  {item.label}
                </NavLink>
              );
            })}
          </div>
        ))}
      </nav>
      <div className="border-t border-soc-border p-2">
        <NavLink
          to="/settings"
          onClick={onNavigate}
          className={({ isActive }) =>
            `flex items-center gap-2 rounded-lg border-l-2 px-3 py-2 text-[13px] ${
              isActive
                ? "border-cyan-400 bg-cyan-500/10 text-white"
                : "border-transparent text-soc-muted hover:bg-soc-raised hover:text-white"
            }`
          }
        >
          <SettingsIcon size={15} aria-hidden="true" />
          Settings
        </NavLink>
        <div className="mt-2 px-3 pb-2 text-[10px] text-soc-muted">
          <div className="font-semibold uppercase tracking-[0.18em] text-soc-text">RansomGuard-X</div>
          <div className="mt-1 uppercase tracking-wide">Synthetic Environment</div>
        </div>
      </div>
    </aside>
  );
}
