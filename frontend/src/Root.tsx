import { Component, lazy, Suspense, type ReactNode } from "react";
import App from "./App";
import { createI18n } from "./i18n/I18nProvider";
import { useLocation } from "./router";

// The component catalog is a development tool: it is excluded from production builds.
const Catalog = import.meta.env.DEV ? lazy(() => import("./dev/Catalog")) : null;
// The private workspace loads on demand; the public site never downloads it.
const ReviewWorkspace = lazy(async () => ({ default: (await import("./review/ReviewWorkspace")).ReviewWorkspace }));
const ImportsWorkspace = lazy(async () => ({ default: (await import("./imports/ImportsWorkspace")).ImportsWorkspace }));
const PortsWorkspace = lazy(async () => ({ default: (await import("./ports/PortsWorkspace")).PortsWorkspace }));
const TeamData = lazy(async () => ({ default: (await import("./workspace/TeamData")).TeamData }));
const AboutPage = lazy(async () => ({ default: (await import("./explore/AboutPage")).AboutPage }));
const TeamHome = lazy(async () => ({ default: (await import("./workspace/TeamHome")).TeamHome }));
const PublishWorkspace = lazy(async () => ({ default: (await import("./workspace/PublishWorkspace")).PublishWorkspace }));

const within = (pathname: string, base: string) => pathname === base || pathname.startsWith(`${base}/`);

// Last resort: an unexpected rendering error shows a message instead of a blank page.
class ErrorBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() {
    return { failed: true };
  }
  render() {
    if (!this.state.failed) return this.props.children;
    return (
      <main className="review" role="alert">
        <p>{createI18n(document.documentElement.lang === "fr" ? "fr" : "en").t("ui.crash")}</p>
      </main>
    );
  }
}

export function Root() {
  return (
    <ErrorBoundary>
      <Routes />
    </ErrorBoundary>
  );
}

function Routes() {
  const { pathname } = useLocation();
  if (Catalog && pathname === "/dev/components")
    return (
      <Suspense fallback={null}>
        <Catalog />
      </Suspense>
    );
  const workspace = within(pathname, "/workspace/review") ? (
    <ReviewWorkspace />
  ) : within(pathname, "/workspace/imports") ? (
    <ImportsWorkspace />
  ) : within(pathname, "/workspace/data") ? (
    <TeamData />
  ) : within(pathname, "/workspace/ports") ? (
    <PortsWorkspace />
  ) : within(pathname, "/workspace/publish") ? (
    <PublishWorkspace />
  ) : pathname === "/workspace" || pathname === "/workspace/" ? (
    <TeamHome />
  ) : null;
  if (workspace) return <Suspense fallback={null}>{workspace}</Suspense>;
  if (pathname === "/about" || pathname === "/about/")
    return (
      <Suspense fallback={null}>
        <AboutPage />
      </Suspense>
    );
  return <App />;
}
