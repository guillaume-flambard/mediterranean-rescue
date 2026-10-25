import { useEffect, useRef } from "react";

// Reads go through TanStack Query, which already aborts unobserved requests (openapi-react-query
// passes its AbortSignal to fetch). This hook is for the other requests (uploads, reviewed
// decisions): each call aborts the previous one, and unmounting aborts the one in flight.

export function isAbortError(error: unknown): boolean {
  return (
    (error instanceof DOMException && error.name === "AbortError") ||
    (error instanceof Error && error.name === "AbortError")
  );
}

export function useAbortableRequest() {
  const controller = useRef<AbortController | null>(null);

  useEffect(
    () => () => {
      controller.current?.abort();
      controller.current = null;
    },
    [],
  );

  const run = <T,>(request: (signal: AbortSignal) => Promise<T>): Promise<T> => {
    controller.current?.abort();
    const next = new AbortController();
    controller.current = next;
    return request(next.signal).finally(() => {
      if (controller.current === next) controller.current = null;
    });
  };

  const abort = () => {
    controller.current?.abort();
    controller.current = null;
  };

  return { run, abort };
}
