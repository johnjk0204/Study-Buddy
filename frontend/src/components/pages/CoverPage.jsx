import { forwardRef } from 'react'
import { getEmoji } from '../../theme'
import './pages.css'

const CoverPage = forwardRef(({ state, theme, pageNum, total }, ref) => {
  const topic    = state.topic   || 'Study Guide'
  const subject  = state.subject || 'General'
  const summary  = state.brief_summary || ''
  const emoji    = getEmoji(subject)
  const concepts = (state.key_concepts || []).slice(0, 4)

  return (
    <div ref={ref} className="sp-root cover-root">
      {/* Top band — solid color, always readable */}
      <div className="cov-top-band" style={{ background: theme.pri }}>
        <div className="cov-brand">
          <span className="cov-brand-icon">📚</span>
          <span className="cov-brand-text">STUDY BUDDY AI</span>
        </div>
        <div className="cov-subject-tag" style={{ background: 'rgba(255,255,255,.2)' }}>
          {subject.toUpperCase()}
        </div>
      </div>

      {/* Central hero — white background, always readable */}
      <div className="cov-hero">
        <div className="cov-emoji-badge" style={{ background: theme.bg, border: `4px solid ${theme.lt}` }}>
          <span className="cov-big-emoji">{emoji}</span>
        </div>

        <h1 className="cov-main-title" style={{ color: theme.dk }}>{topic}</h1>

        {summary && (
          <p className="cov-desc">{summary.slice(0, 120)}{summary.length > 120 ? '…' : ''}</p>
        )}

        {concepts.length > 0 && (
          <div className="cov-chips">
            {concepts.map((c, i) => (
              <span key={i} className="cov-chip" style={{ background: theme.bg, color: theme.dk, border: `1.5px solid ${theme.lt}` }}>
                {c}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Bottom band — solid dark color, always readable */}
      <div className="cov-bottom-band" style={{ background: theme.dk }}>
        <div className="cov-bottom-left">
          <span className="cov-lets">Let's explore! 🚀</span>
          <span className="cov-flip-hint">Click the edge to turn pages →</span>
        </div>
        <span className="cov-page-num" style={{ color: 'rgba(255,255,255,.5)' }}>
          {pageNum} / {total}
        </span>
      </div>
    </div>
  )
})
CoverPage.displayName = 'CoverPage'
export default CoverPage
