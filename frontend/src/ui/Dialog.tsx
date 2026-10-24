import { Dialog as BaseDialog } from "@base-ui/react/dialog";
import type { ReactElement, ReactNode } from "react";
import { useI18n } from "../i18n/I18nProvider";

export interface DialogProps {
  title: string;
  description?: string;
  /** Element that opens the dialog; omit it for a controlled dialog. */
  trigger?: ReactElement;
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  children?: ReactNode;
  /** Visually hide the title while keeping it as the accessible name. */
  hideTitle?: boolean;
  className?: string;
}

// A short task in a modal window; Base UI handles focus trap, Escape and focus return.
export function Dialog({ title, description, trigger, open, onOpenChange, children, hideTitle, className }: DialogProps) {
  const { t } = useI18n();
  return (
    <BaseDialog.Root
      {...(open !== undefined ? { open } : {})}
      {...(onOpenChange ? { onOpenChange: (next: boolean) => onOpenChange(next) } : {})}
    >
      {trigger && <BaseDialog.Trigger render={trigger} />}
      <BaseDialog.Portal>
        <BaseDialog.Backdrop className="ui-backdrop" />
        <BaseDialog.Popup className={["ui-dialog", className].filter(Boolean).join(" ")}>
          <BaseDialog.Title className={hideTitle ? "sr-only" : "ui-dialog__title"}>{title}</BaseDialog.Title>
          {description && <BaseDialog.Description className="ui-dialog__description">{description}</BaseDialog.Description>}
          <BaseDialog.Close className="ui-dialog__close">{t("ui.close")}</BaseDialog.Close>
          {children}
        </BaseDialog.Popup>
      </BaseDialog.Portal>
    </BaseDialog.Root>
  );
}
