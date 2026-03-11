# TranslateGemma v1.0.0 Release Notes (Template)

Release date: `YYYY-MM-DD`

## Highlights
- End-to-end multilingual translation workspace covering:
  - Text translation
  - Image OCR translation
  - PDF translation
  - Voice translation
  - Real-time voice translation
  - Video translation/dubbing
  - Meeting summarization

## What Changed
1. Product and UX
- Refined UI structure and module separation.
- Improved readability and consistency for user-visible messages.

2. API and MCP
- Added/expanded API coverage:
  - `GET /api/languages`
  - `POST /api/translate/text`
  - `POST /api/translate/text/batch`
  - `POST /api/translate/image`
  - `POST /api/translate/pdf`
  - `POST /api/dub/video`
  - `POST /api/jobs/video`
  - `POST /api/jobs/meeting-summary`
  - `GET /api/jobs`
  - `GET /api/jobs/{job_id}`
  - `POST /api/jobs/{job_id}/retry`
- Added/expanded MCP tools:
  - `list_languages`
  - `translate_text`
  - `translate_batch_text`
  - `translate_image`
  - `translate_pdf`
  - `dub_video`

3. Reliability
- Added explicit auto source-language detection path.
- Added lightweight long-task status/retry primitives (job model).
- Added health-check script with UTF-8/mojibake gate.

4. Testing and Quality
- Expanded smoke test coverage.
- Added quality/evaluation scaffolding and docs updates.

## Compatibility Notes
- Python runtime: `[fill version]`
- Requires local model runtime (Ollama) for translation.
- Optional external tools by feature:
  - `ffmpeg` (video/audio pipelines)
  - `pytesseract` + OCR runtime
  - `faster-whisper` (STT)
  - `edge-tts` (TTS)

## Known Limitations
- Some heavy media workflows depend on local machine resources and installed external tools.
- In-memory job storage is suitable for local use, not production persistence.

## Upgrade Notes
- Pull latest code and install dependencies:
  - `pip install -r requirements.txt`
- Re-run health gate:
  - `powershell -ExecutionPolicy Bypass -File scripts/check_project_health.ps1 -FailOnMojibake`

## Verification Snapshot
- Smoke tests: `PASS`
- Health check: `HEALTHY`
- Manual UI acceptance: `[PASS / PENDING / FAIL]`

## Artifact
- Package: `dist/translategemma-v1.0.0-<timestamp>.zip`
- SHA256: `[fill hash]`

## Contributors
- `[name 1]`
- `[name 2]`
