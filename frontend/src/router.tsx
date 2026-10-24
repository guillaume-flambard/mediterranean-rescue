import { useSyncExternalStore, type AnchorHTMLAttributes, type MouseEvent } from "react";

// A small history router for the few workspace routes (English URLs); no route holds raw data.
const CHANGE = "app:locationchange";

function subscribe(onChange: () => void) {
  window.addEventListener("popstate", onChange);
  window.addEventListener(CHANGE, onChange);
  return () => {
    window.removeEventListener("popstate", onChange);
    window.removeEventListener(CHANGE, onChange);
  };
}

const snapshot = () => window.location.pathname + window.location.search;

let guard: (() => boolean) | null = null;

/** A screen with unsaved input can ask before in-app navigation (null removes the guard). */
export function setNavigationGuard(next: (() => boolean) | null) {
  guard = next;
}

export function useLocation(): { pathname: string; query: URLSearchParams } {
  const href = useSyncExternalStore(subscribe, snapshot, snapshot);
  const url = new URL(href, window.location.origin);
  return { pathname: url.pathname, query: url.searchParams };
}

export function navigate(to: string, options: { replace?: boolean } = {}) {
  if (to === snapshot()) return;
  if (guard && !guard()) return;
  if (options.replace) window.history.replaceState(null, "", to);
  else window.history.pushState(null, "", to);
  window.dispatchEvent(new Event(CHANGE));
}

/** Returns the named parameters when `pathname` matches `pattern` ("/a/:id/b"), else null. */
export function matchRoute(pattern: string, pathname: string): Record<string, string> | null {
  const expected = pattern.split("/");
  const actual = pathname.replace(/\/$/, "").split("/");
  if (expected.length !== actual.length) return null;
  const params: Record<string, string> = {};
  for (const [index, part] of expected.entries()) {
    const value = actual[index] ?? "";
    if (part.startsWith(":")) {
      if (!value) return null;
      try {
        params[part.slice(1)] = decodeURIComponent(value);
      } catch {
        return null; // malformed escape in the address: no match rather than a crash
      }
    } else if (part !== value) {
      return null;
    }
  }
  return params;
}

export function withQuery(path: string, values: Record<string, string | number | null | undefined>) {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(values)) {
    if (value !== null && value !== undefined && value !== "") query.set(key, String(value));
  }
  const text = query.toString();
  return text ? `${path}?${text}` : path;
}

export function Link({ to, onClick, ...props }: AnchorHTMLAttributes<HTMLAnchorElement> & { to: string }) {
  const follow = (event: MouseEvent<HTMLAnchorElement>) => {
    onClick?.(event);
    // Let the browser handle new tabs, downloads and modified clicks.
    if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    navigate(to);
  };
  return <a {...props} href={to} onClick={follow} />;
}
