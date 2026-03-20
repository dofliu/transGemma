"""
Language learning progress tracker with Spaced Repetition (SM-2 algorithm).
"""

import json
import math
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class LearningManager:
    """Manages vocabulary cards, learning sessions, and spaced repetition scheduling."""

    def __init__(self, db_path: str = "history.db"):
        self.db_path = db_path
        self._init_tables()

    def _init_tables(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Vocabulary flashcard table with SM-2 fields
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS vocabulary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT NOT NULL,
            part_of_speech TEXT DEFAULT '',
            meaning TEXT NOT NULL,
            example_sentence TEXT DEFAULT '',
            example_translation TEXT DEFAULT '',
            source_lang TEXT NOT NULL,
            target_lang TEXT NOT NULL,
            created_at TEXT NOT NULL,
            -- SM-2 spaced repetition fields
            ease_factor REAL DEFAULT 2.5,
            interval_days INTEGER DEFAULT 0,
            repetitions INTEGER DEFAULT 0,
            next_review TEXT NOT NULL,
            last_reviewed TEXT DEFAULT '',
            UNIQUE(word, source_lang, target_lang)
        )
        """)

        # Learning session log
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS learning_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_type TEXT NOT NULL,
            source_lang TEXT,
            target_lang TEXT,
            score REAL DEFAULT 0,
            details TEXT DEFAULT '{}',
            created_at TEXT NOT NULL
        )
        """)

        conn.commit()
        conn.close()

    # ── Vocabulary CRUD ──

    def add_vocabulary(self, word: str, meaning: str, source_lang: str,
                       target_lang: str, part_of_speech: str = "",
                       example_sentence: str = "",
                       example_translation: str = "") -> int:
        """Add a word to the vocabulary bank. Returns the row id."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        try:
            cursor.execute("""
            INSERT OR IGNORE INTO vocabulary
                (word, part_of_speech, meaning, example_sentence, example_translation,
                 source_lang, target_lang, created_at, next_review)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (word, part_of_speech, meaning, example_sentence,
                  example_translation, source_lang, target_lang, now, now))
            conn.commit()
            return cursor.lastrowid or 0
        finally:
            conn.close()

    def add_vocabulary_batch(self, cards: List[Dict]) -> int:
        """Add multiple vocabulary cards at once. Returns count of inserted rows."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        count = 0
        for card in cards:
            try:
                cursor.execute("""
                INSERT OR IGNORE INTO vocabulary
                    (word, part_of_speech, meaning, example_sentence, example_translation,
                     source_lang, target_lang, created_at, next_review)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    card.get("word", ""),
                    card.get("part_of_speech", ""),
                    card.get("meaning", ""),
                    card.get("example_sentence", ""),
                    card.get("example_translation", ""),
                    card.get("source_lang", "en_US"),
                    card.get("target_lang", "zh_TW"),
                    now, now,
                ))
                if cursor.rowcount > 0:
                    count += 1
            except sqlite3.IntegrityError:
                pass
        conn.commit()
        conn.close()
        return count

    def get_vocabulary(self, source_lang: Optional[str] = None,
                       target_lang: Optional[str] = None,
                       limit: int = 100) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = "SELECT * FROM vocabulary"
        params: list = []
        conditions = []
        if source_lang:
            conditions.append("source_lang = ?")
            params.append(source_lang)
        if target_lang:
            conditions.append("target_lang = ?")
            params.append(target_lang)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    def get_due_cards(self, source_lang: Optional[str] = None,
                      target_lang: Optional[str] = None,
                      limit: int = 20) -> List[Dict]:
        """Get cards due for review (next_review <= now)."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        now = datetime.now().isoformat()

        query = "SELECT * FROM vocabulary WHERE next_review <= ?"
        params: list = [now]
        if source_lang:
            query += " AND source_lang = ?"
            params.append(source_lang)
        if target_lang:
            query += " AND target_lang = ?"
            params.append(target_lang)
        query += " ORDER BY next_review ASC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    def delete_vocabulary(self, word_id: int) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM vocabulary WHERE id = ?", (word_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted

    # ── SM-2 Spaced Repetition ──

    def review_card(self, card_id: int, quality: int) -> Dict:
        """
        Update a card after review using SM-2 algorithm.

        quality: 0-5 rating
            0 - Complete blackout
            1 - Incorrect, but remembered upon seeing answer
            2 - Incorrect, but easy to recall after seeing answer
            3 - Correct with serious difficulty
            4 - Correct with some hesitation
            5 - Perfect recall
        """
        quality = max(0, min(5, quality))
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM vocabulary WHERE id = ?", (card_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return {"error": "Card not found"}

        ef = row["ease_factor"]
        interval = row["interval_days"]
        reps = row["repetitions"]

        # SM-2 algorithm
        if quality >= 3:  # correct
            if reps == 0:
                interval = 1
            elif reps == 1:
                interval = 6
            else:
                interval = max(1, round(interval * ef))
            reps += 1
        else:  # incorrect — reset
            reps = 0
            interval = 1

        # Update ease factor
        ef = ef + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        ef = max(1.3, ef)

        now = datetime.now()
        next_review = (now + timedelta(days=interval)).isoformat()

        cursor.execute("""
        UPDATE vocabulary
        SET ease_factor = ?, interval_days = ?, repetitions = ?,
            next_review = ?, last_reviewed = ?
        WHERE id = ?
        """, (ef, interval, reps, next_review, now.isoformat(), card_id))

        conn.commit()
        conn.close()

        return {
            "card_id": card_id,
            "quality": quality,
            "new_ease_factor": round(ef, 2),
            "new_interval_days": interval,
            "next_review": next_review,
        }

    # ── Learning Sessions ──

    def log_session(self, session_type: str, source_lang: str = "",
                    target_lang: str = "", score: float = 0,
                    details: Optional[Dict] = None) -> int:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute("""
        INSERT INTO learning_sessions (session_type, source_lang, target_lang, score, details, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (session_type, source_lang, target_lang, score,
              json.dumps(details or {}, ensure_ascii=False), now))
        conn.commit()
        row_id = cursor.lastrowid
        conn.close()
        return row_id or 0

    def get_sessions(self, session_type: Optional[str] = None,
                     limit: int = 50) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = "SELECT * FROM learning_sessions"
        params: list = []
        if session_type:
            query += " WHERE session_type = ?"
            params.append(session_type)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    # ── Dashboard Stats ──

    def get_stats(self) -> Dict:
        """Return aggregated learning statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM vocabulary")
        total_words = cursor.fetchone()[0]

        now = datetime.now().isoformat()
        cursor.execute("SELECT COUNT(*) FROM vocabulary WHERE next_review <= ?", (now,))
        due_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM vocabulary WHERE repetitions >= 3")
        mastered = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM learning_sessions")
        total_sessions = cursor.fetchone()[0]

        cursor.execute("""
        SELECT session_type, COUNT(*) as cnt, ROUND(AVG(score), 1) as avg_score
        FROM learning_sessions GROUP BY session_type
        """)
        session_breakdown = {
            row[0]: {"count": row[1], "avg_score": row[2]}
            for row in cursor.fetchall()
        }

        cursor.execute("""
        SELECT DATE(created_at) as day, COUNT(*) as cnt
        FROM learning_sessions
        WHERE created_at >= ?
        GROUP BY day ORDER BY day
        """, ((datetime.now() - timedelta(days=7)).isoformat(),))
        weekly_activity = {row[0]: row[1] for row in cursor.fetchall()}

        conn.close()

        return {
            "total_words": total_words,
            "due_for_review": due_count,
            "mastered": mastered,
            "total_sessions": total_sessions,
            "session_breakdown": session_breakdown,
            "weekly_activity": weekly_activity,
        }


# Singleton
learning_manager = LearningManager()
