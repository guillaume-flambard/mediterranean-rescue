import { render } from "@testing-library/react";
import type { ReactElement } from "react";
import type { Locale } from "../i18n/format";
import { I18nProvider } from "../i18n/I18nProvider";

export function renderWithI18n(ui: ReactElement, locale: Locale = "en") {
  return render(<I18nProvider initialLocale={locale}>{ui}</I18nProvider>);
}
