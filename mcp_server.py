from mcp.server.fastmcp import FastMCP
import os
import sys

# Add current directory to path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from translator import translator
from video_dubber import video_dubber
from history import history_manager

# Initialize FastMCP Server
mcp = FastMCP("TranslateGemma")

@mcp.tool()
def translate_text(text: str, source_lang: str = "auto", target_lang: str = "zh_TW") -> str:
    """
    Translate text using TranslateGemma model.
    
    Args:
        text: Text to translate
        source_lang: Source language code (default: auto)
        target_lang: Target language code (default: zh_TW)
    """
    result = translator.translate(text, source_lang, target_lang)
    
    # Log to history
    history_manager.add_history(
        type="text",
        source_lang=source_lang,
        target_lang=target_lang,
        original_content=text,
        translated_content=result,
        details={"via": "mcp"}
    )
    
    return result

@mcp.tool()
def translate_image(image_path: str, source_lang: str = "auto", target_lang: str = "zh_TW") -> str:
    """
    Translate text from an image file using OCR.
    
    Args:
        image_path: Absolute path to the image file
        source_lang: Source language code
        target_lang: Target language code
    """
    if not os.path.exists(image_path):
        return f"Error: File {image_path} not found."
    
    full_result = ""
    # translate_image is a generator
    for chunk in translator.translate_image(image_path, target_lang, source_lang):
        full_result = chunk
        
    # Log to history
    history_manager.add_history(
        type="image",
        source_lang=source_lang,
        target_lang=target_lang,
        original_content=image_path,
        translated_content=full_result,
        details={"via": "mcp"}
    )
    
    return full_result

@mcp.tool()
def dub_video(video_source: str, source_lang: str = "auto", target_lang: str = "zh_TW", burn_subtitles: bool = True) -> str:
    """
    Dub a video (YouTube URL or local file path). 
    Generates translated audio, merges it with video, and optionally burns subtitles.
    
    Args:
        video_source: YouTube URL or local file path
        source_lang: Source language code
        target_lang: Target language code
        burn_subtitles: Whether to burn subtitles into video frames
    
    Returns:
        Path to the dubbed video file
    """
    # 呼叫單一影片處理
    results = video_dubber.process_video(
        video_source, 
        source_lang, 
        target_lang, 
        burn_subtitles=burn_subtitles
    )
    
    dubbed_path = results.get("dubbed_video", "")
    
    # Log to history
    history_manager.add_history(
        type="video",
        source_lang=source_lang,
        target_lang=target_lang,
        original_content=video_source,
        translated_content=dubbed_path,
        details={
            "via": "mcp", 
            "original_srt": results.get("original_srt"),
            "translated_srt": results.get("translated_srt")
        }
    )
    
    if not dubbed_path:
        return "Error: Failed to generate dubbed video."
        
    return dubbed_path

if __name__ == "__main__":
    mcp.run()
