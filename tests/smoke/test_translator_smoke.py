import unittest
from unittest.mock import patch

from translator import TranslateGemmaService


class TestTranslatorSmoke(unittest.TestCase):
    def setUp(self):
        self.service = TranslateGemmaService(model_name="translategemma")

    def test_prompt_includes_glossary_and_style(self):
        prompt = self.service._build_prompt(
            text="Hello AI",
            source_code="en_US",
            target_code="zh_TW",
            glossary="AI => 人工智慧",
            style="正式、簡潔"
        )
        self.assertIn("Terminology rules (strict)", prompt)
        self.assertIn("AI => 人工智慧", prompt)
        self.assertIn("Style guide", prompt)
        self.assertIn("正式、簡潔", prompt)

    @patch("translator.ollama.chat")
    def test_translate_returns_model_content(self, mock_chat):
        mock_chat.return_value = {"message": {"content": "翻譯結果"}}
        result = self.service.translate("hello", "en_US", "zh_TW")
        self.assertEqual(result, "翻譯結果")

    @patch("translator.ollama.chat")
    def test_translate_stream_accumulates_chunks(self, mock_chat):
        mock_chat.return_value = iter([
            {"message": {"content": "你"}},
            {"message": {"content": "好"}},
        ])
        outputs = list(self.service.translate_stream("hello", "en_US", "zh_TW"))
        self.assertEqual(outputs[-1], "你好")


if __name__ == "__main__":
    unittest.main()
