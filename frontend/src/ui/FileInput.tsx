import { useId, useRef } from "react";
import { useI18n } from "../i18n/I18nProvider";

export interface FileInputProps {
  label: string;
  description?: string;
  accept?: string;
  file: File | null;
  onFileChange: (file: File | null) => void;
  error?: string | null;
}

// A native file input (keyboard, screen readers and mobile pickers work as usual) with the chosen
// file and its size shown next to it. The file stays in memory; nothing is uploaded on choice.
export function FileInput({ label, description, accept, file, onFileChange, error }: FileInputProps) {
  const { t, number } = useI18n();
  const id = useId();
  const input = useRef<HTMLInputElement>(null);
  const describedBy = [description ? `${id}-description` : null, error ? `${id}-error` : null].filter(Boolean).join(" ");
  return (
    <div className="ui-field ui-file">
      <label className="ui-field__label" htmlFor={id}>
        {label}
      </label>
      {description && (
        <span id={`${id}-description`} className="ui-field__description">
          {description}
        </span>
      )}
      <div className="ui-file__row">
        <input
          ref={input}
          id={id}
          type="file"
          accept={accept}
          className="ui-file__input"
          aria-invalid={error ? true : undefined}
          aria-describedby={describedBy || undefined}
          onChange={(event) => onFileChange(event.target.files?.[0] ?? null)}
        />
        <span className="ui-file__button" aria-hidden="true">
          {file ? t("ui.file.change") : t("ui.file.choose")}
        </span>
        <span className="ui-file__name" aria-live="polite">
          {file ? t("ui.file.chosen", { name: file.name, size: number(Math.max(1, Math.round(file.size / 1024))) }) : t("ui.file.none")}
        </span>
      </div>
      {error && (
        <span id={`${id}-error`} className="ui-field__error">
          {error}
        </span>
      )}
    </div>
  );
}
