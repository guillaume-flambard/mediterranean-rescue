// @vitest-environment jsdom
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { fakeServer } from "../test/fakeServer";
import { renderWithI18n } from "../test/render";
import { TeamHistory } from "./TeamHistory";

const ME = {
  username: "ana",
  decisions: 1,
  permissions: { review_identity: true, stage_snapshot: false, prepare_drafts: false, publish: false, invite: false },
};
const ITEM = {
  id: "verify:1",
  kind: "verify",
  at: "2026-10-25T09:30:00Z",
  actor: "ana",
  reason: "Matches the sentence",
  detail: "new",
  subject: { occurred_on: "2024-02-03", kind: "rescue", people: 42, label: null },
  path: "/workspace/review/s/rows/r",
};

afterEach(() => vi.unstubAllGlobals());

describe("history", () => {
  it("shows my decisions with their reason, then the team's, filtered by kind", async () => {
    window.history.replaceState(null, "", "/workspace/history");
    const { calls } = fakeServer({
      "GET /api/private/v1/me/": () => ({ body: ME }),
      "GET /api/private/v1/history/": (call) => ({
        body: {
          items: call.query.get("scope") === "team" ? [ITEM, { ...ITEM, id: "verify:2", actor: "ben", reason: "Checked twice" }] : [ITEM],
          has_next: false,
        },
      }),
    });
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    renderWithI18n(
      <QueryClientProvider client={client}>
        <TeamHistory />
      </QueryClientProvider>,
    );
    expect(await screen.findByText("You verified the operation of Feb 3, 2024 (Rescue operation, 42 people)")).toBeTruthy();
    expect(screen.getByText("Matches the sentence")).toBeTruthy();
    expect(screen.getByRole("link", { name: /See/ }).getAttribute("href")).toBe("/workspace/review/s/rows/r");
    await userEvent.click(screen.getByRole("button", { name: /The whole team/ }));
    expect(await screen.findByText("ben verified the operation of Feb 3, 2024 (Rescue operation, 42 people)")).toBeTruthy();
    await userEvent.click(screen.getByRole("button", { name: "Port names" }));
    await waitFor(() =>
      expect(calls.some((call) => call.path === "/api/private/v1/history/" && call.query.get("kind") === "port" && call.query.get("scope") === "team")).toBe(true),
    );
  });
});
