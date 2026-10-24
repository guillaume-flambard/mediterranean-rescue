import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import { api, errorCode, fetchClient, type IdentityCandidate, type RowDetail } from "../api/client";
import { useI18n, type I18n } from "../i18n/I18nProvider";
import { setNavigationGuard } from "../router";
import { formatPosition } from "../shared/geo";
import { Button } from "../ui/Button";
import { EvidenceBlock } from "../explore/Evidence";
import { ChoiceGroup } from "../ui/ChoiceGroup";
import { Disclosure } from "../ui/Disclosure";
import { ErrorSummary, InlineMessage, PendingState, StatusLabel, type SummaryError } from "../ui/Feedback";
import { SearchCombobox } from "../ui/SearchCombobox";
import { TextField } from "../ui/TextField";
import { AccessProblem } from "./AccessProblem";

type Decision = "create" | "link" | "later";

const SERVER_CODES = new Set([
  "conflict",
  "not_authenticated",
  "permission_denied",
  "csrf_failed",
  "invalid",
  "not_found",
  "method_not_allowed",
  "network",
]);

/** Catalog key for a server error code; unknown codes get the generic message. */
export function serverMessageKey(code: string): Parameters<I18n["t"]>[0] {
  return (SERVER_CODES.has(code) ? `review.server.${code}` : "review.server.error") as Parameters<I18n["t"]>[0];
}
type Summary = IdentityCandidate["summary"];

/** The Google Sheets tab in words; its technical name only when no translation exists. */
function sheetName(i18n: I18n, sheet: string) {
  const key = `explore.sheet.${sheet}` as Parameters<I18n["t"]>[0];
  const label = i18n.t(key);
  return label === key ? sheet : label;
}

/** A row named by what happened and when ("6 Feb 2024 · Rescue operation"), never by its sheet line. */
function rowTitle(i18n: I18n, interpreted: unknown) {
  const facts = (interpreted ?? {}) as { occurred_on?: unknown; kind?: unknown };
  return i18n.t("review.rowTitle", {
    date: typeof facts.occurred_on === "string" ? i18n.date(facts.occurred_on) : i18n.t("review.unreadable"),
    kind: kindLabel(i18n, typeof facts.kind === "string" ? facts.kind : null),
  });
}

/** The singular name of one event's kind ("Rescue operation"). */
export function kindLabel(i18n: I18n, kind: string | null | undefined) {
  if (!kind) return i18n.t("review.unknown");
  const key = `kindOne.${kind}` as const;
  const label = i18n.t(key as Parameters<I18n["t"]>[0]);
  return label === key ? kind : label;
}

export function countLabel(i18n: I18n, item: { people: number | null; deaths: number | null }) {
  if (item.people !== null) return i18n.t("events.people", { count: item.people });
  if (item.deaths !== null) return i18n.t("review.deaths", { count: item.deaths });
  return i18n.t("events.peopleUnknown");
}

export function identityLabel(i18n: I18n, candidate: IdentityCandidate) {
  const { summary } = candidate;
  const date = summary.occurred_on ? i18n.date(summary.occurred_on) : i18n.t("review.unknown");
  return `${kindLabel(i18n, summary.kind)} · ${date} · ${countLabel(i18n, summary)} · ${candidate.id.slice(0, 8)}`;
}

function Interpreted({ row }: { row: RowDetail }) {
  const i18n = useI18n();
  const { t } = i18n;
  const candidate = (row.interpreted ?? {}) as Record<string, unknown>;
  const position = candidate.position as
    | { latitude: string; longitude: string; latitude_format: string; longitude_format: string }
    | null
    | undefined;
  const count = (name: string) => {
    if (!(name in candidate)) return null;
    const value = candidate[name];
    // Unknown, zero and an error are three different answers.
    if (value === null) return row.error_codes.length ? t("review.unreadable") : t("review.unknown");
    return i18n.number(Number(value));
  };
  const inferred = Boolean(position && `${position.latitude_format}${position.longitude_format}`.includes("inferred"));
  const counts = ["nb_survivor", "female", "under_18", "death_nb_people"].filter((name) => name in candidate);
  return (
    <dl className="review-facts">
      <div>
        <dt>{t("review.field.date")}</dt>
        <dd>{typeof candidate.occurred_on === "string" ? i18n.date(candidate.occurred_on) : t("review.unreadable")}</dd>
      </div>
      <div>
        <dt>{t("review.field.kind")}</dt>
        <dd>{typeof candidate.kind === "string" ? kindLabel(i18n, candidate.kind) : t("review.unreadable")}</dd>
      </div>
      {counts.map((name) => (
        <div key={name}>
          <dt>{t(`review.field.${name}` as Parameters<I18n["t"]>[0])}</dt>
          <dd>{count(name)}</dd>
        </div>
      ))}
      <div>
        <dt>{t("review.field.position")}</dt>
        <dd>
          {position
            ? formatPosition(i18n, Number(position.latitude), Number(position.longitude))
            : t("review.unknown")}
          {inferred && <span className="review-note"> {t("review.inferredHemisphere")}</span>}
        </dd>
      </div>
    </dl>
  );
}

function Received({ row }: { row: RowDetail }) {
  const { t } = useI18n();
  return (
    <div className="ui-table review-received">
      <table>
        <caption className="sr-only">{t("review.received")}</caption>
        <thead>
          <tr>
            <th scope="col">{t("review.column")}</th>
            <th scope="col">{t("review.value")}</th>
          </tr>
        </thead>
        <tbody>
          {row.received.cells.map((cell, index) => (
            <tr key={index}>
              <th scope="row">{row.received.headers[index] || t("review.unnamedColumn", { index: index + 1 })}</th>
              {/* Raw text exactly as received; React escapes it, nothing is interpreted as HTML. */}
              <td className="review-raw">{cell}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function RecordedDecision({ row }: { row: RowDetail }) {
  const i18n = useI18n();
  const decision = row.decision;
  if (!decision) return null;
  return (
    <section aria-labelledby="decision-title">
      <h3 id="decision-title">{i18n.t("review.decision.recorded")}</h3>
      <p>
        <StatusLabel status="linked" /> {i18n.t("review.private")}
      </p>
      <dl className="review-facts">
        <div>
          <dt>{i18n.t("review.decision.identity")}</dt>
          <dd className="review-raw">{decision.external_id}</dd>
        </div>
        <div>
          <dt>{i18n.t("review.decision.match")}</dt>
          <dd>{i18n.t(`review.match.${decision.match}` as Parameters<I18n["t"]>[0])}</dd>
        </div>
        <div>
          <dt>{i18n.t("review.decision.by")}</dt>
          <dd>{decision.approved_by}</dd>
        </div>
        <div>
          <dt>{i18n.t("review.decision.reason")}</dt>
          <dd>{decision.reason}</dd>
        </div>
      </dl>
    </section>
  );
}

export interface RowReviewProps {
  rowId: string;
  snapshotId: string;
  /** Called after the server confirmed the decision; `next` asks to open the following row. */
  onDecided: (next: boolean) => void;
  onClose: () => void;
}

/** A diagnostic code in words; the code itself when the catalog has no sentence for it. */
export function codeText(i18n: I18n, code: string) {
  const key = `diag.code.${code}` as Parameters<I18n["t"]>[0];
  const text = i18n.t(key);
  return text === key ? code : text;
}

export function RowReview({ rowId, snapshotId, onDecided, onClose }: RowReviewProps) {
  const i18n = useI18n();
  const { t } = i18n;
  const queryClient = useQueryClient();
  const rowQuery = api.useQuery("get", "/api/private/v1/review/rows/{id}/", { params: { path: { id: rowId } } });
  const decide = api.useMutation("post", "/api/private/v1/review/rows/{id}/decision/");
  const [decision, setDecision] = useState<Decision | null>(null);
  const [candidate, setCandidate] = useState<string | null>(null);
  const [searched, setSearched] = useState<IdentityCandidate | null>(null);
  const [reason, setReason] = useState("");
  const [submission, setSubmission] = useState(0);
  const [outcome, setOutcome] = useState<"saved" | "later" | null>(null);
  const [serverError, setServerError] = useState<string | null>(null);
  const heading = useRef<HTMLHeadingElement>(null);
  // Writes are not aborted (their outcome would be unknown); a late result for a row the user
  // has left is ignored instead.
  const alive = useRef(true);
  useEffect(() => {
    // Set again on every mount: React's development double mount runs the cleanup once, and a
    // flag left false would silently drop every answer (acceptance of 24 October 2026, D1).
    alive.current = true;
    return () => {
      alive.current = false;
    };
  }, []);

  // Leaving with a typed reason that was not submitted loses it: ask first, in the app and in
  // the browser.
  const dirty = reason.trim() !== "" && !decide.isSuccess;
  const unsavedQuestion = t("review.unsaved");
  useEffect(() => {
    if (!dirty) return;
    const warn = (event: BeforeUnloadEvent) => event.preventDefault();
    window.addEventListener("beforeunload", warn);
    setNavigationGuard(() => window.confirm(unsavedQuestion));
    return () => {
      window.removeEventListener("beforeunload", warn);
      setNavigationGuard(null);
    };
  }, [dirty, unsavedQuestion]);

  // Opening a row (or recording its decision) moves focus to its title.
  const loaded = rowQuery.isSuccess;
  useEffect(() => {
    if (loaded) heading.current?.focus();
  }, [loaded, outcome]);

  if (rowQuery.isPending) return <PendingState label={t("review.loadingRow")} />;
  if (rowQuery.error) {
    const code = errorCode(rowQuery.error);
    if (code === "not_authenticated" || code === "permission_denied") return <AccessProblem code={code} />;
    return (
      <InlineMessage tone="error">
        {t(code === "not_found" ? "review.rowMissing" : "review.loadError")}{" "}
        <Button size="sm" onClick={() => void rowQuery.refetch()}>
          {t("ui.retry")}
        </Button>
      </InlineMessage>
    );
  }
  const row = rowQuery.data;
  const chosenIdentity = decision === "link" ? (searched?.id ?? candidate) : null;
  const errors: SummaryError[] = [];
  if (decision === null) errors.push({ fieldId: "review-decision", message: t("review.error.decision") });
  if (decision === "link" && !chosenIdentity)
    errors.push({ fieldId: "review-identity", message: t("review.error.identity") });
  if (decision !== "later" && !reason.trim()) errors.push({ fieldId: "review-reason", message: t("review.error.reason") });

  const submit = async (next: boolean) => {
    setSubmission((count) => count + 1);
    setServerError(null);
    if (errors.length) return;
    if (decision === "later") {
      // Nothing is created or counted as a validation.
      setOutcome("later");
      onClose();
      return;
    }
    try {
      await decide.mutateAsync({
        params: { path: { id: rowId } },
        body:
          decision === "create"
            ? { action: "create_identity", reason }
            : { action: "link", identity: chosenIdentity ?? "", reason },
      });
      // Only a saved decision lifts the guard: after a failure the typed reason stays protected.
      setNavigationGuard(null);
      await queryClient.invalidateQueries({ queryKey: ["get", "/api/private/v1/review/rows/"] });
      if (!alive.current) return;
      setOutcome("saved");
      setReason("");
      await queryClient.invalidateQueries({ queryKey: ["get", "/api/private/v1/review/rows/{id}/"] });
      if (alive.current) onDecided(next);
    } catch (error) {
      if (!alive.current) return;
      const code = errorCode(error);
      setServerError(code);
      // An expired session shows the sign-in screen; a conflict or an unknown outcome is read again.
      if (code === "not_authenticated") void queryClient.invalidateQueries({ queryKey: ["get", "/api/private/v1/me/"] });
      if (code === "conflict" || code === "network") void rowQuery.refetch();
    }
  };

  // A row rebuilt from the public logbook is verified against its sentence (ADR 0014).
  const fromLogbook = row.evidence !== null;
  const verb =
    decision === "link" ? t("review.action.link") : t(fromLogbook ? "review.action.verifyLogbook" : "review.action.create");
  const status = row.status === "to_review" ? "needsReview" : row.status === "blocked" ? "blocked" : "linked";

  return (
    <article className="review-row" aria-labelledby="review-row-title">
      <div className="review-row__header">
        <h2 id="review-row-title" ref={heading} tabIndex={-1}>
          {rowTitle(i18n, row.interpreted)}
        </h2>
        <StatusLabel status={status} />
        <Button size="sm" variant="quiet" onClick={onClose}>
          {t("ui.close")}
        </Button>
      </div>
      {row.evidence ? (
        <>
          <p className="review-note">{t("review.provenanceLogbook")}</p>
          <EvidenceBlock evidence={row.evidence} />
          <section aria-labelledby="compare-title" className="review-compare">
            <h3 id="compare-title">{t("review.compare.title")}</h3>
            <ul>
              <li>{t("review.compare.date")}</li>
              <li>{t("review.compare.people")}</li>
              <li>{t("review.compare.place")}</li>
            </ul>
            <p className="review-note">{t("review.compare.wrong")}</p>
          </section>
        </>
      ) : (
        <p className="review-note">{t("review.provenance", { sheet: sheetName(i18n, row.snapshot.sheet), line: row.line })}</p>
      )}

      {outcome === "saved" && row.status === "linked" && (
        <InlineMessage tone="success">{t("review.saved")}</InlineMessage>
      )}
      {/* Outside the form: after a conflict the row may be linked and the form gone. */}
      {serverError && <InlineMessage tone="error">{t(serverMessageKey(serverError))}</InlineMessage>}

      {fromLogbook && (row.interpreted as { kind?: string } | null)?.kind === "medevac" ? (
        // A medical evacuation is never exported to the sheet: no columns to show.
        <p className="review-note">{t("review.notForSheet")}</p>
      ) : fromLogbook ? (
        // The sheet's columns matter to whoever pastes the row; the sentence is what a volunteer reads.
        <Disclosure title={t("review.sheetColumns")}>
          <Received row={row} />
        </Disclosure>
      ) : (
        <section aria-labelledby="received-title">
          <h3 id="received-title">{t("review.received")}</h3>
          <Received row={row} />
        </section>
      )}
      <section aria-labelledby="interpreted-title">
        <h3 id="interpreted-title">{t("review.interpreted")}</h3>
        {row.proposal.kind === "repeat" && (
          <InlineMessage tone="warning">{t("review.repeat", { line: row.proposal.repeats_line ?? "?" })}</InlineMessage>
        )}
        {row.error_codes.length > 0 && (
          <InlineMessage tone="error">
            {t("review.blocked")} {row.error_codes.map((code) => codeText(i18n, code)).join(" ")}
          </InlineMessage>
        )}
        <Interpreted row={row} />
      </section>

      {row.status === "linked" && <RecordedDecision row={row} />}

      {row.status === "to_review" && (
        <section aria-labelledby="match-title">
          <h3 id="match-title">{t("review.suggested")}</h3>
          <p>{t(`review.proposal.${row.proposal.kind}` as Parameters<I18n["t"]>[0])}</p>
          {/* Decisions are irreversible: only the buttons submit. Enter in a field (the identity
              search above all) must never record a decision. */}
          <form className="review-form" noValidate onSubmit={(event) => event.preventDefault()}>
            {submission > 0 && errors.length > 0 && <ErrorSummary errors={errors} submission={submission} />}
            <div id="review-decision">
              <ChoiceGroup<Decision>
                legend={t("review.decisionLegend")}
                value={decision}
                onValueChange={setDecision}
                choices={[
                  { value: "create", label: t("review.choice.create") },
                  { value: "link", label: t("review.choice.link"), description: t("review.choice.linkHelp") },
                  { value: "later", label: t("review.choice.later"), description: t("review.choice.laterHelp") },
                ]}
              />
            </div>
            {decision === "link" && (
              <div id="review-identity" className="review-identity">
                {row.proposal.candidates.length > 0 && (
                  <ChoiceGroup<string>
                    legend={t("review.candidates")}
                    value={searched ? null : candidate}
                    onValueChange={(value) => {
                      setCandidate(value);
                      setSearched(null);
                    }}
                    choices={row.proposal.candidates.map((item) => ({ value: item.id, label: identityLabel(i18n, item) }))}
                  />
                )}
                <SearchCombobox<IdentityCandidate>
                  label={t("review.searchIdentity")}
                  placeholder={t("review.searchPlaceholder")}
                  value={searched}
                  onValueChange={(value) => {
                    setSearched(value);
                    if (value) setCandidate(null);
                  }}
                  itemId={(item) => item.id}
                  itemLabel={(item) => identityLabel(i18n, item)}
                  search={async (q, signal) => {
                    const { data, error } = await fetchClient.GET("/api/private/v1/review/identities/", {
                      params: { query: { snapshot: snapshotId, q } },
                      signal,
                    });
                    if (error) throw new Error(errorCode(error));
                    return data.items;
                  }}
                />
              </div>
            )}
            {decision !== "later" && (
              <TextField
                id="review-reason"
                label={t("review.reason")}
                description={t("review.reasonHelp")}
                value={reason}
                onChange={(event) => setReason(event.target.value)}
                error={submission > 0 && !reason.trim() ? t("review.error.reason") : null}
              />
            )}
            <p className="review-note">{t("review.effect")}</p>
            <div className="review-actions">
              <Button variant="primary" loading={decide.isPending} onClick={() => void submit(false)}>
                {decision === "later" ? t("review.action.later") : verb}
              </Button>
              {decision !== "later" && (
                <Button loading={decide.isPending} onClick={() => void submit(true)}>
                  {t("review.action.andNext", { action: verb })}
                </Button>
              )}
            </div>
          </form>
        </section>
      )}
    </article>
  );
}

export type { Summary };
