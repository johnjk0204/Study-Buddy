import { useState } from 'react'
import './InputForm.css'

const GRADES = [
  { value: 'Grade 1-2', label: '🌱 Grade 1 – 2',  desc: 'Ages 5–7 · Picture-book style, simple words, big images' },
  { value: 'Grade 3-5', label: '🚀 Grade 3 – 5',  desc: 'Ages 8–11 · Explorer style, fun facts, clear language' },
  { value: 'Grade 6-12', label: '🎓 Grade 6 – 12', desc: 'Ages 12–18 · Deep-dive, magazine style, exam-ready' },
]

const SAMPLES = [
  { label: '🌊 Water Cycle', text: "The water cycle describes how water evaporates from the surface of the earth, rises into the atmosphere, cools and condenses into rain or snow in clouds, and falls again to the surface as precipitation. The water falling on land collects in rivers and lakes, soil, and porous layers of rock, and much of it flows back into the oceans, where it will once more evaporate. The cycling of water in and out of the atmosphere is a significant aspect of the weather patterns on Earth." },
  { label: '🦋 Butterflies',  text: "Butterflies are beautiful flying insects with large, colourful wings. They start their lives as tiny eggs laid on leaves. The eggs hatch into caterpillars, which eat lots of leaves to grow big. Then the caterpillar forms a chrysalis around itself. Inside the chrysalis, it slowly changes and transforms into a butterfly. This amazing change is called metamorphosis. When the butterfly is ready, it breaks out of the chrysalis and flies away to drink nectar from flowers." },
  { label: '🏛️ Roman Empire', text: "The Roman Empire was one of the most powerful and influential civilisations the world has ever seen. At its height it controlled an area stretching from Scotland to Syria. It shaped the languages, laws, and religions of the Western world. Latin, the language of ancient Rome, evolved into the Romance languages — French, Spanish, Italian, Portuguese and Romanian — which are spoken by hundreds of millions of people today." },
]

export default function InputForm({ onAnalyze }) {
  const [text, setText]         = useState('')
  const [grade, setGrade]       = useState('Grade 6-12')
  const [busy, setBusy]         = useState(false)

  async function submit() {
    if (!text.trim()) return
    setBusy(true)
    await onAnalyze(text, grade)
    setBusy(false)
  }

  return (
    <div className="input-wrap">
      <div className="input-card">
        <div className="input-hero">
          <div className="input-hero-badges">
            <span className="ih-badge">🔬 Science</span>
            <span className="ih-badge">🏛️ History</span>
            <span className="ih-badge">🌍 Geography</span>
            <span className="ih-badge">📐 Maths</span>
            <span className="ih-badge">📖 English</span>
          </div>
          <div className="input-hero-icon">📚✨</div>
          <h1>Paste any lesson. Get a<br /><span>flip-book study guide!</span></h1>
          <p>Drop in any paragraph from a textbook or class notes — Study Buddy turns it into a beautiful, page-turning book with facts, a quiz, visuals and more!</p>
        </div>

        {/* Grade selector */}
        <div className="grade-section">
          <p className="grade-label">Who is this guide for?</p>
          <div className="grade-cards">
            {GRADES.map(g => (
              <button
                key={g.value}
                className={`grade-card ${grade === g.value ? 'selected' : ''}`}
                onClick={() => setGrade(g.value)}
              >
                <span className="gc-label">{g.label}</span>
                <span className="gc-desc">{g.desc}</span>
              </button>
            ))}
          </div>
        </div>

        <textarea
          className="passage-box"
          value={text}
          onChange={e => setText(e.target.value)}
          placeholder="Paste your educational passage here…"
          rows={7}
        />

        <div className="input-row">
          <div className="sample-btns">
            <span className="sample-label">Try a sample:</span>
            {SAMPLES.map((s, i) => (
              <button key={i} className="btn-sample" onClick={() => setText(s.text)}>
                {s.label}
              </button>
            ))}
          </div>
          <button
            className="btn-analyze"
            disabled={!text.trim() || busy}
            onClick={submit}
          >
            {busy ? 'Generating…' : '✨ Generate Study Book'}
          </button>
        </div>
      </div>
    </div>
  )
}
