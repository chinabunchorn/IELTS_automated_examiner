import sqlite3
import json
import os

# Get the absolute path of the project root folder
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "state.sqlite")
TOPICS_FILE_PATH = os.path.join(BASE_DIR, "data", "topics.json")
def init_db():
    """Creates the tables and seeds seed data if missing."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS Users (user_id INTEGER PRIMARY KEY, username TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS Essays (essay_id INTEGER PRIMARY KEY, user_id INTEGER, mode TEXT, original_text TEXT, feedback_json TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS UserWeaknesses (weakness_id INTEGER PRIMARY KEY, user_id INTEGER, category TEXT, description TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS Topics (topic_id INTEGER PRIMARY KEY, topic_text TEXT NOT NULL)''')
        
        # Seed logic for Users and UserWeaknesses
        cursor.execute('SELECT COUNT(*) FROM Users')
        if cursor.fetchone()[0] == 0:
            cursor.execute('INSERT INTO Users (username) VALUES ("Chin_Test")')

        # Seed logic for Topics from topics.json
        cursor.execute('SELECT COUNT(*) FROM Topics')
        if cursor.fetchone()[0] == 0:
            if os.path.exists(TOPICS_FILE_PATH):
                with open(TOPICS_FILE_PATH, 'r', encoding='utf-8') as f:
                    topics_data = json.load(f)
                
                # ดึงเฉพาะ value จาก key "topic_text" ของแต่ละ dictionary
                topics_to_insert = [(topic['topic_text'],) for topic in topics_data]
                
                cursor.executemany('INSERT INTO Topics (topic_text) VALUES (?)', topics_to_insert)
                print("✅ Seeded topics from JSON successfully.")
            else:
                print(f"⚠️ Warning: topics.json not found at {TOPICS_FILE_PATH}. No topics seeded.")

def get_user_weaknesses(user_id: int) -> str:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT category, description FROM UserWeaknesses WHERE user_id = ?', (user_id,))
        rows = cursor.fetchall()
        if not rows:
            return "No known weaknesses recorded yet."
        weaknesses = [f"- {row[0]}: {row[1]}" for row in rows]
        return "\n".join(weaknesses)

def save_evaluation(user_id: int, mode: str, original_text: str, feedback_dict: dict, grammar_errors: list = None):
    print(f"\n[DEBUG - Database] ข้อมูลที่รับเข้ามาเพื่อ Save:\nMode: {mode}\nFeedback Keys: {feedback_dict.keys()}\nGrammar Errors: {len(grammar_errors) if grammar_errors else 0} items\n")
    
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        feedback_json = json.dumps(feedback_dict)
        cursor.execute('''
            INSERT INTO Essays (user_id, mode, original_text, feedback_json)
            VALUES (?, ?, ?, ?)
        ''', (user_id, mode, original_text, feedback_json))
        
        if grammar_errors:
            for error in grammar_errors:
                if isinstance(error, dict) and "error_category" in error and "mistake" in error:
                    category = error["error_category"]
                    description = f"Mistake: {error['mistake']} | Correction: {error['correction']}"
                    
                    cursor.execute('''
                        INSERT INTO UserWeaknesses (user_id, category, description)
                        VALUES (?, ?, ?)
                    ''', (user_id, category, description))
        
        conn.commit()
        print("[DEBUG - Database] Transaction Completed: Saved Essay and Updated Weaknesses.")

def get_random_topic() -> dict:
    """Queries the database, picks one random topic, and returns it as a dictionary."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row # This allows access by column name
        cursor = conn.cursor()
        cursor.execute('SELECT topic_id, topic_text FROM Topics ORDER BY RANDOM() LIMIT 1')
        row = cursor.fetchone()
        if row:
            return dict(row)
        return {"topic_id": None, "topic_text": "No topics available."}
