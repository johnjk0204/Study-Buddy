import { useState } from 'react'
import InputForm    from './components/InputForm'
import LoadingScreen from './components/LoadingScreen'
import StudyBook    from './components/StudyBook'
import './App.css'

const STEPS = [
  { node: 'guardrail_check', label: 'Checking content safety' },
  { node: 'topic_extractor', label: 'Extracting topic & concepts' },
  { node: 'summary_agent',   label: 'Writing the article' },
  { node: 'quiz_agent',      label: 'Generating quiz questions' },
  { node: 'image_agent',     label: 'Finding visual aids' },
  { node: 'takeaway_agent',  label: 'Building key takeaways' },
]

export default function App() {
  const [phase, setPhase]           = useState('input')
  const [progress, setProgress]     = useState([])
  const [studyState, setStudyState] = useState(null)
  const [error, setError]           = useState(null)

  async function handleAnalyze(passage, gradeLevel) {
    setError(null)
    setProgress([])
    setPhase('loading')

    const { analyzeStream } = await import('./api.js')
    const state = { requested_grade: gradeLevel }

    try {
      await analyzeStream(passage, gradeLevel, (event) => {
        const { node } = event

        if (node === '__blocked__') {
          setError('This passage contains inappropriate content and cannot be processed.')
          setPhase('input'); return
        }
        if (node === '__error__') {
          setError(event.detail || 'An error occurred.')
          setPhase('input'); return
        }
        if (node === '__done__') {
          setStudyState({ ...state, _renderUrl: event.render_url, _pdfUrl: event.pdf_url })
          setPhase('book'); return
        }

        if (event.payload) Object.assign(state, event.payload)
        setProgress(prev => [...prev.filter(s => s.node !== node), { node, done: true }])
      })
    } catch (err) {
      setError(err.message)
      setPhase('input')
    }
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <span className="app-logo">📚</span>
        <span className="app-title">Study Buddy AI</span>
        {phase !== 'input' && (
          <button className="btn-ghost" onClick={() => setPhase('input')}>← New Guide</button>
        )}
      </header>

      {error && <div className="error-banner">⚠️ {error}</div>}

      {phase === 'input'   && <InputForm onAnalyze={handleAnalyze} />}
      {phase === 'loading' && <LoadingScreen steps={STEPS} completed={progress} />}
      {phase === 'book'    && studyState && <StudyBook state={studyState} />}
    </div>
  )
}
