import { AlertDialog } from "@base-ui/react/alert-dialog";
import { useRef, useState, type ReactElement } from "react";
import { useI18n } from "../i18n/I18nProvider";
import { Button } from "./Button";
import { InlineMessage } from "./Feedback";

export interface ConfirmationDialogProps {
  trigger: ReactElement;
  title: string;
  /** The exact consequence of the action. */
  consequence: string;
  confirmLabel: string;
  /** Resolves when the server confirmed. A rejection keeps the dialog open. */
  onConfirm: () => Promise<void>;
  /**
   * What failed and what the user can do, shown inside the dialog: content outside a modal
   * dialog is hidden from assistive technologies while it is open.
   */
  failureMessage: (error: unknown) => string;
  danger?: boolean;
}

export function ConfirmationDialog({
  trigger,
  title,
  consequence,
  confirmLabel,
  onConfirm,
  failureMessage,
  danger,
}: ConfirmationDialogProps) {
  const { t } = useI18n();
  const [open, setOpen] = useState(false);
  const [pending, setPending] = useState(false);
  const [failure, setFailure] = useState<string | null>(null);
  const cancel = useRef<HTMLButtonElement>(null);

  const confirm = async () => {
    setPending(true);
    setFailure(null);
    try {
      await onConfirm();
      setOpen(false);
    } catch (error) {
      // Stay open with the explanation, so the user can retry or cancel in context.
      setFailure(failureMessage(error));
    } finally {
      setPending(false);
    }
  };

  return (
    // While the request runs, closing would hide an operation that still happens.
    <AlertDialog.Root
      open={open}
      onOpenChange={(next) => {
        if (pending) return;
        setOpen(next);
        if (!next) setFailure(null);
      }}
    >
      <AlertDialog.Trigger render={trigger} />
      <AlertDialog.Portal>
        <AlertDialog.Backdrop className="ui-backdrop" />
        <AlertDialog.Popup className="ui-dialog" initialFocus={cancel}>
          <AlertDialog.Title className="ui-dialog__title">{title}</AlertDialog.Title>
          <AlertDialog.Description className="ui-dialog__description">{consequence}</AlertDialog.Description>
          {failure && <InlineMessage tone="error">{failure}</InlineMessage>}
          <div className="ui-dialog__actions">
            <AlertDialog.Close ref={cancel} disabled={pending} render={<Button variant="secondary" />}>
              {t("ui.cancel")}
            </AlertDialog.Close>
            <Button variant={danger ? "danger" : "primary"} loading={pending} onClick={() => void confirm()}>
              {confirmLabel}
            </Button>
          </div>
        </AlertDialog.Popup>
      </AlertDialog.Portal>
    </AlertDialog.Root>
  );
}
