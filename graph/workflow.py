"""LangGraph StateGraph — sync (Streamlit) and async parallel (FastAPI) graphs."""
from langgraph.graph import StateGraph, END, START

from graph.state import PassageState
from agents.guardrail import guardrail_agent
from agents.analyzer import analyzer_agent
from agents.article import article_agent
from agents.content_generator import content_generator_agent


def _route_guardrail(state: PassageState) -> str:
    return "blocked" if state.get("guardrail_status") == "blocked" else "continue"


def build_graph():
    """
    Sync graph for Streamlit:
      guardrail → analyzer → article_writer → content_generator (sequential)
    """
    g = StateGraph(PassageState)

    g.add_node("guardrail_check",   guardrail_agent)
    g.add_node("smart_analyzer",    analyzer_agent)
    g.add_node("article_writer",    article_agent)
    g.add_node("content_generator", content_generator_agent)

    g.add_edge(START, "guardrail_check")
    g.add_conditional_edges(
        "guardrail_check",
        _route_guardrail,
        {"blocked": END, "continue": "smart_analyzer"},
    )
    g.add_edge("smart_analyzer",    "article_writer")
    g.add_edge("article_writer",    "content_generator")
    g.add_edge("content_generator", END)

    return g.compile()


def build_async_graph():
    """
    Async parallel graph for FastAPI + SSE:

      START
        └─ guardrail_check   (safety screen)
              ├─ blocked → END
              └─ pass
                  └─ topic_extractor   (compress + analyze)
                        ├─ summary_agent    ┐
                        ├─ quiz_agent       │  all 4 run concurrently
                        ├─ image_agent      │  via asyncio
                        └─ takeaway_agent   ┘
                              └─ END  (outputs merged into shared state)
    """
    from agents.guardrail import async_guardrail_agent
    from agents.analyzer import async_analyzer_agent
    from agents.article import async_article_agent
    from agents.quiz import async_quiz_agent
    from agents.visuals import async_visuals_agent
    from agents.takeaways import async_takeaways_agent

    g = StateGraph(PassageState)

    g.add_node("guardrail_check",  async_guardrail_agent)
    g.add_node("topic_extractor",  async_analyzer_agent)
    g.add_node("summary_agent",    async_article_agent)
    g.add_node("quiz_agent",       async_quiz_agent)
    g.add_node("image_agent",      async_visuals_agent)
    g.add_node("takeaway_agent",   async_takeaways_agent)

    g.add_edge(START, "guardrail_check")
    g.add_conditional_edges(
        "guardrail_check",
        _route_guardrail,
        {"blocked": END, "continue": "topic_extractor"},
    )

    # Fan-out: all 4 agents run in parallel after topic_extractor
    g.add_edge("topic_extractor", "summary_agent")
    g.add_edge("topic_extractor", "quiz_agent")
    g.add_edge("topic_extractor", "image_agent")
    g.add_edge("topic_extractor", "takeaway_agent")

    g.add_edge("summary_agent",  END)
    g.add_edge("quiz_agent",     END)
    g.add_edge("image_agent",    END)
    g.add_edge("takeaway_agent", END)

    return g.compile()
