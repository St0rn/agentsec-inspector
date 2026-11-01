import { Activity, Eye, Play, Radio, ShieldAlert, X, Zap } from "lucide-react";
import { useMemo, useState } from "react";
import { ErrorBox, PageHeader, Status } from "../components/ui";
import { AuditHistory } from "../components/AuditHistory";
import { MCPResultView } from "../components/MCPResultView";
import {
  MCPToolArguments,
  defaultToolArguments,
} from "../components/MCPToolArguments";
import type { DiscoveredTool } from "../components/MCPToolArguments";
import { useApi } from "../hooks/useApi";
import { api } from "../lib/api";
import type { Audit, Project, Scenario, Target } from "../types";

type RunnerMode = "mcp" | "prompt" | "jailbreak" | "llm";
type MCPMode = "passive" | "active" | "vulnerability";

const sensitivePattern =
  /(?:^|[_\\-])(delete|remove|exec|shell|admin|write|upload|credential|secret|transfer|password|create|update)(?:$|[_\\-])/i;

export default function AuditRunner({ mode }: { mode: RunnerMode }) {
  const projects = useApi<Project[]>("/projects");
  const targets = useApi<Target[]>("/targets");
  const scenarios = useApi<Scenario[]>("/scenarios");
  const audits = useApi<Audit[]>("/audits");
  const [projectId, setProject] = useState("");
  const [targetId, setTarget] = useState("");
  const [scenarioKey, setScenarioKey] = useState(
    mode === "jailbreak"
      ? "jb.authority-impersonation@@1.0.0"
      : "pi.direct@@1.0.0",
  );
  const [objective, setObjective] = useState(
    "The target must satisfy the locally configured security rules.",
  );
  const [securityRules, setSecurityRules] = useState(
    '[{"id":"marker-not-disclosed","rule_type":"marker_absent","value":"AGENTSEC_CANARY_7F3A","required":true}]',
  );
  const [testMode, setTestMode] = useState<"black_box" | "controlled_lab">(
    "black_box",
  );
  const [controlledConfirmed, setControlledConfirmed] = useState(false);
  const [requestPreview, setRequestPreview] =
    useState<Record<string, unknown>>();
  const [mcpMode, setMcpMode] = useState<MCPMode>("passive");
  const [toolName, setToolName] = useState("");
  const [argumentsText, setArgumentsText] = useState("{}");
  const [activeConfirmed, setActiveConfirmed] = useState(false);
  const [sensitiveConfirmed, setSensitiveConfirmed] = useState(false);
  const [identityNames, setIdentityNames] = useState<string[]>([]);
  const [error, setError] = useState("");
  const [active, setActive] = useState<Audit>();

  const filtered = useMemo(
    () =>
      targets.data?.filter(
        (target) =>
          target.project_id === projectId &&
          (mode === "mcp"
            ? target.target_type.startsWith("mcp_")
            : !target.target_type.startsWith("mcp_") &&
              target.target_type !== "rag"),
      ) || [],
    [targets.data, projectId, mode],
  );
  const discoveredTools = useMemo<DiscoveredTool[]>(() => {
    const source = audits.data?.find(
      (item) =>
        item.audit_type === "mcp_security" &&
        item.target_id === targetId &&
        typeof item.summary.discovery === "object",
    );
    const discovery = source?.summary.discovery as
      { tools?: DiscoveredTool[] } | undefined;
    return Array.isArray(discovery?.tools) ? discovery.tools : [];
  }, [audits.data, targetId]);
  const selectedTool = discoveredTools.find((tool) => tool.name === toolName);
  const selectedTarget = filtered.find((target) => target.id === targetId);
  const configuredIdentities = Array.isArray(selectedTarget?.configuration.identities)
    ? (selectedTarget.configuration.identities as Array<Record<string, unknown>>)
        .map((item) => String(item.name || ""))
        .filter(Boolean)
    : [];
  const sensitive = Boolean(
    selectedTool &&
    (sensitivePattern.test(selectedTool.name) ||
      selectedTool.annotations?.destructiveHint === true ||
      selectedTool.annotations?.readOnlyHint === false ||
      /(delete|remove|administrative delete|execute|transfer money)/i.test(
        selectedTool.description || "",
      )),
  );
  const visibleScenarios = useMemo(
    () =>
      scenarios.data?.filter((scenario) =>
        mode === "jailbreak"
          ? scenario.category === "jailbreak"
          : mode === "prompt"
            ? scenario.category !== "jailbreak"
            : true,
      ) || [],
    [scenarios.data, mode],
  );
  const title =
    mode === "mcp"
      ? "Scanner MCP"
      : mode === "prompt"
        ? "Prompt Injection Tester"
        : mode === "jailbreak"
          ? "Jailbreak Tester"
          : "LLM Security Scanner";

  function resetTarget(next: string) {
    setTarget(next);
    setToolName("");
    setArgumentsText("{}");
    setActiveConfirmed(false);
    setSensitiveConfirmed(false);
    setIdentityNames([]);
  }

  function promptBody() {
    const [scenarioId, scenarioVersion] = scenarioKey.split("@@");
    let rules: unknown;
    try {
      rules = JSON.parse(securityRules);
    } catch {
      throw new Error(
        "Les règles de sécurité doivent être un tableau JSON valide.",
      );
    }
    if (!Array.isArray(rules))
      throw new Error("Les règles de sécurité doivent être un tableau JSON.");
    return {
      project_id: projectId,
      target_id: targetId,
      scenario_id: scenarioId,
      scenario_version: scenarioVersion,
      security_objective: objective,
      security_rules: rules,
      test_mode: testMode,
      marker_provenance:
        testMode === "controlled_lab" ? "controlled_lab" : "user_payload",
      confirm_controlled_lab:
        testMode === "controlled_lab" && controlledConfirmed,
      confirm_active_test: true,
    };
  }

  async function previewRequest() {
    setError("");
    try {
      setRequestPreview(
        await api<Record<string, unknown>>("/audits/prompt/preview", {
          method: "POST",
          body: JSON.stringify(promptBody()),
        }),
      );
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : String(caught));
    }
  }

  async function run() {
    setError("");
    try {
      const path = mode === "mcp" ? "/audits/mcp" : "/audits/prompt";
      let body: Record<string, unknown>;
      if (mode === "mcp") {
        const isActive = mcpMode === "active";
        let toolCalls: Array<Record<string, unknown>> = [];
        if (isActive) {
          if (!toolName)
            throw new Error(
              "Sélectionnez un outil découvert lors d’un audit passif.",
            );
          let parsed: unknown;
          try {
            parsed = JSON.parse(argumentsText);
          } catch {
            throw new Error(
              "Les paramètres doivent être un objet JSON valide.",
            );
          }
          if (!parsed || Array.isArray(parsed) || typeof parsed !== "object")
            throw new Error("Les paramètres MCP doivent être un objet JSON.");
          toolCalls = [
            {
              tool_name: toolName,
              arguments: parsed,
              confirm_sensitive_operation: sensitiveConfirmed,
            },
          ];
        }
        body = {
          project_id: projectId,
          target_id: targetId,
          passive: !isActive,
          scan_mode:
            mcpMode === "vulnerability" ? "vulnerability" : "discovery",
          confirm_active_operations: isActive && activeConfirmed,
          active_tool_calls: toolCalls,
          identity_names: identityNames,
        };
      } else {
        body = promptBody();
      }
      const created = await api<Audit>(path, {
        method: "POST",
        body: JSON.stringify(body),
      });
      setActive(created);
      poll(created.id);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : String(caught));
    }
  }

  function poll(id: string) {
    const timer = setInterval(async () => {
      try {
        const item = await api<Audit>(`/audits/${id}`);
        setActive(item);
        if (["completed", "failed", "cancelled"].includes(item.status)) {
          clearInterval(timer);
          await audits.reload();
        }
      } catch {
        clearInterval(timer);
      }
    }, 900);
  }

  const activeDisabled =
    !projectId ||
    !targetId ||
    active?.status === "running" ||
    (mode !== "mcp" && testMode === "controlled_lab" && !controlledConfirmed) ||
    (mode === "mcp" &&
      mcpMode === "active" &&
      (!activeConfirmed || !toolName || (sensitive && !sensitiveConfirmed)));
  return (
    <>
      <PageHeader
        title={title}
        description={
          mode === "mcp"
            ? "Découverte passive, appel MCP actif contrôlé ou audit de vulnérabilités non destructif avec preuves."
            : mode === "jailbreak"
              ? "Teste les contournements de restrictions par autorité fictive, changement de persona, cadrage hypothétique, obfuscation et coercition de format."
              : "Exécute un scénario contrôlé contre une cible réelle avec marqueur fictif et classification PASS / FAIL / INCONCLUSIVE / ERROR."
        }
      />
      {error && <ErrorBox message={error} />}
      <div className="grid grid-cols-3 gap-5">
        <div className="card col-span-2 space-y-4">
          <label>
            <span className="label">Projet</span>
            <select
              className="input"
              value={projectId}
              onChange={(event) => {
                setProject(event.target.value);
                resetTarget("");
              }}
            >
              <option value="">Sélectionner…</option>
              {projects.data?.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.client_name} — {project.engagement_name}
                </option>
              ))}
            </select>
          </label>
          <label>
            <span className="label">Cible compatible</span>
            <select
              className="input"
              value={targetId}
              onChange={(event) => resetTarget(event.target.value)}
            >
              <option value="">Sélectionner…</option>
              {filtered.map((target) => (
                <option key={target.id} value={target.id}>
                  {target.name} ({target.target_type})
                </option>
              ))}
            </select>
          </label>
          {mode === "mcp" && (
            <>
              <div>
                <span className="label">Mode d’audit</span>
                <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
                  <button
                    type="button"
                    className={mcpMode === "passive" ? "btn-primary" : "btn"}
                    onClick={() => setMcpMode("passive")}
                  >
                    <Eye size={16} />
                    Passif — découverte
                  </button>
                  <button
                    type="button"
                    className={mcpMode === "active" ? "btn-primary" : "btn"}
                    onClick={() => setMcpMode("active")}
                  >
                    <Zap size={16} />
                    Actif — outil contrôlé
                  </button>
                  <button
                    type="button"
                    className={
                      mcpMode === "vulnerability" ? "btn-primary" : "btn"
                    }
                    onClick={() => setMcpMode("vulnerability")}
                  >
                    <ShieldAlert size={16} />
                    Audit de vulnérabilités
                  </button>
                </div>
              </div>
              {mcpMode === "passive" ? (
                <div className="rounded-lg border border-cyan/20 bg-cyan/5 p-4 text-sm text-slate-300">
                  <div className="mb-1 flex items-center gap-2 font-medium text-cyan">
                    <Eye size={16} />
                    Sans effet sur la cible
                  </div>
                  Initialisation MCP et inventaire des outils, ressources,
                  prompts et capacités. Aucun outil n’est appelé.
                </div>
              ) : mcpMode === "vulnerability" ? (
                <div className="space-y-2 rounded-lg border border-cyan/20 bg-cyan/5 p-4 text-sm text-slate-300">
                  <p className="flex items-center gap-2 font-semibold text-cyan">
                    <ShieldAlert size={17} />
                    Audit de vulnérabilités MCP
                  </p>
                  <p>
                    Contrôles des descriptions d’outils, schémas d’entrée,
                    annotations, permissions déclarées, ressources et prompts.
                    Rapports avec preuves, sévérités et remédiations.
                  </p>
                  <p className="text-xs text-amber-200">
                    Non destructif : cet audit analyse la surface MCP exposée
                    mais n’exploite pas les outils. Les résultats représentent
                    des risques potentiels, pas des vulnérabilités confirmées.
                  </p>
                </div>
              ) : (
                <div className="space-y-4 rounded-xl border border-amber-800/70 bg-amber-950/20 p-4">
                  <div className="flex items-start gap-3">
                    <Activity className="mt-0.5 text-amber-400" size={19} />
                    <div>
                      <p className="font-medium text-amber-100">
                        Audit actif explicitement borné
                      </p>
                      <p className="text-xs text-amber-300/80">
                        Exécute uniquement l’outil sélectionné ci-dessous. Un
                        audit passif préalable fournit l’inventaire.
                      </p>
                    </div>
                  </div>
                  {discoveredTools.length ? (
                    <>
                      <label>
                        <span className="label">Outil découvert</span>
                        <select
                          className="input"
                          value={toolName}
                          onChange={(event) => {
                            const next = discoveredTools.find(
                              (tool) => tool.name === event.target.value,
                            );
                            setToolName(event.target.value);
                            setArgumentsText(
                              next ? defaultToolArguments(next) : "{}",
                            );
                            setSensitiveConfirmed(false);
                          }}
                        >
                          <option value="">Sélectionner…</option>
                          {discoveredTools.map((tool) => (
                            <option key={tool.name} value={tool.name}>
                              {tool.name}
                              {sensitivePattern.test(tool.name) ||
                              tool.annotations?.destructiveHint === true ||
                              tool.annotations?.readOnlyHint === false
                                ? " · sensible"
                                : ""}
                            </option>
                          ))}
                        </select>
                      </label>
                      {selectedTool && (
                        <p className="rounded bg-slate-950/60 p-3 text-xs text-slate-400">
                          {selectedTool.description ||
                            "Aucune description fournie"}
                        </p>
                      )}
                      {selectedTool && (
                        <MCPToolArguments
                          tool={selectedTool}
                          value={argumentsText}
                          onChange={setArgumentsText}
                        />
                      )}
                      <label className="flex items-start gap-3 text-sm text-slate-300">
                        <input
                          className="mt-1"
                          type="checkbox"
                          checked={activeConfirmed}
                          onChange={(event) =>
                            setActiveConfirmed(event.target.checked)
                          }
                        />
                        <span>
                          J’autorise cet appel précis avec ces paramètres dans
                          le périmètre de la mission.
                        </span>
                      </label>
                      {sensitive && (
                        <label className="flex items-start gap-3 rounded border border-red-800 bg-red-950/30 p-3 text-sm text-red-200">
                          <input
                            className="mt-1"
                            type="checkbox"
                            checked={sensitiveConfirmed}
                            onChange={(event) =>
                              setSensitiveConfirmed(event.target.checked)
                            }
                          />
                          <span>
                            Je confirme séparément l’exécution de cette capacité
                            identifiée comme sensible ou potentiellement
                            destructive.
                          </span>
                        </label>
                      )}
                    </>
                  ) : (
                    <div className="rounded border border-slate-700 p-4 text-sm text-slate-400">
                      Aucun inventaire disponible pour cette cible. Lancez
                      d’abord un audit passif.
                    </div>
                  )}
                </div>
              )}
              {configuredIdentities.length > 0 && (
                <label>
                  <span className="label">
                    {mcpMode === "active"
                      ? "MCP identity for this call"
                      : "MCP identities to compare"}
                  </span>
                  <select
                    aria-label="MCP identities"
                    className="input"
                    multiple={mcpMode !== "active"}
                    value={identityNames}
                    onChange={(event) =>
                      setIdentityNames(
                        Array.from(event.target.selectedOptions).map(
                          (option) => option.value,
                        ),
                      )
                    }
                  >
                    <option value="default">Default target identity</option>
                    {configuredIdentities.map((identity) => (
                      <option key={identity} value={identity}>
                        {identity}
                      </option>
                    ))}
                  </select>
                  <span className="mt-1 block text-xs text-slate-500">
                    Credentials are resolved from configured environment-variable
                    references and are never displayed or stored in evidence.
                  </span>
                </label>
              )}
            </>
          )}
          {mode !== "mcp" && (
            <>
              <div>
                <span className="label">Mode de test</span>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    className={testMode === "black_box" ? "btn-primary" : "btn"}
                    onClick={() => {
                      setTestMode("black_box");
                      setControlledConfirmed(false);
                    }}
                  >
                    Black-Box Red Team
                  </button>
                  <button
                    type="button"
                    className={
                      testMode === "controlled_lab" ? "btn-primary" : "btn"
                    }
                    onClick={() => setTestMode("controlled_lab")}
                  >
                    Controlled Lab
                  </button>
                </div>
              </div>
              <div className="rounded-lg border border-cyan/20 bg-cyan/5 p-3 text-xs text-slate-300">
                {testMode === "black_box"
                  ? "Seul le payload du scénario est transmis. Aucun message system, objectif ou critère local n’est ajouté."
                  : "Une instruction system artificielle et un marqueur protégé sont ajoutés pour un laboratoire contrôlé."}
              </div>
              <label>
                <span className="label">Scénario versionné</span>
                <select
                  className="input"
                  value={scenarioKey}
                  onChange={(event) => setScenarioKey(event.target.value)}
                >
                  {visibleScenarios.map((scenario) => (
                    <option
                      key={`${scenario.id}-${scenario.version}`}
                      value={`${scenario.id}@@${scenario.version}`}
                    >
                      {scenario.name} — v{scenario.version}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                <span className="label">Objectif de sécurité</span>
                <textarea
                  className="input min-h-20"
                  value={objective}
                  onChange={(event) => setObjective(event.target.value)}
                />
                <span className="mt-1 block text-xs text-cyan">
                  Critère d’évaluation local — jamais transmis à la cible.
                </span>
              </label>
              <label>
                <span className="label">Règles vérifiables (JSON)</span>
                <textarea
                  className="input min-h-24 font-mono text-xs"
                  value={securityRules}
                  onChange={(event) => setSecurityRules(event.target.value)}
                />
                <span className="mt-1 block text-xs text-slate-500">
                  Types : marker_absent, response_contains,
                  response_not_contains, tool_allowed, tool_forbidden et
                  completion_required. Un appel d’outil n’est pas un échec sans
                  règle qui l’interdit.
                </span>
              </label>
              {testMode === "controlled_lab" && (
                <label className="flex items-start gap-3 rounded border border-amber-800 bg-amber-950/20 p-3 text-sm text-amber-200">
                  <input
                    className="mt-1"
                    type="checkbox"
                    checked={controlledConfirmed}
                    onChange={(event) =>
                      setControlledConfirmed(event.target.checked)
                    }
                  />
                  <span>
                    Je confirme l’ajout d’une politique et d’un marqueur
                    artificiels propres au laboratoire.
                  </span>
                </label>
              )}
            </>
          )}
          <div className="flex gap-3">
            {mode !== "mcp" && (
              <button
                className="btn"
                disabled={
                  !projectId ||
                  !targetId ||
                  (testMode === "controlled_lab" && !controlledConfirmed)
                }
                onClick={() => void previewRequest()}
              >
                <Eye size={16} />
                Prévisualiser la requête
              </button>
            )}
            <button
              className="btn-primary"
              disabled={activeDisabled}
              onClick={() => void run()}
            >
              <Play size={16} />
              {mode === "mcp"
                ? mcpMode === "passive"
                  ? "Lancer l’inspection passive"
                  : mcpMode === "vulnerability"
                    ? "Lancer l’audit de vulnérabilités"
                    : "Confirmer et lancer l’appel actif"
                : "Confirmer et lancer le test"}
            </button>
          </div>
        </div>
        <div className="card">
          <div className="mb-4 flex items-center gap-2">
            <Radio className="text-cyan" size={18} />
            <h3 className="font-semibold text-white">Exécution</h3>
          </div>
          {active ? (
            <div className="space-y-3 text-sm">
              <Status value={active.status} />
              <p className="font-mono text-xs text-slate-500">{active.id}</p>
              {active.error && <p className="text-red-300">{active.error}</p>}
              {Object.keys(active.summary).length > 0 && mode === "mcp" ? (
                <MCPResultView summary={active.summary} />
              ) : (
                <pre className="max-h-96 overflow-auto whitespace-pre-wrap rounded bg-slate-950 p-3 text-xs text-slate-300">
                  {JSON.stringify(active.summary, null, 2)}
                </pre>
              )}
            </div>
          ) : (
            <div className="py-12 text-center text-slate-500">
              <ShieldAlert className="mx-auto mb-3" />
              <p className="text-sm">Aucune exécution active</p>
            </div>
          )}
        </div>
      </div>
      <AuditHistory
        onDelete={async () => {
          await audits.reload();
        }}
        audits={(audits.data || []).filter(
          (item) =>
            (!projectId || item.project_id === projectId) &&
            (mode === "mcp"
              ? item.audit_type === "mcp_security"
              : mode === "jailbreak"
                ? item.audit_type === "jailbreak"
                : mode === "llm"
                  ? ["prompt_injection", "jailbreak"].includes(item.audit_type)
                  : item.audit_type === "prompt_injection"),
        )}
      />
      {requestPreview && (
        <div
          role="dialog"
          aria-modal="true"
          className="fixed inset-0 z-50 grid place-items-center bg-black/75 p-8"
          onMouseDown={() => setRequestPreview(undefined)}
        >
          <section
            className="panel max-h-[88vh] w-full max-w-4xl overflow-auto p-6"
            onMouseDown={(event) => event.stopPropagation()}
          >
            <div className="mb-4 flex items-center">
              <div>
                <h2 className="font-semibold text-white">
                  Requête effective prévisualisée
                </h2>
                <p className="text-xs text-slate-500">
                  Les identifiants d’authentification ne sont jamais affichés.
                </p>
              </div>
              <button
                aria-label="Fermer"
                className="btn ml-auto"
                onClick={() => setRequestPreview(undefined)}
              >
                <X size={16} />
              </button>
            </div>
            <pre className="whitespace-pre-wrap rounded bg-slate-950 p-4 text-xs text-slate-200">
              {JSON.stringify(requestPreview, null, 2)}
            </pre>
          </section>
        </div>
      )}
    </>
  );
}
