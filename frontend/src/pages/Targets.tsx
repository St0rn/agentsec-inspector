import { Edit3, Plus, Radio, Trash2, X } from "lucide-react";
import { useMemo, useState } from "react";
import { Empty, ErrorBox, Loading, PageHeader } from "../components/ui";
import { ProjectDisclosure } from "../components/ProjectDisclosure";
import { useApi } from "../hooks/useApi";
import { api } from "../lib/api";
import type { Project, Target } from "../types";

const targetTypes = [
  ["mcp_http", "MCP distant (Streamable)"],
  ["mcp_stdio", "MCP local (stdio)"],
  ["openai", "API compatible OpenAI"],
  ["ollama", "Ollama"],
  ["chatbot", "Chatbot générique"],
  ["custom_http", "API Chat Completions personnalisée"],
  ["rag", "Système RAG / import de traces"],
  ["agent_lab", "Agent local de laboratoire"],
] as const;
const urlTypes = new Set([
  "mcp_http",
  "openai",
  "ollama",
  "chatbot",
  "custom_http",
  "agent_lab",
  "rag",
]);
const configurationHelp: Record<string, string> = {
  mcp_http: 'Exemple : {"headers":{"X-Tenant":"lab"}}.',
  mcp_stdio:
    'Exemple : {"command":"node","args":["server.js"]}. L’exécutable doit être autorisé côté application.',
  openai:
    'Exemple : {"model":"gpt-4.1-mini","response_format":"auto","api_key_env":"OPENAI_API_KEY"}.',
  ollama: 'Exemple : {"model":"llama3.2","response_format":"ollama"}.',
  chatbot:
    'Exemple AI Red Team Range : {"message_path":"message","response_format":"ndjson"}. Pour une réponse JSON imbriquée, ajoutez response_path et tool_calls_path.',
  custom_http:
    'Exemple : {"model":"model-name","response_format":"openai","api_key_env":"CHAT_API_KEY"}.',
  rag: 'Endpoint RAG actif : {"message_path":"query","response_path":"response","chunks_path":"retrieved_chunks","context_path":"llm_context","response_format":"auto"}. Facultatif : ingest_endpoint pour documents contrôlés, après autorisation.',
  agent_lab:
    "Agent contrôlé de laboratoire ; JSON, NDJSON et SSE sont acceptés.",
};
const emptyForm = {
  project_id: "",
  name: "",
  target_type: "mcp_http",
  endpoint: "",
  configuration: "{}",
  remote_authorized: false,
};

interface TestResult {
  connected: boolean;
  protocol?: string;
  model?: string;
  response?: string;
  tool_calls?: unknown[];
  events?: unknown[];
  completed?: boolean | null;
  metadata?: Record<string, unknown>;
  suggested_configuration?: Record<string, unknown>;
}

export default function Targets() {
  const targets = useApi<Target[]>("/targets");
  const projects = useApi<Project[]>("/projects");
  const [show, setShow] = useState(false);
  const [editing, setEditing] = useState<string>();
  const [error, setError] = useState("");
  const [form, setForm] = useState(emptyForm);
  const [testing, setTesting] = useState<string>();
  const [testResult, setTestResult] = useState<TestResult>();
  const needsUrl = urlTypes.has(form.target_type);
  const typeLabel = useMemo(() => Object.fromEntries(targetTypes), []);
  function create() {
    setEditing(undefined);
    setForm(emptyForm);
    setShow(true);
    setTestResult(undefined);
  }
  function edit(target: Target) {
    setEditing(target.id);
    setForm({
      project_id: target.project_id,
      name: target.name,
      target_type: target.target_type,
      endpoint: target.endpoint || "",
      configuration: JSON.stringify(target.configuration, null, 2),
      remote_authorized: target.remote_authorized,
    });
    setShow(true);
    setTestResult(undefined);
  }
  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    try {
      const configuration = JSON.parse(form.configuration);
      await api(editing ? `/targets/${editing}` : "/targets", {
        method: editing ? "PUT" : "POST",
        body: JSON.stringify({
          ...form,
          endpoint: form.endpoint || null,
          configuration,
        }),
      });
      setShow(false);
      setEditing(undefined);
      await targets.reload();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : String(caught));
    }
  }
  async function test(target: Target) {
    setError("");
    setTesting(target.id);
    setTestResult(undefined);
    try {
      const result = await api<TestResult>(`/targets/${target.id}/test`, {
        method: "POST",
        body: JSON.stringify({
          confirm_active_request: true,
          test_message: "Reply with the word CONNECTED.",
        }),
      });
      setTestResult(result);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : String(caught));
    } finally {
      setTesting(undefined);
    }
  }
  async function applySuggestion() {
    if (!testResult?.suggested_configuration) return;
    let current: Record<string, unknown>;
    try {
      current = JSON.parse(form.configuration);
    } catch {
      current = {};
    }
    setForm({
      ...form,
      configuration: JSON.stringify(
        { ...current, ...testResult.suggested_configuration },
        null,
        2,
      ),
    });
  }
  async function remove(id: string) {
    if (confirm("Supprimer cette cible ?")) {
      await api(`/targets/${id}`, { method: "DELETE" });
      await targets.reload();
    }
  }
  const projectTargets = (projects.data || [])
    .map((project) => ({
      project,
      items: (targets.data || []).filter((target) => target.project_id === project.id),
    }))
    .filter((group) => group.items.length);
  return (
    <>
      <PageHeader
        title="Cibles"
        description="Chatbots, API LLM, agents utilisant des outils, serveurs MCP et systèmes RAG du périmètre autorisé."
        action={
          <button className="btn-primary" onClick={create}>
            <Plus size={16} />
            Ajouter
          </button>
        }
      />
      {(targets.error || error) && (
        <ErrorBox message={targets.error || error} />
      )}{" "}
      {show && (
        <form onSubmit={submit} className="card mb-5 grid grid-cols-2 gap-4">
          <div className="col-span-2 flex items-center">
            <h2 className="font-semibold text-white">
              {editing ? "Modifier la cible" : "Nouvelle cible"}
            </h2>
            <button
              aria-label="Fermer"
              type="button"
              className="ml-auto text-slate-500"
              onClick={() => setShow(false)}
            >
              <X size={17} />
            </button>
          </div>
          <label>
            <span className="label">Projet</span>
            <select
              className="input"
              required
              value={form.project_id}
              onChange={(event) =>
                setForm({ ...form, project_id: event.target.value })
              }
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
            <span className="label">Nom</span>
            <input
              className="input"
              required
              placeholder="Chatbot support client"
              value={form.name}
              onChange={(event) =>
                setForm({ ...form, name: event.target.value })
              }
            />
          </label>
          <label>
            <span className="label">Type de cible</span>
            <select
              className="input"
              value={form.target_type}
              onChange={(event) =>
                setForm({
                  ...form,
                  target_type: event.target.value,
                  endpoint:
                    event.target.value === "mcp_stdio" ? "" : form.endpoint,
                })
              }
            >
              {targetTypes.map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </label>
          <label>
            <span className="label">
              URL cible {needsUrl && <span className="text-red-400">*</span>}
            </span>
            <input
              className="input"
              type="url"
              required={needsUrl}
              pattern="https?://.+"
              placeholder="https://chatbot.example.com/api/chat"
              value={form.endpoint}
              onChange={(event) =>
                setForm({ ...form, endpoint: event.target.value })
              }
              disabled={form.target_type === "mcp_stdio"}
            />
            <span className="mt-1 block text-xs text-slate-500">
              Indiquez l’URL réellement appelée ; les identifiants intégrés à
              l’URL sont interdits.
            </span>
          </label>
          <label className="col-span-2">
            <span className="label">Configuration de la requête (JSON)</span>
            <textarea
              className="input min-h-32 font-mono text-xs"
              value={form.configuration}
              onChange={(event) =>
                setForm({ ...form, configuration: event.target.value })
              }
            />
            <span className="mt-1 block text-xs text-slate-500">
              Conservez les identifiants dans une variable d’environnement.{" "}
              {configurationHelp[form.target_type]}
            </span>
          </label>
          {["chatbot", "agent_lab"].includes(form.target_type) && (
            <div className="col-span-2 rounded-lg border border-cyan/20 bg-cyan/5 p-4 text-xs text-slate-300">
              <p className="font-medium text-cyan">Formats et détection</p>
              <p className="mt-1">
                <code>response_format</code> accepte <code>auto</code>,{" "}
                <code>json</code>, <code>ndjson</code>, <code>sse</code>,{" "}
                <code>openai</code> et <code>ollama</code>. En mode{" "}
                <code>auto</code>, AgentSec s’appuie sur le Content-Type et
                normalise la réponse, les événements et les appels d’outils.
              </p>
            </div>
          )}
          <label className="col-span-2 flex items-center gap-2 text-sm text-slate-300">
            <input
              type="checkbox"
              checked={form.remote_authorized}
              onChange={(event) =>
                setForm({ ...form, remote_authorized: event.target.checked })
              }
            />
            Je confirme que les connexions à cette cible distante sont
            autorisées par le périmètre.
          </label>
          <div className="col-span-2 flex justify-end">
            <button className="btn-primary">
              {editing ? "Enregistrer les modifications" : "Enregistrer"}
            </button>
          </div>
        </form>
      )}
      {testResult && (
        <section className="panel mb-5 p-5">
          <div className="flex items-center">
            <h2 className="font-semibold text-white">
              Test de connexion réussi ·{" "}
              {testResult.protocol || "protocole détecté"}
            </h2>
            {editing &&
              Object.keys(testResult.suggested_configuration || {}).length >
                0 && (
                <button
                  className="btn ml-auto"
                  onClick={() => void applySuggestion()}
                >
                  Appliquer la configuration détectée
                </button>
              )}
          </div>
          <pre className="mt-3 max-h-80 overflow-auto whitespace-pre-wrap rounded bg-slate-950 p-3 text-xs text-slate-300">
            {JSON.stringify(testResult, null, 2)}
          </pre>
        </section>
      )}
      {targets.loading ? (
        <Loading />
      ) : targets.data?.length ? (
        <div className="space-y-4">
          {projectTargets.map(({ project, items }, index) => (
            <ProjectDisclosure key={project.id} project={project} count={items.length} label={items.length > 1 ? "cibles" : "cible"} defaultOpen={index === 0}>
              <div className="table-wrap rounded-none border-0"><table className="table"><thead><tr><th>Nom</th><th>Type</th><th>URL / commande</th><th>Format</th><th>Actions</th></tr></thead><tbody>
                {items.map((target) => <tr key={target.id}><td className="text-white">{target.name}</td><td>{typeLabel[target.target_type] || target.target_type}</td><td className="max-w-sm truncate font-mono text-xs">{target.endpoint || String(target.configuration.command || "—")}</td><td>{String(target.configuration.response_format || "auto")}</td><td><div className="flex gap-3"><button title="Tester la connexion" disabled={testing === target.id} onClick={() => void test(target)} className="text-slate-500 hover:text-cyan"><Radio size={16} /></button><button title="Modifier" onClick={() => edit(target)} className="text-slate-500 hover:text-cyan"><Edit3 size={16} /></button><button title="Supprimer" onClick={() => void remove(target.id)} className="text-slate-500 hover:text-red-400"><Trash2 size={16} /></button></div></td></tr>)}
              </tbody></table></div>
            </ProjectDisclosure>
          ))}
        </div>
      ) : (
        <Empty title="Aucune cible" />
      )}
    </>
  );
}
