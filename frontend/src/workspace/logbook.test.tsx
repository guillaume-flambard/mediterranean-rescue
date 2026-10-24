// @vitest-environment jsdom
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { screen } from "@testing-library/react";
import type { ReactElement } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { PreviewBody } from "../explore/EventBody";
import { fakeServer } from "../test/fakeServer";
import { renderWithI18n } from "../test/render";
import { LogbookCard } from "./TeamData";

const ROW = "00000000-0000-0000-0000-0000000000c1";
const LOGBOOK_ROW = {
  id: ROW,
  snapshot: "00000000-0000-0000-0000-0000000000c0",
  sheet: "Data_operations",
  line: 2,
  exported_at: "2026-10-24T12:00:00Z",
  source: { key: "sos-logbook", name: "SOS MEDITERRANEE public logbook" },
  synthetic: false,
  status: "to_review",
  error_codes: [],
  occurred_on: "2025-03-13",
  kind: "rescue",
  people: 40,
  women: null,
  minors: null,
  deaths: null,
  port_label: "Port fictif",
  boat_type: "White rubber boat",
  position: { longitude: 12.25, latitude: 33.5, inferred_hemisphere: true },
  image_count: 0,
  evidence: {
    url: "https://www.sosmediterranee.org/operation/fictitious/",
    rotation: "OPERATION 12-19 March 2025 (fictitious)",
    logged_at: "2025-03-13 07:00",
    quote: "Ocean Viking completes the recovery of 40 shipwrecked persons.",
    to_check: ["position read as compact degrees and minutes"],
  },
};

function render(ui: ReactElement) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return renderWithI18n(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

afterEach(() => vi.unstubAllGlobals());

describe("operations rebuilt from the public logbook", () => {
  it("the card states the lag, the three steps and the download of verified rows", async () => {
    fakeServer({
      "GET /api/private/v1/logbook/": () => ({
        body: {
          sheet_last_date: "2024-02-06",
          last_read_at: "2026-10-24T20:00:00Z",
          last_read_status: "new_data",
          first_date: "2024-03-13",
          last_date: "2026-08-17",
          rows: 61,
          people: 3468,
          verified: 2,
          to_verify: 59,
          to_fix: 0,
          to_check: 24,
        },
      }),
    });
    render(<LogbookCard />);
    expect(
      await screen.findByRole("heading", {
        name: /The sheet behind SOS’s public map stops on/,
      }),
    ).toBeTruthy();
    expect(screen.getByText(/61 operations \(3,468 people\) were rebuilt/)).toBeTruthy();
    expect(screen.getByText(/59 operations wait/)).toBeTruthy();
    const download = screen.getByRole("link", {
      name: "Download 2 verified rows",
    });
    expect(download.getAttribute("href")).toBe("/api/private/v1/logbook/export/");
    expect(screen.getByRole("link", { name: "See them on the map" }).getAttribute("href")).toBe("/workspace/data?source=sos-logbook");
  });

  it("a rebuilt record quotes its logbook sentence and says what to check", async () => {
    fakeServer({
      "GET /api/private/v1/preview/events/:id/": () => ({ body: LOGBOOK_ROW }),
    });
    render(<PreviewBody id={ROW} />);
    expect(await screen.findByText("Ocean Viking completes the recovery of 40 shipwrecked persons.")).toBeTruthy();
    expect(screen.getByText("position read as compact degrees and minutes")).toBeTruthy();
    expect(screen.getByRole("link", { name: "Open the logbook page ↗" }).getAttribute("href")).toBe(LOGBOOK_ROW.evidence.url);
    expect(screen.queryByText(/row 2 of/)).toBeNull();
  });
});
