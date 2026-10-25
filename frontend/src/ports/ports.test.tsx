// @vitest-environment jsdom
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { PortLabel, PortLabelDetail, PortRef } from "../api/client";
import { fakeServer } from "../test/fakeServer";
import { renderWithI18n } from "../test/render";
import { PortsWorkspace } from "./PortsWorkspace";

const CLEAR = "a".repeat(32);
const UNCLEAR = "b".repeat(32);
const REVIEWER = { username: "reviewer", permissions: { review_identity: true, stage_snapshot: true } };
const PORT_A: PortRef = { id: "00000000-0000-0000-0000-0000000000d1", name: "Port fictif A", country_code: "", position: { longitude: 10.2, latitude: 36.8 }, location_source: "sheet_row" };
const PORT_B: PortRef = { id: "00000000-0000-0000-0000-0000000000d2", name: "Port fictif B", country_code: "IT", position: null, location_source: "" };

function label(overrides: Partial<PortLabel> = {}): PortLabel {
  return {
    id: CLEAR,
    label: "Port fictif A",
    source: { key: "fixture", name: "Fictitious source" },
    status: "to_read",
    operations: 2,
    port_list_row: { id: "00000000-0000-0000-0000-0000000000e1", line: 2, position: { longitude: 10.2, latitude: 36.8 }, error_codes: [] },
    suggested_port: null,
    reading: null,
    ...overrides,
  };
}

const UNCLEAR_LABEL = label({
  id: UNCLEAR,
  label: "Port fictif B",
  operations: 1,
  port_list_row: { id: "00000000-0000-0000-0000-0000000000e2", line: 3, position: null, error_codes: ["hemisphere_ambiguous"] },
});

function detail(base: PortLabel, overrides: Partial<PortLabelDetail> = {}): PortLabelDetail {
  return {
    ...base,
    port_list_cells: { headers: ["nom", "latitude", "longitude"], cells: [base.label, "39° 26.32", "0° 18.59"] },
    operation_lines: [{ line: 4, occurred_on: "2024-02-05" }],
    ...overrides,
  };
}

function renderAt(path: string) {
  window.history.replaceState(null, "", path);
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return renderWithI18n(
    <QueryClientProvider client={client}>
      <PortsWorkspace />
    </QueryClientProvider>,
  );
}

function server(routes: Parameters<typeof fakeServer>[0] = {}) {
  return fakeServer({
    "GET /api/private/v1/me/": () => ({ body: REVIEWER }),
    "GET /api/csrf/": () => ({ body: { csrfToken: "t" } }),
    "GET /api/private/v1/ports/labels/": () => ({
      body: { items: [label(), UNCLEAR_LABEL], total_count: 2, has_next: false, counts: { to_read: 2, read: 0 } },
    }),
    "GET /api/private/v1/ports/labels/:id/": (call) => ({
      body: call.path.includes(UNCLEAR) ? detail(UNCLEAR_LABEL) : detail(label()),
    }),
    "GET /api/private/v1/vessels/": () => ({ body: { items: [] } }),
    "GET /api/private/v1/ports/": () => ({ body: { items: [PORT_A, PORT_B] } }),
    ...routes,
  });
}

beforeEach(() => window.history.replaceState(null, "", "/"));
afterEach(() => vi.unstubAllGlobals());

describe("port names", () => {
  it("lists names to read in plain words, with opaque addresses", async () => {
    server();
    renderAt("/workspace/ports");
    const table = await screen.findByRole("table", { name: "Port names: To read" });
    expect(within(table).getByText("Yes, with a position")).toBeTruthy();
    expect(within(table).getByText("Yes, position unclear")).toBeTruthy();
    const link = within(table).getByRole("link", { name: "“Port fictif B”" });
    expect(link.getAttribute("href")).toBe(`/workspace/ports/labels/${UNCLEAR}?status=to_read&offset=0`);
    expect(link.getAttribute("href")).not.toContain("fictif");
  });

  it("an unclear position must be entered, and 0,0 is refused before sending", async () => {
    const { calls } = server({
      "POST /api/private/v1/ports/labels/:id/decision/": () => ({
        body: detail(UNCLEAR_LABEL, {
          status: "read",
          reading: { interpretation: "port", ports: [PORT_B], vessel: null, approved_by: "reviewer", approved_at: "2026-10-24T12:00:00Z", reason: "Chart" },
        }),
      }),
    });
    renderAt(`/workspace/ports/labels/${UNCLEAR}`);
    expect(await screen.findByText(/position is unclear/)).toBeTruthy();
    expect(screen.getByText("39° 26.32")).toBeTruthy();
    await userEvent.click(screen.getByRole("radio", { name: "One port" }));
    // The port list position is unusable, so creating from it is not offered.
    expect(screen.queryByRole("radio", { name: /position given in the port list/ })).toBeNull();
    await userEvent.click(screen.getByRole("radio", { name: "A new port, at a position I enter" }));
    await userEvent.type(screen.getByRole("textbox", { name: "Latitude" }), "0");
    await userEvent.type(screen.getByRole("textbox", { name: "Longitude" }), "0");
    await userEvent.type(screen.getByRole("textbox", { name: "Reason" }), "Chart{Enter}");
    await userEvent.click(screen.getByRole("button", { name: "Save the reading" }));
    expect(screen.getAllByText("Position: 0, 0 is not a port.").length).toBeGreaterThan(0);
    expect(calls.some((call) => call.method === "POST")).toBe(false);

    await userEvent.clear(screen.getByRole("textbox", { name: "Latitude" }));
    await userEvent.type(screen.getByRole("textbox", { name: "Latitude" }), "39,4387");
    await userEvent.clear(screen.getByRole("textbox", { name: "Longitude" }));
    await userEvent.type(screen.getByRole("textbox", { name: "Longitude" }), "-0.3098");
    await userEvent.type(screen.getByRole("textbox", { name: /Country code/ }), "es");
    await userEvent.click(screen.getByRole("button", { name: "Save the reading" }));
    expect(await screen.findByText("Reading saved. It stays private.")).toBeTruthy();
    const post = calls.find((call) => call.method === "POST");
    expect(post?.body).toEqual({
      interpretation: "port",
      // The entered position keeps the link to the unclear port-list row.
      new_port: { from_port_list: true, longitude: -0.3098, latitude: 39.4387, country_code: "ES" },
      reason: "Chart",
    });
  });

  it("a clear position can create the port from the port list", async () => {
    const { calls } = server({
      "POST /api/private/v1/ports/labels/:id/decision/": () => ({ status: 409, body: { code: "conflict", detail: "x" } }),
    });
    renderAt(`/workspace/ports/labels/${CLEAR}`);
    await screen.findByText(/In the port list \(line 2\)/);
    await userEvent.click(screen.getByRole("radio", { name: "One port" }));
    await userEvent.click(screen.getByRole("radio", { name: /position given in the port list/ }));
    await userEvent.type(screen.getByRole("textbox", { name: "Reason" }), "Port list");
    await userEvent.click(screen.getByRole("button", { name: "Save the reading" }));
    expect(await screen.findByText(/Someone else changed this event/)).toBeTruthy();
    expect(calls.find((call) => call.method === "POST")?.body).toEqual({
      interpretation: "port",
      new_port: { from_port_list: true, country_code: "" },
      reason: "Port list",
    });
    // The current state is read again after a conflict.
    await waitFor(() => expect(calls.filter((call) => call.path === `/api/private/v1/ports/labels/${CLEAR}/`).length).toBe(2));
  });

  it("several ports are chosen one by one", async () => {
    const { calls } = server({
      "POST /api/private/v1/ports/labels/:id/decision/": () => ({ body: detail(label()) }),
    });
    renderAt(`/workspace/ports/labels/${CLEAR}`);
    await screen.findByText(/In the port list/);
    await userEvent.click(screen.getByRole("radio", { name: "Several ports" }));
    const search = screen.getByRole("combobox", { name: "Add a port" });
    await userEvent.type(search, "Port");
    await userEvent.click(await screen.findByRole("option", { name: /Port fictif A/ }));
    await userEvent.type(search, "Port");
    await userEvent.click(await screen.findByRole("option", { name: /Port fictif B/ }));
    expect(within(screen.getByRole("list", { name: "Chosen ports" })).getAllByRole("listitem")).toHaveLength(2);
    await userEvent.type(screen.getByRole("textbox", { name: "Reason" }), "Two ports named");
    await userEvent.click(screen.getByRole("button", { name: "Save the reading" }));
    await waitFor(() =>
      expect(calls.find((call) => call.method === "POST")?.body).toEqual({
        interpretation: "ports",
        ports: [PORT_A.id, PORT_B.id],
        reason: "Two ports named",
      }),
    );
  });

  it("asks before leaving a name with a choice made but nothing saved", async () => {
    server();
    const confirm = vi.spyOn(window, "confirm").mockReturnValue(false);
    renderAt(`/workspace/ports/labels/${CLEAR}`);
    await screen.findByText(/In the port list/);
    await userEvent.click(screen.getByRole("radio", { name: "Not a port" }));
    await userEvent.click(screen.getByRole("button", { name: "Close" }));
    expect(confirm).toHaveBeenCalledOnce();
    expect(window.location.pathname).toBe(`/workspace/ports/labels/${CLEAR}`);
    confirm.mockRestore();
  });

  it("save and next opens the next name to read once the server confirmed", async () => {
    server({
      "POST /api/private/v1/ports/labels/:id/decision/": () => ({
        body: detail(label(), {
          status: "read",
          reading: { interpretation: "not_a_port", ports: [], vessel: null, approved_by: "reviewer", approved_at: "2026-10-24T12:00:00Z", reason: "Region" },
        }),
      }),
    });
    renderAt(`/workspace/ports/labels/${CLEAR}`);
    await screen.findByText(/In the port list/);
    await userEvent.click(screen.getByRole("radio", { name: "Not a port" }));
    await userEvent.type(screen.getByRole("textbox", { name: "Reason" }), "Region");
    await userEvent.click(screen.getByRole("button", { name: "Save and read the next name" }));
    await waitFor(() => expect(window.location.pathname).toBe(`/workspace/ports/labels/${UNCLEAR}`));
  });

  it("a ship cannot be chosen while no ship is registered", async () => {
    const { calls } = server();
    renderAt(`/workspace/ports/labels/${CLEAR}`);
    await screen.findByText(/In the port list/);
    await userEvent.click(screen.getByRole("radio", { name: "A ship" }));
    expect(screen.getAllByText(/No ship is registered yet/).length).toBeGreaterThan(0);
    await userEvent.type(screen.getByRole("textbox", { name: "Reason" }), "Transfer");
    await userEvent.click(screen.getByRole("button", { name: "Save the reading" }));
    expect(calls.some((call) => call.method === "POST")).toBe(false);
  });
});
