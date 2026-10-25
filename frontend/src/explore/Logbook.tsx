import { Button as BaseButton } from "@base-ui/react/button";
import { useEffect, useEffectEvent, useRef } from "react";
import { useI18n, type I18n } from "../i18n/I18nProvider";
import { Icon } from "../ui/Icon";
import { PreviewBody, PublicBody } from "./EventBody";
import { kindName, peopleText, type Key } from "./labels";

export interface LogbookItem {
  id: string;
  date: string | null;
  kind: string | null;
  people: number | null;
  port: string | null;
  status: "to_review" | "blocked" | "linked" | null;
  /** Where the record comes from: the source, or the data update. */
  origin: string;
}

interface Month {
  key: string;
  title: string;
  items: LogbookItem[];
}

// Dates are calendar days from the source: formatted in UTC so no time zone moves them.
function monthTitle(i18n: I18n, date: string) {
  return new Intl.DateTimeFormat(i18n.locale, { month: "long", year: "numeric", timeZone: "UTC" }).format(new Date(`${date}T00:00:00Z`));
}

function dayLabel(i18n: I18n, date: string) {
  return new Intl.DateTimeFormat(i18n.locale, { day: "numeric", month: "short", timeZone: "UTC" }).format(new Date(`${date}T00:00:00Z`));
}

function byMonth(i18n: I18n, items: readonly LogbookItem[]): Month[] {
  const months: Month[] = [];
  for (const item of items) {
    const key = item.date?.slice(0, 7) ?? "unknown";
    let month = months.at(-1);
    if (!month || month.key !== key) {
      month = { key, title: item.date ? monthTitle(i18n, item.date) : i18n.t("explore.logbook.noDate"), items: [] };
      months.push(month);
    }
    month.items.push(item);
  }
  return months;
}

/**
 * Totals of a month, only when every event of that month is loaded; never a partial sum. People
 * are added up for rescues only: a person rescued and later transferred must not count twice.
 */
export function monthTotals(i18n: I18n, items: readonly LogbookItem[], complete: boolean, cut: boolean) {
  if (!complete) return i18n.t("explore.logbook.partial");
  const rescues = items.filter((item) => item.kind === "rescue");
  const known = rescues.filter((item) => item.people !== null);
  const rescued = known.reduce((sum, item) => sum + (item.people ?? 0), 0);
  let totals = i18n.t("explore.logbook.events", { count: items.length });
  if (known.length > 0) {
    totals += ` · ${i18n.t(known.length === rescues.length ? "explore.logbook.rescued" : "explore.logbook.rescuedKnown", { count: rescued })}`;
  }
  // A month cut by the chosen period only counts the days inside it.
  return cut ? i18n.t("explore.logbook.inPeriod", { totals }) : totals;
}

// View B: the events as a ship's logbook, month by month. The entry being read lights its point
// on the map, which follows the reading.
export function Logbook({
  items,
  preview,
  openId,
  hasMore,
  period,
  onToggle,
  onRead,
}: {
  items: readonly LogbookItem[];
  preview: boolean;
  openId: string | null;
  hasMore: boolean;
  /** A period is chosen: the first and last months shown may be cut by it. */
  period: boolean;
  onToggle: (id: string) => void;
  onRead: (id: string | null) => void;
}) {
  const i18n = useI18n();
  const { t } = i18n;
  const list = useRef<HTMLDivElement>(null);
  const months = byMonth(i18n, items);

  const read = useEffectEvent((id: string | null) => onRead(id));
  // Rebuilt only when the list of entries changes, not on every render.
  const ids = items.map((item) => item.id).join(" ");

  // The entry crossing the middle of the screen is the one being read.
  useEffect(() => {
    const root = list.current;
    if (!root || typeof IntersectionObserver === "undefined") return;
    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries.find((entry) => entry.isIntersecting);
        if (visible) read((visible.target as HTMLElement).dataset.id ?? null);
      },
      { rootMargin: "-45% 0px -45% 0px" },
    );
    root.querySelectorAll<HTMLElement>("[data-id]").forEach((element) => observer.observe(element));
    return () => observer.disconnect();
  }, [ids]);

  return (
    <div className="logbook" ref={list}>
      {months.map((month, index) => (
        <section key={month.key} className="logbook__month" aria-labelledby={`month-${month.key}`}>
          <h2 id={`month-${month.key}`} className="logbook__month-title">
            {month.title}
            <span className="sr-only">: </span>
            <span>{monthTotals(i18n, month.items, index < months.length - 1 || !hasMore, period && (index === 0 || index === months.length - 1))}</span>
          </h2>
          <ol className="logbook__entries">
            {month.items.map((item) => {
              const open = openId === item.id;
              return (
                <li key={item.id} id={`event-${item.id}`} data-id={item.id} data-kind={item.kind ?? undefined} className={`logbook__entry${open ? " logbook__entry--open" : ""}`}>
                  <BaseButton className="logbook__summary" aria-expanded={open} aria-controls={`log-${item.id}`} onClick={() => onToggle(item.id)}>
                    <span className="logbook__day">{item.date ? dayLabel(i18n, item.date) : "?"}</span>
                    <span className="logbook__dot" aria-hidden="true" />
                    <span className="logbook__text">
                      <b>
                        {kindName(i18n, item.kind)} · {peopleText(i18n, item.kind, item.people)}
                      </b>
                      <span>
                        {item.port ? t("explore.logbook.port", { port: item.port }) : t("explore.logbook.noPort")}
                        {item.status && (
                          <span className={`status status--${item.status}`}>
                            <i aria-hidden="true" />
                            {t(`explore.status.${item.status}` as Key)}
                          </span>
                        )}
                      </span>
                      <span className="logbook__origin">{item.origin}</span>
                    </span>
                    <Icon name="chevronDown" className="logbook__chevron" />
                  </BaseButton>
                  <div id={`log-${item.id}`} className="card__body logbook__body" role="region" aria-label={t("detail.title")} hidden={!open}>
                    {open && (preview ? <PreviewBody id={item.id} /> : <PublicBody id={item.id} />)}
                  </div>
                </li>
              );
            })}
          </ol>
        </section>
      ))}
    </div>
  );
}
