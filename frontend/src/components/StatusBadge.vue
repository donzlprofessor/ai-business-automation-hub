<script setup lang="ts">
import { label } from '../format'
defineProps<{ value: string | null; kind?: 'priority' | 'status' | 'category' }>()
</script>

<template>
  <span class="badge" :class="[kind, value || 'unclassified']">
    <span class="badge-dot" aria-hidden="true"></span>{{ label(value) }}
  </span>
</template>
