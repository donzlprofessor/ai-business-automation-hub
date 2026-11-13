<script setup lang="ts">
import { ArrowDown, ArrowUp, ArrowUpDown, ArrowUpRight } from 'lucide-vue-next'
import type { Inquiry, SortField } from '../api'
import { dateTime } from '../format'
import StatusBadge from './StatusBadge.vue'

const props = defineProps<{
  items: Inquiry[]; sortBy?: SortField; sortDir?: 'asc' | 'desc'; compact?: boolean
}>()
defineEmits<{ select: [id: string]; sort: [field: SortField] }>()
const sortIcon = (field: SortField) => props.sortBy !== field ? ArrowUpDown
  : props.sortDir === 'asc' ? ArrowUp : ArrowDown
const ariaSort = (field: SortField) => props.sortBy !== field ? 'none'
  : props.sortDir === 'asc' ? 'ascending' : 'descending'
</script>

<template>
  <div class="table-scroll" tabindex="0" role="region" aria-label="Inquiry table, scroll horizontally on smaller screens">
    <table>
      <caption class="sr-only">Customer inquiries. Open an inquiry to read its message and summary.</caption>
      <thead><tr>
        <th :aria-sort="ariaSort('customer_name')">
          <button v-if="!compact" class="sort-button" @click="$emit('sort', 'customer_name')">
            Customer <component :is="sortIcon('customer_name')" :size="13" aria-hidden="true" />
          </button><span v-else>Customer</span>
        </th>
        <th>Category</th>
        <th :aria-sort="ariaSort('priority')">
          <button v-if="!compact" class="sort-button" @click="$emit('sort', 'priority')">
            Priority <component :is="sortIcon('priority')" :size="13" aria-hidden="true" />
          </button><span v-else>Priority</span>
        </th>
        <th>Status</th>
        <th :aria-sort="ariaSort('created_at')">
          <button v-if="!compact" class="sort-button" @click="$emit('sort', 'created_at')">
            Received <component :is="sortIcon('created_at')" :size="13" aria-hidden="true" />
          </button><span v-else>Received</span>
        </th>
        <th><span class="sr-only">Details</span></th>
      </tr></thead>
      <tbody>
        <tr v-for="inquiry in items" :key="inquiry.id">
          <td><div class="customer-cell">
            <span class="avatar" aria-hidden="true">{{ inquiry.customer_name.slice(0, 1).toUpperCase() }}</span>
            <div><button class="customer-name" @click="$emit('select', inquiry.id)">{{ inquiry.customer_name }}</button>
              <span class="customer-email">{{ inquiry.email }}</span></div>
          </div></td>
          <td><StatusBadge :value="inquiry.category" kind="category" /></td>
          <td><StatusBadge :value="inquiry.priority" kind="priority" /></td>
          <td><StatusBadge :value="inquiry.status" kind="status" /></td>
          <td class="date-cell">{{ dateTime(inquiry.created_at) }}</td>
          <td><button class="icon-button" :aria-label="`View inquiry from ${inquiry.customer_name}`"
            @click="$emit('select', inquiry.id)"><ArrowUpRight :size="17" aria-hidden="true" /></button></td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
