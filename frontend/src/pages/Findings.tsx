import { useState } from "react";
import { Trash2 } from "lucide-react";
import { Empty, ErrorBox, Loading, PageHeader, Severity, Status } from "../components/ui";
import { ProjectDisclosure } from "../components/ProjectDisclosure";
import { useApi } from "../hooks/useApi";
import { api } from "../lib/api";
import type { Audit, Finding, Project } from "../types";

interface FindingDetail {
  finding: Finding;
  audit: Audit | null;
  executions: Array<Record<string, unknown>>;
  evidence: Array<Record<string, unknown>>;
  occurrences: Array<Record<string, unknown>>;
}

function Field({ label, value, code = false }: { label: string; value: unknown; code?: boolean }) {
  if (value === undefined || value === null || value === "" || (Array.isArray(value) && !value.length)) return null;
  const text = typeof value === "string" ? value : JSON.stringify(value, null, 2);
  return <div><p className="label">{label}</p>{code ? <pre className="max-h-72 overflow-auto whitespace-pre-wrap break-all rounded bg-slate-950 p-3 text-xs text-slate-200">{text}</pre> : <p className="whitespace-pre-wrap text-sm text-slate-300">{text}</p>}</div>;
}

function Payloads({ executions }: { executions: Array<Record<string, unknown>> }) {
  const payloads = executions.flatMap((execution) => {
    const request = (execution.request_data || {}) as Record<string, unknown>;
    const turns = Array.isArray(request.turns) ? request.turns as Array<Record<string, unknown>> : [];
    if (turns.length) return turns.map((turn) => ({ scenario: execution.scenario_id, step: turn.step, payload: turn.exact_payload_sent }));
    return request.messages ? [{ scenario: execution.scenario_id, step: 1, payload: { messages: request.messages } }] : [];
  });
  if (!payloads.length) return null;
  return <div><p className="label">Payload</p><div className="space-y-3">{payloads.map((item, index) => <div key={index}><p className="mb-1 text-xs text-slate-500">{String(item.scenario || "Exécution")} · {String(item.step || index + 1)}</p><pre className="max-h-80 overflow-auto whitespace-pre-wrap break-all rounded border border-cyan/20 bg-slate-950 p-3 text-xs text-slate-200">{JSON.stringify(item.payload, null, 2)}</pre></div>)}</div></div>;
}

export default function Findings() {
  const { data, error, loading, reload } = useApi<Finding[]>("/findings");
  const projects = useApi<Project[]>("/projects");
  const [selected, setSelected] = useState<Finding>();
  const [detail, setDetail] = useState<FindingDetail>();
  const [detailError, setDetailError] = useState("");

  async function open(finding: Finding) {
    setSelected(finding); setDetail(undefined); setDetailError("");
    try { setDetail(await api<FindingDetail>(`/findings/${finding.id}/detail`)); }
    catch (caught) { setDetailError(caught instanceof Error ? caught.message : String(caught)); }
  }

  async function status(id: string, value: string) {
    const updated = await api<Finding>(`/findings/${id}`, { method: "PUT", body: JSON.stringify({ status: value }) });
    setSelected(updated);
    if (detail) setDetail({ ...detail, finding: updated });
    await reload();
  }

  async function removeFinding(finding: Finding) {
    if (!confirm(`Supprimer définitivement le finding « ${finding.title} » et son historique de constats ? Cette action est irréversible.`)) return;
    try {
      setDetailError("");
      await api(`/findings/${finding.id}?confirm_delete=true`, {method:"DELETE"});
      if (selected?.id === finding.id) {setSelected(undefined);setDetail(undefined);}
      await reload();
    } catch(caught) {setDetailError(caught instanceof Error ? caught.message : String(caught));}
  }

  const projectFindings = (projects.data || [])
    .map((project) => ({ project, items: (data || []).filter((finding) => finding.project_id === project.id) }))
    .filter((group) => group.items.length);

  return <>
    <PageHeader title="Findings" description="Observations, risques potentiels et vulnérabilités confirmées avec payloads, preuves et historique de modifications." />
    {(error || (!selected && detailError)) && <ErrorBox message={error || detailError} />}
    {loading ? <Loading /> : data?.length ? <div className="grid grid-cols-5 gap-5">
      <div className="col-span-3 space-y-4">{projectFindings.map(({ project, items }, index) => <ProjectDisclosure key={project.id} project={project} count={items.length} label={items.length > 1 ? "findings" : "finding"} defaultOpen={index === 0}><div className="table-wrap rounded-none border-0"><table className="table"><thead><tr><th>Titre</th><th>Sévérité</th><th>Classification</th><th>Statut</th><th>Actions</th></tr></thead><tbody>{items.map((finding) => <tr key={finding.id} className="cursor-pointer hover:bg-slate-800/40" onClick={() => void open(finding)}><td className="font-medium text-white">{finding.title}{finding.occurrence_count>1&&<span className="ml-2 rounded bg-slate-700 px-2 py-0.5 text-xs text-cyan">×{finding.occurrence_count}</span>}</td><td><Severity value={finding.severity} /></td><td>{finding.classification}</td><td><Status value={finding.status} /></td><td><button type="button" title="Supprimer ce finding" aria-label={`Supprimer ${finding.title}`} className="rounded p-2 text-red-400 hover:bg-red-950/50" onClick={event=>{event.stopPropagation();void removeFinding(finding)}}><Trash2 size={16}/></button></td></tr>)}</tbody></table></div></ProjectDisclosure>)}</div>
      <aside className="card col-span-2 max-h-[calc(100vh-170px)] overflow-auto">{selected ? <div className="space-y-5"><div className="flex items-start justify-between gap-2"><Severity value={selected.severity} /><button type="button" className="btn text-xs text-red-300" onClick={()=>void removeFinding(selected)}><Trash2 size={14}/>Supprimer</button></div><div><h3 className="mt-3 text-lg font-semibold text-white">{selected.title}</h3><p className="mt-1 break-all font-mono text-[10px] text-slate-600">{selected.id}</p><p className="mt-1 text-xs text-slate-500">{selected.component} · confiance {selected.confidence}</p></div>{detailError && <ErrorBox message={detailError} />}<Field label="Description" value={selected.description} /><Field label="Impact" value={selected.impact} /><Field label="Conditions d’exploitation" value={selected.exploitation_conditions} /><Field label="Étapes de reproduction" value={selected.reproduction_steps} />{detail ? <Payloads executions={detail.executions} /> : !detailError && <Loading />}<Field label="Résultat observé" value={selected.observed_result} code /><Field label="Résultat attendu" value={selected.expected_result} /><Field label="Première observation" value={selected.first_seen} /><Field label="Dernière observation" value={selected.last_seen} /><Field label="Occurrences" value={detail?.occurrences} code /><Field label="Preuves" value={detail?.evidence} code /><Field label="Appels, réponses et analyse" value={detail?.executions.map((execution) => ({ response_data: execution.response_data, analysis: execution.analysis }))} code /><Field label="Référentiels" value={selected.frameworks} code /><Field label="Recommandation" value={selected.recommendation} /><label><span className="label">Statut</span><select className="input" value={selected.status} onChange={(event) => void status(selected.id, event.target.value)}>{["Open", "Confirmed", "False Positive", "Accepted Risk", "Remediated"].map((value) => <option key={value}>{value}</option>)}</select></label></div> : <div className="grid h-full min-h-64 place-items-center text-sm text-slate-500">Sélectionnez un finding</div>}</aside>
    </div> : <Empty title="Aucun finding" detail="Les scanners n’inventent pas de résultat : cette vue reste vide avant un audit ou une saisie manuelle." />}
  </>;
}
