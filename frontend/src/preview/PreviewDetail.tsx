import { api, type Kind } from "../api/client";
import { useI18n } from "../i18n/I18nProvider";
import { Link } from "../router";
import { formatPosition } from "../shared/geo";
import { Button } from "../ui/Button";
import { StatusLabel } from "../ui/Feedback";

export type PreviewStatus = "to_review" | "blocked" | "linked";

export function previewStatus(status: PreviewStatus) {
  return status === "to_review" ? "needsReview" : status === "blocked" ? "blocked" : "linked";
}

// One row of the latest private export, as the public detail would show an event; a link leads
// to the review of that row. Nothing here is published.
export function PreviewDetail({ id, kindLabel }: { id: string; kindLabel: (kind: Kind) => string }) {
  const i18n = useI18n();
  const { t } = i18n;
  const { data: item, error, refetch } = api.useQuery("get", "/api/private/v1/preview/events/{id}/", {
    params: { path: { id } },
  });
  if (error)
    return (
      <div role="alert">
        <p>{t("detail.loadError")}</p>
        <Button onClick={() => void refetch()}>{t("ui.retry")}</Button>
      </div>
    );
  if (!item) return <p role="status">{t("detail.loading")}</p>;
  const count = (value: number | null) => (value === null ? t("detail.unknownCount") : i18n.number(value));
  return (
    <>
      <p className="preview-flag">{t("preview.flag")}</p>
      <div className="detail-date">
        {item.occurred_on ? i18n.date(item.occurred_on) : t("review.unknown")} ·{" "}
        {item.kind ? kindLabel(item.kind as Kind) : t("review.unknown")}
      </div>
      <h2>{t("preview.detail.title", { line: item.line })}</h2>
      <p>
        <StatusLabel status={previewStatus(item.status)} />{" "}
        <span className="muted">{t(`preview.status.${item.status}`)}</span>
      </p>
      <dl>
        <div>
          <dt>{t("detail.people")}</dt>
          <dd>{count(item.people)}</dd>
        </div>
        <div>
          <dt>{t("preview.detail.women")}</dt>
          <dd>{count(item.women)}</dd>
        </div>
        <div>
          <dt>{t("preview.detail.minors")}</dt>
          <dd>{count(item.minors)}</dd>
        </div>
        {item.sheet === "Other_data" && (
          <div>
            <dt>{t("preview.detail.deaths")}</dt>
            <dd>{count(item.deaths)}</dd>
          </div>
        )}
        <div>
          <dt>{t("detail.port")}</dt>
          <dd>{item.port_label ? `“${item.port_label}”` : t("detail.notProvided")}</dd>
        </div>
        <div>
          <dt>{t("preview.detail.boat")}</dt>
          <dd>{item.boat_type ?? t("detail.notProvided")}</dd>
        </div>
        <div>
          <dt>{t("detail.position")}</dt>
          <dd>
            {item.position
              ? `${formatPosition(i18n, item.position.latitude, item.position.longitude)}${
                  item.position.inferred_hemisphere ? ` ${t("review.inferredHemisphere")}` : ""
                }`
              : t("detail.unknownPosition")}
          </dd>
        </div>
        <div>
          <dt>{t("preview.detail.photos")}</dt>
          <dd>{i18n.number(item.image_count)}</dd>
        </div>
      </dl>
      <p className="muted">
        {t("preview.detail.provenance", {
          source: item.source.name,
          sheet: item.sheet,
          line: item.line,
          date: i18n.date(item.exported_at.slice(0, 10)),
        })}
      </p>
      <p>
        <Link to={`/workspace/review/${item.snapshot}/rows/${item.id}`}>{t("preview.detail.check")}</Link>
      </p>
    </>
  );
}
