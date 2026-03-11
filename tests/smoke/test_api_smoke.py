import unittest
from io import BytesIO
from unittest.mock import patch

from fastapi import BackgroundTasks, HTTPException, UploadFile

import api


class TestApiSmoke(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        api.JOBS.clear()

    async def test_list_languages_endpoint(self):
        response = await api.list_languages_endpoint()
        self.assertTrue(response["count"] > 0)
        codes = {row["code"] for row in response["languages"]}
        self.assertIn("zh_TW", codes)

    async def test_translate_text_endpoint_success(self):
        request = api.TextTranslationRequest(
            text="Hello world",
            source_lang="en_US",
            target_lang="zh_TW",
        )

        with patch.object(api.translator, "translate", return_value="哈囉世界") as mock_translate, \
             patch.object(api.history_manager, "add_history") as mock_history:
            response = await api.translate_text_endpoint(request)

        self.assertEqual(response, {"translated_text": "哈囉世界"})
        mock_translate.assert_called_once_with("Hello world", "en_US", "zh_TW")
        mock_history.assert_called_once()

    async def test_translate_text_endpoint_error(self):
        request = api.TextTranslationRequest(
            text="Hello world",
            source_lang="en_US",
            target_lang="zh_TW",
        )

        with patch.object(api.translator, "translate", side_effect=RuntimeError("model failure")):
            with self.assertRaises(HTTPException) as ctx:
                await api.translate_text_endpoint(request)

        self.assertEqual(ctx.exception.status_code, 500)
        self.assertIn("model failure", str(ctx.exception.detail))

    async def test_translate_text_batch_endpoint_success(self):
        req = api.BatchTextTranslationRequest(
            items=["a", "b"],
            source_lang="en_US",
            target_lang="zh_TW",
            glossary="",
            style="",
        )

        with patch.object(api.translator, "translate", side_effect=["甲", "乙"]) as mock_translate, \
             patch.object(api.history_manager, "add_history") as mock_history:
            response = await api.translate_text_batch_endpoint(req)

        self.assertEqual(response["count"], 2)
        self.assertEqual(response["translations"], ["甲", "乙"])
        self.assertEqual(mock_translate.call_count, 2)
        mock_history.assert_called_once()

    async def test_translate_image_endpoint_success(self):
        upload = UploadFile(filename="sample.png", file=BytesIO(b"fake-image-bytes"))

        with patch.object(api.translator, "translate_image", return_value=iter(["step", "final translation"])) as mock_translate_image, \
             patch.object(api.history_manager, "add_history") as mock_history:
            response = await api.translate_image_endpoint(
                file=upload,
                source_lang="auto",
                target_lang="zh_TW",
            )

        self.assertEqual(response, {"translated_text": "final translation"})
        mock_translate_image.assert_called_once()
        mock_history.assert_called_once()

    async def test_translate_pdf_endpoint_success(self):
        upload = UploadFile(filename="sample.pdf", file=BytesIO(b"%PDF-1.4 fake"))

        with patch.object(api.translator, "translate_pdf", return_value=iter(["step", "final pdf translation"])) as mock_translate_pdf, \
             patch.object(api.history_manager, "add_history") as mock_history:
            response = await api.translate_pdf_endpoint(
                file=upload,
                source_lang="en_US",
                target_lang="zh_TW",
            )

        self.assertEqual(response, {"translated_text": "final pdf translation"})
        mock_translate_pdf.assert_called_once()
        mock_history.assert_called_once()

    async def test_dub_video_endpoint_invalid_url_returns_400(self):
        request = api.VideoDubRequest(
            url="not_a_url",
            source_lang="auto",
            target_langs=["zh_TW"],
            burn_subtitles=True,
        )

        with self.assertRaises(HTTPException) as ctx:
            await api.dub_video_endpoint(request)

        self.assertEqual(ctx.exception.status_code, 400)

    async def test_create_video_job_endpoint(self):
        request = api.JobVideoRequest(
            url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            source_lang="auto",
            target_langs=["zh_TW"],
            burn_subtitles=True,
        )
        bg = BackgroundTasks()
        response = await api.create_video_job_endpoint(request, bg)
        self.assertIn("job_id", response)
        self.assertEqual(response["status"], "queued")
        self.assertIn(response["job_id"], api.JOBS)

    async def test_list_and_get_job_endpoint(self):
        job_id = api._create_job("video", {"url": "https://example.com"})
        jobs = await api.list_jobs_endpoint()
        self.assertEqual(jobs["count"], 1)
        self.assertEqual(jobs["jobs"][0]["job_id"], job_id)

        detail = await api.get_job_status_endpoint(job_id)
        self.assertEqual(detail["job_id"], job_id)
        self.assertEqual(detail["status"], "queued")

    async def test_retry_failed_video_job_endpoint(self):
        bg = BackgroundTasks()
        job_id = api._create_job("video", {"url": "https://example.com", "source_lang": "auto", "target_langs": ["zh_TW"], "burn_subtitles": True})
        api.JOBS[job_id]["status"] = "failed"
        api.JOBS[job_id]["error"] = "boom"

        response = await api.retry_job_endpoint(job_id, bg)

        self.assertEqual(response["job_id"], job_id)
        self.assertEqual(response["status"], "queued")
        self.assertEqual(response["retry_count"], 1)
        self.assertEqual(api.JOBS[job_id]["error"], "")

    async def test_retry_non_failed_job_returns_400(self):
        bg = BackgroundTasks()
        job_id = api._create_job("video", {"url": "https://example.com"})
        with self.assertRaises(HTTPException) as ctx:
            await api.retry_job_endpoint(job_id, bg)
        self.assertEqual(ctx.exception.status_code, 400)


if __name__ == "__main__":
    unittest.main()
