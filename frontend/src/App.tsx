import { useState, lazy, Suspense } from "react";
import { Button } from "@base-ui/react/button";
import { Select } from "@base-ui/react/select";
import { Dialog } from "@base-ui/react/dialog";
import { api, type Kind } from "./api/client";
import { dateLabel, kinds, kindLabel, makeFilter } from "./filters";
const EventMap = lazy(async () => ({
  default: (await import("./components/Map")).EventMap,
}));

function Detail({ id }: { id: string }) {
  const { data: event, isPending: fetching, error, refetch: retry } = api.useQuery("get", "/api/v1/events/{id}/", { params: { path: { id } } });
  const [evidenceOffset, setEvidenceOffset] = useState(0);
  const evidence = api.useQuery("get", "/api/v1/events/{id}/evidence/", { params: { path: { id }, query: { limit: 25, offset: evidenceOffset } } });
  if (fetching && !event) return <p role="status">Chargement de la fiche…</p>;
  if (error)
    return (
      <div role="alert">
        <p>La fiche n’a pas pu être chargée.</p>
        <Button onClick={() => retry()}>
          Réessayer
        </Button>
      </div>
    );
  if (!event)
    return <p>Cet événement n’est pas disponible à la publication.</p>;
  return (
    <>
      <div className="detail-date">
        {dateLabel(event.occurred_on)} · {kindLabel(event.kind)}
      </div>
      <h2>{event.title}</h2>
      {event.source.synthetic && (
        <p className="training">Données d’entraînement fictives</p>
      )}
      <p>{event.summary || "Aucune description publiée."}</p>
      <dl>
        <div>
          <dt>Effectif déclaré</dt>
          <dd>{event.people ?? "Inconnu"}</dd>
        </div>
        <div>
          <dt>Navire</dt>
          <dd>{event.vessel?.name ?? "Non renseigné"}</dd>
        </div>
        <div>
          <dt>Voyage</dt>
          <dd>{event.voyage?.title ?? "Non renseigné"}</dd>
        </div>
        <div>
          <dt>Port de débarquement</dt>
          <dd>{event.port?.name ?? "Non renseigné"}</dd>
        </div>
        <div>
          <dt>Position</dt>
          <dd>
            {event.position
              ? `${event.position.latitude.toFixed(3)}° N, ${event.position.longitude.toFixed(3)}° E (${event.position.precision === "approximate" ? "approximative" : "rapportée"})`
              : "Inconnue"}
          </dd>
        </div>
      </dl>
      <h3>Sources et provenance</h3>
      <p>
        <a href={event.source_url} target="_blank" rel="noreferrer">
          Consulter la source de l’événement ↗
        </a>
      </p>
      <p>{event.source.name}</p>
      <p className="muted">{event.source.license_note}</p>
      {(evidence.data?.items ?? []).map((e) => (
        <p key={e.url}>
          <a href={e.url} target="_blank" rel="noreferrer">
            {e.label} ↗
          </a>
        </p>
      ))}
      {evidence.error && <p role="alert">Les liens supplémentaires n’ont pas pu être chargés. <Button onClick={() => evidence.refetch()}>Réessayer</Button></p>}
      {evidence.isPending && <p role="status">Chargement des liens…</p>}
      <div className="pagination">
        <Button disabled={evidenceOffset === 0 || evidence.isFetching} onClick={() => setEvidenceOffset(Math.max(0, evidenceOffset - 25))}>Liens précédents</Button>
        <Button disabled={!evidence.data?.has_next || evidence.isFetching} onClick={() => setEvidenceOffset(evidenceOffset + 25)}>Liens suivants</Button>
      </div>
      <p className="muted">
        Un effectif inconnu reste inconnu. Les événements peuvent concerner
        plusieurs fois les mêmes personnes.
      </p>
    </>
  );
}
export default function App() {
  const [start, setStart] = useState(""),
    [end, setEnd] = useState(""),
    [kind, setKind] = useState<Kind | "">(""),
    [offset, setOffset] = useState(0),
    [selected, setSelected] = useState<string | null>(null);
  const invalid = Boolean(start && end && start > end);
  const filters = makeFilter(start, end, kind);
  const eventsQuery = api.useQuery("get", "/api/v1/events/", { params: { query: { ...filters, limit: 25, offset } } }, { enabled: !invalid });
  const mapQuery = api.useQuery("get", "/api/v1/map-points/", { params: { query: filters } }, { enabled: !invalid });
  const fetching = eventsQuery.isFetching || mapQuery.isFetching;
  const error = eventsQuery.error || mapQuery.error;
  const retry = () => { void eventsQuery.refetch(); void mapQuery.refetch(); };
  const data = eventsQuery.data;
  const update = () => setOffset(0),
    reset = () => {
      setStart("");
      setEnd("");
      setKind("");
      setOffset(0);
    };
  const page = data;
  return (
    <>
      <header className="header">
        <a href="/" className="brand">
          Mediterranée Rescue
        </a>
        <span>Les actions en mer, documentées.</span>
        <a href="https://sosmediterranee.fr/" target="_blank" rel="noreferrer">
          SOS MEDITERRANEE ↗
        </a>
      </header>
      <main>
        <section className="intro">
          <div>
            <h1>Explorer les actions en Méditerranée</h1>
            <p>
              Une carte, des événements et les sources qui permettent de les
              comprendre.
            </p>
          </div>
          <span className="phase">Projet en construction</span>
        </section>
        <p className="context">
          Interface indépendante en cours de développement. Le périmètre et la
          publication des données seront validés avec les associations.
        </p>
        {data?.data_mode === "training" && (
          <div className="training" role="status">
            Mode entraînement : tous les événements et effectifs affichés sont
            fictifs.
          </div>
        )}
        <form className="filters" onSubmit={(e) => e.preventDefault()}>
          <label>
            Du
            <input
              type="date"
              value={start}
              onChange={(e) => {
                setStart(e.target.value);
                update();
              }}
            />
          </label>
          <label>
            Au
            <input
              type="date"
              value={end}
              onChange={(e) => {
                setEnd(e.target.value);
                update();
              }}
            />
          </label>
          <div className="field">
            <label id="kind-label">Type d’événement</label>
            <Select.Root
              value={kind}
              onValueChange={(value) => {
                setKind(value ?? "");
                update();
              }}
            >
              <Select.Trigger
                className="select-trigger"
                aria-labelledby="kind-label"
              >
                <Select.Value>{kind ? kindLabel(kind) : "Tous les événements"}</Select.Value>
                <Select.Icon>⌄</Select.Icon>
              </Select.Trigger>
              <Select.Portal>
                <Select.Positioner sideOffset={6}>
                  <Select.Popup className="select-popup">
                    <Select.List>
                      <Select.Item value="" className="select-item">
                        <Select.ItemText>Tous les événements</Select.ItemText>
                      </Select.Item>
                      {kinds.map((k) => (
                        <Select.Item
                          key={k.value}
                          value={k.value}
                          className="select-item"
                        >
                          <Select.ItemText>{k.label}</Select.ItemText>
                          <Select.ItemIndicator>✓</Select.ItemIndicator>
                        </Select.Item>
                      ))}
                    </Select.List>
                  </Select.Popup>
                </Select.Positioner>
              </Select.Portal>
            </Select.Root>
          </div>
          <Button onClick={reset}>Réinitialiser</Button>
          <span className="result-count" role="status">
            {fetching
              ? "Actualisation…"
              : page
                ? `${page.total_count} événements`
                : ""}
          </span>
        </form>
        {invalid && (
          <p role="alert" className="error">
            La date de début doit précéder la date de fin.
          </p>
        )}
        {error && (
          <div className="error" role="alert">
            <p>
              La connexion aux données a échoué. Les résultats précédents
              peuvent être périmés.
            </p>
            <Button onClick={() => retry()}>
              Réessayer
            </Button>
          </div>
        )}
        <div className="workspace" aria-busy={fetching}>
          <section className="map-panel">
            <Suspense
              fallback={
                <div className="map empty" role="status">
                  Chargement de la carte…
                </div>
              }
            >
              <EventMap
                points={invalid ? [] : (mapQuery.data?.points ?? [])}
                onSelect={setSelected}
              />
            </Suspense>
            <div className="map-footer">
              <span>
                <i /> Événement publié • points regroupés à faible zoom
              </span>
              <span>
                {mapQuery.data?.located_count ?? 0} événements localisés
              </span>
            </div>
            {mapQuery.data?.truncated && (
              <p className="notice">
                Les 2 000 premiers points sont affichés. Affinez la période pour
                explorer le reste.
              </p>
            )}
          </section>
          <section className="journal" aria-labelledby="journal-title">
            <div className="journal-head">
              <h2 id="journal-title">Événements</h2>
              <span>{page?.total_count ?? 0}</span>
            </div>
            {!data && fetching ? (
              <p className="empty" role="status">
                Chargement des événements…
              </p>
            ) : !invalid && page && page.total_count === 0 ? (
              <div className="empty">
                <h3>Aucun événement publié</h3>
                <p>
                  Les données apparaîtront ici après import, contrôle et
                  validation de leur publication.
                </p>
                <p>Vous pouvez aussi élargir les filtres.</p>
              </div>
            ) : invalid ? (
              <p className="empty">
                Corrigez la période pour consulter les événements.
              </p>
            ) : (
              <ul className="events">
                {page?.items.map((event) => (
                  <li key={event.id}>
                    <Button
                      className="event"
                      onClick={() => setSelected(event.id)}
                    >
                      <span className="event-date">
                        {dateLabel(event.occurred_on)}
                      </span>
                      <strong>{event.title}</strong>
                      <span className="muted">
                        {kindLabel(event.kind)}
                        {event.vessel ? ` · ${event.vessel.name}` : ""}
                      </span>
                      <span>
                        {event.people === null
                          ? "Effectif inconnu"
                          : `${event.people} personnes déclarées`}
                      </span>
                    </Button>
                  </li>
                ))}
              </ul>
            )}
            <div className="pagination">
              <Button
                disabled={offset === 0 || fetching || invalid}
                onClick={() => setOffset(Math.max(0, offset - 25))}
              >
                Précédent
              </Button>
              <span>
                {page?.total_count
                  ? `${offset + 1} à ${Math.min(offset + 25, page.total_count)}`
                  : "0 résultat"}
              </span>
              <Button
                disabled={!page?.has_next || fetching || invalid}
                onClick={() => setOffset(offset + 25)}
              >
                Suivant
              </Button>
            </div>
          </section>
        </div>
        <footer>
          <p>
            Les effectifs décrivent des événements. Ils ne constituent pas un
            décompte de personnes uniques.
          </p>
          <a
            href="https://map.sosmediterranee.org/"
            target="_blank"
            rel="noreferrer"
          >
            Consulter la carte SOS MEDITERRANEE existante ↗
          </a>
        </footer>
      </main>
      <Dialog.Root
        open={selected !== null}
        onOpenChange={(open) => {
          if (!open) setSelected(null);
        }}
      >
        <Dialog.Portal>
          <Dialog.Backdrop className="backdrop" />
          <Dialog.Popup className="dialog">
            <Dialog.Title className="sr-only">
              Fiche de l’événement
            </Dialog.Title>
            <Dialog.Close className="dialog-close">Fermer ×</Dialog.Close>
            {selected && <Detail key={selected} id={selected} />}
          </Dialog.Popup>
        </Dialog.Portal>
      </Dialog.Root>
    </>
  );
}
