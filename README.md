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

### 🛠️ Tech Stack

* **LLM Backend**: Ollama (running `translategemma` model)
* **Frontend**: Gradio
* **OCR**: Tesseract + Pytesseract
* **PDF Processing**: PyMuPDF (fitz)
* **Speech-to-Text (STT)**: faster-whisper
* **Text-to-Speech (TTS)**: edge-tts

### 🚀 Quick Start

1. **Clone the repository**

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

4. **Run the application**

    ```bash
    python app.py
    ```

    Open your browser at `http://localhost:7860`.

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

### 🛠️ 技術架構

* **大型語言模型**: Ollama (執行 `translategemma` 模型)
* **前端介面**: Gradio
* **文字識別 (OCR)**: Tesseract + Pytesseract
* **PDF 處理**: PyMuPDF (fitz)
* **語音辨識 (STT)**: faster-whisper
* **語音合成 (TTS)**: edge-tts

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

---

## 📄 License

MIT License
