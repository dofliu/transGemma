import unittest

from translator import TranslateGemmaService


class TestPipelineContracts(unittest.TestCase):
    def test_expected_methods_exist(self):
        service = TranslateGemmaService()
        for method_name in [
            "translate",
            "translate_stream",
            "translate_image",
            "translate_pdf",
            "speech_to_text",
            "text_to_speech",
        ]:
            self.assertTrue(hasattr(service, method_name), f"Missing method: {method_name}")


if __name__ == "__main__":
    unittest.main()
