"""
TranslateGemma 蝬脤?隞
========================
雿輻 Gradio 撱箇????蝧餉陌隞

???孵?嚗?
    python app.py

?嚗?
    1. 憭?閮??蝧餉陌
    2. ?? OCR 蝧餉陌
    3. 55 蝔株?閮?舀
"""

import gradio as gr
from translator import translator
from languages import LANGUAGES, COMMON_LANGUAGES, get_language_info

# ============ 隞撣豢 ============
TITLE = "TranslateGemma 多語翻譯助手"
DESCRIPTION = """
支援文字、圖片、PDF、語音、即時串流、影片翻譯與會議摘要。

**功能特色：**
- 文字翻譯（55+ 語言）
- 圖片 OCR 與翻譯
- PDF 逐頁翻譯
- 語音辨識與翻譯（含 TTS）
"""


def get_dropdown_choices():
    """取得語言下拉選單（常用語言優先）"""
    choices = []
    
    # 撣貊隤?
    for code in COMMON_LANGUAGES:
        if code in LANGUAGES:
            ch_name, en_name, locale = LANGUAGES[code]
            choices.append((f"潃?{ch_name} ({en_name})", code))
    
    # ?嗡?隤?
    other_langs = [(code, info) for code, info in LANGUAGES.items() 
                   if code not in COMMON_LANGUAGES]
    other_langs.sort(key=lambda x: x[1][0])
    
    for code, (ch_name, en_name, locale) in other_langs:
        choices.append((f"{ch_name} ({en_name})", code))
    
    return choices


# ========== 甇瑕閮?蝞∠? ==========
from history import history_manager

def translate_text(text: str, source_lang: str, target_lang: str, glossary_text: str = "", style_guide: str = ""):
    """??蝧餉陌嚗葡瘚?"""
    if not text.strip():
        yield "請先輸入要翻譯的文字。"
        return
    
    src_info = get_language_info(source_lang)
    tgt_info = get_language_info(target_lang)
    
    yield f"翻譯中...（{src_info[0]} -> {tgt_info[0]}）\n"
    
    full_translation = ""
    for result in translator.translate_stream(
        text,
        source_lang,
        target_lang,
        glossary=glossary_text,
        style=style_guide,
    ):
        full_translation = result
        yield result
        
    # 撖怠甇瑕閮?
    history_manager.add_history(
        type="text",
        source_lang=source_lang,
        target_lang=target_lang,
        original_content=text,
        translated_content=full_translation,
        details={
            "glossary_applied": bool(glossary_text.strip()) if glossary_text else False,
            "style_applied": bool(style_guide.strip()) if style_guide else False,
        },
    )


def translate_image(image, source_lang: str, target_lang: str):
    """Translate text from image via OCR and model translation."""
    if image is None:
        yield "請先上傳圖片。"
        return
    
    full_result = ""
    original_text = "Image Translation"
    
    for result in translator.translate_image(image, target_lang, source_lang):
        full_result = result
        yield result
        
    # 撖怠甇瑕閮?
    # ?ㄐ?瘜?????憪????隞亙?璅酉
    # 憒??喳???嚗?撠?????output ?桅?銝西??楝敺?
    history_manager.add_history(
        type="image",
        source_lang=source_lang,
        target_lang=target_lang,
        original_content="[Image Upload]",
        translated_content=full_result,
        details={"result_length": len(full_result)}
    )


def translate_pdf(pdf_file, source_lang: str, target_lang: str):
    """PDF ?辣蝧餉陌"""
    if pdf_file is None:
        yield "請先上傳 PDF 檔案。"
        return
    
    full_result = ""
    for result in translator.translate_pdf(pdf_file, target_lang, source_lang):
        full_result = result
        yield result
        
    # 撖怠甇瑕閮?
    history_manager.add_history(
        type="pdf",
        source_lang=source_lang,
        target_lang=target_lang,
        original_content=pdf_file if isinstance(pdf_file, str) else "[PDF File]",
        translated_content=full_result,
        details={"pdf_processed": True}
    )


import asyncio

def translate_voice(audio, source_lang: str, target_lang: str):
    """Speech translation pipeline: STT -> translate -> TTS."""
    if audio is None:
        return "請先提供語音輸入。", "", None
    
    # 1. 隤颲刻? (STT)
    recognized_text, detected_lang = translator.speech_to_text(audio, source_lang)
    
    if recognized_text.startswith("??"):
        return recognized_text, "", None
    
    if not recognized_text:
        return "未辨識到可用語音內容。", "", None
    
    # 2. 蝧餉陌??
    translated_text = translator.translate(recognized_text, source_lang, target_lang)
    
    # 3. ??頧???(TTS)
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        audio_path = loop.run_until_complete(translator.text_to_speech(translated_text, target_lang))
        loop.close()
    except Exception as e:
        audio_path = None
        print(f"TTS ?航炊: {e}")
    
    # 撖怠甇瑕閮?
    history_manager.add_history(
        type="voice",
        source_lang=source_lang,
        target_lang=target_lang,
        original_content=recognized_text,
        translated_content=translated_text,
        details={"audio_path": audio_path if audio_path else ""}
    )
    
    return recognized_text, translated_text, audio_path


# ========== 敶梁?蝧餉陌? ==========
from video_dubber import VideoDubber

# ========== ?降??? ==========
from meeting_summarizer import MeetingSummarizer, SUMMARY_TYPES

# ?典?敶梁?????
video_dubber_instance = None

def process_video_translation(video_source, source_lang: str, target_langs, 
                               burn_subtitles: bool = False, progress=gr.Progress()):
    """Process video translation/dubbing for one or more target languages."""
    global video_dubber_instance
    
    if not video_source:
        return None, None, None, None, "請提供 YouTube URL 或本地影片檔案。"
    
    # ??憭?閮
    if isinstance(target_langs, list):
        langs_list = target_langs if target_langs else ["zh_TW"]
    else:
        langs_list = [target_langs]
    
    # 撱箇??啁?????(?桐?璅∪?嚗??銴??交芋??
    if video_dubber_instance is None:
        # 雿輻撠?銝? temp ?桅?
        project_temp = os.path.join(os.getcwd(), "temp")
        os.makedirs(project_temp, exist_ok=True)
        video_dubber_instance = VideoDubber(output_dir=project_temp)
    
    def update_progress(msg):
        progress(0.5, desc=msg)
    
    try:
        # ?斗靘?憿?
        if isinstance(video_source, str) and video_source.startswith('http'):
            source = video_source
        else:
            source = video_source  # 瑼?頝臬?
        
        if len(langs_list) == 1:
            # ?桐?隤?嚗蝙?典??祉??寞?
            results = video_dubber_instance.process_video(
                source, source_lang, langs_list[0], 
                burn_subtitles=burn_subtitles,
                progress_callback=update_progress
            )
            
            # 撖怠甇瑕閮?
            history_manager.add_history(
                type="video",
                source_lang=source_lang,
                target_lang=langs_list[0],
                original_content=source,
                translated_content=results.get('dubbed_video', ''),
                details={
                    "original_srt": results.get('original_srt'),
                    "translated_srt": results.get('translated_srt')
                }
            )
            
            return (
                results.get('original_video'),
                results.get('dubbed_video'),
                results.get('original_srt'),
                results.get('translated_srt'),
                "影片翻譯處理完成。",
                None  # ?株?閮銝?閬甈⊥?獢?銵?
            )
        else:
            # 憭?閮嚗蝙?冽甈∟???
            batch_results = video_dubber_instance.process_video_batch(
                source, source_lang, langs_list,
                burn_subtitles=burn_subtitles,
                progress_callback=update_progress
            )
            
            # 撖怠甇瑕閮? (?寞活)
            for lang, result in batch_results['languages'].items():
                history_manager.add_history(
                    type="video_batch",
                    source_lang=source_lang,
                    target_lang=lang,
                    original_content=source,
                    translated_content=result.get('dubbed_video', ''),
                    details={
                        "original_srt": batch_results.get('original_srt'),
                        "translated_srt": result.get('translated_srt'),
                        "batch_id": str(id(batch_results)) # 蝪∪璅????寞活
                    }
                )
            
            # 餈?蝚砌???閮????汗
            first_lang = langs_list[0]
            first_result = batch_results['languages'].get(first_lang, {})
            
            # ?園???甈⊥?獢?
            all_batch_files = []
            status_msg = f"???寞活??摰?嚗?? {len(langs_list)} 蝔株?閮:\n\n"
            
            for lang in langs_list:
                lang_res = batch_results['languages'].get(lang, {})
                status_msg += f"?? {lang}:\n"
                if lang_res.get('dubbed_video'):
                    all_batch_files.append(lang_res['dubbed_video'])
                    status_msg += f"   ? 敶梁?: {lang_res['dubbed_video']}\n"
                if lang_res.get('translated_srt'):
                    all_batch_files.append(lang_res['translated_srt'])
                    status_msg += f"   ?? 摮?: {lang_res['translated_srt']}\n"
                status_msg += "\n"
            
            # 銋??亙?憪?撟?
            if batch_results.get('original_srt'):
                all_batch_files.insert(0, batch_results['original_srt'])
            
            return (
                batch_results.get('original_video'),
                first_result.get('dubbed_video'),
                batch_results.get('original_srt'),
                first_result.get('translated_srt'),
                status_msg,
                all_batch_files  # ?啣?嚗??甈⊥?獢?銵?
            )
    except Exception as e:
        return None, None, None, None, f"???航炊: {str(e)}", None


import numpy as np
import tempfile
import wave
import os

# 銝脫?蝧餉陌?????
class StreamState:
    def __init__(self):
        self.audio_buffer = []
        self.sample_rate = 16000
        self.silence_threshold = 0.02  # ???瑼餃潘?????摨佗?
        self.min_audio_length = 3.0    # ?撠敞蝛?3 蝘?? 1 蝘?
        self.max_audio_length = 15.0   # ?憭敞蝛?15 蝘?? 10 蝘?
        self.silence_count = 0         # ????閮
        self.silence_chunks_needed = 3 # ?閬?? 3 ???喟?畾菜??文??箸挾?賜???
        self.last_transcript = ""
        self.full_transcript = ""
        self.full_translation = ""

stream_state = StreamState()


def is_silence(audio_chunk: np.ndarray, threshold: float = 0.02) -> bool:
    """Detect silence using RMS threshold."""
    if audio_chunk is None or len(audio_chunk) == 0:
        return True
    rms = np.sqrt(np.mean(audio_chunk.astype(float) ** 2))
    return rms < threshold * 32768  # 16-bit audio


def save_audio_buffer(audio_data: np.ndarray, sample_rate: int) -> str:
    """撠閮楨銵摮?冽? WAV 瑼?"""
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, f"stream_audio_{id(audio_data)}.wav")
    
    with wave.open(temp_path, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(audio_data.astype(np.int16).tobytes())
    
    return temp_path


def process_stream_chunk(audio_chunk, source_lang: str, target_lang: str, silence_threshold: float = 0.02):
    """??銝脫??唾??挾"""
    global stream_state
    
    # ?湔??瑼餃?
    stream_state.silence_threshold = silence_threshold
    
    if audio_chunk is None:
        return stream_state.full_transcript, stream_state.full_translation, "蝑?隤頛詨...", None
    
    sample_rate, audio_data = audio_chunk
    
    # 頧??箏?脤?
    if len(audio_data.shape) > 1:
        audio_data = audio_data.mean(axis=1)
    
    # 蝝舐??唾?
    stream_state.audio_buffer.append(audio_data)
    stream_state.sample_rate = sample_rate
    
    # 閮?蝝舐??瑕漲
    total_samples = sum(len(chunk) for chunk in stream_state.audio_buffer)
    audio_length = total_samples / sample_rate
    
    # ?寥脩???菜葫嚗?閬??憭??喟?畾?
    is_silent = is_silence(audio_data, stream_state.silence_threshold)
    
    if is_silent:
        stream_state.silence_count += 1
    else:
        stream_state.silence_count = 0  # ?蔭閮
    
    # ?斗?臬?府??
    continuous_silence = stream_state.silence_count >= stream_state.silence_chunks_needed
    should_process = (
        (continuous_silence and audio_length >= stream_state.min_audio_length) or
        (audio_length >= stream_state.max_audio_length)
    )
    
    if not should_process:
        silence_indicator = "??" if is_silent else "??"
        status = f"? ?銝?.. ({audio_length:.1f}s) {silence_indicator}"
        return stream_state.full_transcript, stream_state.full_translation, status, None
    
    # ?蔥銝西??閮?
    full_audio = np.concatenate(stream_state.audio_buffer)
    stream_state.audio_buffer = []  # 皜征蝺抵?
    stream_state.silence_count = 0  # ?蔭?閮
    
    # ?脣??箄??獢?
    temp_path = save_audio_buffer(full_audio, sample_rate)
    
    tts_audio_path = None
    
    try:
        # STT
        recognized, detected_lang = translator.speech_to_text(temp_path, source_lang)
        
        if recognized and not recognized.startswith("??"):
            stream_state.full_transcript += recognized + " "
            
            # 蝧餉陌
            translated = translator.translate(recognized, source_lang, target_lang)
            stream_state.full_translation += translated + " "
            
            # TTS - ??蝧餉陌隤
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                tts_audio_path = loop.run_until_complete(translator.text_to_speech(translated, target_lang))
                loop.close()
            except Exception as e:
                print(f"TTS ?航炊: {e}")
        
        # 皜??冽?瑼?
        os.remove(temp_path)
        
    except Exception as e:
        print(f"銝脫????航炊: {e}")
    
    status = "已完成本段即時翻譯，請繼續說話..."
    return stream_state.full_transcript.strip(), stream_state.full_translation.strip(), status, tts_audio_path


def reset_stream_state():
    """Reset streaming state."""
    global stream_state
    stream_state = StreamState()
    return "", "", "已重設即時翻譯狀態。", None


def swap_languages(source: str, target: str):
    """鈭斗?靘??璅?閮"""
    return target, source


# ============ 甇瑕閮?隞 ============
def create_history_tab():
    with gr.TabItem("歷史紀錄"):
        with gr.Row():
            refresh_btn = gr.Button("重新整理", size="sm")
            clear_btn = gr.Button("清空全部", size="sm", variant="stop")
            filter_type = gr.Dropdown(
                choices=["All", "text", "image", "pdf", "voice", "video", "video_batch"],
                value="All",
                label="類型篩選"
            )
        
        history_table = gr.Dataframe(
            headers=["ID", "類型", "時間", "來源語言", "目標語言", "原文", "譯文"],
            datatype=["number", "str", "str", "str", "str", "str", "str"],
            interactive=False,
            wrap=True
        )
        
        def get_history_data(filter_val):
            type_filter = filter_val if filter_val != "All" else None
            records = history_manager.get_history(limit=50, type_filter=type_filter)
            data = []
            for r in records:
                # 蝪∪??批捆憿舐內
                orig = r["original_content"]
                if len(orig) > 50: orig = orig[:47] + "..."
                trans = r["translated_content"]
                if len(trans) > 50: trans = trans[:47] + "..."
                
                data.append([
                    r["id"],
                    r["timestamp"].replace("T", " ")[:19],
                    r["type"],
                    r["source_lang"],
                    r["target_lang"],
                    orig,
                    trans
                ])
            return data
            
        def clear_all_history():
            history_manager.clear_history()
            return get_history_data("All")

        refresh_btn.click(get_history_data, inputs=[filter_type], outputs=[history_table])
        filter_type.change(get_history_data, inputs=[filter_type], outputs=[history_table])
        clear_btn.click(clear_all_history, outputs=[history_table])
        
        # ????
        # 瘜冽?: ?ㄐ銝?湔隤輻 click 閫貊嚗??箔??ａ?瘝?render 摰?
        # ?臭誑??load 鈭辣嚗? Gradio TabItem 瘝? load??
        # ?? refresh ????Dataframe 蝬?嚗蝙?刻????湔??
        # ? create_ui ?敺孛?潔?甈～?


# ============ 撱箇?隞 ============
def create_ui():
    """撱箇? Gradio 隞"""
    
    language_choices = get_dropdown_choices()
    
    with gr.Blocks(
        title=TITLE,
    ) as demo:
        
        gr.Markdown(f"# {TITLE}")
        gr.Markdown(DESCRIPTION)
        
        with gr.Tabs():
            # ========== ??蝧餉陌?? ==========
            with gr.TabItem("文字翻譯"):
                with gr.Row():
                    source_lang = gr.Dropdown(
                        choices=language_choices,
                        value="en_US",
                        label="來源語言",
                        scale=2
                    )
                    
                    swap_btn = gr.Button("交換", elem_classes="swap-btn", scale=0)
                    
                    target_lang = gr.Dropdown(
                        choices=language_choices,
                        value="zh_TW",
                        label="目標語言",
                        scale=2
                    )
                
                with gr.Row():
                    input_text = gr.Textbox(
                        label="輸入文字",
                        placeholder="請輸入要翻譯的內容...",
                        lines=8,
                        scale=1
                    )
                    
                    output_text = gr.Textbox(
                        label="翻譯結果",
                        lines=8,
                        scale=1,
                        interactive=False
                    )
                with gr.Accordion("進階翻譯設定（術語表 / 風格）", open=False):
                    glossary_text = gr.Textbox(
                        label="術語表（每行一條，格式: source => target）",
                        placeholder="AI => 人工智慧\nLLM => 大型語言模型",
                        lines=4
                    )
                    style_guide = gr.Textbox(
                        label="翻譯風格指南",
                        placeholder="例：正式、簡潔、保留專有名詞英文括註",
                        lines=3
                    )

                
                translate_btn = gr.Button("開始翻譯", variant="primary", size="lg")
                
                # 蝬?鈭辣
                translate_btn.click(
                    fn=translate_text,
                    inputs=[input_text, source_lang, target_lang, glossary_text, style_guide],
                    outputs=output_text
                )
                
                swap_btn.click(
                    fn=swap_languages,
                    inputs=[source_lang, target_lang],
                    outputs=[source_lang, target_lang]
                )
                
                # Enter ?萇蕃霅?
                input_text.submit(
                    fn=translate_text,
                    inputs=[input_text, source_lang, target_lang, glossary_text, style_guide],
                    outputs=output_text
                )
            
            # ========== ??蝧餉陌?? ==========
            with gr.TabItem("圖片翻譯"):
                gr.Markdown("### 上傳圖片後，使用 Tesseract OCR 進行辨識與翻譯")
                
                with gr.Row():
                    image_input = gr.Image(
                        label="上傳圖片",
                        type="filepath",
                        scale=1
                    )
                    
                    image_output = gr.Textbox(
                        label="辨識與翻譯結果",
                        lines=12,
                        scale=1,
                        interactive=False
                    )
                
                with gr.Row():
                    image_source_lang = gr.Dropdown(
                        choices=[("自動偵測", "auto")] + language_choices,
                        value="auto",
                        label="來源語言"
                    )
                    
                    image_target_lang = gr.Dropdown(
                        choices=language_choices,
                        value="zh_TW",
                        label="目標語言"
                    )
                    
                    image_translate_btn = gr.Button("OCR 並翻譯", variant="primary")
                
                image_translate_btn.click(
                    fn=translate_image,
                    inputs=[image_input, image_source_lang, image_target_lang],
                    outputs=image_output
                )
            
            # ========== PDF 蝧餉陌?? ==========
            with gr.TabItem("PDF 翻譯"):
                gr.Markdown("### 上傳 PDF 文件後，可逐頁翻譯內容")
                
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
                        label="PDF 來源語言"
                    )
                    
                    pdf_target_lang = gr.Dropdown(
                        choices=language_choices,
                        value="zh_TW",
                        label="目標語言"
                    )
                    
                    pdf_translate_btn = gr.Button("翻譯 PDF", variant="primary")
                
                pdf_translate_btn.click(
                    fn=translate_pdf,
                    inputs=[pdf_input, pdf_source_lang, pdf_target_lang],
                    outputs=pdf_output
                )
                
                gr.Markdown("""
                > **提示：**
                > - PDF 翻譯採逐頁處理，文件越大耗時越長。
                > - 建議先測試 1-2 頁，確認品質後再翻完整文件。
                > - 若為掃描 PDF，先確保 OCR 可讀性。
                """)
            
            # ========== 隤蝧餉陌?? ==========
            with gr.TabItem("語音翻譯"):
                gr.Markdown("### 錄音或上傳音檔，系統會先辨識再翻譯")
                
                with gr.Row():
                    voice_source_lang = gr.Dropdown(
                        choices=[("自動偵測", "auto")] + language_choices,
                        value="auto",
                        label="來源語言"
                    )
                    
                    voice_target_lang = gr.Dropdown(
                        choices=language_choices,
                        value="zh_TW",
                        label="目標語言"
                    )
                
                with gr.Row():
                    audio_input = gr.Audio(
                        sources=["microphone", "upload"],
                        type="filepath",
                        label="語音輸入（錄音或上傳）"
                    )
                    
                    audio_output = gr.Audio(
                        label="語音輸出（TTS）",
                        type="filepath",
                        interactive=False
                    )
                
                with gr.Row():
                    recognized_text = gr.Textbox(
                        label="語音辨識文字",
                        lines=3,
                        interactive=False
                    )
                    
                    translated_text = gr.Textbox(
                        label="翻譯文字",
                        lines=3,
                        interactive=False
                    )
                
                voice_translate_btn = gr.Button("語音翻譯", variant="primary", size="lg")
                
                voice_translate_btn.click(
                    fn=translate_voice,
                    inputs=[audio_input, voice_source_lang, voice_target_lang],
                    outputs=[recognized_text, translated_text, audio_output]
                )
                
                gr.Markdown("""
                > **提示：**
                > - 建議音檔小於 150MB。
                > - TTS 使用 Edge 語音服務。
                > - 支援常見 wav/mp3。
                """)
            
            # ========== ?單?蝧餉陌?? ==========
            with gr.TabItem("即時語音翻譯"):
                gr.Markdown("### 即時語音翻譯 - 邊說邊翻")
                
                with gr.Row():
                    stream_source_lang = gr.Dropdown(
                        choices=[("自動偵測", "auto")] + language_choices,
                        value="en_US",
                        label="來源語言"
                    )
                    
                    stream_target_lang = gr.Dropdown(
                        choices=language_choices,
                        value="zh_TW",
                        label="目標語言"
                    )
                
                with gr.Row():
                    silence_threshold_slider = gr.Slider(
                        minimum=0.01,
                        maximum=0.10,
                        value=0.02,
                        step=0.005,
                        label="靜音判定閾值（越高越容易判定為靜音）",
                        info="可依環境噪音調整"
                    )
                
                stream_status = gr.Textbox(
                    label="即時狀態",
                    value="等待音訊輸入...",
                    interactive=False
                )
                
                stream_audio = gr.Audio(
                    sources=["microphone"],
                    streaming=True,
                    type="numpy",
                    label="即時語音輸入（麥克風）"
                )
                
                with gr.Row():
                    stream_transcript = gr.Textbox(
                        label="即時辨識文字",
                        lines=6,
                        interactive=False
                    )
                    
                    stream_translation = gr.Textbox(
                        label="即時翻譯文字",
                        lines=6,
                        interactive=False
                    )
                
                stream_tts_output = gr.Audio(
                    label="即時翻譯語音輸出",
                    type="filepath",
                    autoplay=True,
                    interactive=False
                )
                
                reset_btn = gr.Button("重設", variant="secondary")
                
                # 銝脫???
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
                > **使用建議：**
                > - 每段 2-3 秒語音有最佳效果。
                > - 背景噪音過高時，請提高靜音閾值。
                > - 網路或模型忙碌時可能延遲。
                """)
            
            # ========== 敶梁?蝧餉陌?? ==========
            with gr.TabItem("影片翻譯"):
                gr.Markdown("### 影片翻譯與配音 - 支援多語目標")
                
                with gr.Row():
                    video_url_input = gr.Textbox(
                        label="YouTube 連結",
                        placeholder="https://www.youtube.com/watch?v=...",
                        lines=1
                    )
                
                with gr.Row():
                    video_upload = gr.Video(
                        label="或上傳本地影片檔",
                        sources=["upload"]
                    )
                
                with gr.Row():
                    video_source_lang = gr.Dropdown(
                        choices=[("自動偵測", "auto")] + language_choices,
                        value="auto",
                        label="來源語言"
                    )
                    video_target_lang = gr.Dropdown(
                        choices=language_choices,
                        value="zh_TW",
                        label="目標語言（可多選）",
                        multiselect=True,
                        max_choices=5,
                        info="多選時會啟用批次處理"
                    )
                
                with gr.Row():
                    burn_subtitles_checkbox = gr.Checkbox(
                        label="產生並燒錄字幕",
                        value=True,
                        info="啟用後會把字幕直接嵌入影片"
                    )
                
                video_process_btn = gr.Button("開始處理", variant="primary")
                
                video_status = gr.Textbox(
                    label="處理狀態",
                    value="等待任務...",
                    interactive=False,
                    lines=8,
                    max_lines=15
                )
                
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("#### 原始輸出")
                        original_video_output = gr.Video(label="原始影片")
                        original_srt_output = gr.File(label="原始字幕 (SRT)")
                    
                    with gr.Column():
                        gr.Markdown("#### 配音結果")
                        # 隤????詨嚗甈∟????嚗?
                        preview_lang_selector = gr.Dropdown(
                            choices=[],
                            label="預覽語言",
                            visible=False,
                            interactive=True
                        )
                        dubbed_video_output = gr.Video(label="配音影片")
                        translated_srt_output = gr.File(label="翻譯字幕 (SRT)")
                
                # ?冽?脣??寞活蝯??????
                batch_results_state = gr.State(value=None)
                
                gr.Markdown("#### 批次輸出檔案")
                batch_files_output = gr.File(
                    label="批次輸出（可多檔下載）",
                    file_count="multiple"
                )
                
                def handle_video_process(url, uploaded, src_lang, tgt_langs, burn_subs, progress=gr.Progress()):
                    source = url if url else uploaded
                    result = process_video_translation(source, src_lang, tgt_langs, burn_subs, progress)
                    
                    # process_video_translation ?曉餈? 6 ??
                    batch_files = result[5] if len(result) > 5 else None
                    
                    # ?斗?臬?箸甈∟???
                    if isinstance(tgt_langs, list) and len(tgt_langs) > 1:
                        # ?寞活璅∪?嚗??刻?閮?豢???
                        lang_choices = tgt_langs
                        lang_visible = True
                        selected_lang = tgt_langs[0]
                        
                        # ?脣??寞活蝯?靘??蝙??
                        # 敺?batch_files ?遣蝯???
                        # 頝臬?蝯?: temp/batch_job_xxx/{lang}/dubbed_video.mp4
                        batch_data = {}
                        for f in (batch_files or []):
                            if f and isinstance(f, str):
                                # 璅??楝敺??泵
                                f_normalized = f.replace('\\', '/')
                                for lang in tgt_langs:
                                    # 瑼Ｘ頝臬?銝剜?血??怨?閮鞈?憭?/{lang}/
                                    if f'/{lang}/' in f_normalized:
                                        if lang not in batch_data:
                                            batch_data[lang] = {}
                                        if f.endswith('.mp4'):
                                            batch_data[lang]['video'] = f
                                        elif f.endswith('.srt'):
                                            batch_data[lang]['srt'] = f
                    else:
                        # ?桐?隤?璅∪?
                        lang_choices = []
                        lang_visible = False
                        selected_lang = None
                        batch_data = None
                    
                    return (
                        result[0],  # original_video
                        result[1],  # dubbed_video
                        result[2],  # original_srt
                        result[3],  # translated_srt
                        result[4],  # status
                        batch_files,  # batch_files
                        gr.update(choices=lang_choices, visible=lang_visible, value=selected_lang),  # 語言選單
                        batch_data  # ?寞活蝯????
                    )
                
                def switch_preview_language(selected_lang, batch_data):
                    """依語言切換預覽結果"""
                    if not batch_data or not selected_lang:
                        return None, None
                    
                    lang_data = batch_data.get(selected_lang, {})
                    return lang_data.get('video'), lang_data.get('srt')
                
                video_process_btn.click(
                    fn=handle_video_process,
                    inputs=[video_url_input, video_upload, video_source_lang, video_target_lang, burn_subtitles_checkbox],
                    outputs=[original_video_output, dubbed_video_output, original_srt_output, translated_srt_output, video_status, batch_files_output, preview_lang_selector, batch_results_state]
                )
                
                # 隤???鈭辣
                preview_lang_selector.change(
                    fn=switch_preview_language,
                    inputs=[preview_lang_selector, batch_results_state],
                    outputs=[dubbed_video_output, translated_srt_output]
                )
                
                gr.Markdown("""
                > **影片翻譯提示：**
                > - 影片長度與解析度會影響處理時間。
                > - 需要本機可用的 ffmpeg。
                > - 批次處理會輸出多個語言版本。
                > - ?寞活??憭?閮???????瑼????具甈∟撓?箸?獢???
                """)
            
            # ========== ?降???? ==========
            with gr.TabItem("會議摘要"):
                gr.Markdown("### 上傳會議影片，自動產生逐字稿與摘要")
                
                with gr.Row():
                    with gr.Column(scale=1):
                        meeting_video_upload = gr.Video(
                            label="上傳會議影片",
                            sources=["upload"]
                        )
                        
                        meeting_language = gr.Dropdown(
                            choices=[("自動偵測", "auto")] + language_choices,
                            value="auto",
                            label="會議語言"
                        )
                        
                        summary_type_selector = gr.CheckboxGroup(
                            choices=[
                                ("完整摘要", "full_summary"),
                                ("重點整理", "key_points"),
                                ("行動項目", "action_items"),
                                ("決策事項", "decisions")
                            ],
                            value=["full_summary"],
                            label="摘要輸出類型",
                        )
                        
                        with gr.Accordion("AI 設定", open=False):
                            ai_backend_selector = gr.Radio(
                                choices=[
                                    ("Ollama 本地模型", "ollama"),
                                    ("Gemini API", "gemini")
                                ],
                                value="ollama",
                                label="AI 後端"
                            )
                            
                            ollama_model_selector = gr.Dropdown(
                                choices=[
                                    ("qwen3:4b (敹恍?", "qwen3:4b"),
                                    ("ministral-3:8b (擃?鞈?", "ministral-3:8b"),
                                    ("qwen3-v1:8b (擃?鞈?", "qwen3-v1:8b")
                                ],
                                value="qwen3:4b",
                                label="Ollama 模型",
                                visible=True
                            )
                            
                            gemini_api_key_input = gr.Textbox(
                                label="Gemini API Key",
                                type="password",
                                placeholder="請輸入 Gemini API Key...",
                                visible=False
                            )
                        
                        meeting_process_btn = gr.Button("開始摘要", variant="primary", size="lg")
                    
                    with gr.Column(scale=2):
                        meeting_status = gr.Textbox(
                            label="處理狀態",
                            value="等待影片上傳...",
                            interactive=False,
                            lines=2
                        )
                        
                        meeting_progress = gr.Slider(
                            minimum=0,
                            maximum=100,
                            value=0,
                            label="處理進度",
                            interactive=False
                        )
                        
                        with gr.Tabs():
                            with gr.TabItem("逐字稿"):
                                transcript_output = gr.Textbox(
                                    label="逐字稿（可下載）",
                                    lines=15,
                                    interactive=False
                                )
                            
                            with gr.TabItem("摘要結果"):
                                summary_output = gr.Markdown(
                                    value="*尚無摘要內容*"
                                )
                        
                        with gr.Row():
                            download_transcript_btn = gr.Button("下載逐字稿", size="sm")
                            download_summary_btn = gr.Button("下載摘要", size="sm")
                        
                        transcript_file = gr.File(label="逐字稿檔案", visible=False)
                        summary_file = gr.File(label="摘要檔案", visible=False)
                
                # AI 敺垢??鈭辣
                def toggle_ai_settings(backend):
                    return (
                        gr.update(visible=(backend == "ollama")),
                        gr.update(visible=(backend == "gemini"))
                    )
                
                ai_backend_selector.change(
                    fn=toggle_ai_settings,
                    inputs=[ai_backend_selector],
                    outputs=[ollama_model_selector, gemini_api_key_input]
                )
                
                # ?降?????賣
                def process_meeting_summary(video, language, summary_types, 
                                            ai_backend, ollama_model, gemini_key,
                                            progress=gr.Progress()):
                    if video is None:
                        return "請先上傳會議影片", 0, "", "*請先上傳會議影片*"
                    
                    if not summary_types:
                        summary_types = ["full_summary"]
                    
                    # 撱箇?????
                    summarizer = MeetingSummarizer(
                        ai_backend=ai_backend,
                        ollama_model=ollama_model,
                        gemini_api_key=gemini_key
                    )
                    
                    # ???脣漲餈質馱
                    status_messages = []
                    current_progress = 0
                    transcript_text = ""
                    summary_md = ""
                    
                    try:
                        for update in summarizer.process_video_stream(
                            video, language, summary_types
                        ):
                            stage = update.get("stage", "")
                            prog = update.get("progress", 0) * 100
                            msg = update.get("message", "")
                            
                            status_messages.append(msg)
                            current_progress = prog
                            
                            # ?湔 Gradio ?脣漲
                            progress(prog / 100, desc=msg)
                            
                            # ????蝔?
                            if "transcript_with_time" in update:
                                transcript_text = update["transcript_with_time"]
                            
                            # ???典???
                            if "partial_summary" in update:
                                for stype, content in update["partial_summary"].items():
                                    type_name = SUMMARY_TYPES.get(stype, {}).get("name", stype)
                                    summary_md += f"\n\n## {type_name}\n\n{content}"
                            
                            # ?蝯?閬?
                            if stage == "done" and "summary" in update:
                                summary_md = ""
                                for stype, content in update["summary"].items():
                                    type_name = SUMMARY_TYPES.get(stype, {}).get("name", stype)
                                    summary_md += f"## {type_name}\n\n{content}\n\n---\n\n"
                        
                        final_status = "處理完成。"
                        
                    except Exception as e:
                        final_status = f"處理失敗：{str(e)}"
                        summary_md = f"*摘要產生失敗：{str(e)}*"
                    
                    return (
                        final_status,
                        current_progress,
                        transcript_text,
                        summary_md if summary_md else "*尚未產生摘要*"
                    )
                
                # 銝???蝔?
                def save_transcript(transcript_text):
                    if not transcript_text:
                        return None
                    import tempfile
                    temp_path = os.path.join(tempfile.gettempdir(), "meeting_transcript.txt")
                    with open(temp_path, "w", encoding="utf-8") as f:
                        f.write(transcript_text)
                    return temp_path
                
                # 銝???
                def save_summary(summary_md):
                    if not summary_md or summary_md.startswith("*"):
                        return None
                    import tempfile
                    temp_path = os.path.join(tempfile.gettempdir(), "meeting_summary.md")
                    with open(temp_path, "w", encoding="utf-8") as f:
                        f.write(summary_md)
                    return temp_path
                
                # 蝬?鈭辣
                meeting_process_btn.click(
                    fn=process_meeting_summary,
                    inputs=[
                        meeting_video_upload, meeting_language, summary_type_selector,
                        ai_backend_selector, ollama_model_selector, gemini_api_key_input
                    ],
                    outputs=[meeting_status, meeting_progress, transcript_output, summary_output]
                )
                
                download_transcript_btn.click(
                    fn=save_transcript,
                    inputs=[transcript_output],
                    outputs=[transcript_file]
                )
                
                download_summary_btn.click(
                    fn=save_summary,
                    inputs=[summary_output],
                    outputs=[summary_file]
                )
                
                gr.Markdown("""
                > **支援格式：**
                > - 影片：mp4, avi, mov, mkv, webm
                > - 可選擇多種摘要類型。
                > - AI 後端可選本地 Ollama 或 Gemini API。
                > - 建議先用短片測試流程。
                > - ?????捱?澆蔣?摨佗?隢?蝑?
                """)
            
            # ========== 甇瑕閮??? ==========
            create_history_tab()
            
            # ========== ??? ==========
            with gr.TabItem("關於"):
                gr.Markdown("""
                ## TranslateGemma
                
                TranslateGemma 是以 Gemma 系列模型為核心的多語翻譯工具。
                
                ### 特色
                - 支援文字、圖片、PDF、語音、影片翻譯
                - 支援即時語音翻譯與會議摘要
                - 可擴充多模型與工作流程
                - 支援 55+ 語言
                
                ### 模型與執行
                - 模型名稱：`translategemma`
                - 推論平台：Ollama
                - 建議先確認本機模型可正常回應
                
                ### 注意事項
                若遇到翻譯品質不穩定，可調整提示詞、術語表與風格設定。
                建議搭配小型回歸測試集持續驗證。
                """)
        
        gr.Markdown("---")
        gr.Markdown("**提示**：請先確認模型與外部工具安裝完成。")
    
    return demo


# ============ 銝餌?撘?============
if __name__ == "__main__":
    demo = create_ui()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )

