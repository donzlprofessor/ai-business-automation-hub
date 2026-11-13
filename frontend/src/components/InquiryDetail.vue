<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { Mail, X, Sparkles, Clock, Check, ArrowRight, LoaderCircle } from 'lucide-vue-next'
import { ApiError, errorMessage, getInquiry, updateInquiryStatus } from '../api'
import type { Inquiry } from '../api'
import { dateTime, label } from '../format'
import { classificationInfo, statusAction } from '../inquiry'
import StateBlock from './StateBlock.vue'
import StatusBadge from './StatusBadge.vue'

const props = defineProps<{ id: string }>()
const emit = defineEmits<{ close: []; updated: [] }>()
const dialog = ref<HTMLDialogElement>()
const inquiry = ref<Inquiry | null>(null)
const loading = ref(false)
const error = ref('')
const saving = ref(false)
const updateError = ref('')
const success = ref('')
const action = computed(() => inquiry.value ? statusAction[inquiry.value.status] : null)
const insights = computed(() => inquiry.value ? classificationInfo(inquiry.value) : null)
let controller: AbortController | undefined
let mutationController: AbortController | undefined
let previousFocus: HTMLElement | null = null

async function load() {
  controller?.abort()
  mutationController?.abort()
  saving.value = false
  updateError.value = ''
  success.value = ''
  const current = new AbortController()
  controller = current
  loading.value = true
  error.value = ''
  inquiry.value = null
  try {
    const result = await getInquiry(props.id, current.signal)
    if (!current.signal.aborted) inquiry.value = result
  } catch (reason) {
    if (!current.signal.aborted) error.value = errorMessage(reason)
  } finally {
    if (!current.signal.aborted) loading.value = false
  }
}

async function changeStatus() {
  if (!inquiry.value || !action.value || saving.value) return
  const current = inquiry.value
  const target = action.value.target
  const mutation = new AbortController()
  mutationController = mutation
  saving.value = true
  updateError.value = ''
  success.value = ''
  try {
    const updated = await updateInquiryStatus(current.id, target, current.status, mutation.signal)
    if (mutation.signal.aborted) return
    inquiry.value = updated
    success.value = current.status === 'resolved' ? 'Inquiry reopened. Status is In progress.'
      : `Status updated to ${label(updated.status)}.`
    emit('updated')
  } catch (reason) {
    if (!mutation.signal.aborted) updateError.value = reason instanceof ApiError
      ? reason.message : 'Status update could not be confirmed. Reload the inquiry before trying again.'
  } finally {
    if (!mutation.signal.aborted) saving.value = false
  }
}
watch(() => props.id, load, { immediate: true })
onMounted(() => {
  previousFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null
  dialog.value?.showModal()
})
onBeforeUnmount(() => {
  controller?.abort()
  mutationController?.abort()
  dialog.value?.close()
  if (previousFocus?.isConnected) previousFocus.focus({ preventScroll: true })
  else document.getElementById('main-content')?.focus({ preventScroll: true })
})
</script>

<template>
  <dialog ref="dialog" class="detail-dialog" aria-labelledby="detail-title" @cancel.prevent="emit('close')"
    @click="(event) => { if (event.target === dialog) emit('close') }">
    <div class="detail-content">
      <header class="detail-header"><span class="eyebrow">INQUIRY DETAILS</span>
        <button autofocus class="icon-button" aria-label="Close inquiry details" @click="emit('close')"><X :size="21" /></button>
      </header>
      <h2 id="detail-title">{{ inquiry?.customer_name || 'Customer inquiry' }}</h2>
      <StateBlock v-if="loading" kind="loading" title="Loading inquiry" />
      <StateBlock v-else-if="error" kind="error" title="Could not open inquiry" :description="error" @retry="load" />
      <template v-else-if="inquiry">
        <a class="email-link" :href="`mailto:${inquiry.email}`"><Mail :size="15" />{{ inquiry.email }}</a>
        <section class="status-management" aria-labelledby="status-title" :aria-busy="saving">
          <div class="status-heading"><div><h3 id="status-title">Inquiry status</h3>
            <StatusBadge :value="inquiry.status" kind="status" /></div>
            <button v-if="action" class="button primary status-action" :disabled="saving || Boolean(updateError)" @click="changeStatus">
              <LoaderCircle v-if="saving" :size="15" class="spin" aria-hidden="true" />
              <ArrowRight v-else :size="15" aria-hidden="true" />{{ saving ? 'Saving…' : action.label }}
            </button></div>
          <p class="status-guidance">New → In progress → Resolved. Reopening returns to In progress.</p>
        </section>
        <div class="status-feedback" aria-live="polite" role="status">
          <p v-if="success" class="success-feedback"><Check :size="16" aria-hidden="true" />{{ success }}</p>
        </div>
        <div v-if="updateError" class="update-error" role="alert"><p>{{ updateError }}</p>
          <button class="button" @click="load">Reload inquiry</button></div>
        <section class="summary-box ai-insights" aria-labelledby="insights-title">
          <h3 id="insights-title"><Sparkles :size="17" aria-hidden="true" /> AI Insights</h3>
          <p class="insights-label" :class="{ 'legacy-label': !inquiry.category }">{{ insights?.label }}</p>
          <p class="insights-description">{{ insights?.description }}</p>
          <dl class="insights-fields"><div><dt>Category</dt><dd><StatusBadge :value="inquiry.category" kind="category" /></dd></div>
            <div><dt>Priority</dt><dd><StatusBadge :value="inquiry.priority" kind="priority" /></dd></div></dl>
          <h4>AI summary</h4>
          <p class="preserve-text">{{ inquiry.ai_summary || 'No AI summary has been provided for this inquiry.' }}</p>
          <p class="processing-note">Only stored classification fields are available. A priority may be the default value. Model, processing time, confidence, and source are not recorded.</p>
        </section>
        <section class="message-section"><h3>Customer message</h3><p class="preserve-text">{{ inquiry.message }}</p></section>
        <section class="detail-meta"><h3><Clock :size="16" aria-hidden="true" /> Activity</h3>
          <dl><div><dt>Received</dt><dd><time :datetime="inquiry.created_at">{{ dateTime(inquiry.created_at) }}</time></dd></div>
            <div><dt>Inquiry ID</dt><dd class="mono">{{ inquiry.id }}</dd></div></dl>
          <p class="muted small">Times are shown in your local timezone. Only the received timestamp is recorded.</p>
        </section>
      </template>
    </div>
  </dialog>
</template>
