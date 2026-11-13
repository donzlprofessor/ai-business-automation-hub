import { defineStore } from 'pinia'
import { ref } from 'vue'
import { errorMessage, getPage, getStats } from '../api'
import type { InquiryPage, InquiryQuery, Stats } from '../api'

export const useInquiries = defineStore('inquiries', () => {
  const page = ref<InquiryPage | null>(null)
  const stats = ref<Stats | null>(null)
  const loading = ref(false)
  const statsLoading = ref(false)
  const error = ref('')
  const statsError = ref('')
  const updatedAt = ref<Date | null>(null)
  const refreshKey = ref(0)
  let pageController: AbortController | undefined
  let statsController: AbortController | undefined

  async function loadPage(query: InquiryQuery) {
    pageController?.abort()
    const controller = new AbortController()
    pageController = controller
    loading.value = true
    error.value = ''
    page.value = null
    try {
      const result = await getPage(query, controller.signal)
      if (!controller.signal.aborted) page.value = result
    } catch (reason) {
      if (!controller.signal.aborted) error.value = errorMessage(reason)
    } finally {
      if (!controller.signal.aborted) loading.value = false
    }
  }

  async function loadStats() {
    statsController?.abort()
    const controller = new AbortController()
    statsController = controller
    statsLoading.value = true
    statsError.value = ''
    try {
      const result = await getStats(controller.signal)
      if (!controller.signal.aborted) {
        stats.value = result
        updatedAt.value = new Date()
      }
    } catch (reason) {
      if (!controller.signal.aborted) statsError.value = errorMessage(reason)
    } finally {
      if (!controller.signal.aborted) statsLoading.value = false
    }
  }
  function refresh() {
    refreshKey.value++
    return loadStats()
  }
  return {
    page, stats, loading, statsLoading, error, statsError, updatedAt, refreshKey,
    loadPage, loadStats, refresh,
  }
})
