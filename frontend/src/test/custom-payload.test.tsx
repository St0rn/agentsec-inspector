import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, expect, it, vi } from "vitest";
import App from "../App";

const project={id:"p1",client_name:"Acme",engagement_name:"AI red team"};
const target={id:"t1",project_id:"p1",name:"Range",target_type:"chatbot",endpoint:"http://127.0.0.1:8789/target/api/chat/stream",configuration:{response_format:"ndjson"},remote_authorized:false};
const audit={id:"a1",project_id:"p1",target_id:"t1",audit_type:"custom_payload",status:"completed",passive:false,configuration:{category:"jailbreak"},summary:{test_status:"PASS"},error:null,created_at:"2026-10-30T10:00:00Z",started_at:null,finished_at:null};

beforeEach(()=>localStorage.setItem("agentsec-api-token","test-token"));

it("submits multi-turn custom payloads with structured security rules",async()=>{
  const fetchMock=vi.fn(async(input:RequestInfo|URL,options?:RequestInit)=>{const url=String(input);let value:unknown=[];if(url.endsWith("/health"))value={status:"ok",service:"agentsec-backend",version:"1.1.0"};else if(url.includes("/projects"))value=[project];else if(url.includes("/targets"))value=[target];else if(options?.method==="POST")value=audit;return new Response(JSON.stringify(value),{status:options?.method==="POST"?202:200,headers:{"Content-Type":"application/json"}})});
  vi.stubGlobal("fetch",fetchMock);
  render(<MemoryRouter initialEntries={["/custom-payload"]}><App/></MemoryRouter>);
  await screen.findByRole("option",{name:/Acme/});
  fireEvent.change(screen.getByLabelText("Projet"),{target:{value:"p1"}});
  await screen.findByRole("option",{name:"Range"});
  fireEvent.change(screen.getByLabelText("Cible"),{target:{value:"t1"}});
  fireEvent.click(screen.getByRole("button",{name:/Ajouter un tour/}));
  fireEvent.change(screen.getByLabelText("Payload 2"),{target:{value:"Second tour contrôlé"}});
  const checkboxes=screen.getAllByRole("checkbox");
  fireEvent.click(checkboxes[checkboxes.length-1]);
  const run=screen.getByRole("button",{name:/Lancer le test/});
  await waitFor(()=>expect(run).not.toBeDisabled());
  fireEvent.click(run);
  await waitFor(()=>expect(fetchMock.mock.calls.some(([url,options])=>String(url).includes("/audits/custom")&&options?.method==="POST")).toBe(true));
  const call=fetchMock.mock.calls.find(([url,options])=>String(url).includes("/audits/custom")&&options?.method==="POST");
  const body=JSON.parse(String(call?.[1]?.body));
  expect(body.payloads).toHaveLength(2);
  expect(body.security_rules[0]).toMatchObject({rule_type:"marker_absent",required:true});
  expect(body.confirm_active_test).toBe(true);
});
