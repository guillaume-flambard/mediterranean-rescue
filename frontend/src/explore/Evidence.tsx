import type { components } from "../api/schema";
import { useI18n, type I18n } from "../i18n/I18nProvider";
import { Icon } from "../ui/Icon";
import type { Key } from "./labels";

type Evidence = components["schemas"]["LogbookEvidence"];

// The reader's notes are codes ("position_read:compact:3426 01209", "grouped:3"), said in the
// reader's language (ADR 0014).
const CHECKS = [
  "date_outside",
  "medevac",
  "reported_in_message",
  "partial_replaced",
  "no_position",
  "position_read",
  "two_boats",
  "news_site",
  "grouped",
  "count_unknown",
  "merged_repeat",
  "same_size_twice",
  "repeat_unsure",
  "rotation_total",
];

export function checkText(i18n: I18n, point: string) {
  const [code = "", value = "", raw = ""] = point.split(":");
  if (!CHECKS.includes(code)) return point;
  if (code === "position_read") return i18n.t(`logbook.check.position_read.${value}` as Key, { value: raw });
  // A time keeps its colon: "merged_repeat:07:20".
  if (code === "merged_repeat" || code === "repeat_unsure")
    return i18n.t(`logbook.check.${code}` as Key, { value: point.slice(code.length + 1) });
  if (code === "date_outside") return i18n.t("logbook.check.date_outside", { value: i18n.date(value) });
  if (code === "rotation_total") {
    const [stated = "", found = ""] = value.split("/");
    return i18n.t("logbook.check.rotation_total", { stated, found });
  }
  return i18n.t(`logbook.check.${code}` as Key, { value });
}

/** Rows from a French news article rather than from the logbook itself. */
export const fromNewsSite = (evidence: Evidence) => evidence.to_check.includes("news_site");

/** "2026-07-22/2026-08-03" (the mission's dates) said as a sentence; any other name as is. */
export function missionName(i18n: I18n, rotation: string) {
  const window = /^(\d{4}-\d{2}-\d{2})\/(\d{4}-\d{2}-\d{2})$/.exec(rotation);
  if (!window) return rotation;
  return i18n.t("logbook.mission", { from: i18n.date(window[1]!), to: i18n.date(window[2]!) });
}

/** "2026-08-17 10:14" said as "17 August 2026, 10:14" in the reader's language. */
function when(i18n: I18n, loggedAt: string) {
  const [day = "", time = ""] = loggedAt.split(" ");
  if (!/^\d{4}-\d{2}-\d{2}$/.test(day)) return loggedAt;
  return time ? i18n.t("logbook.evidence.at", { date: i18n.date(day), time }) : i18n.date(day);
}

const safeHref = (url: string) => (/^https:\/\/(www\.)?sosmediterranee\.(org|fr)\//.test(url) ? url : undefined);

// The sentence a rebuilt operation comes from, quoted, with what to check and the way to the page.
export function EvidenceBlock({ evidence }: { evidence: Evidence }) {
  const i18n = useI18n();
  const { t } = i18n;
  const news = fromNewsSite(evidence);
  const checks = evidence.to_check.filter((point) => point !== "news_site");
  const href = safeHref(evidence.url);
  return (
    <div className="logbook-evidence">
      <p className="logbook-evidence__label">
        {t(news ? "logbook.evidence.newsLabel" : "logbook.evidence.label", { when: when(i18n, evidence.logged_at) })}
      </p>
      <blockquote lang={news ? "fr" : "en"}>{evidence.quote}</blockquote>
      {evidence.sheet_line !== null && (
        <p className="logbook-evidence__in-sheet">
          <Icon name="check" size={16} /> {t("logbook.evidence.inSheet", { line: evidence.sheet_line })}
        </p>
      )}
      {checks.length > 0 && (
        <div className="logbook-evidence__check">
          <p>
            <Icon name="alert" size={16} /> {t("logbook.evidence.toCheck")}
          </p>
          <ul>
            {checks.map((point) => (
              <li key={point}>{checkText(i18n, point)}</li>
            ))}
          </ul>
        </div>
      )}
      <p className="card__provenance">
        {news
          ? t("logbook.evidence.newsProvenance", { title: evidence.rotation })
          : t("logbook.evidence.provenance", { rotation: missionName(i18n, evidence.rotation) })}{" "}
        {href && (
          <a href={href} target="_blank" rel="noreferrer">
            {t(news ? "logbook.evidence.openArticle" : "logbook.evidence.open")}
          </a>
        )}
      </p>
    </div>
  );
}
