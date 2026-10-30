import { Plus, Trash2 } from "lucide-react";
import { useMemo, useState } from "react";
import { Empty, ErrorBox, Loading, PageHeader } from "../components/ui";
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

const urlTypes = new Set(["mcp_http","openai","ollama","chatbot","custom_http","agent_lab"]);

const configurationHelp:Record<string,string>={
  mcp_http:'Exemple : {"headers":{"X-Tenant":"lab"}}. Aucun secret en clair.',
  mcp_stdio:'Exemple : {"command":"node","args":["server.js"]}. L’exécutable doit être autorisé côté application.',
  openai:'Exemple : {"model":"gpt-4.1-mini","api_key_env":"OPENAI_API_KEY"}. L’URL peut être la racine ou se terminer par /chat/completions.',
  ollama:'Exemple : {"model":"llama3.2"}. AgentSec ajoute /api/chat à l’URL.',
  chatbot:'Exemple : {"message_path":"input.message","history_path":"input.history","response_path":"answer.text","api_key_env":"CHATBOT_API_KEY","api_key_header":"X-API-Key","api_key_prefix":""}.',
  custom_http:'Exemple : {"model":"model-name","api_key_env":"CHAT_API_KEY"}. Le format attendu est compatible OpenAI Chat Completions.',
  rag:'Utilisé pour rattacher les documents et traces RAG à une cible logique. L’URL est facultative.',
  agent_lab:'Cible réservée au laboratoire contrôlé AgentSec.',
};

export default function Targets(){
  const targets=useApi<Target[]>("/targets");
  const projects=useApi<Project[]>("/projects");
  const [show,setShow]=useState(false);
  const [error,setError]=useState("");
  const [form,setForm]=useState({project_id:"",name:"",target_type:"mcp_http",endpoint:"",configuration:"{}",remote_authorized:false});
  const needsUrl=urlTypes.has(form.target_type);
  const typeLabel=useMemo(()=>Object.fromEntries(targetTypes),[]);

  async function submit(event:React.FormEvent){
    event.preventDefault();
    setError("");
    try{
      const configuration=JSON.parse(form.configuration);
      await api("/targets",{method:"POST",body:JSON.stringify({...form,endpoint:form.endpoint||null,configuration})});
      setShow(false);
      await targets.reload();
    }catch(caught){setError(caught instanceof Error?caught.message:String(caught))}
  }

  async function remove(id:string){
    if(confirm("Supprimer cette cible ?")){await api(`/targets/${id}`,{method:"DELETE"});await targets.reload()}
  }

  return <>
    <PageHeader title="Cibles" description="Chatbots, API LLM, serveurs MCP et systèmes RAG déclarés dans le périmètre autorisé." action={<button className="btn-primary" onClick={()=>setShow(value=>!value)}><Plus size={16}/>Ajouter</button>}/>
    {(targets.error||error)&&<ErrorBox message={targets.error||error}/>}
    {show&&<form onSubmit={submit} className="card mb-5 grid grid-cols-2 gap-4">
      <label><span className="label">Projet</span><select className="input" required value={form.project_id} onChange={event=>setForm({...form,project_id:event.target.value})}><option value="">Sélectionner…</option>{projects.data?.map(project=><option key={project.id} value={project.id}>{project.client_name} — {project.engagement_name}</option>)}</select></label>
      <label><span className="label">Nom</span><input className="input" required placeholder="Chatbot support client" value={form.name} onChange={event=>setForm({...form,name:event.target.value})}/></label>
      <label><span className="label">Type de cible</span><select className="input" value={form.target_type} onChange={event=>setForm({...form,target_type:event.target.value,endpoint:event.target.value==="mcp_stdio"?"":form.endpoint})}>{targetTypes.map(([value,label])=><option key={value} value={value}>{label}</option>)}</select></label>
      <label><span className="label">URL cible {needsUrl&&<span className="text-red-400">*</span>}</span><input className="input" type="url" required={needsUrl} pattern="https?://.+" placeholder="https://chatbot.example.com/api/chat" value={form.endpoint} onChange={event=>setForm({...form,endpoint:event.target.value})} disabled={form.target_type==="mcp_stdio"}/><span className="mt-1 block text-xs text-slate-500">Indiquez l’URL réellement appelée par AgentSec ; les identifiants intégrés à l’URL sont interdits.</span></label>
      <label className="col-span-2"><span className="label">Configuration de la requête (JSON)</span><textarea className="input min-h-28 font-mono text-xs" value={form.configuration} onChange={event=>setForm({...form,configuration:event.target.value})}/><span className="mt-1 block text-xs text-slate-500">N’y saisissez aucune clé ni aucun jeton. {configurationHelp[form.target_type]}</span></label>
      {form.target_type==="chatbot"&&<div className="col-span-2 rounded-lg border border-cyan/20 bg-cyan/5 p-4 text-xs text-slate-300"><p className="font-medium text-cyan">Adaptation à une API de chatbot</p><p className="mt-1">Utilisez <code>message_path</code> pour le message courant, <code>history_path</code> pour la conversation complète, <code>response_path</code> pour le texte retourné et <code>tool_calls_path</code> si l’API expose des appels d’outils. Les chemins utilisent une notation pointée, par exemple <code>answer.text</code>.</p></div>}
      <label className="col-span-2 flex items-center gap-2 text-sm text-slate-300"><input type="checkbox" checked={form.remote_authorized} onChange={event=>setForm({...form,remote_authorized:event.target.checked})}/>Je confirme que les connexions à cette cible distante sont autorisées par le périmètre.</label>
      <div className="col-span-2 flex justify-end"><button className="btn-primary">Enregistrer</button></div>
    </form>}
    {targets.loading?<Loading/>:targets.data?.length?<div className="table-wrap"><table className="table"><thead><tr><th>Nom</th><th>Type</th><th>URL / commande</th><th>Distance autorisée</th><th></th></tr></thead><tbody>{targets.data.map(target=><tr key={target.id}><td className="text-white">{target.name}</td><td>{typeLabel[target.target_type]||target.target_type}</td><td className="max-w-sm truncate font-mono text-xs">{target.endpoint||String(target.configuration.command||"—")}</td><td>{target.remote_authorized?"Oui":"Non"}</td><td><button onClick={()=>void remove(target.id)} className="text-slate-500 hover:text-red-400"><Trash2 size={16}/></button></td></tr>)}</tbody></table></div>:<Empty title="Aucune cible"/>}
  </>;
}
