import os
from ollama import Client

from models import EvaluationState, GrammarResponse, IntroExaminerResponse

client = Client(host='http://localhost:11434')

# --- HELPER FUNCTION ---
def read_rubric(filename: str) -> str:
    """Reads the static markdown rubrics you just created."""
    filepath = os.path.join("data", "rubrics", filename)
    with open(filepath, "r", encoding="utf-8") as file:
        return file.read()

# --- AGENT 1: THE GRAMMARIAN ---
def grammar_node(state: EvaluationState):
    """Checks for syntax errors without rewriting the essay."""
    
    prompt = f"""
    You are a strict grammatical analyzer for IELTS writing. Your ONLY job is to identify errors in syntax, spelling, and punctuation.

    USER HISTORY (Focus on these weaknesses):
    {state['user_weaknesses']}

    INSTRUCTIONS:
    1. Analyze the provided text for grammatical errors.
    2. Provide the mistake and a brief correction.
    3. ABSOLUTE RULE: DO NOT rewrite the essay for the user. 
    4. Output strictly in the requested JSON format.

    TEXT TO ANALYZE:
    {state['essay_text']}
    """
    
    response = client.chat(
        model='llama3.1',
        messages=[{'role': 'user', 'content': prompt}],
        format=GrammarResponse.model_json_schema(),
        options={'temperature': 0.0} 
    )
    
    result = json.loads(response['message']['content'])
    
    return {"grammar_errors": result.get("grammar_errors", [])}


# --- AGENT 2: THE INTRO EXAMINER ---
def intro_examiner_node(state: EvaluationState):
    """Evaluates the hook and thesis using the static rubric."""
    
    rubric_text = read_rubric("intro_drill.md")
    
    prompt = f"""
    You are a Senior IELTS Examiner evaluating an isolated introduction paragraph. 

    EVALUATION RUBRIC:
    {rubric_text}

    GRAMMAR CHECK PASSED:
    Here are the grammatical errors found by the previous agent:
    {state['grammar_errors']}
    Do not focus on grammar. Focus ONLY on structure and argument.

    INSTRUCTIONS:
    1. Evaluate the "Hook". Does it effectively paraphrase the prompt without copying?
    2. Evaluate the "Thesis Clarity". Is the writer's position obvious?
    3. Provide one piece of actionable advice to reach Band 7.0+.
    4. ABSOLUTE RULE: DO NOT write a new introduction. 
    5. Output strictly in JSON format.

    TEXT TO EVALUATE:
    {state['essay_text']}
    """
    
    response = client.chat(
        model='llama3.1',
        messages=[{'role': 'system', 'content': prompt}],
        format=IntroExaminerResponse.model_json_schema(),
        options={'temperature': 0.1}
    )
    
    result = json.loads(response['message']['content'])
    
    return {"final_feedback": result}