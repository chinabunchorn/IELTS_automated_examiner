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
        cursor.execute('''CREATE TABLE IF NOT EXISTS Topics (topic_id INTEGER PRIMARY KEY, topic_text TEXT NOT NULL)''')
        
        # Seed logic for Users and UserWeaknesses
        cursor.execute('SELECT COUNT(*) FROM Users')
        if cursor.fetchone()[0] == 0:
            cursor.execute('INSERT INTO Users (username) VALUES ("Chin_Test")')
            cursor.execute('INSERT INTO UserWeaknesses (user_id, category, description) VALUES (1, "Grammar", "Frequent misuse of Present Perfect tense.")')
            cursor.execute('INSERT INTO UserWeaknesses (user_id, category, description) VALUES (1, "Coherence", "Struggles to write a clear thesis statement.")')

        # Seed logic for Topics
        cursor.execute('SELECT COUNT(*) FROM Topics')
        if cursor.fetchone()[0] == 0:
            topics_to_insert = [
                ("Some people believe that the best way to improve public health is by increasing the number of sports facilities. Others think that this is not enough and that other measures are required. Discuss both views and give your own opinion.",),
                ("In many countries, owning a home is considered a fundamental right. However, for many people, this is becoming increasingly difficult. What are the reasons for this? What can be done to address this problem?",),
                ("Technological advancements have made it possible for many people to work from home. Do the advantages of this outweigh the disadvantages for both individuals and companies?",)
            ]
            cursor.executemany('INSERT INTO Topics (topic_text) VALUES (?)', topics_to_insert)
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
