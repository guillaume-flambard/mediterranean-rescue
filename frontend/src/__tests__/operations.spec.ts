import { describe, it, expect } from 'vitest'
import { toPoints, type Operation } from '../operations'

// Tests unitaires, lancés par `pnpm test:unit`. Opérations fictives, jamais de données réelles.
const located: Operation = {
  id: 1,
  kind: 'rescue',
  occurred_on: '2026-01-12',
  title: 'FICTIONAL located',
  people: 18,
  latitude: 35.1,
  longitude: 12.6,
  source_url: 'https://example.org/fictional/1',
}
const unlocated: Operation = { ...located, id: 2, latitude: null, longitude: null }

describe('toPoints', () => {
  it('puts a pin at longitude, latitude', () => {
    expect(toPoints([located]).features[0]!.geometry.coordinates).toEqual([12.6, 35.1])
  })

  it('gives no pin to an operation with an unknown position', () => {
    expect(toPoints([located, unlocated]).features).toHaveLength(1)
  })
})
