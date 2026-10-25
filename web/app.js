"use strict";
const $ = (id) => document.getElementById(id),
  NS = "http://www.w3.org/2000/svg";
let data = RescueModel.validate(window.DEMO),
  selected = null,
  visible = [],
  zoom = 1,
  importGeneration = 0;
const text = (tag, value, parent, cls) => {
  const el = document.createElement(tag);
  el.textContent = value;
  if (cls) el.className = cls;
  parent.append(el);
  return el;
};
const svg = (tag, attrs, parent) => {
  const el = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, v);
  parent.append(el);
  return el;
};
// Equirectangular projection centred on 15° E / 38° N. Local land shapes only.
const project = ([lon, lat]) => [
  ((lon + 6) / 46) * 1000,
  ((46 - lat) / 16) * 600,
];
for (const f of LAND.features) {
  const polys =
    f.geometry.type === "Polygon"
      ? [f.geometry.coordinates]
      : f.geometry.coordinates;
  let path = "";
  for (const poly of polys)
    for (const ring of poly) {
      path +=
        ring
          .map((coord, i) => {
            const [x, y] = project(coord);
            return (i ? "L" : "M") + x.toFixed(2) + "," + y.toFixed(2);
          })
          .join("") + "Z";
    }
  svg("path", { d: path, class: "land", "fill-rule": "evenodd" }, $("land"));
}
for (const [label, lon, lat, sea] of [
  ["Italie", 12, 42.6],
  ["Sicile", 14, 37.6],
  ["Tunisie", 8.3, 34.2],
  ["Libye", 18, 31.7],
  ["Malte", 14.3, 36.2],
  ["Grèce", 24, 40],
  ["Mer Méditerranée", 21, 35.8, true],
]) {
  const [x, y] = project([lon, lat]);
  svg(
    "text",
    { x, y, class: sea ? "sea-label" : "geo-label", "text-anchor": "middle" },
    $("labels"),
  ).textContent = label;
}
function setZoom(value) {
  zoom = Math.max(1, Math.min(4, value));
  let center = [500, 300];
  const e = visible.find((e) => e.id === selected);
  if (e && zoom > 1) center = project([e.longitude, e.latitude]);
  const w = 1000 / zoom,
    h = 600 / zoom;
  const x = Math.max(0, Math.min(1000 - w, center[0] - w / 2)),
    y = Math.max(0, Math.min(600 - h, center[1] - h / 2));
  $("map").setAttribute("viewBox", [x, y, w, h].join(" "));
  $("zoom-in").disabled = zoom >= 4;
  $("zoom-out").disabled = zoom <= 1;
}
function ships() {
  const old = $("ship").value;
  $("ship").replaceChildren(new Option("Tous les navires", ""));
  for (const s of [...new Set(data.map((e) => e.ship))].sort())
    $("ship").add(new Option(s, s));
  if ([...$("ship").options].some((o) => o.value === old))
    $("ship").value = old;
}
function render() {
  const from = $("from").value,
    to = $("to").value;
  const invalid = from && to && from > to;
  $("filter-error").hidden = !invalid;
  $("filter-error").textContent = invalid
    ? "La date de début doit précéder ou égaler la date de fin."
    : "";
  visible = RescueModel.filterEvents(data, { from, to, ship: $("ship").value });
  if (!visible.some((e) => e.id === selected)) selected = null;
  $("summary").textContent =
    visible.length +
    " événements fictifs • " +
    visible.reduce((sum, e) => sum + e.people, 0) +
    " personnes fictives";
  $("count").textContent = visible.length;
  $("events").replaceChildren();
  $("markers").replaceChildren();
  $("detail").replaceChildren();
  $("export").disabled = !visible.length;
  if (!visible.length)
    text(
      "p",
      "Aucun événement pour ces filtres. Effacez les filtres ou importez un autre exemple.",
      $("events"),
      "empty",
    );
  for (const e of visible) {
    const b = text("button", "", $("events"), "event");
    b.dataset.eventId = e.id;
    b.type = "button";
    b.setAttribute("aria-pressed", String(selected === e.id));
    const s = text("span", "", b);
    text("strong", e.date, s);
    text("small", e.ship + " · " + e.id, s);
    text("span", e.people + " pers. fictives", b);
    b.addEventListener("click", () => choose(e.id, true));
    const [x, y] = project([e.longitude, e.latitude]);
    const marker = svg(
      "circle",
      {
        cx: x,
        cy: y,
        r: 8 + Math.sqrt(e.people) * 0.7,
        class: "marker" + (selected === e.id ? " selected" : ""),
        "data-id": e.id,
      },
      $("markers"),
    );
    svg("title", {}, marker).textContent = e.date + " • " + e.id + " • fictif";
    marker.addEventListener("click", () => choose(e.id));
  }
  const e = visible.find((e) => e.id === selected);
  if (e) {
    text("h3", e.id + " · Données fictives", $("detail"));
    text("p", e.date + " | " + e.ship, $("detail"));
    text("p", e.people + " personnes fictives", $("detail"));
    text(
      "p",
      e.latitude.toFixed(3) + "° N, " + e.longitude.toFixed(3) + "° E",
      $("detail"),
    );
    text("p", e.note, $("detail"));
    const link = text("a", "Source déclarée de l’exemple ↗", $("detail"));
    link.href = e.source;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    text(
      "p",
      "Ce lien est une référence déclarée, pas une preuve d’opération réelle.",
      $("detail"),
    );
  } else {
    text(
      "p",
      "Sélectionnez un événement dans la liste ou sur la carte.",
      $("detail"),
    );
  }
  setZoom(zoom);
}
function choose(id, restoreFocus = false) {
  selected = id;
  render();
  if (restoreFocus) {
    const button = [...$("events").children].find(
      (el) => el.dataset.eventId === id,
    );
    button?.focus();
  }
}
function clear() {
  for (const id of ["from", "to", "ship"]) $(id).value = "";
  selected = null;
  setZoom(1);
  render();
}
$("filters").addEventListener("submit", (e) => e.preventDefault());
for (const id of ["from", "to", "ship"])
  $(id).addEventListener("change", render);
$("clear").onclick = clear;
$("zoom-in").onclick = () => setZoom(zoom * 1.5);
$("zoom-out").onclick = () => setZoom(zoom / 1.5);
$("extent").onclick = () => setZoom(1);
$("import").addEventListener("change", async (e) => {
  const f = e.target.files[0];
  if (!f) return;
  const generation = ++importGeneration;
  $("import-error").hidden = true;
  try {
    if (f.size > 2 * 1024 * 1024)
      throw Error("Fichier trop volumineux : maximum 2 Mio.");
    const contents = await f.text();
    if (generation !== importGeneration) return;
    const next = RescueModel.validate(JSON.parse(contents));
    data = next;
    ships();
    clear();
    $("import-status").textContent =
      next.length +
      " exemples fictifs importés localement. Recharger la page restaure la démo.";
  } catch (err) {
    if (generation !== importGeneration) return;
    $("import-error").hidden = false;
    $("import-error").textContent =
      "Import refusé : " + err.message + " Le jeu précédent est conservé.";
    $("import-status").textContent = "";
  } finally {
    e.target.value = "";
  }
});
$("restore").onclick = () => {
  importGeneration++;
  data = RescueModel.validate(DEMO);
  ships();
  clear();
  $("import-error").hidden = true;
  $("import-status").textContent =
    "Les 6 événements fictifs de démonstration sont restaurés.";
};
$("export").onclick = () => {
  const url = URL.createObjectURL(
    new Blob([JSON.stringify(visible, null, 2)], { type: "application/json" }),
  );
  const a = document.createElement("a");
  a.href = url;
  a.download = "evenements-fictifs.json";
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
};
ships();
render();
