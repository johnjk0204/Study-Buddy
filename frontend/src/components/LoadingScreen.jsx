import './LoadingScreen.css'

export default function LoadingScreen({ steps, completed }) {
  const doneSet = new Set(completed.map(s => s.node))

  return (
    <div className="loading-wrap">
      <div className="loading-book">
        <div className="book-anim">
          <div className="bk-page p1" />
          <div className="bk-page p2" />
          <div className="bk-page p3" />
          <div className="bk-spine" />
        </div>
        <p className="loading-title">Preparing your Study Book…</p>
      </div>

      <div className="loading-steps">
        {steps.map(s => {
          const done = doneSet.has(s.node)
          return (
            <div key={s.node} className={`ls-step ${done ? 'done' : 'pending'}`}>
              <span className="ls-icon">{done ? '✅' : '⏳'}</span>
              <span className="ls-label">{s.label}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
