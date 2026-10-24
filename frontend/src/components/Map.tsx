import { useEffect, useRef, useState } from "react";
import {
  Map as LibreMap,
  NavigationControl,
  setWorkerUrl,
  type GeoJSONSource,
} from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import workerUrl from "maplibre-gl/dist/maplibre-gl-worker.mjs?url";
setWorkerUrl(workerUrl);
import type { ExploreQuery } from "../gql/graphql";
type Points = ExploreQuery["mapPoints"]["points"];
export function EventMap({
  points,
  onSelect,
}: {
  points: Points;
  onSelect: (id: string) => void;
}) {
  const element = useRef<HTMLDivElement>(null),
    map = useRef<LibreMap | null>(null),
    selection = useRef(onSelect);
  const [failed, setFailed] = useState(false);
  selection.current = onSelect;
  useEffect(() => {
    if (!element.current) return;
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
            {
              id: "water",
              type: "background",
              paint: { "background-color": "#dceaf0" },
            },
            {
              id: "land",
              type: "fill",
              source: "land",
              paint: { "fill-color": "#f8faf9" },
            },
            {
              id: "coast",
              type: "line",
              source: "land",
              paint: { "line-color": "#94b1bf", "line-width": 1 },
            },
          ],
        },
        attributionControl: {
          customAttribution: "Natural Earth (domaine public)",
        },
      });
    } catch {
      setFailed(true);
      return;
    }
    map.current = instance;
    instance.addControl(
      new NavigationControl({ showCompass: false }),
      "top-left",
    );
    instance.on("load", () => {
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
        paint: {
          "circle-color": "#194b65",
          "circle-radius": 18,
          "circle-stroke-color": "white",
          "circle-stroke-width": 2,
        },
      });
      instance.addLayer({
        id: "events",
        type: "circle",
        source: "events",
        filter: ["!", ["has", "point_count"]],
        paint: {
          "circle-color": "#bc471c",
          "circle-radius": 7,
          "circle-stroke-color": "white",
          "circle-stroke-width": 2,
        },
      });
      instance.on("click", "events", (e) => {
        const id = e.features?.[0]?.properties?.id;
        if (typeof id === "string") selection.current(id);
      });
      instance.on("click", "clusters", (e) => {
        const feature = e.features?.[0];
        if (feature?.geometry.type === "Point") {
          const coordinates = feature.geometry.coordinates;
          instance.easeTo({
            center: [coordinates[0] ?? 15, coordinates[1] ?? 35],
            zoom: Math.min(instance.getZoom() + 2, 10),
          });
        }
      });
      instance.on("mouseenter", "events", () => {
        instance.getCanvas().style.cursor = "pointer";
      });
      instance.on("mouseleave", "events", () => {
        instance.getCanvas().style.cursor = "";
      });
      sync();
    });
    instance.on("error", () => setFailed(true));
    function sync() {
      const source = instance.getSource<GeoJSONSource>("events");
      if (source)
        source.setData({
          type: "FeatureCollection",
          features: pointsRef.current.map((p) => ({
            type: "Feature",
            geometry: { type: "Point", coordinates: [p.longitude, p.latitude] },
            properties: { id: p.id, kind: p.kind },
          })),
        });
    }
    syncRef.current = sync;
    return () => {
      syncRef.current = () => {};
      instance.remove();
      map.current = null;
    };
  }, []);
  const pointsRef = useRef(points),
    syncRef = useRef(() => {});
  pointsRef.current = points;
  useEffect(() => syncRef.current(), [points]);
  return (
    <div className="map-wrap">
      <div
        ref={element}
        className="map"
        role="region"
        aria-label="Carte des événements. La liste permet aussi de consulter chaque événement."
      />
      {failed && (
        <p role="status" className="map-notice">
          Le fond de carte est indisponible. Les événements restent consultables
          dans la liste.
        </p>
      )}
      <span className="map-caption">Méditerranée • carte historique</span>
    </div>
  );
}
