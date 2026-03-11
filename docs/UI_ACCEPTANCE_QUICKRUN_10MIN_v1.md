# UI Acceptance QuickRun (10 Minutes)

Purpose:
- Fast go/no-go check before release.
- Focus on user-visible correctness and core flows.

Preconditions:
- Run app: `python app.py`
- Open: `http://localhost:7860`
- Ollama model `translategemma` is ready.

## Timer Plan (10 min)
1. Minute 0-1: Open app and check top navigation
- Verify all tab labels are readable.
- Verify no mojibake/broken glyphs.
- Result: `PASS / FAIL`

2. Minute 1-3: Text Translation (must pass)
- Tab: `Text Translation`
- Input: `Hello world`
- Source: `English`, Target: `Traditional Chinese`
- Click translate.
- Expected:
  - Status text is readable.
  - Output appears (streaming or final).
- Result: `PASS / FAIL`

3. Minute 3-4: Image Translation (quick sanity)
- Tab: `Image Translation`
- Upload any test image with text.
- Click translate.
- Expected:
  - Progress/error message is readable.
  - Returns result or clear dependency error.
- Result: `PASS / FAIL / SKIP`

4. Minute 4-5: PDF Translation (quick sanity)
- Tab: `PDF Translation`
- Upload short PDF.
- Click translate.
- Expected:
  - Page progress text is readable.
  - Returns translated output or clear dependency error.
- Result: `PASS / FAIL / SKIP`

5. Minute 5-6: History Tab
- Tab: `History`
- Click refresh.
- Change filter once.
- Expected:
  - Table updates without UI error.
- Result: `PASS / FAIL`

6. Minute 6-7: Meeting Summary tab render check
- Tab: `Meeting Summary`
- Verify controls render (upload, summary type, backend settings).
- Expected:
  - No broken text, no frontend exception.
- Result: `PASS / FAIL`

7. Minute 7-8: Video Translation tab render check
- Tab: `Video Translation`
- Verify URL input + language controls + process button are visible/readable.
- Expected:
  - No broken text, no frontend exception.
- Result: `PASS / FAIL`

8. Minute 8-9: Real-time Voice tab render check
- Tab: `Real-time Voice Translation`
- Verify live controls/status fields render.
- Expected:
  - No broken text, no frontend exception.
- Result: `PASS / FAIL`

9. Minute 9-10: About tab final readability check
- Tab: `About`
- Expected:
  - Paragraphs render correctly, no mojibake.
- Result: `PASS / FAIL`

## Release Decision Rule
- `GO` if:
  - Text Translation = PASS
  - History = PASS
  - No mojibake in top nav/tabs
  - No fatal frontend exception in tab switching
- `NO-GO` otherwise.

## Sign-off
- Tester:
- Date:
- Final: `GO / NO-GO`
- Notes:
