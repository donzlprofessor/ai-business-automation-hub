import type { Inquiry, InquiryStatus } from './api'

export const statusAction: Record<InquiryStatus, { target: InquiryStatus; label: string }> = {
  new: { target: 'in_progress', label: 'Start progress' },
  in_progress: { target: 'resolved', label: 'Mark resolved' },
  resolved: { target: 'in_progress', label: 'Reopen inquiry' },
}

export function classificationInfo(inquiry: Pick<Inquiry, 'category' | 'ai_summary'>) {
  if (!inquiry.category) return {
    label: 'Unclassified / legacy-compatible',
    description: 'No category is stored. This may be a legacy inquiry or a submission without classification.',
  }
  return {
    label: inquiry.ai_summary ? 'Classification and summary stored' : 'Partial classification stored',
    description: 'These values were supplied when the inquiry was created. Their presence does not verify AI processing.',
  }
}
