from typing import TypedDict, Optional, List, Dict, Any


class PassageState(TypedDict):
    # Input
    passage: str
    compressed_passage: str

    # Guardrail
    guardrail_status: str        # "pass" | "blocked"
    guardrail_issues: List[str]

    # Analysis (Topic Extractor)
    topic: str
    subject: str
    grade_level: str
    key_concepts: List[str]
    brief_summary: str

    # Parallel agent outputs
    article_title: str                    # Summary Agent
    article_content: str                  # Summary Agent
    quiz_questions: List[Dict[str, Any]]  # Quiz Agent
    visual_descriptions: List[Dict[str, Any]]  # Image Agent
    did_you_know_facts: List[Dict[str, Any]]   # Takeaway Agent
    key_takeaways: List[Dict[str, Any]]        # Takeaway Agent

    # Error tracking
    error: Optional[str]
