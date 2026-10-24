import { vi } from "vitest";

export interface FakeCall {
  method: string;
  path: string;
  query: URLSearchParams;
  headers: Headers;
  body: unknown;
}

type Handler = (call: FakeCall) => { status?: number; body: unknown } | Promise<{ status?: number; body: unknown }>;

// Replaces window.fetch with a router on "METHOD /path"; records every call for assertions.
export function fakeServer(routes: Record<string, Handler>) {
  const calls: FakeCall[] = [];
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const request = input instanceof Request ? input : new Request(new URL(String(input), "http://localhost"), init);
    const url = new URL(request.url, "http://localhost");
    if (request.signal.aborted) throw new DOMException("Aborted", "AbortError");
    let payload: unknown = null;
    if (request.method !== "GET") {
      if ((request.headers.get("Content-Type") ?? "").startsWith("multipart/form-data")) {
        // Uploads: fields as strings, files by name.
        const form = await request.formData();
        payload = Object.fromEntries([...form.entries()].map(([key, value]) => [key, typeof value === "string" ? value : value.name]));
      } else {
        const text = await request.text();
        payload = text ? JSON.parse(text) : null;
      }
    }
    const call: FakeCall = {
      method: request.method,
      path: url.pathname,
      query: url.searchParams,
      headers: request.headers,
      body: payload,
    };
    calls.push(call);
    // Like Django: a write without the CSRF header is refused before any handler runs.
    if (!["GET", "HEAD", "OPTIONS"].includes(call.method) && !call.headers.get("X-CSRFToken")) {
      return new Response(JSON.stringify({ code: "csrf_failed", detail: "CSRF Failed" }), { status: 403 });
    }
    const key = Object.keys(routes).find((pattern) => {
      const [method, path] = pattern.split(" ");
      return method === call.method && new RegExp(`^${(path ?? "").replace(/:[^/]+/g, "[^/]+")}$`).test(call.path);
    });
    if (!key) return new Response(JSON.stringify({ code: "not_found", detail: "No fake route" }), { status: 404 });
    const { status = 200, body } = await routes[key]!(call);
    return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
  });
  vi.stubGlobal("fetch", fetchMock);
  return { calls, fetchMock };
}
