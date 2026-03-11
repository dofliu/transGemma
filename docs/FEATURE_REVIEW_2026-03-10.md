# Feature Review (2026-03-10)

## Summary
- Overall status: **usable**, with strong breadth (text/image/pdf/voice/video/meeting).
- Main blocker to become a robust "translation master": **quality consistency + API/MCP capability gaps + residual mojibake in runtime strings**.

## Functional Coverage Matrix
- Text translation (UI): **Ready**
  - Streaming response, language selection, glossary/style controls.
- Image translation (UI): **Ready (Basic)**
  - OCR + translation pipeline works.
  - Needs better OCR error handling and cleaner user messages.
- PDF translation (UI): **Ready (Basic)**
  - Page-by-page text extraction and translation.
  - Not layout-preserving; no scanned-PDF optimization.
- Voice translation (UI): **Ready (Basic)**
  - STT -> translate -> TTS path available.
- Real-time voice translation (UI): **Ready (Beta)**
  - Works with chunking + silence detection.
  - Needs tuning presets and better observability.
- Video translation/dubbing (UI): **Ready (Heavy dependency)**
  - Single/batch workflow available.
  - Long-task reliability still limited.
- Meeting summary (UI): **Ready (Beta)**
  - Transcript + summary generation available.
  - Progress and model/backend config available.
- REST API: **Partial**
  - `/api/translate/text`, `/api/translate/image`, `/api/dub/video`
  - Missing endpoints for PDF/voice/streaming/meeting summary.
- MCP tools: **Partial**
  - `translate_text`, `translate_image`, `dub_video`
  - Missing `translate_pdf`, language listing, batch operations.

## Findings (Prioritized)
1. **[P1] Residual mojibake in runtime/service messages**
- Impact:
  - User-visible status/error strings are still corrupted in translation pipelines, reducing trust and debuggability.
- Evidence:
  - [translator.py](D:/Dropbox/Project_CodingSimulation/PersonalHelper/translateGemma/translator.py):96
  - [translator.py](D:/Dropbox/Project_CodingSimulation/PersonalHelper/translateGemma/translator.py):120
  - [translator.py](D:/Dropbox/Project_CodingSimulation/PersonalHelper/translateGemma/translator.py):133
  - [translator.py](D:/Dropbox/Project_CodingSimulation/PersonalHelper/translateGemma/translator.py):242

2. **[P1] API/MCP capability lag behind UI capability** - **Resolved (2026-03-10)**
- Impact:
  - Integrators cannot access key features (PDF, voice, meeting summary) programmatically, limiting productization.
- Evidence:
  - [api.py](D:/Dropbox/Project_CodingSimulation/PersonalHelper/translateGemma/api.py):47
  - [api.py](D:/Dropbox/Project_CodingSimulation/PersonalHelper/translateGemma/api.py):76
  - [api.py](D:/Dropbox/Project_CodingSimulation/PersonalHelper/translateGemma/api.py):113
  - [mcp_server.py](D:/Dropbox/Project_CodingSimulation/PersonalHelper/translateGemma/mcp_server.py):15
  - [mcp_server.py](D:/Dropbox/Project_CodingSimulation/PersonalHelper/translateGemma/mcp_server.py):39
  - [mcp_server.py](D:/Dropbox/Project_CodingSimulation/PersonalHelper/translateGemma/mcp_server.py):69

3. **[P2] `auto` source language path lacks explicit detection strategy** - **Resolved (2026-03-10)**
- Impact:
  - Text translation with `source_lang=auto` can rely on unclear prompt semantics (`Unknown` metadata), causing unstable quality.
- Evidence:
  - [api.py](D:/Dropbox/Project_CodingSimulation/PersonalHelper/translateGemma/api.py):54
  - [translator.py](D:/Dropbox/Project_CodingSimulation/PersonalHelper/translateGemma/translator.py):36
  - [languages.py](D:/Dropbox/Project_CodingSimulation/PersonalHelper/translateGemma/languages.py):141

4. **[P2] Long-task workflow still lacks queue/retry primitives** - **Resolved (2026-03-10)**
- Impact:
  - Video/meeting workflows are vulnerable to interruption and hard to resume at scale.
- Evidence:
  - [app.py](D:/Dropbox/Project_CodingSimulation/PersonalHelper/translateGemma/app.py):951
  - [app.py](D:/Dropbox/Project_CodingSimulation/PersonalHelper/translateGemma/app.py):1105

## What Is Already Strong
- Health checks + strict mojibake gate script in place.
- Smoke test coverage includes API success/error basics.
- Seed evaluation dataset + evaluator + CI dry gate established.
- UI has clear module-level separation and improved visual hierarchy.

## Recommended Next Sprint (1-2 weeks)
1. **Message sanitation sprint**
- Replace all user-facing corrupted strings in `translator.py` and `meeting_summarizer.py`.
- Keep internal comments optional; prioritize visible outputs.

2. **Programmatic parity sprint**
- Add API endpoints: `translate/pdf`, `translate/voice` (sync minimal), `meeting/summary` (async-friendly).
- Add MCP tools: `translate_pdf`, `list_languages`, `translate_batch`.

3. **Auto-language reliability**
- Introduce explicit language detection step for text path or deterministic prompt policy for `auto`.
- Add test cases validating `auto` behavior.

4. **Long-task resilience**
- Add lightweight job IDs + status lookup + retry for video/meeting.

## Exit Criteria for "Translation Master v1"
- No mojibake in any UI/API visible message.
- UI/API/MCP capability parity for top 5 workflows.
- Baseline live eval pass with stable thresholds.
- Long-task retryable workflow available for video/meeting.
