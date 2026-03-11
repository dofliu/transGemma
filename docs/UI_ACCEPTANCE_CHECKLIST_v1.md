# UI Acceptance Checklist (v1)

## Test Setup
- Start command: `python app.py`
- URL: `http://localhost:7860`
- Required tools:
  - Ollama model available (`translategemma`)
  - Optional: `ffmpeg`, `pytesseract`, `faster-whisper`, `edge-tts`

## 1. Dashboard
- Open `Dashboard` tab.
- Verify KPI cards render without broken text.
- Click refresh and verify latest records table updates.

## 2. Text Translation
- Open `Text Translation` tab.
- Input: `Hello world`
- Source: `English`, Target: `Traditional Chinese`
- Click translate.
- Expected:
  - Streaming output appears.
  - No mojibake / broken glyphs in status or result.
- Optional:
  - Add glossary/style content and verify output still returns.

## 3. Image Translation
- Open `Image Translation` tab.
- Upload a simple screenshot with visible text.
- Click translate.
- Expected:
  - OCR progress/status updates.
  - Final translated output shown.
  - Error message is readable if OCR tool is missing.

## 4. PDF Translation
- Open `PDF Translation` tab.
- Upload a short text PDF (1-3 pages).
- Click translate.
- Expected:
  - Page-by-page progress shown.
  - Final combined output appears.
  - Error message is readable if PDF parser is missing.

## 5. Voice Translation
- Open `Voice Translation` tab.
- Record/upload short audio.
- Click translate.
- Expected:
  - STT text appears.
  - Translation appears.
  - TTS audio is generated (if dependency installed).

## 6. Real-time Voice Translation
- Open `Real-time Voice Translation` tab.
- Speak for 3-8 seconds.
- Expected:
  - Status changes from waiting/recording to translated segment.
  - Transcript and translation append progressively.
  - Reset button clears current stream state.

## 7. Video Translation
- Open `Video Translation` tab.
- Input YouTube URL or upload local video.
- Select one language and run once; then run multi-language batch.
- Expected:
  - Status text is readable.
  - Outputs include video/subtitle files when successful.
  - Batch preview language switch works.

## 8. Meeting Summary
- Open `Meeting Summary` tab.
- Upload short meeting clip.
- Select summary types and run.
- Expected:
  - Progress updates across extract/transcribe/summarize.
  - Transcript and summary tabs populate.
  - Download buttons generate files.

## 9. History
- Open `History` tab.
- Verify rows appear after running at least one task.
- Test filter and refresh.
- Click clear all and verify table refreshes.

## 10. About
- Open `About` tab.
- Verify all paragraphs render with readable text.

## Pass Criteria
- No visible mojibake in UI labels/status/errors.
- All tabs open and operate without frontend exceptions.
- Core paths (Text + one media path + History) complete end-to-end.
