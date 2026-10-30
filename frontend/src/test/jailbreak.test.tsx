import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, expect, it, vi } from "vitest";
import App from "../App";

const project={id:"project-1",client_name:"Lab",engagement_name:"Jailbreak",description:"",authorized_scope:"Loopback",start_date:null,end_date:null,created_at:"2026-01-01",updated_at:"2026-01-01"};
const target={id:"target-1",project_id:"project-1",name:"LLM Lab",target_type:"agent_lab",endpoint:"http://127.0.0.1:8877/chat",configuration:{},remote_authorized:false,created_at:"2026-01-01"};
const jailbreak={id:"jb.authority-impersonation",version:"1.0.0",name:"Authority Impersonation Jailbreak",description:"Controlled test",category:"jailbreak",references:["OWASP-LLM01:2025"]};
const injection={id:"pi.direct",version:"1.0.0",name:"Direct Prompt Injection",description:"Controlled test",category:"prompt-injection",references:["OWASP-LLM01:2025"]};

function payload(value:unknown,status=200){return new Response(JSON.stringify(value),{status,headers:{"Content-Type":"application/json"}})}

beforeEach(()=>localStorage.setItem("agentsec-api-token","test-token"));

it("lists dedicated jailbreak scenarios and submits the selected controlled test",async()=>{
  const fetchMock=vi.fn(async(url:string,options?:RequestInit)=>{
    if(url.endsWith("/health"))return payload({status:"ok",service:"agentsec-backend",version:"1.0.1"});
    if(options?.method==="POST")return payload({id:"audit-1",project_id:"project-1",target_id:"target-1",audit_type:"jailbreak",status:"queued",passive:false,configuration:{},summary:{},error:null,created_at:"2026-01-01",started_at:null,finished_at:null},202);
    if(url.includes("/audits/audit-1"))return payload({id:"audit-1",project_id:"project-1",target_id:"target-1",audit_type:"jailbreak",status:"completed",passive:false,configuration:{},summary:{test_status:"PASS"},error:null,created_at:"2026-01-01",started_at:"2026-01-01",finished_at:"2026-01-01"});
    return payload(url.includes("/projects")?[project]:url.includes("/targets")?[target]:url.includes("/scenarios")?[jailbreak,injection]:[]);
  });
  vi.stubGlobal("fetch",fetchMock);
  render(<MemoryRouter initialEntries={["/jailbreak"]}><App/></MemoryRouter>);
  expect(await screen.findByText("Jailbreak Tester")).toBeInTheDocument();
  expect(await screen.findByRole("option",{name:/Authority Impersonation Jailbreak/})).toBeInTheDocument();
  const scenario=screen.getByLabelText("Scénario versionné");
  expect(scenario).toHaveTextContent("Authority Impersonation Jailbreak");
  expect(scenario).not.toHaveTextContent("Direct Prompt Injection");
  fireEvent.change(screen.getByLabelText("Projet"),{target:{value:"project-1"}});
  fireEvent.change(screen.getByLabelText("Cible compatible"),{target:{value:"target-1"}});
  fireEvent.click(screen.getByRole("button",{name:/Confirmer et lancer le test/i}));
  await waitFor(()=>expect(fetchMock.mock.calls.some(([,options])=>options?.method==="POST")).toBe(true));
  const post=fetchMock.mock.calls.find(([,options])=>options?.method==="POST");
  expect(JSON.parse(String(post?.[1]?.body))).toMatchObject({scenario_id:"jb.authority-impersonation",scenario_version:"1.0.0",confirm_active_test:true});
});
