from mcp.server.fastmcp import FastMCP
import os
import sys
from typing import List

# Add current directory to path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from translator import translator
from video_dubber import video_dubber
from history import history_manager
from languages import LANGUAGES

mcp = FastMCP("TranslateGemma")


@mcp.tool()
def list_languages() -> list[dict]:
    """List supported languages with code and locale."""
    rows = []
    for code, (ch_name, en_name, locale) in LANGUAGES.items():
        rows.append({"code": code, "name_zh": ch_name, "name_en": en_name, "locale": locale})
    rows.sort(key=lambda x: x["name_zh"])
    return rows


@mcp.tool()
def translate_text(text: str, source_lang: str = "auto", target_lang: str = "zh_TW") -> str:
    """Translate text using TranslateGemma model."""
    result = translator.translate(text, source_lang, target_lang)
    history_manager.add_history(
        type="text",
        source_lang=source_lang,
        target_lang=target_lang,
        original_content=text,
        translated_content=result,
        details={"via": "mcp"},
    )
    return result


@mcp.tool()
def translate_batch_text(texts: List[str], source_lang: str = "auto", target_lang: str = "zh_TW") -> List[str]:
    """Translate a batch of text items."""
    outputs = [translator.translate(t, source_lang, target_lang) for t in texts]
    history_manager.add_history(
        type="text_batch",
        source_lang=source_lang,
        target_lang=target_lang,
        original_content=f"[mcp-batch:{len(texts)}]",
        translated_content="\n".join(outputs[:3]),
        details={"via": "mcp", "count": len(texts)},
    )
    return outputs


@mcp.tool()
def translate_image(image_path: str, source_lang: str = "auto", target_lang: str = "zh_TW") -> str:
    """Translate text from an image file using OCR."""
    if not os.path.exists(image_path):
        return f"Error: File {image_path} not found."

    full_result = ""
    for chunk in translator.translate_image(image_path, target_lang, source_lang):
        full_result = chunk

    history_manager.add_history(
        type="image",
        source_lang=source_lang,
        target_lang=target_lang,
        original_content=image_path,
        translated_content=full_result,
        details={"via": "mcp"},
    )
    return full_result


@mcp.tool()
def translate_pdf(pdf_path: str, source_lang: str = "en_US", target_lang: str = "zh_TW") -> str:
    """Translate text extracted from PDF pages."""
    if not os.path.exists(pdf_path):
        return f"Error: File {pdf_path} not found."

    final_result = ""
    for chunk in translator.translate_pdf(pdf_path, target_lang, source_lang):
        final_result = chunk

    history_manager.add_history(
        type="pdf",
        source_lang=source_lang,
        target_lang=target_lang,
        original_content=pdf_path,
        translated_content=final_result,
        details={"via": "mcp"},
    )
    return final_result


@mcp.tool()
def dub_video(video_source: str, source_lang: str = "auto", target_lang: str = "zh_TW", burn_subtitles: bool = True) -> str:
    """Dub a video and return output path."""
    results = video_dubber.process_video(
        video_source,
        source_lang,
        target_lang,
        burn_subtitles=burn_subtitles,
    )

    dubbed_path = results.get("dubbed_video", "")
    history_manager.add_history(
        type="video",
        source_lang=source_lang,
        target_lang=target_lang,
        original_content=video_source,
        translated_content=dubbed_path,
        details={
            "via": "mcp",
            "original_srt": results.get("original_srt"),
            "translated_srt": results.get("translated_srt"),
        },
    )

    if not dubbed_path:
        return "Error: Failed to generate dubbed video."

    return dubbed_path


if __name__ == "__main__":
    mcp.run()
