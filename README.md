# 🛰️ TaskPilot-AI
### Full-Stack Autonomous Agentic Researcher

Welcome to **TaskPilot-AI**, a high-performance, autonomous AI task automator. This platform seamlessly integrates a premium dashboard with a robust LangGraph-powered AI agent, capable of real-time web research, data synthesis, and structured reporting.

---

## 🛠️ Tech Stack
*   **Frontend**: Vanilla HTML5, CSS3 (Modern Responsive Dashboard), JavaScript (SSE Streaming).
*   **Backend**: Python, FastAPI (Asynchronous Event Streaming).
*   **AI Framework**: LangGraph, LangChain (ReAct Agent Pattern).
*   **Intelligence**: Google Gemini 1.5 Flash API.
*   **Search**: duckduckgo-search (Autonomous Web Access).
*   **Security**: DOMPurify (Sanitised Markdown Rendering).

---

## 🌀 Autonomous Workflow
The flowchart below illustrates how TaskPilot-AI processes your "Mission Input" autonomously using real-time memory and tool interaction.

```mermaid
graph TD
    A[User Input] -->|Session ID| B(FastAPI Backend)
    B -->|Thread ID| C{LangGraph Agent}
    C -->|Thinking| D[Agent Planning]
    D --> E{Tool Selection}
    E -->|Web Access| F[Web Search Tool]
    E -->|Synthesis| G[Summarise Tool]
    E -->|Structure| H[Write Report Tool]
    F --> I[Memory Update]
    G --> I
    H --> J[Final Agent Output]
    I -->|Past Context| C
    J -->|SSE Stream| K[Secured Frontend]
    K -->|DOMPurify| L[User Display]
```

---

## 🚀 Advanced Features

### 🧠 Persistent AI Memory
Unlike standard AI chats, TaskPilot-AI utilizes **LangGraph's checkpointing system**. The agent remembers your name, previous tasks, and research context across multiple prompts within a single session.

### 🛑 Real-time Stop Control
Integrated `AbortController` functionality allowing users to instantly cancel a running agent mission if the task scope changes.

### 📱 Premium Responsive UI
A fluid, modern dashboard designed for all screen sizes. The layout intelligently stacks from a two-column desktop view to a mobile-optimized vertical structure.

### 🔒 Security-First Rendering
All AI reports are processed through **DOMPurify** before being rendered, ensuring zero risk of XSS or malicious code injection from hallucinated outputs.

### ⚡ Async Agentic Flow
The entire agentic cycle is non-blocking. Tools are executed asynchronously, and steps are streamed to the frontend via **Server-Sent Events (SSE)** for a "living" UX.

---

## ⚙️ Setup & Installation

### 1. Requirements
*   Python 3.9+
*   Google Gemini API Key ([Get one here](https://ai.google.dev))

### 2. Basic Installation
```bash
# Clone the repository
git clone https://github.com/avy2025/TaskPilotAI.git
cd TaskPilotAI

# Install dependencies
pip install -r requirements.txt
```

### 3. Setup Environment
Create a `.env` file in the root directory:
```env
GEMINI_API_KEY=your_api_key_here
```

### 4. Run the Application
```bash
python main.py
```
Open your browser at **[http://localhost:8000](http://localhost:8000)**.

---

## 📂 Project Structure
*   `main.py`: FastAPI server & SSE routing.
*   `agent.py`: LangGraph agent architecture & tool definitions.
*   `index.html`: Premium dashboard UI.
*   `style.css`: Responsive design system & animations.
*   `script.js`: SSE handling & UI state management.

---
*Created with ❤️ by the TaskPilot-AI Team.*
