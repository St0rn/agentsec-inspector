import { Database, FileWarning, Plus } from "lucide-react";
import { RAGActivePanel } from "../components/RAGActivePanel";
import { useState } from "react";
import { Empty, ErrorBox, PageHeader } from "../components/ui";
import { useApi } from "../hooks/useApi";
import { api } from "../lib/api";
import type { Project } from "../types";

interface RAGDocument {
  id: string;
  name: string;
  sha256: string;
  is_lab_document: boolean;
  instruction_indicators: string[];
  created_at: string;
  document_format: "txt" | "markdown" | "pdf";
  source: string;
  test_objective: string;
  markers: string[];
  ingestion_status: string;
}
interface RAGTrace {
  id: string;
  query: string;
  retrieved_chunks: Array<Record<string, unknown>>;
  llm_context: string | null;
  response: string;
  expected_response: string;
  telemetry_available: boolean;
  analysis: Record<string, unknown>;
  created_at: string;
}

export default function RagSecurity() {
  const projects = useApi<Project[]>("/projects");
  const [project, setProject] = useState("");
  const documents = useApi<RAGDocument[]>(
    `/rag/documents?project_id=${project || "none"}`,
  );
  const traces = useApi<RAGTrace[]>(
    `/rag/traces?project_id=${project || "none"}`,
  );
  const [error, setError] = useState("");
  const [doc, setDoc] = useState({
    name: "",
    content: "",
    source: "auditor_import",
    test_objective: "",
    markers: "AGENTSEC_CANARY_RAG",
    is_lab_document: false,
  });
  const [fileDocument, setFileDocument] = useState<{
    content_base64: string;
    document_format: "txt" | "markdown" | "pdf";
  }>();
  const [trace, setTrace] = useState({
    query: "",
    retrieved_chunks: "[]",
    llm_context: "",
    response: "",
    expected_response: "",
    telemetry_available: false,
  });
  async function addDocument(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    try {
      await api("/rag/documents", {
        method: "POST",
        body: JSON.stringify({
          project_id: project,
          name: doc.name,
          content: fileDocument ? "" : doc.content,
          content_base64: fileDocument?.content_base64 || null,
          document_format: fileDocument?.document_format || "txt",
          source: doc.source,
          test_objective: doc.test_objective,
          markers: doc.markers
            .split(",")
            .map((item) => item.trim())
            .filter(Boolean),
          metadata: {},
          is_lab_document: doc.is_lab_document,
        }),
      });
      setDoc({
        name: "",
        content: "",
        source: "auditor_import",
        test_objective: "",
        markers: "AGENTSEC_CANARY_RAG",
        is_lab_document: false,
      });
      setFileDocument(undefined);
      await documents.reload();
    } catch (x) {
      setError(x instanceof Error ? x.message : String(x));
    }
  }
  async function selectDocumentFile(file?: File) {
    if (!file) {
      setFileDocument(undefined);
      return;
    }
    if (file.size > 2_000_000) {
      setError("The selected document exceeds the 2 MB import limit.");
      return;
    }
    const extension = file.name.split(".").pop()?.toLowerCase();
    const format =
      extension === "pdf" ? "pdf" : extension === "md" ? "markdown" : "txt";
    const bytes = new Uint8Array(await file.arrayBuffer());
    let binary = "";
    for (const byte of bytes) binary += String.fromCharCode(byte);
    setFileDocument({ content_base64: btoa(binary), document_format: format });
    setDoc((current) => ({
      ...current,
      name: current.name || file.name,
      content: "",
    }));
  }
  async function addTrace(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    try {
      await api("/rag/traces", {
        method: "POST",
        body: JSON.stringify({
          project_id: project,
          ...trace,
          retrieved_chunks: JSON.parse(trace.retrieved_chunks),
          llm_context: trace.llm_context || null,
        }),
      });
      setTrace({ ...trace, query: "", response: "" });
      await traces.reload();
    } catch (x) {
      setError(x instanceof Error ? x.message : String(x));
    }
  }
  return (
    <>
      <PageHeader
        title="RAG Security Auditor"
        description="Inspection de documents et traces réellement importés. Les chunks et le contexte ne sont affichés que si la télémétrie est explicitement disponible."
      />
      {error && <ErrorBox message={error} />}
      <label className="mb-5 block max-w-xl">
        <span className="label">Projet</span>
        <select
          className="input"
          value={project}
          onChange={(e) => setProject(e.target.value)}
        >
          <option value="">Sélectionner…</option>
          {projects.data?.map((p) => (
            <option key={p.id} value={p.id}>
              {p.client_name} — {p.engagement_name}
            </option>
          ))}
        </select>
      </label>
      <RAGActivePanel
        projectId={project}
        documents={documents.data || []}
        onComplete={async () => {
          await traces.reload();
        }}
      />
      <div className="grid grid-cols-2 gap-5">
        <form className="card space-y-3" onSubmit={addDocument}>
          <h3 className="flex items-center gap-2 font-semibold text-white">
            <FileWarning className="text-cyan" size={18} />
            Importer un document
          </h3>
          <label>
            <span className="label">Nom</span>
            <input
              className="input"
              required
              value={doc.name}
              onChange={(e) => setDoc({ ...doc, name: e.target.value })}
            />
          </label>
          <label>
            <span className="label">Contenu de test</span>
            <textarea
              className="input min-h-28"
              required={!fileDocument}
              disabled={Boolean(fileDocument)}
              value={doc.content}
              onChange={(e) => setDoc({ ...doc, content: e.target.value })}
            />
          </label>
          <label>
            <span className="label">TXT, Markdown or PDF file</span>
            <input
              aria-label="RAG document file"
              className="input"
              type="file"
              accept=".txt,.md,.markdown,.pdf,text/plain,text/markdown,application/pdf"
              onChange={(event) =>
                void selectDocumentFile(event.target.files?.[0])
              }
            />
            {fileDocument && (
              <span className="mt-1 block text-xs text-cyan">
                Secure local extraction: {fileDocument.document_format}
              </span>
            )}
          </label>
          <div className="grid grid-cols-2 gap-3">
            <label>
              <span className="label">Source</span>
              <input
                className="input"
                value={doc.source}
                onChange={(event) =>
                  setDoc({ ...doc, source: event.target.value })
                }
              />
            </label>
            <label>
              <span className="label">Synthetic markers (comma-separated)</span>
              <input
                className="input font-mono text-xs"
                value={doc.markers}
                onChange={(event) =>
                  setDoc({ ...doc, markers: event.target.value })
                }
              />
            </label>
          </div>
          <label>
            <span className="label">Test objective</span>
            <textarea
              className="input min-h-16"
              value={doc.test_objective}
              onChange={(event) =>
                setDoc({ ...doc, test_objective: event.target.value })
              }
            />
          </label>
          <label className="flex gap-2 text-sm text-slate-300">
            <input
              type="checkbox"
              checked={doc.is_lab_document}
              onChange={(e) =>
                setDoc({ ...doc, is_lab_document: e.target.checked })
              }
            />
            Document de laboratoire contrôlé
          </label>
          <button disabled={!project} className="btn-primary">
            <Plus size={15} />
            Importer
          </button>
        </form>
        <form className="card space-y-3" onSubmit={addTrace}>
          <h3 className="flex items-center gap-2 font-semibold text-white">
            <Database className="text-cyan" size={18} />
            Importer une trace
          </h3>
          <input
            className="input"
            required
            placeholder="Requête"
            value={trace.query}
            onChange={(e) => setTrace({ ...trace, query: e.target.value })}
          />
          <textarea
            className="input min-h-16 font-mono text-xs"
            placeholder='Chunks JSON, ex. [{"content":"…"}]'
            value={trace.retrieved_chunks}
            onChange={(e) =>
              setTrace({ ...trace, retrieved_chunks: e.target.value })
            }
          />
          <textarea
            className="input min-h-16"
            placeholder="Contexte LLM observé (optionnel)"
            value={trace.llm_context}
            onChange={(e) =>
              setTrace({ ...trace, llm_context: e.target.value })
            }
          />
          <textarea
            className="input min-h-16"
            required
            placeholder="Réponse obtenue"
            value={trace.response}
            onChange={(e) => setTrace({ ...trace, response: e.target.value })}
          />
          <textarea
            className="input min-h-16"
            placeholder="Réponse attendue"
            value={trace.expected_response}
            onChange={(e) =>
              setTrace({ ...trace, expected_response: e.target.value })
            }
          />
          <label className="flex gap-2 text-sm text-slate-300">
            <input
              type="checkbox"
              checked={trace.telemetry_available}
              onChange={(e) =>
                setTrace({ ...trace, telemetry_available: e.target.checked })
              }
            />
            Les chunks et le contexte proviennent d’une télémétrie réelle
          </label>
          <button disabled={!project} className="btn-primary">
            Analyser la trace
          </button>
        </form>
      </div>
      <div className="mt-6 grid grid-cols-4 gap-3">
        <Step title="Document" />
        <Step title="Retrieval" />
        <Step title="Contexte LLM" />
        <Step title="Réponse" />
      </div>
      <div className="mt-5 grid grid-cols-2 gap-5">
        {documents.data?.length ? (
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>Document</th>
                  <th>Indicateurs</th>
                  <th>Source</th>
                  <th>Format / ingestion</th>
                </tr>
              </thead>
              <tbody>
                {documents.data.map((d) => (
                  <tr key={d.id}>
                    <td>{d.name}</td>
                    <td>{d.instruction_indicators.length}</td>
                    <td>{d.source}</td>
                    <td>
                      {d.document_format} · {d.ingestion_status}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <Empty title="Aucun document" />
        )}
        {traces.data?.length ? (
          <div className="space-y-3">
            {traces.data.map((t) => (
              <article className="card" key={t.id}>
                <p className="font-medium text-white">{t.query}</p>
                <p className="mt-1 text-xs text-slate-500">
                  {t.telemetry_available
                    ? "Télémétrie fournie"
                    : "Réponse uniquement"}
                </p>
                <p className="mt-3 text-sm text-slate-300">{t.response}</p>
                <pre className="mt-3 overflow-auto rounded bg-slate-950 p-2 text-xs">
                  {JSON.stringify(t.analysis, null, 2)}
                </pre>
              </article>
            ))}
          </div>
        ) : (
          <Empty title="Aucune trace" />
        )}
      </div>
    </>
  );
}
function Step({ title }: { title: string }) {
  return <div className="card text-center text-sm text-slate-300">{title}</div>;
}
