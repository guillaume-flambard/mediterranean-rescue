import { Checkbox as BaseCheckbox } from "@base-ui/react/checkbox";

export interface CheckboxProps {
  label: string;
  checked: boolean;
  onCheckedChange: (checked: boolean) => void;
  indeterminate?: boolean;
  disabled?: boolean;
}

export function Checkbox({ label, checked, onCheckedChange, indeterminate, disabled }: CheckboxProps) {
  return (
    <label className="ui-checkbox">
      <BaseCheckbox.Root
        checked={checked}
        indeterminate={indeterminate}
        disabled={disabled}
        onCheckedChange={(next) => onCheckedChange(next)}
        className="ui-checkbox__box"
      >
        <BaseCheckbox.Indicator className="ui-checkbox__mark" aria-hidden>
          {indeterminate ? "−" : "✓"}
        </BaseCheckbox.Indicator>
      </BaseCheckbox.Root>
      <span>{label}</span>
    </label>
  );
}
