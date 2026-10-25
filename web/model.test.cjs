const { test } = require("node:test");
const assert = require("node:assert/strict");
const { validate, filterEvents } = require("./model.js");
const e = {
  id: "demo",
  date: "2024-02-29",
  longitude: 13,
  latitude: 34,
  people: 12,
  ship: "Navire A",
  source: "https://example.org/demo",
  note: "Fictif",
  synthetic: true,
};
test("validates a leap day and preserves zero count", () => {
  assert.equal(validate([{ ...e, people: 0 }])[0].people, 0);
});
test("rejects invalid calendar dates and types", () => {
  for (const date of ["2023-02-29", "2024-02-30", "2024-13-01", null])
    assert.throws(() => validate([{ ...e, date }]));
});
test("rejects coordinates outside Mediterranean or non numbers", () => {
  for (const longitude of [null, "13", -20, 41, NaN])
    assert.throws(() => validate([{ ...e, longitude }]));
});
test("rejects duplicates, mixed reality, unsafe links and missing fields", () => {
  assert.throws(() => validate([e, e]));
  for (const source of ["javascript:alert(1)", "file:///etc/passwd", "oops"])
    assert.throws(() => validate([{ ...e, source }]));
  assert.throws(() => validate([{ ...e, synthetic: false }]));
  assert.throws(() => validate([{ ...e, ship: "" }]));
  assert.throws(() => validate([{ ...e, people: -1 }]));
});
test("empty dataset accepted; size bounded", () => {
  assert.deepEqual(validate([]), []);
  assert.throws(() => validate({}));
  assert.throws(() => validate(Array(2001).fill(e)));
});
test("filters inclusive date boundaries and vessel, sorts recent first", () => {
  const events = validate([
    e,
    { ...e, id: "second", date: "2023-01-01", ship: "Navire B" },
  ]);
  assert.equal(
    filterEvents(events, { from: "2024-02-29", to: "2024-02-29", ship: "" })
      .length,
    1,
  );
  assert.equal(filterEvents(events, { ship: "Navire B" })[0].id, "second");
  assert.equal(filterEvents(events, { from: "2025-01-01" }).length, 0);
  assert.equal(
    filterEvents(events, { from: "2025-01-01", to: "2024-01-01" }).length,
    0,
  );
  assert.equal(filterEvents(events, {})[0].id, "demo");
});
