import json
import os
from typing import TypedDict, List
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END
from ollama import Client

# Import from your models.py
# Assuming you added VocabResponse and FullExaminerResponse there
from models import EvaluationState, GrammarResponse, IntroExaminerResponse, VocabResponse, FullExaminerResponse

# Initialize the local Ollama client
client = Client(host='http://localhost:11434')

# --- HELPER FUNCTION ---
def read_rubric(filename: str) -> str:
    filepath = os.path.join("data", "rubrics", filename)
    with open(filepath, "r", encoding="utf-8") as file:
        return file.read()

# --- AGENT 1: THE GRAMMARIAN ---
def grammar_node(state: EvaluationState):
    prompt = f"""
    You are a strict grammatical analyzer for IELTS writing. Your ONLY job is to identify errors in syntax, spelling, and punctuation.

    USER HISTORY (Focus on these weaknesses):
    {state['user_weaknesses']}

    INSTRUCTIONS:
    1. Analyze the provided text for grammatical errors.
    2. Provide the mistake and a brief correction.
    3. ABSOLUTE RULE: DO NOT rewrite the essay for the user. 
    4. Output strictly in JSON format.

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

# --- AGENT 2: THE LEXICOGRAPHER (Full Route Only) ---
def vocab_node(state: EvaluationState):
    prompt = f"""
    You are an IELTS Lexical Resource expert. 
    
    INSTRUCTIONS:
    1. Identify basic or repetitive vocabulary in the text.
    2. Suggest higher-level (Band 7.0+) replacements.
    3. Ensure suggestions fit the context perfectly. Do not change the original meaning.
    4. Output strictly in JSON format.

    TEXT TO ANALYZE:
    {state['essay_text']}
    """
    response = client.chat(
        model='llama3.1',
        messages=[{'role': 'user', 'content': prompt}],
        format=VocabResponse.model_json_schema(),
        options={'temperature': 0.2}
    )
    result = json.loads(response['message']['content'])
    return {"vocab_suggestions": result.get("vocab_suggestions", [])}

# --- AGENT 3A: THE INTRO EXAMINER ---
def intro_examiner_node(state: EvaluationState):
    rubric_text = read_rubric("intro_drill.md")
    prompt = f"""
    You are a Senior IELTS Examiner evaluating an isolated introduction paragraph. 

    TOPIC:
    {state['topic_text']}

    EVALUATION RUBRIC:
    {rubric_text}

    GRAMMAR CHECK PASSED:
    Errors found: {state['grammar_errors']}
    Do not focus on grammar. Focus ONLY on structure.

    INSTRUCTIONS:
    1. Evaluate the "Hook" and "Thesis Clarity".
    2. Provide one piece of actionable advice.
    3. DO NOT write a new introduction. 
    4. Output strictly in JSON format.

    TEXT:
    {state['essay_text']}
    """
    response = client.chat(
        model='llama3.1',
        messages=[{'role': 'system', 'content': prompt}],
        format=IntroExaminerResponse.model_json_schema(),
        options={'temperature': 0.1}
    )
    return {"final_feedback": json.loads(response['message']['content'])}

# --- AGENT 3B: THE FULL EXAMINER ---
def full_examiner_node(state: EvaluationState):
    rubric_text = read_rubric("full_essay.md")
    prompt = f"""
    You are the Lead Senior IELTS Examiner. Calculate a final Band Score for this full essay.

    TOPIC:
    {state['topic_text']}

    EVALUATION RUBRIC:
    {rubric_text}

    PREVIOUS ANALYSIS:
    - Grammar Errors: {state['grammar_errors']}
    - Vocab Suggestions: {state.get('vocab_suggestions', [])}
    Use these to inform your Lexical Resource and Grammatical Range scoring. Do not list them again.

    INSTRUCTIONS:
    1. Calculate the estimated overall Band Score (0.0 to 9.0).
    2. Write a diagnostic "overall comments" summary focusing on Task Achievement and Coherence.
    3. DO NOT write a new essay.
    4. Output strictly in JSON format.

    TEXT:
    {state['essay_text']}
    """
    response = client.chat(
        model='llama3.1',
        messages=[{'role': 'system', 'content': prompt}],
        format=FullExaminerResponse.model_json_schema(),
        options={'temperature': 0.1}
    )
    return {"final_feedback": json.loads(response['message']['content'])}

# --- THE ROUTER ---
def route_evaluation(state: EvaluationState):
    if state["mode"] == "/drill_intro":
        return "intro_examiner"
    return "vocab"

# --- BUILD THE ORCHESTRATOR ---
workflow = StateGraph(EvaluationState)

workflow.add_node("grammar", grammar_node)
workflow.add_node("vocab", vocab_node)
workflow.add_node("intro_examiner", intro_examiner_node)
workflow.add_node("full_examiner", full_examiner_node)

workflow.add_edge(START, "grammar")

workflow.add_conditional_edges(
    "grammar",
    route_evaluation,
    {
        "intro_examiner": "intro_examiner",
        "vocab": "vocab"
    }
)

# Vocab always leads to the full examiner
workflow.add_edge("vocab", "full_examiner")

workflow.add_edge("intro_examiner", END)
workflow.add_edge("full_examiner", END)

ielts_pipeline = workflow.compile()
