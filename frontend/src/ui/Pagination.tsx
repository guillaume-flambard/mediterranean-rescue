import { useI18n } from "../i18n/I18nProvider";
import { Button } from "./Button";

export interface PaginationProps {
  offset: number;
  limit: number;
  total: number;
  hasNext: boolean;
  disabled?: boolean;
  onOffsetChange: (offset: number) => void;
  className?: string;
}

// Bounded server pages; the total comes from the server, never from the visible page.
export function Pagination({ offset, limit, total, hasNext, disabled, onOffsetChange, className }: PaginationProps) {
  const { t } = useI18n();
  return (
    <nav className={["ui-pagination", className].filter(Boolean).join(" ")} aria-label={t("ui.pagination.label")}>
      {/* Focusable while disabled, so keyboard focus survives a page load. */}
      <Button
        size="sm"
        focusableWhenDisabled
        disabled={disabled || offset === 0}
        onClick={() => onOffsetChange(Math.max(0, offset - limit))}
      >
        {t("ui.previous")}
      </Button>
      <span className="ui-pagination__range">
        {total
          ? t("ui.pagination.range", { first: offset + 1, last: Math.min(offset + limit, total), total })
          : t("ui.pagination.empty")}
      </span>
      <Button size="sm" focusableWhenDisabled disabled={disabled || !hasNext} onClick={() => onOffsetChange(offset + limit)}>
        {t("ui.next")}
      </Button>
    </nav>
  );
}
