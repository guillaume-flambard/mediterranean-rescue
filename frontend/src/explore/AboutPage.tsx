import { useEffect } from "react";
import { kinds } from "../filters";
import { useI18n } from "../i18n/I18nProvider";
import type { Key } from "./labels";
import { Link } from "../router";
import { Icon } from "../ui/Icon";
import { PublicBar } from "./PublicBar";

const KNOW = ["checked", "notUnique", "unknown", "approximate", "scope"] as const;
const STEPS = ["recorded", "read", "checked", "published"] as const;
const WORDS = ["survivors", "approximate", "notKnown"] as const;

// "About the data": what a first-time visitor needs before trusting a number, on one page, in
// the order they ask: what is this, what should I know, how do I read it, where does it come from.
export function AboutPage() {
  const { t } = useI18n();
  useEffect(() => {
    document.title = `${t("about.title")} · ${t("app.documentTitle")}`;
  }, [t]);
  return (
    <div className="explore about">
      <PublicBar />
      <main className="about__body">
        <header className="about__hero">
          <p className="about__eyebrow">{t("about.eyebrow")}</p>
          <h1>{t("about.title")}</h1>
          <p className="about__lead">{t("about.lead")}</p>
          <p className="about__independent">
            <Icon name="info" size={18} />
            <span>
              {t("about.independent")}{" "}
              <a href="https://www.sosmediterranee.org/" target="_blank" rel="noreferrer">
                {t("about.sosSite")}
              </a>
            </span>
          </p>
          <Link to="/" className="pill-button pill-button--primary about__cta">
            <Icon name="map" size={18} />
            {t("about.toMap")}
          </Link>
        </header>

        <section className="about__card" aria-labelledby="about-know">
          <h2 id="about-know">{t("about.know.title")}</h2>
          <ul className="about__know">
            {KNOW.map((key) => (
              <li key={key}>
                <Icon name="check" size={18} />
                <span>
                  <b>{t(`about.know.${key}.title` as Key)}</b> {t(`about.know.${key}.body` as Key)}
                </span>
              </li>
            ))}
          </ul>
        </section>

        <section className="about__card" aria-labelledby="about-read">
          <h2 id="about-read">{t("about.read.title")}</h2>
          <ol className="about__read">
            <li>
              <span className="about__legend-point" aria-hidden="true" />
              <span>{t("about.read.point")}</span>
            </li>
            <li>
              <span className="about__legend-group" aria-hidden="true">
                12
              </span>
              <span>{t("about.read.group")}</span>
            </li>
            <li>
              <span className="about__legend-open" aria-hidden="true" />
              <span>{t("about.read.open")}</span>
            </li>
          </ol>
          <p className="about__views">{t("about.read.views")}</p>
        </section>

        <section className="about__card" aria-labelledby="about-words">
          <h2 id="about-words">{t("about.words.title")}</h2>
          <p className="about__note">{t("about.words.note")}</p>
          <dl className="about__words">
            {kinds.map((kind) => (
              <div key={kind} className={`about__word chip--${kind}`}>
                <dt>
                  <i className="chip__dot" aria-hidden="true" />
                  {t(`kindOne.${kind}` as Key)}
                </dt>
                <dd>{t(`about.kind.${kind}` as Key)}</dd>
              </div>
            ))}
            {WORDS.map((word) => (
              <div key={word} className="about__word">
                <dt>{t(`about.word.${word}.term` as Key)}</dt>
                <dd>{t(`about.word.${word}.body` as Key)}</dd>
              </div>
            ))}
          </dl>
        </section>

        <section className="about__card" aria-labelledby="about-path">
          <h2 id="about-path">{t("about.path.title")}</h2>
          <ol className="about__steps">
            {STEPS.map((step, index) => (
              <li key={step}>
                <span className="about__step-number">{index + 1}</span>
                <span>
                  <b>{t(`about.path.${step}.title` as Key)}</b>
                  <span>{t(`about.path.${step}.body` as Key)}</span>
                </span>
              </li>
            ))}
          </ol>
        </section>

        <section className="about__card about__card--quiet" aria-labelledby="about-dignity">
          <h2 id="about-dignity">{t("about.dignity.title")}</h2>
          <p>{t("about.dignity.body")}</p>
        </section>

        <section className="about__card" aria-labelledby="about-cite">
          <h2 id="about-cite">{t("about.cite.title")}</h2>
          <p>{t("about.cite.body")}</p>
          <h3>{t("about.more.title")}</h3>
          <ul className="about__links">
            <li>
              <a href="https://map.sosmediterranee.org/" target="_blank" rel="noreferrer">
                {t("about.more.sosMap")}
              </a>
            </li>
            <li>
              <a href="https://missingmigrants.iom.int/data" target="_blank" rel="noreferrer">
                {t("about.more.iom")}
              </a>
            </li>
            <li>
              <a href="https://www.sosmediterranee.org/faq/" target="_blank" rel="noreferrer">
                {t("about.more.faq")}
              </a>
            </li>
          </ul>
        </section>
      </main>
    </div>
  );
}
