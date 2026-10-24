import { api } from "../api/client";
import { Explore } from "../explore/Explore";
import { useI18n, type I18n } from "../i18n/I18nProvider";
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
              <span className="sync-card__name">{t(`explore.sheet.${sheet.sheet}` as Key)}</span>
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

// The team's own view of the latest data received, kept out of the public page.
export function TeamData() {
  const { t } = useI18n();
  return (
    <WorkspaceShell section="data" title={t("workspace.section.data")} className="review review--wide">
      {() => (
        <>
          <SyncStatus />
          <Explore audience="team" />
        </>
      )}
    </WorkspaceShell>
  );
}
