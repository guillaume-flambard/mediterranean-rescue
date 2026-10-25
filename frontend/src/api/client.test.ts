// @vitest-environment jsdom
import { afterEach, describe, expect, it, vi } from "vitest";
import { fakeServer } from "../test/fakeServer";
import { errorCode, fetchClient } from "./client";

const ROW = "11111111-1111-1111-1111-111111111111";

describe("private API client", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("sends the CSRF token on writes only, and replays a write once when the token expired", async () => {
    let tokens = 0;
    let attempts = 0;
    const { calls } = fakeServer({
      "GET /api/csrf/": () => ({ body: { csrfToken: `token-${++tokens}` } }),
      "GET /api/private/v1/me/": () => ({ body: { username: "r", permissions: { review_identity: true } } }),
      "POST /api/private/v1/review/rows/:id/decision/": (call) =>
        ++attempts === 1
          ? { status: 403, body: { code: "csrf_failed", detail: "CSRF Failed" } }
          : { body: { seen: call.headers.get("X-CSRFToken") } },
    });
    await fetchClient.GET("/api/private/v1/me/");
    expect(calls.at(-1)?.headers.get("X-CSRFToken")).toBeNull();
    const result = await fetchClient.POST("/api/private/v1/review/rows/{id}/decision/", {
      params: { path: { id: ROW } },
      body: { action: "create_identity", reason: "r" },
    });
    expect(result.response.status).toBe(200);
    expect((result.data as unknown as { seen: string }).seen).toBe("token-2");
    expect(attempts).toBe(2);
  });

  it("reads the error code of the envelope", async () => {
    fakeServer({ "GET /api/private/v1/me/": () => ({ status: 401, body: { code: "not_authenticated", detail: "x" } }) });
    const { error } = await fetchClient.GET("/api/private/v1/me/");
    expect(errorCode(error)).toBe("not_authenticated");
    expect(errorCode(new TypeError("Failed to fetch"))).toBe("network");
  });
});
