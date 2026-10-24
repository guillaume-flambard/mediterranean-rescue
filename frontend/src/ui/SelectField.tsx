import { Select } from "@base-ui/react/select";

export interface SelectOption<V extends string> {
  value: V;
  label: string;
  /** Language of the label when it differs from the page (WCAG 3.1.2). */
  lang?: string;
}

export interface SelectFieldProps<V extends string> {
  label: string;
  value: V | "";
  options: readonly SelectOption<V>[];
  onValueChange: (value: V | "") => void;
  /** Label of the empty choice; omit it to require a value. */
  emptyLabel?: string;
  className?: string;
}

// For a short, stable list of known categories; long searchable lists use a combobox.
export function SelectField<V extends string>({
  label,
  value,
  options,
  onValueChange,
  emptyLabel,
  className,
}: SelectFieldProps<V>) {
  const selected = options.find((option) => option.value === value);
  const current = selected?.label ?? emptyLabel ?? "";
  return (
    <div className={["ui-field", className].filter(Boolean).join(" ")}>
      <Select.Root<V | ""> value={value} onValueChange={(next) => onValueChange(next ?? "")}>
        <Select.Label className="ui-field__label">{label}</Select.Label>
        <Select.Trigger className="ui-select__trigger">
          <Select.Value lang={selected?.lang}>{current}</Select.Value>
          <Select.Icon className="ui-select__icon" aria-hidden>
            ⌄
          </Select.Icon>
        </Select.Trigger>
        <Select.Portal>
          <Select.Positioner sideOffset={6} className="ui-layer-popover">
            <Select.Popup className="ui-select__popup">
              <Select.List>
                {emptyLabel !== undefined && (
                  <Select.Item value="" className="ui-select__item">
                    <Select.ItemText>{emptyLabel}</Select.ItemText>
                  </Select.Item>
                )}
                {options.map((option) => (
                  <Select.Item key={option.value} value={option.value} className="ui-select__item" lang={option.lang}>
                    <Select.ItemText>{option.label}</Select.ItemText>
                    <Select.ItemIndicator className="ui-select__check" aria-hidden>
                      ✓
                    </Select.ItemIndicator>
                  </Select.Item>
                ))}
              </Select.List>
            </Select.Popup>
          </Select.Positioner>
        </Select.Portal>
      </Select.Root>
    </div>
  );
}
