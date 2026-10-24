// @vitest-environment jsdom
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { File as NodeFile } from "node:buffer";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { Diagnostic, ImportDetail } from "../api/client";
import { fakeServer } from "../test/fakeServer";
import { renderWithI18n } from "../test/render";
import { ImportsWorkspace } from "./ImportsWorkspace";

const SOURCE = "00000000-0000-0000-0000-0000000000a1";
const SNAPSHOT = "00000000-0000-0000-0000-00000000000a";
const STAGER = { username: "volunteer", permissions: { review_identity: false, stage_snapshot: true } };
const OPTIONS = {
  sources: [{ id: SOURCE, key: "fixture", name: "Fictitious source", synthetic: true }],
  sheets: ["Data_operations", "Other_data", "Data_ports"],
  max_bytes: 5242880,
};

function diagnostic(overrides: Partial<Diagnostic> = {}): Diagnostic {
  return {
    source: { key: "fixture", name: "Fictitious source" },
    sheet: "Data_operations",
    sha256: "abc",
    bytes: 120,
    contract_version: "sheets-observed-v1",
    source_read: "end_unverified",
    normalization: "blocked",
    counts: {
      records_read: 3,
      rows_diagnosed: 2,
      blank_rows_skipped: 1,
      file_errors: 0,
      rows_with_errors: 1,
      rows_with_warnings: 0,
      errors: 1,
      warnings: 0,
    },
    issues_by_code: [{ code: "negative_count", severity: "error", count: 1 }],
    issues: [{ severity: "error", code: "negative_count", line: 3, column: 4, field: "nb_survivor" }],
    issues_truncated: false,
    stageable: true,
    blocking_reason: null,
    existing_snapshot: null,
    ...overrides,
  };
}

function detail(overrides: Partial<ImportDetail> = {}): ImportDetail {
  return {
    id: SNAPSHOT,
    source: { key: "fixture", name: "Fictitious source" },
    sheet: "Data_operations",
    created_at: "2026-10-24T12:00:00Z",
    staged_by: "volunteer",
    sha256: "abc",
    byte_count: 120,
    row_count: 2,
    source_read: "end_unverified",
    contract_version: "sheets-observed-v1",
    rows_with_errors: 1,
    errors_by_code: [{ code: "negative_count", rows: 1 }],
    review: { to_review: 1, blocked: 1, linked: 0 },
    ...overrides,
  };
}

function renderAt(path: string) {
  window.history.replaceState(null, "", path);
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return renderWithI18n(
    <QueryClientProvider client={client}>
      <ImportsWorkspace />
    </QueryClientProvider>,
  );
}

function server(routes: Parameters<typeof fakeServer>[0] = {}) {
  return fakeServer({
    "GET /api/private/v1/me/": () => ({ body: STAGER }),
    "GET /api/csrf/": () => ({ body: { csrfToken: "t" } }),
    "GET /api/private/v1/imports/options/": () => ({ body: OPTIONS }),
    "GET /api/private/v1/imports/": () => ({ body: { items: [], total_count: 0, has_next: false } }),
    "GET /api/private/v1/imports/:id/": () => ({ body: detail() }),
    ...routes,
  });
}

async function choose(label: string, option: string) {
  await userEvent.click(screen.getByRole("combobox", { name: label }));
  await userEvent.click(await screen.findByRole("option", { name: option }));
}

async function fillForm() {
  await screen.findByRole("heading", { name: "Add a data update" });
  await choose("Where does the file come from?", "Fictitious source (fictitious data)");
  await choose("Which tab is it?", "Operations at sea (Data_operations)");
  const file = new File(["date,type_ops\n"], "export.csv", { type: "text/csv" });
  await userEvent.upload(screen.getByLabelText("CSV file"), file);
}

// jsdom's FormData and File cannot go through Node's Request (openapi-fetch builds one), so uploads
// use Node's own classes here; browsers have a single implementation.
const NodeFormData = (await new Response(new URLSearchParams()).formData()).constructor as typeof FormData;

beforeEach(() => {
  window.history.replaceState(null, "", "/");
  vi.stubGlobal("FormData", NodeFormData);
  vi.stubGlobal("File", NodeFile);
});
afterEach(() => vi.unstubAllGlobals());

describe("imports", () => {
  it("shows only the sections this account may open", async () => {
    server();
    renderAt("/workspace/imports");
    const nav = await screen.findByRole("navigation", { name: "Private workspace" });
    expect(within(nav).getAllByRole("link").map((link) => link.textContent)).toEqual(["Data updates"]);
    expect(await screen.findByText("No export saved yet")).toBeTruthy();
  });

  it("checks a file without saving it, then saves it on an explicit click", async () => {
    const { calls } = server({
      "POST /api/private/v1/imports/diagnose/": () => ({ body: diagnostic() }),
      "POST /api/private/v1/imports/": () => ({ status: 201, body: { created: true, snapshot: detail() } }),
    });
    renderAt("/workspace/imports/new");
    await fillForm();
    await userEvent.click(screen.getByRole("button", { name: "Check the file" }));
    expect(await screen.findByRole("heading", { name: "What the file contains" })).toBeTruthy();
    expect(window.location.pathname).toBe("/workspace/imports/new/diagnostic");
    expect(screen.getByText(/last line has no line ending/)).toBeTruthy();
    expect(screen.getAllByText(/Negative count/).length).toBeGreaterThan(0);
    const diagnose = calls.find((call) => call.path === "/api/private/v1/imports/diagnose/");
    expect(diagnose?.body).toEqual({ source: SOURCE, sheet: "Data_operations", file: "export.csv" });
    expect(diagnose?.headers.get("X-CSRFToken")).toBe("t");
    expect(calls.some((call) => call.method === "POST" && call.path === "/api/private/v1/imports/")).toBe(false);

    await userEvent.click(screen.getByRole("button", { name: "Save this export" }));
    await waitFor(() => expect(window.location.pathname).toBe(`/workspace/imports/${SNAPSHOT}`));
    expect(await screen.findByText("Export saved. It stays private.")).toBeTruthy();
    // This account cannot review: the next step is named, without a link it could not open.
    expect(screen.getByText("Another person with the review permission takes the next step.")).toBeTruthy();
    expect(screen.queryByRole("link", { name: "Check the rows" })).toBeNull();
  });

  it("explains a file that cannot be saved and offers no save button", async () => {
    server({
      "POST /api/private/v1/imports/diagnose/": () => ({
        body: diagnostic({ stageable: false, blocking_reason: "read_partial", source_read: "partial" }),
      }),
    });
    renderAt("/workspace/imports/new");
    await fillForm();
    await userEvent.click(screen.getByRole("button", { name: "Check the file" }));
    expect(await screen.findByText(/only part of it could be read/)).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Save this export" })).toBeNull();
  });

  it("points to the export already saved for the same file", async () => {
    server({
      "POST /api/private/v1/imports/diagnose/": () => ({ body: diagnostic({ existing_snapshot: SNAPSHOT }) }),
    });
    renderAt("/workspace/imports/new");
    await fillForm();
    await userEvent.click(screen.getByRole("button", { name: "Check the file" }));
    expect((await screen.findByRole("link", { name: "Open it" })).getAttribute("href")).toBe(`/workspace/imports/${SNAPSHOT}`);
    expect(screen.queryByRole("button", { name: "Save this export" })).toBeNull();
  });

  it("asks for every field before checking anything", async () => {
    const { calls } = server();
    renderAt("/workspace/imports/new");
    await screen.findByRole("heading", { name: "Add a data update" });
    await userEvent.click(screen.getByRole("button", { name: "Check the file" }));
    expect(screen.getByText("Choose where the file comes from.")).toBeTruthy();
    expect(screen.getByText("Choose a CSV file.")).toBeTruthy();
    expect(calls.some((call) => call.method === "POST")).toBe(false);
  });

  it("changing the source after a check forgets the diagnostic, so it cannot be saved elsewhere", async () => {
    server({ "POST /api/private/v1/imports/diagnose/": () => ({ body: diagnostic() }) });
    renderAt("/workspace/imports/new");
    await fillForm();
    await userEvent.click(screen.getByRole("button", { name: "Check the file" }));
    await screen.findByRole("heading", { name: "What the file contains" });
    await userEvent.click(screen.getByRole("link", { name: "Check another file" }));
    await choose("Which tab is it?", "Port list (Data_ports)");
    act(() => {
      window.history.pushState(null, "", "/workspace/imports/new/diagnostic");
      window.dispatchEvent(new PopStateEvent("popstate"));
    });
    expect(await screen.findByText("The file is no longer in memory")).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Save this export" })).toBeNull();
  });

  it("a failed save stays on the diagnostic with a message", async () => {
    server({
      "POST /api/private/v1/imports/diagnose/": () => ({ body: diagnostic() }),
      "POST /api/private/v1/imports/": () => ({ status: 413, body: { code: "http_413", detail: "Request too large" } }),
    });
    renderAt("/workspace/imports/new");
    await fillForm();
    await userEvent.click(screen.getByRole("button", { name: "Check the file" }));
    await userEvent.click(await screen.findByRole("button", { name: "Save this export" }));
    expect(await screen.findByText("The server refused the file: it is too large.")).toBeTruthy();
    expect(window.location.pathname).toBe("/workspace/imports/new/diagnostic");
  });

  it("a reloaded diagnostic asks for the file again instead of inventing a result", async () => {
    server();
    renderAt("/workspace/imports/new/diagnostic");
    expect(await screen.findByText("The file is no longer in memory")).toBeTruthy();
  });

  it("an account that cannot add exports gets no add button", async () => {
    server({
      "GET /api/private/v1/me/": () => ({ body: { username: "r", permissions: { review_identity: true, stage_snapshot: false } } }),
    });
    renderAt("/workspace/imports");
    await screen.findByText("No export saved yet");
    expect(screen.queryByRole("link", { name: "Add a data update" })).toBeNull();
  });
});
