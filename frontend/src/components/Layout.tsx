import {
  Activity,
  Boxes,
  BrainCircuit,
  ChevronRight,
  FileCode2,
  FileSearch,
  FileText,
  FolderKanban,
  Gauge,
  GitBranch,
  ListChecks,
  Network,
  Settings,
  ShieldAlert,
  ShieldOff,
  Target,
} from "lucide-react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { useBackendConnection } from "../hooks/useBackendConnection";

const nav = [
  ["Dashboard", "/", Gauge],
  ["Projects", "/projects", FolderKanban],
  ["Targets", "/targets", Target],
  ["MCP Security", "/mcp", Network],
  ["Prompt Injection", "/prompt-injection", ShieldAlert],
  ["Jailbreak", "/jailbreak", ShieldOff],
  ["Custom Payload", "/custom-payload", FileCode2],
  ["RAG Security", "/rag", FileSearch],
  ["Agent Behavior", "/agent-behavior", Activity],
  ["LLM Security", "/llm", BrainCircuit],
  ["Attack Chains", "/attack-chains", GitBranch],
  ["Findings", "/findings", ListChecks],
  ["Reports", "/reports", FileText],
  ["Settings", "/settings", Settings],
] as const;

export function Layout() {
  const location = useLocation();
  const current =
    nav.find(([, path]) =>
      path === "/"
        ? location.pathname === "/"
        : location.pathname.startsWith(path),
    )?.[0] || "AgentSec";
  const { state, reconnect } = useBackendConnection();
  const connection = {
    connecting: {
      label: "Connecting...",
      dot: "bg-amber-400",
      panel: "border-amber-900/70 bg-amber-950/30 text-amber-300",
    },
    online: {
      label: "Backend Online",
      dot: "bg-emerald-400",
      panel: "border-emerald-900/70 bg-emerald-950/30 text-emerald-300",
    },
    offline: {
      label: "Backend Offline",
      dot: "bg-red-400",
      panel: "border-red-900/70 bg-red-950/30 text-red-300",
    },
  }[state];
  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_65%_-20%,rgba(47,123,255,.16),transparent_35%)]">
      <aside className="fixed inset-y-0 left-0 z-20 w-64 border-r border-slate-800 bg-[#090e17]/95 p-4 backdrop-blur">
        <div className="mb-7 flex items-center gap-3 px-2">
          <div className="grid h-10 w-10 place-items-center rounded-xl border border-cyan/40 bg-cyan/10 text-cyan">
            <Boxes size={21} />
          </div>
          <div>
            <div className="font-bold tracking-tight text-white">
              AgentSec Inspector
            </div>
            <div className="text-[10px] uppercase tracking-widest text-cyan">
              AI Security Audit
            </div>
          </div>
        </div>
        <nav className="space-y-1">
          {nav.map(([label, path, Icon]) => (
            <NavLink
              key={path}
              to={path}
              end={path === "/"}
              className={({ isActive }) =>
                `group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition ${isActive ? "bg-electric/15 text-cyan ring-1 ring-electric/30" : "text-slate-400 hover:bg-slate-800/60 hover:text-slate-100"}`
              }
            >
              <Icon size={17} />
              <span>{label}</span>
              <ChevronRight
                size={13}
                className="ml-auto opacity-0 transition group-hover:opacity-100"
              />
            </NavLink>
          ))}
        </nav>
        <div
          aria-live="polite"
          className={`absolute bottom-4 left-4 right-4 rounded-lg border p-3 text-xs ${connection.panel}`}
        >
          <div className="font-medium text-slate-200">Local Mode</div>
          <div className="mt-1 flex items-center">
            <span
              className={`mr-2 inline-block h-2 w-2 rounded-full ${connection.dot}`}
            />
            {connection.label}
          </div>
          {state === "offline" && (
            <button
              type="button"
              className="mt-2 text-xs font-medium text-cyan hover:text-white"
              onClick={() => void reconnect()}
            >
              Reconnecter
            </button>
          )}
        </div>
      </aside>
      <main className="ml-64 min-h-screen">
        <header className="sticky top-0 z-10 flex h-16 items-center border-b border-slate-800 bg-ink/75 px-8 backdrop-blur">
          <h1 className="text-lg font-semibold text-white">{current}</h1>
          <div className="ml-auto text-xs text-slate-500">
          Audit passif par défaut · v1.2.0
          </div>
        </header>
        <div className="p-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
