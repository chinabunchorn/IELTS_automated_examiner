from typing import TypedDict, List, Dict
from pydantic import BaseModel, Field

# ---------------------------------------------------------
# 1. THE GLOBAL GRAPH STATE
# ---------------------------------------------------------
class EvaluationState(TypedDict):
    mode: str                              # '/full' or '/drill_intro'
    essay_text: str                        # The text the user submitted
    topic_text: str                        # The topic text injected from SQLite
    user_weaknesses: str                   # Injected from SQLite
    grammar_errors: List[Dict[str, str]]   # Populated by the Grammarian Node
    vocab_suggestions: List[Dict[str, str]] # Populated by the Lexicographer Node (if full mode)
    final_feedback: dict                   # Populated by the final Examiner Node

# ---------------------------------------------------------
# 2. NESTED ITEM SCHEMAS
# These define the shape of each ITEM inside the lists above.
# ---------------------------------------------------------

class GrammarError(BaseModel):
    error_category: str = Field(
        description="The general grammatical category of the mistake (e.g., 'Subject-Verb Agreement', 'Prepositions', 'Tense', 'Articles'). Keep it concise."
    )
    mistake: str = Field(
        description="The exact incorrect word, phrase, or sentence fragment as it appears in the original text."
    )
    correction: str = Field(
        description="The corrected version, with a brief explanation of the grammatical rule violated."
    )

class VocabSuggestion(BaseModel):
    original_word: str = Field(
        description="The basic or repetitive word/phrase from the original text."
    )
    suggestion: str = Field(
        description="A higher-level (Band 7.0+) vocabulary replacement that fits the context perfectly."
    )

# ---------------------------------------------------------
# 3. OUTPUT SCHEMAS (PYDANTIC)
# These are the top-level shapes passed to Ollama's format= parameter.
# ---------------------------------------------------------

# Node 1: Used by the Grammarian
class GrammarResponse(BaseModel):
    grammar_errors: List[GrammarError] = Field(
        description="A list of grammatical mistakes found in the text. Do NOT rewrite the text."
    )

# Node 2: Used by the Lexicographer (Full Essay Route Only)
class VocabResponse(BaseModel):
    vocab_suggestions: List[VocabSuggestion] = Field(
        description="A list of advanced vocabulary replacements for basic or repetitive words in the essay."
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