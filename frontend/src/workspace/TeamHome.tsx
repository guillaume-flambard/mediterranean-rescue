import { Button as BaseButton } from "@base-ui/react/button";
import { useState } from "react";
import { api, type Me } from "../api/client";
import { useI18n, type I18n } from "../i18n/I18nProvider";
import { Link } from "../router";
import { Icon } from "../ui/Icon";
import { WorkspaceShell } from "./WorkspaceShell";

type Key = Parameters<I18n["t"]>[0];
type State = "todo" | "done" | "waiting";

interface Step {
  key: string;
  state: State;
  detail: string;
  path: string;
  action: string;
}

const INTRO_KEY = "team-intro-dismissed";

function introDismissed() {
  try {
    return window.localStorage.getItem(INTRO_KEY) === "1";
  } catch {
    return false;
  }
}

// The team space's front door: what needs doing today, in the order of the work, each step with
// one sentence and one button. Built for a volunteer who has never been here (PRODUCT.md, 0).
export function TeamHome() {
  const { t } = useI18n();
  return (
    <WorkspaceShell section="home" title={t("home.title")} className="review review--wide">
      {(me) => <Home me={me} />}
    </WorkspaceShell>
  );
}

function Home({ me }: { me: Me }) {
  const i18n = useI18n();
  const { t } = i18n;
  const reviewer = me.permissions.review_identity;
  const [intro, setIntro] = useState(() => !introDismissed());
  const sync = api.useQuery("get", "/api/private/v1/sync/", {}, { refetchInterval: 60_000 });
  const queue = api.useQuery("get", "/api/private/v1/preview/events/", { params: { query: { limit: 1 } } }, { enabled: reviewer });
  const publication = api.useQuery("get", "/api/private/v1/publication/", {});
  const labels = api.useQuery("get", "/api/private/v1/ports/labels/", { params: { query: { status: "to_read", limit: 1 } } }, { enabled: reviewer });

  const sheets = (sync.data?.sheets ?? []).filter((sheet) => sheet.sheet !== "Data_ports");
  const failing = sheets.some((sheet) => sheet.last_status === "failed" || sheet.last_status === "refused");
  const counts = queue.data?.counts;
  const prep = publication.data?.preparation ?? [];
  const sum = (key: "ready" | "changed" | "to_fix") => prep.reduce((total, item) => total + item[key], 0);
  const drafts = publication.data?.events.draft ?? 0;
  const published = publication.data?.events.published ?? 0;
  const locked = (publication.data?.sources ?? []).some((source) => !source.rights_approved);

  const steps: Step[] = [
    {
      key: "read",
      state: sync.data ? (failing ? "todo" : "done") : "waiting",
      detail: !sync.data ? t("home.loading") : sheets.length === 0 ? t("home.read.never") : failing ? t("home.read.failing") : t("home.read.ok"),
      path: "/workspace/data",
      action: t("home.read.action"),
    },
    {
      key: "verify",
      state: !counts ? "waiting" : counts.to_review > 0 ? "todo" : "done",
      detail: !reviewer
        ? t("home.notYourRole")
        : !counts
          ? t("home.loading")
          : `${t("home.verify.count", { count: counts.to_review })}${counts.blocked ? ` ${t("home.verify.blocked", { count: counts.blocked })}` : ""}`,
      path: "/workspace/review",
      action: t("home.verify.action"),
    },
    {
      key: "prepare",
      state: !publication.data ? "waiting" : sum("ready") > 0 ? "todo" : drafts + published > 0 ? "done" : "waiting",
      detail: !publication.data
        ? t("home.loading")
        : sum("ready") > 0
          ? t("home.prepare.count", { count: sum("ready") })
          : t("home.prepare.none"),
      path: "/workspace/publish",
      action: t("home.prepare.action"),
    },
    {
      key: "publish",
      state: !publication.data || locked ? "waiting" : drafts > 0 ? "todo" : published > 0 ? "done" : "waiting",
      detail: !publication.data
        ? t("home.loading")
        : locked
          ? t("home.publish.locked")
          : drafts > 0
            ? t("home.publish.count", { count: drafts })
            : t("home.publish.published", { count: published }),
      path: "/workspace/publish",
      action: t("home.publish.action"),
    },
  ];

  // One orange button on the page: the next thing to do. Later steps wait their turn.
  const next = steps.findIndex((step) => step.state === "todo");

  const close = () => {
    setIntro(false);
    try {
      window.localStorage.setItem(INTRO_KEY, "1");
    } catch {
      // Blocked storage: the introduction comes back next time, nothing else changes.
    }
  };

  return (
    <div className="team-home">
      <div className="team-home__head">
        <h1>{t("home.hello", { name: me.username })}</h1>
        <p>{t("home.lead")}</p>
      </div>

      {intro && (
        <section className="team-intro" aria-labelledby="team-intro-title">
          <div className="team-intro__head">
            <h2 id="team-intro-title">{t("home.intro.title")}</h2>
            <BaseButton className="icon-button team-intro__close" aria-label={t("home.intro.close")} onClick={close}>
              <Icon name="close" size={18} />
            </BaseButton>
          </div>
          <p>{t("home.intro.body")}</p>
          <p className="team-intro__safe">
            <Icon name="lock" size={16} />
            {t("home.intro.safe")}
          </p>
        </section>
      )}

      <section aria-labelledby="todo-title" className="team-steps">
        <h2 id="todo-title">{t("home.todo")}</h2>
        <ol>
          {steps.map((step, index) => (
            <li key={step.key} className={`team-step team-step--${step.state}`}>
              <span className="team-step__number" aria-hidden="true">
                {step.state === "done" ? <Icon name="check" size={18} /> : index + 1}
              </span>
              <div className="team-step__text">
                <h3>{t(`home.${step.key}.title` as Key)}</h3>
                <p className="team-step__why">{t(`home.${step.key}.why` as Key)}</p>
                <p className="team-step__detail">
                  <span className={`team-step__state team-step__state--${step.state}`}>{t(`home.state.${step.state}` as Key)}</span>
                  {step.detail}
                </p>
              </div>
              <Link to={step.path} className={`pill-button${index === next ? " pill-button--primary" : ""} team-step__action`}>
                {step.action}
                <Icon name="arrowRight" size={16} />
              </Link>
            </li>
          ))}
        </ol>
      </section>

      <section aria-labelledby="also-title" className="team-also">
        <h2 id="also-title">{t("home.also")}</h2>
        <div className="team-also__grid">
          {reviewer && (
            <Link to="/workspace/ports" className="team-also__card">
              <Icon name="anchor" size={20} />
              <span>
                <b>{t("home.ports.title")}</b>
                <span>{labels.data ? t("home.ports.count", { count: labels.data.total_count }) : t("home.loading")}</span>
              </span>
            </Link>
          )}
          <Link to="/workspace/imports" className="team-also__card">
            <Icon name="external" size={20} />
            <span>
              <b>{t("home.import.title")}</b>
              <span>{t("home.import.body")}</span>
            </span>
          </Link>
          <Link to="/about" className="team-also__card">
            <Icon name="help" size={20} />
            <span>
              <b>{t("home.words.title")}</b>
              <span>{t("home.words.body")}</span>
            </span>
          </Link>
        </div>
      </section>

      <section aria-labelledby="role-title" className="team-role">
        <h2 id="role-title">{t("home.role.title")}</h2>
        <ul>
          {(["review_identity", "prepare_drafts", "publish", "stage_snapshot"] as const).map((permission) => (
            <li key={permission} className={me.permissions[permission] ? "" : "team-role__no"}>
              <Icon name={me.permissions[permission] ? "check" : "close"} size={16} />
              {t(`home.role.${permission}` as Key)}
            </li>
          ))}
        </ul>
        <p>{t("home.role.ask")}</p>
      </section>
    </div>
  );
}
