import { Download, Eye, FileJson, FileText, Save, ShieldCheck, X } from "lucide-react";
import { useMemo, useState } from "react";
import { Empty, ErrorBox, PageHeader } from "../components/ui";
import { ProjectDisclosure } from "../components/ProjectDisclosure";
import { useApi } from "../hooks/useApi";
import { api, downloadApi, textApi } from "../lib/api";
import type { Project } from "../types";

interface Report {
  id: string;
  project_id: string;
  report_type: string;
  language: string;
  format: string;
  template_name: string;
  filename: string;
  size_bytes: number;
  sha256: string;
  created_at: string;
}

interface FileSystemWritableFileStream {
  write(data: Blob): Promise<void>;
  close(): Promise<void>;
}

interface FileSystemFileHandle {
  createWritable(): Promise<FileSystemWritableFileStream>;
}

type SavePickerWindow = Window & {
  showSaveFilePicker?: (options: {
    suggestedName: string;
    types: Array<{ description: string; accept: Record<string, string[]> }>;
  }) => Promise<FileSystemFileHandle>;
};

const MIME: Record<string, string> = {
  html: "text/html",
  pdf: "application/pdf",
  json: "application/json",
};

function Select({ label, value, values, set }: { label: string; value: string; values: Array<[string, string]>; set: (value: string) => void }) {
  return <label><span className="label">{label}</span><select className="input" value={value} onChange={(event) => set(event.target.value)}>{values.map(([key, text]) => <option key={key} value={key}>{text}</option>)}</select></label>;
}

function humanSize(bytes: number) {
  if (!bytes) return "—";
  if (bytes < 1024) return `${bytes} o`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} Ko`;
  return `${(bytes / 1024 / 1024).toFixed(1)} Mo`;
}

function browserDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

export default function Reports() {
  const projects = useApi<Project[]>("/projects");
  const reports = useApi<Report[]>("/reports");
  const [form, setForm] = useState({ project_id: "", report_type: "technical", language: "fr", format: "html", template_name: "default" });
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [preview, setPreview] = useState<string>();
  const [busy, setBusy] = useState<"preview" | "generate" | "">("");
  const selectedProject = useMemo(() => projects.data?.find((item) => item.id === form.project_id), [projects.data, form.project_id]);
  const projectReports = useMemo(() => (projects.data || [])
    .map((project) => ({ project, items: (reports.data || []).filter((report) => report.project_id === project.id) }))
    .filter((group) => group.items.length), [projects.data, reports.data]);

  async function showPreview() {
    setError(""); setNotice(""); setBusy("preview");
    try {
      const html = await textApi("/reports/preview", { method: "POST", body: JSON.stringify(form) });
      setPreview(html);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : String(caught));
    } finally { setBusy(""); }
  }

  async function generate() {
    setError(""); setNotice(""); setBusy("generate");
    try {
      const created = await api<Report>("/reports", { method: "POST", body: JSON.stringify(form) });
      await reports.reload();
      setNotice(`Rapport ${created.format.toUpperCase()} généré. Empreinte SHA-256 : ${created.sha256}`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : String(caught));
    } finally { setBusy(""); }
  }

  async function saveReport(report: Report, chooseLocation: boolean) {
    setError(""); setNotice("");
    try {
      const blob = await downloadApi(`/reports/${report.id}/download`);
      const filename = report.filename || `agentsec-${report.report_type}-${report.language}.${report.format}`;
      const picker = (window as SavePickerWindow).showSaveFilePicker;
      if (chooseLocation && picker) {
        const handle = await picker({
          suggestedName: filename,
          types: [{ description: `AgentSec ${report.format.toUpperCase()}`, accept: { [MIME[report.format] || "application/octet-stream"]: [`.${report.format}`] } }],
        });
        const writable = await handle.createWritable();
        await writable.write(blob);
        await writable.close();
        setNotice(`Rapport enregistré : ${filename}`);
        return;
      }
      browserDownload(blob, filename);
      if (chooseLocation) setNotice("Le sélecteur natif n’est pas disponible sur cette plateforme ; le téléchargement standard a été utilisé.");
    } catch (caught) {
      if (caught instanceof DOMException && caught.name === "AbortError") return;
      setError(caught instanceof Error ? caught.message : String(caught));
    }
  }

  return <>
    <PageHeader title="Reporting Engine" description="Rapports techniques et exécutifs détaillés, prévisualisés avant export et générés uniquement à partir des données conservées dans le projet." />
    {error && <ErrorBox message={error} />}
    {notice && <div className="mb-5 rounded-lg border border-emerald-800 bg-emerald-950/30 p-3 text-sm text-emerald-300">{notice}</div>}
    <section className="card mb-6">
      <div className="mb-5 flex items-start gap-3"><div className="rounded-lg bg-cyan/10 p-2 text-cyan"><ShieldCheck size={22} /></div><div><h2 className="font-semibold text-white">Composer un rapport</h2><p className="mt-1 text-sm text-slate-400">La prévisualisation reprend les findings, preuves, requêtes, réponses, outils et résultats d’audit réellement enregistrés.</p></div></div>
      <div className="grid grid-cols-1 gap-4 xl:grid-cols-5">
        <label className="xl:col-span-2"><span className="label">Projet</span><select className="input" value={form.project_id} onChange={(event) => setForm({ ...form, project_id: event.target.value })}><option value="">Sélectionner…</option>{projects.data?.map((project) => <option key={project.id} value={project.id}>{project.client_name} — {project.engagement_name}</option>)}</select></label>
        <Select label="Type" value={form.report_type} values={[["technical", "Technique"], ["executive", "Exécutif"]]} set={(value) => setForm({ ...form, report_type: value })} />
        <Select label="Langue" value={form.language} values={[["fr", "Français"], ["en", "English"]]} set={(value) => setForm({ ...form, language: value })} />
        <Select label="Format" value={form.format} values={[["html", "HTML"], ["pdf", "PDF"], ["json", "JSON"]]} set={(value) => setForm({ ...form, format: value })} />
      </div>
      {selectedProject && <div className="mt-4 rounded-lg border border-slate-800 bg-slate-950/50 p-4 text-sm text-slate-400"><span className="font-semibold text-slate-200">{selectedProject.engagement_name}</span><span className="mx-2 text-slate-700">·</span>{selectedProject.authorized_scope}</div>}
      <div className="mt-5 flex flex-wrap justify-end gap-3"><button disabled={!form.project_id || busy !== ""} onClick={() => void showPreview()} className="btn"><Eye size={16} />{busy === "preview" ? "Préparation…" : "Prévisualiser"}</button><button disabled={!form.project_id || busy !== ""} onClick={() => void generate()} className="btn-primary"><FileText size={16} />{busy === "generate" ? "Génération…" : "Générer"}</button></div>
    </section>
    {reports.data?.length ? <div className="space-y-4">{projectReports.map(({ project, items }, index) => <ProjectDisclosure key={project.id} project={project} count={items.length} label={items.length > 1 ? "rapports" : "rapport"} defaultOpen={index === 0}><div className="table-wrap rounded-none border-0"><table className="table"><thead><tr><th>Rapport</th><th>Format</th><th>Taille</th><th>Empreinte SHA-256</th><th>Date</th><th></th></tr></thead><tbody>{items.map((report) => <tr key={report.id}><td><div className="flex items-center gap-2">{report.format === "json" ? <FileJson size={16} className="text-cyan" /> : <FileText size={16} className="text-cyan" />}<div><div className="font-medium text-white">{report.report_type === "technical" ? "Technique" : "Exécutif"} · {report.language.toUpperCase()}</div><div className="max-w-xs truncate text-xs text-slate-500">{report.filename}</div></div></div></td><td>{report.format.toUpperCase()}</td><td>{humanSize(report.size_bytes)}</td><td className="max-w-[220px] truncate font-mono text-xs" title={report.sha256}>{report.sha256}</td><td>{new Date(report.created_at).toLocaleString()}</td><td><div className="flex justify-end gap-2"><button className="btn px-3" onClick={() => void saveReport(report, false)}><Download size={14} />Télécharger</button><button className="btn px-3" onClick={() => void saveReport(report, true)}><Save size={14} />Enregistrer sous</button></div></td></tr>)}</tbody></table></div></ProjectDisclosure>)}</div> : <Empty title="Aucun rapport" detail="Sélectionnez un projet, prévisualisez le document, puis générez le format souhaité." />}
    {preview && <div role="dialog" aria-modal="true" aria-label="Prévisualisation du rapport" className="fixed inset-0 z-50 flex flex-col bg-black/80 p-4 lg:p-8" onMouseDown={() => setPreview(undefined)}><div className="mx-auto flex h-full w-full max-w-7xl flex-col overflow-hidden rounded-xl border border-slate-700 bg-slate-950 shadow-2xl" onMouseDown={(event) => event.stopPropagation()}><div className="flex items-center border-b border-slate-800 px-4 py-3"><Eye size={17} className="mr-2 text-cyan" /><div><p className="font-semibold text-white">Prévisualisation</p><p className="text-xs text-slate-500">Rendu HTML A4 · utilisez l’export PDF pour le document final paginé</p></div><button aria-label="Fermer" className="btn ml-auto px-3" onClick={() => setPreview(undefined)}><X size={16} /></button></div><iframe title="Prévisualisation du rapport" sandbox="" srcDoc={preview} className="h-full w-full bg-slate-200" /></div></div>}
  </>;
}
