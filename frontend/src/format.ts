export const number = (value: number) => new Intl.NumberFormat().format(value)
export const dateTime = (value: string) => new Intl.DateTimeFormat(undefined, {
  dateStyle: 'medium', timeStyle: 'short',
}).format(new Date(value))
export const label = (value: string | null) => value
  ? value.replaceAll('_', ' ').replace(/^./, (letter) => letter.toUpperCase()) : 'Unclassified'
