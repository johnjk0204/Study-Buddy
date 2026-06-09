import { forwardRef } from 'react'
import { getEmoji } from '../../theme'
import './pages.css'

const ClosingPage = forwardRef(({ state, theme, pageNum, total }, ref) => {
  const topic     = state.topic   || 'this topic'
  const subject   = state.subject || ''
  const emoji     = getEmoji(subject)
  const concepts  = (state.key_concepts || []).length
  const facts     = (state.did_you_know_facts || []).length
  const questions = (state.quiz_questions || []).length
  const takes     = (state.key_takeaways || []).length

  const stats = [
    { icon: '💡', label: 'Key Concepts', val: concepts },
    { icon: '🤯', label: 'Cool Facts',   val: facts    },
    { icon: '🧠', label: 'Quiz Questions', val: questions },
    { icon: '🎯', label: 'Takeaways',    val: takes    },
  ]

  return (
    <div ref={ref} className="sp-root cl-root">
      {/* Top band */}
      <div className="cl-top-band" style={{ background: theme.pri }}>
        <span className="cl-top-text">🎉 You Did It!</span>
      </div>

      {/* White body — guaranteed readable */}
      <div className="cl-body-white">
        {/* Trophy badge */}
        <div className="cl-trophy-ring" style={{ background: theme.bg, border: `4px solid ${theme.lt}` }}>
          <span className="cl-trophy-em">{emoji}</span>
          <span className="cl-trophy-label" style={{ color: theme.sec }}>COMPLETED</span>
        </div>

        <h2 className="cl-title" style={{ color: theme.dk }}>Amazing Work!</h2>
        <p className="cl-sub">You just finished studying</p>
        <p className="cl-topic" style={{ color: theme.pri }}>"{topic}"</p>

        {/* Stats grid */}
        <div className="cl-stats">
          {stats.filter(s => s.val > 0).map((s, i) => (
            <div key={i} className="cl-stat" style={{ background: theme.bg, borderTop: `3px solid ${theme.sec}` }}>
              <span className="cl-stat-icon">{s.icon}</span>
              <span className="cl-stat-val" style={{ color: theme.dk }}>{s.val}</span>
              <span className="cl-stat-label">{s.label}</span>
            </div>
          ))}
        </div>

        <p className="cl-quote">"The more that you read,<br/>the more things you will know."</p>
        <p className="cl-attr" style={{ color: theme.sec }}>— Dr. Seuss</p>
      </div>

      {/* Bottom band */}
      <div className="cl-bottom-band" style={{ background: theme.dk }}>
        <span style={{ color: 'rgba(255,255,255,.7)', fontSize: 11, fontWeight: 700, letterSpacing: 1 }}>📚 STUDY BUDDY AI</span>
        <span style={{ color: 'rgba(255,255,255,.4)', fontSize: 11 }}>{pageNum} / {total}</span>
      </div>
    </div>
  )
})
ClosingPage.displayName = 'ClosingPage'
export default ClosingPage
