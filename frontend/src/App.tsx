import { Button as BaseButton } from "@base-ui/react/button";
import { lazy, Suspense, useEffect, useState } from "react";
import { api, type Kind } from "./api/client";
import { PreviewDetail, previewStatus, type PreviewStatus } from "./preview/PreviewDetail";
import { Link } from "./router";
import { StatusLabel } from "./ui/Feedback";
import { kinds, makeFilter } from "./filters";
import { LOCALES, type Locale } from "./i18n/format";
import { useI18n } from "./i18n/I18nProvider";
import { formatPosition } from "./shared/geo";
import { Button } from "./ui/Button";
import { Dialog } from "./ui/Dialog";
import { Pagination } from "./ui/Pagination";
import { SelectField } from "./ui/SelectField";

const EventMap = lazy(async () => ({ default: (await import("./components/Map")).EventMap }));
const PAGE = 25;
type Mode = "preview" | "public";
// Each language is named in its own language, as language pickers usually do.
const LANGUAGE_NAMES: Record<Locale, string> = { en: "English", fr: "Français" };

function useKindLabel() {
  const { t } = useI18n();
  return (kind: Kind) => {
    const key = `kind.${kind}` as const;
    const label = t(key);
    // A category the catalog does not know yet shows its source value.
    return label === key ? kind : label;
  };
}

function Detail({ id }: { id: string }) {
  const i18n = useI18n();
  const { t } = i18n;
  const { data: event, isPending, error, refetch } = api.useQuery("get", "/api/v1/events/{id}/", {
    params: { path: { id } },
  });
  const [evidenceOffset, setEvidenceOffset] = useState(0);
  const evidence = api.useQuery("get", "/api/v1/events/{id}/evidence/", {
    params: { path: { id }, query: { limit: PAGE, offset: evidenceOffset } },
  });
  const kindLabel = useKindLabel();
  if (isPending && !event) return <p role="status">{t("detail.loading")}</p>;
  if (error)
    return (
      <div role="alert">
        <p>{t("detail.loadError")}</p>
        <Button onClick={() => void refetch()}>{t("ui.retry")}</Button>
      </div>
    );
  if (!event) return <p>{t("detail.unavailable")}</p>;
  const position = event.position;
  return (
    <>
      <div className="detail-date">
        {i18n.date(event.occurred_on)} · {kindLabel(event.kind)}
      </div>
      <h2>{event.title}</h2>
      {event.source.synthetic && <p className="training">{t("detail.trainingData")}</p>}
      <p>{event.summary || t("detail.noSummary")}</p>
      <dl>
        <div>
          <dt>{t("detail.people")}</dt>
          <dd>{event.people === null ? t("detail.unknownCount") : i18n.number(event.people)}</dd>
        </div>
        <div>
          <dt>{t("detail.vessel")}</dt>
          <dd>{event.vessel?.name ?? t("detail.notProvided")}</dd>
        </div>
        <div>
          <dt>{t("detail.voyage")}</dt>
          <dd>{event.voyage?.title ?? t("detail.notProvided")}</dd>
        </div>
        <div>
          <dt>{t("detail.port")}</dt>
          <dd>{event.port?.name ?? t("detail.notProvided")}</dd>
        </div>
        <div>
          <dt>{t("detail.position")}</dt>
          <dd>
            {position
              ? `${formatPosition(i18n, position.latitude, position.longitude)} (${t(
                  position.precision === "approximate" ? "detail.precision.approximate" : "detail.precision.reported",
                )})`
              : t("detail.unknownPosition")}
          </dd>
        </div>
      </dl>
      <h3>{t("detail.sources")}</h3>
      <p>
        <a href={event.source_url} target="_blank" rel="noreferrer">
          {t("detail.sourceLink")}
        </a>
      </p>
      <p>{event.source.name}</p>
      <p className="muted">{event.source.license_note}</p>
      {(evidence.data?.items ?? []).map((item) => (
        <p key={item.url}>
          <a href={item.url} target="_blank" rel="noreferrer">
            {item.label} ↗
          </a>
        </p>
      ))}
      {evidence.error && (
        <p role="alert">
          {t("detail.evidenceError")} <Button onClick={() => void evidence.refetch()}>{t("ui.retry")}</Button>
        </p>
      )}
      {evidence.isPending && <p role="status">{t("detail.evidenceLoading")}</p>}
      <div className="pagination">
        <Button
          disabled={evidenceOffset === 0 || evidence.isFetching}
          onClick={() => setEvidenceOffset(Math.max(0, evidenceOffset - PAGE))}
        >
          {t("detail.evidencePrevious")}
        </Button>
        <Button
          disabled={!evidence.data?.has_next || evidence.isFetching}
          onClick={() => setEvidenceOffset(evidenceOffset + PAGE)}
        >
          {t("detail.evidenceNext")}
        </Button>
      </div>
      <p className="muted">{t("detail.countsNote")}</p>
    </>
  );
}

export default function App() {
  const i18n = useI18n();
  const { t } = i18n;
  const kindLabel = useKindLabel();
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [kind, setKind] = useState<Kind | "">("");
  const [offset, setOffset] = useState(0);
  const [selected, setSelected] = useState<string | null>(null);
  const invalid = Boolean(start && end && start > end);
  const filters = makeFilter(start, end, kind);
  // Signed-in reviewers see the latest private export on this screen; everyone else sees only
  // published events. The preview is never published and never cached by the browser.
  const me = api.useQuery("get", "/api/private/v1/me/", {}, { retry: false });
  const canPreview = me.data?.permissions.review_identity === true;
  const [modeChoice, setModeChoice] = useState<Mode | null>(null);
  const mode: Mode = canPreview ? (modeChoice ?? "preview") : "public";
  const preview = mode === "preview";
  const eventsQuery = api.useQuery(
    "get",
    "/api/v1/events/",
    { params: { query: { ...filters, limit: PAGE, offset } } },
    { enabled: !invalid && !preview },
  );
  const mapQuery = api.useQuery("get", "/api/v1/map-points/", { params: { query: filters } }, { enabled: !invalid && !preview });
  const previewEvents = api.useQuery(
    "get",
    "/api/private/v1/preview/events/",
    { params: { query: { ...filters, limit: PAGE, offset } } },
    { enabled: !invalid && preview },
  );
  const previewMap = api.useQuery(
    "get",
    "/api/private/v1/preview/map-points/",
    { params: { query: filters } },
    { enabled: !invalid && preview },
  );
  const fetching = preview ? previewEvents.isFetching || previewMap.isFetching : eventsQuery.isFetching || mapQuery.isFetching;
  const error = preview ? previewEvents.error || previewMap.error : eventsQuery.error || mapQuery.error;
  const page = eventsQuery.data;
  const total = preview ? previewEvents.data?.total_count : page?.total_count;
  const map = preview ? previewMap.data : mapQuery.data;
  const points = (map?.points ?? []).map((point) => ({ id: point.id, longitude: point.longitude, latitude: point.latitude, kind: point.kind as Kind }));
  const retry = () => {
    if (preview) {
      void previewEvents.refetch();
      void previewMap.refetch();
    } else {
      void eventsQuery.refetch();
      void mapQuery.refetch();
    }
  };
  useEffect(() => {
    document.title = t("app.documentTitle");
    document.querySelector('meta[name="description"]')?.setAttribute("content", t("app.metaDescription"));
  }, [t]);
  const reset = () => {
    setStart("");
    setEnd("");
    setKind("");
    setOffset(0);
  };

  return (
    <>
      <header className="header">
        <a href="/" className="brand">
          {t("app.brand")}
        </a>
        <span>{t("app.tagline")}</span>
        <SelectField<Locale>
          className="language"
          label={t("app.language")}
          value={i18n.locale}
          options={LOCALES.map((value) => ({ value, label: LANGUAGE_NAMES[value], lang: value }))}
          onValueChange={(value) => value && i18n.setLocale(value)}
        />
        <a href="https://sosmediterranee.fr/" target="_blank" rel="noreferrer">
          {t("app.sosLink")}
        </a>
        <Link to="/workspace" className="workspace-link">
          {canPreview ? t("preview.workspace") : t("preview.signIn")}
        </Link>
      </header>
      <main>
        <section className="intro">
          <div>
            <h1>{t("app.title")}</h1>
            <p>{t("app.lead")}</p>
          </div>
          <span className="phase">{t("app.phase")}</span>
        </section>
        <p className="context">{t("app.context")}</p>
        {canPreview && (
          <div className="preview-bar" role="group" aria-label={t("preview.modeLabel")}>
            {(["preview", "public"] as const).map((value) => (
              <Button
                key={value}
                size="sm"
                variant={mode === value ? "primary" : "secondary"}
                aria-pressed={mode === value}
                onClick={() => {
                  setModeChoice(value);
                  setOffset(0);
                  setSelected(null);
                }}
              >
                {t(`preview.mode.${value}`)}
              </Button>
            ))}
          </div>
        )}
        {preview && (
          <div className="preview-banner" role="status">
            <strong>{t("preview.banner.title")}</strong>{" "}
            {t("preview.banner.body")}
            {previewEvents.data && (
              <span className="preview-banner__counts">
                {" "}
                {t("preview.banner.counts", {
                  toReview: previewEvents.data.counts.to_review,
                  blocked: previewEvents.data.counts.blocked,
                  linked: previewEvents.data.counts.linked,
                })}
              </span>
            )}
          </div>
        )}
        {page?.data_mode === "training" && (
          <div className="training" role="status">
            {t("app.training")}
          </div>
        )}
        <form className="filters" onSubmit={(e) => e.preventDefault()}>
          <label>
            {t("filters.from")}
            <input
              type="date"
              value={start}
              onChange={(e) => {
                setStart(e.target.value);
                setOffset(0);
              }}
            />
          </label>
          <label>
            {t("filters.to")}
            <input
              type="date"
              value={end}
              onChange={(e) => {
                setEnd(e.target.value);
                setOffset(0);
              }}
            />
          </label>
          <SelectField<Kind>
            label={t("filters.kind")}
            value={kind}
            emptyLabel={t("filters.allKinds")}
            options={kinds.map((value) => ({ value, label: kindLabel(value) }))}
            onValueChange={(value) => {
              setKind(value);
              setOffset(0);
            }}
          />
          <Button onClick={reset}>{t("filters.reset")}</Button>
          <span className="result-count" role="status">
            {fetching ? t("filters.refreshing") : total !== undefined ? t("events.count", { count: total }) : ""}
          </span>
        </form>
        {invalid && (
          <p role="alert" className="error">
            {t("filters.invalidRange")}
          </p>
        )}
        {error && (
          <div className="error" role="alert">
            <p>{t("events.loadError")}</p>
            <Button onClick={retry}>{t("ui.retry")}</Button>
          </div>
        )}
        <div className="workspace" aria-busy={fetching}>
          <section className="map-panel">
            <Suspense
              fallback={
                <div className="map empty" role="status">
                  {t("map.loading")}
                </div>
              }
            >
              <EventMap points={invalid ? [] : points} onSelect={setSelected} />
            </Suspense>
            <div className="map-footer">
              <span>
                <i /> {t(preview ? "preview.legend" : "map.legend")}
              </span>
              <span>{t("map.located", { count: map?.located_count ?? 0 })}</span>
            </div>
            {map?.truncated && <p className="notice">{t("map.truncated")}</p>}
          </section>
          <section className="journal" aria-labelledby="journal-title">
            <div className="journal-head">
              <h2 id="journal-title">{t(preview ? "preview.heading" : "events.heading")}</h2>
              <span>{i18n.number(total ?? 0)}</span>
            </div>
            {preview ? (
              !previewEvents.data ? (
                <p className="empty" role="status">
                  {invalid ? t("filters.fixRange") : t("events.loading")}
                </p>
              ) : previewEvents.data.total_count === 0 ? (
                <div className="empty">
                  <h3>{t("preview.empty.title")}</h3>
                  <p>{t("preview.empty.body")}</p>
                </div>
              ) : (
                <ul className="events">
                  {previewEvents.data.items.map((item) => (
                    <li key={item.id}>
                      <BaseButton className="event" onClick={() => setSelected(item.id)}>
                        <span className="event-date">{item.occurred_on ? i18n.date(item.occurred_on) : t("review.unknown")}</span>
                        <strong>
                          {item.kind ? kindLabel(item.kind as Kind) : t("review.unknown")}
                          {item.port_label ? ` · ${item.port_label}` : ""}
                        </strong>
                        <span className="muted">{t("preview.item.line", { sheet: item.sheet, line: item.line })}</span>
                        <span className="preview-item-meta">
                          {item.people === null ? t("events.peopleUnknown") : t("events.people", { count: item.people })}{" "}
                          <StatusLabel status={previewStatus(item.status as PreviewStatus)} />
                        </span>
                      </BaseButton>
                    </li>
                  ))}
                </ul>
              )
            ) : !page && fetching ? (
              <p className="empty" role="status">
                {t("events.loading")}
              </p>
            ) : !invalid && page && page.total_count === 0 ? (
              <div className="empty">
                <h3>{t("events.empty.title")}</h3>
                <p>{t("events.empty.body")}</p>
                <p>{t("events.empty.hint")}</p>
              </div>
            ) : invalid ? (
              <p className="empty">{t("filters.fixRange")}</p>
            ) : (
              <ul className="events">
                {page?.items.map((event) => (
                  <li key={event.id}>
                    {/* Legacy list row, styled by styles.css until the public screen is rebuilt (UI4). */}
                    <BaseButton className="event" onClick={() => setSelected(event.id)}>
                      <span className="event-date">{i18n.date(event.occurred_on)}</span>
                      <strong>{event.title}</strong>
                      <span className="muted">
                        {kindLabel(event.kind)}
                        {event.vessel ? ` · ${event.vessel.name}` : ""}
                      </span>
                      <span>
                        {event.people === null ? t("events.peopleUnknown") : t("events.people", { count: event.people })}
                      </span>
                    </BaseButton>
                  </li>
                ))}
              </ul>
            )}
            <Pagination
              className="pagination"
              offset={offset}
              limit={PAGE}
              total={total ?? 0}
              hasNext={Boolean(preview ? previewEvents.data?.has_next : page?.has_next)}
              disabled={fetching || invalid}
              onOffsetChange={setOffset}
            />
          </section>
        </div>
        <footer>
          <p>{t("app.footer.counts")}</p>
          <a href="https://map.sosmediterranee.org/" target="_blank" rel="noreferrer">
            {t("app.footer.sosMap")}
          </a>
        </footer>
      </main>
      <Dialog
        className="dialog"
        title={t("detail.title")}
        hideTitle
        open={selected !== null}
        onOpenChange={(open) => {
          if (!open) setSelected(null);
        }}
      >
        {selected && (preview ? <PreviewDetail key={selected} id={selected} kindLabel={kindLabel} /> : <Detail key={selected} id={selected} />)}
      </Dialog>
    </>
  );
}
