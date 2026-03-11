# TECHNICAL

本文件描述 TranslateGemma 的技術架構、核心流程、模組邊界與開發維運重點。

## 1. 架構總覽

TranslateGemma 目前採單體應用（monolith）型態，核心分為：
- 介面層：Gradio (`app.py`)
- 服務層：翻譯服務 (`translator.py`)
- 入口層：FastAPI (`api.py`) / MCP (`mcp_server.py`)
- 任務模組：影片配音 (`video_dubber.py`)、會議摘要 (`meeting_summarizer.py`)
- 基礎設施：歷史紀錄 (`history.py` + `history.db`)

## 2. 主要模組

### 2.1 `app.py`
- 建立主要 UI（儀表板、文字/圖片/PDF/語音/即時語音/影片/會議摘要/歷史/關於）。
- 負責將 UI 輸入轉換成服務呼叫。
- 管理即時語音翻譯狀態（buffer、靜音判定、分段時機）。

### 2.2 `translator.py`
- 封裝與 Ollama 的互動。
- 主要能力：
  - `translate` / `translate_stream`
  - `translate_image`
  - `translate_pdf`
  - `speech_to_text`
  - `text_to_speech`
- 支援文字翻譯的自訂規則：
  - `glossary`（術語表）
  - `style`（風格指南）

### 2.3 `languages.py`
- 集中管理語言代碼、顯示名稱與 locale。
- 提供下拉顯示與 TTS voice mapping。

### 2.4 `api.py`
- 提供 REST API 入口，並掛載 Gradio UI。
- 主要端點：
  - `POST /api/translate/text`
  - `POST /api/translate/image`
  - `POST /api/dub/video`

### 2.5 `mcp_server.py`
- 提供 MCP 工具化介面，支援 Agent 調用翻譯與影片配音。

### 2.6 `history.py`
- 使用 SQLite 儲存歷史紀錄。
- 主要欄位：type、source_lang、target_lang、original_content、translated_content、details。

## 3. 核心流程

### 3.1 文字翻譯
1. UI 收到輸入文字與語言設定。
2. 可選：術語表、風格指南。
3. 呼叫 `translator.translate_stream(...)`。
4. 逐步回傳結果並寫入歷史。

### 3.2 圖片翻譯
1. 上傳圖片。
2. OCR 擷取文字。
3. 逐步翻譯並更新輸出。
4. 儲存歷史。

### 3.3 PDF 翻譯
1. 上傳 PDF。
2. 逐頁擷取文字。
3. 逐頁翻譯與整合格式化輸出。
4. 儲存歷史。

### 3.4 語音翻譯
1. 音訊輸入。
2. STT 轉文字。
3. 翻譯。
4. TTS 合成回播。
5. 儲存歷史。

### 3.5 即時語音翻譯
1. 音訊流分段收集。
2. RMS 靜音判定。
3. 達條件後觸發 STT -> 翻譯 -> TTS。
4. 累積即時逐字與翻譯內容。

## 4. 測試策略

目前已有 `tests/smoke/`：
- `test_translator_smoke.py`
- `test_pipeline_contracts.py`

建議擴充：
- API smoke（mock translator）
- UI 文案/語言資料 sanity check
- 影片與會議摘要的最小路徑測試（可 mock 外部依賴）

## 5. 依賴與外部工具

- 模型：Ollama + `translategemma`
- OCR：Tesseract
- 視訊：FFmpeg、yt-dlp
- STT/TTS：faster-whisper、edge-tts

這些工具缺失時，功能會退化或失敗；文件中需明確列出安裝步驟與 PATH 要求。

## 6. 編碼與文件治理（重要）

歷史上專案曾出現 mojibake（亂碼）問題，導致 UI/文件可讀性受損。

建議固定規範：
- 所有 `.py`、`.md`、`.json` 使用 UTF-8。
- 變更前後執行 smoke checks：

```bash
python -m py_compile app.py translator.py languages.py api.py mcp_server.py
python -m unittest discover -s tests/smoke -p "test_*.py"
```

- 逐步加入自動化編碼檢查腳本（Roadmap Phase 1）。

## 7. 下一步技術方向

- 文件與編碼治理收斂（README/TECHNICAL 持續同步）
- 品質基線資料集（`datasets/eval/`）與報表工具
- 長任務佇列化（video/pdf/meeting summary）
- provider abstraction（local/cloud）
