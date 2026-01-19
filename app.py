"""
TranslateGemma 網頁介面
========================
使用 Gradio 建立的多功能翻譯介面

啟動方式：
    python app.py

功能：
    1. 多語言文字翻譯
    2. 圖片 OCR 翻譯
    3. 55 種語言支援
"""

import gradio as gr
from translator import translator
from languages import LANGUAGES, COMMON_LANGUAGES, get_language_info

# ============ 介面常數 ============
TITLE = "🌐 TranslateGemma 翻譯工具"
DESCRIPTION = """
基於 Google TranslateGemma 模型的多語言翻譯工具，支援 55 種語言互譯。

**功能特色**：
- ✨ 高品質機器翻譯
- 🖼️ 圖片文字識別與翻譯
- 🌏 支援 55 種語言
- ⚡ 串流輸出即時顯示
"""


def get_dropdown_choices():
    """取得語言下拉選單選項"""
    choices = []
    
    # 常用語言
    for code in COMMON_LANGUAGES:
        if code in LANGUAGES:
            ch_name, en_name, locale = LANGUAGES[code]
            choices.append((f"⭐ {ch_name} ({en_name})", code))
    
    # 其他語言
    other_langs = [(code, info) for code, info in LANGUAGES.items() 
                   if code not in COMMON_LANGUAGES]
    other_langs.sort(key=lambda x: x[1][0])
    
    for code, (ch_name, en_name, locale) in other_langs:
        choices.append((f"{ch_name} ({en_name})", code))
    
    return choices


def translate_text(text: str, source_lang: str, target_lang: str):
    """文字翻譯（串流）"""
    if not text.strip():
        yield "請輸入要翻譯的文字..."
        return
    
    src_info = get_language_info(source_lang)
    tgt_info = get_language_info(target_lang)
    
    yield f"🔄 翻譯中... ({src_info[0]} → {tgt_info[0]})\n"
    
    for result in translator.translate_stream(text, source_lang, target_lang):
        yield result


def translate_image(image, source_lang: str, target_lang: str):
    """圖片翻譯（Tesseract OCR + TranslateGemma 翻譯）"""
    if image is None:
        yield "請上傳圖片..."
        return
    
    for result in translator.translate_image(image, target_lang, source_lang):
        yield result


def translate_pdf(pdf_file, source_lang: str, target_lang: str):
    """PDF 文件翻譯"""
    if pdf_file is None:
        yield "請上傳 PDF 文件..."
        return
    
    for result in translator.translate_pdf(pdf_file, target_lang, source_lang):
        yield result


import asyncio

def translate_voice(audio, source_lang: str, target_lang: str):
    """語音翻譯（STT → 翻譯 → TTS）"""
    if audio is None:
        return "請錄製或上傳音檔...", "", None
    
    # 1. 語音辨識 (STT)
    recognized_text, detected_lang = translator.speech_to_text(audio, source_lang)
    
    if recognized_text.startswith("❌"):
        return recognized_text, "", None
    
    if not recognized_text:
        return "⚠️ 無法識別語音內容", "", None
    
    # 2. 翻譯文字
    translated_text = translator.translate(recognized_text, source_lang, target_lang)
    
    # 3. 文字轉語音 (TTS)
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        audio_path = loop.run_until_complete(translator.text_to_speech(translated_text, target_lang))
        loop.close()
    except Exception as e:
        audio_path = None
        print(f"TTS 錯誤: {e}")
    
    return recognized_text, translated_text, audio_path


# ========== 影片翻譯功能 ==========
from video_dubber import VideoDubber

# 全域影片處理器
video_dubber_instance = None

def process_video_translation(video_source, source_lang: str, target_langs, 
                               burn_subtitles: bool = False, progress=gr.Progress()):
    """處理影片翻譯與配音（支援多語言批次）"""
    global video_dubber_instance
    
    if not video_source:
        return None, None, None, None, "請提供 YouTube 網址或上傳影片檔案"
    
    # 處理多語言
    if isinstance(target_langs, list):
        langs_list = target_langs if target_langs else ["zh_TW"]
    else:
        langs_list = [target_langs]
    
    # 建立新的處理器
    video_dubber_instance = VideoDubber()
    
    def update_progress(msg):
        progress(0.5, desc=msg)
    
    try:
        # 判斷來源類型
        if isinstance(video_source, str) and video_source.startswith('http'):
            source = video_source
        else:
            source = video_source  # 檔案路徑
        
        if len(langs_list) == 1:
            # 單一語言：使用原本的方法
            results = video_dubber_instance.process_video(
                source, source_lang, langs_list[0], 
                burn_subtitles=burn_subtitles,
                progress_callback=update_progress
            )
            return (
                results.get('original_video'),
                results.get('dubbed_video'),
                results.get('original_srt'),
                results.get('translated_srt'),
                "✅ 處理完成！"
            )
        else:
            # 多語言：使用批次處理
            batch_results = video_dubber_instance.process_video_batch(
                source, source_lang, langs_list,
                burn_subtitles=burn_subtitles,
                progress_callback=update_progress
            )
            
            # 返回第一個語言的結果到預覽，其他語言的結果在狀態中說明
            first_lang = langs_list[0]
            first_result = batch_results['languages'].get(first_lang, {})
            
            status_msg = f"✅ 批次處理完成！共處理 {len(langs_list)} 種語言:\n"
            for lang in langs_list:
                lang_res = batch_results['languages'].get(lang, {})
                if lang_res.get('dubbed_video'):
                    status_msg += f"  ✓ {lang}: {lang_res['dubbed_video']}\n"
            
            return (
                batch_results.get('original_video'),
                first_result.get('dubbed_video'),
                batch_results.get('original_srt'),
                first_result.get('translated_srt'),
                status_msg
            )
    except Exception as e:
        return None, None, None, None, f"❌ 錯誤: {str(e)}"


import numpy as np
import tempfile
import wave
import os

# 串流翻譯的全域狀態
class StreamState:
    def __init__(self):
        self.audio_buffer = []
        self.sample_rate = 16000
        self.silence_threshold = 0.02  # 提高門檻值（降低敏感度）
        self.min_audio_length = 3.0    # 最少累積 3 秒（原本 1 秒）
        self.max_audio_length = 15.0   # 最多累積 15 秒（原本 10 秒）
        self.silence_count = 0         # 連續靜音計數
        self.silence_chunks_needed = 3 # 需要連續 3 個靜音片段才判定為段落結束
        self.last_transcript = ""
        self.full_transcript = ""
        self.full_translation = ""

stream_state = StreamState()


def is_silence(audio_chunk: np.ndarray, threshold: float = 0.02) -> bool:
    """判斷音訊片段是否為靜音（提高門檻值降低敏感度）"""
    if audio_chunk is None or len(audio_chunk) == 0:
        return True
    rms = np.sqrt(np.mean(audio_chunk.astype(float) ** 2))
    return rms < threshold * 32768  # 16-bit audio


def save_audio_buffer(audio_data: np.ndarray, sample_rate: int) -> str:
    """將音訊緩衝儲存為臨時 WAV 檔案"""
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, f"stream_audio_{id(audio_data)}.wav")
    
    with wave.open(temp_path, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(audio_data.astype(np.int16).tobytes())
    
    return temp_path


def process_stream_chunk(audio_chunk, source_lang: str, target_lang: str, silence_threshold: float = 0.02):
    """處理串流音訊片段"""
    global stream_state
    
    # 更新靜音門檻值
    stream_state.silence_threshold = silence_threshold
    
    if audio_chunk is None:
        return stream_state.full_transcript, stream_state.full_translation, "等待語音輸入...", None
    
    sample_rate, audio_data = audio_chunk
    
    # 轉換為單聲道
    if len(audio_data.shape) > 1:
        audio_data = audio_data.mean(axis=1)
    
    # 累積音訊
    stream_state.audio_buffer.append(audio_data)
    stream_state.sample_rate = sample_rate
    
    # 計算累積長度
    total_samples = sum(len(chunk) for chunk in stream_state.audio_buffer)
    audio_length = total_samples / sample_rate
    
    # 改進的靜音偵測：需要連續多個靜音片段
    is_silent = is_silence(audio_data, stream_state.silence_threshold)
    
    if is_silent:
        stream_state.silence_count += 1
    else:
        stream_state.silence_count = 0  # 重置計數
    
    # 判斷是否應該處理
    continuous_silence = stream_state.silence_count >= stream_state.silence_chunks_needed
    should_process = (
        (continuous_silence and audio_length >= stream_state.min_audio_length) or
        (audio_length >= stream_state.max_audio_length)
    )
    
    if not should_process:
        silence_indicator = "🔇" if is_silent else "🔊"
        status = f"🎤 錄音中... ({audio_length:.1f}s) {silence_indicator}"
        return stream_state.full_transcript, stream_state.full_translation, status, None
    
    # 合併並處理音訊
    full_audio = np.concatenate(stream_state.audio_buffer)
    stream_state.audio_buffer = []  # 清空緩衝
    stream_state.silence_count = 0  # 重置靜音計數
    
    # 儲存為臨時檔案
    temp_path = save_audio_buffer(full_audio, sample_rate)
    
    tts_audio_path = None
    
    try:
        # STT
        recognized, detected_lang = translator.speech_to_text(temp_path, source_lang)
        
        if recognized and not recognized.startswith("❌"):
            stream_state.full_transcript += recognized + " "
            
            # 翻譯
            translated = translator.translate(recognized, source_lang, target_lang)
            stream_state.full_translation += translated + " "
            
            # TTS - 生成翻譯語音
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                tts_audio_path = loop.run_until_complete(translator.text_to_speech(translated, target_lang))
                loop.close()
            except Exception as e:
                print(f"TTS 錯誤: {e}")
        
        # 清理臨時檔案
        os.remove(temp_path)
        
    except Exception as e:
        print(f"串流處理錯誤: {e}")
    
    status = "✅ 段落處理完成，繼續說話..."
    return stream_state.full_transcript.strip(), stream_state.full_translation.strip(), status, tts_audio_path


def reset_stream_state():
    """重置串流狀態"""
    global stream_state
    stream_state = StreamState()
    return "", "", "已重置，準備開始錄音", None


def swap_languages(source: str, target: str):
    """交換來源與目標語言"""
    return target, source


# ============ 建立介面 ============
def create_ui():
    """建立 Gradio 介面"""
    
    language_choices = get_dropdown_choices()
    
    with gr.Blocks(
        title=TITLE,
    ) as demo:
        
        gr.Markdown(f"# {TITLE}")
        gr.Markdown(DESCRIPTION)
        
        with gr.Tabs():
            # ========== 文字翻譯分頁 ==========
            with gr.TabItem("📝 文字翻譯"):
                with gr.Row():
                    source_lang = gr.Dropdown(
                        choices=language_choices,
                        value="en_US",
                        label="來源語言",
                        scale=2
                    )
                    
                    swap_btn = gr.Button("🔄", elem_classes="swap-btn", scale=0)
                    
                    target_lang = gr.Dropdown(
                        choices=language_choices,
                        value="zh_TW",
                        label="目標語言",
                        scale=2
                    )
                
                with gr.Row():
                    input_text = gr.Textbox(
                        label="輸入文字",
                        placeholder="請輸入要翻譯的文字...",
                        lines=8,
                        scale=1
                    )
                    
                    output_text = gr.Textbox(
                        label="翻譯結果",
                        lines=8,
                        scale=1,
                        interactive=False
                    )
                
                translate_btn = gr.Button("🚀 翻譯", variant="primary", size="lg")
                
                # 綁定事件
                translate_btn.click(
                    fn=translate_text,
                    inputs=[input_text, source_lang, target_lang],
                    outputs=output_text
                )
                
                swap_btn.click(
                    fn=swap_languages,
                    inputs=[source_lang, target_lang],
                    outputs=[source_lang, target_lang]
                )
                
                # Enter 鍵翻譯
                input_text.submit(
                    fn=translate_text,
                    inputs=[input_text, source_lang, target_lang],
                    outputs=output_text
                )
            
            # ========== 圖片翻譯分頁 ==========
            with gr.TabItem("🖼️ 圖片翻譯"):
                gr.Markdown("### 上傳包含文字的圖片，使用 Tesseract OCR 識別並翻譯")
                
                with gr.Row():
                    image_input = gr.Image(
                        label="上傳圖片",
                        type="filepath",
                        scale=1
                    )
                    
                    image_output = gr.Textbox(
                        label="識別與翻譯結果",
                        lines=12,
                        scale=1,
                        interactive=False
                    )
                
                with gr.Row():
                    image_source_lang = gr.Dropdown(
                        choices=[("🔍 自動偵測", "auto")] + language_choices,
                        value="auto",
                        label="圖片文字語言"
                    )
                    
                    image_target_lang = gr.Dropdown(
                        choices=language_choices,
                        value="zh_TW",
                        label="翻譯目標語言"
                    )
                    
                    image_translate_btn = gr.Button("🔍 識別並翻譯", variant="primary")
                
                image_translate_btn.click(
                    fn=translate_image,
                    inputs=[image_input, image_source_lang, image_target_lang],
                    outputs=image_output
                )
            
            # ========== PDF 翻譯分頁 ==========
            with gr.TabItem("📄 PDF 翻譯"):
                gr.Markdown("### 上傳 PDF 文件，逐頁提取文字並翻譯")
                
                with gr.Row():
                    pdf_input = gr.File(
                        label="上傳 PDF",
                        file_types=[".pdf"],
                        type="filepath",
                        scale=1
                    )
                    
                    pdf_output = gr.Textbox(
                        label="翻譯結果",
                        lines=15,
                        scale=2,
                        interactive=False
                    )
                
                with gr.Row():
                    pdf_source_lang = gr.Dropdown(
                        choices=language_choices,
                        value="en_US",
                        label="PDF 文字語言"
                    )
                    
                    pdf_target_lang = gr.Dropdown(
                        choices=language_choices,
                        value="zh_TW",
                        label="翻譯目標語言"
                    )
                    
                    pdf_translate_btn = gr.Button("📄 翻譯 PDF", variant="primary")
                
                pdf_translate_btn.click(
                    fn=translate_pdf,
                    inputs=[pdf_input, pdf_source_lang, pdf_target_lang],
                    outputs=pdf_output
                )
                
                gr.Markdown("""
                > **💡 提示**：
                > - PDF 翻譯會逐頁處理，大型文件需較長時間
                > - 目前支援文字型 PDF，掃描版 PDF 可能無法正確提取文字
                > - 如需翻譯掃描版 PDF，請先將頁面轉為圖片後使用圖片翻譯功能
                """)
            
            # ========== 語音翻譯分頁 ==========
            with gr.TabItem("🎙️ 語音翻譯"):
                gr.Markdown("### 錄製語音或上傳音檔，自動辨識、翻譯並朗讀")
                
                with gr.Row():
                    voice_source_lang = gr.Dropdown(
                        choices=[("🔍 自動偵測", "auto")] + language_choices,
                        value="auto",
                        label="語音語言"
                    )
                    
                    voice_target_lang = gr.Dropdown(
                        choices=language_choices,
                        value="zh_TW",
                        label="翻譯目標語言"
                    )
                
                with gr.Row():
                    audio_input = gr.Audio(
                        sources=["microphone", "upload"],
                        type="filepath",
                        label="🎤 錄製或上傳語音"
                    )
                    
                    audio_output = gr.Audio(
                        label="🔊 翻譯語音輸出",
                        type="filepath",
                        interactive=False
                    )
                
                with gr.Row():
                    recognized_text = gr.Textbox(
                        label="📝 語音辨識結果",
                        lines=3,
                        interactive=False
                    )
                    
                    translated_text = gr.Textbox(
                        label="📖 翻譯結果",
                        lines=3,
                        interactive=False
                    )
                
                voice_translate_btn = gr.Button("🎙️ 翻譯語音", variant="primary", size="lg")
                
                voice_translate_btn.click(
                    fn=translate_voice,
                    inputs=[audio_input, voice_source_lang, voice_target_lang],
                    outputs=[recognized_text, translated_text, audio_output]
                )
                
                gr.Markdown("""
                > **💡 提示**：
                > - 首次使用時會下載語音辨識模型（約 150MB）
                > - 語音輸出使用 Microsoft Edge 神經網路語音
                > - 支援錄音或上傳 wav/mp3 等格式
                """)
            
            # ========== 即時翻譯分頁 ==========
            with gr.TabItem("⚡ 即時翻譯"):
                gr.Markdown("### 即時語音翻譯 - 邊說邊翻譯")
                
                with gr.Row():
                    stream_source_lang = gr.Dropdown(
                        choices=[("🔍 自動偵測", "auto")] + language_choices,
                        value="en_US",
                        label="語音語言"
                    )
                    
                    stream_target_lang = gr.Dropdown(
                        choices=language_choices,
                        value="zh_TW",
                        label="翻譯目標語言"
                    )
                
                with gr.Row():
                    silence_threshold_slider = gr.Slider(
                        minimum=0.01,
                        maximum=0.10,
                        value=0.02,
                        step=0.005,
                        label="🔇 靜音門檻值（環境較吵可調高）",
                        info="值越高：需要更安靜才判定為靜音"
                    )
                
                stream_status = gr.Textbox(
                    label="狀態",
                    value="準備開始錄音...",
                    interactive=False
                )
                
                stream_audio = gr.Audio(
                    sources=["microphone"],
                    streaming=True,
                    type="numpy",
                    label="🎤 即時錄音（持續說話）"
                )
                
                with gr.Row():
                    stream_transcript = gr.Textbox(
                        label="📝 即時語音辨識",
                        lines=6,
                        interactive=False
                    )
                    
                    stream_translation = gr.Textbox(
                        label="📖 即時翻譯結果",
                        lines=6,
                        interactive=False
                    )
                
                stream_tts_output = gr.Audio(
                    label="🔊 翻譯語音（自動播放）",
                    type="filepath",
                    autoplay=True,
                    interactive=False
                )
                
                reset_btn = gr.Button("🔄 重置", variant="secondary")
                
                # 串流處理
                stream_audio.stream(
                    fn=process_stream_chunk,
                    inputs=[stream_audio, stream_source_lang, stream_target_lang, silence_threshold_slider],
                    outputs=[stream_transcript, stream_translation, stream_status, stream_tts_output]
                )
                
                reset_btn.click(
                    fn=reset_stream_state,
                    outputs=[stream_transcript, stream_translation, stream_status, stream_tts_output]
                )
                
                gr.Markdown("""
                > **⚠️ 注意事項**：
                > - 會有 2-3 秒延遲（等待段落結束才處理）
                > - 說完一段話後稍作停頓，系統會自動辨識
                > - 點擊「重置」清空所有內容重新開始
                """)
            
            # ========== 影片翻譯分頁 ==========
            with gr.TabItem("🎥 影片翻譯"):
                gr.Markdown("### 影片翻譯與配音 - 自動生成翻譯字幕與配音")
                
                with gr.Row():
                    video_url_input = gr.Textbox(
                        label="YouTube 網址",
                        placeholder="https://www.youtube.com/watch?v=...",
                        lines=1
                    )
                
                with gr.Row():
                    video_upload = gr.Video(
                        label="或上傳影片檔案",
                        sources=["upload"]
                    )
                
                with gr.Row():
                    video_source_lang = gr.Dropdown(
                        choices=[("🔍 自動偵測", "auto")] + language_choices,
                        value="auto",
                        label="影片語言"
                    )
                    video_target_lang = gr.Dropdown(
                        choices=language_choices,
                        value="zh_TW",
                        label="翻譯目標語言",
                        multiselect=True,
                        max_choices=5,
                        info="可選擇多個語言（最多5個）進行批次處理"
                    )
                
                with gr.Row():
                    burn_subtitles_checkbox = gr.Checkbox(
                        label="🔤 燒錄字幕到影片",
                        value=True,
                        info="將翻譯字幕直接嵌入影片畫面"
                    )
                
                video_process_btn = gr.Button("🚀 開始處理", variant="primary")
                
                video_status = gr.Textbox(
                    label="處理狀態",
                    value="等待開始...",
                    interactive=False
                )
                
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("#### 原始影片")
                        original_video_output = gr.Video(label="原始影片預覽")
                        original_srt_output = gr.File(label="📄 原始字幕 (SRT)")
                    
                    with gr.Column():
                        gr.Markdown("#### 配音版影片")
                        dubbed_video_output = gr.Video(label="配音影片預覽")
                        translated_srt_output = gr.File(label="📄 翻譯字幕 (SRT)")
                
                def handle_video_process(url, uploaded, src_lang, tgt_langs, burn_subs, progress=gr.Progress()):
                    source = url if url else uploaded
                    return process_video_translation(source, src_lang, tgt_langs, burn_subs, progress)
                
                video_process_btn.click(
                    fn=handle_video_process,
                    inputs=[video_url_input, video_upload, video_source_lang, video_target_lang, burn_subtitles_checkbox],
                    outputs=[original_video_output, dubbed_video_output, original_srt_output, translated_srt_output, video_status]
                )
                
                gr.Markdown("""
                > **⚠️ 注意事項**：
                > - 影片處理需要較長時間（下載、辨識、翻譯、合成）
                > - 建議先測試短影片（5 分鐘內）
                > - 需要系統已安裝 ffmpeg
                """)
            
            # ========== 關於分頁 ==========
            with gr.TabItem("ℹ️ 關於"):
                gr.Markdown("""
                ## 關於 TranslateGemma
                
                TranslateGemma 是 Google 基於 Gemma 3 模型微調的專業翻譯模型。
                
                ### 技術特點
                - 🔧 基於 Gemma 3 架構，經過 SFT + RL 微調
                - 📊 在 MetricX 和 COMET22 評測中表現優異
                - 🌍 支援 55 種語言互譯
                - 🖼️ 支援圖片文字識別與翻譯
                
                ### 本機模型
                - 模型名稱：`translategemma`
                - 執行方式：Ollama
                - 參數規模：4.3B (Q4_K_M 量化)
                
                ### 支援語言
                繁體中文、簡體中文、英文、日文、韓文、德文、法文、西班牙文、
                義大利文、俄文、葡萄牙文、越南文、泰文、印尼文、阿拉伯文...等 55 種語言
                """)
        
        gr.Markdown("---")
        gr.Markdown("💡 **提示**：翻譯較長文字時請耐心等待，模型需要時間處理。")
    
    return demo


# ============ 主程式 ============
if __name__ == "__main__":
    demo = create_ui()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )
