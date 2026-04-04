import os
import json
import asyncio
import logging
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from sse_starlette.sse import EventSourceResponse
from dotenv import load_dotenv

# Import agent and RAG routes
from agent import run_task_agent
from rag.upload import router as upload_router

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

load_dotenv()

# Ensure uploads directory exists
os.makedirs("uploads", exist_ok=True)

app = FastAPI(title="TaskPilotAI API")

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include RAG router
app.include_router(upload_router)

@app.get("/", response_class=HTMLResponse)
async def read_index():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/style.css")
async def get_style():
    return FileResponse("style.css")

@app.get("/script.js")
async def get_script():
    return FileResponse("script.js")

@app.post("/run-agent")
async def run_agent(request: Request):
    """
    Expects JSON body: { "task": "...", "session_id": "..." }
    """
    body = await request.json()
    task = body.get("task", "")
    session_id = body.get("session_id", "default_session")

    logger.info(f"Starting agent task: {task} for session: {session_id}")

    async def event_generator():
        # Pass session_id as thread_id to the agent for memory
        async for chunk in run_task_agent(task, thread_id=session_id):
            yield chunk

    return EventSourceResponse(event_generator())

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting TaskPilotAI Server on http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)
