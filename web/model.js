(function (root) {
  "use strict";
  function validate(data) {
    if (!Array.isArray(data) || data.length > 2000)
      throw Error("Un tableau JSON de 0 à 2 000 événements est attendu.");
    const ids = new Set();
    return data.map((e, i) => {
      const fail = (message) => {
        throw Error("Ligne " + (i + 1) + " : " + message);
      };
      if (!e || typeof e !== "object" || Array.isArray(e))
        fail("objet attendu.");
      for (const key of ["id", "date", "ship", "source", "note"])
        if (
          typeof e[key] !== "string" ||
          !e[key].trim() ||
          e[key].length > 2000
        )
          fail(
            key + " doit être un texte non vide (2 000 caractères maximum).",
          );
      if (ids.has(e.id)) fail("identifiant dupliqué.");
      ids.add(e.id);
      if (
        !/^\d{4}-\d{2}-\d{2}$/.test(e.date) ||
        !Number.isFinite(Date.parse(e.date)) ||
        new Date(e.date).toISOString().slice(0, 10) !== e.date
      )
        fail("date calendaire YYYY-MM-DD invalide.");
      if (
        !Number.isFinite(e.longitude) ||
        e.longitude < -6 ||
        e.longitude > 40 ||
        !Number.isFinite(e.latitude) ||
        e.latitude < 30 ||
        e.latitude > 46
      )
        fail("coordonnées hors du cadre méditerranéen (-6 à 40°, 30 à 46°).");
      if (!Number.isSafeInteger(e.people) || e.people < 0 || e.people > 10000)
        fail("people doit être un entier de 0 à 10 000.");
      try {
        const u = new URL(e.source);
        if (
          !["https:", "http:"].includes(u.protocol) ||
          u.username ||
          u.password
        )
          fail("URL HTTP/S publique attendue.");
      } catch {
        fail("URL HTTP/S publique attendue.");
      }
      if (e.synthetic !== true)
        fail(
          "ce POC accepte uniquement des données fictives (synthetic: true).",
        );
      return Object.fromEntries(
        [
          "id",
          "date",
          "longitude",
          "latitude",
          "people",
          "ship",
          "source",
          "note",
          "synthetic",
        ].map((k) => [k, e[k]]),
      );
    });
  }
  function filterEvents(data, { from = "", to = "", ship = "" } = {}) {
    return data
      .filter(
        (e) =>
          (!from || e.date >= from) &&
          (!to || e.date <= to) &&
          (!ship || e.ship === ship),
      )
      .sort((a, b) => b.date.localeCompare(a.date) || a.id.localeCompare(b.id));
  }
  const api = { validate, filterEvents };
  if (typeof module !== "undefined") module.exports = api;
  else root.RescueModel = api;
})(typeof window === "undefined" ? globalThis : window);
