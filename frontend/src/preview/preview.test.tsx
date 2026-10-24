// @vitest-environment jsdom
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import App from "../App";
import { fakeServer } from "../test/fakeServer";
import { renderWithI18n } from "../test/render";

// MapLibre needs WebGL; the map is replaced by its point count.
vi.mock("../components/Map", () => ({
  EventMap: ({ points }: { points: readonly unknown[] }) => <p>{`${points.length} map points`}</p>,
}));

const ROW = "00000000-0000-0000-0000-0000000000b1";
const SNAPSHOT = "00000000-0000-0000-0000-00000000000a";
const ITEM = {
  id: ROW,
  snapshot: SNAPSHOT,
  sheet: "Data_operations",
  line: 12,
  exported_at: "2026-10-24T12:00:00Z",
  source: { key: "fixture", name: "Fictitious source" },
  synthetic: true,
  status: "to_review",
  error_codes: [],
  occurred_on: "2024-02-03",
  kind: "rescue",
  people: 42,
  women: 10,
  minors: null,
  deaths: null,
  port_label: "Port fictif",
  boat_type: null,
  position: { longitude: 12.25, latitude: 34.5, inferred_hemisphere: false },
  image_count: 0,
};
const EMPTY_PUBLIC = {
  "GET /api/v1/events/": () => ({ body: { items: [], total_count: 0, has_next: false, data_mode: "production" } }),
  "GET /api/v1/map-points/": () => ({ body: { points: [], located_count: 0, truncated: false } }),
};

function renderApp() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return renderWithI18n(
    <QueryClientProvider client={client}>
      <App />
    </QueryClientProvider>,
  );
}

beforeEach(() => window.history.replaceState(null, "", "/"));
afterEach(() => vi.unstubAllGlobals());

describe("main screen preview", () => {
  it("visitors see only published events and never call the preview", async () => {
    const { calls } = fakeServer({
      ...EMPTY_PUBLIC,
      "GET /api/private/v1/me/": () => ({ status: 401, body: { code: "not_authenticated", detail: "x" } }),
    });
    renderApp();
    expect(await screen.findByText("No published event")).toBeTruthy();
    await screen.findByRole("link", { name: "Team sign-in" });
    expect(screen.queryByRole("group", { name: "Data shown" })).toBeNull();
    expect(calls.some((call) => call.path.startsWith("/api/private/v1/preview/"))).toBe(false);
  });

  it("a signed-in reviewer sees the latest export, clearly marked private, and can open a row", async () => {
    const { calls } = fakeServer({
      ...EMPTY_PUBLIC,
      "GET /api/private/v1/me/": () => ({ body: { username: "r", permissions: { review_identity: true, stage_snapshot: true } } }),
      "GET /api/private/v1/preview/events/": () => ({
        body: { items: [ITEM], total_count: 1, has_next: false, counts: { to_review: 1, blocked: 0, linked: 0 } },
      }),
      "GET /api/private/v1/preview/map-points/": () => ({
        body: { points: [{ id: ROW, longitude: 12.25, latitude: 34.5, kind: "rescue", status: "to_review" }], located_count: 1, truncated: false },
      }),
      "GET /api/private/v1/preview/events/:id/": () => ({ body: ITEM }),
    });
    renderApp();
    expect(await screen.findByText(/latest export as received/)).toBeTruthy();
    expect(await screen.findByText("1 map points")).toBeTruthy();
    const list = await screen.findByRole("heading", { name: "Rows of the export" });
    expect(list).toBeTruthy();
    await userEvent.click(screen.getByRole("button", { name: /Port fictif/ }));
    const dialog = await screen.findByRole("dialog");
    expect(within(dialog).getByText("Private preview: not checked, not published")).toBeTruthy();
    expect(within(dialog).getByRole("link", { name: "Check this row" }).getAttribute("href")).toBe(
      `/workspace/review/${SNAPSHOT}/rows/${ROW}`,
    );
    // Published events stay one click away, and the public endpoints are used for them.
    await userEvent.keyboard("{Escape}");
    await userEvent.click(screen.getByRole("button", { name: "Published" }));
    expect(await screen.findByText("0 map points")).toBeTruthy();
    expect(calls.some((call) => call.path === "/api/v1/events/")).toBe(true);
  });
});
