import { api } from "../api/client";
import { Explore } from "../explore/Explore";
import { useI18n, type I18n } from "../i18n/I18nProvider";
import { Link } from "../router";
import { Icon } from "../ui/Icon";
import { WorkspaceShell } from "./WorkspaceShell";

type Key = Parameters<I18n["t"]>[0];

/** "3 minutes ago", from the reader's clock; the full date stays in the title attribute. */
function ago(i18n: I18n, timestamp: string, now: number) {
  const minutes = Math.max(0, Math.round((now - new Date(timestamp).getTime()) / 60000));
  const format = new Intl.RelativeTimeFormat(i18n.locale, { numeric: "auto" });
  if (minutes < 60) return format.format(-minutes, "minute");
  const hours = Math.round(minutes / 60);
  if (hours < 48) return format.format(-hours, "hour");
  return format.format(-Math.round(hours / 24), "day");
}

function SyncStatus() {
  const i18n = useI18n();
  const { t } = i18n;
  // Read again every minute, so "read 3 minutes ago" stays true while the page is open.
  const status = api.useQuery("get", "/api/private/v1/sync/", {}, { refetchInterval: 60_000 });
  const sheets = (status.data?.sheets ?? []).filter((sheet) => sheet.sheet !== "Data_ports");
  if (status.error) return <p className="sync-card sync-card--error">{t("sync.loadError")}</p>;
  if (!status.data) return null;
  if (sheets.length === 0) {
    return (
      <section className="sync-card" aria-labelledby="sync-title">
        <h2 id="sync-title">{t("sync.title")}</h2>
        <p>{t("sync.never")}</p>
      </section>
    );
  }
  // Two sources read the same tab (the sheet and the public logbook): say which is which.
  const sources = new Set(sheets.map((sheet) => sheet.source)).size;
  // The time the status was received is the reference, so rendering stays pure.
  const now = status.dataUpdatedAt;
  return (
    <section className="sync-card" aria-labelledby="sync-title">
      <h2 id="sync-title">{t("sync.title")}</h2>
      <p className="sync-card__lead">{t("sync.lead")}</p>
      <ul className="sync-card__list">
        {sheets.map((sheet) => {
          const change = sheet.last_change;
          const failing = sheet.last_status === "failed" || sheet.last_status === "refused";
          return (
            <li key={sheet.sheet} className={failing ? "sync-card__item sync-card__item--warn" : "sync-card__item"}>
              <span className="sync-card__name">
                {t(`explore.sheet.${sheet.sheet}` as Key)}
                {sources > 1 && <span className="sync-card__source"> · {sheet.source}</span>}
              </span>
              <span title={new Date(sheet.last_checked_at).toLocaleString(i18n.locale)}>
                <Icon name={failing ? "alert" : "check"} size={15} />{" "}
                {t(`sync.status.${sheet.last_status}` as Key, { when: ago(i18n, sheet.last_checked_at, now) })}
              </span>
              {sheet.last_change_at && (
                <span className="sync-card__change">
                  {t("sync.lastChange", { when: ago(i18n, sheet.last_change_at, now) })}{" "}
                  {t("sync.counts", {
                    look: change.to_look_at ?? 0,
                    fix: change.to_fix ?? 0,
                    same: change.unchanged ?? 0,
                  })}
                </span>
              )}
            </li>
          );
        })}
      </ul>
    </section>
  );
}

// The public logbook as the way to bring SOS's map up to date (ADR 0014): how far the sheet lags,
// what was rebuilt, what is verified, and the verified rows to paste into the sheet.
export function LogbookCard() {
  const i18n = useI18n();
  const { t } = i18n;
  const overview = api.useQuery("get", "/api/private/v1/logbook/", {});
  const data = overview.data;
  if (overview.error || !data || data.rows === 0) return null;
  return (
    <section className="logbook-card" aria-labelledby="logbook-card-title">
      <p className="logbook-card__eyebrow">{t("logbook.card.eyebrow")}</p>
      <h2 id="logbook-card-title">{t("logbook.card.title", { date: i18n.date(data.sheet_last_date) })}</h2>
      <p className="logbook-card__lead">
        {t("logbook.card.lead", {
          rows: data.rows,
          people: i18n.number(data.people),
          from: data.first_date ? i18n.date(data.first_date) : "…",
          to: data.last_date ? i18n.date(data.last_date) : "…",
        })}
      </p>
      <ol className="logbook-card__steps">
        <li>
          <b>{t("logbook.card.step1")}</b> {t("logbook.card.step1Body", { count: data.to_verify })}
          {data.to_check > 0 && ` ${t("logbook.card.toCheck", { count: data.to_check })}`}
        </li>
        <li>
          <b>{t("logbook.card.step2")}</b> {t("logbook.card.step2Body", { count: data.verified })}
        </li>
        <li>
          <b>{t("logbook.card.step3")}</b> {t("logbook.card.step3Body")}
        </li>
      </ol>
      <div className="logbook-card__actions">
        <Link to="/workspace/data?source=sos-logbook" className="pill-button pill-button--primary">
          <Icon name="map" size={16} />
          {t("logbook.card.show")}
        </Link>
        <a className="pill-button" href="/api/private/v1/logbook/export/" download>
          <Icon name="external" size={16} />
          {t("logbook.card.download", { count: data.verified })}
        </a>
      </div>
    </section>
  );
}

// The team's own view of the latest data received, kept out of the public page.
export function TeamData() {
  const { t } = useI18n();
  return (
    <WorkspaceShell section="data" title={t("workspace.section.data")} className="review review--wide">
      {() => (
        <>
          <SyncStatus />
          <LogbookCard />
          <Explore audience="team" />
        </>
      )}
    </WorkspaceShell>
  );
}
