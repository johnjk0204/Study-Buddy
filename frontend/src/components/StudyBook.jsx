import { useRef, useState } from 'react'
import HTMLFlipBook from 'react-pageflip'
import { getTheme } from '../theme'
import CoverPage     from './pages/CoverPage'
import OverviewPage  from './pages/OverviewPage'
import FactsPage     from './pages/FactsPage'
import VisualsPage   from './pages/VisualsPage'
import TakeawaysPage from './pages/TakeawaysPage'
import QuizPage      from './pages/QuizPage'
import ArticlePage   from './pages/ArticlePage'
import ClosingPage   from './pages/ClosingPage'
import './StudyBook.css'

const PAGE_W = 460
const PAGE_H = 640

export default function StudyBook({ state }) {
  const bookRef    = useRef()
  const [page, setPage] = useState(0)

  const theme    = getTheme(state.subject)
  const allPages = [
    CoverPage, OverviewPage, FactsPage, VisualsPage,
    TakeawaysPage, QuizPage, ArticlePage, ClosingPage,
  ]
  const total = allPages.length

  function prev() { bookRef.current?.pageFlip().flipPrev() }
  function next() { bookRef.current?.pageFlip().flipNext() }

  return (
    <div className="book-shell">
      {/* Navigation arrows */}
      <button
        className={`nav-arrow nav-left ${page === 0 ? 'hidden' : ''}`}
        onClick={prev}
        aria-label="Previous page"
      >
        ‹
      </button>

      <div className="book-stage">
        <HTMLFlipBook
          ref={bookRef}
          width={PAGE_W}
          height={PAGE_H}
          size="fixed"
          minWidth={PAGE_W}
          maxWidth={PAGE_W}
          minHeight={PAGE_H}
          maxHeight={PAGE_H}
          drawShadow
          flippingTime={700}
          usePortrait={false}
          startPage={0}
          showCover
          mobileScrollSupport={false}
          onFlip={e => setPage(e.data)}
          className="the-book"
        >
          {allPages.map((PageComp, i) => (
            <PageComp key={i} state={state} theme={theme} pageNum={i + 1} total={total} />
          ))}
        </HTMLFlipBook>
      </div>

      <button
        className={`nav-arrow nav-right ${page >= total - 1 ? 'hidden' : ''}`}
        onClick={next}
        aria-label="Next page"
      >
        ›
      </button>

      {/* Bottom bar */}
      <div className="book-footer">
        <div className="page-dots">
          {allPages.map((_, i) => (
            <button
              key={i}
              className={`dot ${i === page ? 'active' : ''}`}
              onClick={() => bookRef.current?.pageFlip().flip(i)}
              aria-label={`Go to page ${i + 1}`}
            />
          ))}
        </div>
        <span className="page-counter">{page + 1} / {total}</span>
      </div>

      {/* Download bar */}
      {(state._renderUrl || state._pdfUrl) && (
        <div className="download-bar">
          <span className="dl-label">⬇ Download your study guide</span>
          <div className="dl-btns">
            {state._renderUrl && (
              <a
                className="dl-btn dl-html"
                href={state._renderUrl}
                target="_blank"
                rel="noopener noreferrer"
                download
              >
                <span className="dl-icon">🌐</span>
                <span>HTML</span>
              </a>
            )}
            {state._pdfUrl && (
              <a
                className="dl-btn dl-pdf"
                href={state._pdfUrl}
                download
              >
                <span className="dl-icon">📄</span>
                <span>PDF</span>
              </a>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
