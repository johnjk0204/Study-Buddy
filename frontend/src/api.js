const BASE = ''   // Vite proxy handles /api → localhost:8000

export async function analyzeStream(passage, gradeLevel, onEvent) {
  const res = await fetch(`${BASE}/api/analyze/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ passage, grade_level: gradeLevel }),
  })

  if (!res.ok) {
    const text = await res.text()
    throw new Error(`API error ${res.status}: ${text}`)
  }

  const reader = res.body.getReader()
  const dec    = new TextDecoder()
  let buf      = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buf += dec.decode(value, { stream: true })
    const parts = buf.split('\n\n')
    buf = parts.pop()
    for (const part of parts) {
      const line = part.trim()
      if (line.startsWith('data: ')) {
        try {
          const data = JSON.parse(line.slice(6))
          onEvent(data)
        } catch (_) { /* skip malformed */ }
      }
    }
  }
}
