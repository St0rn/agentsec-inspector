import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import App from "../App";

const project={id:"project-1",client_name:"Lab",engagement_name:"MCP",description:"",authorized_scope:"Loopback",start_date:null,end_date:null,created_at:"2026-01-01",updated_at:"2026-01-01"};
const target={id:"target-1",project_id:"project-1",name:"MCP Lab",target_type:"mcp_http",endpoint:"http://127.0.0.1:8877/mcp",configuration:{},remote_authorized:false,created_at:"2026-01-01"};
const audit={id:"audit-1",project_id:"project-1",target_id:"target-1",audit_type:"mcp_security",status:"completed",passive:true,configuration:{},summary:{discovery:{tools:[{name:"read_lab_note",description:"Read a controlled note",inputSchema:{type:"object"}},{name:"delete_demo_record",description:"Administrative destructive capability",inputSchema:{type:"object"}}]}},error:null,created_at:"2026-01-01",started_at:"2026-01-01",finished_at:"2026-01-01"};

function payload(value:unknown,status=200){return new Response(JSON.stringify(value),{status,headers:{"Content-Type":"application/json"}})}
function getPayload(url:string,value:unknown){return url.endsWith("/health")?payload({status:"ok",service:"agentsec-backend",version:"1.0.1"}):payload(value)}

describe("MCP passive and active audit controls",()=>{
  beforeEach(()=>localStorage.setItem("agentsec-api-token","test-token"));

  it("keeps passive discovery as the safe default",async()=>{
    vi.stubGlobal("fetch",vi.fn(async(url:string)=>getPayload(url,url.includes("/projects")?[project]:url.includes("/targets")?[target]:url.includes("/audits")?[audit]:[])));
    render(<MemoryRouter initialEntries={["/mcp"]}><App/></MemoryRouter>);
    expect(await screen.findByText("Sans effet sur la cible")).toBeInTheDocument();
    expect(screen.getByRole("button",{name:/Lancer l’inspection passive/i})).toBeDisabled();
    expect(screen.getByText(/Aucun outil n’est appelé/)).toBeInTheDocument();
  });

  it("submits only the explicitly selected active call",async()=>{
    const fetchMock=vi.fn(async(url:string,options?:RequestInit)=>{
      if(url.endsWith("/health"))return payload({status:"ok",service:"agentsec-backend",version:"1.0.1"});
      if(options?.method==="POST")return payload({...audit,id:"active-1",passive:false,status:"queued",summary:{}},202);
      return payload(url.includes("/projects")?[project]:url.includes("/targets")?[target]:url.includes("/audits")?[audit]:[]);
    });
    vi.stubGlobal("fetch",fetchMock);
    render(<MemoryRouter initialEntries={["/mcp"]}><App/></MemoryRouter>);
    fireEvent.change(await screen.findByLabelText("Projet"),{target:{value:"project-1"}});
    fireEvent.change(screen.getByLabelText("Cible compatible"),{target:{value:"target-1"}});
    fireEvent.click(screen.getByRole("button",{name:/Actif — outil contrôlé/i}));
    fireEvent.change(screen.getByLabelText("Outil découvert"),{target:{value:"read_lab_note"}});
    fireEvent.change(screen.getByLabelText("Paramètres JSON exacts"),{target:{value:'{"note_id":"welcome"}'}});
    fireEvent.click(screen.getByLabelText(/J’autorise cet appel précis/i));
    const launch=screen.getByRole("button",{name:/Confirmer et lancer l’appel actif/i});
    expect(launch).toBeEnabled();
    fireEvent.click(launch);
    await waitFor(()=>expect(fetchMock.mock.calls.some(([,options])=>options?.method==="POST")).toBe(true));
    const post=fetchMock.mock.calls.find(([,options])=>options?.method==="POST");
    const body=JSON.parse(String(post?.[1]?.body));
    expect(body).toMatchObject({passive:false,confirm_active_operations:true,active_tool_calls:[{tool_name:"read_lab_note",arguments:{note_id:"welcome"}}]});
  });

  it("requires a separate confirmation for sensitive tools",async()=>{
    vi.stubGlobal("fetch",vi.fn(async(url:string)=>getPayload(url,url.includes("/projects")?[project]:url.includes("/targets")?[target]:url.includes("/audits")?[audit]:[])));
    render(<MemoryRouter initialEntries={["/mcp"]}><App/></MemoryRouter>);
    fireEvent.change(await screen.findByLabelText("Projet"),{target:{value:"project-1"}});
    fireEvent.change(screen.getByLabelText("Cible compatible"),{target:{value:"target-1"}});
    fireEvent.click(screen.getByRole("button",{name:/Actif — outil contrôlé/i}));
    fireEvent.change(screen.getByLabelText("Outil découvert"),{target:{value:"delete_demo_record"}});
    fireEvent.click(screen.getByLabelText(/J’autorise cet appel précis/i));
    const launch=screen.getByRole("button",{name:/Confirmer et lancer l’appel actif/i});
    expect(launch).toBeDisabled();
    fireEvent.click(screen.getByLabelText(/Je confirme séparément/i));
    expect(launch).toBeEnabled();
  });
});
