import os
import json
import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from sse_starlette.sse import EventSourceResponse
from dotenv import load_dotenv

from agent import run_task_agent

load_dotenv()

app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=HTMLResponse)
async def read_index():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.post("/run-agent")
async def run_agent(request: Request):
    """
    Expects JSON body: { "task": "..." }
    Yields SSE events:
    - { "type": "step", "name": "Searching Web", "desc": "...", "status": "active" }
    - { "type": "step_complete", "name": "..." }
    - { "type": "result", "content": "Markdown text...", "tokens": 1204 }
    """
    body = await request.json()
    task = body.get("task", "")

    async def event_generator():
        # Yield the thought process by invoking the agent generator
        async for chunk in run_task_agent(task):
            yield chunk

    return EventSourceResponse(event_generator())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
