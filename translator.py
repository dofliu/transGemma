"""
TranslateGemma 蝧餉陌???詨?
===========================
?? Ollama ?澆 TranslateGemma 璅∪??脰?蝧餉陌
"""

import ollama
from typing import Generator
from languages import LANGUAGES, get_language_info


class TranslateGemmaService:
    """TranslateGemma 蝧餉陌??"""
    
    def __init__(self, model_name: str = "translategemma"):
        self.model_name = model_name
    
    def _format_custom_rules(self, glossary: str = "", style: str = "") -> str:
        """Build optional terminology/style rules to prepend into prompt."""
        rules = []
        if glossary and glossary.strip():
            rules.append(
                "Terminology rules (strict):\n"
                f"{glossary.strip()}\n"
                "Prefer mapped terms when source terms are present."
            )
        if style and style.strip():
            rules.append(
                "Style guide:\n"
                f"{style.strip()}\n"
                "Follow this style while preserving semantic accuracy."
            )
        return "\n\n".join(rules)
    def _build_prompt(self, text: str, source_code: str, target_code: str, glossary: str = "", style: str = "") -> str:
        """撱箸?蝧餉陌 prompt"""
        src_info = get_language_info(source_code)
        tgt_info = get_language_info(target_code)
        
        src_name, src_en, src_locale = src_info
        tgt_name, tgt_en, tgt_locale = tgt_info
        
        custom_rules = self._format_custom_rules(glossary, style)
        
        # 蝜?銝剜??寞???
        if target_code == "zh_TW":
            prompt = f"""You are a professional {src_en} ({src_locale}) to Traditional Chinese (Taiwan) translator.

IMPORTANT RULES:
1. You MUST output ONLY Traditional Chinese characters (蝜?摮? as used in Taiwan.
2. DO NOT use any Simplified Chinese characters (蝞雿?).
3. Examples of correct Traditional vs incorrect Simplified:
   - ??(correct) vs ??(wrong)
   - ??(correct) vs ? (wrong)
   - ??(correct) vs 餈?(wrong)
   - 鋆?(correct) vs ??(wrong)
   - 隤?(correct) vs 霂?(wrong)
   - 頠? (correct) vs 頧臭辣 (wrong)
   - 蝬脰楝 (correct) vs 蝵? (wrong)

Please provide ONLY the Traditional Chinese translation without any additional explanations.

{custom_rules}

Translate the following text:

{text}"""
        else:
            prompt = f"""You are a professional {src_en} ({src_locale}) to {tgt_en} ({tgt_locale}) translator.
Your goal is to accurately convey the meaning and nuances of the original {src_en} text 
while adhering to {tgt_en} grammar, style, and conventions.

Please provide ONLY the {tgt_en} translation without any additional explanations or commentary.

{custom_rules}

Translate the following text:

{text}"""
        
        return prompt
    
    def translate(self, text: str, source_code: str, target_code: str, glossary: str = "", style: str = "") -> str:
        """Run non-streaming translation."""
        if not text.strip():
            return ""
        
        prompt = self._build_prompt(text, source_code, target_code, glossary, style)
        
        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[{'role': 'user', 'content': prompt}]
            )
            return response['message']['content']
        except Exception as e:
            return f"??蝧餉陌?航炊: {str(e)}"
    
    def translate_stream(self, text: str, source_code: str, target_code: str, glossary: str = "", style: str = "") -> Generator[str, None, None]:
        """?瑁?蝧餉陌嚗葡瘚?"""
        if not text.strip():
            yield ""
            return
        
        prompt = self._build_prompt(text, source_code, target_code, glossary, style)
        
        try:
            stream = ollama.chat(
                model=self.model_name,
                messages=[{'role': 'user', 'content': prompt}],
                stream=True
            )
            
            full_response = ""
            for chunk in stream:
                content = chunk['message']['content']
                full_response += content
                yield full_response
                
        except Exception as e:
            yield f"??蝧餉陌?航炊: {str(e)}"
    
    def translate_pdf(self, pdf_path: str, target_code: str, source_code: str = "en_US") -> Generator[str, None, None]:
        """Translate PDF pages with PyMuPDF extraction."""
        try:
            import fitz  # PyMuPDF
        except ImportError:
            yield "??隢?鋆?PyMuPDF: pip install PyMuPDF"
            return
        
        tgt_info = get_language_info(target_code)
        tgt_name, tgt_en, tgt_locale = tgt_info
        
        yield "?? 甇?霈??PDF ?辣...\n"
        
        try:
            doc = fitz.open(pdf_path)
            total_pages = len(doc)
            
            if total_pages == 0:
                yield "Error: PDF has no pages."
                return
            
            yield f"?? PDF ??{total_pages} ??????...\n\n"
            
            all_results = []
            
            for page_num in range(total_pages):
                page = doc[page_num]
                page_text = page.get_text().strip()
                
                if not page_text:
                    all_results.append(f"?洵 {page_num + 1} ?n嚗?航??交?摮?\n")
                    yield self._format_pdf_results(all_results, page_num + 1, total_pages)
                    continue
                
                # 憿舐內?脣漲
                all_results.append(f"?洵 {page_num + 1} ?n")
                yield self._format_pdf_results(all_results, page_num + 1, total_pages, translating=True)
                
                # 蝧餉陌????
                page_translation = ""
                for result in self.translate_stream(page_text, source_code, target_code):
                    page_translation = result
                    current_results = all_results.copy()
                    current_results[-1] = f"?洵 {page_num + 1} ?n{result}\n"
                    yield self._format_pdf_results(current_results, page_num + 1, total_pages, translating=True)
                
                all_results[-1] = f"?洵 {page_num + 1} ?n{page_translation}\n"
                yield self._format_pdf_results(all_results, page_num + 1, total_pages)
            
            doc.close()
            yield self._format_pdf_results(all_results, total_pages, total_pages, done=True)
            
        except FileNotFoundError:
            yield f"???曆???PDF ?辣: {pdf_path}"
        except Exception as e:
            yield f"??PDF ???航炊: {str(e)}"
    
    def _format_pdf_results(self, results: list, current_page: int, total_pages: int, 
                            translating: bool = False, done: bool = False) -> str:
        """?澆???PDF 蝧餉陌蝯?"""
        if done:
            header = f"??蝧餉陌摰?嚗 {total_pages} ?n{'='*40}\n\n"
        elif translating:
            header = f"?? 甇?蝧餉陌蝚?{current_page}/{total_pages} ??..\n{'='*40}\n\n"
        else:
            header = f"?? 撌脰???{current_page}/{total_pages} ?n{'='*40}\n\n"
        
        return header + "\n".join(results)
    
    def translate_image(self, image_path: str, target_code: str, source_code: str = "auto") -> Generator[str, None, None]:
        """Translate OCR text extracted from an image."""
        try:
            import pytesseract
            from PIL import Image
        except ImportError:
            yield "??隢?鋆?pytesseract ??Pillow: pip install pytesseract Pillow"
            return
        
        tgt_info = get_language_info(target_code)
        tgt_name, tgt_en, tgt_locale = tgt_info
        
        yield "?? 甇?霅??銝剔???...\n"
        
        try:
            # 雿輻 Tesseract OCR 霅??
            image = Image.open(image_path)
            
            # ?寞?靘?隤?閮剖? OCR 隤?
            ocr_lang_map = {
                "zh_TW": "chi_tra",
                "zh_CN": "chi_sim",
                "ja_JP": "jpn",
                "ko_KR": "kor",
                "en_US": "eng",
                "de_DE": "deu",
                "fr_FR": "fra",
                "es_ES": "spa",
                "it_IT": "ita",
                "ru_RU": "rus",
                "vi_VN": "vie",
                "th_TH": "tha",
                "ar_SA": "ara",
            }
            
            # ?岫憭?閮霅
            if source_code == "auto":
                ocr_lang = "chi_tra+chi_sim+eng+jpn+kor"
            else:
                ocr_lang = ocr_lang_map.get(source_code, "eng")
            
            # ?瑁? OCR
            try:
                extracted_text = pytesseract.image_to_string(image, lang=ocr_lang)
            except Exception:
                # 憒???隤?憭望?嚗蝙?刻??
                extracted_text = pytesseract.image_to_string(image, lang="eng")
            
            extracted_text = extracted_text.strip()
            
            if not extracted_text:
                yield "?? ?⊥?霅??銝剔???\n\n?內嚗n- 蝣箔???皜\n- 蝣箔???憭批??拐葉\n- ?踹????撟脫"
                return
            
            yield f"???亦??n{extracted_text}\n\n?? 甇?蝧餉陌...\n"
            
            # 雿輻 TranslateGemma 蝧餉陌
            full_translation = ""
            for result in self.translate_stream(extracted_text, source_code if source_code != "auto" else "en_US", target_code):
                full_translation = result
                yield f"???亦??n{extracted_text}\n\n?蕃霅舐??n{result}"
            
        except FileNotFoundError:
            yield f"???曆??啣??? {image_path}"
        except Exception as e:
            yield f"???????航炊: {str(e)}"
    
    def speech_to_text(self, audio_path: str, language: str = "auto") -> tuple[str, str]:
        """雿輻 faster-whisper 撠??唾??箸?摮?
        
        Returns:
            tuple: (霅??, ?菜葫?啁?隤?隞?Ⅳ)
        """
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            return "??隢?鋆?faster-whisper: pip install faster-whisper", ""
        
        try:
            # 雿輻 base 璅∪?撟唾﹛?漲??蝣箏漲
            model = WhisperModel("base", device="cpu", compute_type="int8")
            
            # 隤?撠?
            whisper_lang_map = {
                "zh_TW": "zh", "zh_CN": "zh",
                "en_US": "en", "ja_JP": "ja", "ko_KR": "ko",
                "de_DE": "de", "fr_FR": "fr", "es_ES": "es",
                "it_IT": "it", "ru_RU": "ru", "pt_BR": "pt",
                "vi_VN": "vi", "th_TH": "th", "ar_SA": "ar",
            }
            
            lang_code = None if language == "auto" else whisper_lang_map.get(language, None)
            
            segments, info = model.transcribe(audio_path, language=lang_code)
            
            text = "".join([segment.text for segment in segments]).strip()
            detected_lang = info.language
            
            return text, detected_lang
            
        except Exception as e:
            return f"??隤颲刻??航炊: {str(e)}", ""
    
    async def text_to_speech(self, text: str, language_code: str) -> str:
        """雿輻 edge-tts 撠?摮??箄???
        
        Args:
            text: 閬?????
            language_code: 隤?隞?Ⅳ
            
        Returns:
            str: ???瑼楝敺?
        """
        try:
            import edge_tts
            import tempfile
            import os
        except ImportError:
            return ""
        
        # edge-tts 隤撠?
        voice_map = {
            "zh_TW": "zh-TW-HsiaoChenNeural",  # ?啁憟唾
            "zh_CN": "zh-CN-XiaoxiaoNeural",    # 憭折憟唾
            "en_US": "en-US-JennyNeural",       # 蝢??望?憟唾
            "ja_JP": "ja-JP-NanamiNeural",      # ?交?憟唾
            "ko_KR": "ko-KR-SunHiNeural",       # ??憟唾
            "de_DE": "de-DE-KatjaNeural",       # 敺瑟?憟唾
            "fr_FR": "fr-FR-DeniseNeural",      # 瘜?憟唾
            "es_ES": "es-ES-ElviraNeural",      # 镼輻??憟唾
            "it_IT": "it-IT-ElsaNeural",        # 蝢拙之?拇?憟唾
            "ru_RU": "ru-RU-SvetlanaNeural",    # 靽?憟唾
            "pt_BR": "pt-BR-FranciscaNeural",   # ?∟???憟唾
            "vi_VN": "vi-VN-HoaiMyNeural",      # 頞??戊??
            "th_TH": "th-TH-PremwadeeNeural",   # 瘜唳?憟唾
            "ar_SA": "ar-SA-ZariyahNeural",     # ?踵?隡舀?憟唾
        }
        
        voice = voice_map.get(language_code, "en-US-JennyNeural")
        
        try:
            # 撱箇??怠??單?
            temp_dir = tempfile.gettempdir()
            output_path = os.path.join(temp_dir, f"tts_output_{id(text)}.mp3")
            
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(output_path)
            
            return output_path
            
        except Exception as e:
            print(f"TTS ?航炊: {e}")
            return ""


# ?桐?撖虫?
translator = TranslateGemmaService()


