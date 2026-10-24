// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it } from "vitest";
import { Link, matchRoute, navigate, useLocation, withQuery } from "./router";

function Where() {
  const { pathname, query } = useLocation();
  return <p>{`${pathname}|${query.get("status") ?? ""}`}</p>;
}

describe("router", () => {
  afterEach(() => window.history.replaceState(null, "", "/"));

  it("matches parameters and builds queries without empty values", () => {
    expect(matchRoute("/workspace/review/:snapshot/rows/:row", "/workspace/review/a/rows/b/")).toEqual({ snapshot: "a", row: "b" });
    expect(matchRoute("/workspace/review/:snapshot/rows/:row", "/workspace/review/a")).toBeNull();
    expect(withQuery("/workspace/review", { status: "linked", offset: 0, snapshot: null })).toBe("/workspace/review?status=linked&offset=0");
  });

  it("navigates in place and lets modified clicks open new tabs", async () => {
    render(
      <>
        <Where />
        <Link to="/workspace/review?status=blocked">Blocked</Link>
      </>,
    );
    await userEvent.click(screen.getByRole("link", { name: "Blocked" }));
    expect(screen.getByText("/workspace/review|blocked")).toBeTruthy();
    navigate("/", { replace: true });
    expect(await screen.findByText("/|")).toBeTruthy();
  });
});
