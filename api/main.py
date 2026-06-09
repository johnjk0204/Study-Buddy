"""
Study Buddy AI — FastAPI backend.

Endpoints
---------
GET  /health                      health check
POST /api/analyze                 full JSON result (waits for all agents)
POST /api/analyze/stream          SSE stream — sends partial results as each agent completes
GET  /api/render/{render_id}      serve a saved HTML report (shareable link)
GET  /api/render/{render_id}/pdf  serve a PDF download for a saved report

Run with:
    uvicorn api.main:app --port 8000 --reload
"""
import asyncio
import json
import uuid
from collections import OrderedDict
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response, StreamingResponse
from pydantic import BaseModel

from graph.state import PassageState
from graph.workflow import build_async_graph
from utils.html_renderer import render_book_html
from utils.pdf_renderer import render_pdf

# ── App ────────────────────────────────────────────────────────────────────────
app = FastAPI(title="Study Buddy AI", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── In-memory render store (last 100 HTML reports + states) ───────────────────
_renders: OrderedDict[str, str]  = OrderedDict()
_render_states: OrderedDict[str, dict] = OrderedDict()
_MAX_RENDERS = 100


def _save_render(html: str, state: dict | None = None) -> str:
    render_id = str(uuid.uuid4())[:8]
    _renders[render_id] = html
    if state is not None:
        _render_states[render_id] = dict(state)
    # Evict oldest when over limit
    while len(_renders) > _MAX_RENDERS:
        oldest = next(iter(_renders))
        _renders.pop(oldest, None)
        _render_states.pop(oldest, None)
    return render_id


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_initial_state(passage: str) -> PassageState:
    return PassageState(
        passage=passage,
        compressed_passage="",
        guardrail_status="",
        guardrail_issues=[],
        topic="",
        subject="",
        grade_level="",
        key_concepts=[],
        brief_summary="",
        article_title="",
        article_content="",
        quiz_questions=[],
        visual_descriptions=[],
        did_you_know_facts=[],
        key_takeaways=[],
        error=None,
    )


_NODE_LABELS = {
    "guardrail_check": "Checking content safety…",
    "topic_extractor": "Extracting topic and concepts…",
    "summary_agent":   "Writing article…",
    "quiz_agent":      "Generating quiz questions…",
    "image_agent":     "Finding visual aids…",
    "takeaway_agent":  "Building key takeaways…",
}

# Keys to include in SSE partial payloads (avoid sending huge HTML bodies mid-stream)
_STREAM_KEYS: dict[str, list[str]] = {
    "guardrail_check": ["guardrail_status", "guardrail_issues"],
    "topic_extractor": ["topic", "subject", "key_concepts", "brief_summary"],
    "summary_agent":   ["article_title", "article_content"],
    "quiz_agent":      ["quiz_questions"],
    "image_agent":     ["visual_descriptions"],
    "takeaway_agent":  ["key_takeaways", "did_you_know_facts"],
}


def _pick(output: dict, node: str) -> dict:
    keys = _STREAM_KEYS.get(node, list(output.keys()))
    return {k: output[k] for k in keys if k in output}


# ── Request schema ─────────────────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    passage: str


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "version": "2.0.0"}


@app.post("/api/analyze")
async def analyze(req: AnalyzeRequest) -> dict[str, Any]:
    """
    Run the full async parallel graph and return the complete result + shareable link.
    """
    if not req.passage.strip():
        raise HTTPException(status_code=422, detail="passage must not be empty")

    graph = build_async_graph()
    state = _make_initial_state(req.passage)
    final: dict = dict(state)

    async for event in graph.astream(state):
        for node_output in event.values():
            final.update(node_output)

    if final.get("guardrail_status") == "blocked":
        return {"blocked": True, "issues": final.get("guardrail_issues", [])}

    html = render_book_html(final)
    render_id = _save_render(html, state=final)

    # Strip raw passage from API response to keep payload small
    final.pop("passage", None)
    final.pop("compressed_passage", None)

    return {
        "blocked": False,
        "state": final,
        "render_id": render_id,
        "render_url": f"/api/render/{render_id}",
        "pdf_url":    f"/api/render/{render_id}/pdf",
    }


@app.post("/api/analyze/stream")
async def analyze_stream(req: AnalyzeRequest) -> StreamingResponse:
    """
    SSE stream — emits one event per agent as it completes so the
    browser can render content progressively without waiting for all agents.

    Event format:
        data: {"node": "<name>", "label": "<human label>", "payload": {...}}\n\n

    Final event:
        data: {"node": "__done__", "render_id": "...", "render_url": "..."}\n\n

    Error event:
        data: {"node": "__error__", "detail": "..."}\n\n
    """
    if not req.passage.strip():
        raise HTTPException(status_code=422, detail="passage must not be empty")

    async def event_generator():
        graph = build_async_graph()
        state = _make_initial_state(req.passage)
        final: dict = dict(state)

        try:
            async for event in graph.astream(state):
                for node, output in event.items():
                    final.update(output)

                    # Check for block immediately
                    if node == "guardrail_check" and output.get("guardrail_status") == "blocked":
                        yield _sse({"node": "__blocked__",
                                    "issues": output.get("guardrail_issues", [])})
                        return

                    payload = _pick(output, node)
                    yield _sse({
                        "node":    node,
                        "label":   _NODE_LABELS.get(node, node),
                        "payload": payload,
                    })
                    await asyncio.sleep(0)  # give the event loop a chance to flush

            # All agents done — render and save HTML + state for PDF
            html = render_book_html(final)
            render_id = _save_render(html, state=final)
            yield _sse({
                "node":       "__done__",
                "render_id":  render_id,
                "render_url": f"/api/render/{render_id}",
                "pdf_url":    f"/api/render/{render_id}/pdf",
            })

        except Exception as exc:
            yield _sse({"node": "__error__", "detail": str(exc)})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",    # tells nginx not to buffer SSE
            "Connection": "keep-alive",
        },
    )


@app.get("/api/render/{render_id}", response_class=HTMLResponse)
async def get_render(render_id: str) -> HTMLResponse:
    """Return the saved HTML report for a given render ID (shareable link)."""
    html = _renders.get(render_id)
    if not html:
        raise HTTPException(status_code=404, detail="Report not found or expired.")
    return HTMLResponse(content=html)


@app.get("/api/render/{render_id}/pdf")
async def get_render_pdf(render_id: str) -> Response:
    """
    Generate and return a PDF for a saved render ID.

    The PDF is generated on-demand from the stored HTML using WeasyPrint
    (best quality) or fpdf2 (pure-Python fallback).
    """
    html = _renders.get(render_id)
    if not html:
        raise HTTPException(status_code=404, detail="Report not found or expired.")

    # Reconstruct a minimal state from the stored HTML is not possible, so we
    # store state alongside HTML for PDF generation.
    state = _render_states.get(render_id)
    if state is None:
        raise HTTPException(
            status_code=422,
            detail="State data unavailable for this render — re-analyse the passage to get a PDF.",
        )

    try:
        pdf_bytes = await asyncio.get_event_loop().run_in_executor(
            None, render_pdf, state
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {exc}") from exc

    slug = (state.get("topic") or "report").replace(" ", "_")[:40]
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="study_buddy_{slug}.pdf"'},
    )


# ── Utility ────────────────────────────────────────────────────────────────────

def _sse(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
