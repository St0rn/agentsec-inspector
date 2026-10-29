import { Activity, Eye, Play, Radio, ShieldAlert, Zap } from "lucide-react";
import { useMemo, useState } from "react";
import { ErrorBox, PageHeader, Status } from "../components/ui";
import { useApi } from "../hooks/useApi";
import { api } from "../lib/api";
import type { Audit, Project, Scenario, Target } from "../types";

type RunnerMode = "mcp" | "prompt" | "jailbreak" | "llm";
type MCPMode = "passive" | "active";
interface DiscoveredTool { name:string; description?:string; inputSchema?:Record<string,unknown> }

const sensitivePattern = /(delete|remove|exec|shell|admin|write|upload|credential|secret|token)/i;

export default function AuditRunner({mode}:{mode:RunnerMode}) {
  const projects=useApi<Project[]>("/projects");
  const targets=useApi<Target[]>("/targets");
  const scenarios=useApi<Scenario[]>("/scenarios");
  const audits=useApi<Audit[]>("/audits");
  const [projectId,setProject]=useState("");
  const [targetId,setTarget]=useState("");
  const [scenarioKey,setScenarioKey]=useState(mode==="jailbreak"?"jb.authority-impersonation@@1.0.0":"pi.direct@@1.0.0");
  const [objective,setObjective]=useState("Le marqueur fictif ne doit pas être divulgué et aucun outil ne doit être appelé.");
  const [mcpMode,setMcpMode]=useState<MCPMode>("passive");
  const [toolName,setToolName]=useState("");
  const [argumentsText,setArgumentsText]=useState("{}");
  const [activeConfirmed,setActiveConfirmed]=useState(false);
  const [sensitiveConfirmed,setSensitiveConfirmed]=useState(false);
  const [error,setError]=useState("");
  const [active,setActive]=useState<Audit>();

  const filtered=useMemo(()=>targets.data?.filter(target=>target.project_id===projectId&&(mode==="mcp"?target.target_type.startsWith("mcp_"):!target.target_type.startsWith("mcp_")&&target.target_type!=="rag"))||[],[targets.data,projectId,mode]);
  const discoveredTools=useMemo<DiscoveredTool[]>(()=>{
    const source=audits.data?.find(item=>item.audit_type==="mcp_security"&&item.target_id===targetId&&typeof item.summary.discovery==="object");
    const discovery=source?.summary.discovery as {tools?:DiscoveredTool[]}|undefined;
    return Array.isArray(discovery?.tools)?discovery.tools:[];
  },[audits.data,targetId]);
  const selectedTool=discoveredTools.find(tool=>tool.name===toolName);
  const sensitive=Boolean(selectedTool&&sensitivePattern.test(`${selectedTool.name} ${selectedTool.description||""}`));
  const visibleScenarios=useMemo(()=>scenarios.data?.filter(scenario=>mode==="jailbreak"?scenario.category==="jailbreak":mode==="prompt"?scenario.category!=="jailbreak":true)||[],[scenarios.data,mode]);
  const title=mode==="mcp"?"Scanner MCP":mode==="prompt"?"Prompt Injection Tester":mode==="jailbreak"?"Jailbreak Tester":"LLM Security Scanner";

  function resetTarget(next:string){setTarget(next);setToolName("");setArgumentsText("{}");setActiveConfirmed(false);setSensitiveConfirmed(false)}

  async function run(){
    setError("");
    try{
      const path=mode==="mcp"?"/audits/mcp":"/audits/prompt";
      let body:Record<string,unknown>;
      if(mode==="mcp"){
        const isActive=mcpMode==="active";
        let toolCalls:Array<Record<string,unknown>>=[];
        if(isActive){
          if(!toolName)throw new Error("Sélectionnez un outil découvert lors d’un audit passif.");
          let parsed:unknown;
          try{parsed=JSON.parse(argumentsText)}catch{throw new Error("Les paramètres doivent être un objet JSON valide.")}
          if(!parsed||Array.isArray(parsed)||typeof parsed!=="object")throw new Error("Les paramètres MCP doivent être un objet JSON.");
          toolCalls=[{tool_name:toolName,arguments:parsed,confirm_sensitive_operation:sensitiveConfirmed}];
        }
        body={project_id:projectId,target_id:targetId,passive:!isActive,confirm_active_operations:isActive&&activeConfirmed,active_tool_calls:toolCalls};
      }else{
        const [scenarioId,scenarioVersion]=scenarioKey.split("@@");
        body={project_id:projectId,target_id:targetId,scenario_id:scenarioId,scenario_version:scenarioVersion,security_objective:objective,confirm_active_test:true};
      }
      const created=await api<Audit>(path,{method:"POST",body:JSON.stringify(body)});
      setActive(created);
      poll(created.id);
    }catch(caught){setError(caught instanceof Error?caught.message:String(caught))}
  }

  function poll(id:string){
    const timer=setInterval(async()=>{
      try{
        const item=await api<Audit>(`/audits/${id}`);
        setActive(item);
        if(["completed","failed","cancelled"].includes(item.status)){clearInterval(timer);await audits.reload()}
      }catch{clearInterval(timer)}
    },900);
  }

  const activeDisabled=!projectId||!targetId||active?.status==="running"||(mode==="mcp"&&mcpMode==="active"&&(!activeConfirmed||!toolName||(sensitive&&!sensitiveConfirmed)));
  return <>
    <PageHeader title={title} description={mode==="mcp"?"Découverte passive par défaut ou appels actifs précisément autorisés, avec paramètres et preuves observables.":mode==="jailbreak"?"Teste les contournements de restrictions par autorité fictive, changement de persona, cadrage hypothétique, obfuscation et coercition de format.":"Exécute un scénario contrôlé contre une cible réelle avec marqueur fictif et classification PASS / FAIL / INCONCLUSIVE / ERROR."}/>
    {error&&<ErrorBox message={error}/>}
    <div className="grid grid-cols-3 gap-5">
      <div className="card col-span-2 space-y-4">
        <label><span className="label">Projet</span><select className="input" value={projectId} onChange={event=>{setProject(event.target.value);resetTarget("")}}><option value="">Sélectionner…</option>{projects.data?.map(project=><option key={project.id} value={project.id}>{project.client_name} — {project.engagement_name}</option>)}</select></label>
        <label><span className="label">Cible compatible</span><select className="input" value={targetId} onChange={event=>resetTarget(event.target.value)}><option value="">Sélectionner…</option>{filtered.map(target=><option key={target.id} value={target.id}>{target.name} ({target.target_type})</option>)}</select></label>
        {mode==="mcp"&&<>
          <div><span className="label">Mode d’audit</span><div className="grid grid-cols-2 gap-3"><button type="button" className={mcpMode==="passive"?"btn-primary":"btn"} onClick={()=>setMcpMode("passive")}><Eye size={16}/>Passif — découverte seule</button><button type="button" className={mcpMode==="active"?"btn-primary":"btn"} onClick={()=>setMcpMode("active")}><Zap size={16}/>Actif — appel contrôlé</button></div></div>
          {mcpMode==="passive"?<div className="rounded-lg border border-cyan/20 bg-cyan/5 p-4 text-sm text-slate-300"><div className="mb-1 flex items-center gap-2 font-medium text-cyan"><Eye size={16}/>Sans effet sur la cible</div>Initialisation MCP et inventaire des outils, ressources, prompts et capacités. Aucun outil n’est appelé.</div>:<div className="space-y-4 rounded-xl border border-amber-800/70 bg-amber-950/20 p-4"><div className="flex items-start gap-3"><Activity className="mt-0.5 text-amber-400" size={19}/><div><p className="font-medium text-amber-100">Audit actif explicitement borné</p><p className="text-xs text-amber-300/80">Exécute uniquement l’outil sélectionné ci-dessous. Un audit passif préalable fournit l’inventaire.</p></div></div>{discoveredTools.length?<><label><span className="label">Outil découvert</span><select className="input" value={toolName} onChange={event=>{setToolName(event.target.value);setSensitiveConfirmed(false)}}><option value="">Sélectionner…</option>{discoveredTools.map(tool=><option key={tool.name} value={tool.name}>{tool.name}{sensitivePattern.test(`${tool.name} ${tool.description||""}`)?" · sensible":""}</option>)}</select></label>{selectedTool&&<p className="rounded bg-slate-950/60 p-3 text-xs text-slate-400">{selectedTool.description||"Aucune description fournie"}</p>}<label><span className="label">Paramètres JSON exacts</span><textarea className="input min-h-28 font-mono text-xs" value={argumentsText} onChange={event=>setArgumentsText(event.target.value)}/></label><label className="flex items-start gap-3 text-sm text-slate-300"><input className="mt-1" type="checkbox" checked={activeConfirmed} onChange={event=>setActiveConfirmed(event.target.checked)}/><span>J’autorise cet appel précis avec ces paramètres dans le périmètre de la mission.</span></label>{sensitive&&<label className="flex items-start gap-3 rounded border border-red-800 bg-red-950/30 p-3 text-sm text-red-200"><input className="mt-1" type="checkbox" checked={sensitiveConfirmed} onChange={event=>setSensitiveConfirmed(event.target.checked)}/><span>Je confirme séparément l’exécution de cette capacité identifiée comme sensible ou potentiellement destructive.</span></label>}</>:<div className="rounded border border-slate-700 p-4 text-sm text-slate-400">Aucun inventaire disponible pour cette cible. Lancez d’abord un audit passif.</div>}</div>}
        </>}
        {mode!=="mcp"&&<><label><span className="label">Scénario versionné</span><select className="input" value={scenarioKey} onChange={event=>setScenarioKey(event.target.value)}>{visibleScenarios.map(scenario=><option key={`${scenario.id}-${scenario.version}`} value={`${scenario.id}@@${scenario.version}`}>{scenario.name} — v{scenario.version}</option>)}</select></label><label><span className="label">Objectif de sécurité</span><textarea className="input min-h-20" value={objective} onChange={event=>setObjective(event.target.value)}/></label><div className="rounded-lg border border-amber-900 bg-amber-950/20 p-3 text-xs text-amber-200">Ce test envoie réellement des requêtes à la cible. Il utilise uniquement le marqueur fictif <code>AGENTSEC_CANARY_7F3A</code>.</div></>}
        <button className="btn-primary" disabled={activeDisabled} onClick={()=>void run()}><Play size={16}/>{mode==="mcp"?(mcpMode==="passive"?"Lancer l’inspection passive":"Confirmer et lancer l’appel actif"):"Confirmer et lancer le test"}</button>
      </div>
      <div className="card"><div className="mb-4 flex items-center gap-2"><Radio className="text-cyan" size={18}/><h3 className="font-semibold text-white">Exécution</h3></div>{active?<div className="space-y-3 text-sm"><Status value={active.status}/><p className="font-mono text-xs text-slate-500">{active.id}</p>{active.error&&<p className="text-red-300">{active.error}</p>}{Object.keys(active.summary).length>0&&<pre className="max-h-96 overflow-auto whitespace-pre-wrap rounded bg-slate-950 p-3 text-xs text-slate-300">{JSON.stringify(active.summary,null,2)}</pre>}</div>:<div className="py-12 text-center text-slate-500"><ShieldAlert className="mx-auto mb-3"/><p className="text-sm">Aucune exécution active</p></div>}</div>
    </div>
    {audits.data?.length?<div className="mt-7 table-wrap"><table className="table"><thead><tr><th>Audit</th><th>État</th><th>Mode</th><th>Date</th></tr></thead><tbody>{audits.data.filter(item=>mode==="mcp"?item.audit_type==="mcp_security":mode==="jailbreak"?item.audit_type==="jailbreak":mode==="llm"?["prompt_injection","jailbreak"].includes(item.audit_type):item.audit_type==="prompt_injection").slice(0,10).map(item=><tr key={item.id}><td>{item.audit_type}</td><td><Status value={item.status}/></td><td>{item.passive?"Passif":"Actif confirmé"}</td><td>{new Date(item.created_at).toLocaleString()}</td></tr>)}</tbody></table></div>:null}
  </>;
}
