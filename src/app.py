import chainlit as cl
import json

# Import your compiled LangGraph pipeline
from workflow import ielts_pipeline
from database import get_user_weaknesses, save_evaluation
from database import get_user_weaknesses, save_evaluation, init_db, get_random_topic

@cl.on_chat_start
@cl.on_chat_start
async def on_chat_start():
    """Runs when the web server boots up for the user."""
    # Ensure the database tables exist before any queries are made!
    init_db()
    
    welcome_message = """
    **Welcome to the Local-First IELTS Evaluator.** 🚀
    
    I am a strict, deterministic evaluation pipeline. I will NOT rewrite your essay.
    
    **Available Commands:**
    * `/topic` - Get a random IELTS Task 2 topic.
    * `/drill_intro [your text]` - Fast analysis of an introduction paragraph.
    * `/full [your text]` - Complete 4-criteria evaluation of a full essay.
    """
    await cl.Message(content=welcome_message).send()

@cl.on_message
async def main(message: cl.Message):
    """Handles incoming user messages and orchestrates the UI loading state."""
    
    text = message.content.strip()
    
    # 1. Parse the Command
    mode = None
    essay_text = ""

    if text.startswith("/topic"):
        topic_data = get_random_topic()
        topic_text = topic_data.get("topic_text", "No topic found.")
        cl.user_session.set("current_topic", topic_text)
        await cl.Message(content=f"**Here's your IELTS Task 2 Topic:**\n\n{topic_text}\n\n"
                                 f"Now you can write your essay using `/full [your essay]` "
                                 f"or `/drill_intro [your introduction]`.").send()
        return
    elif text.startswith("/drill_intro"):
        mode = "/drill_intro"
        essay_text = text.replace("/drill_intro", "").strip()
    elif text.startswith("/full"):
        mode = "/full"
        essay_text = text.replace("/full", "").strip()
    else:
        await cl.Message(content="⚠️ Please start your message with `/topic`, `/full` or `/drill_intro`.").send()
        return
        
    if not essay_text:
        await cl.Message(content="⚠️ Please provide an essay after the command.").send()
        return

    # Retrieve current topic from session
    current_topic = cl.user_session.get("current_topic")
    if not current_topic:
        await cl.Message(content="⚠️ Please request a topic first using `/topic` before submitting your writing.").send()
        return

    # 2. Setup the Initial State (Now pulling from SQLite!)
    user_id = 1 # Hardcoded for local testing
    live_weaknesses = get_user_weaknesses(user_id)
    
    initial_state = {
        "mode": mode,
        "essay_text": essay_text,
        "topic_text": current_topic, # Inject the topic here
        "user_weaknesses": live_weaknesses, 
        "grammar_errors": [],
        "vocab_suggestions": [],
        "final_feedback": {}
    }

    # 3. Stream the LangGraph execution to the UI
    final_state = None
    
    # LangGraph's .astream() yields updates after every node finishes!
    async for event in ielts_pipeline.astream(initial_state):
        for node_name, node_state in event.items():
            
            # Create a loading step in the Chainlit UI for the current node
            async with cl.Step(name=f"Agent: {node_name.capitalize()}") as step:
                step.output = f"Finished processing."
            
            # Keep track of the latest state
            final_state = node_state

    # 4. Format the final Pydantic JSON output into a beautiful Markdown message
    feedback = final_state.get("final_feedback", {})
    
    if mode == "/drill_intro":
        ui_response = f"""
### 🎯 Introduction Drill Evaluation

**Topic:**
{current_topic}

**Hook Analysis:**
{feedback.get('hook_evaluation', 'N/A')}

**Thesis Clarity:**
{feedback.get('thesis_clarity', 'N/A')}

**💡 Actionable Advice:**
{feedback.get('actionable_advice', 'N/A')}
        """
    else:
        ui_response = f"""
### 📝 Full Essay Evaluation
**Estimated Band Score: {feedback.get('band_score', 'N/A')}**

**Topic:**
{current_topic}

**Overall Comments:**
{feedback.get('overall_comments', 'N/A')}

*(Check the agent steps above for specific grammar and vocabulary feedback!)*
        """

    # Send the final formatted message to the user
    
    save_evaluation(user_id, mode, essay_text, feedback)
    await cl.Message(content=ui_response).send()
