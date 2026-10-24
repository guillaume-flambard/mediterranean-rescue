import createFetchClient, { type Middleware } from "openapi-fetch";
import createClient from "openapi-react-query";
import type { components, paths } from "./schema";

const SAFE_METHODS = new Set(["GET", "HEAD", "OPTIONS"]);
let csrfToken: Promise<string> | null = null;

// The CSRF cookie is HttpOnly: the token is read from /api/csrf/ and sent in X-CSRFToken.
function readCsrfToken(): Promise<string> {
  csrfToken ??= fetch("/api/csrf/", { credentials: "same-origin" })
    .then((response) => (response.ok ? response.json() : Promise.reject(new Error("csrf"))))
    .then((body: { csrfToken: string }) => body.csrfToken)
    .catch((error: unknown) => {
      csrfToken = null;
      throw error;
    });
  return csrfToken;
}

/** Forget the token: Django rotates it when a user signs in or out. */
export function resetCsrfToken() {
  csrfToken = null;
}

const retries = new WeakMap<Request, Request>();

export const csrfMiddleware: Middleware = {
  async onRequest({ request }) {
    if (SAFE_METHODS.has(request.method)) return undefined;
    request.headers.set("X-CSRFToken", await readCsrfToken());
    // Kept to replay the write once if the token expired (403 csrf_failed).
    retries.set(request, request.clone());
    return request;
  },
  async onResponse({ request, response }) {
    const original = retries.get(request);
    if (!original || response.status !== 403) return undefined;
    const body = (await response.clone().json().catch(() => null)) as { code?: string } | null;
    if (body?.code !== "csrf_failed") return undefined;
    csrfToken = null;
    original.headers.set("X-CSRFToken", await readCsrfToken());
    return fetch(original);
  },
};

// fetch is resolved at call time (not captured at import), so polyfills and test doubles apply.
export const fetchClient = createFetchClient<paths>({
  // Absolute same-origin URLs: relative URLs are not valid outside a document (tests, workers).
  baseUrl: typeof window === "undefined" ? "" : window.location.origin,
  credentials: "same-origin",
  fetch: (request) => globalThis.fetch(request),
});
fetchClient.use(csrfMiddleware);
export const api = createClient(fetchClient);

export type Kind = components["schemas"]["KindEnum"];
export type EventFilter = NonNullable<paths["/api/v1/map-points/"]["get"]["parameters"]["query"]>;
export type MapPoints = components["schemas"]["MapResult"]["points"];
export type ApiError = components["schemas"]["Error"];
export type ReviewStatus = components["schemas"]["ReviewStatusEnum"];
export type QueueItem = components["schemas"]["QueueItem"];
export type RowDetail = components["schemas"]["RowDetail"];
export type IdentityCandidate = components["schemas"]["Candidate"];

/** Error code of the private API envelope, or "network" when no response was readable. */
export function errorCode(error: unknown): string {
  if (error && typeof error === "object" && "code" in error && typeof error.code === "string") return error.code;
  return "network";
}
