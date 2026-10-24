import { useEffect, useEffectEvent, useRef, useState } from "react";
import { Map as LibreMap, NavigationControl, setWorkerUrl, type GeoJSONSource } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import workerUrl from "maplibre-gl/dist/maplibre-gl-worker.mjs?url";
import type { MapPoints as Points } from "../api/client";
import { useI18n } from "../i18n/I18nProvider";

setWorkerUrl(workerUrl);

function supportsWebGL(): boolean {
  try {
    const canvas = document.createElement("canvas");
    const context = canvas.getContext("webgl2") ?? canvas.getContext("webgl");
    // Release the probe context: browsers cap the number of live WebGL contexts.
    context?.getExtension("WEBGL_lose_context")?.loseContext();
    return context !== null;
  } catch {
    return false;
  }
}

function asFeatures(points: Points) {
  return {
    type: "FeatureCollection" as const,
    features: points.map((p) => ({
      type: "Feature" as const,
      geometry: { type: "Point" as const, coordinates: [p.longitude, p.latitude] },
      properties: { id: p.id, kind: p.kind },
    })),
  };
}

export function EventMap({
  points,
  onSelect,
  activeId = null,
}: {
  points: Points;
  onSelect: (id: string) => void;
  /** The event open in the list: ringed on the map and brought into view. */
  activeId?: string | null;
}) {
  const { t } = useI18n();
  const element = useRef<HTMLDivElement>(null);
  const [map, setMap] = useState<LibreMap | null>(null);
  // Checked once before the map exists, so a missing WebGL never needs a state update in an effect.
  const [failed, setFailed] = useState(() => !supportsWebGL());
  // A non-fatal map error (a tile or source fetch) keeps the map and only shows the notice.
  const [degraded, setDegraded] = useState(false);
  // Map listeners always call the latest callbacks without re-creating the map.
  const select = useEffectEvent((id: string) => onSelect(id));
  const fail = useEffectEvent(() => setFailed(true));
  const degrade = useEffectEvent(() => setDegraded(true));
  // Read once at creation: changing language must not rebuild the map and lose the view.
  const attribution = useEffectEvent(() => t("map.attribution"));

  useEffect(() => {
    if (failed || !element.current) return;
    let instance: LibreMap;
    try {
      instance = new LibreMap({
        container: element.current,
        center: [15, 35.5],
        zoom: 4,
        maxBounds: [
          [-15, 20],
          [50, 55],
        ],
        style: {
          version: 8,
          sources: { land: { type: "geojson", data: "/land.geojson" } },
          layers: [
            { id: "water", type: "background", paint: { "background-color": "#dfe3ee" } },
            { id: "land", type: "fill", source: "land", paint: { "fill-color": "#fbfbfd" } },
            { id: "coast", type: "line", source: "land", paint: { "line-color": "#a9afc4", "line-width": 0.8 } },
          ],
        },
        attributionControl: { customAttribution: attribution() },
      });
    } catch {
      // The external map failed to start (WebGL lost, driver refusal): report it like any
      // other map event, outside the effect body, and keep the list usable.
      queueMicrotask(fail);
      return;
    }
    instance.addControl(new NavigationControl({ showCompass: false }), "top-left");
    let loaded = false;
    instance.on("load", () => {
      loaded = true;
      instance.addSource("events", {
        type: "geojson",
        data: { type: "FeatureCollection", features: [] },
        cluster: true,
        clusterMaxZoom: 8,
        clusterRadius: 35,
      });
      instance.addLayer({
        id: "clusters",
        type: "circle",
        source: "events",
        filter: ["has", "point_count"],
        // Larger groups read larger, in three steps.
        paint: {
          "circle-color": "#1b2747",
          "circle-opacity": 0.92,
          "circle-radius": ["step", ["get", "point_count"], 13, 10, 17, 50, 22],
          "circle-stroke-color": "white",
          "circle-stroke-width": 2,
        },
      });
      instance.addLayer({
        id: "events",
        type: "circle",
        source: "events",
        filter: ["!", ["has", "point_count"]],
        paint: { "circle-color": "#e83e1b", "circle-radius": 6, "circle-stroke-color": "white", "circle-stroke-width": 2 },
      });
      instance.addSource("active", { type: "geojson", data: { type: "FeatureCollection", features: [] } });
      instance.addLayer({
        id: "active",
        type: "circle",
        source: "active",
        paint: {
          "circle-color": "rgba(232, 62, 27, 0.18)",
          "circle-radius": 16,
          "circle-stroke-color": "#e83e1b",
          "circle-stroke-width": 2.5,
        },
      });
      instance.on("click", "events", (e) => {
        const id = e.features?.[0]?.properties?.id;
        if (typeof id === "string") select(id);
      });
      instance.on("click", "clusters", (e) => {
        const feature = e.features?.[0];
        if (feature?.geometry.type === "Point") {
          const [lon, lat] = feature.geometry.coordinates;
          instance.easeTo({ center: [lon ?? 15, lat ?? 35], zoom: Math.min(instance.getZoom() + 2, 10) });
        }
      });
      instance.on("mouseenter", "events", () => {
        instance.getCanvas().style.cursor = "pointer";
      });
      instance.on("mouseleave", "events", () => {
        instance.getCanvas().style.cursor = "";
      });
      setMap(instance);
    });
    // Before load the map cannot work (style or WebGL failure); after load it degrades only.
    instance.on("error", () => (loaded ? degrade() : fail()));
    return () => {
      setMap(null);
      instance.remove();
    };
  }, [failed]);

  // Points are pushed to the loaded map whenever they change.
  useEffect(() => {
    map?.getSource<GeoJSONSource>("events")?.setData(asFeatures(points));
  }, [map, points]);

  // The open event is ringed and brought into view; nothing moves when it is already visible.
  useEffect(() => {
    if (!map) return;
    const active = points.filter((point) => point.id === activeId);
    map.getSource<GeoJSONSource>("active")?.setData(asFeatures(active));
    const point = active[0];
    if (point && !map.getBounds().contains([point.longitude, point.latitude])) {
      const reduce = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
      map.easeTo({ center: [point.longitude, point.latitude], duration: reduce ? 0 : 700 });
    }
  }, [map, points, activeId]);

  return (
    <div className="map-wrap">
      <div ref={element} className="map" role="region" aria-label={t("map.label")} />
      {(failed || degraded) && (
        <p role="status" className="map-notice">
          {t("map.unavailable")}
        </p>
      )}
      <span className="map-caption">{t("map.caption")}</span>
    </div>
  );
}
