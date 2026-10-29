import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, expect, it, vi } from "vitest";
import App from "../App";

beforeEach(()=>{
  localStorage.setItem("agentsec-api-token","test-token");
  vi.stubGlobal("fetch",vi.fn(async()=>new Response("[]",{status:200,headers:{"Content-Type":"application/json"}})));
});

it("configures a generic chatbot through a target URL",async()=>{
  render(<MemoryRouter initialEntries={["/targets"]}><App/></MemoryRouter>);
  fireEvent.click(await screen.findByRole("button",{name:/Ajouter/i}));
  fireEvent.change(screen.getByLabelText("Type de cible"),{target:{value:"chatbot"}});
  const url=screen.getByLabelText(/URL cible/);
  expect(url).toBeRequired();
  expect(url).toHaveAttribute("type","url");
  expect(screen.getByText("Adaptation à une API de chatbot")).toBeInTheDocument();
  expect(screen.getAllByText(/response_path/).length).toBeGreaterThan(0);
});

it("creates and deletes a target with the declared URL",async()=>{
  const project={id:"p1",client_name:"Acme",engagement_name:"Chatbot audit"};
  const existing={id:"t1",project_id:"p1",name:"Support bot",target_type:"chatbot",endpoint:"https://chat.example.test/audit",configuration:{},remote_authorized:true};
  const fetchMock=vi.fn(async(input:RequestInfo|URL,options?:RequestInit)=>{
    const url=String(input);
    if(options?.method==="POST")return new Response(JSON.stringify(existing),{status:201,headers:{"Content-Type":"application/json"}});
    if(options?.method==="DELETE")return new Response(null,{status:204});
    const value=url.includes("/projects")?[project]:url.includes("/targets")?[existing]:[];
    return new Response(JSON.stringify(value),{status:200,headers:{"Content-Type":"application/json"}});
  });
  vi.stubGlobal("fetch",fetchMock);

  render(<MemoryRouter initialEntries={["/targets"]}><App/></MemoryRouter>);
  expect(await screen.findByText("Support bot")).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button",{name:/Ajouter/i}));
  fireEvent.change(screen.getByLabelText("Projet"),{target:{value:"p1"}});
  fireEvent.change(screen.getByLabelText("Nom"),{target:{value:"Support bot"}});
  fireEvent.change(screen.getByLabelText("Type de cible"),{target:{value:"chatbot"}});
  fireEvent.change(screen.getByLabelText(/URL cible/),{target:{value:"https://chat.example.test/audit"}});
  fireEvent.change(screen.getByLabelText(/^Configuration JSON non secrète/),{target:{value:'{"message_path":"message","response_path":"answer"}'}});
  fireEvent.click(screen.getByLabelText(/connexions à cette cible distante/));
  fireEvent.click(screen.getByRole("button",{name:"Enregistrer"}));

  await waitFor(()=>expect(fetchMock.mock.calls.some(([,options])=>options?.method==="POST")).toBe(true));
  const post=fetchMock.mock.calls.find(([,options])=>options?.method==="POST");
  expect(JSON.parse(String(post?.[1]?.body))).toMatchObject({target_type:"chatbot",endpoint:"https://chat.example.test/audit",remote_authorized:true});

  fireEvent.click(screen.getByRole("button",{name:""}));
  await waitFor(()=>expect(fetchMock.mock.calls.some(([,options])=>options?.method==="DELETE")).toBe(true));
});

it("shows malformed target configuration as a form error",async()=>{
  render(<MemoryRouter initialEntries={["/targets"]}><App/></MemoryRouter>);
  fireEvent.click(await screen.findByRole("button",{name:/Ajouter/i}));
  fireEvent.change(screen.getByLabelText(/^Configuration JSON non secrète/),{target:{value:"{"}});
  fireEvent.submit(screen.getByRole("button",{name:"Enregistrer"}).closest("form")!);
  expect(await screen.findByRole("alert")).toHaveTextContent(/JSON|Unexpected|position/i);
});
