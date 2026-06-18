from typing import TypedDict, List
from pydantic import BaseModel, Field

class EvaluationState(TypedDict):
    mode: str                  
    essay_text: str            
    user_weaknesses: str      
    grammar_errors: List[str]  
    vocab_suggestions: List[str] 
    final_feedback: dict      

# OUTPUT SCHEMAS
class GrammarResponse(BaseModel):
    grammar_errors: List[str] = Field(
        description="A list of specific grammatical mistakes found in the text. Provide the error and a brief correction. Do NOT rewrite the text."
    )

class IntroExaminerResponse(BaseModel):
    hook_evaluation: str = Field(
        description="Critique of the opening sentence. Does it grab attention and introduce the topic?"
    )
    thesis_clarity: str = Field(
        description="Critique of the thesis statement. Is the writer's position clear?"
    )
    actionable_advice: str = Field(
        description="One specific tip to make this introduction stronger."
    )