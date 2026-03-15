from __future__ import annotations

import asyncio
import logging
import os
import tempfile
import time
from pathlib import Path
from typing import Any, Optional
import json

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from utils.schema import AgenticJSOSharedState, HealthResponse, SearchResponse


logger = logging.getLogger("agentic_jso_api")
if not logger.handlers:
	logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

MAX_UPLOAD_SIZE_BYTES = 20 * 1024 * 1024
ALLOWED_RESUME_EXTENSIONS = {".pdf"}


def _validate_required_env() -> None:
	missing = [
		key
		for key in ("GEMINI_KEY", "SERP_DEV_API_KEY")
		if not os.getenv(key)
	]
	if missing:
		missing_str = ", ".join(missing)
		raise RuntimeError(f"Missing required environment variables: {missing_str}")


def _validate_resume_filename(filename: Optional[str]) -> str:
	if not filename:
		raise HTTPException(status_code=400, detail="resume file must have a filename")

	suffix = Path(filename).suffix.lower()
	if suffix not in ALLOWED_RESUME_EXTENSIONS:
		raise HTTPException(status_code=400, detail="resume file must be a PDF")
	return suffix


async def _save_uploaded_resume(file: UploadFile) -> str:
	suffix = _validate_resume_filename(file.filename)
	total_size = 0

	with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
		while True:
			chunk = await file.read(1024 * 1024)
			if not chunk:
				break
			total_size += len(chunk)
			if total_size > MAX_UPLOAD_SIZE_BYTES:
				temp_path = temp_file.name
				temp_file.close()
				try:
					os.remove(temp_path)
				except OSError:
					pass
				raise HTTPException(status_code=413, detail="resume file exceeds 20MB limit")
			temp_file.write(chunk)
		return temp_file.name


def _run_pipeline(state: AgenticJSOSharedState) -> AgenticJSOSharedState:
	from nodes.parser import parse_resume
	from nodes.query_expansion import query_expansion
	from nodes.query_generator import generate_job_query
	from nodes.search import run_parallel_search

	state = parse_resume(state)
	with open("state_debug.json", "w", encoding="utf-8") as f:
		f.write(state.model_dump_json(indent=2))
	state = query_expansion(state)
	with open("state_debug_after_expansion.json", "w", encoding="utf-8") as f:
		f.write(state.model_dump_json(indent=2))
	state = generate_job_query(state)
	with open("state_debug_after_query_generation.json", "w", encoding="utf-8") as f:
		f.write(state.model_dump_json(indent=2))
	state = run_parallel_search(state)
	with open("state_debug_after_search.json", "w", encoding="utf-8") as f:
		f.write(state.model_dump_json(indent=2))
	return state


app = FastAPI(title="Agentic JSO API", version="0.1.0")


@app.on_event("startup")
def startup_checks() -> None:
	_validate_required_env()
	logger.info("Startup checks passed")


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
	return HealthResponse(status="ok")


@app.post("/search", response_model=SearchResponse)
async def search_jobs(
	query: str = Form(...),
	resume: UploadFile = File(...),
	job_search_intent: Optional[list[str]] = Form(default=None),
	location_preferences: Optional[list[str]] = Form(default=None),
) -> SearchResponse:
	cleaned_query = query.strip()
	if not cleaned_query:
		raise HTTPException(status_code=400, detail="query must not be empty")

	start_time = time.perf_counter()
	resume_path = await _save_uploaded_resume(resume)

	try:
		state = AgenticJSOSharedState(
			query=cleaned_query,
			job_search_intent=job_search_intent,
			resume_path=resume_path,
			resume_data={},
			target_roles=[],
			location_preferences=location_preferences,
			skills=[],
			expanded_titles=[],
			domain=[],
			xray_queries={},
			search_results=[],
		)

		final_state = await run_in_threadpool(_run_pipeline, state)
		results = final_state.search_results if isinstance(final_state.search_results, list) else []

		elapsed_ms = int((time.perf_counter() - start_time) * 1000)
		logger.info("Search request completed in %sms with %s results", elapsed_ms, len(results))

		return SearchResponse(search_results=results)
	except HTTPException:
		raise
	except ValueError as exc:
		logger.exception("Input processing failed") 
		raise HTTPException(status_code=400, detail=str(exc)) from exc
	except Exception as exc:
		logger.exception("Pipeline execution failed")
		raise HTTPException(status_code=500, detail="search pipeline failed") from exc
	finally:
		try:
			os.remove(resume_path)
		except OSError:
			pass
		await resume.close()


if __name__ == "__main__":
	import uvicorn

	uvicorn.run("main:app", reload=True)
