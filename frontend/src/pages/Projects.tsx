import { Pencil, Plus, Trash2, X } from "lucide-react";
import { useState } from "react";
import { Empty, ErrorBox, Loading, PageHeader } from "../components/ui";
import { useApi } from "../hooks/useApi";
import { api } from "../lib/api";
import type { Project } from "../types";

type ProjectForm = {
  client_name: string;
  engagement_name: string;
  description: string;
  authorized_scope: string;
  start_date: string;
  end_date: string;
};

const initial: ProjectForm = {
  client_name: "",
  engagement_name: "",
  description: "",
  authorized_scope: "",
  start_date: "",
  end_date: "",
};

function projectForm(project: Project): ProjectForm {
  return {
    client_name: project.client_name,
    engagement_name: project.engagement_name,
    description: project.description,
    authorized_scope: project.authorized_scope,
    start_date: project.start_date || "",
    end_date: project.end_date || "",
  };
}

export default function Projects() {
  const { data, error, loading, reload } = useApi<Project[]>("/projects");
  const [open, setOpen] = useState(false);
  const [editingId, setEditingId] = useState<string>();
  const [form, setForm] = useState<ProjectForm>(initial);
  const [saving, setSaving] = useState(false);
  const [localError, setLocalError] = useState("");

  function create() {
    setEditingId(undefined);
    setForm(initial);
    setLocalError("");
    setOpen(true);
  }

  function edit(project: Project) {
    setEditingId(project.id);
    setForm(projectForm(project));
    setLocalError("");
    setOpen(true);
  }

  function close() {
    setOpen(false);
    setEditingId(undefined);
    setForm(initial);
  }

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setSaving(true);
    setLocalError("");
    try {
      await api(editingId ? `/projects/${editingId}` : "/projects", {
        method: editingId ? "PUT" : "POST",
        body: JSON.stringify({
          ...form,
          start_date: form.start_date || null,
          end_date: form.end_date || null,
        }),
      });
      close();
      await reload();
    } catch (currentError) {
      setLocalError(currentError instanceof Error ? currentError.message : String(currentError));
    } finally {
      setSaving(false);
    }
  }

  async function remove(id: string) {
    if (!confirm("Supprimer ce projet et toutes ses données liées ?")) return;
    setLocalError("");
    try {
      await api(`/projects/${id}`, { method: "DELETE" });
      await reload();
    } catch (currentError) {
      setLocalError(currentError instanceof Error ? currentError.message : String(currentError));
    }
  }

  return <>
    <PageHeader
      title="Projets"
      description="Missions indépendantes avec périmètre autorisé et données isolées."
      action={<button className="btn-primary" onClick={create}><Plus size={16}/>Nouveau projet</button>}
    />
    {(error || localError) && <ErrorBox message={error || localError}/>}
    {loading ? <Loading/> : data?.length ? <div className="table-wrap">
      <table className="table">
        <thead><tr><th>Client</th><th>Mission</th><th>Périmètre</th><th>Dates</th><th><span className="sr-only">Actions</span></th></tr></thead>
        <tbody>{data.map((project) => <tr key={project.id}>
          <td className="font-medium text-white">{project.client_name}</td>
          <td>{project.engagement_name}</td>
          <td className="max-w-md truncate">{project.authorized_scope}</td>
          <td>{project.start_date || "—"} → {project.end_date || "—"}</td>
          <td><div className="flex justify-end gap-3">
            <button aria-label={`Modifier ${project.engagement_name}`} className="text-slate-500 hover:text-cyan" onClick={() => edit(project)}><Pencil size={16}/></button>
            <button aria-label={`Supprimer ${project.engagement_name}`} className="text-slate-500 hover:text-red-400" onClick={() => void remove(project.id)}><Trash2 size={16}/></button>
          </div></td>
        </tr>)}</tbody>
      </table>
    </div> : <Empty title="Aucun projet" detail="Créez une mission avant d’ajouter des cibles ou de lancer des audits."/>}

    {open && <div className="fixed inset-0 z-50 grid place-items-center bg-black/70 p-8">
      <form onSubmit={submit} className="panel w-full max-w-2xl p-6">
        <div className="mb-5 flex">
          <h3 className="text-lg font-semibold text-white">{editingId ? "Modifier la mission" : "Nouvelle mission"}</h3>
          <button type="button" aria-label="Fermer" className="ml-auto" onClick={close}><X/></button>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <Field label="Client" value={form.client_name} set={(value) => setForm({...form, client_name: value})}/>
          <Field label="Mission" value={form.engagement_name} set={(value) => setForm({...form, engagement_name: value})}/>
          <Field label="Début" type="date" value={form.start_date} set={(value) => setForm({...form, start_date: value})}/>
          <Field label="Fin" type="date" value={form.end_date} set={(value) => setForm({...form, end_date: value})}/>
          <div className="col-span-2"><Field label="Description" textarea value={form.description} set={(value) => setForm({...form, description: value})}/></div>
          <div className="col-span-2"><Field label="Périmètre autorisé" textarea required value={form.authorized_scope} set={(value) => setForm({...form, authorized_scope: value})}/></div>
        </div>
        <div className="mt-5 flex justify-end"><button disabled={saving} className="btn-primary">{saving ? "Enregistrement…" : editingId ? "Enregistrer les modifications" : "Créer le projet"}</button></div>
      </form>
    </div>}
  </>;
}

function Field({ label, value, set, type = "text", textarea = false, required = true }: {
  label: string;
  value: string;
  set: (value: string) => void;
  type?: string;
  textarea?: boolean;
  required?: boolean;
}) {
  return <label>
    <span className="label">{label}</span>
    {textarea
      ? <textarea className="input min-h-20" value={value} required={required} onChange={(event) => set(event.target.value)}/>
      : <input className="input" type={type} value={value} required={required} onChange={(event) => set(event.target.value)}/>
    }
  </label>;
}
