import { Download, Search, X } from "lucide-react";
import { useMemo, useState } from "react";
import { ErrorBox, Status } from "./ui";
import { MCPResultView } from "./MCPResultView";
import { api, downloadApi } from "../lib/api";
import type { Audit, AuditDetail } from "../types";

interface Props {
  audits: Audit[];
  title?: string;
}

export function AuditHistory({audits,title="Historique des audits"}:Props){
  const [search,setSearch]=useState("");
  const [status,setStatus]=useState("");
  const [sort,setSort]=useState<"newest"|"oldest">("newest");
  const [detail,setDetail]=useState<AuditDetail>();
  const [error,setError]=useState("");
  const filtered=useMemo(()=>audits.filter(item=>(!status||item.status===status)&&(!search||`${item.id} ${item.audit_type} ${JSON.stringify(item.configuration)}`.toLowerCase().includes(search.toLowerCase()))).sort((a,b)=>(sort==="newest"?-1:1)*(new Date(a.created_at).getTime()-new Date(b.created_at).getTime())),[audits,search,status,sort]);

  async function open(id:string){setError("");try{setDetail(await api<AuditDetail>(`/audits/${id}/detail`))}catch(caught){setError(caught instanceof Error?caught.message:String(caught))}}
  async function download(id:string,format:"json"|"pdf"){
    try{const blob=await downloadApi(`/audits/${id}/export?format=${format}`);const href=URL.createObjectURL(blob);const anchor=document.createElement("a");anchor.href=href;anchor.download=`audit-${id}.${format}`;anchor.click();URL.revokeObjectURL(href)}catch(caught){setError(caught instanceof Error?caught.message:String(caught))}
  }
  if(!audits.length)return null;
  return <section className="mt-7">
    <div className="mb-3 flex items-center gap-3"><h2 className="text-lg font-semibold text-white">{title}</h2><span className="rounded-full bg-slate-800 px-2 py-0.5 text-xs text-slate-400">{filtered.length}</span></div>
    {error&&<ErrorBox message={error}/>}<div className="mb-3 grid grid-cols-[1fr_180px_180px] gap-3"><label className="relative"><Search className="absolute left-3 top-3 text-slate-500" size={15}/><input aria-label="Rechercher les audits" className="input pl-9" placeholder="ID, type, scénario…" value={search} onChange={event=>setSearch(event.target.value)}/></label><select aria-label="Filtrer par statut" className="input" value={status} onChange={event=>setStatus(event.target.value)}><option value="">Tous les statuts</option>{["queued","running","completed","failed","cancelled"].map(value=><option key={value}>{value}</option>)}</select><select aria-label="Trier les audits" className="input" value={sort} onChange={event=>setSort(event.target.value as "newest"|"oldest")}><option value="newest">Plus récents</option><option value="oldest">Plus anciens</option></select></div>
    <div className="table-wrap"><table className="table"><thead><tr><th>Audit</th><th>Scénario / catégorie</th><th>État</th><th>Mode</th><th>Date</th></tr></thead><tbody>{filtered.map(item=><tr key={item.id} className="cursor-pointer hover:bg-slate-800/50" onClick={()=>void open(item.id)}><td><p className="text-white">{item.audit_type}</p><p className="font-mono text-[10px] text-slate-600">{item.id}</p></td><td>{String(item.configuration.scenario_id||item.configuration.category||item.configuration.name||"—")}</td><td><Status value={item.status}/></td><td>{item.passive?"Passif":"Actif confirmé"}</td><td>{new Date(item.created_at).toLocaleString()}</td></tr>)}</tbody></table></div>
    {detail&&<div role="dialog" aria-modal="true" className="fixed inset-0 z-50 grid place-items-center bg-black/70 p-8" onMouseDown={()=>setDetail(undefined)}><article className="panel max-h-[90vh] w-full max-w-5xl overflow-auto p-6" onMouseDown={event=>event.stopPropagation()}><div className="mb-5 flex items-start"><div><h2 className="text-xl font-semibold text-white">Détail de l’audit</h2><p className="font-mono text-xs text-slate-500">{detail.audit.id}</p></div><div className="ml-auto flex gap-2"><button className="btn" onClick={()=>void download(detail.audit.id,"json")}><Download size={15}/>JSON</button><button className="btn" onClick={()=>void download(detail.audit.id,"pdf")}><Download size={15}/>PDF</button><button aria-label="Fermer" className="btn" onClick={()=>setDetail(undefined)}><X size={16}/></button></div></div>{detail.historical_data_notice&&<p className="mb-4 rounded border border-amber-800 bg-amber-950/30 p-3 text-sm text-amber-200">{detail.historical_data_notice}</p>}{detail.audit.audit_type==="mcp_security"&&<MCPResultView summary={detail.audit.summary}/>}<DetailSection title="Audit et configuration" value={detail.audit}/><DetailSection title="Cible" value={detail.target}/><ExecutionSection executions={detail.executions}/><DetailSection title="Événements et outils observés" value={detail.events}/><DetailSection title="Preuves" value={detail.evidence}/><DetailSection title="Findings" value={detail.findings}/></article></div>}
  </section>
}

function DetailSection({title,value}:{title:string;value:unknown}){return <details className="mb-3 rounded-lg border border-slate-800 bg-slate-950/40" open><summary className="cursor-pointer px-4 py-3 text-sm font-medium text-cyan">{title}</summary><pre className="max-h-96 overflow-auto whitespace-pre-wrap border-t border-slate-800 p-4 text-xs text-slate-300">{JSON.stringify(value,null,2)}</pre></details>}

function ExecutionSection({executions}:{executions:Array<Record<string,unknown>>}){
  return <details className="mb-3 rounded-lg border border-slate-800 bg-slate-950/40" open><summary className="cursor-pointer px-4 py-3 text-sm font-medium text-cyan">Exécutions</summary><div className="space-y-4 border-t border-slate-800 p-4">{executions.map((execution,index)=>{
    const request=(execution.request_data||{}) as Record<string,unknown>;
    const recordedTurns=Array.isArray(request.turns)?request.turns as Array<Record<string,unknown>>:[];
    const turns=recordedTurns.length?recordedTurns:(request.messages?[{step:1,exact_payload_sent:{messages:request.messages},historical:true}]:[]);
    return <section key={String(execution.id||index)} className="rounded-lg border border-slate-800 bg-slate-950 p-4"><div className="mb-3 flex items-center gap-3"><span className="rounded bg-slate-800 px-2 py-1 font-mono text-xs text-cyan">{String(execution.status||"—")}</span><span className="text-sm text-slate-300">{String(execution.scenario_id||"Exécution")}</span></div>{turns.map((turn,turnIndex)=><div key={turnIndex} className="mb-4"><p className="label">Payload</p><pre className="max-h-80 overflow-auto whitespace-pre-wrap rounded bg-black p-3 text-xs text-slate-200">{JSON.stringify(turn.exact_payload_sent,null,2)}</pre>{Boolean(turn.request_url)&&<p className="mt-2 break-all font-mono text-[10px] text-slate-600">{String(turn.request_url)}</p>}{Boolean(turn.historical)&&<p className="mt-2 text-xs text-slate-500">Requête enregistrée par une version antérieure ; l’enveloppe de transport complète n’était pas conservée.</p>}</div>)}{!turns.length&&<p className="text-xs text-slate-500">Aucun payload n’a été conservé pour cette exécution historique.</p>}<p className="label">Réponse et analyse</p><pre className="max-h-80 overflow-auto whitespace-pre-wrap rounded bg-black p-3 text-xs text-slate-200">{JSON.stringify({response_data:execution.response_data,analysis:execution.analysis},null,2)}</pre></section>
  })}</div></details>
}
