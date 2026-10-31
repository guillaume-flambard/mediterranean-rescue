<script setup lang="ts">
import { Map, setWorkerUrl, type GeoJSONSource } from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url'
import { onMounted, onUnmounted, useTemplateRef, watch } from 'vue'
import { toPoints, type Operation } from '@/operations'

// Réglage demandé par la doc MapLibre pour Vite : indiquer où trouver son « worker »
// (le script qui prépare la carte en arrière-plan). https://maplibre.org/maplibre-gl-js/docs/
setWorkerUrl(workerUrl)

// La carte reçoit les opérations de la page (MapView.vue) : null tant qu'elles chargent.
const props = defineProps<{ operations: Operation[] | null }>()

// La balise <div ref="map-container"> du gabarit, dans laquelle MapLibre dessine la carte.
// Ce nom ne doit reprendre aucune variable du script (comme `map` plus bas) : sinon, une fois
// l'app construite, Vue relie la balise à cette variable et useTemplateRef renvoie null.
const container = useTemplateRef('map-container')
let map: Map | undefined

// Les couleurs viennent des jetons de assets/main.css : la carte et la page partagent les mêmes.
function token(name: string) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim()
}

// Met les opérations sur la carte : la première fois on crée la couche, ensuite on la met à jour.
function showOperations(operations: Operation[]) {
  const points = toPoints(operations)
  const source = map!.getSource<GeoJSONSource>('operations')
  if (source) {
    source.setData(points)
    return
  }
  map!.addSource('operations', { type: 'geojson', data: points })
  map!.addLayer({
    id: 'operations',
    type: 'circle',
    source: 'operations',
    paint: {
      'circle-radius': 6,
      'circle-color': token('--color-accent'),
      'circle-stroke-width': 1.5,
      'circle-stroke-color': token('--color-surface'),
    },
  })
}

// onMounted : Vue appelle cette fonction quand la balise de la carte existe.
onMounted(() => {
  map = new Map({
    container: container.value!,
    // Aucun service extérieur : le contour des terres est servi par l'app
    // (frontend/public/land.geojson, Natural Earth, domaine public).
    style: {
      version: 8,
      sources: { land: { type: 'geojson', data: '/land.geojson' } },
      layers: [
        { id: 'water', type: 'background', paint: { 'background-color': token('--color-water') } },
        { id: 'land', type: 'fill', source: 'land', paint: { 'fill-color': token('--color-land') } },
      ],
    },
    // Centre de départ [longitude, latitude] : la Méditerranée centrale.
    center: [13.5, 35],
    zoom: 5,
  })

  // Dès que les opérations sont là, et à chaque changement, on met la carte à jour.
  // La carte peut ne pas avoir fini de charger son style : on attend alors l'événement « load ».
  watch(
    () => props.operations,
    (operations) => {
      if (operations === null) return
      if (map!.loaded()) showOperations(operations)
      else map!.once('load', () => showOperations(operations))
    },
    { immediate: true },
  )
})

// Quand on quitte la page, on libère la carte.
onUnmounted(() => map?.remove())
</script>

<template>
  <div ref="map-container" class="map" />
</template>
