<script setup lang="ts">
import type { Operation } from '@/operations'

// Le bandeau en haut de la page : le titre et l'état du chargement des opérations.
// Il reçoit tout de la page (MapView.vue) et ne demande rien à l'API lui-même.
defineProps<{
  // null pendant le chargement, puis la liste des opérations publiées.
  operations: Operation[] | null
  // Le message d'erreur si le chargement a échoué, sinon null.
  error: string | null
}>()
</script>

<template>
  <header>
    <h1>SOS MEDITERRANEE operations</h1>
    <p v-if="error" role="alert">The operations could not be loaded ({{ error }}).</p>
    <p v-else-if="operations === null" role="status">Loading the operations…</p>
    <p v-else role="status">{{ operations.length }} published operations</p>
  </header>
</template>

<style scoped>
header {
  padding: var(--space-3) var(--space-4);
  background: var(--color-brand);
  color: var(--color-on-brand);
}

h1 {
  margin: 0;
  font-size: 1.25rem;
}

p {
  margin: var(--space-1) 0 0;
}
</style>
