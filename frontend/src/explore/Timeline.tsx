import { Button as BaseButton } from "@base-ui/react/button";
import { useEffect, useId, useMemo, useRef, useState, type Ref } from "react";
import { useI18n, type I18n } from "../i18n/I18nProvider";

export interface MonthCount {
  month: string; // YYYY-MM
  count: number;
}

/** Every month from the first to the last one with events, empty months included. */
export function continuousMonths(months: readonly MonthCount[]) {
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

export function lastDay(month: string) {
  const [year, number] = month.split("-").map(Number) as [number, number];
  return new Date(Date.UTC(year, number, 0)).toISOString().slice(0, 10);
}

// Bars, window and year labels sit inside the handles' travel: half a thumb in from each side.
const position = (index: number, count: number) => `calc(var(--thumb-half) + (100% - 2 * var(--thumb-half)) * ${index / count})`;

// View C's period selector: events per month as bars, two handles to choose whole months. The
// handles are native range inputs, so keyboard and screen readers work as they do everywhere.
export function Timeline({
  months,
  undated = 0,
  start,
  end,
  onPeriodChange,
  className = "",
  ref,
}: {
  months: readonly MonthCount[];
  /** Events with no date: never placed on the timeline, but always said. */
  undated?: number;
  start: string;
  end: string;
  onPeriodChange: (start: string, end: string) => void;
  className?: string;
  ref?: Ref<HTMLElement> | undefined;
}) {
  const titleId = useId();
  const i18n = useI18n();
  const { t } = i18n;
  const all = useMemo(() => continuousMonths(months), [months]);
  const last = all.length - 1;
  const keys = all.map((item) => item.month);
  // Months being moved, kept as keys so a refreshed list never shifts them.
  const [moving, setMoving] = useState<[string, string] | null>(null);
  const report = useRef(onPeriodChange);
  useEffect(() => {
    report.current = onPeriodChange;
  });

  useEffect(() => {
    if (!moving) return;
    const timer = window.setTimeout(() => {
      const whole = moving[0] === keys[0] && moving[1] === keys[last];
      report.current(whole ? "" : `${moving[0]}-01`, whole ? "" : lastDay(moving[1]));
      setMoving(null);
    }, 300);
    return () => window.clearTimeout(timer);
    // keys and last derive from `all`, which only changes with the months themselves.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [moving, all]);

  if (all.length === 0) {
    return (
      <p ref={ref as Ref<HTMLParagraphElement>} className={`timeline timeline--empty ${className}`.trim()}>
        {undated ? t("timeline.onlyUndated", { count: undated }) : t("timeline.empty")}
      </p>
    );
  }

  const indexOf = (month: string | undefined, fallback: number) => {
    const found = month ? keys.indexOf(month) : -1;
    return found === -1 ? fallback : found;
  };
  // A period chosen elsewhere that does not fall on whole months of this timeline is "custom".
  const custom =
    (start !== "" && (!start.endsWith("-01") || !keys.includes(start.slice(0, 7)))) ||
    (end !== "" && (end !== lastDay(end.slice(0, 7)) || !keys.includes(end.slice(0, 7))));
  const from = indexOf(moving?.[0] ?? (start ? start.slice(0, 7) : undefined), 0);
  const to = indexOf(moving?.[1] ?? (end ? end.slice(0, 7) : undefined), last);
  const whole = !custom && from === 0 && to === last;
  const max = Math.max(1, ...all.map((item) => item.count));
  const selected = all.slice(from, to + 1).reduce((sum, item) => sum + item.count, 0);
  const label = custom
    ? t("timeline.custom")
    : whole
      ? t("timeline.whole", { count: selected })
      : from === to
        ? t("timeline.oneMonth", { month: monthName(i18n, keys[from]!), count: selected })
        : t("timeline.selected", { from: monthName(i18n, keys[from]!), to: monthName(i18n, keys[to]!), count: selected });
  // A year label is dropped when it would sit within three months of the next one.
  const years = all
    .map((item, index) => ({ index, year: item.month.slice(0, 4), january: item.month.endsWith("-01") }))
    .filter((item) => item.january || (item.index === 0 && !keys.slice(1, 4).some((key) => key.endsWith("-01"))));

  return (
    <section ref={ref} className={`timeline ${className}`.trim()} aria-labelledby={titleId}>
      <div className="timeline__head">
        <h2 id={titleId}>{t("timeline.title")}</h2>
        <p aria-live="polite">{label}</p>
        {!whole && (
          <BaseButton className="link-button" onClick={() => onPeriodChange("", "")}>
            {t("timeline.reset")}
          </BaseButton>
        )}
      </div>
      {undated > 0 && <p className="timeline__undated">{t("timeline.undated", { count: undated })}</p>}
      <div className="timeline__chart" aria-hidden="true">
        {all.map((item, index) => (
          <span
            key={item.month}
            className={`timeline__bar${whole || (index >= from && index <= to) ? " timeline__bar--in" : ""}`}
            style={{ height: `${Math.max(item.count ? 6 : 2, (item.count / max) * 100)}%` }}
          />
        ))}
        {!whole && (
          <span className="timeline__window" style={{ left: position(from, all.length), width: `calc((100% - 2 * var(--thumb-half)) * ${(to - from + 1) / all.length})` }} />
        )}
      </div>
      <div className={`timeline__handles${from === to && to === last ? " timeline__handles--start-on-top" : ""}`}>
        <input
          type="range"
          min={0}
          max={last}
          value={from}
          aria-label={t("timeline.start")}
          aria-valuetext={monthName(i18n, keys[from]!)}
          onChange={(event) => setMoving([keys[Math.min(Number(event.target.value), to)]!, keys[to]!])}
        />
        <input
          type="range"
          min={0}
          max={last}
          value={to}
          aria-label={t("timeline.end")}
          aria-valuetext={monthName(i18n, keys[to]!)}
          onChange={(event) => setMoving([keys[from]!, keys[Math.max(Number(event.target.value), from)]!])}
        />
      </div>
      <div className="timeline__years" aria-hidden="true">
        {years.map((item) => (
          <span key={item.index} style={{ left: position(item.index, all.length) }}>
            {item.year}
          </span>
        ))}
      </div>
    </section>
  );
}
