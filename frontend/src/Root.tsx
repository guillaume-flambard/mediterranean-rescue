import { Component, lazy, Suspense, type ReactNode } from "react";
import App from "./App";
import { createI18n } from "./i18n/I18nProvider";
import { useLocation } from "./router";

// The component catalog is a development tool: it is excluded from production builds.
const Catalog = import.meta.env.DEV ? lazy(() => import("./dev/Catalog")) : null;
// The private workspace loads on demand; the public site never downloads it.
const ReviewWorkspace = lazy(async () => ({ default: (await import("./review/ReviewWorkspace")).ReviewWorkspace }));

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
  if (pathname === "/workspace/review" || pathname.startsWith("/workspace/review/"))
    return (
      <Suspense fallback={null}>
        <ReviewWorkspace />
      </Suspense>
    );
  return <App />;
}
