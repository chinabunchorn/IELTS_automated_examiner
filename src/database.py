import sqlite3
import json
import os

# Get the absolute path of the project root folder
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "state.sqlite")

def init_db():
    """Creates the tables and seeds seed data if missing."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS Users (user_id INTEGER PRIMARY KEY, username TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS Essays (essay_id INTEGER PRIMARY KEY, user_id INTEGER, mode TEXT, original_text TEXT, feedback_json TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS UserWeaknesses (weakness_id INTEGER PRIMARY KEY, user_id INTEGER, category TEXT, description TEXT)''')
        
        # Seed logic
        cursor.execute('SELECT COUNT(*) FROM Users')
        if cursor.fetchone()[0] == 0:
            cursor.execute('INSERT INTO Users (username) VALUES ("Chin_Test")')
            cursor.execute('INSERT INTO UserWeaknesses (user_id, category, description) VALUES (1, "Grammar", "Frequent misuse of Present Perfect tense.")')
            cursor.execute('INSERT INTO UserWeaknesses (user_id, category, description) VALUES (1, "Coherence", "Struggles to write a clear thesis statement.")')
        conn.commit()

def get_user_weaknesses(user_id: int) -> str:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT category, description FROM UserWeaknesses WHERE user_id = ?', (user_id,))
        rows = cursor.fetchall()
        if not rows:
            return "No known weaknesses recorded yet."
        weaknesses = [f"- {row[0]}: {row[1]}" for row in rows]
        return "\n".join(weaknesses)

def save_evaluation(user_id: int, mode: str, original_text: str, feedback_dict: dict):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        feedback_json = json.dumps(feedback_dict)
        cursor.execute('''
            INSERT INTO Essays (user_id, mode, original_text, feedback_json)
            VALUES (?, ?, ?, ?)
        ''', (user_id, mode, original_text, feedback_json))
        conn.commit()