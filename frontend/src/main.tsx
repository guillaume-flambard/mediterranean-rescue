import "@fontsource-variable/raleway";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { errorCode } from "./api/client";
import { Root } from "./Root";
import { I18nProvider } from "./i18n/I18nProvider";
import "./styles/tokens.css";
import "./styles/ui.css";
import "./styles.css";
import "./styles/review.css";
import "./styles/workspace.css";

// A refused request (sign-in, permission, not found, invalid) is not retried; a network or
// server failure gets one more try.
const FINAL_CODES = new Set(["not_authenticated", "permission_denied", "csrf_failed", "not_found", "invalid"]);
const client = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 0, gcTime: 60000, retry: (failures, error) => failures < 1 && !FINAL_CODES.has(errorCode(error)) },
  },
});
const root = document.getElementById("root");
if (!root) throw Error("Application root missing");

createRoot(root).render(
  <StrictMode>
    <I18nProvider>
      <QueryClientProvider client={client}>
        <Root />
      </QueryClientProvider>
    </I18nProvider>
  </StrictMode>,
);
