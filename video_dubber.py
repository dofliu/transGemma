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
        self.output_dir = output_dir or tempfile.mkdtemp(prefix="video_dub_")
        self.whisper_model = None
        
    def _get_whisper_model(self):
        """延遲載入 Whisper 模型"""
        if self.whisper_model is None:
            self.whisper_model = WhisperModel("base", device="cpu", compute_type="int8")
        return self.whisper_model
    
    def download_youtube(self, url: str, progress_callback=None) -> Tuple[str, str]:
        """
        下載 YouTube 影片
        
        Returns:
            (video_path, audio_path)
        """
        video_path = os.path.join(self.output_dir, "video.mp4")
        audio_path = os.path.join(self.output_dir, "audio.wav")
        
        # 下載影片
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': os.path.join(self.output_dir, "video.%(ext)s"),
            'merge_output_format': 'mp4',
            'quiet': True,
            'no_warnings': True,
        }
        
        if progress_callback:
            progress_callback("正在下載影片...")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
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
        
        Returns:
            List of Segment with start, end, text
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
        翻譯所有字幕片段
        """
        total = len(segments)
        
        for i, seg in enumerate(segments):
            if progress_callback:
                progress_callback(f"翻譯中... ({i+1}/{total})")
            
            # 使用 TranslateGemma 翻譯
            translated = translator.translate(seg.text, source_lang, target_lang)
            seg.translated_text = translated
        
        return segments
    
    async def synthesize_segment_audio(self, segment: Segment, target_lang: str,
                                        index: int) -> str:
        """
        為單一片段合成語音
        """
        import edge_tts
        
        voice = get_edge_tts_voice(target_lang)
        output_path = os.path.join(self.output_dir, f"tts_{index:04d}.mp3")
        
        communicate = edge_tts.Communicate(segment.translated_text, voice)
        await communicate.save(output_path)
        
        segment.audio_path = output_path
        return output_path
    
    def synthesize_all_audio(self, segments: List[Segment], target_lang: str,
                              progress_callback=None) -> List[Segment]:
        """
        為所有片段合成語音
        """
        total = len(segments)
        
        async def run_all():
            for i, seg in enumerate(segments):
                if progress_callback:
                    progress_callback(f"語音合成中... ({i+1}/{total})")
                await self.synthesize_segment_audio(seg, target_lang, i)
        
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
        return float(result.stdout.strip())
    
    def adjust_audio_speed(self, audio_path: str, target_duration: float) -> str:
        """
        調整音訊速度以符合目標時長
        """
        current_duration = self.get_audio_duration(audio_path)
        
        if current_duration <= 0:
            return audio_path
        
        speed_factor = current_duration / target_duration
        
        # 限制速度範圍 (0.5x - 2.0x)
        speed_factor = max(0.5, min(2.0, speed_factor))
        
        if abs(speed_factor - 1.0) < 0.05:  # 差異小於 5% 不調整
            return audio_path
        
        output_path = audio_path.replace('.mp3', '_adjusted.mp3')
        
        subprocess.run([
            'ffmpeg', '-y', '-i', audio_path,
            '-filter:a', f'atempo={speed_factor}',
            output_path
        ], capture_output=True)
        
        return output_path
    
    def merge_dubbed_audio(self, segments: List[Segment], total_duration: float,
                            progress_callback=None) -> str:
        """
        合併所有配音片段，產生一條完整音軌
        """
        if progress_callback:
            progress_callback("正在合併音軌...")
        
        # 建立時間軸對齊的音軌
        output_path = os.path.join(self.output_dir, "dubbed_audio.wav")
        
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
        
        # 混合所有音軌，並加大音量（amix 會降低音量，需要補償）
        mix_inputs = ''.join([f'[a{i}]' for i in range(len(filter_parts))])
        # amix 會將音量除以輸入數量，使用 volume 濾鏡補償
        volume_boost = min(len(filter_parts), 5)  # 最多 5 倍
        filter_complex = ';'.join(filter_parts) + f';{mix_inputs}amix=inputs={len(filter_parts)}:duration=longest,volume={volume_boost}[out]'
        
        cmd = ['ffmpeg', '-y'] + inputs + [
            '-filter_complex', filter_complex,
            '-map', '[out]',
            '-t', str(total_duration),
            output_path
        ]
        
        subprocess.run(cmd, capture_output=True)
        
        return output_path
    
    def mux_video(self, video_path: str, dubbed_audio_path: str,
                   subtitle_path: str = None, progress_callback=None) -> str:
        """
        合成最終影片
        """
        if progress_callback:
            progress_callback("正在合成影片...")
        
        output_path = os.path.join(self.output_dir, "dubbed_video.mp4")
        
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
    
    def generate_srt(self, segments: List[Segment], use_translated: bool = False) -> str:
        """
        產生 SRT 字幕檔
        """
        filename = "translated.srt" if use_translated else "original.srt"
        output_path = os.path.join(self.output_dir, filename)
        
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
                       progress_callback=None) -> dict:
        """
        完整處理流程
        
        Returns:
            dict with paths to: video, dubbed_video, original_srt, translated_srt
        """
        results = {}
        
        # 判斷是 URL 還是檔案路徑
        if video_source.startswith('http'):
            video_path, audio_path = self.download_youtube(video_source, progress_callback)
        else:
            video_path = video_source
            audio_path = os.path.join(self.output_dir, "audio.wav")
            subprocess.run([
                'ffmpeg', '-y', '-i', video_path,
                '-vn', '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1',
                audio_path
            ], capture_output=True)
        
        results['original_video'] = video_path
        
        # 生成字幕
        segments = self.generate_subtitles(audio_path, source_lang, progress_callback)
        
        # 產生原始 SRT
        results['original_srt'] = self.generate_srt(segments, use_translated=False)
        
        # 翻譯
        segments = self.translate_segments(segments, target_lang, source_lang, progress_callback)
        
        # 產生翻譯 SRT
        results['translated_srt'] = self.generate_srt(segments, use_translated=True)
        
        # 合成語音
        segments = self.synthesize_all_audio(segments, target_lang, progress_callback)
        
        # 取得影片總時長
        total_duration = self.get_audio_duration(audio_path)
        
        # 合併配音音軌
        dubbed_audio = self.merge_dubbed_audio(segments, total_duration, progress_callback)
        
        # 合成影片
        if dubbed_audio:
            results['dubbed_video'] = self.mux_video(video_path, dubbed_audio, 
                                                      progress_callback=progress_callback)
        
        if progress_callback:
            progress_callback("✅ 處理完成！")
        
        return results


# 單例
video_dubber = VideoDubber()
