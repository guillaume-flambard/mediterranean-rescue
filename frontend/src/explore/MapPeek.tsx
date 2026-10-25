import { Button as BaseButton } from "@base-ui/react/button";
import { api } from "../api/client";
import { useI18n } from "../i18n/I18nProvider";
import { Icon } from "../ui/Icon";
import { kindName, peopleText } from "./labels";

export interface PeekFacts {
  date: string | null;
  kind: string | null;
  people: number | null;
  port: string | null;
}

/** The facts of a point picked on the map: from the loaded feed when it holds the event, else
 * read once from its record (cached like any other read). */
function usePeekFacts(id: string, preview: boolean, known: PeekFacts | undefined): PeekFacts | undefined {
  const team = api.useQuery("get", "/api/private/v1/preview/events/{id}/", { params: { path: { id } } }, { enabled: preview && !known });
  const visitor = api.useQuery("get", "/api/v1/events/{id}/", { params: { path: { id } } }, { enabled: !preview && !known });
  if (known) return known;
  if (team.data) return { date: team.data.occurred_on, kind: team.data.kind, people: team.data.people, port: team.data.port_label };
  if (visitor.data)
    return { date: visitor.data.occurred_on, kind: visitor.data.kind, people: visitor.data.people, port: visitor.data.port?.name ?? null };
  return undefined;
}

// On a phone, a point tapped on the map is previewed over the map's foot: the reader keeps the
// map and opens the full record only when they choose to (Guillaume, 25 October 2026).
export function MapPeek({
  id,
  preview,
  known,
  onOpen,
  onClose,
}: {
  id: string;
  preview: boolean;
  known: PeekFacts | undefined;
  onOpen: () => void;
  onClose: () => void;
}) {
  const i18n = useI18n();
  const { t } = i18n;
  const facts = usePeekFacts(id, preview, known);
  return (
    <section className="map-peek" aria-label={t("map.peek.label")} aria-live="polite" data-kind={facts?.kind ?? undefined}>
      {facts ? (
        <div className="map-peek__facts">
          <p className="map-peek__date">{facts.date ? i18n.date(facts.date) : t("review.unknown")}</p>
          <p className="map-peek__kind">
            <i className="card__kind-dot" aria-hidden="true" />
            {kindName(i18n, facts.kind)}
          </p>
          <p className="map-peek__line">
            <span>
              <Icon name="people" size={16} />
              {peopleText(i18n, facts.kind, facts.people)}
            </span>
            {facts.port && (
              <span>
                <Icon name="anchor" size={15} />
                {facts.port}
              </span>
            )}
          </p>
        </div>
      ) : (
        <p className="map-peek__facts map-peek__loading">{t("detail.loading")}</p>
      )}
      <div className="map-peek__actions">
        <BaseButton className="pill-button pill-button--primary map-peek__open" onClick={onOpen}>
          {t("map.peek.open")}
          <Icon name="arrowRight" size={16} />
        </BaseButton>
        <BaseButton className="icon-button map-peek__close" aria-label={t("map.peek.close")} onClick={onClose}>
          <Icon name="close" size={18} />
        </BaseButton>
      </div>
    </section>
  );
}
