import { api } from "../api/client";
import { LOCALES, type Locale } from "../i18n/format";
import { useI18n } from "../i18n/I18nProvider";
import { Link, useLocation } from "../router";
import { BrandMark } from "../ui/BrandMark";
import { Icon } from "../ui/Icon";
import { SelectField } from "../ui/SelectField";

const LANGUAGE_NAMES: Record<Locale, string> = { en: "English", fr: "Français" };

// The public site's bar: the project's mark and name, the page about the data, the language and the
// door to the team space. Shared by the map screen and the about page.
export function PublicBar() {
  const i18n = useI18n();
  const { t } = i18n;
  const { pathname } = useLocation();
  const me = api.useQuery("get", "/api/private/v1/me/", {}, { retry: false });
  const signedIn = me.data?.permissions.review_identity === true;
  return (
    <header className="explore-bar">
      <Link to="/" className="explore-bar__brand">
        <BrandMark size={30} className="explore-bar__mark" />
        {t("app.brand")}
      </Link>
      <span className="explore-bar__tagline">{t("app.tagline")}</span>
      <div className="explore-bar__actions">
        <Link to="/about" className="explore-bar__link" aria-current={pathname === "/about" ? "page" : undefined}>
          <Icon name="info" size={16} />
          <span className="explore-bar__link-label">{t("about.nav")}</span>
        </Link>
        <SelectField<Locale>
          className="explore-bar__language"
          label={t("app.language")}
          value={i18n.locale}
          options={LOCALES.map((value) => ({ value, label: LANGUAGE_NAMES[value], lang: value }))}
          onValueChange={(value) => value && i18n.setLocale(value)}
        />
        <Link to="/workspace" className="explore-bar__workspace">
          <Icon name="lock" size={16} />
          <span className="explore-bar__workspace-label">{signedIn ? t("preview.workspace") : t("preview.signIn")}</span>
        </Link>
      </div>
    </header>
  );
}
