from typing import TypedDict, List
from pydantic import BaseModel, Field

# ---------------------------------------------------------
# 1. THE GLOBAL GRAPH STATE
# ---------------------------------------------------------
class EvaluationState(TypedDict):
    mode: str                  # '/full' or '/drill_intro'
    essay_text: str            # The text the user submitted
    topic_text: str            # The topic text injected from SQLite
    user_weaknesses: str       # Injected from SQLite
    grammar_errors: List[str]  # Populated by the Grammarian Node
    vocab_suggestions: List[str] # Populated by the Lexicographer Node (if full mode)
    final_feedback: dict       # Populated by the final Examiner Node

# ---------------------------------------------------------
# 2. OUTPUT SCHEMAS (PYDANTIC)
# Forcing Ollama to return strict JSON shapes
# ---------------------------------------------------------

# Node 1: Used by the Grammarian
class GrammarResponse(BaseModel):
    grammar_errors: List[str] = Field(
        description="A list of specific grammatical mistakes found in the text. Provide the error and a brief correction. Do NOT rewrite the text."
    )

# Node 2: Used by the Lexicographer (Full Essay Route Only)
class VocabResponse(BaseModel):
    vocab_suggestions: List[str] = Field(
        description="A list of advanced, higher-level vocabulary options (Band 7.0+) that can replace basic or repetitive words used in the essay."
    )

# Node 3A: Used by the Intro Examiner
class IntroExaminerResponse(BaseModel):
    hook_evaluation: str = Field(
        description="Critique of the opening sentence. Does it grab attention and introduce the topic effectively?"
    )
    thesis_clarity: str = Field(
        description="Critique of the thesis statement. Is the writer's position obvious and directly answering the prompt?"
    )
    actionable_advice: str = Field(
        description="One specific piece of tactical advice to make this introduction hit a Band 7.0+ standard."
    )

# Node 3B: Used by the Full Essay Examiner
class FullExaminerResponse(BaseModel):
    band_score: float = Field(
        description="Estimated overall IELTS band score from 0.0 to 9.0, rounded to the nearest half-band (e.g., 6.5, 7.0)."
    )
    overall_comments: str = Field(
        description="A high-level diagnostic summary evaluating Task Achievement and Coherence & Cohesion."
    )
