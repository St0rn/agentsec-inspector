import { useMemo } from "react";

type Obj = Record<string, unknown>;
export interface DiscoveredTool {
  name: string;
  description?: string;
  annotations?: Obj;
  inputSchema?: Obj;
}
function asObject(value: unknown): Obj {
  return value !== null && typeof value === "object" && !Array.isArray(value) ? value as Obj : {};
}
function initialValue(schema: Obj): unknown {
  if (schema.default !== undefined) return schema.default;
  if (schema.const !== undefined) return schema.const;
  const choices = schema.enum;
  if (Array.isArray(choices) && choices.length) return choices[0];
  if (schema.type === "integer" || schema.type === "number") return schema.minimum ?? 0;
  if (schema.type === "boolean") return false;
  if (schema.type === "array") return [];
  if (schema.type === "object") {
    return Object.fromEntries(
      Object.entries(asObject(schema.properties))
        .filter(([name]) => Array.isArray(schema.required) && schema.required.includes(name))
        .map(([name, item]) => [name, initialValue(asObject(item))]),
    );
  }
  return "";
}
export function defaultToolArguments(tool: DiscoveredTool): string {
  const schema = asObject(tool.inputSchema);
  const props = asObject(schema.properties);
  const required = Array.isArray(schema.required) ? schema.required : [];
  return JSON.stringify(Object.fromEntries(
    required.filter((name): name is string => typeof name === "string")
      .map(name => [name, initialValue(asObject(props[name]))])
  ), null, 2);
}
function convert(value: string, type: unknown): unknown {
  if (type === "number" || type === "integer") return Number(value);
  if (type === "array" || type === "object") return JSON.parse(value);
  return value;
}
export function MCPToolArguments({
  tool, value, onChange,
}: {tool: DiscoveredTool;value: string;onChange: (value:string)=>void}) {
  const schema = asObject(tool.inputSchema);
  const properties = asObject(schema.properties);
  const required = Array.isArray(schema.required) ? schema.required as string[] : [];
  const parsed = useMemo(() => {
    try {
      const valueAsJson: unknown = JSON.parse(value);
      return valueAsJson && !Array.isArray(valueAsJson) && typeof valueAsJson === "object" ?
        valueAsJson as Obj : null;
    } catch { return null; }
  }, [value]);
  const update = (name:string, next:unknown) => {
    if (!parsed) return;
    const copy = {...parsed};
    if (next === undefined) delete copy[name];
    else copy[name] = next;
    onChange(JSON.stringify(copy, null, 2));
  };
  return <div className="space-y-3">
    <div className="flex flex-wrap justify-between gap-2">
      <p className="text-sm font-semibold text-white">Paramètres de {tool.name}</p>
      <button type="button" className="btn text-xs" onClick={() => onChange(defaultToolArguments(tool))}>
        Restaurer les valeurs initiales
      </button>
    </div>
    {Object.keys(properties).length ? <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
      {Object.entries(properties).map(([name, raw]) => {
        const definition = asObject(raw);
        const requiredField = required.includes(name);
        const type = String(definition.type || "string");
        const valueHere = parsed?.[name];
        const choices = Array.isArray(definition.enum) ? definition.enum : null;
        const hasValue = parsed !== null && Object.hasOwn(parsed, name);
        const textValue = typeof valueHere === "object" ? JSON.stringify(valueHere, null, 2) : String(valueHere ?? "");
        return <label key={name} className="space-y-1">
          <span className="label">{name} {requiredField ? <span className="text-amber-300">*</span> :
            <span className="text-slate-500">(optionnel)</span>}</span>
          {Boolean(definition.description) && <span className="block text-xs text-slate-400">{String(definition.description)}</span>}
          {choices ? <select className="input" aria-label={name} value={hasValue ? JSON.stringify(valueHere) : "__omit__"} onChange={event => update(name, event.target.value === "__omit__" ? undefined : JSON.parse(event.target.value))}>
              {!requiredField && <option value="__omit__">— Ne pas envoyer —</option>}
              {choices.map((choice, index) => <option key={index} value={JSON.stringify(choice)}>{String(choice)}</option>)}
            </select> : type === "boolean" ? <select aria-label={name} className="input" value={hasValue ? String(valueHere) : "omit"} onChange={event => update(name, event.target.value === "omit" ? undefined : event.target.value === "true")}>
              {!requiredField && <option value="omit">— Ne pas envoyer —</option>}
              <option value="true">true</option><option value="false">false</option>
            </select> : <div className="flex gap-2">
              {type === "object" || type === "array" ?
                <textarea aria-label={name} className="input min-h-24 font-mono text-xs" value={hasValue ? textValue : ""} placeholder={type === "array" ? "[]" : "{}"} onChange={event => {
                  try {update(name, convert(event.target.value, type));} catch { /* Keep last valid structured value; raw JSON editor below handles drafts. */ }
                }}/> :
                <input aria-label={name} className="input" type={type === "integer" || type === "number" ? "number" : "text"}
                  step={type === "integer" ? "1" : "any"}
                  min={typeof definition.minimum === "number" ? definition.minimum : undefined}
                  max={typeof definition.maximum === "number" ? definition.maximum : undefined}
                  value={hasValue ? textValue : ""} placeholder={type}
                  onChange={event => update(name, event.target.value === "" && !requiredField ? undefined : convert(event.target.value, type))}/>}
              {!requiredField && hasValue && <button type="button" className="btn" onClick={() => update(name, undefined)}>Retirer</button>}
            </div>}
          <span className="text-[11px] text-slate-500">{type}{definition.pattern ? ` · pattern : ${definition.pattern}` : ""}</span>
          {!requiredField && !hasValue && !choices && type !== "boolean" && <button type="button" className="block text-xs text-cyan" onClick={() => update(name, initialValue(definition))}>Ajouter le paramètre</button>}
        </label>;
      })}
    </div> : <p className="text-xs text-slate-400">Aucun paramètre déclaré par le schéma MCP.</p>}
    <details className="rounded-lg border border-slate-700 p-3"><summary className="cursor-pointer text-sm text-cyan">Édition JSON avancée et schéma MCP</summary>
      <label className="mt-3 block"><span className="label">Paramètres JSON exacts</span>
        <textarea aria-label="Paramètres JSON exacts" className="input min-h-32 font-mono text-xs" value={value} onChange={event => onChange(event.target.value)}/>
      </label>
      <details className="mt-2"><summary className="cursor-pointer text-xs text-slate-300">Schéma d'entrée découvert</summary>
        <pre className="max-h-64 overflow-auto whitespace-pre-wrap text-xs text-slate-400">{JSON.stringify(schema,null,2)}</pre>
      </details>
    </details>
    {parsed === null && <p role="alert" className="text-sm text-red-300">JSON invalide : vérifie les paramètres avant de lancer le test.</p>}
  </div>;
}
