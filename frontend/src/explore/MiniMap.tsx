import { MED_BOUNDS, MED_LAND, MED_SCALE, MED_VIEWBOX } from "../shared/medOutline";

/** Where a point falls on the central Mediterranean locator, or null outside it. */
function place(longitude: number, latitude: number) {
  const { west, east, south, north } = MED_BOUNDS;
  if (longitude < west || longitude > east || latitude < south || latitude > north) return null;
  return { x: (longitude - west) * MED_SCALE, y: north - latitude };
}

// A static locator drawn from the same coastline as the map: no WebGL, cheap enough for every card.
export function MiniMap({ position, label }: { position: { longitude: number; latitude: number } | null; label: string }) {
  const point = position ? place(position.longitude, position.latitude) : null;
  return (
    <svg className="mini-map" viewBox={MED_VIEWBOX} role="img" aria-label={label} preserveAspectRatio="xMidYMid slice">
      <path className="mini-map__land" d={MED_LAND} />
      {point && (
        <>
          <circle className="mini-map__halo" cx={point.x} cy={point.y} r={1.4} />
          <circle className="mini-map__dot" cx={point.x} cy={point.y} r={0.55} />
        </>
      )}
    </svg>
  );
}
