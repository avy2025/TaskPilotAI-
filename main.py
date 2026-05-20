import os
import json
import logging
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from dotenv import load_dotenv
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Import agent and RAG routes
from agent import run_task_agent
from rag.upload import router as upload_router
from rag.retrieve import router as retrieve_router
from rag.rag_pipeline import rag_pipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

load_dotenv()

# Rate limiting setup
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="TaskPilotAI API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS configuration
allowed_origins = [os.getenv("ALLOWED_ORIGIN", "http://localhost:8000")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure uploads directory exists
os.makedirs("uploads", exist_ok=True)

# Include RAG routers
app.include_router(upload_router)
app.include_router(retrieve_router)

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
@limiter.limit("10/minute")
async def run_agent(request: Request):
    """
    Supports both traditional agent (SSE) and RAG response (JSON).
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    task = body.get("task") or body.get("query") or ""
    session_id = body.get("session_id", "default_session")
    use_rag = body.get("use_rag", False)
    api_key = body.get("api_key") # User-provided API key

    # Input Validation
    if not task.strip():
        raise HTTPException(status_code=400, detail="Task description cannot be empty.")
    if len(task) > 2000:
        raise HTTPException(status_code=400, detail="Task description too long (max 2000 characters).")

    if use_rag:
        logger.info(f"Starting RAG query: {task[:50]}...")
        result = await rag_pipeline.generate_response(task, user_api_key=api_key)
        return result

    logger.info(f"Starting agent task for session: {session_id}")

    async def event_generator():
        async for chunk in run_task_agent(task, thread_id=session_id, user_api_key=api_key):
            yield f"data: {chunk}\n\n"

    return EventSourceResponse(event_generator())

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting TaskPilotAI Server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
