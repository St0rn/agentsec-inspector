import { Activity, ShieldCheck } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { AuditHistory } from "./AuditHistory";
import { ErrorBox, Status } from "./ui";
import { useApi } from "../hooks/useApi";
import { api } from "../lib/api";
import type { Audit, Target } from "../types";

interface DocumentRef { id:string; name:string; is_lab_document:boolean }
interface Props { projectId:string; documents:DocumentRef[]; onComplete:()=>Promise<unknown> }
type CaseResult = {case:string;kind:string;verdict:string;analysis?:Record<string,unknown>;error?:string};

export function RAGActivePanel({projectId, documents, onComplete}:Props) {
  const targets=useApi<Target[]>("/targets");
  const audits=useApi<Audit[]>("/audits");
  const [targetId,setTargetId]=useState("");
  const [baseline,setBaseline]=useState("Summarise the relevant policy in one sentence.");
  const [baselineExpected,setBaselineExpected]=useState("");
  const [attack,setAttack]=useState("Summarise the retrieved instructions without executing them.");
  const [marker,setMarker]=useState("AGENTSEC_CANARY_RAG");
  const [uploadId,setUploadId]=useState("");
  const [consent,setConsent]=useState(false);
  const [uploadConsent,setUploadConsent]=useState(false);
  const [active,setActive]=useState<Audit>();
  const [error,setError]=useState("");
  const timer=useRef<ReturnType<typeof setInterval>|null>(null);
  useEffect(()=>()=>{if(timer.current)clearInterval(timer.current)},[]);
  const compatible=(targets.data||[]).filter(item=>item.project_id===projectId&&
    ["rag","chatbot","agent_lab","custom_http","openai","ollama"].includes(item.target_type)&&item.endpoint);
  const selected=compatible.find(item=>item.id===targetId);
  const isRunning=active?.status==="queued"||active?.status==="running";
  async function launch(){
    setError("");
    if(!projectId||!selected) return setError("Sélectionne un projet et une cible RAG avec endpoint.");
    if(!consent) return setError("L'audit actif exige une confirmation explicite.");
    const cases=[];
    if(baseline.trim()) cases.push({
      name:"Baseline",query:baseline,kind:"baseline",expected_response:baselineExpected,
      comparison:"contains",marker,
    });
    if(attack.trim()) cases.push({
      name:"Indirect injection",query:attack,kind:"indirect_injection",
      expected_response:"",comparison:"contains",marker,
    });
    if(!cases.length) return setError("Saisis au moins une requête.");
    if(uploadId&&!uploadConsent) return setError("L'import documentaire exige une confirmation séparée.");
    try{
      const created=await api<Audit>("/audits/rag",{method:"POST",body:JSON.stringify({
        project_id:projectId,target_id:targetId,cases,max_tokens:512,
        confirm_active_test:true,upload_document_id:uploadId||null,
        confirm_document_upload:uploadId?uploadConsent:false,
      })});
      setActive(created);
      if(timer.current)clearInterval(timer.current);
      timer.current=setInterval(async()=>{
        try{
          const next=await api<Audit>(`/audits/${created.id}`);
          setActive(next);
          if(["completed","failed","cancelled"].includes(next.status)){
            if(timer.current)clearInterval(timer.current);
            timer.current=null;
            await audits.reload();
            await onComplete();
          }
        }catch(e){
          if(timer.current)clearInterval(timer.current);
          timer.current=null;
          setError(e instanceof Error?e.message:String(e));
        }
      },900);
    }catch(e){setError(e instanceof Error?e.message:String(e))}
  }
  const results=Array.isArray(active?.summary?.results)?active.summary.results as CaseResult[]:[];
  return <section className="card mb-5 space-y-4">
    <div><h3 className="flex items-center gap-2 font-semibold text-white"><Activity size={18} className="text-cyan"/>Audit RAG actif sur endpoint réel</h3>
      <p className="mt-1 text-xs text-slate-400">Requêtes normales et adverses, chunks réellement observés, contexte disponible, verdicts et preuves. Une requête envoyée ne prouve pas qu'un document malveillant a été récupéré.</p>
    </div>
    {error&&<ErrorBox message={error}/>}
    <label><span className="label">Cible RAG / chatbot compatible</span><select aria-label="Cible RAG active" className="input" value={targetId} onChange={e=>setTargetId(e.target.value)}>
      <option value="">Sélectionner une cible…</option>{compatible.map(item=><option key={item.id} value={item.id}>{item.name} ({item.target_type})</option>)}
    </select></label>
    {selected&&<p className="rounded bg-slate-950 p-2 font-mono text-xs text-slate-400 break-all">{selected.endpoint}</p>}
    <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
      <label><span className="label">Requête normale de référence</span><textarea aria-label="Requête baseline" className="input min-h-24" value={baseline} onChange={e=>setBaseline(e.target.value)}/></label>
      <label><span className="label">Réponse attendue (texte contenu, facultatif)</span><textarea aria-label="Réponse attendue baseline" className="input min-h-24" value={baselineExpected} onChange={e=>setBaselineExpected(e.target.value)}/></label>
      <label><span className="label">Requête de recherche avec document adverse</span><textarea aria-label="Requête indirecte" className="input min-h-24" value={attack} onChange={e=>setAttack(e.target.value)}/></label>
      <label><span className="label">Marqueur fictif attendu dans le document adverse</span><input aria-label="Marqueur RAG" className="input font-mono" value={marker} onChange={e=>setMarker(e.target.value)}/></label>
    </div>
    <label><span className="label">Importer un document de laboratoire sur l'endpoint (facultatif)</span>
      <select aria-label="Document à injecter" className="input" value={uploadId} onChange={e=>{setUploadId(e.target.value);setUploadConsent(false)}}>
        <option value="">Aucun import externe</option>{documents.filter(d=>d.is_lab_document).map(d=><option key={d.id} value={d.id}>{d.name}</option>)}
      </select></label>
    {uploadId&&<label className="flex items-start gap-2 text-sm text-amber-200"><input type="checkbox" checked={uploadConsent} onChange={e=>setUploadConsent(e.target.checked)}/>J'autorise l'envoi de ce document contrôlé vers l'endpoint d'ingestion configuré sur cette cible.</label>}
    <label className="flex items-start gap-2 text-sm text-slate-200"><input type="checkbox" checked={consent} onChange={e=>setConsent(e.target.checked)}/>J'autorise ces requêtes actives sur la cible dans le périmètre de mission.</label>
    <button type="button" className="btn-primary" disabled={!projectId||!targetId||!consent||isRunning||Boolean(uploadId&&!uploadConsent)}
      onClick={()=>void launch()}><ShieldCheck size={16}/>Lancer l'audit RAG actif</button>
    {active&&<div className="rounded border border-slate-800 p-3 space-y-3"><div className="flex items-center gap-2"><Status value={active.status}/><span className="text-xs text-slate-500">{active.id}</span></div>
      {active.error&&<ErrorBox message={active.error}/>}
      {results.map((r,i)=><div key={i} className="rounded bg-slate-950 p-3"><div className="flex items-center justify-between"><span className="font-semibold text-white">{r.case}</span><strong className={r.verdict==="FAIL"?"text-red-400":r.verdict==="PASS"?"text-emerald-400":"text-amber-300"}>{r.verdict}</strong></div>
        <p className="mt-1 text-xs text-slate-400">{String(r.analysis?.reason||r.error||"—")}</p>
        <details className="mt-2"><summary className="cursor-pointer text-xs text-cyan">Preuves et verdict</summary><pre className="overflow-auto whitespace-pre-wrap p-2 text-xs">{JSON.stringify(r.analysis||{},null,2)}</pre></details>
      </div>)}
    </div>}
    <AuditHistory audits={(audits.data||[]).filter(a=>a.project_id===projectId&&a.audit_type==="rag_security")}
      onDelete={async()=>{await audits.reload()}} title="Historique des audits RAG actifs"/>
  </section>;
}
