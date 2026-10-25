import { Fieldset } from "@base-ui/react/fieldset";
import { useId, useState } from "react";
import { useI18n } from "../i18n/I18nProvider";
import { Button } from "./Button";

export interface DateRangeProps {
  legend: string;
  startLabel: string;
  endLabel: string;
  start: string;
  end: string;
  onApply: (start: string, end: string) => void;
}

// Native date inputs; the range is applied explicitly so typing does not reload between dates.
export function DateRange({ legend, startLabel, endLabel, start, end, onApply }: DateRangeProps) {
  const { t } = useI18n();
  const [draftStart, setDraftStart] = useState(start);
  const [draftEnd, setDraftEnd] = useState(end);
  const [submitted, setSubmitted] = useState(false);
  const [applied, setApplied] = useState({ start, end });
  if (applied.start !== start || applied.end !== end) {
    // The parent changed the period (e.g. cleared it): adjust during render, not in an effect.
    setApplied({ start, end });
    setDraftStart(start);
    setDraftEnd(end);
    setSubmitted(false);
  }
  const errorId = useId();
  const invalid = Boolean(draftStart && draftEnd && draftStart > draftEnd);
  const showError = submitted && invalid;
  return (
    <Fieldset.Root className="ui-date-range">
      <Fieldset.Legend className="ui-field__label">{legend}</Fieldset.Legend>
      <div className="ui-date-range__row">
      <label className="ui-field">
        <span className="ui-field__label">{startLabel}</span>
        <input
          type="date"
          className="ui-field__control"
          value={draftStart}
          aria-invalid={showError || undefined}
          aria-describedby={showError ? errorId : undefined}
          onChange={(event) => setDraftStart(event.target.value)}
        />
      </label>
      <label className="ui-field">
        <span className="ui-field__label">{endLabel}</span>
        <input
          type="date"
          className="ui-field__control"
          value={draftEnd}
          aria-invalid={showError || undefined}
          aria-describedby={showError ? errorId : undefined}
          onChange={(event) => setDraftEnd(event.target.value)}
        />
      </label>
      <Button
        onClick={() => {
          setSubmitted(true);
          if (!invalid) onApply(draftStart, draftEnd);
        }}
      >
        {t("ui.dateRange.apply")}
      </Button>
      </div>
      {showError && (
        <p id={errorId} className="ui-field__error" role="alert">
          {t("ui.dateRange.invalid")}
        </p>
      )}
    </Fieldset.Root>
  );
}
