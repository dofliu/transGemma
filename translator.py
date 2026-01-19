"""
TranslateGemma 翻譯服務核心
===========================
透過 Ollama 呼叫 TranslateGemma 模型進行翻譯
"""

import ollama
from typing import Generator, Optional
from languages import LANGUAGES, get_language_info


class TranslateGemmaService:
    """TranslateGemma 翻譯服務"""
    
    def __init__(self, model_name: str = "translategemma"):
        self.model_name = model_name
    
    def _build_prompt(self, text: str, source_code: str, target_code: str) -> str:
        """建構翻譯 prompt"""
        src_info = get_language_info(source_code)
        tgt_info = get_language_info(target_code)
        
        src_name, src_en, src_locale = src_info
        tgt_name, tgt_en, tgt_locale = tgt_info
        
        # 繁體中文特殊處理
        if target_code == "zh_TW":
            prompt = f"""You are a professional {src_en} ({src_locale}) to Traditional Chinese (Taiwan) translator.

IMPORTANT RULES:
1. You MUST output ONLY Traditional Chinese characters (繁體字) as used in Taiwan.
2. DO NOT use any Simplified Chinese characters (简体字).
3. Examples of correct Traditional vs incorrect Simplified:
   - 嗎 (correct) vs 吗 (wrong)
   - 著 (correct) vs 着 (wrong)
   - 這 (correct) vs 这 (wrong)
   - 裡 (correct) vs 里 (wrong)
   - 說 (correct) vs 说 (wrong)
   - 軟體 (correct) vs 软件 (wrong)
   - 網路 (correct) vs 网络 (wrong)

Please provide ONLY the Traditional Chinese translation without any additional explanations.

Translate the following text:

{text}"""
        else:
            prompt = f"""You are a professional {src_en} ({src_locale}) to {tgt_en} ({tgt_locale}) translator.
Your goal is to accurately convey the meaning and nuances of the original {src_en} text 
while adhering to {tgt_en} grammar, style, and conventions.

Please provide ONLY the {tgt_en} translation without any additional explanations or commentary.

Translate the following text:

{text}"""
        
        return prompt
    
    def translate(self, text: str, source_code: str, target_code: str) -> str:
        """執行翻譯（非串流）"""
        if not text.strip():
            return ""
        
        prompt = self._build_prompt(text, source_code, target_code)
        
        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[{'role': 'user', 'content': prompt}]
            )
            return response['message']['content']
        except Exception as e:
            return f"❌ 翻譯錯誤: {str(e)}"
    
    def translate_stream(self, text: str, source_code: str, target_code: str) -> Generator[str, None, None]:
        """執行翻譯（串流）"""
        if not text.strip():
            yield ""
            return
        
        prompt = self._build_prompt(text, source_code, target_code)
        
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
            yield f"❌ 翻譯錯誤: {str(e)}"
    
    def translate_pdf(self, pdf_path: str, target_code: str, source_code: str = "en_US") -> Generator[str, None, None]:
        """翻譯 PDF 文件（PyMuPDF 提取 + TranslateGemma 翻譯）"""
        try:
            import fitz  # PyMuPDF
        except ImportError:
            yield "❌ 請安裝 PyMuPDF: pip install PyMuPDF"
            return
        
        tgt_info = get_language_info(target_code)
        tgt_name, tgt_en, tgt_locale = tgt_info
        
        yield "📄 正在讀取 PDF 文件...\n"
        
        try:
            doc = fitz.open(pdf_path)
            total_pages = len(doc)
            
            if total_pages == 0:
                yield "⚠️ PDF 文件為空或無法讀取"
                return
            
            yield f"📄 PDF 共 {total_pages} 頁，開始處理...\n\n"
            
            all_results = []
            
            for page_num in range(total_pages):
                page = doc[page_num]
                page_text = page.get_text().strip()
                
                if not page_text:
                    all_results.append(f"【第 {page_num + 1} 頁】\n（無可識別文字）\n")
                    yield self._format_pdf_results(all_results, page_num + 1, total_pages)
                    continue
                
                # 顯示進度
                all_results.append(f"【第 {page_num + 1} 頁】\n")
                yield self._format_pdf_results(all_results, page_num + 1, total_pages, translating=True)
                
                # 翻譯這一頁
                page_translation = ""
                for result in self.translate_stream(page_text, source_code, target_code):
                    page_translation = result
                    current_results = all_results.copy()
                    current_results[-1] = f"【第 {page_num + 1} 頁】\n{result}\n"
                    yield self._format_pdf_results(current_results, page_num + 1, total_pages, translating=True)
                
                all_results[-1] = f"【第 {page_num + 1} 頁】\n{page_translation}\n"
                yield self._format_pdf_results(all_results, page_num + 1, total_pages)
            
            doc.close()
            yield self._format_pdf_results(all_results, total_pages, total_pages, done=True)
            
        except FileNotFoundError:
            yield f"❌ 找不到 PDF 文件: {pdf_path}"
        except Exception as e:
            yield f"❌ PDF 處理錯誤: {str(e)}"
    
    def _format_pdf_results(self, results: list, current_page: int, total_pages: int, 
                            translating: bool = False, done: bool = False) -> str:
        """格式化 PDF 翻譯結果"""
        if done:
            header = f"✅ 翻譯完成！共 {total_pages} 頁\n{'='*40}\n\n"
        elif translating:
            header = f"🔄 正在翻譯第 {current_page}/{total_pages} 頁...\n{'='*40}\n\n"
        else:
            header = f"📄 已處理 {current_page}/{total_pages} 頁\n{'='*40}\n\n"
        
        return header + "\n".join(results)
    
    def translate_image(self, image_path: str, target_code: str, source_code: str = "auto") -> Generator[str, None, None]:
        """翻譯圖片中的文字（Tesseract OCR + TranslateGemma 翻譯）"""
        try:
            import pytesseract
            from PIL import Image
        except ImportError:
            yield "❌ 請安裝 pytesseract 和 Pillow: pip install pytesseract Pillow"
            return
        
        tgt_info = get_language_info(target_code)
        tgt_name, tgt_en, tgt_locale = tgt_info
        
        yield "🔍 正在識別圖片中的文字...\n"
        
        try:
            # 使用 Tesseract OCR 識別文字
            image = Image.open(image_path)
            
            # 根據來源語言設定 OCR 語言
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
            
            # 嘗試多語言識別
            if source_code == "auto":
                ocr_lang = "chi_tra+chi_sim+eng+jpn+kor"
            else:
                ocr_lang = ocr_lang_map.get(source_code, "eng")
            
            # 執行 OCR
            try:
                extracted_text = pytesseract.image_to_string(image, lang=ocr_lang)
            except Exception:
                # 如果指定語言失敗，使用英文
                extracted_text = pytesseract.image_to_string(image, lang="eng")
            
            extracted_text = extracted_text.strip()
            
            if not extracted_text:
                yield "⚠️ 無法識別圖片中的文字\n\n提示：\n- 確保圖片清晰\n- 確保文字大小適中\n- 避免過多背景干擾"
                return
            
            yield f"【識別結果】\n{extracted_text}\n\n🔄 正在翻譯...\n"
            
            # 使用 TranslateGemma 翻譯
            full_translation = ""
            for result in self.translate_stream(extracted_text, source_code if source_code != "auto" else "en_US", target_code):
                full_translation = result
                yield f"【識別結果】\n{extracted_text}\n\n【翻譯結果】\n{result}"
            
        except FileNotFoundError:
            yield f"❌ 找不到圖片: {image_path}"
        except Exception as e:
            yield f"❌ 圖片處理錯誤: {str(e)}"
    
    def speech_to_text(self, audio_path: str, language: str = "auto") -> tuple[str, str]:
        """使用 faster-whisper 將語音轉為文字
        
        Returns:
            tuple: (識別文字, 偵測到的語言代碼)
        """
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            return "❌ 請安裝 faster-whisper: pip install faster-whisper", ""
        
        try:
            # 使用 base 模型平衡速度與準確度
            model = WhisperModel("base", device="cpu", compute_type="int8")
            
            # 語言對應
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
            return f"❌ 語音辨識錯誤: {str(e)}", ""
    
    async def text_to_speech(self, text: str, language_code: str) -> str:
        """使用 edge-tts 將文字轉為語音
        
        Args:
            text: 要轉換的文字
            language_code: 語言代碼
            
        Returns:
            str: 生成的音檔路徑
        """
        try:
            import edge_tts
            import tempfile
            import os
        except ImportError:
            return ""
        
        # edge-tts 語音對應
        voice_map = {
            "zh_TW": "zh-TW-HsiaoChenNeural",  # 台灣女聲
            "zh_CN": "zh-CN-XiaoxiaoNeural",    # 大陸女聲
            "en_US": "en-US-JennyNeural",       # 美式英文女聲
            "ja_JP": "ja-JP-NanamiNeural",      # 日文女聲
            "ko_KR": "ko-KR-SunHiNeural",       # 韓文女聲
            "de_DE": "de-DE-KatjaNeural",       # 德文女聲
            "fr_FR": "fr-FR-DeniseNeural",      # 法文女聲
            "es_ES": "es-ES-ElviraNeural",      # 西班牙文女聲
            "it_IT": "it-IT-ElsaNeural",        # 義大利文女聲
            "ru_RU": "ru-RU-SvetlanaNeural",    # 俄文女聲
            "pt_BR": "pt-BR-FranciscaNeural",   # 葡萄牙文女聲
            "vi_VN": "vi-VN-HoaiMyNeural",      # 越南文女聲
            "th_TH": "th-TH-PremwadeeNeural",   # 泰文女聲
            "ar_SA": "ar-SA-ZariyahNeural",     # 阿拉伯文女聲
        }
        
        voice = voice_map.get(language_code, "en-US-JennyNeural")
        
        try:
            # 建立暫存音檔
            temp_dir = tempfile.gettempdir()
            output_path = os.path.join(temp_dir, f"tts_output_{id(text)}.mp3")
            
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(output_path)
            
            return output_path
            
        except Exception as e:
            print(f"TTS 錯誤: {e}")
            return ""


# 單例實例
translator = TranslateGemmaService()
