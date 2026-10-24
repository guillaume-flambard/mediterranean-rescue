import { Combobox } from "@base-ui/react/combobox";
import { useEffect, useId, useRef, useState, type ReactNode } from "react";
import { useI18n } from "../i18n/I18nProvider";
import { isAbortError, useAbortableRequest } from "../shared/abortable";

export interface SearchComboboxProps<T> {
  label: string;
  /** Server search; the signal aborts superseded requests. */
  search: (query: string, signal: AbortSignal) => Promise<T[]>;
  itemId: (item: T) => string;
  itemLabel: (item: T) => string;
  renderItem?: (item: T) => ReactNode;
  value: T | null;
  onValueChange: (value: T | null) => void;
  placeholder?: string;
  debounceMs?: number;
}

// Server-side search following the Base UI async example: filter={null}, the selected item kept
// in `items`, the previous request aborted. Nothing is selected without an explicit choice.
export function SearchCombobox<T>({
  label,
  search,
  itemId,
  itemLabel,
  renderItem,
  value,
  onValueChange,
  placeholder,
  debounceMs = 250,
}: SearchComboboxProps<T>) {
  const { t } = useI18n();
  const labelId = useId();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<T[]>([]);
  const [pending, setPending] = useState(false);
  const [failed, setFailed] = useState(false);
  const timer = useRef<number | undefined>(undefined);
  const { run, abort } = useAbortableRequest();

  useEffect(() => () => window.clearTimeout(timer.current), []);

  const items = value && !results.some((item) => itemId(item) === itemId(value)) ? [...results, value] : results;
  const trimmed = query.trim();

  const lookFor = (next: string) => {
    window.clearTimeout(timer.current);
    abort();
    setFailed(false);
    if (!next.trim()) {
      setResults([]);
      setPending(false);
      return;
    }
    setPending(true);
    timer.current = window.setTimeout(() => {
      run((signal) => search(next.trim(), signal))
        .then((found) => {
          setResults(found);
          setPending(false);
        })
        .catch((error: unknown) => {
          if (isAbortError(error)) return;
          setFailed(true);
          setPending(false);
        });
    }, debounceMs);
  };

  const status = pending
    ? t("ui.search.searching")
    : failed
      ? t("ui.search.failed")
      : !trimmed
        ? value
          ? null
          : t("ui.search.start")
        : results.length === 0
          ? t("ui.search.none", { query: trimmed })
          : null;

  return (
    <Combobox.Root<T>
      items={items}
      filter={null}
      value={value}
      itemToStringLabel={itemLabel}
      isItemEqualToValue={(item, selected) => itemId(item) === itemId(selected)}
      onValueChange={(next) => {
        onValueChange(next ?? null);
        setQuery("");
      }}
      onInputValueChange={(next, { reason }) => {
        setQuery(next);
        if (reason !== "item-press") lookFor(next);
      }}
    >
      <div className="ui-field">
        {/* Base UI generates the input id and Combobox.Label does not name the input in 1.9:
            the label is linked explicitly. */}
        <span id={labelId} className="ui-field__label">
          {label}
        </span>
        <Combobox.InputGroup className="ui-combobox">
          <Combobox.Input
            aria-labelledby={labelId}
            placeholder={placeholder}
            className="ui-field__control ui-combobox__input"
          />
          <Combobox.Clear className="ui-combobox__clear" aria-label={t("ui.search.clear")}>
            ×
          </Combobox.Clear>
        </Combobox.InputGroup>
      </div>
      <Combobox.Portal>
        <Combobox.Positioner sideOffset={4} className="ui-layer-popover">
          <Combobox.Popup className="ui-select__popup ui-combobox__popup" aria-busy={pending || undefined}>
            <Combobox.Status className="ui-combobox__status">{status}</Combobox.Status>
            <Combobox.List>
              {(item: T) => (
                <Combobox.Item key={itemId(item)} value={item} className="ui-select__item">
                  {renderItem ? renderItem(item) : itemLabel(item)}
                </Combobox.Item>
              )}
            </Combobox.List>
          </Combobox.Popup>
        </Combobox.Positioner>
      </Combobox.Portal>
    </Combobox.Root>
  );
}
