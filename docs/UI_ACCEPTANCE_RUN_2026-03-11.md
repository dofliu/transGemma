# UI Acceptance Run (2026-03-11)

Operator:
- Tester: `user`
- App URL: `http://127.0.0.1:8899`
- Checklist reference: `docs/UI_ACCEPTANCE_QUICKRUN_10MIN_v1.md`

Packaging:
- Artifact: `dist/translategemma-v1.0.0-20260311-002403.zip`
- SHA256: `EB67AD993B0760D7C99B2866E01D94BFDF799A44EA302A06F60701F5C187D921`

## Pass/Fail Log
1. Top navigation readability: `PASS` (screenshot verified, 127.0.0.1:8899)
2. Text Translation core flow: `PASS` (`HELLO WORLD` -> translated output shown)
3. Image Translation quick sanity: `PASS`
4. PDF Translation quick sanity: `PASS`
5. History refresh/filter: `PASS`
6. Meeting Summary tab render: `PASS` (UI config build + tab structure check passed)
7. Video Translation tab render: `FAIL` (runtime 403 Forbidden from external source video)
8. Real-time Voice tab render: `PASS`
9. About tab readability: `PASS`
10. Fatal frontend exception during tab switch: `PASS` (current session stable)

## Final Decision
- Release decision: `GO (with known limitation)`
- Notes: `Core UI flows pass. Known limitation: video URL path may fail with external source HTTP 403; use local upload, alternate URL, or updated yt-dlp/cookies as workaround.`
