import { Button as BaseButton } from "@base-ui/react/button";
import type { ComponentProps } from "react";

export type ButtonVariant = "primary" | "secondary" | "quiet" | "danger";
export type ButtonSize = "sm" | "md" | "lg";

export interface ButtonProps extends ComponentProps<typeof BaseButton> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  /** Keeps the label and width, announces the wait and blocks a second submission. */
  loading?: boolean;
}

export function Button({
  variant = "secondary",
  size = "md",
  loading = false,
  className,
  disabled,
  onClick,
  children,
  ...props
}: ButtonProps) {
  return (
    <BaseButton
      {...props}
      // Focusable while loading so focus is not lost in the middle of a submission.
      focusableWhenDisabled={loading || props.focusableWhenDisabled}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      className={["ui-button", `ui-button--${variant}`, `ui-button--${size}`, className]
        .filter(Boolean)
        .join(" ")}
      onClick={loading ? undefined : onClick}
    >
      {children}
    </BaseButton>
  );
}
