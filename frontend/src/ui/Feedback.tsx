import { useEffect, useRef, type ReactNode } from "react";
import { useI18n } from "../i18n/I18nProvider";
import type { MessageKey } from "../i18n/en";

export type Status = "blocked" | "needsReview" | "linked" | "draft" | "published" | "withdrawn" | "unknown" | "training";
const STATUS_TONE: Record<Status, "error" | "warning" | "success" | "info" | "neutral"> = {
  blocked: "error",
  needsReview: "warning",
  linked: "success",
  draft: "neutral",
  published: "success",
  withdrawn: "neutral",
  unknown: "neutral",
  training: "info",
};

// A word, never a color alone.
export function StatusLabel({ status }: { status: Status }) {
  const { t } = useI18n();
  const key: MessageKey = `ui.status.${status}`;
  return <span className={`ui-status ui-status--${STATUS_TONE[status]}`}>{t(key)}</span>;
}

export type Tone = "info" | "success" | "warning" | "error";

export function InlineMessage({ tone, children }: { tone: Tone; children: ReactNode }) {
  // Errors interrupt; other messages are announced politely.
  return (
    <div className={`ui-message ui-message--${tone}`} role={tone === "error" ? "alert" : "status"}>
      {children}
    </div>
  );
}

export interface SummaryError {
  /** id of the field to focus when the link is followed */
  fieldId: string;
  message: string;
}

// Shown at the top of an invalid form after submission. It takes focus once per failed
// submission (`submission` changes), never while the user corrects the fields.
export function ErrorSummary({ errors, submission }: { errors: readonly SummaryError[]; submission: number }) {
  const { t } = useI18n();
  const heading = useRef<HTMLHeadingElement>(null);
  const hasErrors = errors.length > 0;
  useEffect(() => {
    if (submission > 0 && hasErrors) heading.current?.focus();
    // Only a new submission moves focus; error updates while typing must not.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [submission]);
  if (!errors.length) return null;
  return (
    <div className="ui-message ui-message--error ui-error-summary" role="alert">
      <h2 ref={heading} tabIndex={-1} className="ui-error-summary__title">
        {t("ui.errorSummary.title", { count: errors.length })}
      </h2>
      <ul>
        {errors.map((error) => (
          <li key={error.fieldId}>
            <a href={`#${error.fieldId}`}>{error.message}</a>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function EmptyState({ title, children, action }: { title: string; children?: ReactNode; action?: ReactNode }) {
  return (
    <div className="ui-empty">
      <h3 className="ui-empty__title">{title}</h3>
      {children}
      {action}
    </div>
  );
}

// Indeterminate by default: a percentage is shown only when the server gives a real one.
export function PendingState({ label }: { label: string }) {
  return (
    <div className="ui-pending" role="status">
      <span className="ui-pending__bar" aria-hidden />
      {label}
    </div>
  );
}
