// @vitest-environment jsdom
import { act, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { describe, expect, it, vi } from "vitest";
import { renderWithI18n } from "../test/render";
import { DataTable } from "./DataTable";
import { FilterBar } from "./FilterBar";
import { SearchCombobox } from "./SearchCombobox";

type Row = { id: string; line: number; eligible: boolean };
const ROWS: Row[] = [
  { id: "a", line: 2, eligible: true },
  { id: "b", line: 3, eligible: false },
  { id: "c", line: 4, eligible: true },
];

function Table() {
  const [selected, setSelected] = useState<Set<string>>(new Set());
  return (
    <DataTable<Row>
      caption="Rows"
      rows={ROWS}
      rowId={(row) => row.id}
      columns={[{ key: "line", header: "Line", render: (row) => <button>{`Line ${row.line}`}</button> }]}
      selection={{ isEligible: (row) => row.eligible, selected, onChange: setSelected, rowLabel: (row) => `Select line ${row.line}` }}
    />
  );
}

describe("DataTable", () => {
  it("has a caption and headers, and selects only the eligible rows of the page", async () => {
    renderWithI18n(<Table />);
    expect(screen.getByRole("table", { name: "Rows" })).toBeTruthy();
    expect(screen.getByRole("columnheader", { name: "Line" })).toBeTruthy();
    expect(screen.queryByRole("checkbox", { name: "Select line 3" })).toBeNull();
    await userEvent.click(screen.getByRole("checkbox", { name: "Select the 2 eligible rows of this page" }));
    expect(screen.getByRole("status").textContent).toBe("2 rows selected on this page");
    await userEvent.click(screen.getByRole("checkbox", { name: "Select line 2" }));
    expect(screen.getByRole("status").textContent).toBe("1 row selected on this page");
    expect(screen.getByRole("checkbox", { name: "Select the 2 eligible rows of this page" }).getAttribute("aria-checked")).toBe("mixed");
  });
});

describe("FilterBar", () => {
  it("offers exclusive facets named with their counts", async () => {
    const onValueChange = vi.fn();
    renderWithI18n(
      <FilterBar
        legend="Show"
        value="to_review"
        onValueChange={onValueChange}
        facets={[
          { value: "to_review", label: "To review", count: 1234 },
          { value: "blocked", label: "Blocked", count: 3 },
        ]}
      />,
    );
    expect(screen.getByRole("radiogroup", { name: "Show" })).toBeTruthy();
    expect(screen.getByRole("radio", { name: "To review 1,234" }).getAttribute("aria-checked")).toBe("true");
    await userEvent.click(screen.getByRole("radio", { name: "Blocked 3" }));
    expect(onValueChange).toHaveBeenCalledWith("blocked");
  });
});

type Item = { id: string; name: string };

describe("SearchCombobox", () => {
  it("waits for a pause, aborts the superseded search and never picks a result by itself", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const signals: AbortSignal[] = [];
    const search = vi.fn((query: string, signal: AbortSignal) => {
      signals.push(signal);
      return Promise.resolve(query === "2024" ? [{ id: "1", name: "Rescue 2024" }] : []);
    });
    const onValueChange = vi.fn();
    renderWithI18n(
      <SearchCombobox<Item>
        label="Identity"
        search={search}
        itemId={(item) => item.id}
        itemLabel={(item) => item.name}
        value={null}
        onValueChange={onValueChange}
      />,
    );
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    await user.type(screen.getByRole("combobox", { name: "Identity" }), "2024");
    expect(search).not.toHaveBeenCalled();
    await act(async () => vi.advanceTimersByTime(300));
    expect(search).toHaveBeenCalledTimes(1);
    expect(search).toHaveBeenLastCalledWith("2024", expect.any(AbortSignal));
    expect(await screen.findByRole("option", { name: "Rescue 2024" })).toBeTruthy();
    expect(onValueChange).not.toHaveBeenCalled();
    await user.type(screen.getByRole("combobox", { name: "Identity" }), "x");
    await act(async () => vi.advanceTimersByTime(300));
    await waitFor(() => expect(screen.getByText("No match for “2024x”.")).toBeTruthy());
    vi.useRealTimers();
  });
});
