# TranslateGemma Roadmap (Updated: 2026-03-10)

## Current Status
- Core features are available: text/image/pdf/voice/streaming/video/meeting summary.
- UI has been refreshed and smoke tests are in place.
- Main gap is project hardening: documentation quality, encoding consistency, evaluation data, and release workflow.

## Phase 1 (Next 2 Weeks): Stabilize Foundation
- Goal:
  - Make the project reliable for daily use and team collaboration.
- Deliverables:
  - Rebuild `README.md` and `TECHNICAL.md` in clean UTF-8 (Traditional Chinese + English sections).
  - Add encoding sanity checks to prevent mojibake regressions.
  - Expand smoke tests to cover API endpoints (`/api/translate/text`, `/api/translate/image` minimal path).
  - Add `scripts/check_project_health.ps1` for one-command checks (compile + tests + basic lint).
- Exit Criteria:
  - New contributor can run app within 30-60 minutes using docs only.
  - No visible mojibake in UI/documentation.
  - Smoke tests pass in local and CI (if CI enabled).

## Phase 2 (Weeks 3-4): Translation Quality Infrastructure
- Goal:
  - Build measurable translation quality loop.
- Deliverables:
  - Create `datasets/eval/` with seed set (at least 30 items across zh/en/ja/ko, plus OCR/PDF samples).
  - Add `tools/eval_runner.py` to run baseline quality reports (automatic metrics + manual rubric template).
  - Add glossary/style test cases for text translation.
- Exit Criteria:
  - Quality report can be generated in one command.
  - Baseline quality score archived and reproducible.

## Phase 3 (Month 2): Production Workflow
- Goal:
  - Improve throughput and operational UX for heavy tasks.
- Deliverables:
  - Add lightweight job queue for long tasks (video/pdf/meeting summary).
  - Add unified task status panel in UI (queued/running/done/failed).
  - Add retry + resumable output for batch jobs.
- Exit Criteria:
  - Long-running tasks are trackable and retryable.
  - Failure cases no longer require full restart.

## Phase 4 (Month 3): Multi-Provider Architecture
- Goal:
  - Support model routing and fallback strategy.
- Deliverables:
  - Introduce provider abstraction (`local_ollama`, `cloud_provider`) behind translation service.
  - Add policy-based routing (cost/latency/quality mode).
  - Extend API/MCP with batch and provider selection parameters.
- Exit Criteria:
  - Same request contract works across at least two providers.
  - Automatic fallback works when primary provider fails.

## Risks & Dependencies
- External tools dependency (Ollama/Tesseract/FFmpeg) still affects onboarding quality.
- Video and meeting-summary paths are resource heavy on CPU-only machines.
- Model output consistency requires evaluation loop; without it, regressions are hard to detect.

## Definition of Done (For Any Feature)
- Code:
  - Feature implemented with backward-compatible interfaces where possible.
- Quality:
  - Relevant smoke tests updated or added.
- Docs:
  - User-facing docs and technical notes updated.
- Operability:
  - Clear run/test command and expected output documented.
