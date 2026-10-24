// @vitest-environment jsdom
import { renderHook } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { isAbortError, useAbortableRequest } from "./abortable";

const pending = (signals: AbortSignal[]) => (signal: AbortSignal) =>
  new Promise<string>((resolve, reject) => {
    signals.push(signal);
    signal.addEventListener("abort", () => reject(new DOMException("Aborted", "AbortError")));
    setTimeout(() => resolve("done"), 50);
  });

describe("useAbortableRequest", () => {
  it("aborts the previous request when a new one starts", async () => {
    const signals: AbortSignal[] = [];
    const { result } = renderHook(() => useAbortableRequest());
    const first = result.current.run(pending(signals));
    const second = result.current.run(pending(signals));
    await expect(first).rejects.toSatisfy(isAbortError);
    await expect(second).resolves.toBe("done");
    expect(signals.map((signal) => signal.aborted)).toEqual([true, false]);
  });

  it("aborts the request in flight on unmount", async () => {
    const signals: AbortSignal[] = [];
    const { result, unmount } = renderHook(() => useAbortableRequest());
    const request = result.current.run(pending(signals));
    unmount();
    await expect(request).rejects.toSatisfy(isAbortError);
    expect(signals[0]?.aborted).toBe(true);
  });

  it("can be cancelled explicitly", async () => {
    const signals: AbortSignal[] = [];
    const { result } = renderHook(() => useAbortableRequest());
    const request = result.current.run(pending(signals));
    result.current.abort();
    await expect(request).rejects.toSatisfy(isAbortError);
  });

  it("recognizes abort errors only", () => {
    expect(isAbortError(new DOMException("x", "AbortError"))).toBe(true);
    expect(isAbortError(new Error("network"))).toBe(false);
  });
});
