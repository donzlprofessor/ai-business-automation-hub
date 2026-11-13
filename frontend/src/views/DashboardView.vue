<script setup lang="ts">
import { computed, watch } from 'vue'
import { ArrowRight, ArrowUpRight, Headphones, Inbox, ShoppingBag, Zap } from 'lucide-vue-next'
import { useRoute, useRouter } from 'vue-router'
import { defaultQuery } from '../api'
import { number } from '../format'
import { useInquiries } from '../stores/inquiries'
import InquiryTable from '../components/InquiryTable.vue'
import InquiryDetail from '../components/InquiryDetail.vue'
import StateBlock from '../components/StateBlock.vue'

const store = useInquiries()
const route = useRoute()
const router = useRouter()
const selected = computed(() => typeof route.query.selected === 'string' ? route.query.selected : '')
const cards = computed(() => [
  { label: 'Total inquiries', value: store.stats?.total, icon: Inbox, note: 'All customer conversations', query: {} },
  { label: 'High priority', value: store.stats?.high_priority, icon: Zap, note: 'Conversations to focus on', query: { priority: 'high' }, accent: true },
  { label: 'Sales inquiries', value: store.stats?.sales, icon: ShoppingBag, note: 'New opportunities to explore', query: { category: 'sales' } },
  { label: 'Support inquiries', value: store.stats?.support, icon: Headphones, note: 'Customers looking for help', query: { category: 'support' } },
])
const categories = computed(() => [
  { name: 'Sales', count: store.stats?.sales ?? 0, color: 'teal', category: 'sales' },
  { name: 'Support', count: store.stats?.support ?? 0, color: 'blue', category: 'support' },
  { name: 'Other', count: store.stats?.other ?? 0, color: 'violet', category: 'other' },
  { name: 'Unclassified', count: store.stats?.unclassified ?? 0, color: 'gray', category: 'unclassified' },
])
const percent = (count: number) => store.stats?.total ? Math.round(count / store.stats.total * 100) : 0
async function loadRecent() { await store.loadPage({ ...defaultQuery, limit: 5 }) }
watch(() => store.refreshKey, loadRecent, { immediate: true })
function closeDetail() {
  const query = { ...route.query }
  delete query.selected
  void router.replace({ query })
}
</script>

<template>
  <div class="section-caption"><span class="live-dot"></span>ALL-TIME SNAPSHOT<span class="caption-line"></span><span>Live inquiry data</span></div>
  <div v-if="store.statsError" class="inline-error" role="alert"><span>{{ store.statsError }}</span><button class="text-button" @click="store.loadStats()">Retry connection</button></div>
  <div class="metrics-grid" :aria-busy="store.statsLoading">
    <RouterLink v-for="card in cards" :key="card.label" :to="{ path: '/inquiries', query: card.query }" class="metric-card" :class="{ accented: card.accent }">
      <div class="metric-top"><span>{{ card.label }}</span><component :is="card.icon" :size="18" aria-hidden="true" /></div>
      <div class="metric-value" :class="{ skeleton: store.statsLoading && !store.stats }">{{ card.value === undefined ? '—' : number(card.value) }}<ArrowUpRight :size="19" aria-hidden="true" /></div>
      <p>{{ card.note }}</p>
    </RouterLink>
  </div>
  <div class="overview-grid">
    <section class="panel category-panel"><header class="panel-heading"><div><h2>Inquiry mix</h2><p>How your conversations are classified</p></div><span class="mini-label">ALL TIME</span></header>
      <StateBlock v-if="!store.stats" :kind="store.statsError ? 'error' : 'loading'" :title="store.statsError ? 'Stats unavailable' : 'Loading insights'" @retry="store.loadStats()" />
      <template v-else>
        <div class="segmented-bar" role="img" :aria-label="categories.map(c => `${c.name}: ${c.count}`).join(', ')">
          <span v-for="category in categories" :key="category.name" :class="category.color" :style="{ flexGrow: category.count }"></span>
        </div>
        <div class="category-list"><RouterLink v-for="category in categories" :key="category.name" :to="{ path: '/inquiries', query: { category: category.category } }" class="category-row">
          <span class="color-dot" :class="category.color"></span><span>{{ category.name }}</span><strong>{{ number(category.count) }}</strong><small>{{ percent(category.count) }}%</small></RouterLink></div>
      </template>
    </section>
    <section class="panel focus-panel"><div class="focus-icon"><Zap :size="22" aria-hidden="true" /></div><span class="eyebrow">NEEDS YOUR ATTENTION</span>
      <h2>{{ store.stats ? number(store.stats.high_priority) : '—' }} high-priority {{ store.stats?.high_priority === 1 ? 'inquiry' : 'inquiries' }}</h2>
      <p>Keep important conversations in view.<br />Review messages and AI summaries in one place.</p>
      <RouterLink class="button primary" to="/inquiries?priority=high">Review high priority<ArrowRight :size="16" /></RouterLink>
      <div v-if="store.stats" class="status-overview"><span><i class="color-dot teal"></i>{{ number(store.stats.new) }} new</span><span>{{ number(store.stats.in_progress) }} in progress</span><span>{{ number(store.stats.resolved) }} resolved</span></div>
    </section>
  </div>
  <section class="panel recent-panel"><header class="panel-heading"><div><h2>Recent inquiries</h2><p>The latest conversations arriving in your workspace</p></div><RouterLink class="text-button" to="/inquiries">View all inquiries<ArrowRight :size="15" /></RouterLink></header>
    <StateBlock v-if="store.loading" kind="loading" title="Loading recent inquiries" />
    <StateBlock v-else-if="store.error" kind="error" title="Could not load inquiries" :description="store.error" @retry="loadRecent" />
    <StateBlock v-else-if="!store.page?.items.length" kind="empty" title="Your inbox is ready" description="New customer inquiries will appear here as they arrive through your API." />
    <InquiryTable v-else :items="store.page.items" compact @select="id => router.push({ query: { selected: id } })" />
  </section>
  <InquiryDetail v-if="selected" :id="selected" @close="closeDetail" @updated="store.refresh" />
</template>
