"""Smoke tests for the learning module (vocabulary, SM-2, sessions, stats)."""

import os
import sqlite3
import tempfile
import unittest

# Use a temp DB so tests don't pollute the real database
_TEST_DB = os.path.join(tempfile.gettempdir(), "tg_test_learning.db")


def _fresh_manager():
    """Create a LearningManager backed by a fresh temp DB."""
    if os.path.exists(_TEST_DB):
        os.remove(_TEST_DB)
    from learning import LearningManager
    return LearningManager(db_path=_TEST_DB)


class TestVocabularyCRUD(unittest.TestCase):
    def setUp(self):
        self.mgr = _fresh_manager()

    def tearDown(self):
        if os.path.exists(_TEST_DB):
            os.remove(_TEST_DB)

    def test_add_and_retrieve_vocabulary(self):
        rid = self.mgr.add_vocabulary(
            word="postpone", meaning="延期",
            source_lang="en_US", target_lang="zh_TW",
            part_of_speech="v.", example_sentence="The meeting was postponed.",
        )
        self.assertGreater(rid, 0)

        cards = self.mgr.get_vocabulary()
        self.assertEqual(len(cards), 1)
        self.assertEqual(cards[0]["word"], "postpone")
        self.assertEqual(cards[0]["meaning"], "延期")

    def test_add_duplicate_is_ignored(self):
        self.mgr.add_vocabulary(word="hello", meaning="你好", source_lang="en_US", target_lang="zh_TW")
        self.mgr.add_vocabulary(word="hello", meaning="你好2", source_lang="en_US", target_lang="zh_TW")
        cards = self.mgr.get_vocabulary()
        self.assertEqual(len(cards), 1)

    def test_add_batch(self):
        cards = [
            {"word": "apple", "meaning": "蘋果", "source_lang": "en_US", "target_lang": "zh_TW"},
            {"word": "banana", "meaning": "香蕉", "source_lang": "en_US", "target_lang": "zh_TW"},
            {"word": "cherry", "meaning": "櫻桃", "source_lang": "en_US", "target_lang": "zh_TW"},
        ]
        count = self.mgr.add_vocabulary_batch(cards)
        self.assertEqual(count, 3)
        self.assertEqual(len(self.mgr.get_vocabulary()), 3)

    def test_delete_vocabulary(self):
        self.mgr.add_vocabulary(word="test", meaning="測試", source_lang="en_US", target_lang="zh_TW")
        cards = self.mgr.get_vocabulary()
        self.assertTrue(self.mgr.delete_vocabulary(cards[0]["id"]))
        self.assertEqual(len(self.mgr.get_vocabulary()), 0)

    def test_delete_nonexistent_returns_false(self):
        self.assertFalse(self.mgr.delete_vocabulary(999))

    def test_filter_by_language(self):
        self.mgr.add_vocabulary(word="bonjour", meaning="你好", source_lang="fr_FR", target_lang="zh_TW")
        self.mgr.add_vocabulary(word="hello", meaning="你好", source_lang="en_US", target_lang="zh_TW")
        fr = self.mgr.get_vocabulary(source_lang="fr_FR")
        self.assertEqual(len(fr), 1)
        self.assertEqual(fr[0]["word"], "bonjour")


class TestSpacedRepetition(unittest.TestCase):
    def setUp(self):
        self.mgr = _fresh_manager()

    def tearDown(self):
        if os.path.exists(_TEST_DB):
            os.remove(_TEST_DB)

    def test_due_cards_includes_new(self):
        self.mgr.add_vocabulary(word="new", meaning="新", source_lang="en_US", target_lang="zh_TW")
        due = self.mgr.get_due_cards()
        self.assertEqual(len(due), 1)

    def test_review_correct_increases_interval(self):
        self.mgr.add_vocabulary(word="test", meaning="測", source_lang="en_US", target_lang="zh_TW")
        cards = self.mgr.get_due_cards()
        card_id = cards[0]["id"]

        # First review: quality 5 (perfect)
        result = self.mgr.review_card(card_id, 5)
        self.assertEqual(result["new_interval_days"], 1)
        self.assertGreater(result["new_ease_factor"], 2.4)

        # Force card to be due again for second review
        conn = sqlite3.connect(_TEST_DB)
        conn.execute("UPDATE vocabulary SET next_review = '2000-01-01' WHERE id = ?", (card_id,))
        conn.commit()
        conn.close()

        result2 = self.mgr.review_card(card_id, 5)
        self.assertEqual(result2["new_interval_days"], 6)

    def test_review_incorrect_resets(self):
        self.mgr.add_vocabulary(word="hard", meaning="難", source_lang="en_US", target_lang="zh_TW")
        cards = self.mgr.get_due_cards()
        card_id = cards[0]["id"]

        # Quality 1 = incorrect
        result = self.mgr.review_card(card_id, 1)
        self.assertEqual(result["new_interval_days"], 1)

    def test_review_nonexistent_card(self):
        result = self.mgr.review_card(999, 5)
        self.assertIn("error", result)

    def test_quality_clamped(self):
        self.mgr.add_vocabulary(word="clamp", meaning="夾", source_lang="en_US", target_lang="zh_TW")
        cards = self.mgr.get_due_cards()
        card_id = cards[0]["id"]

        # Quality out of range should be clamped
        result = self.mgr.review_card(card_id, 10)
        self.assertEqual(result["quality"], 5)


class TestLearningSessions(unittest.TestCase):
    def setUp(self):
        self.mgr = _fresh_manager()

    def tearDown(self):
        if os.path.exists(_TEST_DB):
            os.remove(_TEST_DB)

    def test_log_and_retrieve_session(self):
        sid = self.mgr.log_session(
            session_type="flashcard", source_lang="en_US",
            target_lang="zh_TW", score=85.0,
            details={"cards": 10},
        )
        self.assertGreater(sid, 0)

        sessions = self.mgr.get_sessions()
        self.assertEqual(len(sessions), 1)
        self.assertEqual(sessions[0]["session_type"], "flashcard")

    def test_filter_sessions_by_type(self):
        self.mgr.log_session(session_type="flashcard", score=80)
        self.mgr.log_session(session_type="dictation", score=70)
        self.mgr.log_session(session_type="flashcard", score=90)

        fc = self.mgr.get_sessions(session_type="flashcard")
        self.assertEqual(len(fc), 2)


class TestStats(unittest.TestCase):
    def setUp(self):
        self.mgr = _fresh_manager()

    def tearDown(self):
        if os.path.exists(_TEST_DB):
            os.remove(_TEST_DB)

    def test_empty_stats(self):
        stats = self.mgr.get_stats()
        self.assertEqual(stats["total_words"], 0)
        self.assertEqual(stats["due_for_review"], 0)
        self.assertEqual(stats["mastered"], 0)
        self.assertEqual(stats["total_sessions"], 0)

    def test_stats_reflect_data(self):
        self.mgr.add_vocabulary(word="a", meaning="甲", source_lang="en_US", target_lang="zh_TW")
        self.mgr.add_vocabulary(word="b", meaning="乙", source_lang="en_US", target_lang="zh_TW")
        self.mgr.log_session(session_type="flashcard", score=90)

        stats = self.mgr.get_stats()
        self.assertEqual(stats["total_words"], 2)
        self.assertEqual(stats["due_for_review"], 2)
        self.assertEqual(stats["total_sessions"], 1)
        self.assertIn("flashcard", stats["session_breakdown"])


try:
    import fastapi as _fastapi_check
    _HAS_FASTAPI = True
except ImportError:
    _HAS_FASTAPI = False


@unittest.skipUnless(_HAS_FASTAPI, "fastapi not installed")
class TestLearningAPI(unittest.IsolatedAsyncioTestCase):
    """Test learning-related API endpoints."""

    async def test_add_vocabulary_endpoint(self):
        import api
        request = api.VocabularyAddRequest(
            word="test_api", meaning="API 測試",
            source_lang="en_US", target_lang="zh_TW",
        )
        response = await api.add_vocabulary_endpoint(request)
        self.assertEqual(response["word"], "test_api")

    async def test_learning_stats_endpoint(self):
        import api
        response = await api.learning_stats_endpoint()
        self.assertIn("total_words", response)
        self.assertIn("due_for_review", response)

    async def test_review_nonexistent_returns_404(self):
        import api
        from fastapi import HTTPException
        request = api.ReviewCardRequest(card_id=99999, quality=5)
        with self.assertRaises(HTTPException) as ctx:
            await api.review_vocabulary_endpoint(request)
        self.assertEqual(ctx.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
