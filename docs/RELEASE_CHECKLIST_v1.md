# Release Checklist (v1)

## 1. Pre-Release Gate
- Run:
  - `powershell -ExecutionPolicy Bypass -File scripts/check_project_health.ps1 -FailOnMojibake`
- Must pass:
  - UTF-8 validation
  - mojibake marker scan
  - py_compile
  - smoke tests

## 2. Functional Validation
- Execute `docs/UI_ACCEPTANCE_CHECKLIST_v1.md`.
- Confirm:
  - Text translation path
  - At least one media path (image/pdf/voice/video)
  - Meeting summary path
  - History tab path

## 3. API/MCP Sanity
- API smoke:
  - `python -m unittest discover -s tests/smoke -p "test_*.py"`
- Spot-check endpoints:
  - `/api/languages`
  - `/api/translate/text`
  - `/api/translate/text/batch`
  - `/api/translate/image`
  - `/api/translate/pdf`
  - `/api/jobs/*`
- Confirm MCP server starts and tools list loads.

## 4. Versioning
- Choose release version tag (example: `v1.0.0`).
- Update release notes with:
  - Added features
  - Breaking/non-breaking behavior
  - Known limitations

## 5. Package Build
- Run:
  - `powershell -ExecutionPolicy Bypass -File scripts/package_release.ps1 -Version v1.0.0`
- Output:
  - `dist/translategemma-v1.0.0-<timestamp>.zip`

## 6. Package Validation
- Unzip artifact in clean folder.
- Validate:
  - `README.md`, `requirements.txt`, `app.py`, `api.py`, `mcp_server.py` exist.
  - `python app.py` starts.
  - `python api.py` starts.

## 7. Publish
- Create git tag and push.
- Attach `dist/*.zip` to release entry.
- Include checksum if needed:
  - `Get-FileHash dist\\<artifact>.zip -Algorithm SHA256`

## 8. Post-Release
- Smoke run in release environment.
- Log known warnings/deps (for example local `matplotlibrc` duplicate font warning).
- Open follow-up issues for non-blocking improvements.
