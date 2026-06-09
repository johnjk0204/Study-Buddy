import { forwardRef, useState, useEffect } from 'react'
import './pages.css'

const TYPE_ICON = {
  'bar chart': '📊', 'mind map': '🗺️', 'timeline': '📅',
  'table': '📋', 'venn': '🔵', 'cycle': '🔄',
  'flowchart': '📐', 'infographic': '📌', 'map': '🌍',
  'diagram': '🖼️', 'illustration': '🎨', 'photo': '📷',
}

function getIcon(type = '') {
  const k = type.toLowerCase()
  for (const [key, val] of Object.entries(TYPE_ICON)) {
    if (k.includes(key)) return val
  }
  return '📊'
}

// Fetch a Wikipedia thumbnail for the given search term
function useWikiImage(query) {
  const [url, setUrl] = useState(null)

  useEffect(() => {
    if (!query) return
    const term = query.replace(/[^a-zA-Z0-9 ]/g, '').trim()
    if (!term) return

    const controller = new AbortController()
    fetch(
      `https://en.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(term)}`,
      { signal: controller.signal }
    )
      .then(r => (r.ok ? r.json() : null))
      .then(data => { if (data?.thumbnail?.source) setUrl(data.thumbnail.source) })
      .catch(() => {})

    return () => controller.abort()
  }, [query])

  return url
}

function VisualCard({ v, index, theme, isKids }) {
  // Try the visual title first, then first search term
  const primaryQuery = v.title || (v.search_terms?.[0] ?? '')
  const fallbackQuery = v.search_terms?.[1] ?? ''

  const img1 = useWikiImage(primaryQuery)
  const img2 = useWikiImage(img1 ? null : fallbackQuery)   // only fetch fallback if primary failed
  const imgUrl = img1 || img2

  const borderColor = index % 2 === 0 ? theme.pri : theme.sec

  return (
    <div className={`vis-card ${isKids ? 'vis-card-kids' : ''}`}
         style={{ borderTop: `4px solid ${borderColor}` }}>

      {imgUrl ? (
        <div className="vis-img-wrap">
          <img
            src={imgUrl}
            alt={v.title || 'Visual aid'}
            className="vis-img"
            loading="lazy"
            onError={e => { e.target.style.display = 'none' }}
          />
        </div>
      ) : (
        <div className="vis-img-placeholder" style={{ background: theme.bg }}>
          <span style={{ fontSize: isKids ? 40 : 30 }}>{getIcon(v.type || '')}</span>
        </div>
      )}

      <div className="vis-content">
        <div className="vis-type" style={{ color: borderColor }}>
          {(v.type || 'Visual').toUpperCase()}
        </div>
        <div className={`vis-title ${isKids ? 'vis-title-kids' : ''}`} style={{ color: theme.dk }}>
          {v.title || ''}
        </div>
        <p className={`vis-desc ${isKids ? 'vis-desc-kids' : ''}`}>
          {(v.description || '').slice(0, isKids ? 100 : 130)}
        </p>
      </div>
    </div>
  )
}

const VisualsPage = forwardRef(({ state, theme, pageNum, total }, ref) => {
  const visuals  = (state.visual_descriptions || []).slice(0, 4)
  const isKids   = ['grade 1', 'grade 2', '1-2'].some(g =>
    (state.requested_grade || '').toLowerCase().includes(g))

  return (
    <div ref={ref} className="sp-root">
      <div className="sp-header" style={{ background: theme.dk }}>
        <span className="sp-header-label">
          {isKids ? '🖼️ Let\'s Look at Pictures!' : '🎨 Illustrated Guide'}
        </span>
      </div>

      <div className="sp-body vis-body">
        <div className={`vis-grid ${isKids ? 'vis-grid-kids' : ''}`}>
          {visuals.map((v, i) => (
            <VisualCard key={i} v={v} index={i} theme={theme} isKids={isKids} />
          ))}
          {visuals.length === 0 && (
            <p style={{ color: '#94a3b8', fontSize: 14 }}>No visuals available.</p>
          )}
        </div>
      </div>

      <div className="sp-footer">
        <span>STUDY BUDDY AI</span>
        <span>{pageNum} / {total}</span>
      </div>
    </div>
  )
})
VisualsPage.displayName = 'VisualsPage'
export default VisualsPage
