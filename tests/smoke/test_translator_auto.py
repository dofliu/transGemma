import unittest

from translator import TranslateGemmaService


class TestTranslatorAutoDetection(unittest.TestCase):
    def setUp(self):
        self.service = TranslateGemmaService()

    def test_detects_japanese(self):
        self.assertEqual(self.service.detect_source_language("こんにちは"), "ja_JP")

    def test_detects_korean(self):
        self.assertEqual(self.service.detect_source_language("안녕하세요"), "ko_KR")

    def test_detects_simplified_chinese(self):
        self.assertEqual(self.service.detect_source_language("这是测试文本"), "zh_CN")

    def test_detects_traditional_chinese(self):
        self.assertEqual(self.service.detect_source_language("這是測試文本"), "zh_TW")

    def test_resolve_auto_fallback(self):
        self.assertEqual(self.service._resolve_source_code("Hello world", "auto"), "en_US")


if __name__ == "__main__":
    unittest.main()
