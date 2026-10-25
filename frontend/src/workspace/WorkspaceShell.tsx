import { useQueryClient } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { api, errorCode, resetCsrfToken, type Me } from "../api/client";
import { useI18n } from "../i18n/I18nProvider";
import { AccessProblem } from "../review/AccessProblem";
import { Link, useLocation } from "../router";
import { Button } from "../ui/Button";
import { BrandMark } from "../ui/BrandMark";
import { Icon, type IconName } from "../ui/Icon";
import { InlineMessage, PendingState } from "../ui/Feedback";

export const ME_QUERY = ["get", "/api/private/v1/me/"] as const;

type Section = "home" | "data" | "imports" | "review" | "publish" | "ports" | "team" | "help" | "practice" | "history";

const anyRole = (me: Me) => Object.values(me.permissions).some(Boolean);

// In the order of the work: see what is new, verify it, publish it; then the occasional tasks.
const SECTIONS: readonly { key: Section; path: string; icon: IconName; allowed: (me: Me) => boolean; secondary?: boolean }[] = [
  { key: "home", path: "/workspace", icon: "grid", allowed: anyRole },
  { key: "review", path: "/workspace/review", icon: "listCheck", allowed: (me) => me.permissions.review_identity },
  {
    key: "publish",
    path: "/workspace/publish",
    icon: "send",
    allowed: (me) => me.permissions.review_identity || me.permissions.prepare_drafts || me.permissions.publish,
  },
  { key: "data", path: "/workspace/data", icon: "database", allowed: (me) => me.permissions.review_identity },
  { key: "ports", path: "/workspace/ports", icon: "anchor", allowed: (me) => me.permissions.review_identity, secondary: true },
  {
    key: "imports",
    path: "/workspace/imports",
    icon: "upload",
    allowed: (me) => me.permissions.stage_snapshot || me.permissions.review_identity,
    secondary: true,
  },
  { key: "history", path: "/workspace/history", icon: "history", allowed: anyRole },
  { key: "team", path: "/workspace/team", icon: "people", allowed: (me) => me.permissions.invite },
  { key: "practice", path: "/workspace/practice", icon: "school", allowed: anyRole },
  { key: "help", path: "/workspace/help", icon: "help", allowed: anyRole },
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
  // Signed out, coming back to the window must not refetch who is signed in: the refetch shows
  // "Loading" and remounts the sign-in form, which loses what was typed.
  const me = api.useQuery("get", "/api/private/v1/me/", {}, { refetchOnWindowFocus: (query) => query.state.status === "success" });
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
  const sections = SECTIONS.filter((item) => item.allowed(me.data));
  const signOutButton = (className: string) => (
    <Button
      size="sm"
      variant="quiet"
      className={className}
      aria-label={t("signIn.signOut")}
      loading={signOut.isPending}
      onClick={async () => {
        await signOut.mutateAsync({});
        resetCsrfToken();
        // Reset, not clear: a cleared cache left the screen on "Loading" with no observer to
        // refetch who is signed in.
        await queryClient.resetQueries();
      }}
    >
      <Icon name="signOut" size={18} />
      <span className="workspace-bar__label">{t("signIn.signOut")}</span>
    </Button>
  );
  return (
    <div className="workstation">
      {/* Desk: one navy column with every section this person may open, in the order of the work. */}
      <aside className="workspace-side">
        <p className="workspace-side__brand">
          <BrandMark size={30} />
          <span>
            {t("app.brand")}
            <small>{t("workspace.teamSpace")}</small>
          </span>
        </p>
        <nav className="workspace-side__nav" aria-label={t("workspace.nav")}>
          {sections.map((item) => (
            <Link
              key={item.key}
              to={item.path}
              className={`workspace-side__link${item.secondary ? " workspace-side__link--secondary" : ""}`}
              aria-current={isCurrent(item.path, pathname) ? "page" : undefined}
            >
              <Icon name={item.icon} size={19} />
              {t(`workspace.section.${item.key}`)}
            </Link>
          ))}
        </nav>
        <div className="workspace-side__foot">
          <p className="workspace-side__user" title={t("review.signedInAs", { name: me.data.username })}>
            <Icon name="people" size={16} />
            {me.data.username}
          </p>
          <Link to="/" className="workspace-side__link workspace-side__link--secondary">
            <Icon name="map" size={18} />
            {t("review.publicSite")}
          </Link>
          {signOutButton("workspace-side__link workspace-side__link--secondary workspace-side__signout")}
        </div>
      </aside>
      <main className={className}>
        {/* Phones and tablets: the navy band with the sections as pills under it. */}
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
            {signOutButton("workspace-bar__action")}
          </div>
          <nav className="workspace-nav" aria-label={t("workspace.navCompact")}>
            {sections.map((item) => (
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
    </div>
  );
}
