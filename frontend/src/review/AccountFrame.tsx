import type { ReactNode } from "react";
import { useI18n } from "../i18n/I18nProvider";
import { Link } from "../router";
import { MED_LAND, MED_VIEWBOX } from "../shared/medOutline";
import { BrandMark } from "../ui/BrandMark";
import { Icon } from "../ui/Icon";

// The frame of every account screen (sign in, invitation): the sea the team works on, drawn from
// the same coastline as the map, beside a calm card that holds the one thing to do.
export function AccountFrame({ children, titleId }: { children: ReactNode; titleId: string }) {
  const { t } = useI18n();
  return (
    <div className="account">
      <aside className="account__sea">
        <p className="account__brand">
          <BrandMark size={34} />
          <span>
            {t("app.brand")}
            <small>{t("workspace.teamSpace")}</small>
          </span>
        </p>
        <svg className="account__coast" viewBox={MED_VIEWBOX} aria-hidden="true" preserveAspectRatio="xMidYMid slice">
          <path d={MED_LAND} />
          {/* Where the rescues happen, as on the map: a few quiet points off Libya and Tunisia. */}
          <circle className="account__point" cx="7.4" cy="10.9" r="0.16" />
          <circle className="account__point" cx="8.6" cy="10.2" r="0.12" />
          <circle className="account__point" cx="6.6" cy="10.0" r="0.1" />
          <circle className="account__point account__point--live" cx="9.3" cy="11.3" r="0.2" />
        </svg>
        <div className="account__words">
          <p className="account__claim">{t("account.claim")}</p>
          <p className="account__note">{t("account.note")}</p>
        </div>
      </aside>
      <main className="account__side" aria-labelledby={titleId}>
        <div className="account__card">{children}</div>
        <Link to="/" className="account__back">
          <Icon name="map" size={16} />
          {t("account.back")}
        </Link>
      </main>
    </div>
  );
}
