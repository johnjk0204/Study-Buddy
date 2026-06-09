import { forwardRef, useState } from 'react'
import './pages.css'

const OptionBtn = ({ label, selected, correct, revealed, onClick }) => {
  let cls = 'quiz-opt'
  if (revealed) {
    if (correct) cls += ' opt-correct'
    else if (selected) cls += ' opt-wrong'
    else cls += ' opt-dim'
  } else if (selected) cls += ' opt-selected'
  return (
    <button className={cls} onClick={onClick} disabled={revealed}>
      <span className="opt-letter">{label}</span>
      <span className="opt-text">{/* filled by parent */}</span>
    </button>
  )
}

function QuizQuestion({ q, index, theme }) {
  const [chosen, setChosen]   = useState(null)
  const [revealed, setReveal] = useState(false)
  const opts = (q.options || []).map(o =>
    // strip legacy "A. " / "B. " prefixes if the agent returned them
    o.replace(/^[A-D]\.\s+/, '')
  )
  // support both correct_answer (new) and answer letter (legacy fallback)
  const correct = q.correct_answer ||
    (() => {
      const letter = (q.answer || '').trim().toUpperCase()
      const idx = ['A','B','C','D'].indexOf(letter)
      return idx >= 0 ? opts[idx] : ''
    })()

  function pick(opt) {
    if (revealed) return
    setChosen(opt)
    setReveal(true)
  }

  return (
    <div className="quiz-q">
      <div className="quiz-qnum" style={{ color: theme.sec }}>Q{index + 1}</div>
      <p className="quiz-qtext">{q.question}</p>
      <div className="quiz-opts">
        {opts.map((opt, i) => {
          const letter = ['A', 'B', 'C', 'D'][i]
          const isCorrect = opt === correct
          const isSelected = opt === chosen
          let cls = 'quiz-opt'
          if (revealed) {
            if (isCorrect)       cls += ' opt-correct'
            else if (isSelected) cls += ' opt-wrong'
            else                 cls += ' opt-dim'
          } else if (isSelected) {
            cls += ' opt-selected'
          }
          return (
            <button
              key={i}
              className={cls}
              style={revealed && isCorrect ? { borderColor: theme.sec } : {}}
              onClick={() => pick(opt)}
              disabled={revealed}
            >
              <span className="opt-letter" style={{ background: revealed && isCorrect ? theme.sec : theme.lt, color: revealed && isCorrect ? '#fff' : theme.dk }}>
                {letter}
              </span>
              <span className="opt-text">{opt}</span>
            </button>
          )
        })}
      </div>
      {revealed && (
        <p className="quiz-expl" style={{ color: theme.dk }}>
          {chosen === correct ? '✅ Correct! ' : `❌ The answer is: ${correct}. `}
          {q.explanation || ''}
        </p>
      )}
    </div>
  )
}

const QuizPage = forwardRef(({ state, theme, pageNum, total }, ref) => {
  const questions = (state.quiz_questions || []).slice(0, 4)

  return (
    <div ref={ref} className="sp-root">
      <div className="sp-header" style={{ background: theme.dk }}>
        <span className="sp-header-label">🧠 Test Yourself</span>
      </div>

      <div className="sp-body quiz-body">
        {questions.length === 0 ? (
          <p style={{ color: '#94a3b8', fontSize: 14 }}>No quiz questions available yet.</p>
        ) : (
          questions.map((q, i) => (
            <QuizQuestion key={i} q={q} index={i} theme={theme} />
          ))
        )}
      </div>

      <div className="sp-footer">
        <span>STUDY BUDDY AI</span>
        <span>{pageNum} / {total}</span>
      </div>
    </div>
  )
})
QuizPage.displayName = 'QuizPage'
export default QuizPage
