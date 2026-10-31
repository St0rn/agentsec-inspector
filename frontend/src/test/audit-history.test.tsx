import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, expect, it, vi } from "vitest";
import { AuditHistory } from "../components/AuditHistory";
import type { Audit } from "../types";

const audit:Audit={id:"a-history",project_id:"p1",target_id:"t1",audit_type:"prompt_injection",status:"completed",passive:false,configuration:{scenario_id:"pi.direct"},summary:{test_status:"PASS"},error:null,created_at:"2026-10-30T10:00:00Z",started_at:null,finished_at:null};

beforeEach(()=>localStorage.setItem("agentsec-api-token","test-token"));

it("opens a permanent audit detail with requests, events, evidence and findings",async()=>{
  vi.stubGlobal("fetch",vi.fn(async(input:RequestInfo|URL)=>{const url=String(input);const value=url.endsWith("/health")?{status:"ok",service:"agentsec-backend",version:"1.1.0"}:{audit,target:{name:"Range"},executions:[{request_data:{messages:["payload"]},response_data:{text:"safe"}}],events:[{event_type:"llm_exchange"}],evidence:[{title:"preuve"}],findings:[],historical_data_notice:null};return new Response(JSON.stringify(value),{status:200,headers:{"Content-Type":"application/json"}})}));
  render(<AuditHistory audits={[audit]}/>);
  fireEvent.click(screen.getByText("prompt_injection"));
  expect(await screen.findByText("Détail de l’audit")).toBeInTheDocument();
  expect(screen.getByText("Exécutions")).toBeInTheDocument();
  expect(screen.getByText("Payload")).toBeInTheDocument();
  expect(screen.getByText(/Requête enregistrée par une version antérieure/)).toBeInTheDocument();
  expect(screen.getByText(/payload/)).toBeInTheDocument();
  expect(screen.getByText(/llm_exchange/)).toBeInTheDocument();
  expect(screen.getByText(/preuve/)).toBeInTheDocument();
});
