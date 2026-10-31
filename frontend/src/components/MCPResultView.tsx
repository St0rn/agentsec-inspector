import { useMemo, useState } from "react";

type Obj = Record<string, unknown>;
const asObject = (value: unknown): Obj =>
  value !== null && typeof value === "object" && !Array.isArray(value) ? value as Obj : {};
const asRows = (value: unknown): Obj[] =>
  Array.isArray(value) ? value.map(asObject).filter(item => Object.keys(item).length > 0) : [];
const display = (value: unknown): string => {
  if (value === null || value === undefined) return "—";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
};

function DataTable({ rows, caption }: { rows: Obj[]; caption: string }) {
  const [showAll, setShowAll] = useState(false);
  const columns = useMemo(() => Array.from(new Set(rows.slice(0, 12).flatMap(row => Object.keys(row))))
    .slice(0, 12), [rows]);
  if (!rows.length) return <p className="text-sm text-slate-500">Aucun enregistrement retourné.</p>;
  return <div>
    <div className="mb-2 flex items-center justify-between gap-2">
      <p className="text-xs font-medium text-slate-400">{caption} · {rows.length} élément(s)</p>
      {rows.length > 10 && <button type="button" className="btn text-xs" onClick={() => setShowAll(!showAll)}>
        {showAll ? "Réduire" : "Afficher tout"}
      </button>}
    </div>
    <div className="max-h-96 overflow-auto rounded-lg border border-slate-800">
      <table className="table"><thead><tr>{columns.map(col => <th key={col}>{col}</th>)}</tr></thead>
        <tbody>{(showAll ? rows : rows.slice(0, 10)).map((row, index) =>
          <tr key={index}>{columns.map(col =>
            <td key={col} className="max-w-52 truncate text-xs" title={display(row[col])}>{display(row[col])}</td>
          )}</tr>)}</tbody>
      </table>
    </div>
  </div>;
}

export function MCPResultView({ summary }: { summary: Obj }) {
  const discovery = asObject(summary.discovery);
  const calls = asRows(summary.active_tool_calls);
  const stats = [
    ["Outils", summary.tools],
    ["Ressources", summary.resources],
    ["Prompts", summary.prompts],
    ["Observations", summary.observations],
  ];
  return <section className="space-y-4" aria-label="Résultats MCP">
    <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">{stats.map(([label, count]) =>
      <div key={String(label)} className="rounded-lg border border-slate-800 bg-slate-950/60 p-3 text-center">
        <p className="text-2xl font-semibold text-white">{typeof count === "number" ? count : "—"}</p>
        <p className="mt-1 text-xs text-slate-400">{String(label)}</p>
      </div>)}
    </div>
    <p className="text-xs text-slate-400">
      Mode {summary.mode === "active" ? "actif autorisé" : "passif"} ·
      serveur {display(asObject(discovery.server_info).name)} ·
      {calls.length} appel(s) actif(s)
    </p>
    {calls.map((call, index) => {
      const result = asObject(call.result);
      const structured = asObject(result.structuredContent);
      const data = asRows(structured.data);
      const collections = asRows(structured.collections);
      const meta = asObject(structured.meta);
      const failed = call.status === "ERROR";
      return <article key={index} className="rounded-xl border border-slate-700 bg-slate-950/30 p-4 space-y-3">
        <div className="flex flex-wrap items-center gap-3">
          <h3 className="font-semibold text-white">{display(call.tool_name)}</h3>
          <span className={`rounded px-2 py-1 text-xs font-semibold ${failed ? "bg-red-950 text-red-300" : "bg-emerald-950 text-emerald-300"}`}>
            {display(call.status)}
          </span>
          <span className="ml-auto text-xs text-slate-400">{display(call.duration_ms)} ms</span>
        </div>
        <div><p className="label">Paramètres envoyés</p>
          <pre className="overflow-auto rounded bg-slate-950 p-3 text-xs text-slate-300">{JSON.stringify(call.arguments || {}, null, 2)}</pre>
        </div>
        {failed && <p className="rounded border border-red-900 p-3 text-sm text-red-300">{display(call.error)}</p>}
        {Object.keys(meta).length > 0 && <p className="rounded bg-slate-900 p-3 text-xs text-slate-200">
          Page {display(meta.page)} / {display(meta.pages)} · Limite {display(meta.limit)} · Total filtré {display(meta.total)}
        </p>}
        {data.length > 0 && <DataTable rows={data} caption="Enregistrements retournés"/>}
        {collections.length > 0 && <DataTable rows={collections.map(col => ({
          name: col.name, records: col.records, description: col.description,
          fields: Array.isArray(col.fields) ? col.fields.length : "—",
          relations: Array.isArray(col.relations) ? col.relations.length : "—",
        }))} caption="Collections et schémas"/>}
        {!failed && !data.length && !collections.length && Object.keys(structured).length > 0 &&
          <pre className="max-h-80 overflow-auto whitespace-pre-wrap rounded bg-slate-950 p-3 text-xs text-slate-300">{JSON.stringify(structured, null, 2)}</pre>}
        <details className="rounded border border-slate-800"><summary className="cursor-pointer px-3 py-2 text-xs text-cyan">Voir la réponse MCP brute</summary>
          <pre className="max-h-80 overflow-auto whitespace-pre-wrap border-t border-slate-800 p-3 text-xs text-slate-300">{JSON.stringify(result, null, 2)}</pre>
        </details>
      </article>;
    })}
    <details className="rounded border border-slate-800"><summary className="cursor-pointer px-3 py-2 text-xs text-cyan">
      Inventaire et résumé JSON complet
    </summary><pre className="max-h-96 overflow-auto whitespace-pre-wrap border-t border-slate-800 p-3 text-xs text-slate-300">{JSON.stringify(summary, null, 2)}</pre></details>
  </section>;
}
