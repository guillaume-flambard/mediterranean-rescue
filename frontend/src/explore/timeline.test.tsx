// @vitest-environment jsdom
import { fireEvent, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { renderWithI18n } from "../test/render";
import { monthTotals, type LogbookItem } from "./Logbook";
import { Timeline } from "./Timeline";

const MONTHS = [
  { month: "2023-11", count: 2 },
  { month: "2024-01", count: 3 },
  { month: "2024-02", count: 5 },
];

describe("timeline", () => {
  it("fills empty months and counts the whole period", () => {
    renderWithI18n(<Timeline months={MONTHS} start="" end="" onPeriodChange={() => {}} />);
    expect(screen.getByText("Whole period · 10 events")).toBeTruthy();
    // Nov, Dec (empty), Jan, Feb: the handles span four months.
    expect(screen.getByRole("slider", { name: "End of the period" }).getAttribute("max")).toBe("3");
  });

  it("moving a handle chooses a period of whole months, after a short pause", () => {
    vi.useFakeTimers();
    const onPeriodChange = vi.fn();
    renderWithI18n(<Timeline months={MONTHS} start="" end="" onPeriodChange={onPeriodChange} />);
    fireEvent.change(screen.getByRole("slider", { name: "Start of the period" }), { target: { value: "2" } });
    expect(screen.getByText(/Jan 2024 to Feb 2024 · 8 events/)).toBeTruthy();
    vi.advanceTimersByTime(350);
    expect(onPeriodChange).toHaveBeenCalledWith("2024-01-01", "2024-02-29");
    vi.useRealTimers();
  });

  it("shows the period chosen elsewhere and can return to the whole period", () => {
    const onPeriodChange = vi.fn();
    renderWithI18n(<Timeline months={MONTHS} start="2024-02-01" end="2024-02-29" onPeriodChange={onPeriodChange} />);
    expect(screen.getByText("Feb 2024 · 5 events")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Whole period" }));
    expect(onPeriodChange).toHaveBeenCalledWith("", "");
  });

  it("calls a period that does not fall on whole months a custom one", () => {
    renderWithI18n(<Timeline months={MONTHS} start="2024-01-10" end="2024-02-29" onPeriodChange={() => {}} />);
    expect(screen.getByText("Period chosen by dates")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Whole period" })).toBeTruthy();
  });

  it("says how many events have no date instead of hiding them", () => {
    renderWithI18n(<Timeline months={MONTHS} undated={2} start="" end="" onPeriodChange={() => {}} />);
    expect(screen.getByText("2 events without a date are not on the timeline.")).toBeTruthy();
  });

  it("keeps the start handle reachable when both handles sit on the last month", () => {
    const { container } = renderWithI18n(<Timeline months={MONTHS} start="2024-02-01" end="2024-02-29" onPeriodChange={() => {}} />);
    expect(container.querySelector(".timeline__handles--start-on-top")).toBeTruthy();
  });
});

describe("month totals", () => {
  const entry = (kind: string, people: number | null): LogbookItem => ({
    id: `${kind}-${people}`,
    date: "2024-02-03",
    kind,
    people,
    port: null,
    status: null,
    origin: "Source: fictitious",
  });
  const i18n = { t: (key: string, values?: Record<string, unknown>) => `${key}${values ? JSON.stringify(values) : ""}` } as never;

  it("adds up people rescued only, never transfers on top of them", () => {
    const totals = monthTotals(i18n, [entry("rescue", 40), entry("transfer", 40), entry("rescue", 2)], true, false);
    expect(totals).toBe('explore.logbook.events{"count":3} · explore.logbook.rescued{"count":42}');
  });

  it("says where the number is missing, and gives no sum for a month still loading", () => {
    expect(monthTotals(i18n, [entry("rescue", 5), entry("rescue", null)], true, false)).toContain('rescuedKnown{"count":5}');
    expect(monthTotals(i18n, [entry("transfer", 9)], true, false)).toBe('explore.logbook.events{"count":1}');
    expect(monthTotals(i18n, [entry("rescue", 5)], false, false)).toBe("explore.logbook.partial");
  });

  it("marks a month cut by the chosen period", () => {
    expect(monthTotals(i18n, [entry("rescue", 5)], true, true)).toMatch(/^explore.logbook.inPeriod/);
  });
});
