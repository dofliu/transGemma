# TranslateGemma

TranslateGemma 是一個本地優先（Local-first）的多語翻譯工作台，整合文字、圖片 OCR、PDF、語音、即時語音、影片翻譯與會議摘要功能。

## 主要功能
- 文字翻譯：支援多語互譯，提供串流回傳。
- 術語表與風格指南：可在文字翻譯頁提供自訂術語與文風指令。
- 圖片翻譯：Tesseract OCR + 模型翻譯。
- PDF 翻譯：逐頁擷取文字並翻譯。
- 語音翻譯：STT -> 翻譯 -> TTS。
- 即時語音翻譯：分段音訊偵測、即時辨識、即時翻譯與語音回播。
- 影片翻譯與配音：支援 YouTube 連結或本地影片，多語批次輸出。
- 會議摘要：上傳影片後產生逐字稿與摘要。
- 使用紀錄：將任務寫入 SQLite 歷史紀錄。

## 技術棧
- UI: Gradio
- Translation backend: Ollama (`translategemma`)
- OCR: Tesseract + pytesseract
- PDF: PyMuPDF
- STT: faster-whisper
- TTS: edge-tts
- Video: yt-dlp + FFmpeg
- API: FastAPI
- MCP: FastMCP

## 系統需求
- Python 3.10+
- 可用的 Ollama 環境
- 外部工具：Tesseract、FFmpeg

## 快速開始
1. 安裝相依

```bash
pip install -r requirements.txt
```

2. 準備模型

```bash
ollama pull translategemma
```

3. 啟動 Web UI

```bash
python app.py
```

- 預設網址：`http://localhost:7860`

## API 模式

```bash
python api.py
```

- API 文件：`http://localhost:8000/docs`
- Web UI：`http://localhost:8000/`

## MCP 模式

```bash
python mcp_server.py
```

可接入支援 MCP 的 Agent / IDE。

## 測試與健康檢查

```bash
python -m py_compile app.py translator.py languages.py api.py mcp_server.py
python -m unittest discover -s tests/smoke -p "test_*.py"
```

一鍵檢查（PowerShell）：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/check_project_health.ps1
```

嚴格模式（偵測到可疑亂碼即失敗）：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/check_project_health.ps1 -FailOnMojibake
```

## CI
- GitHub Actions workflow: `.github/workflows/health-check.yml`
- 每次 push / pull request 到 `main` 會自動執行嚴格健康檢查。
- CI 也會執行 `eval_runner` 的 dry gate，並上傳 `reports/eval/` 報表 artifact。

## 評測基線（Seed Eval）
資料集位置：
- `datasets/eval/seed_v1.jsonl`

執行（dry-run，不呼叫模型）：

```bash
python tools/eval_runner.py --mode dry
```

執行（live-run，呼叫翻譯模型）：

```bash
python tools/eval_runner.py --mode live --limit 10
```

輸出會放在 `reports/eval/`（JSONL、CSV、Markdown 報告）。

可加入 gate（供 CI 擋版）：

```bash
python tools/eval_runner.py --mode live --limit 20 --max-errors 0 --min-non-empty-rate 0.95
```

## 專案結構

```text
translateGemma/
  app.py
  translator.py
  languages.py
  api.py
  mcp_server.py
  video_dubber.py
  meeting_summarizer.py
  history.py
  docs/
  tests/smoke/
```

## 文件導覽
- 專案藍圖：[docs/PROJECT_BLUEPRINT.md](docs/PROJECT_BLUEPRINT.md)
- 路線圖：[docs/ROADMAP.md](docs/ROADMAP.md)
- 下一步執行清單：[docs/NEXT_STEPS_2026-03-10.md](docs/NEXT_STEPS_2026-03-10.md)
- 架構文件：[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

## 目前已知優先事項
- 文件與編碼治理（持續清理亂碼來源）
- API smoke tests 擴充
- 翻譯品質基線資料集與報表工具

## License
MIT
