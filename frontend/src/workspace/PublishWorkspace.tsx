import { Button as BaseButton } from "@base-ui/react/button";
import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api, errorCode, fetchClient, type Me, type PublicationOverview } from "../api/client";
import { kindName, peopleText } from "../explore/labels";
import { useI18n, type I18n } from "../i18n/I18nProvider";
import { Link } from "../router";
import { Button } from "../ui/Button";
import { ConfirmationDialog } from "../ui/ConfirmationDialog";
import { DataTable } from "../ui/DataTable";
import { EmptyState, InlineMessage, PendingState } from "../ui/Feedback";
import { Icon } from "../ui/Icon";
import { Pagination } from "../ui/Pagination";
import { TextField } from "../ui/TextField";
import { ME_QUERY, WorkspaceShell } from "./WorkspaceShell";

type Key = Parameters<I18n["t"]>[0];
type Status = "draft" | "published" | "withdrawn";
const STATUSES: readonly Status[] = ["draft", "published", "withdrawn"];
const PAGE = 25;
const OVERVIEW = ["get", "/api/private/v1/publication/"] as const;

function failure(t: I18n["t"], error: unknown): string {
  const code = errorCode(error);
  if (code === "rights_not_approved") return t("publish.error.rights");
  if (code === "conflict") return t("publish.error.conflict");
  if (code === "permission_denied") return t("publish.error.denied");
  if (code === "not_authenticated") return t("publish.error.signedOut");
  return t("publish.error.other");
}

// Two named decisions take a verified event to the public site: prepare (a private copy), then
// publish. Each asks for a short reason, kept with the event (ADR 0013).
export function PublishWorkspace() {
  const { t } = useI18n();
  return (
    <WorkspaceShell section="publish" title={t("publish.title")} className="review review--wide">
      {(me) => <Publish me={me} />}
    </WorkspaceShell>
  );
}

function Publish({ me }: { me: Me }) {
  const { t } = useI18n();
  const overview = api.useQuery("get", "/api/private/v1/publication/", {});
  if (overview.error) return <InlineMessage tone="error">{t("workspace.loadError")}</InlineMessage>;
  if (!overview.data) return <PendingState label={t("workspace.loading")} />;
  const data = overview.data;
  const locked = data.sources.filter((source) => !source.rights_approved);
  return (
    <div className="publish">
      <div className="team-home__head">
        <h1>{t("publish.title")}</h1>
        <p>{t("publish.lead")}</p>
      </div>
      {locked.length > 0 && (
        <div className="publish-lock" role="status">
          <Icon name="lock" size={22} />
          <div>
            <h2>{t("publish.locked.title")}</h2>
            <p>
              {t("publish.locked.body", {
                sources: locked.map((source) => source.name).join(", "),
              })}
            </p>
          </div>
        </div>
      )}
      <Prepare overview={data} />
      <Decide
        canPublish={data.can.publish}
        counts={data.events}
        ready={data.preparation.reduce((sum, item) => sum + item.ready, 0)}
        reviewer={me.permissions.review_identity}
      />
    </div>
  );
}

function Prepare({ overview }: { overview: PublicationOverview }) {
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const [reason, setReason] = useState("");
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{
    tone: "success" | "error";
    text: string;
  } | null>(null);
  const total = (key: "ready" | "changed" | "not_verified" | "to_fix") => overview.preparation.reduce((sum, item) => sum + item[key], 0);
  const ready = total("ready");

  const prepare = async () => {
    setSaving(true);
    setMessage(null);
    try {
      // A write is never aborted; the overview is replaced by the one the server returns.
      const { data, error } = await fetchClient.POST("/api/private/v1/publication/prepare/", { body: { reason: reason.trim() } });
      if (error) throw error;
      queryClient.setQueryData(api.queryOptions(...OVERVIEW, {}).queryKey, data.overview);
      await queryClient.invalidateQueries({
        queryKey: ["get", "/api/private/v1/publication/events/"],
      });
      setReason("");
      setMessage({
        tone: "success",
        text: t("publish.prepare.done", { count: data.created }),
      });
    } catch (error) {
      setMessage({ tone: "error", text: failure(t, error) });
      void queryClient.invalidateQueries({ queryKey: [...OVERVIEW] });
      if (errorCode(error) === "not_authenticated") void queryClient.invalidateQueries({ queryKey: ME_QUERY });
    } finally {
      setSaving(false);
    }
  };

  return (
    <section className="publish-step" aria-labelledby="prepare-title">
      <p className="publish-step__eyebrow">{t("publish.step", { number: 1 })}</p>
      <h2 id="prepare-title">{t("publish.prepare.title")}</h2>
      <p className="publish-step__why">{t("publish.prepare.why")}</p>
      <ul className="publish-counts">
        <li className="publish-counts__main">
          <b>{ready}</b> {t("publish.prepare.ready", { count: ready })}
        </li>
        {total("not_verified") > 0 && (
          <li>
            <Link to="/workspace/review">
              {t("publish.prepare.notVerified", {
                count: total("not_verified"),
              })}
            </Link>
          </li>
        )}
        {total("to_fix") > 0 && <li>{t("publish.prepare.toFix", { count: total("to_fix") })}</li>}
        {total("changed") > 0 && <li>{t("publish.prepare.changed", { count: total("changed") })}</li>}
      </ul>
      {!overview.can.prepare ? (
        <InlineMessage tone="info">{t("publish.prepare.notAllowed")}</InlineMessage>
      ) : ready > 0 ? (
        <form
          className="publish-form"
          onSubmit={(event) => {
            event.preventDefault();
            if (reason.trim()) void prepare();
          }}
        >
          <TextField
            label={t("publish.reason")}
            description={t("publish.prepare.reasonHelp")}
            value={reason}
            maxLength={500}
            onChange={(event) => setReason(event.target.value)}
          />
          <Button type="submit" loading={saving} disabled={!reason.trim()}>
            {t("publish.prepare.action", { count: ready })}
          </Button>
        </form>
      ) : null}
      {message && <InlineMessage tone={message.tone}>{message.text}</InlineMessage>}
    </section>
  );
}

function Decide({
  canPublish,
  counts,
  ready,
  reviewer,
}: {
  canPublish: boolean;
  counts: Record<Status, number>;
  /** Verified events not prepared yet: the empty list then points to step 1. */
  ready: number;
  reviewer: boolean;
}) {
  const i18n = useI18n();
  const { t } = i18n;
  const queryClient = useQueryClient();
  const [status, setStatus] = useState<Status>("draft");
  const [offset, setOffset] = useState(0);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [reason, setReason] = useState("");
  const [done, setDone] = useState<string | null>(null);
  const events = api.useQuery("get", "/api/private/v1/publication/events/", {
    params: { query: { status, offset, limit: PAGE } },
  });
  const publish = status !== "published";
  // Only the ticked events still shown count: a refreshed list never carries hidden ones along.
  const chosen = (events.data?.items ?? []).map((item) => item.id).filter((id) => selected.has(id));
  const count = chosen.length;
  const refresh = () =>
    Promise.all([
      queryClient.invalidateQueries({
        queryKey: ["get", "/api/private/v1/publication/events/"],
      }),
      queryClient.invalidateQueries({ queryKey: [...OVERVIEW] }),
    ]);

  const decide = async () => {
    const { data, error } = await fetchClient.POST("/api/private/v1/publication/decisions/", {
      body: {
        action: publish ? "publish" : "withdraw",
        events: chosen,
        reason: reason.trim(),
      },
    });
    if (error) {
      // The dialog stays open with the explanation; the list behind it shows the current state.
      void refresh();
      throw error;
    }
    setSelected(new Set());
    setReason("");
    setOffset(0);
    setDone(
      t(publish ? "publish.decide.published" : "publish.decide.withdrawn", {
        count: data.count,
      }),
    );
    await refresh();
  };

  return (
    <section className="publish-step" aria-labelledby="decide-title">
      <p className="publish-step__eyebrow">{t("publish.step", { number: 2 })}</p>
      <h2 id="decide-title">{t("publish.decide.title")}</h2>
      <p className="publish-step__why">{t("publish.decide.why")}</p>
      <div className="views publish-tabs" role="group" aria-label={t("publish.decide.show")}>
        {STATUSES.map((value) => (
          <BaseButton
            key={value}
            className="views__option"
            aria-pressed={status === value}
            onClick={() => {
              setStatus(value);
              setOffset(0);
              setSelected(new Set());
              setDone(null);
            }}
          >
            {t(`publish.tab.${value}` as Key)} <span className="publish-tabs__count">{counts[value]}</span>
          </BaseButton>
        ))}
      </div>
      {done && <InlineMessage tone="success">{done}</InlineMessage>}
      {!canPublish && <InlineMessage tone="info">{t("publish.decide.notAllowed")}</InlineMessage>}
      {events.error ? (
        <InlineMessage tone="error">{t("workspace.loadError")}</InlineMessage>
      ) : !events.data ? (
        <PendingState label={t("workspace.loading")} />
      ) : (
        <>
          <DataTable
            caption={t(`publish.tab.${status}` as Key)}
            rows={events.data.items}
            rowId={(item) => item.id}
            busy={events.isFetching}
            columns={[
              {
                key: "date",
                header: t("publish.col.date"),
                render: (item) => i18n.date(item.occurred_on),
              },
              {
                key: "event",
                header: t("publish.col.event"),
                render: (item) => (
                  <span>
                    <b>{kindName(i18n, item.kind)}</b> · {peopleText(i18n, item.kind, item.people)}
                  </span>
                ),
              },
              {
                key: "port",
                header: t("publish.col.port"),
                render: (item) => item.port ?? t("explore.logbook.noPort"),
              },
              {
                key: "place",
                header: t("publish.col.place"),
                render: (item) => t(item.located ? "publish.located" : "publish.notLocated"),
              },
            ]}
            selection={
              canPublish
                ? {
                    // An event whose source has not agreed cannot be ticked for publishing.
                    isEligible: (item) => !publish || item.rights_approved,
                    selected,
                    onChange: setSelected,
                    rowLabel: (item) => `${kindName(i18n, item.kind)}, ${i18n.date(item.occurred_on)}`,
                  }
                : undefined
            }
            empty={
              <EmptyState title={t(`publish.empty.${status}.title` as Key)}>
                {status === "draft" && ready > 0 ? (
                  <>
                    <p>{t("publish.empty.ready", { count: ready })}</p>
                    <a href="#prepare-title" className="pill-button">
                      {t("publish.empty.toStep1")}
                    </a>
                  </>
                ) : (
                  <>
                    <p>{t(`publish.empty.${status}.body` as Key)}</p>
                    {status === "draft" && reviewer && (
                      <Link to="/workspace/review" className="pill-button">
                        {t("home.verify.action")}
                      </Link>
                    )}
                  </>
                )}
              </EmptyState>
            }
          />
          {events.data.total_count > 0 && (
            <Pagination
              offset={offset}
              limit={PAGE}
              total={events.data.total_count}
              hasNext={events.data.has_next}
              disabled={events.isFetching}
              onOffsetChange={(next) => {
                setOffset(next);
                setSelected(new Set());
              }}
            />
          )}
          {canPublish && count > 0 && (
            <div className="publish-form publish-form--decision">
              <TextField
                label={t("publish.reason")}
                description={t(publish ? "publish.decide.reasonHelp" : "publish.decide.withdrawHelp")}
                value={reason}
                maxLength={500}
                onChange={(event) => setReason(event.target.value)}
              />
              <ConfirmationDialog
                trigger={
                  <Button variant={publish ? "primary" : "danger"} disabled={!reason.trim()}>
                    {t(publish ? "publish.decide.publish" : "publish.decide.withdraw", { count })}
                  </Button>
                }
                title={t(publish ? "publish.confirm.publishTitle" : "publish.confirm.withdrawTitle", { count })}
                consequence={t(publish ? "publish.confirm.publish" : "publish.confirm.withdraw", { count })}
                confirmLabel={t(publish ? "publish.decide.publish" : "publish.decide.withdraw", { count })}
                danger={!publish}
                onConfirm={decide}
                failureMessage={(error) => failure(t, error)}
              />
            </div>
          )}
        </>
      )}
    </section>
  );
}
