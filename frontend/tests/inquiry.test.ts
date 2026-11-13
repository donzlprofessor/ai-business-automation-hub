import { describe, expect, it } from 'vitest'
import { classificationInfo, statusAction } from '../src/inquiry'

describe('status actions', () => {
  it('only offers the next forward step or reopening to in progress', () => {
    expect(statusAction.new.target).toBe('in_progress')
    expect(statusAction.in_progress.target).toBe('resolved')
    expect(statusAction.resolved).toEqual({ target: 'in_progress', label: 'Reopen inquiry' })
  })
})

describe('AI visibility uses stored evidence only', () => {
  it('distinguishes unclassified legacy-compatible records without asserting their origin', () => {
    const info = classificationInfo({ category: null, ai_summary: null })
    expect(info.label).toBe('Unclassified / legacy-compatible')
    expect(info.description).toContain('may be')
  })
  it('keeps a missing category unclassified even if a summary exists', () => {
    expect(classificationInfo({ category: null, ai_summary: 'Provided summary' }).label)
      .toBe('Unclassified / legacy-compatible')
  })
  it('distinguishes partial data and avoids asserting that AI actually processed it', () => {
    expect(classificationInfo({ category: 'support', ai_summary: null }).label).toContain('Partial')
    const info = classificationInfo({ category: 'sales', ai_summary: 'Provided summary' })
    expect(info.label).toBe('Classification and summary stored')
    expect(info.description).toContain('does not verify AI processing')
  })
})
