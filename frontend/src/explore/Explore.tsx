import { Button as BaseButton } from "@base-ui/react/button";
import { lazy, Suspense, useEffect, useRef, useState } from "react";
import { api, type Kind } from "../api/client";
import { kinds } from "../filters";
import { LOCALES, type Locale } from "../i18n/format";
import { useI18n } from "../i18n/I18nProvider";
import { Link, navigate, useLocation, withQuery } from "../router";
import { formatPosition } from "../shared/geo";
import { Icon } from "../ui/Icon";
import { SelectField } from "../ui/SelectField";
import { PreviewBody, PublicBody } from "./EventBody";
import { kindLabel, kindName, peopleText, type Key } from "./labels";
import { Logbook } from "./Logbook";
import { MiniMap } from "./MiniMap";

const EventMap = lazy(async () => ({ default: (await import("../components/Map")).EventMap }));
const PAGE = 25;
const LANGUAGE_NAMES: Record<Locale, string> = { en: "English", fr: "Français" };
// Three ways to read the same events; only the feed is built so far, the others say so.
type View = "feed" | "logbook" | "timeline";
const VIEWS: readonly { value: View; icon: "map" | "calendar" | "anchor"; ready: boolean }[] = [
  { value: "feed", icon: "anchor", ready: true },
  { value: "logbook", icon: "calendar", ready: true },
  { value: "timeline", icon: "map", ready: false },
];
type Status = "to_review" | "blocked" | "linked";

/** One feed entry, from a published event or from a row of the private export. */
interface FeedItem {
  id: string;
  date: string | null;
  kind: string | null;
  people: number | null;
  port: string | null;
  position: { longitude: number; latitude: number } | null;
  title: string | null;
  status: Status | null;
  line: number | null;
  /** Where the record comes from, shown on the closed card: the source, or the export row. */
  origin: string;
}

function useDebounced<T>(value: T, delay: number) {
  const [current, setCurrent] = useState(value);
  useEffect(() => {
    const timer = window.setTimeout(() => setCurrent(value), delay);
    return () => window.clearTimeout(timer);
  }, [value, delay]);
  return current;
}

// The same reading screen for two audiences, never mixed: "public" shows only published events;
// "team" (inside the team space) shows the latest data received, with its review state.
export function Explore({ audience = "public" }: { audience?: "public" | "team" }) {
  const i18n = useI18n();
  const { t } = i18n;
  const me = api.useQuery("get", "/api/private/v1/me/", {}, { retry: false });
  const signedIn = me.data?.permissions.review_identity === true;
  const preview = audience === "team";
  const { pathname, query } = useLocation();
  const requested = VIEWS.find((item) => item.value === query.get("view") && item.ready);
  const view: View = requested?.value ?? "feed";

  const [text, setText] = useState("");
  const q = useDebounced(text.trim(), 300);
  const [kind, setKind] = useState<Kind | "">("");
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [periodOpen, setPeriodOpen] = useState(false);
  const [mapOpen, setMapOpen] = useState(true);
  const [openId, setOpenId] = useState<string | null>(null);
  const [pinnedId, setPinnedId] = useState<string | null>(null);
  // The card under the pointer lights its point; the open card wins over it.
  const [hoverId, setHoverId] = useState<string | null>(null);
  // In the logbook, the entry being read; the map follows it.
  const [readId, setReadId] = useState<string | null>(null);
  const invalid = Boolean(start && end && start > end);
  const filters = {
    ...(start ? { start } : {}),
    ...(end ? { end } : {}),
    ...(kind ? { kind } : {}),
    ...(q ? { q } : {}),
  };

  const page = (all: readonly unknown[], last: { has_next: boolean }) => (last.has_next ? all.length * PAGE : undefined);
  const publicFeed = api.useInfiniteQuery(
    "get",
    "/api/v1/events/",
    { params: { query: { ...filters, limit: PAGE } } },
    { pageParamName: "offset", initialPageParam: 0, getNextPageParam: (last, all) => page(all, last), enabled: !invalid && !preview },
  );
  const previewFeed = api.useInfiniteQuery(
    "get",
    "/api/private/v1/preview/events/",
    { params: { query: { ...filters, limit: PAGE } } },
    { pageParamName: "offset", initialPageParam: 0, getNextPageParam: (last, all) => page(all, last), enabled: !invalid && preview },
  );
  const publicMap = api.useQuery("get", "/api/v1/map-points/", { params: { query: filters } }, { enabled: !invalid && !preview });
  const previewMap = api.useQuery("get", "/api/private/v1/preview/map-points/", { params: { query: filters } }, { enabled: !invalid && preview });

  const feed = preview ? previewFeed : publicFeed;
  const map = preview ? previewMap.data : publicMap.data;
  const items: FeedItem[] = preview
    ? (previewFeed.data?.pages ?? []).flatMap((p) =>
        p.items.map((row) => ({
          id: row.id,
          date: row.occurred_on,
          kind: row.kind,
          people: row.people,
          port: row.port_label,
          position: row.position,
          title: null,
          status: row.status as Status,
          line: row.line,
          origin: t("explore.origin.update", { date: i18n.date(row.exported_at.slice(0, 10)) }),
        })),
      )
    : (publicFeed.data?.pages ?? []).flatMap((p) =>
        p.items.map((event) => ({
          id: event.id,
          date: event.occurred_on,
          kind: event.kind,
          people: event.people,
          port: event.port?.name ?? null,
          position: event.position,
          title: event.title,
          status: null,
          line: null,
          origin: t("explore.origin.source", { source: event.source.name }),
        })),
      );
  const total = preview ? previewFeed.data?.pages[0]?.total_count : publicFeed.data?.pages[0]?.total_count;
  const counts = previewFeed.data?.pages[0]?.counts;
  const trainingData = !preview && publicFeed.data?.pages[0]?.data_mode === "training";
  const points = (map?.points ?? []).map((point) => ({
    id: point.id,
    longitude: point.longitude,
    latitude: point.latitude,
    kind: point.kind as Kind,
  }));
  const followId = view === "logbook" ? readId : null;
  const activeId = openId ?? pinnedId ?? hoverId ?? followId;
  const filtered = Boolean(kind || start || end || q);

  useEffect(() => {
    document.title = t("app.documentTitle");
    document.querySelector('meta[name="description"]')?.setAttribute("content", t("app.metaDescription"));
  }, [t]);

  const resetView = () => {
    setOpenId(null);
    setPinnedId(null);
  };
  const clearFilters = () => {
    setText("");
    setKind("");
    setStart("");
    setEnd("");
    resetView();
  };
  // A point picked on the map opens its card in the feed, or pins it on top when it is not loaded.
  const selectFromMap = (id: string) => {
    setOpenId(id);
    if (items.some((item) => item.id === id)) {
      setPinnedId(null);
      requestAnimationFrame(() => document.getElementById(`event-${id}`)?.scrollIntoView({ behavior: "smooth", block: "nearest" }));
    } else {
      setPinnedId(id);
      requestAnimationFrame(() => document.getElementById("pinned-event")?.scrollIntoView({ behavior: "smooth", block: "nearest" }));
    }
  };

  return (
    <div className={`explore${preview ? " explore--team" : ""}`}>
      {!preview && (
      <header className="explore-bar">
        <a href="/" className="explore-bar__brand">
          {t("app.brand")}
        </a>
        <span className="explore-bar__tagline">{t("app.tagline")}</span>
        <div className="explore-bar__actions">
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
      )}

      <div className="explore-body">
        <section className="explore-feed" aria-labelledby="explore-title">
          <div className="explore-intro">
            <h1 id="explore-title">{t("app.title")}</h1>
            <p>{t("app.lead")}</p>
          </div>

          <div className="composer">
            <div className="views" role="group" aria-label={t("explore.view")}>
              {VIEWS.map((item) => (
                <BaseButton
                  key={item.value}
                  className="views__option"
                  aria-pressed={view === item.value}
                  disabled={!item.ready}
                  onClick={() => navigate(withQuery(pathname, { view: item.value === "feed" ? null : item.value }), { replace: true })}
                >
                  <Icon name={item.icon} size={16} />
                  {t(`explore.view.${item.value}`)}
                  {!item.ready && <span className="views__soon">{t("explore.soon")}</span>}
                </BaseButton>
              ))}
            </div>
            <label className="composer__field">
              <Icon name="search" className="composer__icon" />
              <span className="sr-only">{t("explore.search")}</span>
              <input
                type="search"
                value={text}
                placeholder={t(preview ? "explore.searchPreview" : "explore.searchPublic")}
                onChange={(event) => {
                  setText(event.target.value);
                  resetView();
                }}
                enterKeyHint="search"
              />
              {text && (
                <BaseButton className="composer__clear" aria-label={t("ui.search.clear")} onClick={() => setText("")}>
                  <Icon name="close" size={16} />
                </BaseButton>
              )}
            </label>
            <div className="chips" role="group" aria-label={t("filters.kind")}>
              <BaseButton className="chip" aria-pressed={kind === ""} onClick={() => setKind("")}>
                {t("filters.allKinds")}
              </BaseButton>
              {kinds.map((value) => (
                <BaseButton
                  key={value}
                  className={`chip chip--${value}`}
                  aria-pressed={kind === value}
                  onClick={() => {
                    setKind(kind === value ? "" : value);
                    resetView();
                  }}
                >
                  <i className="chip__dot" aria-hidden="true" />
                  {kindLabel(i18n, value)}
                </BaseButton>
              ))}
              <BaseButton className="chip chip--period" aria-pressed={Boolean(start || end)} aria-expanded={periodOpen} onClick={() => setPeriodOpen(!periodOpen)}>
                <Icon name="calendar" size={15} />
                {start || end ? t("explore.periodSet", { from: start ? i18n.date(start) : "…", to: end ? i18n.date(end) : "…" }) : t("explore.period")}
              </BaseButton>
            </div>
            <div className="composer__period" data-open={periodOpen || undefined}>
              <div className="composer__period-inner">
                <label>
                  {t("filters.from")}
                  <input type="date" value={start} max={end || undefined} onChange={(event) => setStart(event.target.value)} />
                </label>
                <label>
                  {t("filters.to")}
                  <input type="date" value={end} min={start || undefined} onChange={(event) => setEnd(event.target.value)} />
                </label>
              </div>
            </div>
            {invalid && (
              <p role="alert" className="explore-alert">
                <Icon name="alert" size={16} /> {t("filters.invalidRange")}
              </p>
            )}
          </div>

          {preview && (
            <div className="preview-strip">
              {preview && (
                <div className="notice-preview" role="status">
                  <Icon name="lock" size={18} />
                  <div>
                    <strong>{t("preview.banner.title")}</strong> <span className="notice-preview__body">{t("preview.banner.body")}</span>
                    {counts && (
                      <p className="notice-preview__counts">
                        <span className="count count--to_review">{t("explore.toCheck", { count: counts.to_review })}</span>
                        <span className="count count--blocked">{t("explore.blocked", { count: counts.blocked })}</span>
                        <span className="count count--linked">{t("explore.checked", { count: counts.linked })}</span>
                      </p>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}
          {trainingData && (
            <div className="notice-preview" role="status">
              <Icon name="alert" size={18} />
              <div>{t("app.training")}</div>
            </div>
          )}

          <div className="explore-meta">
            <p role="status">
              {feed.isFetching && !feed.isFetchingNextPage
                ? t("filters.refreshing")
                : total !== undefined
                  ? t(preview ? "preview.count" : "events.count", { count: total })
                  : ""}
              {map && total !== undefined ? ` · ${t("explore.onMap", { count: map.located_count })}` : ""}
            </p>
            <div className="explore-meta__actions">
              {filtered && (
                <BaseButton className="link-button" onClick={clearFilters}>
                  {t("filters.reset")}
                </BaseButton>
              )}
              <BaseButton className="link-button explore-meta__map" aria-expanded={mapOpen} onClick={() => setMapOpen(!mapOpen)}>
                <Icon name="map" size={16} />
                {t(mapOpen ? "explore.hideMap" : "explore.showMap")}
              </BaseButton>
            </div>
          </div>

          <div className="explore-map explore-map--inline" data-open={mapOpen || undefined}>
            <MapPanel points={invalid ? [] : points} activeId={activeId} focusId={openId ?? pinnedId} followId={followId} onSelect={selectFromMap} truncated={Boolean(map?.truncated)} />
          </div>

          {pinnedId && !items.some((item) => item.id === pinnedId) && (
            <div id="pinned-event" className="feed feed--pinned">
              <PinnedCard id={pinnedId} preview={preview} onClose={() => setPinnedId(null)} />
            </div>
          )}

          {feed.error ? (
            <div className="explore-state" role="alert">
              <Icon name="alert" size={22} />
              <p>{t("events.loadError")}</p>
              <BaseButton className="pill-button" onClick={() => void feed.refetch()}>
                {t("ui.retry")}
              </BaseButton>
            </div>
          ) : !feed.data && !invalid ? (
            <ol className="feed" aria-busy="true" aria-label={t("events.loading")}>
              {[0, 1, 2].map((index) => (
                <li key={index} className="card card--skeleton" />
              ))}
            </ol>
          ) : items.length === 0 ? (
            <div className="explore-state">
              <Icon name="search" size={22} />
              <h2>{t(filtered ? "explore.noMatch" : preview ? "preview.empty.title" : "events.empty.title")}</h2>
              <p>{t(filtered ? "explore.noMatchBody" : preview ? "preview.empty.body" : "events.empty.body")}</p>
              {filtered && (
                <BaseButton className="pill-button" onClick={clearFilters}>
                  {t("filters.reset")}
                </BaseButton>
              )}
            </div>
          ) : view === "logbook" ? (
            <Logbook
              items={items}
              preview={preview}
              openId={openId}
              hasMore={Boolean(feed.hasNextPage)}
              onToggle={(id) => {
                setPinnedId(null);
                setOpenId(openId === id ? null : id);
              }}
              onRead={setReadId}
            />
          ) : (
            <ol className="feed" aria-label={t(preview ? "preview.heading" : "events.heading")}>
              {items.map((item) => (
                <EventCard
                  key={item.id}
                  item={item}
                  preview={preview}
                  open={openId === item.id}
                  onHover={(hovered) => setHoverId(hovered ? item.id : null)}
                  onToggle={() => {
                    setPinnedId(null);
                    setOpenId(openId === item.id ? null : item.id);
                  }}
                />
              ))}
            </ol>
          )}
          {feed.hasNextPage && (
            <BaseButton className="pill-button feed-more" disabled={feed.isFetchingNextPage} onClick={() => void feed.fetchNextPage()}>
              {feed.isFetchingNextPage ? t("events.loading") : t("explore.more")}
            </BaseButton>
          )}

          <footer className="explore-footer">
            <p>{t("app.footer.counts")}</p>
            <p>{t("app.context")}</p>
            <a href="https://map.sosmediterranee.org/" target="_blank" rel="noreferrer">
              {t("app.footer.sosMap")}
            </a>
          </footer>
        </section>

        <aside className="explore-map explore-map--side" aria-label={t("map.label")}>
          <MapPanel points={invalid ? [] : points} activeId={activeId} focusId={openId ?? pinnedId} followId={followId} onSelect={selectFromMap} truncated={Boolean(map?.truncated)} />
        </aside>
      </div>
    </div>
  );
}

function MapPanel({
  points,
  activeId,
  focusId,
  followId,
  onSelect,
  truncated,
}: {
  points: { id: string; longitude: number; latitude: number; kind: Kind }[];
  activeId: string | null;
  focusId: string | null;
  followId: string | null;
  onSelect: (id: string) => void;
  truncated: boolean;
}) {
  const { t } = useI18n();
  return (
    <div className="map-card">
      <Suspense fallback={<div className="map-card__loading">{t("map.loading")}</div>}>
        <EventMap points={points} onSelect={onSelect} activeId={activeId} focusId={focusId} followId={followId} />
      </Suspense>
      {truncated && <p className="map-card__note">{t("map.truncated")}</p>}
    </div>
  );
}

// Short labels for the card badge; the full sentence stays in the opened record.
function statusKey(status: Status): Key {
  return `explore.status.${status}` as Key;
}

function EventCard({
  item,
  preview,
  open,
  onToggle,
  onHover,
}: {
  item: FeedItem;
  preview: boolean;
  open: boolean;
  onToggle: () => void;
  onHover: (hovered: boolean) => void;
}) {
  const i18n = useI18n();
  const { t } = i18n;
  const ref = useRef<HTMLLIElement>(null);
  const bodyId = `event-${item.id}-body`;
  return (
    <li
      id={`event-${item.id}`}
      ref={ref}
      className={`card${open ? " card--open" : ""}`}
      data-kind={item.kind ?? undefined}
      onPointerEnter={(event) => event.pointerType === "mouse" && onHover(true)}
      onPointerLeave={(event) => event.pointerType === "mouse" && onHover(false)}
    >
      <BaseButton className="card__summary" aria-expanded={open} aria-controls={bodyId} onClick={onToggle}>
        <span className="card__text">
          <span className="card__top">
            <span className="card__date">{item.date ? i18n.date(item.date) : t("review.unknown")}</span>
            {item.status && (
              <span className={`status status--${item.status}`}>
                <i aria-hidden="true" />
                {t(statusKey(item.status))}
              </span>
            )}
          </span>
          <span className="card__kind">
            <i className="card__kind-dot" aria-hidden="true" />
            {item.title ?? kindName(i18n, item.kind)}
          </span>
          <span className="card__facts">
            <span className="card__people">
              <Icon name="people" size={17} />
              {peopleText(i18n, item.kind, item.people)}
            </span>
            {item.port && (
              <span className="card__port">
                <Icon name="anchor" size={16} />
                {item.port}
              </span>
            )}
          </span>
          <span className="card__origin">{item.origin}</span>
        </span>
        <span className="card__locator">
          <MiniMap
            position={item.position}
            label={item.position ? formatPosition(i18n, item.position.latitude, item.position.longitude) : t("detail.unknownPosition")}
          />
        </span>
        <Icon name="chevronDown" className="card__chevron" />
      </BaseButton>
      <div id={bodyId} className="card__body" role="region" aria-label={t("detail.title")} hidden={!open}>
        {open && (preview ? <PreviewBody id={item.id} /> : <PublicBody id={item.id} />)}
      </div>
    </li>
  );
}

function PinnedCard({ id, preview, onClose }: { id: string; preview: boolean; onClose: () => void }) {
  const { t } = useI18n();
  return (
    <div className="card card--open card--pinned">
      <div className="card__pinned-head">
        <span>
          <Icon name="pin" size={16} /> {t("explore.fromMap")}
        </span>
        <BaseButton className="icon-button" aria-label={t("ui.close")} onClick={onClose}>
          <Icon name="close" size={18} />
        </BaseButton>
      </div>
      <div className="card__body">{preview ? <PreviewBody id={id} /> : <PublicBody id={id} />}</div>
    </div>
  );
}
