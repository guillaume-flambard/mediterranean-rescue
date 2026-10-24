// @vitest-environment jsdom
import { act, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { ChoiceGroup } from "./ChoiceGroup";
import { describe, expect, it, vi } from "vitest";
import { useI18n } from "../i18n/I18nProvider";
import { renderWithI18n } from "../test/render";
import { Button } from "./Button";
import { ConfirmationDialog } from "./ConfirmationDialog";
import { DateRange } from "./DateRange";
import { ErrorSummary, StatusLabel } from "./Feedback";
import { Pagination } from "./Pagination";
import { TextField } from "./TextField";

describe("Button", () => {
  it("announces loading, keeps its label and blocks a second submission", async () => {
    const onClick = vi.fn();
    renderWithI18n(
      <Button loading onClick={onClick}>
        Save
      </Button>,
    );
    const button = screen.getByRole("button", { name: "Save" });
    expect(button).toHaveProperty("ariaBusy", "true");
    await userEvent.click(button);
    expect(onClick).not.toHaveBeenCalled();
  });
});

describe("TextField", () => {
  it("links help and error to the control and marks it invalid", () => {
    renderWithI18n(<TextField label="Reason" description="One sentence." error="A reason is required." />);
    const input = screen.getByRole("textbox", { name: "Reason" });
    expect(input.getAttribute("aria-invalid")).toBe("true");
    const described = (input.getAttribute("aria-describedby") ?? "").split(" ");
    const texts = described.map((id) => document.getElementById(id)?.textContent);
    expect(texts).toEqual(expect.arrayContaining(["One sentence.", "A reason is required."]));
  });

  it("marks optional fields in the current language", () => {
    renderWithI18n(<TextField label="Motif" optional />, "fr");
    expect(screen.getByText("(facultatif)")).toBeTruthy();
  });
});

describe("ConfirmationDialog", () => {
  it("focuses Cancel, stays open while the server works and closes after confirmation", async () => {
    let finish: () => void = () => {};
    const onConfirm = vi.fn(() => new Promise<void>((resolve) => (finish = resolve)));
    renderWithI18n(
      <ConfirmationDialog
        trigger={<button>Withdraw</button>}
        title="Withdraw this event?"
        consequence="It leaves the public site."
        confirmLabel="Withdraw event"
        onConfirm={onConfirm}
        failureMessage={() => "Withdrawal failed. Nothing changed."}
        danger
      />,
    );
    await userEvent.click(screen.getByRole("button", { name: "Withdraw" }));
    const dialog = await screen.findByRole("alertdialog", { name: "Withdraw this event?" });
    await waitFor(() => expect(document.activeElement?.textContent).toBe("Cancel"));
    await userEvent.click(screen.getByRole("button", { name: "Withdraw event" }));
    expect(onConfirm).toHaveBeenCalledOnce();
    await userEvent.keyboard("{Escape}");
    expect(dialog.isConnected).toBe(true);
    await act(async () => finish());
    await waitFor(() => expect(screen.queryByRole("alertdialog")).toBeNull());
  });

  it("keeps the dialog open and explains the failure inside it", async () => {
    const onConfirm = vi.fn(() => Promise.reject(new Error("refused")));
    renderWithI18n(
      <ConfirmationDialog
        trigger={<button>Withdraw</button>}
        title="Withdraw this event?"
        consequence="It leaves the public site."
        confirmLabel="Withdraw event"
        onConfirm={onConfirm}
        failureMessage={() => "Withdrawal failed. Nothing changed."}
      />,
    );
    await userEvent.click(screen.getByRole("button", { name: "Withdraw" }));
    await userEvent.click(await screen.findByRole("button", { name: "Withdraw event" }));
    await waitFor(() => expect(onConfirm).toHaveBeenCalledOnce());
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Withdraw event" }).getAttribute("aria-busy")).toBeNull(),
    );
    const dialog = screen.getByRole("alertdialog");
    const message = await screen.findByText("Withdrawal failed. Nothing changed.");
    expect(dialog.contains(message)).toBe(true);
    expect(message.closest("[role=alert]")).not.toBeNull();
  });
});

describe("ErrorSummary and StatusLabel", () => {
  it("focuses the summary title and counts problems with plural rules", async () => {
    renderWithI18n(<ErrorSummary submission={1} errors={[{ fieldId: "reason", message: "Reason: required." }]} />, "fr");
    const heading = screen.getByRole("heading", { name: "1 problème à corriger" });
    await waitFor(() => expect(document.activeElement).toBe(heading));
    expect(screen.getByRole("link", { name: "Reason: required." }).getAttribute("href")).toBe("#reason");
  });

  it("states a status in words", () => {
    renderWithI18n(<StatusLabel status="needsReview" />);
    expect(screen.getByText("Not verified yet")).toBeTruthy();
  });
});

describe("Pagination", () => {
  it("shows the server range and disables impossible moves", async () => {
    const onOffsetChange = vi.fn();
    renderWithI18n(<Pagination offset={0} limit={25} total={370} hasNext onOffsetChange={onOffsetChange} />);
    expect(screen.getByText("1 to 25 of 370")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Previous" }).getAttribute("aria-disabled")).toBe("true");
    await userEvent.click(screen.getByRole("button", { name: "Next" }));
    expect(onOffsetChange).toHaveBeenCalledWith(25);
  });
});

describe("DateRange", () => {
  it("refuses an inverted period before any request", async () => {
    const onApply = vi.fn();
    renderWithI18n(<DateRange legend="Period" startLabel="From" endLabel="To" start="" end="" onApply={onApply} />);
    await userEvent.type(screen.getByLabelText("From"), "2024-03-10");
    await userEvent.type(screen.getByLabelText("To"), "2024-03-01");
    await userEvent.click(screen.getByRole("button", { name: "Apply dates" }));
    expect(onApply).not.toHaveBeenCalled();
    expect(screen.getByRole("alert").textContent).toBe("The start date must be before the end date.");
    expect(screen.getByLabelText("From").getAttribute("aria-invalid")).toBe("true");
  });
});

describe("I18nProvider", () => {
  it("switches language, updates the document language and remembers the choice", async () => {
    function Switcher() {
      const { t, setLocale } = useI18n();
      const [clicked, setClicked] = useState(false);
      return (
        <button
          onClick={() => {
            setLocale("fr");
            setClicked(true);
          }}
        >
          {clicked ? t("ui.close") : "switch"}
        </button>
      );
    }
    renderWithI18n(<Switcher />);
    await userEvent.click(screen.getByRole("button", { name: "switch" }));
    expect(screen.getByRole("button", { name: "Fermer" })).toBeTruthy();
    expect(document.documentElement.lang).toBe("fr");
    expect(window.localStorage.getItem("locale")).toBe("fr");
  });
});


describe("review regressions", () => {
  it("does not steal focus from a field while errors update as the user types", async () => {
    function Form() {
      const [value, setValue] = useState("");
      return (
        <>
          <ErrorSummary submission={1} errors={value.length < 3 ? [{ fieldId: "f", message: "Too short" }] : []} />
          <input aria-label="Field" value={value} onChange={(event) => setValue(event.target.value)} />
        </>
      );
    }
    renderWithI18n(<Form />);
    const input = screen.getByRole("textbox", { name: "Field" });
    input.focus();
    await userEvent.type(input, "ab");
    expect(document.activeElement).toBe(input);
    expect((input as HTMLInputElement).value).toBe("ab");
  });

  it("names a choice by its label and describes it separately", () => {
    renderWithI18n(
      <ChoiceGroup
        legend="Decision"
        value={null}
        onValueChange={() => {}}
        choices={[{ value: "create", label: "Create", description: "Makes a new identity." }]}
      />,
    );
    const radio = screen.getByRole("radio", { name: "Create" });
    const describedBy = radio.getAttribute("aria-describedby") ?? "";
    expect(document.getElementById(describedBy)?.textContent).toBe("Makes a new identity.");
  });

  it("follows a period cleared by the parent", async () => {
    function Parent() {
      const [range, setRange] = useState({ start: "2024-01-01", end: "2024-02-01" });
      return (
        <>
          <DateRange legend="Period" startLabel="From" endLabel="To" start={range.start} end={range.end} onApply={() => {}} />
          <button onClick={() => setRange({ start: "", end: "" })}>Clear</button>
        </>
      );
    }
    renderWithI18n(<Parent />);
    expect((screen.getByLabelText("From") as HTMLInputElement).value).toBe("2024-01-01");
    await userEvent.click(screen.getByRole("button", { name: "Clear" }));
    expect((screen.getByLabelText("From") as HTMLInputElement).value).toBe("");
  });

  it("keeps keyboard focus on a pagination button disabled during a load", () => {
    renderWithI18n(<Pagination offset={25} limit={25} total={370} hasNext disabled onOffsetChange={() => {}} />);
    const next = screen.getByRole("button", { name: "Next" });
    expect(next.hasAttribute("disabled")).toBe(false);
    expect(next.getAttribute("aria-disabled")).toBe("true");
  });
});
