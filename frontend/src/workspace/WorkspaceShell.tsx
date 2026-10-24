import { useQueryClient } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { api, errorCode, resetCsrfToken, type Me } from "../api/client";
import { useI18n } from "../i18n/I18nProvider";
import { AccessProblem } from "../review/AccessProblem";
import { Link, useLocation } from "../router";
import { Button } from "../ui/Button";
import { BrandMark } from "../ui/BrandMark";
import { Icon } from "../ui/Icon";
import { InlineMessage, PendingState } from "../ui/Feedback";

export const ME_QUERY = ["get", "/api/private/v1/me/"] as const;

type Section = "home" | "data" | "imports" | "review" | "publish" | "ports";

const anyRole = (me: Me) => Object.values(me.permissions).some(Boolean);

// In the order of the work: see what is new, verify it, publish it; then the occasional tasks.
const SECTIONS: readonly { key: Section; path: string; allowed: (me: Me) => boolean }[] = [
  { key: "home", path: "/workspace", allowed: anyRole },
  { key: "data", path: "/workspace/data", allowed: (me) => me.permissions.review_identity },
  { key: "review", path: "/workspace/review", allowed: (me) => me.permissions.review_identity },
  {
    key: "publish",
    path: "/workspace/publish",
    allowed: (me) => me.permissions.review_identity || me.permissions.prepare_drafts || me.permissions.publish,
  },
  { key: "ports", path: "/workspace/ports", allowed: (me) => me.permissions.review_identity },
  { key: "imports", path: "/workspace/imports", allowed: (me) => me.permissions.stage_snapshot || me.permissions.review_identity },
];

const isCurrent = (path: string, pathname: string) =>
  path === "/workspace" ? pathname === path || pathname === `${path}/` : pathname === path || pathname.startsWith(`${path}/`);

// Private workspace frame: session and permission checks, then a short navigation that only lists
// the sections this user may open (user-flows §3). Children render once the user is known.
export function WorkspaceShell({
  section,
  title,
  className = "review",
  children,
}: {
  section: Section;
  title: string;
  className?: string;
  children: (me: Me) => ReactNode;
}) {
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const { pathname } = useLocation();
  const me = api.useQuery("get", "/api/private/v1/me/", {});
  const signOut = api.useMutation("delete", "/api/private/v1/session/");

  if (me.isPending) return <PendingState label={t("workspace.loading")} />;
  if (me.error) {
    const code = errorCode(me.error);
    if (code === "not_authenticated") return <AccessProblem code={code} />;
    return (
      <main className={className}>
        <h1>{title}</h1>
        {code === "permission_denied" ? (
          <AccessProblem code={code} />
        ) : (
          <InlineMessage tone="error">{t("workspace.loadError")}</InlineMessage>
        )}
      </main>
    );
  }

  const current = SECTIONS.find((item) => item.key === section);
  const allowed = current?.allowed(me.data) ?? false;
  return (
    <main className={className}>
      <header className="workspace-bar">
        <div className="workspace-bar__top">
          <p className="workspace-bar__brand">
            <BrandMark size={28} className="workspace-bar__mark" />
            {t("app.brand")} <span>{t("workspace.teamSpace")}</span>
          </p>
          <span className="workspace-bar__user" title={t("review.signedInAs", { name: me.data.username })}>
            {me.data.username}
          </span>
          <Link to="/" className="workspace-bar__action" aria-label={t("review.publicSite")} title={t("review.publicSite")}>
            <Icon name="map" size={18} />
            <span className="workspace-bar__label">{t("review.publicSite")}</span>
          </Link>
          <Button
            size="sm"
            variant="quiet"
            className="workspace-bar__action"
            aria-label={t("signIn.signOut")}
            loading={signOut.isPending}
            onClick={async () => {
              await signOut.mutateAsync({});
              resetCsrfToken();
              queryClient.clear();
              void me.refetch();
            }}
          >
            <Icon name="signOut" size={18} />
            <span className="workspace-bar__label">{t("signIn.signOut")}</span>
          </Button>
        </div>
        <nav className="workspace-nav" aria-label={t("workspace.nav")}>
          {SECTIONS.filter((item) => item.allowed(me.data)).map((item) => (
            <Link
              key={item.key}
              to={item.path}
              className="workspace-nav__link"
              aria-current={isCurrent(item.path, pathname) ? "page" : undefined}
            >
              {t(`workspace.section.${item.key}`)}
            </Link>
          ))}
        </nav>
      </header>
      {allowed ? (
        children(me.data)
      ) : (
        <>
          <h1>{title}</h1>
          <AccessProblem code="permission_denied" />
        </>
      )}
    </main>
  );
}
