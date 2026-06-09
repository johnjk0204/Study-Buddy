export const THEMES = {
  science:   { pri: '#1565c0', sec: '#0097a7', bg: '#e3f2fd', lt: '#bbdefb', dk: '#0d47a1' },
  biology:   { pri: '#2e7d32', sec: '#558b2f', bg: '#e8f5e9', lt: '#c8e6c9', dk: '#1b5e20' },
  chemistry: { pri: '#6a1b9a', sec: '#ad1457', bg: '#f3e5f5', lt: '#e1bee7', dk: '#4a148c' },
  physics:   { pri: '#e65100', sec: '#f57f17', bg: '#fff3e0', lt: '#ffe0b2', dk: '#bf360c' },
  math:      { pri: '#283593', sec: '#6a1b9a', bg: '#e8eaf6', lt: '#c5cae9', dk: '#1a237e' },
  history:   { pri: '#5d4037', sec: '#e65100', bg: '#efebe9', lt: '#d7ccc8', dk: '#3e2723' },
  geography: { pri: '#00695c', sec: '#0277bd', bg: '#e0f2f1', lt: '#b2dfdb', dk: '#004d40' },
  english:   { pri: '#880e4f', sec: '#4a148c', bg: '#fce4ec', lt: '#f8bbd0', dk: '#560027' },
  default:   { pri: '#1565c0', sec: '#6a1b9a', bg: '#f0f4ff', lt: '#e8eaf6', dk: '#0d47a1' },
}

export function getTheme(subject = '') {
  const key = (subject || '').toLowerCase().trim()
  return THEMES[key] || THEMES.default
}

export const SUBJECT_EMOJI = {
  science: '🔬', biology: '🧬', chemistry: '⚗️', physics: '⚡',
  math: '📐', history: '🏛️', geography: '🌍', english: '📖',
  default: '💡',
}

export function getEmoji(subject = '') {
  return SUBJECT_EMOJI[(subject || '').toLowerCase()] || SUBJECT_EMOJI.default
}
