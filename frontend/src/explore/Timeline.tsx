import { Button as BaseButton } from "@base-ui/react/button";
import { useEffect, useId, useState } from "react";
import { useI18n, type I18n } from "../i18n/I18nProvider";

export interface MonthCount {
  month: string; // YYYY-MM
  count: number;
}

/** Every month from the first to the last one with events, empty months included. */
function continuousMonths(months: readonly MonthCount[]) {
  if (months.length === 0) return [];
  const counts = new Map(months.map((item) => [item.month, item.count]));
  const [firstYear, firstMonth] = months[0]!.month.split("-").map(Number) as [number, number];
  const [lastYear, lastMonth] = months.at(-1)!.month.split("-").map(Number) as [number, number];
  const all: MonthCount[] = [];
  for (let year = firstYear, month = firstMonth; year < lastYear || (year === lastYear && month <= lastMonth); ) {
    const key = `${year}-${String(month).padStart(2, "0")}`;
    all.push({ month: key, count: counts.get(key) ?? 0 });
    month += 1;
    if (month > 12) {
      month = 1;
      year += 1;
    }
  }
  return all;
}

function monthName(i18n: I18n, month: string) {
  return new Intl.DateTimeFormat(i18n.locale, { month: "short", year: "numeric", timeZone: "UTC" }).format(new Date(`${month}-01T00:00:00Z`));
}

function lastDay(month: string) {
  const [year, number] = month.split("-").map(Number) as [number, number];
  return new Date(Date.UTC(year, number, 0)).toISOString().slice(0, 10);
}

// View C's period selector: events per month as bars, two handles to choose the period. The handles
// are native range inputs, so keyboard and screen readers work as they do everywhere.
export function Timeline({
  months,
  start,
  end,
  onPeriodChange,
  className = "",
}: {
  months: readonly MonthCount[];
  start: string;
  end: string;
  onPeriodChange: (start: string, end: string) => void;
  className?: string;
}) {
  const titleId = useId();
  const i18n = useI18n();
  const { t } = i18n;
  const all = continuousMonths(months);
  const last = all.length - 1;
  const indexOf = (date: string, fallback: number) => {
    const found = all.findIndex((item) => item.month === date.slice(0, 7));
    return found === -1 ? fallback : found;
  };
  const [range, setRange] = useState<[number, number] | null>(null);
  // The handles follow the period chosen elsewhere (chips, reset) unless they are being moved.
  const from = range?.[0] ?? (start ? indexOf(start, 0) : 0);
  const to = range?.[1] ?? (end ? indexOf(end, last) : last);

  useEffect(() => {
    if (!range) return;
    const timer = window.setTimeout(() => {
      const whole = range[0] === 0 && range[1] === last;
      onPeriodChange(whole ? "" : `${all[range[0]]!.month}-01`, whole ? "" : lastDay(all[range[1]]!.month));
      setRange(null);
    }, 300);
    return () => window.clearTimeout(timer);
  }, [range, last, all, onPeriodChange]);

  if (all.length === 0) return <p className="timeline timeline--empty">{t("timeline.empty")}</p>;
  const max = Math.max(1, ...all.map((item) => item.count));
  const selected = all.slice(from, to + 1).reduce((sum, item) => sum + item.count, 0);
  const whole = from === 0 && to === last;

  return (
    <section className={`timeline ${className}`.trim()} aria-labelledby={titleId}>
      <div className="timeline__head">
        <h2 id={titleId}>{t("timeline.title")}</h2>
        <p aria-live="polite">
          {whole
            ? t("timeline.whole", { count: selected })
            : t("timeline.selected", { from: monthName(i18n, all[from]!.month), to: monthName(i18n, all[to]!.month), count: selected })}
        </p>
        {!whole && (
          <BaseButton className="link-button" onClick={() => onPeriodChange("", "")}>
            {t("timeline.reset")}
          </BaseButton>
        )}
      </div>
      <div className="timeline__chart" aria-hidden="true">
        {all.map((item, index) => (
          <span
            key={item.month}
            className={`timeline__bar${index >= from && index <= to ? " timeline__bar--in" : ""}`}
            style={{ height: `${Math.max(item.count ? 6 : 2, (item.count / max) * 100)}%` }}
            title={`${monthName(i18n, item.month)}: ${item.count}`}
          />
        ))}
        <span className="timeline__window" style={{ left: `${(from / all.length) * 100}%`, width: `${((to - from + 1) / all.length) * 100}%` }} />
      </div>
      <div className="timeline__handles">
        <input
          type="range"
          min={0}
          max={last}
          value={from}
          aria-label={t("timeline.start")}
          aria-valuetext={monthName(i18n, all[from]!.month)}
          onChange={(event) => setRange([Math.min(Number(event.target.value), to), to])}
        />
        <input
          type="range"
          min={0}
          max={last}
          value={to}
          aria-label={t("timeline.end")}
          aria-valuetext={monthName(i18n, all[to]!.month)}
          onChange={(event) => setRange([from, Math.max(Number(event.target.value), from)])}
        />
      </div>
      <div className="timeline__years" aria-hidden="true">
        {all.map((item, index) =>
          item.month.endsWith("-01") || index === 0 ? (
            <span key={item.month} style={{ left: `${(index / all.length) * 100}%` }}>
              {item.month.slice(0, 4)}
            </span>
          ) : null,
        )}
      </div>
    </section>
  );
}
