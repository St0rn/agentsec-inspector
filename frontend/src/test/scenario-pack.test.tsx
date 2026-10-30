import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, expect, it, vi } from "vitest";
import App from "../App";

beforeEach(()=>localStorage.setItem("agentsec-api-token","test-token"));

it("rejects malformed scenario pack JSON before sending it",async()=>{
  const fetchMock=vi.fn(async(input:RequestInfo|URL,options?:RequestInit)=>{
    void options;
    const value=String(input).endsWith("/health")?{status:"ok",service:"agentsec-backend",version:"1.0.1"}:[];
    return new Response(JSON.stringify(value),{status:200,headers:{"Content-Type":"application/json"}});
  });
  vi.stubGlobal("fetch",fetchMock);
  render(<MemoryRouter initialEntries={["/settings"]}><App/></MemoryRouter>);
  const editor=await screen.findByLabelText("Pack de scénarios JSON");
  fireEvent.change(editor,{target:{value:"{invalid"}});
  fireEvent.click(screen.getByRole("button",{name:/Valider et importer/i}));
  expect(await screen.findByRole("alert")).toHaveTextContent(/JSON/i);
  expect(fetchMock.mock.calls.filter(([,options]:[RequestInfo|URL,RequestInit?])=>options?.method==="POST")).toHaveLength(0);
});

it("imports a declarative scenario pack through the API",async()=>{
  const fetchMock=vi.fn(async(url:string,options?:RequestInit)=>new Response(JSON.stringify(url.endsWith("/health")?{status:"ok",service:"agentsec-backend",version:"1.0.1"}:options?.method==="POST"?{pack_id:"team.redteam",pack_version:"1.0.0",imported:1,updated:0}:[]),{status:options?.method==="POST"?201:200,headers:{"Content-Type":"application/json"}}));
  vi.stubGlobal("fetch",fetchMock);
  render(<MemoryRouter initialEntries={["/settings"]}><App/></MemoryRouter>);
  fireEvent.click(await screen.findByRole("button",{name:/Valider et importer/i}));
  expect(await screen.findByText(/1 importé/)).toBeInTheDocument();
  await waitFor(()=>expect(fetchMock.mock.calls.some(([url,options])=>String(url).includes("/scenarios/import")&&options?.method==="POST")).toBe(true));
});
