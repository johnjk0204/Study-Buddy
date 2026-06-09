import { forwardRef } from 'react'
import './pages.css'

function isKidsGrade(g) {
  return ['grade 1', 'grade 2', '1-2'].some(k => (g || '').toLowerCase().includes(k))
}

const ArticlePage = forwardRef(({ state, theme, pageNum, total }, ref) => {
  const title   = state.article_title   || 'In Depth'
  const content = state.article_content || ''
  const isKids  = isKidsGrade(state.requested_grade)

  const paras = content
    .split(/\n+/)
    .map(p => p.trim())
    .filter(Boolean)
    .slice(0, isKids ? 5 : 7)

  return (
    <div ref={ref} className="sp-root">
      <div className="sp-header" style={{ background: theme.sec }}>
        <span className="sp-header-label">
          {isKids ? '📖 Story Time!' : '📰 In Depth'}
        </span>
      </div>

      <div className={`sp-body article-body ${isKids ? 'article-body-kids' : ''}`}>
        <h2 className={`art-title ${isKids ? 'art-title-kids' : ''}`} style={{ color: theme.dk }}>
          {title}
        </h2>

        {paras.length > 0 ? (
          paras.map((p, i) => (
            i === 0
              ? <p key={i} className={`art-para art-lead ${isKids ? 'art-lead-kids' : ''}`}>{p}</p>
              : <p key={i} className={`art-para ${isKids ? 'art-para-kids' : ''}`}>{p}</p>
          ))
        ) : (
          <p style={{ color: '#94a3b8', fontSize: 14 }}>Article content loading…</p>
        )}
      </div>

      <div className="sp-footer">
        <span>STUDY BUDDY AI</span>
        <span>{pageNum} / {total}</span>
      </div>
    </div>
  )
})
ArticlePage.displayName = 'ArticlePage'
export default ArticlePage
