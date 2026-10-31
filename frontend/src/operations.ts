// Les opérations publiées, lues dans l'API Django (backend/operations/views.py).
// Les types ci-dessous décrivent exactement le JSON renvoyé par /api/operations/.
import type { FeatureCollection, Point } from 'geojson'

export type Kind = 'rescue' | 'transfer' | 'medevac' | 'incident' | 'shipwreck' | 'dead_missing'

export interface Operation {
  id: number
  kind: Kind
  occurred_on: string
  title: string
  people: number | null
  latitude: number | null
  longitude: number | null
  source_url: string
}

/** Demande les opérations à l'API. En cas d'erreur, la page affiche un message. */
export async function fetchOperations(): Promise<Operation[]> {
  const response = await fetch('/api/operations/')
  if (!response.ok) throw new Error(`API answered ${response.status}`)
  const body: { operations: Operation[] } = await response.json()
  return body.operations
}

/**
 * Transforme les opérations en points GeoJSON, le format que lit MapLibre.
 * Une opération sans position connue n'a pas de point : inconnu n'est jamais zéro.
 */
export function toPoints(operations: Operation[]): FeatureCollection<Point> {
  return {
    type: 'FeatureCollection',
    features: operations
      .filter((operation) => operation.latitude !== null && operation.longitude !== null)
      .map((operation) => ({
        type: 'Feature',
        id: operation.id,
        geometry: { type: 'Point', coordinates: [operation.longitude!, operation.latitude!] },
        properties: { kind: operation.kind, title: operation.title },
      })),
  }
}
