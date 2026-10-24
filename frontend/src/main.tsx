import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { createClient, cacheExchange, fetchExchange, Provider } from "urql";
import App from "./App";
import "./styles.css";
let csrf: Promise<string> | undefined;
async function csrfToken() {
  csrf ??= fetch("/api/csrf/", { credentials: "same-origin" })
    .then(async (response) => {
      if (!response.ok) throw Error("Connexion au serveur impossible");
      const body: unknown = await response.json();
      if (
        typeof body !== "object" ||
        body === null ||
        !("csrfToken" in body) ||
        typeof body.csrfToken !== "string"
      )
        throw Error("Réponse de sécurité invalide");
      return body.csrfToken;
    })
    .catch((error) => {
      csrf = undefined;
      throw error;
    });
  return csrf;
}
const securedFetch: typeof fetch = async (input, init) => {
  const headers = new Headers(init?.headers);
  headers.set("X-CSRFToken", await csrfToken());
  return fetch(input, { ...init, headers, credentials: "same-origin" });
};
const client = createClient({
  url: "/graphql/",
  exchanges: [cacheExchange, fetchExchange],
  fetch: securedFetch,
  requestPolicy: "cache-and-network",
  preferGetMethod: false,
});
const root = document.getElementById("root");
if (!root) throw Error("Application root missing");
createRoot(root).render(
  <StrictMode>
    <Provider value={client}>
      <App />
    </Provider>
  </StrictMode>,
);
