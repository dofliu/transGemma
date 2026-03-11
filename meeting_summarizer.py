# -*- coding: utf-8 -*-
"""
Meeting summarizer module.

Pipeline:
1. Extract audio from video (ffmpeg)
2. Transcribe speech (faster-whisper)
3. Generate summaries (Ollama or Gemini)
"""

from __future__ import annotations

import os
import subprocess
import tempfile
from dataclasses import dataclass
from typing import Generator


@dataclass
class TranscriptSegment:
    """One transcript segment with start/end time."""

    start: float
    end: float
    text: str


@dataclass
class MeetingSummaryResult:
    """Final summarized meeting result."""

    transcript: str
    transcript_with_time: str
    summary: dict
    duration: float
    language: str


SUMMARY_TYPES = {
    "key_points": {
        "name": "Key Points",
        "prompt": "List the key points from this meeting using concise bullet points.",
    },
    "action_items": {
        "name": "Action Items",
        "prompt": "List action items with owner, due date (if available), and concrete next steps.",
    },
    "decisions": {
        "name": "Decisions",
        "prompt": "List decisions that were explicitly made in the meeting.",
    },
    "full_summary": {
        "name": "Full Summary",
        "prompt": "Provide a complete meeting summary including context, discussion, decisions, and follow-ups.",
    },
}


class MeetingSummarizer:
    """Meeting summarizer service."""

    def __init__(
        self,
        ai_backend: str = "ollama",
        ollama_model: str = "qwen3:4b",
        gemini_api_key: str = "",
    ):
        self.ai_backend = ai_backend
        self.ollama_model = ollama_model
        self.gemini_api_key = gemini_api_key
        self._whisper_model = None

    def _get_whisper_model(self):
        """Lazy-load whisper model."""
        if self._whisper_model is None:
            from faster_whisper import WhisperModel

            self._whisper_model = WhisperModel("base", device="cpu", compute_type="int8")
        return self._whisper_model

    def extract_audio(self, video_path: str, output_dir: str | None = None) -> str:
        """Extract 16kHz mono WAV from input video."""
        if output_dir is None:
            output_dir = tempfile.mkdtemp(prefix="meeting_audio_")

        base_name = os.path.splitext(os.path.basename(video_path))[0]
        audio_path = os.path.join(output_dir, f"{base_name}_audio.wav")

        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            video_path,
            "-vn",
            "-acodec",
            "pcm_s16le",
            "-ar",
            "16000",
            "-ac",
            "1",
            audio_path,
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return audio_path
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(f"Audio extraction failed: {exc.stderr.decode(errors='ignore')}")

    def transcribe(
        self,
        audio_path: str,
        language: str = "auto",
        progress_callback=None,
    ) -> tuple[list[TranscriptSegment], str]:
        """Transcribe audio into segments and detected language."""
        model = self._get_whisper_model()

        whisper_lang_map = {
            "zh_TW": "zh",
            "zh_CN": "zh",
            "en_US": "en",
            "ja_JP": "ja",
            "ko_KR": "ko",
            "de_DE": "de",
            "fr_FR": "fr",
            "es_ES": "es",
            "it_IT": "it",
            "ru_RU": "ru",
            "pt_BR": "pt",
            "vi_VN": "vi",
            "th_TH": "th",
            "ar_SA": "ar",
        }
        lang_code = None if language == "auto" else whisper_lang_map.get(language)

        if progress_callback:
            progress_callback("Transcribing audio...")

        segments_iter, info = model.transcribe(audio_path, language=lang_code, word_timestamps=False)

        segments: list[TranscriptSegment] = []
        for seg in segments_iter:
            segments.append(TranscriptSegment(start=seg.start, end=seg.end, text=seg.text.strip()))

        return segments, info.language

    def format_transcript(self, segments: list[TranscriptSegment], with_timestamps: bool = True) -> str:
        """Format transcript with optional timestamps."""
        lines = []
        for seg in segments:
            if with_timestamps:
                lines.append(f"[{self._format_time(seg.start)}] {seg.text}")
            else:
                lines.append(seg.text)
        return "\n".join(lines)

    def _format_time(self, seconds: float) -> str:
        """Format seconds to MM:SS or HH:MM:SS."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"

    def generate_summary(self, transcript: str, summary_types: list[str], progress_callback=None) -> dict:
        """Generate selected summary sections."""
        if self.ai_backend == "gemini":
            return self._generate_summary_gemini(transcript, summary_types, progress_callback)
        return self._generate_summary_ollama(transcript, summary_types, progress_callback)

    def _generate_summary_ollama(self, transcript: str, summary_types: list[str], progress_callback=None) -> dict:
        """Generate summaries with Ollama."""
        import ollama

        results = {}
        for i, summary_type in enumerate(summary_types):
            if summary_type not in SUMMARY_TYPES:
                continue
            type_info = SUMMARY_TYPES[summary_type]
            if progress_callback:
                progress_callback(f"Generating {type_info['name']} ({i + 1}/{len(summary_types)})...")

            prompt = f"""You are a professional meeting summarizer.\n\nTranscript:\n---\n{transcript}\n---\n\nTask: {type_info['prompt']}\n\nReturn only the summary content without additional commentary."""
            try:
                response = ollama.chat(
                    model=self.ollama_model,
                    messages=[{"role": "user", "content": prompt}],
                    options={"num_predict": 2048},
                )
                results[summary_type] = response["message"]["content"]
            except Exception as exc:
                results[summary_type] = f"Summary generation failed: {exc}"
        return results

    def _generate_summary_gemini(self, transcript: str, summary_types: list[str], progress_callback=None) -> dict:
        """Generate summaries with Gemini API."""
        try:
            import google.generativeai as genai
        except ImportError:
            return {st: "google-generativeai is not installed. Run: pip install google-generativeai" for st in summary_types}

        if not self.gemini_api_key:
            return {st: "Gemini API key is missing." for st in summary_types}

        genai.configure(api_key=self.gemini_api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")

        results = {}
        for i, summary_type in enumerate(summary_types):
            if summary_type not in SUMMARY_TYPES:
                continue
            type_info = SUMMARY_TYPES[summary_type]
            if progress_callback:
                progress_callback(f"Generating {type_info['name']} ({i + 1}/{len(summary_types)})...")

            prompt = f"""You are a professional meeting summarizer.\n\nTranscript:\n---\n{transcript}\n---\n\nTask: {type_info['prompt']}\n\nReturn only the summary content without additional commentary."""
            try:
                response = model.generate_content(prompt)
                results[summary_type] = response.text
            except Exception as exc:
                results[summary_type] = f"Summary generation failed: {exc}"
        return results

    def process_video(
        self,
        video_path: str,
        language: str = "auto",
        summary_types: list[str] | None = None,
        progress_callback=None,
    ) -> MeetingSummaryResult:
        """Run full pipeline: extract -> transcribe -> summarize."""
        if summary_types is None:
            summary_types = ["full_summary"]

        if progress_callback:
            progress_callback("Extracting audio from video...")
        audio_path = self.extract_audio(video_path)

        if progress_callback:
            progress_callback("Transcribing audio...")
        segments, detected_lang = self.transcribe(audio_path, language, progress_callback)

        transcript = self.format_transcript(segments, with_timestamps=False)
        transcript_with_time = self.format_transcript(segments, with_timestamps=True)
        duration = segments[-1].end if segments else 0.0

        if progress_callback:
            progress_callback("Generating meeting summary...")
        summary = self.generate_summary(transcript, summary_types, progress_callback)

        try:
            os.remove(audio_path)
            os.rmdir(os.path.dirname(audio_path))
        except OSError:
            pass

        return MeetingSummaryResult(
            transcript=transcript,
            transcript_with_time=transcript_with_time,
            summary=summary,
            duration=duration,
            language=detected_lang,
        )

    def process_video_stream(
        self,
        video_path: str,
        language: str = "auto",
        summary_types: list[str] | None = None,
        progress_callback=None,
    ) -> Generator[dict, None, None]:
        """Streaming status updates for long-running summary generation."""
        if summary_types is None:
            summary_types = ["full_summary"]

        yield {"stage": "extract_audio", "progress": 0.1, "message": "Extracting audio from video..."}
        audio_path = self.extract_audio(video_path)
        yield {"stage": "extract_audio", "progress": 0.2, "message": "Audio extraction completed."}

        yield {"stage": "transcribe", "progress": 0.3, "message": "Transcribing audio..."}
        segments, detected_lang = self.transcribe(audio_path, language)

        transcript = self.format_transcript(segments, with_timestamps=False)
        transcript_with_time = self.format_transcript(segments, with_timestamps=True)
        duration = segments[-1].end if segments else 0.0

        yield {
            "stage": "transcribe",
            "progress": 0.5,
            "message": f"Transcription completed ({self._format_time(duration)}).",
            "transcript": transcript,
            "transcript_with_time": transcript_with_time,
            "language": detected_lang,
            "duration": duration,
        }

        yield {"stage": "summarize", "progress": 0.6, "message": "Generating summary..."}

        summary = {}
        for i, summary_type in enumerate(summary_types):
            progress = 0.6 + (0.35 * (i + 1) / len(summary_types))
            type_name = SUMMARY_TYPES.get(summary_type, {}).get("name", summary_type)
            yield {"stage": "summarize", "progress": progress, "message": f"Generating {type_name}..."}

            partial_summary = self.generate_summary(transcript, [summary_type])
            summary.update(partial_summary)

            yield {
                "stage": "summarize",
                "progress": progress,
                "message": f"{type_name} completed.",
                "partial_summary": {summary_type: partial_summary.get(summary_type, "")},
            }

        try:
            os.remove(audio_path)
            os.rmdir(os.path.dirname(audio_path))
        except OSError:
            pass

        yield {"stage": "done", "progress": 1.0, "message": "Done.", "summary": summary}


meeting_summarizer = MeetingSummarizer()
