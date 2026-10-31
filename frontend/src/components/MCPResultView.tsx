import { useMemo, useState } from "react";
import { Search, X } from "lucide-react";

type Obj = Record<string, unknown>;
type Inventory = "Outils" | "Ressources" | "Prompts" | "Observations";
const asObject = (value: unknown): Obj =>
  value !== null && typeof value === "object" && !Array.isArray(value) ? value as Obj : {};
const asRows = (value: unknown): Obj[] =>
  Array.isArray(value) ? value.map(asObject).filter(item => Object.keys(item).length > 0) : [];
const display = (value: unknown): string => {
  if (value === null || value === undefined) return "—";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
};
function DataTable({rows,caption}:{rows:Obj[];caption:string}) {
  const [showAll,setShowAll]=useState(false);
  const columns=useMemo(()=>Array.from(new Set(rows.slice(0,12).flatMap(row=>Object.keys(row)))).slice(0,12),[rows]);
  if(!rows.length)return <p className="text-sm text-slate-500">Aucun enregistrement retourné.</p>;
  return <div className="space-y-2"><div className="flex items-center justify-between gap-2">
    <span className="text-xs text-slate-400">{caption} · {rows.length} élément(s)</span>
    {rows.length>10&&<button className="btn text-xs" onClick={()=>setShowAll(!showAll)}>{showAll?"Réduire":"Afficher tout"}</button>}
  </div><div className="max-h-96 overflow-auto rounded-lg border border-slate-800"><table className="table">
    <thead><tr>{columns.map(col=><th key={col}>{col}</th>)}</tr></thead>
    <tbody>{(showAll?rows:rows.slice(0,10)).map((row,index)=><tr key={index}>{columns.map(col=>
      <td key={col} className="max-w-52 truncate text-xs" title={display(row[col])}>{display(row[col])}</td>)}</tr>)}</tbody>
  </table></div></div>;
}
function InventoryModal({kind,items,close}:{kind:Inventory;items:Obj[];close:()=>void}) {
  const [search,setSearch]=useState("");
  const shown=items.filter(item=>JSON.stringify(item).toLowerCase().includes(search.toLowerCase()));
  return <div role="dialog" aria-modal="true" aria-label={`Inventaire MCP : ${kind}`}
    className="fixed inset-0 z-[70] grid place-items-center bg-black/80 p-4" onMouseDown={close}>
    <section className="panel flex max-h-[92vh] w-full max-w-5xl flex-col overflow-hidden p-5" onMouseDown={event=>event.stopPropagation()}>
      <div className="mb-4 flex items-center gap-4"><div><h3 className="text-xl font-semibold text-white">{kind}</h3>
        <p className="text-xs text-slate-400">{shown.length} / {items.length} élément(s) découverts</p></div>
        <button className="btn ml-auto" aria-label="Fermer l'inventaire" onClick={close}><X size={18}/></button>
      </div>
      <label className="relative mb-4"><Search className="absolute left-3 top-3 text-slate-500" size={16}/>
        <input className="input pl-9" aria-label="Rechercher dans l'inventaire" placeholder="Nom, description, type, sévérité…" value={search} onChange={event=>setSearch(event.target.value)}/>
      </label>
      <div className="space-y-3 overflow-auto">
        {shown.map((item,index)=>{
          const props=asObject(asObject(item.inputSchema).properties);
          const required=asObject(item.inputSchema).required;
          return <details key={String(item.name||item.uri||item.title||index)+index} className="rounded-lg border border-slate-700 bg-slate-950/60 p-4">
            <summary className="cursor-pointer font-semibold text-white">
              {display(item.name||item.uri||item.title||`Élément ${index+1}`)}
              {Boolean(item.severity)&&<span className="ml-2 rounded bg-slate-800 px-2 py-1 text-xs text-amber-300">{display(item.severity)}</span>}
            </summary>
            <div className="mt-3 space-y-3 text-sm text-slate-300">
              <p>{display(item.description)}</p>
              {Object.keys(props).length>0&&<div><p className="label">Paramètres disponibles</p><div className="overflow-auto rounded-lg border border-slate-800">
                <table className="table"><thead><tr><th>Paramètre</th><th>Type</th><th>Obligatoire</th><th>Valeurs / contraintes</th></tr></thead><tbody>
                  {Object.entries(props).map(([name,raw])=>{const def=asObject(raw);return <tr key={name}>
                    <td className="font-mono text-cyan">{name}</td><td>{display(def.type)}</td>
                    <td>{Array.isArray(required)&&required.includes(name)?"Oui":"Non"}</td>
                    <td>{Array.isArray(def.enum)?def.enum.map(display).join(", "):display(def.description||def.pattern||"—")}</td>
                  </tr>})}
                </tbody></table></div></div>}
              {Boolean(item.evidence)&&<pre className="max-h-44 overflow-auto whitespace-pre-wrap break-all rounded bg-slate-900 p-3 text-xs">{display(item.evidence)}</pre>}
              {Boolean(item.recommendation)&&<p><strong>Remédiation :</strong> {display(item.recommendation)}</p>}
              <details><summary className="cursor-pointer text-xs text-cyan">Métadonnées complètes (JSON)</summary>
                <pre className="max-h-72 overflow-auto whitespace-pre-wrap break-all p-3 text-xs">{JSON.stringify(item,null,2)}</pre>
              </details>
            </div>
          </details>;
        })}
        {!shown.length&&<p className="py-8 text-center text-slate-400">Aucun résultat pour ce filtre.</p>}
      </div>
    </section>
  </div>;
}
export function MCPResultView({summary}:{summary:Obj}) {
  const [opened,setOpened]=useState<Inventory|null>(null);
  const discovery=asObject(summary.discovery);
  const calls=asRows(summary.active_tool_calls);
  const inventory: Record<Inventory,Obj[]> = {
    Outils:asRows(discovery.tools),
    Ressources:asRows(discovery.resources),
    Prompts:asRows(discovery.prompts),
    Observations:asRows(summary.findings),
  };
  const stats:Inventory[]=["Outils","Ressources","Prompts","Observations"];
  return <section className="space-y-4" aria-label="Résultats MCP">
    <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">{stats.map((kind)=>
      <button type="button" key={kind} aria-label={`Voir ${kind.toLowerCase()} MCP`}
        className="rounded-lg border border-slate-700 bg-slate-950/60 p-3 text-center transition-colors hover:border-cyan hover:bg-slate-900 focus-visible:outline focus-visible:outline-2 focus-visible:outline-cyan"
        onClick={()=>setOpened(kind)}>
        <p className="text-2xl font-semibold text-white">{inventory[kind].length||Number(summary[kind==="Outils"?"tools":kind==="Ressources"?"resources":kind==="Prompts"?"prompts":"observations"]||0)}</p>
        <p className="mt-1 text-xs text-slate-300">{kind} · consulter</p>
      </button>)}
    </div>
    <div className="flex flex-wrap justify-between gap-2 text-xs text-slate-400">
      <span>{summary.scan_mode==="vulnerability"?"Audit de vulnérabilités (sans appels d’outils)":summary.mode==="active"?"Appels actifs autorisés":"Découverte passive"} · serveur {display(asObject(discovery.server_info).name)}</span>
      <span>{calls.length} appel(s) actif(s)</span>
    </div>
    {summary.scan_mode==="vulnerability"&&<div className="rounded-lg border border-cyan/20 bg-cyan/5 p-3 text-sm text-slate-300">
      Contrôles des métadonnées et schémas MCP : ces constats indiquent des risques potentiels, pas une exploitation démontrée.
      {inventory.Observations.length>0&&<span className="ml-2 font-semibold text-white">{inventory.Observations.length} constat(s) à examiner.</span>}
    </div>}
    {calls.map((call,index)=>{
      const result=asObject(call.result);
      const structured=asObject(result.structuredContent);
      const data=asRows(structured.data),collections=asRows(structured.collections),meta=asObject(structured.meta);
      const failed=call.status==="ERROR";
      return <article key={index} className="space-y-3 rounded-xl border border-slate-700 bg-slate-950/30 p-4">
        <div className="flex flex-wrap items-center gap-3">
          <h3 className="font-semibold text-white">{display(call.tool_name)}</h3>
          <span className={`rounded px-2 py-1 text-xs font-semibold ${failed?"bg-red-950 text-red-300":"bg-emerald-950 text-emerald-300"}`}>{display(call.status)}</span>
          <span className="ml-auto text-xs text-slate-400">{display(call.duration_ms)} ms</span>
        </div>
        <div><p className="label">Paramètres envoyés</p><pre className="overflow-auto rounded bg-slate-950 p-3 text-xs text-slate-300">{JSON.stringify(call.arguments||{},null,2)}</pre></div>
        {failed&&<p className="rounded border border-red-900 p-3 text-sm text-red-300">{display(call.error)}</p>}
        {Object.keys(meta).length>0&&<p className="rounded bg-slate-900 p-3 text-xs text-slate-200">Page {display(meta.page)} / {display(meta.pages)} · Limite {display(meta.limit)} · Total filtré {display(meta.total)}</p>}
        {data.length>0&&<DataTable rows={data} caption="Enregistrements retournés"/>}
        {collections.length>0&&<DataTable rows={collections.map(col=>({
          name:col.name,records:col.records,description:col.description,
          fields:Array.isArray(col.fields)?col.fields.length:"—",
          relations:Array.isArray(col.relations)?col.relations.length:"—",
        }))} caption="Collections et schémas"/>}
        {!failed&&!data.length&&!collections.length&&Object.keys(structured).length>0&&<pre className="max-h-80 overflow-auto whitespace-pre-wrap rounded bg-slate-950 p-3 text-xs text-slate-300">{JSON.stringify(structured,null,2)}</pre>}
        <details className="rounded border border-slate-800"><summary className="cursor-pointer px-3 py-2 text-xs text-cyan">Voir la réponse MCP brute</summary>
          <pre className="max-h-80 overflow-auto whitespace-pre-wrap border-t border-slate-800 p-3 text-xs text-slate-300">{JSON.stringify(result,null,2)}</pre>
        </details>
      </article>;
    })}
    <details className="rounded border border-slate-800"><summary className="cursor-pointer px-3 py-2 text-xs text-cyan">Inventaire et résumé JSON complet</summary>
      <pre className="max-h-96 overflow-auto whitespace-pre-wrap border-t border-slate-800 p-3 text-xs text-slate-300">{JSON.stringify(summary,null,2)}</pre>
    </details>
    {opened&&<InventoryModal kind={opened} items={inventory[opened]} close={()=>setOpened(null)}/>}
  </section>;
}
