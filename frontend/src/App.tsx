import { lazy, Suspense } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { Loading } from "./components/ui";
import { LanguageProvider } from "./i18n";

const AgentBehavior = lazy(() => import("./pages/AgentBehavior"));
const AttackChains = lazy(() => import("./pages/AttackChains"));
const CustomPayload = lazy(() => import("./pages/CustomPayload"));
const AdaptiveRedTeam = lazy(() => import("./pages/AdaptiveRedTeam"));
const AuditRunner = lazy(() => import("./pages/AuditRunner"));
const Dashboard = lazy(() => import("./pages/Dashboard"));
const Findings = lazy(() => import("./pages/Findings"));
const Projects = lazy(() => import("./pages/Projects"));
const RagSecurity = lazy(() => import("./pages/RagSecurity"));
const Reports = lazy(() => import("./pages/Reports"));
const Settings = lazy(() => import("./pages/Settings"));
const Targets = lazy(() => import("./pages/Targets"));

export default function App() {
  return (
    <LanguageProvider>
      <Suspense fallback={<Loading />}>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="projects" element={<Projects />} />
            <Route path="targets" element={<Targets />} />
            <Route path="mcp" element={<AuditRunner mode="mcp" />} />
            <Route
              path="prompt-injection"
              element={<AuditRunner mode="prompt" />}
            />
            <Route
              path="jailbreak"
              element={<AuditRunner mode="jailbreak" />}
            />
            <Route path="custom-payload" element={<CustomPayload />} />
            <Route path="adaptive-red-team" element={<AdaptiveRedTeam />} />
            <Route path="rag" element={<RagSecurity />} />
            <Route path="agent-behavior" element={<AgentBehavior />} />
            <Route path="llm" element={<AuditRunner mode="llm" />} />
            <Route path="attack-chains" element={<AttackChains />} />
            <Route path="findings" element={<Findings />} />
            <Route path="reports" element={<Reports />} />
            <Route path="settings" element={<Settings />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </Suspense>
    </LanguageProvider>
  );
}
