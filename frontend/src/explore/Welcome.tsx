import { Button as BaseButton } from "@base-ui/react/button";
import { useState } from "react";
import { useI18n } from "../i18n/I18nProvider";
import { Link } from "../router";
import { Icon } from "../ui/Icon";

const STORAGE_KEY = "welcome-dismissed";
const POINTS = ["what", "checked", "numbers"] as const;

function dismissedBefore() {
  try {
    return window.localStorage.getItem(STORAGE_KEY) === "1";
  } catch {
    return false;
  }
}

// First visit on the public screen: the three things a newcomer needs before reading a number,
// and the way to the full explanation. Closing it is remembered on this browser only.
export function Welcome() {
  const { t } = useI18n();
  const [open, setOpen] = useState(() => !dismissedBefore());
  if (!open) return null;
  const close = () => {
    setOpen(false);
    try {
      window.localStorage.setItem(STORAGE_KEY, "1");
    } catch {
      // Private mode or blocked storage: the card simply comes back next time.
    }
  };
  return (
    <section className="welcome" aria-labelledby="welcome-title">
      <div className="welcome__head">
        <h2 id="welcome-title">{t("welcome.title")}</h2>
        <BaseButton className="icon-button welcome__close" aria-label={t("welcome.close")} onClick={close}>
          <Icon name="close" size={18} />
        </BaseButton>
      </div>
      <ul className="welcome__points">
        {POINTS.map((point) => (
          <li key={point}>{t(`welcome.${point}`)}</li>
        ))}
      </ul>
      <Link to="/about" className="welcome__more">
        {t("welcome.more")}
        <Icon name="arrowRight" size={16} />
      </Link>
    </section>
  );
}
