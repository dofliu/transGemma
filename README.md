# TranslateGemma 翻譯工具

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![Gradio](https://img.shields.io/badge/Gradio-UI-orange)](https://gradio.app/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

[English](#english) | [中文說明](#中文說明)

---

<a name="english"></a>

## 🇬🇧 English Description

**TranslateGemma** is a comprehensive translation tool powered by Google's **TranslateGemma** model (fine-tuned on Gemma 3). It provides a user-friendly web interface built with **Gradio** to support essential translation needs including text, images, PDF documents, and real-time voice.

### 🌟 Key Features

* **📝 Text Translation**: Support for 55 languages with high-quality output.
* **🖼️ Image Translation**: Integrated OCR (Tesseract) to extract and translate text from images.
* **📄 PDF Translation**: Extract text from PDF documents and translate them page by page.
* **🎙️ Voice Translation**: Record voice, transcribe using **faster-whisper**, translate, and read aloud using **edge-tts**.
* **⚡ Real-time Streaming Translation**: Live speech-to-text-to-translation pipeline with automatic audio playback for seamless communication.
* **🎥 Video Translation & Dubbing** *(NEW)*: Download YouTube videos, generate subtitles, translate to multiple languages, and create dubbed videos with burned-in subtitles.

### 🛠️ Tech Stack

* **LLM Backend**: Ollama (running `translategemma` model)
* **Frontend**: Gradio
* **OCR**: Tesseract + Pytesseract
* **PDF Processing**: PyMuPDF (fitz)
* **Speech-to-Text (STT)**: faster-whisper
* **Text-to-Speech (TTS)**: edge-tts
* **Video Processing**: yt-dlp + FFmpeg

### 🚀 Quick Start

1. **Clone and install**

    ```bash
    git clone https://github.com/dofliu/transGemma.git
    cd transGemma
    ```

2. **Install dependencies**

    ```bash
    pip install -r requirements.txt
    ```

3. **Install external tools**
    * **Ollama**: Install [Ollama](https://ollama.com/) and pull the model: `ollama run translategemma`
    * **Tesseract OCR**: Install [Tesseract](https://github.com/tesseract-ocr/tesseract) and add it to your system PATH.
    * **FFmpeg**: Install [FFmpeg](https://ffmpeg.org/) for video processing.

4. **Run the application**

    ```bash
    python app.py
    ```

    OPEN YOUR BROWSER AT `http://localhost:7860`.

### 🔌 API Mode

To run TranslateGemma as a REST API (FastAPI) which also serves the Web UI:

```bash
python api.py
```

* **API Docs**: `http://localhost:8000/docs`
* **Web UI**: `http://localhost:8000/`

### 🤖 MCP Server

TranslateGemma supports the **Model Context Protocol (MCP)**, allowing integration with AI agents like **Claude Desktop** or **Cursor**.

Add the following configuration to your MCP settings (e.g., `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "translategemma": {
      "command": "python",
      "args": ["/absolute/path/to/transGemma/mcp_server.py"]
    }
  }
}
```

---

<a name="中文說明"></a>

## 🇹🇼 中文說明

**TranslateGemma** 是一個基於 Google **TranslateGemma** 模型（基於 Gemma 3 微調）的多功能翻譯工具。透過 **Gradio** 建構的友善網頁介面，提供文字、圖片、PDF 文件以及即時語音翻譯的全方位解決方案。

### 🌟 主要功能

* **📝 文字翻譯**：支援 55 種語言互譯，針對繁體中文語境優化。
* **🖼️ 圖片翻譯**：整合 Tesseract OCR 技術，自動識別圖片文字並進行翻譯。
* **📄 PDF 翻譯**：從 PDF 文件中提取文字，支援逐頁翻譯與進度顯示。
* **🎙️ 語音翻譯**：錄製語音，使用 **faster-whisper** 辨識，翻譯後透過 **edge-tts** 朗讀。
* **⚡ 即時串流翻譯**：即時接收麥克風輸入，邊說邊譯，並自動播放翻譯語音，實現無縫溝通。
* **🎥 影片翻譯與配音** *(新功能)*：下載 YouTube 影片，生成字幕，翻譯成多種語言，並製作帶有燒錄字幕的配音影片。

### 🛠️ 技術架構

* **大型語言模型**: Ollama (執行 `translategemma` 模型)
* **前端介面**: Gradio
* **文字識別 (OCR)**: Tesseract + Pytesseract
* **PDF 處理**: PyMuPDF (fitz)
* **語音辨識 (STT)**: faster-whisper
* **語音合成 (TTS)**: edge-tts
* **影片處理**: yt-dlp + FFmpeg

### 🚀 快速開始

1. **下載專案**

    ```bash
    git clone https://github.com/dofliu/transGemma.git
    cd transGemma
    ```

2. **安裝依賴套件**

    ```bash
    pip install -r requirements.txt
    ```

3. **安裝外部工具**
    * **Ollama**: 下載並安裝 [Ollama](https://ollama.com/)，然後執行：`ollama run translategemma`
    * **Tesseract OCR**: 安裝 [Tesseract](https://github.com/tesseract-ocr/tesseract) 並確保已加入系統 PATH 環境變數。

4. **執行應用程式**

    ```bash
    python app.py
    ```

    在瀏覽器打開 `http://localhost:7860` 即可使用。

### 🔌 API 模式

啟動 API 模式（同時提供 REST API 與網頁介面）：

```bash
python api.py
```

* **API 文件**: `http://localhost:8000/docs`
* **網頁介面**: `http://localhost:8000/`

### 🤖 MCP Server

TranslateGemma 支援 **Model Context Protocol (MCP)**，可供 **Claude Desktop** 或 **Cursor** 等 AI Agent 調用。

請將以下設定加入您的 MCP 設定檔（如 `claude_desktop_config.json`）：

```json
{
  "mcpServers": {
    "translategemma": {
      "command": "python",
      "args": ["/absolute/path/to/transGemma/mcp_server.py"]
    }
  }
}
```

---

<a name="roadmap"></a>

## 🗺️ Roadmap / 未來規劃

### 🔥 High Priority / 高優先級

* **Format-preserving PDF Translation / 格式保留 PDF 翻譯**: Translate PDF documents while maintaining original layout and formatting (similar to BabelDOC).
* **Scanned PDF Support / 掃描版 PDF 支援**: Enhanced support for scanned PDFs using OCR.

### ⭐ Planned Features / 規劃中功能

* ~~**Translation History / 翻譯歷史記錄**~~: ✅ Completed (`history.py`)
* ~~**API Mode / API 模式**~~: ✅ Completed (`api.py`)
* ~~**MCP Server**~~: ✅ Completed (`mcp_server.py`)
* **Batch Translation / 批次翻譯**: Process multiple files at once.
* **Performance Optimization / 效能優化**: Further optimization for local inference speed.

### 🌐 Multi-Platform Integration / 多平台整合 (Future)

* **Browser Extension / 瀏覽器擴充套件**: Chrome/Edge extension for in-page translation, similar to Immersive Translate.
* **Windows System Tray Tool / Windows 托盤工具**: Global hotkey (`Ctrl+Alt+T`), clipboard monitoring, floating translation window.
* **Enhanced MCP Tools / 強化 MCP 工具**: Add `translate_pdf`, `translate_clipboard`, `get_supported_languages` tools.
* **PDF Reader Integration / PDF 閱讀器整合**: Integration with Zotero, SumatraPDF, or built-in reader.

---

## 📄 License

MIT License
