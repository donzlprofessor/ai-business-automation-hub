<script setup lang="ts">
import { Inbox, AlertCircle, LoaderCircle } from 'lucide-vue-next'
defineProps<{ kind: 'loading' | 'error' | 'empty'; title: string; description?: string }>()
defineEmits<{ retry: [] }>()
</script>

<template>
  <div class="state-block" :role="kind === 'error' ? 'alert' : 'status'">
    <component :is="kind === 'loading' ? LoaderCircle : kind === 'error' ? AlertCircle : Inbox"
      :size="28" :class="{ spin: kind === 'loading' }" aria-hidden="true" />
    <h3>{{ title }}</h3>
    <p v-if="description">{{ description }}</p>
    <button v-if="kind === 'error'" class="button" @click="$emit('retry')">Try again</button>
    <slot />
  </div>
</template>
