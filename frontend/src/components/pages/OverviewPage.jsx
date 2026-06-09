import { forwardRef } from 'react'
import './pages.css'

function isKidsGrade(g) {
  return ['grade 1', 'grade 2', '1-2'].some(k => (g || '').toLowerCase().includes(k))
}

const OverviewPage = forwardRef(({ state, theme, pageNum, total }, ref) => {
  const concepts = state.key_concepts || []
  const summary  = state.brief_summary || ''
  const title    = state.article_title || state.topic || 'Overview'
  const isKids   = isKidsGrade(state.requested_grade)

  return (
    <div ref={ref} className="sp-root">
      <div className="sp-header" style={{ background: theme.pri }}>
        <span className="sp-header-label">
          {isKids ? '🔍 What\'s This About?' : '📌 At a Glance'}
        </span>
      </div>

      <div className="sp-body">
        <h2 className={`ov-title ${isKids ? 'ov-title-kids' : ''}`} style={{ color: theme.dk }}>
          {title}
        </h2>

        {summary && (
          <p className={`ov-summary ${isKids ? 'ov-summary-kids' : ''}`}>{summary}</p>
        )}

        {concepts.length > 0 && (
          <>
            <div className="ov-section-label" style={{ color: theme.sec }}>
              {isKids ? '🌟 BIG IDEAS' : 'KEY CONCEPTS'}
            </div>
            <div className="ov-concepts">
              {concepts.map((c, i) => (
                <div key={i} className={`ov-concept ${isKids ? 'ov-concept-kids' : ''}`}
                     style={{ borderLeft: `4px solid ${theme.pri}`, background: theme.bg }}>
                  <span className="ov-concept-num" style={{ color: theme.sec }}>
                    {isKids ? ['1️⃣','2️⃣','3️⃣','4️⃣','5️⃣','6️⃣'][i] || `${i+1}.` : String(i + 1).padStart(2, '0')}
                  </span>
                  <span className={`ov-concept-txt ${isKids ? 'ov-concept-txt-kids' : ''}`}>{c}</span>
                </div>
              ))}
            </div>
          </>
        )}
      </div>

      <div className="sp-footer">
        <span>STUDY BUDDY AI</span>
        <span>{pageNum} / {total}</span>
      </div>
    </div>
  )
})
OverviewPage.displayName = 'OverviewPage'
export default OverviewPage
