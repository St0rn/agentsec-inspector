import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { MCPResultView } from "../components/MCPResultView";

describe("MCP result presentation", () => {
  it("renders paginated records and exposes the original MCP evidence", () => {
    render(<MCPResultView summary={{
      mode: "active", tools: 26, resources: 47, prompts: 4, observations: 2,
      discovery: {server_info: {name: "sondahub"}},
      active_tool_calls: [{
        tool_name: "list_records", status: "SUCCESS", duration_ms: 280,
        arguments: {api: "store", collection: "products", filters: {in_stock: true}},
        result: {structuredContent: {
          data: [{id: 4, name: "Fjord", in_stock: true}, {id: 5, name: "Kettleworth", in_stock: true}],
          meta: {page: 2, pages: 566, limit: 3, total: 1698},
        }, content: [{type: "text", text: "MCP original response"}]}
      }]
    }}/>);
    expect(screen.getByText("47")).toBeInTheDocument();
    expect(screen.getByText("Fjord")).toBeInTheDocument();
    expect(screen.getByText("Kettleworth")).toBeInTheDocument();
    expect(screen.getByText(/Total filtré 1698/)).toBeInTheDocument();
    expect(screen.getByText("SUCCESS")).toBeInTheDocument();
    fireEvent.click(screen.getByText("Voir la réponse MCP brute"));
    expect(screen.getByText(/MCP original response/)).toBeInTheDocument();
  });

  it("renders collections with counts and non-structured MCP results", () => {
    render(<MCPResultView summary={{
      mode: "active", tools: 1, resources: 0, prompts: 0, observations: 0,
      active_tool_calls: [
        {tool_name: "describe_api", status: "SUCCESS", duration_ms: 120,
          result: {structuredContent: {collections: [{name: "devices", records: 500, fields: [{name: "id"}], relations: []}]}}},
        {tool_name: "add", status: "SUCCESS", duration_ms: 10,
          result: {structuredContent: {sum: 42}}},
        {tool_name: "fail", status: "ERROR", duration_ms: 1, error: "Controlled failure", result: {}}
      ]
    }}/>);
    expect(screen.getByText("devices")).toBeInTheDocument();
    expect(screen.getByText("500")).toBeInTheDocument();
    expect(screen.getByText(/"sum": 42/)).toBeInTheDocument();
    expect(screen.getByText("Controlled failure")).toBeInTheDocument();
  });

  it("allows expanding large structured data tables", () => {
    const rows = Array.from({length: 12}, (_, i) => ({id: i + 1, name: `demo-${i + 1}`}));
    render(<MCPResultView summary={{
      mode: "active", tools: 1,
      active_tool_calls: [{
        tool_name: "list_records", status: "SUCCESS", duration_ms: 5,
        result: {structuredContent: {data: rows}}
      }]
    }}/>);
    expect(screen.queryByText("demo-12")).not.toBeInTheDocument();
    fireEvent.click(screen.getByText("Afficher tout"));
    expect(screen.getByText("demo-12")).toBeInTheDocument();
    fireEvent.click(screen.getByText("Réduire"));
    expect(screen.queryByText("demo-12")).not.toBeInTheDocument();
  });
});
