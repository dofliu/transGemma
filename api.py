from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any
import os
import shutil
import tempfile
import uuid
from datetime import datetime

from translator import translator
from video_dubber import video_dubber
from history import history_manager
from languages import LANGUAGES
from meeting_summarizer import MeetingSummarizer

import gradio as gr
from app import create_ui


project_temp = os.path.join(os.getcwd(), "temp")
os.makedirs(project_temp, exist_ok=True)
video_dubber.output_dir = project_temp
print(f"API configured video_dubber output_dir: {project_temp}")

app = FastAPI(
    title="TranslateGemma API",
    description="API for TranslateGemma Translation Service",
    version="1.1.0",
)

# Mount Gradio UI
app = gr.mount_gradio_app(app, create_ui(), path="/")


class TextTranslationRequest(BaseModel):
    text: str
    source_lang: str = "auto"
    target_lang: str = "zh_TW"


class BatchTextTranslationRequest(BaseModel):
    items: List[str]
    source_lang: str = "auto"
    target_lang: str = "zh_TW"
    glossary: str = ""
    style: str = ""


class VideoDubRequest(BaseModel):
    url: str
    source_lang: str = "auto"
    target_langs: List[str] = ["zh_TW"]
    burn_subtitles: bool = True


class JobVideoRequest(BaseModel):
    url: str
    source_lang: str = "auto"
    target_langs: List[str] = ["zh_TW"]
    burn_subtitles: bool = True


JOBS: Dict[str, Dict[str, Any]] = {}


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _create_job(job_type: str, payload: Dict[str, Any]) -> str:
    job_id = str(uuid.uuid4())
    JOBS[job_id] = {
        "job_id": job_id,
        "type": job_type,
        "status": "queued",
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
        "payload": payload,
        "result": None,
        "error": "",
        "retry_count": 0,
    }
    return job_id


def _set_job_running(job_id: str) -> None:
    if job_id in JOBS:
        JOBS[job_id]["status"] = "running"
        JOBS[job_id]["updated_at"] = _now_iso()


def _set_job_done(job_id: str, result: Dict[str, Any]) -> None:
    if job_id in JOBS:
        JOBS[job_id]["status"] = "done"
        JOBS[job_id]["result"] = result
        JOBS[job_id]["updated_at"] = _now_iso()


def _set_job_failed(job_id: str, error: str) -> None:
    if job_id in JOBS:
        JOBS[job_id]["status"] = "failed"
        JOBS[job_id]["error"] = error
        JOBS[job_id]["updated_at"] = _now_iso()


def _language_payload() -> List[Dict[str, str]]:
    rows = []
    for code, (ch_name, en_name, locale) in LANGUAGES.items():
        rows.append(
            {
                "code": code,
                "name_zh": ch_name,
                "name_en": en_name,
                "locale": locale,
            }
        )
    rows.sort(key=lambda x: x["name_zh"])
    return rows


def _run_video_job(job_id: str) -> None:
    payload = JOBS[job_id]["payload"]
    try:
        _set_job_running(job_id)
        req = VideoDubRequest(**payload)
        if len(req.target_langs) == 1:
            target_lang = req.target_langs[0]
            results = video_dubber.process_video(
                req.url, req.source_lang, target_lang, burn_subtitles=req.burn_subtitles
            )
            history_manager.add_history(
                type="video",
                source_lang=req.source_lang,
                target_lang=target_lang,
                original_content=req.url,
                translated_content=results.get("dubbed_video", ""),
                details={"via": "api_job", "job_id": job_id},
            )
            _set_job_done(job_id, results)
        else:
            results = video_dubber.process_video_batch(
                req.url, req.source_lang, req.target_langs, burn_subtitles=req.burn_subtitles
            )
            for lang, res in results.get("languages", {}).items():
                history_manager.add_history(
                    type="video_batch",
                    source_lang=req.source_lang,
                    target_lang=lang,
                    original_content=req.url,
                    translated_content=res.get("dubbed_video", ""),
                    details={"via": "api_job", "job_id": job_id},
                )
            _set_job_done(job_id, results)
    except Exception as exc:
        _set_job_failed(job_id, str(exc))


def _run_meeting_summary_job(job_id: str) -> None:
    payload = JOBS[job_id]["payload"]
    video_path = payload.get("video_path")
    try:
        _set_job_running(job_id)
        summarizer = MeetingSummarizer(
            ai_backend=payload.get("ai_backend", "ollama"),
            ollama_model=payload.get("ollama_model", "qwen3:4b"),
            gemini_api_key=payload.get("gemini_api_key", ""),
        )
        result = summarizer.process_video(
            video_path,
            language=payload.get("language", "auto"),
            summary_types=payload.get("summary_types", ["full_summary"]),
        )
        response = {
            "transcript": result.transcript,
            "transcript_with_time": result.transcript_with_time,
            "summary": result.summary,
            "duration": result.duration,
            "language": result.language,
        }
        _set_job_done(job_id, response)
    except Exception as exc:
        _set_job_failed(job_id, str(exc))
    finally:
        if video_path and os.path.exists(video_path):
            try:
                os.remove(video_path)
            except OSError:
                pass


@app.get("/api/languages")
async def list_languages_endpoint():
    rows = _language_payload()
    return {"count": len(rows), "languages": rows}


@app.post("/api/translate/text")
async def translate_text_endpoint(request: TextTranslationRequest):
    try:
        result = translator.translate(request.text, request.source_lang, request.target_lang)
        history_manager.add_history(
            type="text",
            source_lang=request.source_lang,
            target_lang=request.target_lang,
            original_content=request.text,
            translated_content=result,
            details={"via": "api"},
        )
        return {"translated_text": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/translate/text/batch")
async def translate_text_batch_endpoint(request: BatchTextTranslationRequest):
    try:
        outputs = []
        for text in request.items:
            translated = translator.translate(
                text,
                request.source_lang,
                request.target_lang,
                glossary=request.glossary,
                style=request.style,
            )
            outputs.append(translated)
        history_manager.add_history(
            type="text_batch",
            source_lang=request.source_lang,
            target_lang=request.target_lang,
            original_content=f"[batch:{len(request.items)}]",
            translated_content="\n".join(outputs[:3]),
            details={"via": "api", "count": len(request.items)},
        )
        return {"count": len(outputs), "translations": outputs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/translate/image")
async def translate_image_endpoint(
    file: UploadFile = File(...),
    source_lang: str = Form("auto"),
    target_lang: str = Form("zh_TW"),
):
    try:
        suffix = os.path.splitext(file.filename or "image.png")[1] or ".png"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name

        full_result = ""
        for chunk in translator.translate_image(tmp_path, target_lang, source_lang):
            full_result = chunk

        os.unlink(tmp_path)

        history_manager.add_history(
            type="image",
            source_lang=source_lang,
            target_lang=target_lang,
            original_content=f"[API Upload] {file.filename}",
            translated_content=full_result,
            details={"via": "api"},
        )

        return {"translated_text": full_result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/translate/pdf")
async def translate_pdf_endpoint(
    file: UploadFile = File(...),
    source_lang: str = Form("en_US"),
    target_lang: str = Form("zh_TW"),
):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name

        final_result = ""
        for chunk in translator.translate_pdf(tmp_path, target_lang, source_lang):
            final_result = chunk

        os.unlink(tmp_path)

        history_manager.add_history(
            type="pdf",
            source_lang=source_lang,
            target_lang=target_lang,
            original_content=f"[API Upload] {file.filename}",
            translated_content=final_result,
            details={"via": "api"},
        )
        return {"translated_text": final_result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/dub/video")
async def dub_video_endpoint(request: VideoDubRequest):
    try:
        if not request.url.startswith("http"):
            raise HTTPException(status_code=400, detail="Only YouTube URLs supported in this endpoint for now")

        if len(request.target_langs) == 1:
            target_lang = request.target_langs[0]
            results = video_dubber.process_video(
                request.url, request.source_lang, target_lang, burn_subtitles=request.burn_subtitles
            )
            history_manager.add_history(
                type="video",
                source_lang=request.source_lang,
                target_lang=target_lang,
                original_content=request.url,
                translated_content=results.get("dubbed_video", ""),
                details={"via": "api", "original_srt": results.get("original_srt")},
            )
            return results

        results = video_dubber.process_video_batch(
            request.url, request.source_lang, request.target_langs, burn_subtitles=request.burn_subtitles
        )
        for lang, res in results.get("languages", {}).items():
            history_manager.add_history(
                type="video_batch",
                source_lang=request.source_lang,
                target_lang=lang,
                original_content=request.url,
                translated_content=res.get("dubbed_video", ""),
                details={"via": "api", "batch_id": str(id(results))},
            )
        return results

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/jobs/video")
async def create_video_job_endpoint(request: JobVideoRequest, background_tasks: BackgroundTasks):
    if not request.url.startswith("http"):
        raise HTTPException(status_code=400, detail="Only YouTube URLs are currently supported.")

    payload = request.model_dump() if hasattr(request, "model_dump") else request.dict()
    job_id = _create_job("video", payload)
    background_tasks.add_task(_run_video_job, job_id)
    return {"job_id": job_id, "status": "queued"}


@app.post("/api/jobs/meeting-summary")
async def create_meeting_summary_job_endpoint(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    language: str = Form("auto"),
    summary_types: str = Form("full_summary"),
    ai_backend: str = Form("ollama"),
    ollama_model: str = Form("qwen3:4b"),
    gemini_api_key: str = Form(""),
):
    suffix = os.path.splitext(file.filename or "video.mp4")[1] or ".mp4"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    type_list = [x.strip() for x in summary_types.split(",") if x.strip()]
    if not type_list:
        type_list = ["full_summary"]

    payload = {
        "video_path": tmp_path,
        "language": language,
        "summary_types": type_list,
        "ai_backend": ai_backend,
        "ollama_model": ollama_model,
        "gemini_api_key": gemini_api_key,
    }
    job_id = _create_job("meeting_summary", payload)
    background_tasks.add_task(_run_meeting_summary_job, job_id)
    return {"job_id": job_id, "status": "queued"}


@app.get("/api/jobs")
async def list_jobs_endpoint(limit: int = 20):
    jobs = sorted(JOBS.values(), key=lambda x: x["created_at"], reverse=True)[:limit]
    return {"count": len(jobs), "jobs": jobs}


@app.get("/api/jobs/{job_id}")
async def get_job_status_endpoint(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.post("/api/jobs/{job_id}/retry")
async def retry_job_endpoint(job_id: str, background_tasks: BackgroundTasks):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["status"] != "failed":
        raise HTTPException(status_code=400, detail="Only failed jobs can be retried")

    job["retry_count"] += 1
    job["status"] = "queued"
    job["error"] = ""
    job["updated_at"] = _now_iso()

    if job["type"] == "video":
        background_tasks.add_task(_run_video_job, job_id)
    elif job["type"] == "meeting_summary":
        background_tasks.add_task(_run_meeting_summary_job, job_id)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported job type: {job['type']}")

    return {"job_id": job_id, "status": "queued", "retry_count": job["retry_count"]}


# ========== Learning Endpoints ==========
from learning import learning_manager


class LearningTranslateRequest(BaseModel):
    text: str
    source_lang: str = "auto"
    target_lang: str = "zh_TW"


class WritingCorrectionRequest(BaseModel):
    text: str
    writing_lang: str = "en_US"
    native_lang: str = "zh_TW"


class ConversationRequest(BaseModel):
    scenario: str
    user_message: str
    practice_lang: str = "en_US"
    native_lang: str = "zh_TW"
    history: str = ""


class VocabularyAddRequest(BaseModel):
    word: str
    meaning: str
    source_lang: str = "en_US"
    target_lang: str = "zh_TW"
    part_of_speech: str = ""
    example_sentence: str = ""
    example_translation: str = ""


class ReviewCardRequest(BaseModel):
    card_id: int
    quality: int  # 0-5


@app.post("/api/learning/translate")
async def learning_translate_endpoint(request: LearningTranslateRequest):
    """Translate with learning annotations (vocabulary, grammar, examples)."""
    try:
        result = ""
        for chunk in translator.translate_learning(request.text, request.source_lang, request.target_lang):
            result = chunk
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/learning/writing-correction")
async def writing_correction_endpoint(request: WritingCorrectionRequest):
    """Correct and score a piece of writing."""
    try:
        result = ""
        for chunk in translator.writing_correction(request.text, request.writing_lang, request.native_lang):
            result = chunk
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/learning/conversation")
async def conversation_endpoint(request: ConversationRequest):
    """AI conversation practice partner."""
    try:
        result = ""
        for chunk in translator.conversation_practice(
            request.scenario, request.user_message,
            request.practice_lang, request.native_lang, request.history
        ):
            result = chunk
        return {"reply": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/learning/flashcards")
async def flashcards_endpoint(request: LearningTranslateRequest):
    """Generate vocabulary flashcards from text."""
    try:
        result = ""
        for chunk in translator.generate_flashcards(request.text, request.source_lang, request.target_lang):
            result = chunk
        return {"flashcards": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/learning/vocabulary")
async def add_vocabulary_endpoint(request: VocabularyAddRequest):
    """Add a word to the vocabulary bank."""
    row_id = learning_manager.add_vocabulary(
        word=request.word, meaning=request.meaning,
        source_lang=request.source_lang, target_lang=request.target_lang,
        part_of_speech=request.part_of_speech,
        example_sentence=request.example_sentence,
        example_translation=request.example_translation,
    )
    return {"id": row_id, "word": request.word}


@app.get("/api/learning/vocabulary")
async def list_vocabulary_endpoint(source_lang: str = "", target_lang: str = "", limit: int = 100):
    """List vocabulary cards."""
    cards = learning_manager.get_vocabulary(
        source_lang=source_lang or None,
        target_lang=target_lang or None,
        limit=limit,
    )
    return {"count": len(cards), "vocabulary": cards}


@app.get("/api/learning/vocabulary/due")
async def due_vocabulary_endpoint(source_lang: str = "", target_lang: str = "", limit: int = 20):
    """Get cards due for spaced repetition review."""
    cards = learning_manager.get_due_cards(
        source_lang=source_lang or None,
        target_lang=target_lang or None,
        limit=limit,
    )
    return {"count": len(cards), "cards": cards}


@app.post("/api/learning/vocabulary/review")
async def review_vocabulary_endpoint(request: ReviewCardRequest):
    """Submit a spaced repetition review for a vocabulary card."""
    result = learning_manager.review_card(request.card_id, request.quality)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.get("/api/learning/stats")
async def learning_stats_endpoint():
    """Get learning progress statistics."""
    return learning_manager.get_stats()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
