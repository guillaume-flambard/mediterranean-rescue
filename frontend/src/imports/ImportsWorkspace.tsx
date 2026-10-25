import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import {
  api,
  errorCode,
  fetchClient,
  uploadBody,
  type Diagnostic,
  type ImportDetail,
  type ImportSummary,
  type Me,
  type Sheet,
} from "../api/client";
import { useI18n, type I18n } from "../i18n/I18nProvider";
import { serverMessageKey } from "../review/RowReview";
import { Link, matchRoute, navigate, useLocation, withQuery } from "../router";
import { isAbortError, useAbortableRequest } from "../shared/abortable";
import { Button } from "../ui/Button";
import { DataTable } from "../ui/DataTable";
import { EmptyState, InlineMessage, PendingState } from "../ui/Feedback";
import { FileInput } from "../ui/FileInput";
import { Pagination } from "../ui/Pagination";
import { SelectField } from "../ui/SelectField";
import { ME_QUERY, WorkspaceShell } from "../workspace/WorkspaceShell";

export const IMPORTS_PATH = "/workspace/imports";
const NEW_PATH = `${IMPORTS_PATH}/new`;
const DIAGNOSTIC_PATH = `${NEW_PATH}/diagnostic`;
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const PAGE = 25;
const REVIEW_SHEETS: readonly string[] = ["Data_operations", "Other_data"];

type Key = Parameters<I18n["t"]>[0];

export function sheetLabel(i18n: I18n, sheet: string) {
  const key = `imports.sheet.${sheet}` as Key;
  const label = i18n.t(key);
  return label === key ? sheet : label;
}

/** Calendar day of a timestamp where the reader is (an import at 01:00 in Paris is that day). */
export function localDay(timestamp: string) {
  const date = new Date(timestamp);
  const pad = (value: number) => String(value).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

/** Plain explanation of a diagnostic code; unknown codes are shown as they are. */
export function issueText(i18n: I18n, code: string) {
  const key = `diag.code.${code}` as Key;
  const text = i18n.t(key);
  return text === key ? code : text;
}

// Parcours A: imports list, W02 (add an export), W03 (what the file holds, before and after saving).
export function ImportsWorkspace() {
  const { t } = useI18n();
  const { pathname } = useLocation();
  const detail = matchRoute(`${IMPORTS_PATH}/:id`, pathname);
  return (
    <WorkspaceShell section="imports" title={t("imports.title")}>
      {(me) =>
        pathname === NEW_PATH || pathname === DIAGNOSTIC_PATH ? (
          // Same element for both steps, so the chosen file survives the change of address.
          <NewImport me={me} step={pathname === DIAGNOSTIC_PATH ? "diagnostic" : "form"} />
        ) : detail?.id && UUID.test(detail.id) ? (
          <ImportView id={detail.id} me={me} />
        ) : (
          <ImportList me={me} />
        )
      }
    </WorkspaceShell>
  );
}

function ImportList({ me }: { me: Me }) {
  const i18n = useI18n();
  const { t } = i18n;
  const { query } = useLocation();
  const offset = Math.max(0, Number(query.get("offset")) || 0);
  const list = api.useQuery("get", "/api/private/v1/imports/", { params: { query: { limit: PAGE, offset } } });
  return (
    <>
      <div className="workspace-heading">
        <h1>{t("imports.title")}</h1>
        {me.permissions.stage_snapshot && (
          <Link to={NEW_PATH} className="ui-button ui-button--primary ui-button--md">
            {t("imports.add")}
          </Link>
        )}
      </div>
      <p className="workspace-lead">{t("imports.lead")}</p>
      {list.error ? (
        <InlineMessage tone="error">
          {t("workspace.loadError")}{" "}
          <Button size="sm" onClick={() => void list.refetch()}>
            {t("ui.retry")}
          </Button>
        </InlineMessage>
      ) : !list.data ? (
        <PendingState label={t("workspace.loading")} />
      ) : (
        <>
          <DataTable<ImportSummary>
            caption={t("imports.caption")}
            rows={list.data.items}
            rowId={(item) => item.id}
            busy={list.isFetching}
            empty={
              <EmptyState
                title={t("imports.empty.title")}
                action={
                  me.permissions.stage_snapshot ? (
                    <Link to={NEW_PATH}>{t("imports.add")}</Link>
                  ) : undefined
                }
              >
                <p>{t("imports.empty.body")}</p>
              </EmptyState>
            }
            columns={[
              {
                key: "sheet",
                header: t("imports.col.sheet"),
                render: (item) => <Link to={`${IMPORTS_PATH}/${item.id}`}>{sheetLabel(i18n, item.sheet)}</Link>,
              },
              { key: "date", header: t("imports.col.date"), render: (item) => i18n.date(localDay(item.created_at)) },
              { key: "source", header: t("imports.col.source"), render: (item) => item.source.name },
              { key: "rows", header: t("imports.col.rows"), render: (item) => i18n.number(item.row_count) },
              { key: "by", header: t("imports.col.by"), render: (item) => item.staged_by },
            ]}
          />
          <Pagination
            offset={offset}
            limit={PAGE}
            total={list.data.total_count}
            hasNext={list.data.has_next}
            disabled={list.isFetching}
            onOffsetChange={(next) => navigate(withQuery(IMPORTS_PATH, { offset: next }))}
          />
        </>
      )}
    </>
  );
}

function NewImport({ me, step }: { me: Me; step: "form" | "diagnostic" }) {
  const i18n = useI18n();
  const { t } = i18n;
  const queryClient = useQueryClient();
  const options = api.useQuery("get", "/api/private/v1/imports/options/", {}, { enabled: me.permissions.stage_snapshot });
  const [source, setSource] = useState("");
  const [sheet, setSheet] = useState<Sheet | "">("");
  const [file, setFile] = useState<File | null>(null);
  const [submitted, setSubmitted] = useState(false);
  const [checking, setChecking] = useState(false);
  const [saving, setSaving] = useState(false);
  // The diagnostic and the exact choices it was made for: saving sends those, never newer ones.
  const [result, setResult] = useState<{ diagnostic: Diagnostic; source: string; sheet: Sheet; file: File } | null>(null);
  const [failure, setFailure] = useState<string | null>(null);
  const { run, abort } = useAbortableRequest();
  const alive = useRef(true);
  const heading = useRef<HTMLHeadingElement>(null);

  useEffect(() => {
    alive.current = true;
    return () => {
      alive.current = false;
    };
  }, []);
  useEffect(() => {
    heading.current?.focus();
  }, [step]);

  if (!me.permissions.stage_snapshot) {
    return <InlineMessage tone="warning">{t("imports.denied")}</InlineMessage>;
  }
  if (options.error) return <InlineMessage tone="error">{t("workspace.loadError")}</InlineMessage>;
  if (!options.data) return <PendingState label={t("workspace.loading")} />;

  const maxBytes = options.data.max_bytes;
  const fileError = !file
    ? submitted
      ? t("imports.error.file")
      : null
    : file.size > maxBytes
      ? t("imports.error.tooLarge", { size: i18n.number(Math.round(maxBytes / 1024 / 1024)) })
      : null;

  const check = async () => {
    setSubmitted(true);
    setFailure(null);
    if (!source || !sheet || !file || file.size > maxBytes) return;
    setChecking(true);
    try {
      // A diagnostic writes nothing: a superseded or abandoned one is simply aborted.
      const { data, error } = await run((signal) =>
        fetchClient.POST("/api/private/v1/imports/diagnose/", { body: uploadBody({ source, sheet, file }), signal }),
      );
      if (error) throw error;
      setResult({ diagnostic: data, source, sheet, file });
      navigate(DIAGNOSTIC_PATH);
    } catch (error) {
      if (!isAbortError(error)) setFailure(t(failureKey(errorCode(error))));
      if (errorCode(error) === "not_authenticated") void queryClient.invalidateQueries({ queryKey: ME_QUERY });
    } finally {
      setChecking(false);
    }
  };

  const save = async () => {
    if (!result) return;
    setSaving(true);
    setFailure(null);
    try {
      // A write is never aborted; if the screen moved on, its result is ignored.
      const { data, error } = await fetchClient.POST("/api/private/v1/imports/", {
        body: uploadBody({ source: result.source, sheet: result.sheet, file: result.file }),
      });
      if (error) throw error;
      await queryClient.invalidateQueries({ queryKey: ["get", "/api/private/v1/imports/"] });
      await queryClient.invalidateQueries({ queryKey: ["get", "/api/private/v1/snapshots/"] });
      if (!alive.current) return;
      navigate(withQuery(`${IMPORTS_PATH}/${data.snapshot.id}`, { saved: data.created ? "new" : "existing" }));
    } catch (error) {
      if (!alive.current) return;
      setFailure(t(failureKey(errorCode(error))));
      if (errorCode(error) === "not_authenticated") void queryClient.invalidateQueries({ queryKey: ME_QUERY });
    } finally {
      if (alive.current) setSaving(false);
    }
  };

  if (step === "diagnostic") {
    if (!result) {
      return (
        <>
          <h1 ref={heading} tabIndex={-1}>
            {t("imports.check.title")}
          </h1>
          <EmptyState title={t("imports.check.lost")} action={<Link to={NEW_PATH}>{t("imports.check.chooseAgain")}</Link>}>
            <p>{t("imports.check.lostBody")}</p>
          </EmptyState>
        </>
      );
    }
    return (
      <>
        <h1 ref={heading} tabIndex={-1}>
          {t("imports.check.title")}
        </h1>
        <p className="workspace-lead">
          {t("imports.check.lead", {
            sheet: sheetLabel(i18n, result.diagnostic.sheet),
            file: result.file.name,
            source: result.diagnostic.source.name,
          })}
        </p>
        {failure && <InlineMessage tone="error">{failure}</InlineMessage>}
        <DiagnosticSummary result={result.diagnostic} />
        <section className="workspace-panel" aria-labelledby="next-step">
          <h2 id="next-step">{t("imports.next.title")}</h2>
          {result.diagnostic.existing_snapshot ? (
            <InlineMessage tone="info">
              {t("imports.next.existing")} <Link to={`${IMPORTS_PATH}/${result.diagnostic.existing_snapshot}`}>{t("imports.next.open")}</Link>
            </InlineMessage>
          ) : result.diagnostic.stageable ? (
            <>
              <p>{t("imports.next.saveBody")}</p>
              {result.diagnostic.counts.rows_with_errors > 0 && (
                <p className="review-note">{t("imports.next.blockedRows", { count: result.diagnostic.counts.rows_with_errors })}</p>
              )}
              <div className="workspace-actions">
                <Button variant="primary" loading={saving} onClick={() => void save()}>
                  {t("imports.next.save")}
                </Button>
                <Link to={NEW_PATH}>{t("imports.next.otherFile")}</Link>
              </div>
            </>
          ) : (
            <>
              <InlineMessage tone="error">
                {t(`imports.blocking.${result.diagnostic.blocking_reason ?? "file_errors"}` as Key)}
              </InlineMessage>
              <p>{t("imports.next.fixSource")}</p>
              <Link to={NEW_PATH}>{t("imports.next.otherFile")}</Link>
            </>
          )}
        </section>
      </>
    );
  }

  return (
    <>
      <h1 ref={heading} tabIndex={-1}>
        {t("imports.new.title")}
      </h1>
      <p className="workspace-lead">{t("imports.new.lead")}</p>
      <form
        className="review-form workspace-panel"
        noValidate
        onSubmit={(event) => {
          event.preventDefault();
          void check();
        }}
      >
        {failure && <InlineMessage tone="error">{failure}</InlineMessage>}
        <SelectField<string>
          label={t("imports.new.source")}
          value={source}
          emptyLabel={t("imports.new.choose")}
          options={options.data.sources.map((item) => ({
            value: item.id,
            label: item.synthetic ? t("imports.new.synthetic", { name: item.name }) : item.name,
          }))}
          onValueChange={(value) => {
            abort();
            setResult(null);
            setSource(value);
          }}
        />
        {submitted && !source && <p className="ui-field__error">{t("imports.error.source")}</p>}
        <SelectField<Sheet>
          label={t("imports.new.sheet")}
          value={sheet}
          emptyLabel={t("imports.new.choose")}
          options={options.data.sheets.map((value) => ({ value, label: sheetLabel(i18n, value) }))}
          onValueChange={(value) => {
            abort();
            setResult(null);
            setSheet(value);
          }}
        />
        {submitted && !sheet && <p className="ui-field__error">{t("imports.error.sheet")}</p>}
        <FileInput
          label={t("imports.new.file")}
          description={t("imports.new.fileHelp", { size: i18n.number(Math.round(maxBytes / 1024 / 1024)) })}
          accept=".csv,text/csv"
          file={file}
          onFileChange={(next) => {
            abort();
            setFile(next);
            setResult(null);
          }}
          error={fileError}
        />
        <p className="review-note">{t("imports.new.private")}</p>
        <div className="workspace-actions">
          <Button type="submit" variant="primary" loading={checking}>
            {t("imports.new.check")}
          </Button>
          <Link to={IMPORTS_PATH}>{t("ui.cancel")}</Link>
        </div>
      </form>
    </>
  );
}

function failureKey(code: string): Key {
  if (code === "throttled") return "imports.error.throttled";
  if (code === "invalid") return "imports.error.invalid";
  if (code === "permission_denied") return "imports.denied";
  if (code === "http_413") return "imports.error.tooLargeServer";
  return serverMessageKey(code);
}

function DiagnosticSummary({ result }: { result: Diagnostic }) {
  const i18n = useI18n();
  const { t } = i18n;
  const counts = result.counts;
  const readKey = `imports.read.${result.source_read}` as Key;
  const read = t(readKey);
  return (
    <>
      <section className="workspace-panel" aria-labelledby="reading">
        <h2 id="reading">{t("imports.check.reading")}</h2>
        <p>{read === readKey ? result.source_read : read}</p>
        <dl className="workspace-facts">
          <div>
            <dt>{t("imports.count.rows")}</dt>
            <dd>{i18n.number(counts.rows_diagnosed)}</dd>
          </div>
          <div>
            <dt>{t("imports.count.rowsWithErrors")}</dt>
            <dd>{i18n.number(counts.rows_with_errors)}</dd>
          </div>
          <div>
            <dt>{t("imports.count.rowsWithWarnings")}</dt>
            <dd>{i18n.number(counts.rows_with_warnings)}</dd>
          </div>
          <div>
            <dt>{t("imports.count.blank")}</dt>
            <dd>{i18n.number(counts.blank_rows_skipped)}</dd>
          </div>
        </dl>
      </section>
      {result.issues_by_code.length > 0 && (
        <section className="workspace-panel" aria-labelledby="problems">
          <h2 id="problems">{t("imports.check.problems")}</h2>
          <p className="review-note">{t("imports.check.problemsHelp")}</p>
          <ul className="workspace-issues">
            {result.issues_by_code.map((item) => (
              <li key={`${item.code}-${item.severity}`}>
                <span className={`workspace-severity workspace-severity--${item.severity}`}>
                  {t(item.severity === "error" ? "imports.severity.error" : "imports.severity.warning")}
                </span>{" "}
                {issueText(i18n, item.code)} <span className="review-note">({t("imports.check.times", { count: item.count })})</span>
              </li>
            ))}
          </ul>
          <details className="workspace-details">
            <summary>{t("imports.check.where")}</summary>
            <ul className="workspace-locations">
              {result.issues.map((issue, index) => (
                <li key={index}>
                  {issue.line ? t("imports.check.line", { line: issue.line }) : t("imports.check.wholeFile")}
                  {issue.field ? ` · ${issue.field}` : ""} : {issueText(i18n, issue.code)}
                </li>
              ))}
            </ul>
            {result.issues_truncated && <p className="review-note">{t("imports.check.truncated", { count: result.issues.length })}</p>}
          </details>
        </section>
      )}
    </>
  );
}

function ImportView({ id, me }: { id: string; me: Me }) {
  const i18n = useI18n();
  const { t } = i18n;
  const { query } = useLocation();
  const detail = api.useQuery("get", "/api/private/v1/imports/{id}/", { params: { path: { id } } });
  const saved = query.get("saved");
  if (detail.error) {
    return (
      <InlineMessage tone="error">
        {errorCode(detail.error) === "not_found" ? t("imports.missing") : t("workspace.loadError")}
      </InlineMessage>
    );
  }
  if (!detail.data) return <PendingState label={t("workspace.loading")} />;
  const data: ImportDetail = detail.data;
  return (
    <>
      <p>
        <Link to={IMPORTS_PATH}>{t("imports.back")}</Link>
      </p>
      <h1>{t("imports.detail.title", { sheet: sheetLabel(i18n, data.sheet), date: i18n.date(localDay(data.created_at)) })}</h1>
      {saved === "new" && <InlineMessage tone="success">{t("imports.detail.saved")}</InlineMessage>}
      {saved === "existing" && <InlineMessage tone="info">{t("imports.detail.alreadySaved")}</InlineMessage>}
      <p className="workspace-lead">{t("imports.detail.private")}</p>
      <dl className="workspace-facts workspace-panel">
        <div>
          <dt>{t("imports.col.source")}</dt>
          <dd>{data.source.name}</dd>
        </div>
        <div>
          <dt>{t("imports.col.by")}</dt>
          <dd>{data.staged_by}</dd>
        </div>
        <div>
          <dt>{t("imports.count.rows")}</dt>
          <dd>{i18n.number(data.row_count)}</dd>
        </div>
        <div>
          <dt>{t("imports.count.rowsWithErrors")}</dt>
          <dd>{i18n.number(data.rows_with_errors)}</dd>
        </div>
      </dl>
      {data.errors_by_code.length > 0 && (
        <section className="workspace-panel" aria-labelledby="detail-problems">
          <h2 id="detail-problems">{t("imports.detail.problems")}</h2>
          <ul className="workspace-issues">
            {data.errors_by_code.map((item) => (
              <li key={item.code}>
                {issueText(i18n, item.code)} <span className="review-note">({t("imports.detail.rows", { count: item.rows })})</span>
              </li>
            ))}
          </ul>
        </section>
      )}
      <section className="workspace-panel" aria-labelledby="detail-next">
        <h2 id="detail-next">{t("imports.next.title")}</h2>
        {data.review && REVIEW_SHEETS.includes(data.sheet) ? (
          <>
            <p>{t("imports.detail.reviewCounts", { toReview: data.review.to_review, blocked: data.review.blocked, linked: data.review.linked })}</p>
            {me.permissions.review_identity ? (
              <Link to={withQuery("/workspace/review", { snapshot: data.id })}>{t("imports.detail.openReview")}</Link>
            ) : (
              <p className="review-note">{t("imports.detail.othersReview")}</p>
            )}
          </>
        ) : (
          <>
            <p>{t("imports.detail.portsNext")}</p>
            {me.permissions.review_identity ? (
              <Link to="/workspace/ports">{t("imports.detail.openPorts")}</Link>
            ) : (
              <p className="review-note">{t("imports.detail.othersReview")}</p>
            )}
          </>
        )}
      </section>
    </>
  );
}
