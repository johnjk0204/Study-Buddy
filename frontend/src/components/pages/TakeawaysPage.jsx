import { forwardRef } from 'react'
import './pages.css'

const STAR_NUMS = ['1️⃣','2️⃣','3️⃣','4️⃣','5️⃣','6️⃣','7️⃣','8️⃣']

function isKidsGrade(g) {
  return ['grade 1', 'grade 2', '1-2'].some(k => (g || '').toLowerCase().includes(k))
}

const TakeawaysPage = forwardRef(({ state, theme, pageNum, total }, ref) => {
  const takeaways = state.key_takeaways || []
  const isKids    = isKidsGrade(state.requested_grade)

  return (
    <div ref={ref} className="sp-root">
      <div className="sp-header" style={{ background: theme.pri }}>
        <span className="sp-header-label">
          {isKids ? '⭐ Remember This!' : '🎯 Key Takeaways'}
        </span>
      </div>

      <div className="sp-body">
        <p className={`tk-intro ${isKids ? 'tk-intro-kids' : ''}`} style={{ color: theme.dk }}>
          {isKids
            ? '⭐ Here\'s what we learned today!'
            : 'Remember these essential points from your study:'}
        </p>

        <div className="tk-list">
          {takeaways.map((tk, i) => (
            <div key={i} className={`tk-row ${isKids ? 'tk-row-kids' : ''}`}>
              <div className={`tk-num ${isKids ? 'tk-num-kids' : ''}`}
                   style={isKids ? { background: theme.lt, color: theme.dk } : { background: theme.pri, color: '#fff' }}>
                {isKids ? (STAR_NUMS[i] || `${i+1}`) : String(i + 1).padStart(2, '0')}
              </div>
              <div className="tk-body">
                <div className={`tk-point ${isKids ? 'tk-point-kids' : ''}`} style={isKids ? { color: theme.dk } : {}}>
                  {tk.point || tk}
                </div>
                {tk.explanation && (
                  <div className={`tk-expl ${isKids ? 'tk-expl-kids' : ''}`}>{tk.explanation}</div>
                )}
              </div>
            </div>
          ))}
          {takeaways.length === 0 && (
            <p style={{ color: '#94a3b8', fontSize: 14 }}>No takeaways available yet.</p>
          )}
        </div>

        {takeaways.length > 0 && (
          <div className="tk-banner" style={{ background: `linear-gradient(135deg,${theme.bg},${theme.lt})`, borderLeft: `4px solid ${theme.sec}` }}>
            <span className="tk-banner-icon">{isKids ? '🎉' : '💪'}</span>
            <span className={`tk-banner-text ${isKids ? 'tk-banner-text-kids' : ''}`} style={{ color: theme.dk }}>
              {isKids
                ? `You learned ${takeaways.length} cool things today! Great job! 🌟`
                : `You now have ${takeaways.length} key ideas to take away!`}
            </span>
          </div>
        )}
      </div>

      <div className="sp-footer">
        <span>STUDY BUDDY AI</span>
        <span>{pageNum} / {total}</span>
      </div>
    </div>
  )
})
TakeawaysPage.displayName = 'TakeawaysPage'
export default TakeawaysPage
