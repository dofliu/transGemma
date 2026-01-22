# -*- coding: utf-8 -*-
"""
會議摘要模組 (Meeting Summarizer Module)

功能：
1. 從影片抽取音訊 (ffmpeg)
2. 語音轉文字 (faster-whisper)
3. AI 會議摘要生成 (Ollama / Gemini API)
"""

import os
import tempfile
import subprocess
from typing import Optional, Generator
from dataclasses import dataclass

# ========== 資料類別 ==========

@dataclass
class TranscriptSegment:
    """逐字稿片段"""
    start: float
    end: float
    text: str


@dataclass
class MeetingSummaryResult:
    """會議摘要結果"""
    transcript: str                    # 完整逐字稿
    transcript_with_time: str          # 帶時間戳的逐字稿
    summary: dict                      # 摘要內容 {"key_points": ..., "action_items": ..., ...}
    duration: float                    # 音訊時長（秒）
    language: str                      # 偵測到的語言


# ========== 摘要類型定義 ==========

SUMMARY_TYPES = {
    "key_points": {
        "name": "📝 會議重點",
        "prompt": "請整理這份會議逐字稿的重點摘要，用條列式呈現主要討論內容。"
    },
    "action_items": {
        "name": "✅ 待辦事項",
        "prompt": "請從會議逐字稿中提取所有待辦事項（Action Items），列出負責人（如有提及）和截止日期（如有提及）。"
    },
    "decisions": {
        "name": "📋 決議事項",
        "prompt": "請從會議逐字稿中提取所有達成的決議和共識。"
    },
    "full_summary": {
        "name": "📄 完整摘要",
        "prompt": "請為這份會議逐字稿撰寫一份完整的會議摘要，包含：會議主題、參與討論的重點、主要決議、以及後續行動事項。"
    }
}


# ========== 會議摘要服務 ==========

class MeetingSummarizer:
    """會議摘要服務"""
    
    def __init__(self, 
                 ai_backend: str = "ollama",
                 ollama_model: str = "qwen3:4b",
                 gemini_api_key: str = ""):
        """
        初始化會議摘要服務
        
        Args:
            ai_backend: "ollama" 或 "gemini"
            ollama_model: Ollama 模型名稱
            gemini_api_key: Gemini API Key（僅 gemini 後端需要）
        """
        self.ai_backend = ai_backend
        self.ollama_model = ollama_model
        self.gemini_api_key = gemini_api_key
        self._whisper_model = None
    
    def _get_whisper_model(self):
        """延遲載入 Whisper 模型"""
        if self._whisper_model is None:
            from faster_whisper import WhisperModel
            # 使用 base 模型，平衡速度與準確度
            self._whisper_model = WhisperModel("base", device="cpu", compute_type="int8")
        return self._whisper_model
    
    # ========== 音訊抽取 ==========
    
    def extract_audio(self, video_path: str, output_dir: str = None) -> str:
        """
        從影片抽取音訊
        
        Args:
            video_path: 影片檔案路徑
            output_dir: 輸出目錄（預設使用暫存目錄）
            
        Returns:
            音訊檔案路徑 (WAV 格式)
        """
        if output_dir is None:
            output_dir = tempfile.mkdtemp(prefix="meeting_audio_")
        
        # 產生輸出路徑
        base_name = os.path.splitext(os.path.basename(video_path))[0]
        audio_path = os.path.join(output_dir, f"{base_name}_audio.wav")
        
        # 使用 ffmpeg 抽取音訊並轉換為 16kHz mono WAV（Whisper 最佳格式）
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-vn",                    # 不要影片
            "-acodec", "pcm_s16le",   # 16-bit PCM
            "-ar", "16000",           # 16kHz
            "-ac", "1",               # mono
            audio_path
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return audio_path
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"音訊抽取失敗: {e.stderr.decode()}")
    
    # ========== 語音辨識 ==========
    
    def transcribe(self, audio_path: str, language: str = "auto",
                   progress_callback=None) -> tuple[list[TranscriptSegment], str]:
        """
        語音轉文字
        
        Args:
            audio_path: 音訊檔案路徑
            language: 語言代碼（"auto" 自動偵測）
            progress_callback: 進度回調函數
            
        Returns:
            (segments, detected_language)
        """
        model = self._get_whisper_model()
        
        # 語言對應
        whisper_lang_map = {
            "zh_TW": "zh", "zh_CN": "zh",
            "en_US": "en", "ja_JP": "ja", "ko_KR": "ko",
            "de_DE": "de", "fr_FR": "fr", "es_ES": "es",
            "it_IT": "it", "ru_RU": "ru", "pt_BR": "pt",
            "vi_VN": "vi", "th_TH": "th", "ar_SA": "ar",
        }
        
        lang_code = None if language == "auto" else whisper_lang_map.get(language, None)
        
        if progress_callback:
            progress_callback("🎙️ 正在進行語音辨識...")
        
        # 執行辨識
        segments_iter, info = model.transcribe(
            audio_path, 
            language=lang_code,
            word_timestamps=False
        )
        
        # 收集片段
        segments = []
        for seg in segments_iter:
            segments.append(TranscriptSegment(
                start=seg.start,
                end=seg.end,
                text=seg.text.strip()
            ))
        
        return segments, info.language
    
    def format_transcript(self, segments: list[TranscriptSegment], 
                          with_timestamps: bool = True) -> str:
        """
        格式化逐字稿
        
        Args:
            segments: 逐字稿片段列表
            with_timestamps: 是否包含時間戳
        """
        lines = []
        for seg in segments:
            if with_timestamps:
                start_time = self._format_time(seg.start)
                lines.append(f"[{start_time}] {seg.text}")
            else:
                lines.append(seg.text)
        
        return "\n".join(lines)
    
    def _format_time(self, seconds: float) -> str:
        """格式化時間為 HH:MM:SS"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"
    
    # ========== AI 摘要生成 ==========
    
    def generate_summary(self, transcript: str, summary_types: list[str],
                         progress_callback=None) -> dict:
        """
        生成會議摘要
        
        Args:
            transcript: 完整逐字稿文字
            summary_types: 摘要類型列表 ["key_points", "action_items", ...]
            progress_callback: 進度回調
            
        Returns:
            {"key_points": "...", "action_items": "...", ...}
        """
        if self.ai_backend == "gemini":
            return self._generate_summary_gemini(transcript, summary_types, progress_callback)
        else:
            return self._generate_summary_ollama(transcript, summary_types, progress_callback)
    
    def _generate_summary_ollama(self, transcript: str, summary_types: list[str],
                                  progress_callback=None) -> dict:
        """使用 Ollama 生成摘要"""
        import ollama
        
        results = {}
        
        for i, summary_type in enumerate(summary_types):
            if summary_type not in SUMMARY_TYPES:
                continue
            
            type_info = SUMMARY_TYPES[summary_type]
            
            if progress_callback:
                progress_callback(f"🤖 正在生成 {type_info['name']} ({i+1}/{len(summary_types)})...")
            
            # 構建 prompt
            prompt = f"""你是一位專業的會議記錄整理助手。以下是一份會議的逐字稿：

---
{transcript}
---

{type_info['prompt']}

請用繁體中文回答，格式清晰、條理分明。"""

            try:
                response = ollama.chat(
                    model=self.ollama_model,
                    messages=[{"role": "user", "content": prompt}],
                    options={"num_predict": 2048}
                )
                results[summary_type] = response['message']['content']
            except Exception as e:
                results[summary_type] = f"❌ 生成失敗: {str(e)}"
        
        return results
    
    def _generate_summary_gemini(self, transcript: str, summary_types: list[str],
                                  progress_callback=None) -> dict:
        """使用 Gemini API 生成摘要"""
        try:
            import google.generativeai as genai
        except ImportError:
            return {st: "❌ 請安裝 google-generativeai: pip install google-generativeai" 
                    for st in summary_types}
        
        if not self.gemini_api_key:
            return {st: "❌ 請提供 Gemini API Key" for st in summary_types}
        
        # 配置 Gemini
        genai.configure(api_key=self.gemini_api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")
        
        results = {}
        
        for i, summary_type in enumerate(summary_types):
            if summary_type not in SUMMARY_TYPES:
                continue
            
            type_info = SUMMARY_TYPES[summary_type]
            
            if progress_callback:
                progress_callback(f"🤖 正在生成 {type_info['name']} ({i+1}/{len(summary_types)})...")
            
            # 構建 prompt
            prompt = f"""你是一位專業的會議記錄整理助手。以下是一份會議的逐字稿：

---
{transcript}
---

{type_info['prompt']}

請用繁體中文回答，格式清晰、條理分明。"""

            try:
                response = model.generate_content(prompt)
                results[summary_type] = response.text
            except Exception as e:
                results[summary_type] = f"❌ 生成失敗: {str(e)}"
        
        return results
    
    # ========== 完整處理流程 ==========
    
    def process_video(self, video_path: str, 
                      language: str = "auto",
                      summary_types: list[str] = None,
                      progress_callback=None) -> MeetingSummaryResult:
        """
        完整處理流程：影片 → 音訊 → 逐字稿 → 摘要
        
        Args:
            video_path: 影片檔案路徑
            language: 語言代碼（"auto" 自動偵測）
            summary_types: 摘要類型列表（預設為 ["full_summary"]）
            progress_callback: 進度回調函數
            
        Returns:
            MeetingSummaryResult
        """
        if summary_types is None:
            summary_types = ["full_summary"]
        
        # 1. 抽取音訊
        if progress_callback:
            progress_callback("🎬 正在從影片抽取音訊...")
        
        audio_path = self.extract_audio(video_path)
        
        # 2. 語音辨識
        if progress_callback:
            progress_callback("🎙️ 正在進行語音辨識...")
        
        segments, detected_lang = self.transcribe(audio_path, language, progress_callback)
        
        # 格式化逐字稿
        transcript = self.format_transcript(segments, with_timestamps=False)
        transcript_with_time = self.format_transcript(segments, with_timestamps=True)
        
        # 計算時長
        duration = segments[-1].end if segments else 0.0
        
        # 3. 生成摘要
        if progress_callback:
            progress_callback("🤖 正在生成會議摘要...")
        
        summary = self.generate_summary(transcript, summary_types, progress_callback)
        
        # 4. 清理暫存檔案
        try:
            os.remove(audio_path)
            os.rmdir(os.path.dirname(audio_path))
        except:
            pass
        
        return MeetingSummaryResult(
            transcript=transcript,
            transcript_with_time=transcript_with_time,
            summary=summary,
            duration=duration,
            language=detected_lang
        )
    
    def process_video_stream(self, video_path: str,
                             language: str = "auto",
                             summary_types: list[str] = None,
                             progress_callback=None) -> Generator[dict, None, None]:
        """
        串流處理流程，逐步回傳結果
        
        Yields:
            {"stage": "...", "progress": 0.0-1.0, "data": ...}
        """
        if summary_types is None:
            summary_types = ["full_summary"]
        
        # Stage 1: 抽取音訊
        yield {"stage": "extract_audio", "progress": 0.1, "message": "🎬 正在從影片抽取音訊..."}
        audio_path = self.extract_audio(video_path)
        yield {"stage": "extract_audio", "progress": 0.2, "message": "✅ 音訊抽取完成"}
        
        # Stage 2: 語音辨識
        yield {"stage": "transcribe", "progress": 0.3, "message": "🎙️ 正在進行語音辨識..."}
        segments, detected_lang = self.transcribe(audio_path, language)
        
        transcript = self.format_transcript(segments, with_timestamps=False)
        transcript_with_time = self.format_transcript(segments, with_timestamps=True)
        duration = segments[-1].end if segments else 0.0
        
        yield {
            "stage": "transcribe", 
            "progress": 0.5, 
            "message": f"✅ 語音辨識完成（{self._format_time(duration)}）",
            "transcript": transcript,
            "transcript_with_time": transcript_with_time,
            "language": detected_lang,
            "duration": duration
        }
        
        # Stage 3: 生成摘要
        yield {"stage": "summarize", "progress": 0.6, "message": "🤖 正在生成會議摘要..."}
        
        summary = {}
        for i, summary_type in enumerate(summary_types):
            progress = 0.6 + (0.35 * (i + 1) / len(summary_types))
            type_name = SUMMARY_TYPES.get(summary_type, {}).get("name", summary_type)
            yield {"stage": "summarize", "progress": progress, "message": f"🤖 正在生成 {type_name}..."}
            
            partial_summary = self.generate_summary(transcript, [summary_type])
            summary.update(partial_summary)
            
            yield {
                "stage": "summarize",
                "progress": progress,
                "message": f"✅ {type_name} 完成",
                "partial_summary": {summary_type: partial_summary.get(summary_type, "")}
            }
        
        # 清理
        try:
            os.remove(audio_path)
            os.rmdir(os.path.dirname(audio_path))
        except:
            pass
        
        yield {
            "stage": "done",
            "progress": 1.0,
            "message": "✅ 處理完成！",
            "summary": summary
        }


# ========== 單例實例（方便直接使用）==========

meeting_summarizer = MeetingSummarizer()
