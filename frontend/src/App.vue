<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { Activity, ArrowUpRight, ChevronRight, CircleHelp, Command, Inbox, LayoutDashboard, Menu, RefreshCw, ShieldCheck, X } from 'lucide-vue-next'
import { useInquiries } from './stores/inquiries'

const route = useRoute()
const store = useInquiries()
const menuOpen = ref(false)
const menuButton = ref<HTMLButtonElement>()
const sidebar = ref<HTMLElement>()
const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'
const docsUrl = `${(apiBase.startsWith('http') ? apiBase : 'http://127.0.0.1:8000').replace(/\/$/, '')}/docs`
const connection = computed(() => store.statsError ? 'Connection issue' : store.stats ? 'Connected' : 'Connecting')
watch(() => route.path, () => { menuOpen.value = false })
watch(menuOpen, async (open) => {
  await nextTick()
  if (open) sidebar.value?.querySelector<HTMLAnchorElement>('a')?.focus()
  else if (menuButton.value?.offsetParent) menuButton.value.focus()
})
function sidebarKeys(event: KeyboardEvent) {
  if (!menuOpen.value || event.key !== 'Tab' || !sidebar.value) return
  const links = Array.from(sidebar.value.querySelectorAll<HTMLElement>('a[href],button:not(:disabled)'))
  const first = links[0]
  const last = links.at(-1)
  if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus() }
  else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus() }
}
onMounted(() => { void store.loadStats() })
</script>

<template>
  <a class="skip-link" href="#main-content">Skip to content</a>
  <div class="app-shell" @keydown.esc="menuOpen = false">
    <button v-if="menuOpen" class="sidebar-scrim" aria-label="Close navigation" @click="menuOpen = false"></button>
    <aside id="sidebar" ref="sidebar" class="sidebar" :class="{ 'is-open': menuOpen }" aria-label="Workspace navigation" @keydown="sidebarKeys">
      <button v-if="menuOpen" class="icon-button drawer-close" aria-label="Close navigation" @click="menuOpen = false"><X :size="20" /></button>
      <RouterLink to="/" class="brand"><span class="brand-mark"><Command :size="22" aria-hidden="true" /></span>
        <span>Automation<span class="brand-light">Hub</span></span></RouterLink>
      <div class="workspace-switch"><span class="workspace-icon">A</span>
        <span><strong>Business workspace</strong><small>Local environment</small></span><ShieldCheck :size="15" aria-hidden="true" /></div>
      <p class="nav-label">WORKSPACE</p>
      <nav>
        <RouterLink to="/" class="nav-link" exact-active-class="active"><LayoutDashboard :size="18" />Overview</RouterLink>
        <RouterLink to="/inquiries" class="nav-link" active-class="active"><Inbox :size="18" />Inquiries
          <span v-if="store.stats" class="nav-count">{{ store.stats.total.toLocaleString() }}</span></RouterLink>
      </nav>
      <div class="sidebar-bottom">
        <div class="local-card"><ShieldCheck :size="19" aria-hidden="true" /><strong>Your local workspace</strong>
          <p>Customer insights, kept close.<br />Available on this device.</p></div>
        <a :href="docsUrl" class="nav-link" target="_blank" rel="noopener noreferrer"><CircleHelp :size="18" />API documentation<ArrowUpRight :size="15" /></a>
        <div class="workspace-footer"><span class="footer-avatar"><Activity :size="19" /></span>
          <div><strong>Automation Hub</strong><small>Inquiry operations</small></div><span class="version">v0.1</span></div>
      </div>
    </aside>
    <div class="main-shell">
      <header class="topbar">
        <div class="breadcrumb"><button ref="menuButton" class="icon-button mobile-menu" :aria-expanded="menuOpen" aria-controls="sidebar"
          :aria-label="menuOpen ? 'Close navigation' : 'Open navigation'" @click="menuOpen = !menuOpen">
          <component :is="menuOpen ? X : Menu" :size="20" /></button>
          <span class="breadcrumb-parent">Workspace</span><ChevronRight :size="14" aria-hidden="true" /><strong>{{ route.meta.title }}</strong></div>
        <div class="topbar-actions"><span class="connection" :class="{ failed: store.statsError }"><i></i>{{ connection }}</span>
          <span class="topbar-separator"></span><span class="local-label"><ShieldCheck :size="14" />Local only</span></div>
      </header>
      <main id="main-content" tabindex="-1">
        <div class="page-heading"><div><p class="eyebrow">CUSTOMER OPERATIONS</p>
          <h1>{{ route.name === 'dashboard' ? 'Workspace overview' : route.meta.title }}</h1>
          <p class="page-description">{{ route.name === 'dashboard' ? 'A clear view of your customer conversations.' : 'Find, review, and understand every customer inquiry.' }}</p></div>
          <button v-if="route.name" class="button refresh-button" :disabled="store.loading || store.statsLoading" @click="store.refresh()">
            <RefreshCw :size="15" :class="{ spin: store.statsLoading }" aria-hidden="true" />Refresh data</button></div>
        <RouterView />
        <footer class="page-footer"><span>AI Business Automation Hub</span><span v-if="store.updatedAt">Last synced {{ store.updatedAt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }}</span></footer>
      </main>
    </div>
  </div>
</template>
