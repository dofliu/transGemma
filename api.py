from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import os
import shutil
import tempfile
from translator import translator
from video_dubber import video_dubber
from history import history_manager

import gradio as gr
from app import create_ui

# Ensure temp directory exists and configure video_dubber
project_temp = os.path.join(os.getcwd(), "temp")
os.makedirs(project_temp, exist_ok=True)
video_dubber.output_dir = project_temp
print(f"API configured video_dubber output_dir: {project_temp}")

app = FastAPI(
    title="TranslateGemma API",
    description="API for TranslateGemma Translation Service",
    version="1.0.0"
)

# Mount Gradio UI
# 注意: Gradio 會接管 "/" 路徑，所以 API 文件移至 "/docs"
app = gr.mount_gradio_app(app, create_ui(), path="/")

# Request Models
class TextTranslationRequest(BaseModel):
    text: str
    source_lang: str = "auto"
    target_lang: str = "zh_TW"

class VideoDubRequest(BaseModel):
    url: str
    source_lang: str = "auto"
    target_langs: List[str] = ["zh_TW"]
    burn_subtitles: bool = True

# --- Endpoints ---

# --- Endpoints ---

@app.post("/api/translate/text")
async def translate_text_endpoint(request: TextTranslationRequest):
    """Translate text"""
    try:
        # Use the streaming method but consume it all for JSON response
        # or use simple translate if available. translator.translate calls chat method.
        # Let's use translator.translate which returns full string
        if request.source_lang == "auto":
             # translator.translate assumes a source lang or handles it. 
             # Let's use "auto" if supported, or let translator handle it.
             # Actually translator.translate(text, source, target)
             pass

        result = translator.translate(request.text, request.source_lang, request.target_lang)
        
        # Log history
        history_manager.add_history(
            type="text",
            source_lang=request.source_lang,
            target_lang=request.target_lang,
            original_content=request.text,
            translated_content=result,
            details={"via": "api"}
        )
        
        return {"translated_text": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/translate/image")
async def translate_image_endpoint(
    file: UploadFile = File(...),
    source_lang: str = Form("auto"),
    target_lang: str = Form("zh_TW")
):
    """Translate text from image file"""
    try:
        # Save temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name
        
        # Translate
        # translator.translate_image generator needs to be consumed
        full_result = ""
        for chunk in translator.translate_image(tmp_path, target_lang, source_lang):
            full_result = chunk # accumulate or just take last update if it yields progress
            # Actually translate_image yields accumulated text? 
            # Check implementation. It yields accumulated text.
        
        os.unlink(tmp_path)
        
        # Log history
        history_manager.add_history(
            type="image",
            source_lang=source_lang,
            target_lang=target_lang,
            original_content=f"[API Upload] {file.filename}",
            translated_content=full_result,
            details={"via": "api"}
        )

        return {"translated_text": full_result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/dub/video")
async def dub_video_endpoint(request: VideoDubRequest):
    """
    Dub a YouTube video.
    Returns JSON with paths to generated files.
    Note: Processing is synchronous and slow. For production, use background tasks.
    """
    try:
        # Check if URL
        if not request.url.startswith("http"):
             raise HTTPException(status_code=400, detail="Only YouTube URLs supported in this endpoint for now")

        # Determine single or batch
        if len(request.target_langs) == 1:
            target_lang = request.target_langs[0]
            results = video_dubber.process_video(
                request.url, request.source_lang, target_lang,
                burn_subtitles=request.burn_subtitles
            )
            
            # Log history
            history_manager.add_history(
                type="video",
                source_lang=request.source_lang,
                target_lang=target_lang,
                original_content=request.url,
                translated_content=results.get('dubbed_video', ''),
                details={"via": "api", "original_srt": results.get("original_srt")}
            )
            
            return results
        else:
            # Batch
            results = video_dubber.process_video_batch(
                request.url, request.source_lang, request.target_langs,
                burn_subtitles=request.burn_subtitles
            )
            
            # Log history handled inside caller? No, process_video_batch doesn't log history.
            # We need to log it here repeatedly?
            # Or make a helper. For now let's log loop.
            for lang, res in results.get('languages', {}).items():
                 history_manager.add_history(
                    type="video_batch",
                    source_lang=request.source_lang,
                    target_lang=lang,
                    original_content=request.url,
                    translated_content=res.get('dubbed_video', ''),
                    details={"via": "api", "batch_id": str(id(results))}
                )

            return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
