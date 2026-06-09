import { forwardRef } from 'react'
import './pages.css'

const LABELS      = ['⚡ DISCOVERY', '🌟 AMAZING', '❓ DID YOU KNOW', '✓ TRUE FACT', '🤯 MIND BLOWN']
const LABELS_KIDS = ['🌟 WOW!',      '⚡ COOL!',    '❓ GUESS WHAT?',  '✅ TRUE!',    '🤯 AMAZING!']

function isKidsGrade(g) {
  return ['grade 1', 'grade 2', '1-2'].some(k => (g || '').toLowerCase().includes(k))
}

function FactCard({ fact, index, theme, isKids }) {
  const em    = fact.emoji || '💡'
  const text  = fact.fact || ''
  const wow   = fact.wow_factor || ''
  const label = isKids ? LABELS_KIDS[index % LABELS_KIDS.length] : LABELS[index % LABELS.length]

  if (index === 0) {
    return (
      <div className={`fc-hero ${isKids ? 'fc-hero-kids' : ''}`}
           style={{ background: `linear-gradient(135deg,${theme.pri},${theme.dk})` }}>
        <div className="fc-h-body">
          <span className="fc-badge fc-b-white">{label}</span>
          <p className={`fc-h-fact ${isKids ? 'fc-h-fact-kids' : ''}`}>{text}</p>
          <p className="fc-h-wow">"{wow}"</p>
        </div>
        <div className={`fc-h-em ${isKids ? 'fc-h-em-kids' : ''}`}>{em}</div>
      </div>
    )
  }
  if (index === 1) {
    return (
      <div className="fc-numcard">
        <div className="fc-numcol" style={{ background: theme.pri }}>
          <span className={`fc-bignum ${isKids ? 'fc-bignum-kids' : ''}`}>0{index + 1}</span>
        </div>
        <div className="fc-ncbody">
          <span className="fc-badge" style={{ background: theme.lt, color: theme.dk }}>{label}</span>
          <p className={`fc-ncfact ${isKids ? 'fc-ncfact-kids' : ''}`}>{text}</p>
          <p className="fc-ncwow" style={{ color: theme.pri }}>{wow}</p>
        </div>
      </div>
    )
  }
  if (index === 2) {
    return (
      <div className="fc-emcard" style={{ background: theme.bg, border: `2px solid ${theme.lt}` }}>
        <div className={`fc-emicon ${isKids ? 'fc-emicon-kids' : ''}`}>{em}</div>
        <span className="fc-badge" style={{ background: `${theme.sec}28`, color: theme.sec }}>{label}</span>
        <p className={`fc-emfact ${isKids ? 'fc-emfact-kids' : ''}`}>{text}</p>
        <p className="fc-emwow" style={{ color: theme.sec }}>{wow}</p>
      </div>
    )
  }
  if (index === 3) {
    return (
      <div className="fc-qcard" style={{ borderLeft: `5px solid ${theme.dk}` }}>
        <div className="fc-qdeco" style={{ color: theme.dk }}>&ldquo;</div>
        <div className="fc-qbody">
          <span className="fc-badge" style={{ background: `${theme.dk}22`, color: theme.dk }}>{label}</span>
          <p className={`fc-qfact ${isKids ? 'fc-qfact-kids' : ''}`}>{text}</p>
          <p className="fc-qwow" style={{ color: theme.dk }}>{wow}</p>
        </div>
      </div>
    )
  }
  return (
    <div className="fc-spotlight" style={{ background: `${theme.sec}1a`, border: `2px solid ${theme.sec}55` }}>
      <div className="fc-sphead">
        <span className="fc-badge" style={{ background: theme.sec, color: '#fff' }}>{label}</span>
        <span className={`fc-spem ${isKids ? 'fc-spem-kids' : ''}`}>{em}</span>
      </div>
      <p className={`fc-spfact ${isKids ? 'fc-spfact-kids' : ''}`}>{text}</p>
      <p className="fc-spwow" style={{ color: theme.sec }}>{wow}</p>
    </div>
  )
}

const FactsPage = forwardRef(({ state, theme, pageNum, total }, ref) => {
  const facts  = (state.did_you_know_facts || []).slice(0, 5)
  const isKids = isKidsGrade(state.requested_grade)

  return (
    <div ref={ref} className="sp-root">
      <div className="sp-header" style={{ background: theme.sec }}>
        <span className="sp-header-label">
          {isKids ? '🤩 Cool Facts!' : '💡 Fascinating Facts'}
        </span>
      </div>

      <div className="sp-body facts-body">
        <div className="facts-grid">
          {facts.map((f, i) => (
            <FactCard key={i} fact={f} index={i} theme={theme} isKids={isKids} />
          ))}
          {facts.length === 0 && (
            <p style={{ color: '#94a3b8', fontSize: 14 }}>No facts available yet.</p>
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
FactsPage.displayName = 'FactsPage'
export default FactsPage
