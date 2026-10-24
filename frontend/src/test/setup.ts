import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";
import { resetCsrfToken } from "../api/client";

afterEach(() => {
  cleanup();
  // The cached CSRF token must not leak from one test to the next.
  resetCsrfToken();
});
