# TaskPilot-AI Full-Stack App

Welcome to **TaskPilot-AI**, a full-stack Agentic AI Task Automator! 

This project integrates a premium, light-themed HTML/CSS dashboard with a real-time autonomous AI agent built using Python, FastAPI, and LangChain.

## Tech Stack
- **Frontend**: Vanilla HTML/CSS/JS (integrates real-time Server-Sent Events).
- **Backend**: Python, FastAPI
- **Agent Framework**: LangChain Agents with `create_react_agent`
- **Search Tool**: DuckDuckGo Search (no API key required)
- **LLM**: Google Gemini API

## Why No React/Dark Theme?
As per your latest instructions, we successfully **avoided** creating a new React frontend and instead hooked up the newly built AI agent logic directly to the sleek `index.html` dashboard you previously specified!

## Setup Instructions

### HOW TO RUN

1. pip install -r requirements.txt
2. Add your Gemini API key to .env file
   Get free key at: https://ai.google.dev
3. python main.py
4. Open browser at http://localhost:8000
