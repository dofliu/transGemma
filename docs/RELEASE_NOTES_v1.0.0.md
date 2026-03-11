# TranslateGemma v1.0.0

Release date: 2026-03-11

## Highlights
- Unified multilingual workspace for:
  - Text translation
  - Image OCR translation
  - PDF translation
  - Voice translation
  - Real-time voice translation
  - Video translation/dubbing
  - Meeting summarization

## Major Updates
1. API and MCP coverage expansion
- Added/expanded API endpoints:
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

2. Reliability and operability
- Added explicit auto source-language detection path in translation service.
- Added lightweight long-task job model with status and retry.
- Added strict project health gate:
  - UTF-8 validation
  - mojibake marker scan
  - syntax compile check
  - smoke tests

3. Quality and testing
- Expanded smoke coverage (API + job flow + translator auto-detect tests).
- Added project-level quality and feature review documentation.

## Validation Snapshot
- Health check: `HEALTHY`
- Smoke tests: `Ran 20 tests ... OK`
- Mojibake gate: `PASS`

## Compatibility and Dependencies
- Runtime: Python + local Ollama model (`translategemma`)
- Optional tools by feature:
  - `ffmpeg` (video/audio pipeline)
  - `pytesseract` (OCR)
  - `faster-whisper` (speech-to-text)
  - `edge-tts` (text-to-speech)

## Known Limitations
- Heavy media workflows are resource-sensitive on CPU-only environments.
- Job records are currently in-memory (non-persistent).
- A local environment warning may appear if `matplotlibrc` has duplicate font settings; non-blocking.

## Upgrade Notes
- Install dependencies:
  - `pip install -r requirements.txt`
- Run health gate:
  - `powershell -ExecutionPolicy Bypass -File scripts/check_project_health.ps1 -FailOnMojibake`

## Packaging
- Build artifact:
  - `powershell -ExecutionPolicy Bypass -File scripts/package_release.ps1 -Version v1.0.0`
- Output:
  - `dist/translategemma-v1.0.0-<timestamp>.zip`

## Checklist References
- UI full checklist:
  - `docs/UI_ACCEPTANCE_CHECKLIST_v1.md`
- UI quick release check (10 min):
  - `docs/UI_ACCEPTANCE_QUICKRUN_10MIN_v1.md`
- Release checklist:
  - `docs/RELEASE_CHECKLIST_v1.md`
