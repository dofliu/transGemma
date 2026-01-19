# -*- coding: utf-8 -*-
"""
影片翻譯與配音模組 (Video Dubbing Module)

功能：
1. 下載 YouTube 影片 (yt-dlp)
2. 語音轉字幕 (faster-whisper)
3. 字幕翻譯 (TranslateGemma)
4. 語音合成 (edge-tts)
5. 影片合成 (ffmpeg)
"""

import os
import tempfile
import subprocess
import asyncio
import time
from typing import List, Tuple, Generator, Optional
from dataclasses import dataclass

import yt_dlp
from faster_whisper import WhisperModel

from translator import translator
from languages import get_edge_tts_voice


@dataclass
class Segment:
    """字幕片段"""
    start: float
    end: float
    text: str
    translated_text: str = ""
    audio_path: str = ""


class VideoDubber:
    """影片翻譯與配音服務"""
    
    def __init__(self, output_dir: str = None):
        # 如果未指定 output_dir，則使用系統 temp
        self.output_dir = output_dir or tempfile.mkdtemp(prefix="video_dub_")
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir, exist_ok=True)
            
        self.whisper_model = None
        print(f"VideoDubber initialized with output_dir: {self.output_dir}")
        
    def _get_whisper_model(self):
        """延遲載入 Whisper 模型"""
        if self.whisper_model is None:
            self.whisper_model = WhisperModel("base", device="cpu", compute_type="int8")
        return self.whisper_model
    
    def _create_job_dir(self, prefix="job"):
        """建立工作專屬目錄"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        job_dir = os.path.join(self.output_dir, f"{prefix}_{timestamp}")
        os.makedirs(job_dir, exist_ok=True)
        return job_dir

    def download_youtube(self, url: str, output_dir: str, progress_callback=None) -> Tuple[str, str]:
        """
        下載 YouTube 影片
        
        Args:
            output_dir: 指定輸出目錄
            
        Returns:
            (video_path, audio_path)
        """
        # 下載影片
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': os.path.join(output_dir, "video.%(ext)s"),
            'merge_output_format': 'mp4',
            'quiet': True,
            'no_warnings': True,
        }
        
        if progress_callback:
            progress_callback("正在下載影片...")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        video_path = os.path.join(output_dir, "video.mp4")
        audio_path = os.path.join(output_dir, "audio.wav")
        
        # 提取音訊
        if progress_callback:
            progress_callback("正在提取音訊...")
        
        subprocess.run([
            'ffmpeg', '-y', '-i', video_path,
            '-vn', '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1',
            audio_path
        ], capture_output=True)
        
        return video_path, audio_path
    
    def generate_subtitles(self, audio_path: str, source_lang: str = "auto", 
                           progress_callback=None) -> List[Segment]:
        """
        使用 Whisper 生成字幕
        """
        if progress_callback:
            progress_callback("正在辨識語音...")
        
        model = self._get_whisper_model()
        
        # 設定語言
        language = None if source_lang == "auto" else source_lang[:2]
        
        segments_result, info = model.transcribe(
            audio_path,
            language=language,
            word_timestamps=False
        )
        
        segments = []
        for seg in segments_result:
            segments.append(Segment(
                start=seg.start,
                end=seg.end,
                text=seg.text.strip()
            ))
        
        if progress_callback:
            progress_callback(f"辨識完成，共 {len(segments)} 個片段")
        
        return segments
    
    def translate_segments(self, segments: List[Segment], target_lang: str,
                           source_lang: str = "auto",
                           progress_callback=None) -> List[Segment]:
        """
        翻譯所有字幕片段（長度感知翻譯）
        
        透過在 prompt 中加入時間限制，引導模型產生適當長度的翻譯，
        減少後續音訊重疊問題。
        """
        total = len(segments)
        
        # 不同語言的平均語速估計（字/秒）
        # 用於計算目標翻譯應該有多少字
        SPEECH_RATE = {
            "zh_TW": 4.0, "zh_CN": 4.0,  # 中文約 4 字/秒
            "ja": 5.0,                    # 日文約 5 字/秒  
            "ko": 4.5,                    # 韓文約 4.5 字/秒
            "en": 2.5,                    # 英文約 2.5 詞/秒 (按字元算約 12-15 字元/秒)
            "de": 2.3, "fr": 2.5, "es": 2.8,  # 歐洲語言
            "default": 3.0
        }
        
        # 取得目標語言的語速
        target_rate = SPEECH_RATE.get(target_lang, SPEECH_RATE.get(target_lang[:2], SPEECH_RATE["default"]))
        
        for i, seg in enumerate(segments):
            if progress_callback:
                progress_callback(f"翻譯中... ({i+1}/{total})")
            
            # 計算這段的可用時間
            duration = seg.end - seg.start
            
            # 估計目標語言的理想字數
            if target_lang.startswith("en") or target_lang in ["de", "fr", "es", "it", "pt", "ru"]:
                # 英文等語言用字元數估計（含空格）
                max_chars = int(duration * 12)  # 約 12 字元/秒
                length_hint = f"Keep translation under {max_chars} characters (including spaces)."
            else:
                # 中日韓等語言用字數估計
                max_chars = int(duration * target_rate)
                length_hint = f"Keep translation under {max_chars} characters."
            
            # 構建長度感知的翻譯 prompt
            # 注意：TranslateGemma 使用特定格式，這裡我們在原文前加入提示
            length_aware_prompt = f"""[DUBBING MODE] Translate concisely for voice dubbing. 
Time limit: {duration:.1f} seconds. {length_hint}
Use natural, spoken language. Simplify if needed while preserving meaning.

{seg.text}"""
            
            # 使用 TranslateGemma 翻譯
            translated = translator.translate(length_aware_prompt, source_lang, target_lang)
            
            # 清理可能的額外標記（如果模型輸出了我們的 prompt 部分）
            # TranslateGemma 應該會正確處理，但以防萬一
            if "[DUBBING MODE]" in translated:
                # 模型可能把我們的 prompt 也輸出了，嘗試提取翻譯部分
                translated = translated.split("\n")[-1].strip()
            
            seg.translated_text = translated
        
        return segments
    
    async def synthesize_segment_audio(self, segment: Segment, target_lang: str,
                                        output_dir: str, index: int) -> str:
        """
        為單一片段合成語音
        """
        import edge_tts
        
        voice = get_edge_tts_voice(target_lang)
        output_path = os.path.join(output_dir, f"tts_{index:04d}.mp3")
        
        communicate = edge_tts.Communicate(segment.translated_text, voice)
        await communicate.save(output_path)
        
        segment.audio_path = output_path
        return output_path
    
    def synthesize_all_audio(self, segments: List[Segment], target_lang: str,
                              output_dir: str, progress_callback=None) -> List[Segment]:
        """
        為所有片段合成語音
        """
        total = len(segments)
        
        async def run_all():
            for i, seg in enumerate(segments):
                if progress_callback:
                    progress_callback(f"語音合成中... ({i+1}/{total})")
                await self.synthesize_segment_audio(seg, target_lang, output_dir, i)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(run_all())
        loop.close()
        
        return segments
    
    def get_audio_duration(self, audio_path: str) -> float:
        """取得音訊時長"""
        result = subprocess.run([
            'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1', audio_path
        ], capture_output=True, text=True)
        try:
            return float(result.stdout.strip())
        except:
            return 0.0
    
    def adjust_audio_speed(self, audio_path: str, target_duration: float) -> str:
        """
        調整音訊速度以符合目標時長
        """
        current_duration = self.get_audio_duration(audio_path)
        
        if current_duration <= 0:
            return audio_path
        
        speed_factor = current_duration / target_duration
        
        # 限制速度範圍 (0.85x - 1.25x)
        original_speed = speed_factor
        speed_factor = max(0.85, min(1.25, speed_factor))
        
        if abs(speed_factor - 1.0) < 0.05:  # 差異小於 5% 不調整
            return audio_path
        
        output_path = audio_path.replace('.mp3', '_adjusted.mp3')
        
        # 如果原始速度超出範圍，記錄警告
        if (original_speed < 0.85 or original_speed > 1.25):
            print(f"⚠️ 語速調整受限: 原始需要 {original_speed:.2f}x，實際使用 {speed_factor:.2f}x")
        
        # 先調整速度
        subprocess.run([
            'ffmpeg', '-y', '-i', audio_path,
            '-filter:a', f'atempo={speed_factor}',
            output_path
        ], capture_output=True)
        
        # 如果調整後仍然超過目標時長，則強制截斷（fallback）
        adjusted_duration = self.get_audio_duration(output_path)
        if adjusted_duration > target_duration * 1.05:  # 容許 5% 誤差
            truncated_path = output_path.replace('.mp3', '_truncated.mp3')
            subprocess.run([
                'ffmpeg', '-y', '-i', output_path,
                '-t', str(target_duration),
                truncated_path
            ], capture_output=True)
            return truncated_path
        
        return output_path
    
    def merge_dubbed_audio(self, segments: List[Segment], total_duration: float,
                            output_dir: str, progress_callback=None) -> str:
        """
        合併所有配音片段
        """
        if progress_callback:
            progress_callback("正在合併音軌...")
        
        output_path = os.path.join(output_dir, "dubbed_audio.wav")
        
        # 使用 ffmpeg 的 adelay 和 amix 濾鏡
        filter_parts = []
        inputs = []
        
        for i, seg in enumerate(segments):
            if not seg.audio_path or not os.path.exists(seg.audio_path):
                continue
            
            # 調整速度以符合時間軸
            target_duration = seg.end - seg.start
            adjusted_path = self.adjust_audio_speed(seg.audio_path, target_duration)
            
            inputs.extend(['-i', adjusted_path])
            delay_ms = int(seg.start * 1000)
            filter_parts.append(f'[{i}:a]adelay={delay_ms}|{delay_ms}[a{i}]')
        
        if not filter_parts:
            return ""
        
        # 混合所有音軌
        mix_inputs = ''.join([f'[a{i}]' for i in range(len(filter_parts))])
        
        # 使用 loudnorm 進行標準化響度控制 (I=-14 LUFS)
        filter_complex = ';'.join(filter_parts) + f';{mix_inputs}amix=inputs={len(filter_parts)}:duration=longest:dropout_transition=0,loudnorm=I=-14:TP=-1.0:LRA=11[out]'
        
        cmd = ['ffmpeg', '-y'] + inputs + [
            '-filter_complex', filter_complex,
            '-map', '[out]',
            '-t', str(total_duration),
            output_path
        ]
        
        subprocess.run(cmd, capture_output=True)
        
        return output_path
    
    def mux_video(self, video_path: str, dubbed_audio_path: str,
                   output_dir: str, subtitle_path: str = None, burn_subtitles: bool = False,
                   progress_callback=None) -> str:
        """
        合成最終影片
        """
        if progress_callback:
            progress_callback("正在合成影片...")
        
        output_path = os.path.join(output_dir, "dubbed_video.mp4")
        
        if burn_subtitles and subtitle_path and os.path.exists(subtitle_path):
            # 燒錄字幕
            subtitle_escaped = subtitle_path.replace('\\', '/').replace(':', '\\:')
            
            cmd = [
                'ffmpeg', '-y',
                '-i', video_path,
                '-i', dubbed_audio_path,
                '-vf', f"subtitles='{subtitle_escaped}':force_style='FontSize=18,PrimaryColour=&HFFFFFF,OutlineColour=&H000000,Outline=2'",
                '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
                '-map', '0:v:0',
                '-map', '1:a:0',
                '-shortest',
                output_path
            ]
        else:
            # 不燒錄字幕
            cmd = [
                'ffmpeg', '-y',
                '-i', video_path,
                '-i', dubbed_audio_path,
                '-c:v', 'copy',
                '-map', '0:v:0',
                '-map', '1:a:0',
                '-shortest',
                output_path
            ]
        
        subprocess.run(cmd, capture_output=True)
        
        return output_path
    
    def generate_srt(self, segments: List[Segment], output_dir: str, use_translated: bool = False) -> str:
        """
        產生 SRT 字幕檔
        """
        filename = "translated.srt" if use_translated else "original.srt"
        output_path = os.path.join(output_dir, filename)
        
        def format_time(seconds: float) -> str:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            millis = int((seconds % 1) * 1000)
            return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for i, seg in enumerate(segments, 1):
                text = seg.translated_text if use_translated else seg.text
                f.write(f"{i}\n")
                f.write(f"{format_time(seg.start)} --> {format_time(seg.end)}\n")
                f.write(f"{text}\n\n")
        
        return output_path
    
    def process_video(self, video_source: str, source_lang: str, target_lang: str,
                       burn_subtitles: bool = False,
                       progress_callback=None,
                       job_dir: str = None) -> dict:
        """
        完整處理流程
        """
        # 建立工作目錄 (若未指定)
        job_dir = job_dir or self._create_job_dir()
        
        results = {}
        
        # 判斷是 URL 還是檔案路徑
        if video_source.startswith('http'):
            video_path, audio_path = self.download_youtube(video_source, job_dir, progress_callback)
        else:
            video_path = video_source
            audio_path = os.path.join(job_dir, "audio.wav")
            # 轉換本地影片音訊
            subprocess.run([
                'ffmpeg', '-y', '-i', video_path,
                '-vn', '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1',
                audio_path
            ], capture_output=True)
        
        results['original_video'] = video_path
        
        # 生成字幕
        segments = self.generate_subtitles(audio_path, source_lang, progress_callback)
        
        # 產生原始 SRT
        results['original_srt'] = self.generate_srt(segments, job_dir, use_translated=False)
        
        # 翻譯
        segments = self.translate_segments(segments, target_lang, source_lang, progress_callback)
        
        # 產生翻譯 SRT
        translated_srt = self.generate_srt(segments, job_dir, use_translated=True)
        results['translated_srt'] = translated_srt
        
        # 合成語音
        segments = self.synthesize_all_audio(segments, target_lang, job_dir, progress_callback)
        
        # 取得影片總時長
        total_duration = self.get_audio_duration(audio_path)
        
        # 合併配音音軌
        dubbed_audio = self.merge_dubbed_audio(segments, total_duration, job_dir, progress_callback)
        
        # 合成影片
        if dubbed_audio:
            results['dubbed_video'] = self.mux_video(
                video_path, dubbed_audio,
                output_dir=job_dir,
                subtitle_path=translated_srt,
                burn_subtitles=burn_subtitles,
                progress_callback=progress_callback
            )
        
        if progress_callback:
            progress_callback("✅ 處理完成！")
        
        return results
    
    def process_video_batch(self, video_source: str, source_lang: str, target_langs: list,
                             burn_subtitles: bool = False,
                             progress_callback=None) -> dict:
        """
        批次處理多語言翻譯
        """
        # 建立主工作目錄
        job_dir = self._create_job_dir(prefix="batch_job")
        
        batch_results = {}
        total_langs = len(target_langs)
        
        # 先下載/提取音訊（只做一次）
        if video_source.startswith('http'):
            video_path, audio_path = self.download_youtube(video_source, job_dir, progress_callback)
        else:
            video_path = video_source
            audio_path = os.path.join(job_dir, "audio.wav")
            subprocess.run([
                'ffmpeg', '-y', '-i', video_path,
                '-vn', '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1',
                audio_path
            ], capture_output=True)
        
        # 生成字幕（只做一次）
        segments = self.generate_subtitles(audio_path, source_lang, progress_callback)
        original_srt = self.generate_srt(segments, job_dir, use_translated=False)
        batch_results['original_video'] = video_path
        batch_results['original_srt'] = original_srt
        batch_results['languages'] = {}
        
        # 對每個語言進行處理
        for i, target_lang in enumerate(target_langs):
            if progress_callback:
                progress_callback(f"處理語言 {i+1}/{total_langs}: {target_lang}")
            
            # 建立語言專屬子目錄，避免檔名衝突
            lang_dir = os.path.join(job_dir, target_lang)
            os.makedirs(lang_dir, exist_ok=True)
            
            lang_result = {}
            
            # 複製 segments (Deep copy segments)
            import copy
            lang_segments = copy.deepcopy(segments)
            
            # 翻譯
            lang_segments = self.translate_segments(lang_segments, target_lang, source_lang, progress_callback)
            
            # 產生翻譯 SRT
            translated_srt = self.generate_srt(lang_segments, lang_dir, use_translated=True)
            lang_result['translated_srt'] = translated_srt
            
            # 合成語音
            lang_segments = self.synthesize_all_audio(lang_segments, target_lang, lang_dir, progress_callback)
            
            # 取得影片總時長
            total_duration = self.get_audio_duration(audio_path)
            
            # 合併配音音軌
            dubbed_audio = self.merge_dubbed_audio(lang_segments, total_duration, lang_dir, progress_callback)
            
            # 合成影片
            if dubbed_audio:
                dubbed_video = self.mux_video(
                    video_path, dubbed_audio,
                    output_dir=lang_dir,
                    subtitle_path=translated_srt,
                    burn_subtitles=burn_subtitles,
                    progress_callback=progress_callback
                )
                lang_result['dubbed_video'] = dubbed_video
            
            batch_results['languages'][target_lang] = lang_result
        
        if progress_callback:
            progress_callback(f"✅ 批次處理完成！共處理 {total_langs} 種語言")
        
        return batch_results


# 單例 (預設使用 temp, 但 app.py 會重新初始化)
video_dubber = VideoDubber()
