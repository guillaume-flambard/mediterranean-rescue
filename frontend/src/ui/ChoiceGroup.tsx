import { Fieldset } from "@base-ui/react/fieldset";
import { Radio } from "@base-ui/react/radio";
import { RadioGroup } from "@base-ui/react/radio-group";
import { useId } from "react";

export interface Choice<V extends string> {
  value: V;
  label: string;
  description?: string;
}

export interface ChoiceGroupProps<V extends string> {
  legend: string;
  choices: readonly Choice<V>[];
  value: V | null;
  onValueChange: (value: V) => void;
}

// A decision among explicitly named options; nothing is chosen until the user picks one.
export function ChoiceGroup<V extends string>({ legend, choices, value, onValueChange }: ChoiceGroupProps<V>) {
  const id = useId();
  return (
    <Fieldset.Root render={<RadioGroup value={value} onValueChange={(next) => onValueChange(next as V)} />} className="ui-choices">
      <Fieldset.Legend className="ui-field__label">{legend}</Fieldset.Legend>
      {choices.map((choice) => {
        const descriptionId = `${id}-${choice.value}-description`;
        return (
          <div key={choice.value} className="ui-choice">
            <label className="ui-choice__option">
              <Radio.Root
                value={choice.value}
                className="ui-choice__radio"
                aria-describedby={choice.description ? descriptionId : undefined}
              >
                <Radio.Indicator className="ui-choice__dot" />
              </Radio.Root>
              <span className="ui-choice__label">{choice.label}</span>
            </label>
            {choice.description && (
              <span id={descriptionId} className="ui-field__description ui-choice__description">
                {choice.description}
              </span>
            )}
          </div>
        );
      })}
    </Fieldset.Root>
  );
}
