# Next Steps (2026-03-10)

## Completed Today
1. `P1-2` API/MCP parity (core workflows)
- Added API endpoints for language list, PDF translation, text batch, and async job operations.
- Added MCP tools for language list, text batch, and PDF translation.

2. `P2` Auto source-language reliability
- Added explicit `auto` language detection flow in translation service.
- Added smoke tests for language auto-detection behavior.

3. `P2` Long-task resilience baseline
- Added lightweight async job model with job ID, status, list, and retry for video/meeting summary tasks.
- Added smoke tests for job list/get/retry behavior.

## Remaining Priority
1. `P1-1` Message sanitation
- Continue replacing residual mojibake in user-visible runtime messages (especially edge/error paths).

2. API parity extensions
- Add minimal voice translation endpoint to align with UI voice workflow.

3. Hardening
- Persist job state to storage (current implementation is in-memory only).
- Add retry backoff and timeout handling for heavy workloads.

## Verification Commands
1. `python -m py_compile api.py mcp_server.py translator.py meeting_summarizer.py app.py`
2. `python -m unittest discover -s tests/smoke -p "test_*.py"`
3. `powershell -ExecutionPolicy Bypass -File scripts/check_project_health.ps1 -FailOnMojibake`
