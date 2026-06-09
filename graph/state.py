from typing import TypedDict, Optional, List, Dict, Any


class PassageState(TypedDict):
    # Input
    passage: str
    compressed_passage: str
    requested_grade: str          # selected by user: "Grade 1-2" | "Grade 3-5" | "Grade 6-12"

    # Guardrail
    guardrail_status: str         # "pass" | "blocked"
    guardrail_issues: List[str]

    # Analysis (Topic Extractor)
    topic: str
    subject: str
    grade_level: str              # auto-detected from passage
    key_concepts: List[str]
    brief_summary: str

    # Parallel agent outputs
    article_title: str
    article_content: str
    quiz_questions: List[Dict[str, Any]]
    visual_descriptions: List[Dict[str, Any]]
    did_you_know_facts: List[Dict[str, Any]]
    key_takeaways: List[Dict[str, Any]]

    # Error tracking
    error: Optional[str]
