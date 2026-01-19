# TranslateGemma 技術文件

## 專案概述

TranslateGemma 是一個基於 Google TranslateGemma 模型的多功能翻譯工具，透過 Gradio 網頁介面提供文字、圖片、PDF 和語音翻譯功能。

---

## 系統架構

```
┌─────────────────────────────────────────────────────────────┐
│                     Gradio Web UI                            │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐│
│  │文字翻譯 │ │圖片翻譯 │ │PDF翻譯  │ │語音翻譯 │ │即時翻譯 ││
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘│
└───────┼──────────┼──────────┼──────────┼──────────┼────────┘
        │          │          │          │          │
        ▼          ▼          ▼          ▼          ▼
┌─────────────────────────────────────────────────────────────┐
│                  TranslateGemmaService                       │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐ │
│  │ translate()  │ │translate_pdf │ │ speech_to_text()    │ │
│  │ translate    │ │translate     │ │ text_to_speech()    │ │
│  │ _stream()    │ │ _image()     │ │                      │ │
│  └──────┬───────┘ └──────┬───────┘ └──────────┬───────────┘ │
└─────────┼────────────────┼────────────────────┼─────────────┘
          │                │                    │
          ▼                ▼                    ▼
┌─────────────────┐ ┌──────────────┐ ┌────────────────────────┐
│     Ollama      │ │   PyMuPDF    │ │  faster-whisper (STT)  │
│ TranslateGemma  │ │  Tesseract   │ │   edge-tts (TTS)       │
└─────────────────┘ └──────────────┘ └────────────────────────┘
```

---

## 檔案結構

```
translateGemma/
├── app.py              # Gradio UI 主程式
├── translator.py       # 翻譯服務核心
├── languages.py        # 55 種語言定義
├── requirements.txt    # Python 依賴
└── TECHNICAL.md        # 本技術文件
```

---

## 即時語音翻譯處理機制

### 流程圖

```
麥克風輸入 (Gradio streaming)
         │
         ▼ (每 ~250ms 傳送一個 audio_chunk)
    ┌────────────────────────────────────┐
    │     process_stream_chunk()          │
    │                                     │
    │  1. 接收 (sample_rate, audio_data) │
    │  2. 累積到 audio_buffer[]          │
    │  3. 計算累積長度                    │
    │  4. 靜音偵測 (RMS 計算)            │
    │  5. 連續靜音計數                    │
    │  6. 判斷是否處理                    │
    └────────────────────────────────────┘
         │
         ├─ 否 → 返回狀態，繼續累積
         │
         ▼ 是
    ┌────────────────────────────────────┐
    │  7. 合併 buffer → WAV 檔案         │
    │  8. Whisper STT → 文字             │
    │  9. TranslateGemma → 翻譯          │
    │  10. edge-tts → 語音輸出           │
    └────────────────────────────────────┘
         │
         ▼
    顯示結果 + 自動播放語音
```

### 靜音偵測演算法

```python
def is_silence(audio_chunk, threshold=0.02):
    """
    使用 RMS (Root Mean Square) 計算音量
    若 RMS < threshold × 32768 則判定為靜音
    """
    rms = sqrt(mean(audio_chunk ** 2))
    return rms < threshold * 32768
```

### 段落判定邏輯

```python
# 觸發處理的條件：
should_process = (
    # 條件 A: 連續靜音達標 且 累積時間足夠
    (silence_count >= 3 and audio_length >= 3.0秒) or
    # 條件 B: 累積時間達上限（強制處理）
    (audio_length >= 15.0秒)
)
```

### 可調整參數

| 參數 | 預設值 | UI 可調 | 說明 |
|------|--------|---------|------|
| `silence_threshold` | 0.02 | ✅ 滑桿 | RMS 判定靜音的門檻值 |
| `silence_chunks_needed` | 3 | ❌ | 需要連續幾個靜音片段 |
| `min_audio_length` | 3.0s | ❌ | 最少累積時間 |
| `max_audio_length` | 15.0s | ❌ | 最多累積時間（強制處理）|

---

## 各功能技術細節

### 1. 文字翻譯

- **模型**: TranslateGemma (Ollama)
- **特點**: 串流輸出、繁體中文優化 prompt

### 2. 圖片翻譯

- **OCR**: Tesseract
- **支援語言**: chi_tra, chi_sim, eng, jpn, kor 等
- **流程**: 圖片 → OCR → 翻譯

### 3. PDF 翻譯

- **提取**: PyMuPDF (fitz)
- **處理**: 逐頁提取文字 → 翻譯 → 串流顯示

### 4. 語音翻譯

- **STT**: faster-whisper (base 模型)
- **TTS**: edge-tts (Microsoft Neural Voice)
- **台灣語音**: zh-TW-HsiaoChenNeural

### 5. 即時翻譯

- **輸入**: Gradio streaming audio
- **分段**: 連續靜音偵測
- **輸出**: 自動播放 TTS

---

## 依賴套件

| 套件 | 用途 |
|------|------|
| gradio | Web UI 框架 |
| ollama | LLM 呼叫 |
| pytesseract | OCR |
| Pillow | 圖片處理 |
| PyMuPDF | PDF 處理 |
| faster-whisper | 語音辨識 |
| edge-tts | 語音合成 |

---

## 啟動方式

```bash
cd d:\Dropbox\Project_CodingSimulation\MCP\translateGemma
python app.py
# 開啟 http://localhost:7860
```
