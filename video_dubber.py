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
        使用較窄的速度範圍避免不自然的語速
        """
        current_duration = self.get_audio_duration(audio_path)
        
        if current_duration <= 0:
            return audio_path
        
        speed_factor = current_duration / target_duration
        
        # 限制速度範圍 (0.85x - 1.25x) - 更窄的範圍避免不自然
        # 超出範圍的部分：過長會截斷，過短會保留靜音
        original_speed = speed_factor
        speed_factor = max(0.85, min(1.25, speed_factor))
        
        if abs(speed_factor - 1.0) < 0.05:  # 差異小於 5% 不調整
            return audio_path
        
        output_path = audio_path.replace('.mp3', '_adjusted.mp3')
        
        # 如果原始速度超出範圍，記錄警告
        if original_speed < 0.85 or original_speed > 1.25:
            print(f"⚠️ 語速調整受限: 原始需要 {original_speed:.2f}x，實際使用 {speed_factor:.2f}x")
        
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
        
        # 混合所有音軌
        mix_inputs = ''.join([f'[a{i}]' for i in range(len(filter_parts))])
        
        # 使用 amix 混合，接著使用 loudnorm 進行標準化響度控制
        # I=-14 是 YouTube/Web 建議的響度標準 (LUFS)
        # TP=-1.0 是 True Peak 上限
        # amix 參數: dropout_transition=0 避免非重疊區域音量浮動 (如果有重疊的話)
        # 注意: 如果 segments 數量非常多，amix 可能會很慢或指令過長。暫時維持此實作。
        
        # 移除原來的 volume_boost，改用 loudnorm
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
                   subtitle_path: str = None, burn_subtitles: bool = False,
                   progress_callback=None) -> str:
        """
        合成最終影片
        
        Args:
            video_path: 原始影片路徑
            dubbed_audio_path: 配音音軌路徑
            subtitle_path: 字幕檔路徑 (SRT)
            burn_subtitles: 是否燒錄字幕到影片中
        """
        if progress_callback:
            progress_callback("正在合成影片...")
        
        output_path = os.path.join(self.output_dir, "dubbed_video.mp4")
        
        if burn_subtitles and subtitle_path and os.path.exists(subtitle_path):
            # 燒錄字幕 - 需要重新編碼影片
            # 處理 Windows 路徑中的反斜線和冒號
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
            # 不燒錄字幕 - 直接複製影片流
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
                       burn_subtitles: bool = False,
                       progress_callback=None) -> dict:
        """
        完整處理流程
        
        Args:
            video_source: YouTube URL 或本地檔案路徑
            source_lang: 來源語言
            target_lang: 目標語言
            burn_subtitles: 是否燒錄字幕到影片
        
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
        translated_srt = self.generate_srt(segments, use_translated=True)
        results['translated_srt'] = translated_srt
        
        # 合成語音
        segments = self.synthesize_all_audio(segments, target_lang, progress_callback)
        
        # 取得影片總時長
        total_duration = self.get_audio_duration(audio_path)
        
        # 合併配音音軌
        dubbed_audio = self.merge_dubbed_audio(segments, total_duration, progress_callback)
        
        # 合成影片（支援字幕燒錄）
        if dubbed_audio:
            results['dubbed_video'] = self.mux_video(
                video_path, dubbed_audio,
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
        
        Args:
            video_source: YouTube URL 或本地檔案路徑
            source_lang: 來源語言
            target_langs: 目標語言列表
            burn_subtitles: 是否燒錄字幕
        
        Returns:
            dict with language keys, each containing video/srt paths
        """
        batch_results = {}
        total_langs = len(target_langs)
        
        # 先下載/提取音訊（只做一次）
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
        
        # 生成字幕（只做一次）
        segments = self.generate_subtitles(audio_path, source_lang, progress_callback)
        original_srt = self.generate_srt(segments, use_translated=False)
        batch_results['original_video'] = video_path
        batch_results['original_srt'] = original_srt
        batch_results['languages'] = {}
        
        # 對每個語言進行處理
        for i, target_lang in enumerate(target_langs):
            if progress_callback:
                progress_callback(f"處理語言 {i+1}/{total_langs}: {target_lang}")
            
            lang_result = {}
            
            # 複製 segments 以避免污染
            import copy
            lang_segments = copy.deepcopy(segments)
            
            # 翻譯
            lang_segments = self.translate_segments(lang_segments, target_lang, source_lang, progress_callback)
            
            # 產生翻譯 SRT
            translated_srt = self.generate_srt(lang_segments, use_translated=True)
            # 重命名避免覆蓋
            lang_srt_path = translated_srt.replace('.srt', f'_{target_lang}.srt')
            os.rename(translated_srt, lang_srt_path)
            lang_result['translated_srt'] = lang_srt_path
            
            # 合成語音
            lang_segments = self.synthesize_all_audio(lang_segments, target_lang, progress_callback)
            
            # 取得影片總時長
            total_duration = self.get_audio_duration(audio_path)
            
            # 合併配音音軌
            dubbed_audio = self.merge_dubbed_audio(lang_segments, total_duration, progress_callback)
            
            # 合成影片
            if dubbed_audio:
                dubbed_video = self.mux_video(
                    video_path, dubbed_audio,
                    subtitle_path=lang_srt_path,
                    burn_subtitles=burn_subtitles,
                    progress_callback=progress_callback
                )
                # 重命名避免覆蓋
                lang_video_path = dubbed_video.replace('.mp4', f'_{target_lang}.mp4')
                os.rename(dubbed_video, lang_video_path)
                lang_result['dubbed_video'] = lang_video_path
            
            batch_results['languages'][target_lang] = lang_result
        
        if progress_callback:
            progress_callback(f"✅ 批次處理完成！共處理 {total_langs} 種語言")
        
        return batch_results


# 單例
video_dubber = VideoDubber()
