<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { ChevronLeft, ChevronRight, Search, SlidersHorizontal, X } from 'lucide-vue-next'
import { useRoute, useRouter } from 'vue-router'
import type { InquiryQuery, SortField } from '../api'
import { defaultQuery } from '../api'
import { number } from '../format'
import { parseQuery } from '../query'
import { useInquiries } from '../stores/inquiries'
import InquiryTable from '../components/InquiryTable.vue'
import InquiryDetail from '../components/InquiryDetail.vue'
import StateBlock from '../components/StateBlock.vue'

const route = useRoute()
const router = useRouter()
const store = useInquiries()
const query = computed(() => {
  const parsed = parseQuery(route.query)
  return { ...parsed, limit: Number(parsed.limit) }
})
const search = ref(query.value.search)
const selected = computed(() => typeof route.query.selected === 'string' ? route.query.selected : '')
const hasFilters = computed(() => Boolean(query.value.search || query.value.category || query.value.priority || query.value.status))
const currentPage = computed(() => Math.floor(query.value.offset / query.value.limit) + 1)
const pageCount = computed(() => Math.max(1, Math.ceil((store.page?.total ?? 0) / query.value.limit)))
let timer: ReturnType<typeof setTimeout> | undefined

function update(values: Partial<InquiryQuery>, replace = false) {
  const next = { ...query.value, search: search.value.trim(), offset: 0, ...values }
  const entries = Object.fromEntries(Object.entries(next).filter(([key, value]) =>
    value !== '' && value !== defaultQuery[key as keyof InquiryQuery],
  ).map(([key, value]) => [key, String(value)]))
  void router[replace ? 'replace' : 'push']({ query: entries })
}
function searchInput(event: Event) {
  search.value = (event.target as HTMLInputElement).value
  clearTimeout(timer)
  timer = setTimeout(() => { update({ search: search.value.trim() }, true) }, 300)
}
function setFilter(field: 'category' | 'priority' | 'status' | 'limit', event: Event) {
  const value = (event.target as HTMLSelectElement).value
  update({ [field]: field === 'limit' ? Number(value) : value })
}
function sort(field: SortField) {
  update({ sort_by: field, sort_dir: query.value.sort_by === field && query.value.sort_dir === 'desc' ? 'asc' : 'desc' })
}
function reset() { search.value = ''; clearTimeout(timer); void router.push({ query: {} }) }
async function load() {
  await store.loadPage(query.value)
  if (store.page && query.value.offset > 0 && query.value.offset >= store.page.total) {
    const next = { ...route.query }
    const offset = Math.max(0, Math.ceil(store.page.total / query.value.limit) - 1) * query.value.limit
    if (offset) next.offset = String(offset)
    else delete next.offset
    void router.replace({ query: next })
  }
}
watch(() => JSON.stringify(query.value), () => {
  clearTimeout(timer)
  search.value = query.value.search
  void load()
}, { immediate: true })
watch(() => store.refreshKey, load)
onBeforeUnmount(() => { clearTimeout(timer) })
function closeDetail() {
  const next = { ...route.query }
  delete next.selected
  void router.replace({ query: next })
}
</script>

<template>
  <section class="panel inbox-panel">
    <header class="panel-heading"><div class="inbox-title"><h2>All inquiries</h2><span v-if="store.page" class="count-pill">{{ number(store.page.total) }}</span></div><span class="mini-label">CUSTOMER INBOX</span></header>
    <div class="filter-bar"><div class="search-input"><Search :size="17" aria-hidden="true" /><label class="sr-only" for="inquiry-search">Search inquiries</label>
      <input id="inquiry-search" :value="search" maxlength="200" type="search" placeholder="Search names, emails, or messages…" @input="searchInput" /></div>
      <div class="filter-controls"><SlidersHorizontal class="filter-symbol" :size="16" aria-hidden="true" />
        <label class="sr-only" for="category-filter">Category</label><select id="category-filter" :value="query.category" @change="setFilter('category', $event)"><option value="">All categories</option><option value="sales">Sales</option><option value="support">Support</option><option value="other">Other</option><option value="unclassified">Unclassified</option></select>
        <label class="sr-only" for="priority-filter">Priority</label><select id="priority-filter" :value="query.priority" @change="setFilter('priority', $event)"><option value="">All priorities</option><option value="high">High</option><option value="medium">Medium</option><option value="low">Low</option></select>
        <label class="sr-only" for="status-filter">Status</label><select id="status-filter" :value="query.status" @change="setFilter('status', $event)"><option value="">All statuses</option><option value="new">New</option><option value="in_progress">In progress</option><option value="resolved">Resolved</option></select>
      </div>
    </div>
    <div v-if="hasFilters" class="active-filters"><span>Showing filtered results</span><button class="text-button" @click="reset"><X :size="13" />Clear filters</button></div>
    <div :aria-busy="store.loading">
      <StateBlock v-if="store.loading" kind="loading" title="Loading inquiries" description="Getting the latest conversations from your workspace." />
      <StateBlock v-else-if="store.error" kind="error" title="Could not load inquiries" :description="store.error" @retry="load" />
      <StateBlock v-else-if="!store.page?.items.length" kind="empty" :title="hasFilters ? 'No matching inquiries' : 'Your inbox is ready'" :description="hasFilters ? 'Try a different search or clear your filters.' : 'Customer inquiries will appear here when they arrive through your API.'">
        <button v-if="hasFilters" class="button" @click="reset">Clear filters</button>
      </StateBlock>
      <InquiryTable v-else :items="store.page.items" :sort-by="query.sort_by" :sort-dir="query.sort_dir"
        @sort="sort" @select="id => router.push({ query: { ...route.query, selected: id } })" />
    </div>
    <footer class="pagination"><div class="page-size"><label for="page-size">Rows per page</label><select id="page-size" :value="query.limit" @change="setFilter('limit', $event)"><option :value="10">10</option><option :value="20">20</option><option :value="50">50</option><option :value="100">100</option></select></div>
      <span class="pagination-count" role="status">{{ store.page ? `${number(store.page.total ? query.offset + 1 : 0)}–${number(query.offset + store.page.items.length)} of ${number(store.page.total)}` : '—' }}</span>
      <div class="pagination-buttons"><button class="icon-button" aria-label="Previous page" :disabled="store.loading || !store.page || query.offset === 0" @click="update({ offset: Math.max(0, query.offset - query.limit) })"><ChevronLeft :size="17" /></button>
        <span>Page {{ currentPage }} of {{ pageCount }}</span><button class="icon-button" aria-label="Next page" :disabled="store.loading || !store.page || query.offset + query.limit >= store.page.total" @click="update({ offset: query.offset + query.limit })"><ChevronRight :size="17" /></button></div>
    </footer>
  </section>
  <p class="inbox-note">Search covers customer names, email addresses, messages, and AI summaries. All times are local.</p>
  <InquiryDetail v-if="selected" :id="selected" @close="closeDetail" @updated="store.refresh" />
</template>
