// @vitest-environment jsdom
import { fireEvent, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { renderWithI18n } from "../test/render";
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
    expect(screen.getByText(/Feb 2024 to Feb 2024 · 5 events/)).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Whole period" }));
    expect(onPeriodChange).toHaveBeenCalledWith("", "");
  });
});
