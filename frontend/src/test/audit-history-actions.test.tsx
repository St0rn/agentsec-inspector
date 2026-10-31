import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { AuditHistory } from "../components/AuditHistory";
import type { Audit } from "../types";

const run = (id:string, project_id="project-a", audit_type="custom_payload"): Audit => ({
  id, project_id, target_id:"target-local", audit_type,
  status:"completed", passive:false,
  configuration:{name:"Controlled test"}, summary:{}, error:null,
  created_at:"2026-10-31T10:00:00Z", started_at:null, finished_at:null,
});

function mockBackend() {
  const requests: Array<{url:string;method:string}>=[];
  const fetcher=vi.fn(async (input:RequestInfo|URL,init?:RequestInit)=>{
    const url=String(input),method=init?.method||"GET";
    requests.push({url,method});
    if (url.endsWith("/health")) return new Response(JSON.stringify({
      status:"ok", service:"agentsec-backend", version:"1.4.0",
    }),{status:200,headers:{"Content-Type":"application/json"}});
    if(method==="DELETE")return new Response(null,{status:204});
    return new Response(JSON.stringify({}),{status:200,headers:{"Content-Type":"application/json"}});
  });
  vi.stubGlobal("fetch",fetcher);
  return requests;
}

beforeEach(()=>{
  localStorage.setItem("agentsec-api-token","test-token");
  vi.stubGlobal("confirm",vi.fn(()=>true));
});

describe("confirmed audit history cleanup",()=>{
  it("removes only the selected audit after confirmation",async()=>{
    const requests=mockBackend();
    const callback=vi.fn(async()=>undefined);
    render(<AuditHistory audits={[run("one"),run("two")]} onDelete={callback}/>);
    fireEvent.click(screen.getAllByTitle("Supprimer cet audit")[0]);
    await waitFor(()=>expect(callback).toHaveBeenCalledOnce());
    expect(requests.some(item=>item.method==="DELETE" &&
      item.url.endsWith("/audits/one?confirm_delete=true"))).toBe(true);
    expect(screen.getByText("Vider l'historique du projet")).toBeInTheDocument();
  });

  it("clears only the selected project's audit type",async()=>{
    const requests=mockBackend();
    const callback=vi.fn(async()=>undefined);
    render(<AuditHistory audits={[run("one"),run("two")]} onDelete={callback}/>);
    fireEvent.click(screen.getByText("Vider l'historique du projet"));
    await waitFor(()=>expect(callback).toHaveBeenCalledOnce());
    expect(requests.some(item=>item.method==="DELETE" &&
      item.url.includes("project_id=project-a") && item.url.includes("audit_type=custom_payload") &&
      item.url.includes("confirm_delete=true"))).toBe(true);
  });

  it("globally clears custom-payload history only after distinct confirmation",async()=>{
    const requests=mockBackend();
    const callback=vi.fn(async()=>undefined);
    render(<AuditHistory audits={[run("one","project-a"),run("two","project-b")]}
      onDelete={callback} allowClearAll/>);
    fireEvent.click(screen.getByText("Vider tout l'historique Custom Payload"));
    await waitFor(()=>expect(callback).toHaveBeenCalledOnce());
    expect(requests.some(item=>item.method==="DELETE" &&
      item.url.endsWith("/audits?audit_type=custom_payload&all_projects=true&confirm_delete=true"))).toBe(true);
  });

  it("refuses to clear a mixed-project list from the project button",async()=>{
    const requests=mockBackend();
    render(<AuditHistory audits={[run("one","project-a"),run("two","project-b")]}
      onDelete={vi.fn(async()=>undefined)} allowClearAll/>);
    fireEvent.click(screen.getByText("Vider l'historique du projet"));
    expect(screen.getByText(/Sélectionnez une vue limitée à un seul projet/)).toBeInTheDocument();
    expect(requests.some(item=>item.method==="DELETE")).toBe(false);
  });

  it("does not delete an audit when confirmation is refused",async()=>{
    const requests=mockBackend();
    vi.stubGlobal("confirm",vi.fn(()=>false));
    render(<AuditHistory audits={[run("one")]} onDelete={vi.fn(async()=>undefined)}/>);
    fireEvent.click(screen.getByTitle("Supprimer cet audit"));
    expect(requests.some(item=>item.method==="DELETE")).toBe(false);
  });
});
