<script setup lang="ts">
import { onMounted, ref } from 'vue'
import OperationsMap from '@/components/OperationsMap.vue'
import StatusBanner from '@/components/StatusBanner.vue'
import { fetchOperations, type Operation } from '@/operations'

// La page de la carte. Elle charge les opérations une fois, puis les passe au bandeau et à la
// carte : chacun a son fichier dans components/, pour qu'on puisse y travailler séparément.

// null pendant le chargement, puis la liste des opérations publiées ou un message d'erreur.
const operations = ref<Operation[] | null>(null)
const error = ref<string | null>(null)

// onMounted : Vue appelle cette fonction quand la page est affichée.
onMounted(async () => {
  try {
    operations.value = await fetchOperations()
  } catch (reason) {
    error.value = String(reason)
  }
})
</script>

<template>
  <main>
    <StatusBanner :operations="operations" :error="error" />
    <OperationsMap :operations="operations" />
  </main>
</template>

<style scoped>
main {
  display: grid;
  grid-template-rows: auto 1fr;
  height: 100dvh;
}
</style>
