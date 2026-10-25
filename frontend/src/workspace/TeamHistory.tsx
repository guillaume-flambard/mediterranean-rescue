import { Button as BaseButton } from "@base-ui/react/button";
import type { components } from "../api/schema";
import { api } from "../api/client";
import { kindName } from "../explore/labels";
import { useI18n, type I18n } from "../i18n/I18nProvider";
import { changeQuery, Link, useLocation } from "../router";
import { InlineMessage } from "../ui/Feedback";
import { Icon, type IconName } from "../ui/Icon";
import { WorkspaceShell } from "./WorkspaceShell";

type Key = Parameters<I18n["t"]>[0];
type Item = components["schemas"]["HistoryItem"];
type Kind = Item["kind"];

const PAGE = 30;
const KINDS: Kind[] = ["verify", "prepare", "publish", "withdraw", "port", "correction"];
const ICONS: Record<Kind, IconName> = {
  verify: "listCheck",
  prepare: "check",
  publish: "send",
  withdraw: "close",
  port: "anchor",
  correction: "upload",
};

/** What was decided on, in words: an operation by its date, kind and people, or a port name. */
function subjectText(i18n: I18n, item: Item) {
  const { subject } = item;
  if (item.kind === "port") return i18n.t("history.subject.port", { label: subject.label ?? "" });
  const date = subject.occurred_on ? i18n.date(subject.occurred_on) : i18n.t("review.unknown");
  const parts = [kindName(i18n, subject.kind)];
  if (subject.people !== null) parts.push(i18n.t("history.subject.people", { count: subject.people }));
  return i18n.t("history.subject.event", { date, facts: parts.join(", ") });
}

function detailText(i18n: I18n, item: Item) {
  if (!item.detail || item.kind === "publish" || item.kind === "withdraw") return null;
  const key = `history.detail.${item.kind}.${item.detail}` as Key;
  const text = i18n.t(key);
  return text === key ? null : text;
}

function time(locale: string, value: string) {
  return new Date(value).toLocaleTimeString(locale, { hour: "2-digit", minute: "2-digit" });
}

function day(value: string) {
  // Local calendar day of the decision, as the person lived it.
  const date = new Date(value);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
}

// Who decided what, when and why: the team's own memory, newest first (25 October 2026).
function History() {
  const i18n = useI18n();
  const { t } = i18n;
  const { query } = useLocation();
  const scope = query.get("scope") === "team" ? "team" : "mine";
  const kindParam = query.get("kind");
  const kind = KINDS.find((value) => value === kindParam);
  const list = api.useInfiniteQuery(
    "get",
    "/api/private/v1/history/",
    { params: { query: { scope, ...(kind ? { kind } : {}), limit: PAGE } } },
    {
      pageParamName: "offset",
      initialPageParam: 0,
      getNextPageParam: (last, all) => (last.has_next ? all.length * PAGE : undefined),
    },
  );
  const items = (list.data?.pages ?? []).flatMap((page) => page.items);
  const days: { day: string; items: Item[] }[] = [];
  for (const item of items) {
    const key = day(item.at);
    if (days.at(-1)?.day !== key) days.push({ day: key, items: [] });
    days.at(-1)!.items.push(item);
  }

  return (
    <div className="history">
      <div className="practice__head">
        <h1>{t("history.title")}</h1>
        <p>{t("history.lead")}</p>
      </div>

      <div className="history__filters">
        <div className="views history__scope" role="group" aria-label={t("history.scope")}>
          {(["mine", "team"] as const).map((value) => (
            <BaseButton
              key={value}
              className="views__option"
              aria-pressed={scope === value}
              onClick={() => changeQuery({ scope: value === "mine" ? null : value }, { replace: true })}
            >
              <Icon name={value === "mine" ? "people" : "grid"} size={16} />
              {t(`history.scope.${value}`)}
            </BaseButton>
          ))}
        </div>
        <div className="chips history__kinds" role="group" aria-label={t("history.kinds")}>
          <BaseButton className="chip" aria-pressed={!kind} onClick={() => changeQuery({ kind: null }, { replace: true })}>
            {t("history.kind.all")}
          </BaseButton>
          {KINDS.map((value) => (
            <BaseButton key={value} className="chip" aria-pressed={kind === value} onClick={() => changeQuery({ kind: value }, { replace: true })}>
              {t(`history.kind.${value}` as Key)}
            </BaseButton>
          ))}
        </div>
      </div>

      {list.error && !list.data ? (
        <InlineMessage tone="error">{t("history.error")}</InlineMessage>
      ) : !list.data ? (
        <p className="review-note">{t("history.loading")}</p>
      ) : items.length === 0 ? (
        <div className="history__empty">
          <h2>{t(scope === "mine" ? "history.empty.mine" : "history.empty.team")}</h2>
          <p>{t("history.empty.body")}</p>
        </div>
      ) : (
        days.map((group) => (
          <section key={group.day} className="history__day" aria-label={i18n.date(group.day, "long")}>
            <h2>{i18n.date(group.day, "long")}</h2>
            <ol>
              {group.items.map((item) => {
                const detail = detailText(i18n, item);
                return (
                  <li key={item.id} className={`history__item history__item--${item.kind}`}>
                    <span className="history__icon" aria-hidden="true">
                      <Icon name={ICONS[item.kind]} size={18} />
                    </span>
                    <div className="history__body">
                      <p className="history__what">
                        {scope === "mine"
                          ? t(`history.mine.${item.kind}` as Key, { what: subjectText(i18n, item) })
                          : t(`history.team.${item.kind}` as Key, { who: item.actor, what: subjectText(i18n, item) })}
                      </p>
                      <p className="history__meta">
                        <time dateTime={item.at}>{time(i18n.locale, item.at)}</time>
                        {detail && <span> · {detail}</span>}
                      </p>
                      <blockquote className="history__reason">{item.reason || t("history.noReason")}</blockquote>
                    </div>
                    {item.path && (
                      <Link to={item.path} className="link-button history__open">
                        {t("history.open")}
                        <Icon name="arrowRight" size={14} />
                      </Link>
                    )}
                  </li>
                );
              })}
            </ol>
          </section>
        ))
      )}

      {list.hasNextPage && (
        <BaseButton className="pill-button history__more" disabled={list.isFetchingNextPage} onClick={() => void list.fetchNextPage()}>
          {list.isFetchingNextPage ? t("history.loading") : t("history.more")}
        </BaseButton>
      )}
    </div>
  );
}

export function TeamHistory() {
  const { t } = useI18n();
  return (
    <WorkspaceShell section="history" title={t("workspace.section.history")} className="review">
      {() => <History />}
    </WorkspaceShell>
  );
}
