import "@fontsource-variable/raleway";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { lazy, StrictMode, Suspense } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import { I18nProvider } from "./i18n/I18nProvider";
import "./styles/tokens.css";
import "./styles/ui.css";
import "./styles.css";

// The component catalog is a development tool: it is excluded from production builds.
const Catalog = import.meta.env.DEV ? lazy(() => import("./dev/Catalog")) : null;

const client = new QueryClient({ defaultOptions: { queries: { staleTime: 0, gcTime: 60000, retry: 1 } } });
const root = document.getElementById("root");
if (!root) throw Error("Application root missing");
const showCatalog = Catalog !== null && window.location.pathname === "/dev/components";

createRoot(root).render(
  <StrictMode>
    <I18nProvider>
      <QueryClientProvider client={client}>
        {showCatalog && Catalog ? (
          <Suspense fallback={null}>
            <Catalog />
          </Suspense>
        ) : (
          <App />
        )}
      </QueryClientProvider>
    </I18nProvider>
  </StrictMode>,
);
