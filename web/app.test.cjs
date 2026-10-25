const { test } = require("node:test");
const assert = require("node:assert/strict");
const vm = require("node:vm");
const fs = require("node:fs");
const path = require("node:path");
function setup() {
  let active = null;
  const elements = {};
  const downloads = [];
  class Element {
    constructor(tag) {
      this.tag = tag;
      this.children = [];
      this.attrs = {};
      this.dataset = {};
      this.value = "";
      this.disabled = false;
      this.hidden = false;
      this.events = {};
      this.textContent = "";
      this.files = [];
    }
    append(el) {
      this.children.push(el);
    }
    replaceChildren(...els) {
      this.children = els;
    }
    setAttribute(k, v) {
      this.attrs[k] = String(v);
    }
    addEventListener(k, fn) {
      this.events[k] = fn;
    }
    focus() {
      active = this;
    }
    click() {
      if (this.tag === "a") downloads.push(this);
      this.events.click?.();
      this.onclick?.();
    }
    get options() {
      return this.children;
    }
    add(el) {
      this.append(el);
    }
  }
  const document = {
    getElementById: (id) => (elements[id] ??= new Element(id)),
    createElement: (tag) => new Element(tag),
    createElementNS: (_, tag) => new Element(tag),
  };
  const context = vm.createContext({
    document,
    URL,
    Blob,
    setTimeout: (fn) => fn(),
    Option: function (text, value) {
      const e = new Element("option");
      e.textContent = text;
      e.value = value;
      return e;
    },
    window: {},
    console,
  });
  for (const file of ["model.js", "demo.js"])
    vm.runInContext(
      fs.readFileSync(path.join(__dirname, file), "utf8"),
      context,
    );
  context.RescueModel = context.window.RescueModel;
  context.DEMO = context.window.DEMO;
  context.LAND = { features: [] };
  vm.runInContext(
    fs.readFileSync(path.join(__dirname, "app.js"), "utf8"),
    context,
  );
  const upload = async (contents) => {
    elements.import.files = [
      { size: contents.length, text: async () => contents },
    ];
    await elements.import.events.change({ target: elements.import });
  };
  return { elements, upload, context, downloads, active: () => active };
}
test("list and details preserve keyboard focus; filters remove stale selection", () => {
  const a = setup(),
    e = a.elements;
  assert.equal(e.events.children.length, 6);
  e.events.children[0].click();
  assert.equal(a.active().dataset.eventId, "DEMO-006");
  assert.match(e.detail.children[0].textContent, /DEMO-006/);
  e.ship.value = "Navire B";
  e.ship.events.change();
  assert.equal(e.events.children.length, 2);
  assert.match(e.detail.children[0].textContent, /Sélectionnez/);
  e.from.value = "2025-01-01";
  e.from.events.change();
  assert.match(e.events.children[0].textContent, /Aucun événement/);
  assert.equal(e.export.disabled, true);
  e.to.value = "2024-01-01";
  e.to.events.change();
  assert.equal(e["filter-error"].hidden, false);
  e.clear.onclick();
  assert.equal(e.events.children.length, 6);
});
test("import replacement is atomic and blank dataset can be restored", async () => {
  const a = setup(),
    e = a.elements;
  await a.upload("invalid JSON");
  assert.equal(e.events.children.length, 6);
  assert.equal(e["import-error"].hidden, false);
  await a.upload(
    JSON.stringify([
      { ...a.context.DEMO[0], id: "new" },
      { ...a.context.DEMO[1], source: "javascript:alert(1)" },
    ]),
  );
  assert.equal(e.events.children.length, 6);
  await a.upload("[]");
  assert.match(e.summary.textContent, /0 événements/);
  assert.equal(e.export.disabled, true);
  e.restore.onclick();
  assert.equal(e.events.children.length, 6);
  assert.equal(e["import-error"].hidden, true);
  await a.upload(JSON.stringify([{ ...a.context.DEMO[0], id: "IMPORTED" }]));
  assert.equal(e.events.children.length, 1);
  assert.equal(e.events.children[0].dataset.eventId, "IMPORTED");
});
test("restore invalidates an in-flight file read", async () => {
  const a = setup(),
    e = a.elements;
  let resolve;
  const pending = new Promise((r) => (resolve = r));
  e.import.files = [{ size: 2, text: () => pending }];
  const uploading = e.import.events.change({ target: e.import });
  e.restore.onclick();
  resolve("[]");
  await uploading;
  assert.equal(e.events.children.length, 6);
  assert.match(e["import-status"].textContent, /restaurés/);
});
test("oversize file rejected, plain text cannot become injected HTML, export initiates download", async () => {
  const a = setup(),
    e = a.elements;
  e.import.files = [
    {
      size: 3000000,
      text: () => {
        throw Error("must not read");
      },
    },
  ];
  await e.import.events.change({ target: e.import });
  assert.match(e["import-error"].textContent, /volumineux/);
  assert.equal(e.events.children.length, 6);
  await a.upload(
    JSON.stringify([
      {
        ...a.context.DEMO[0],
        ship: "<img src=x onerror=alert(1)>",
        note: "<script>alert(1)</script>",
      },
    ]),
  );
  e.events.children[0].click();
  assert.ok(
    e.detail.children.some(
      (el) => el.textContent === "<script>alert(1)</script>",
    ),
  );
  e.export.onclick();
  assert.equal(a.downloads[0].download, "evenements-fictifs.json");
});
