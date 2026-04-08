# 🛰️ TaskPilot-AI
### Full-Stack Autonomous Agentic Researcher

Welcome to **TaskPilot-AI**, a high-performance, autonomous AI task automator. This platform seamlessly integrates a premium dashboard with a robust LangGraph-powered AI agent, capable of real-time web research, data synthesis, and structured reporting.

---

## 🛠️ Tech Stack
*   **Frontend**: Vanilla HTML5, CSS3 (Modern Responsive Dashboard), JavaScript (SSE & JSON Integration).
*   **Backend**: Python, FastAPI (Hybrid SSE & REST API).
*   **AI Framework**: LangGraph, LangChain (ReAct Agent Pattern).
*   **Vector DB**: FAISS (High-performance similarity search).
*   **Embeddings**: OpenAI `text-embedding-3-small`.
*   **Intelligence**: Google Gemini 1.5 Flash API.
*   **Search**: `duckduckgo-search` & `wikipedia`.
*   **PDF Engine**: PyPDF (Secure document parsing).
*   **Security**: DOMPurify (Sanitised Markdown Rendering).

---

The flowchart below illustrates how TaskPilot-AI processes your "Mission Input" autonomously, switching between real-time web research and internal document retrieval (RAG).

```mermaid
graph TD
    A[User Input] -->|Session ID| B(FastAPI Backend)
    B -->|Toggle: use_rag| C{Mode Selector}
    
    subgraph "Autonomous Agent Mode"
    C -->|False| D{LangGraph Agent}
    D --> E[Planning & Tool Exec]
    E -->|Web| F[DDG/Wikipedia]
    F --> G[Memory Update]
    G -->|Context| D
    E -->|Final| H[Structured Report]
    end

    subgraph "RAG Pipeline Mode"
    C -->|True| I[FAISS Vector Store]
    I --> J[Similarity Search]
    J --> K[Gemini Context Synthesis]
    K --> L[RAG Response]
    end

    H --> M[SSE Stream]
    L --> N[JSON Payload]
    M --> O[Secured Frontend]
    N --> O
    O -->|DOMPurify| P[User Display]
```

---

## 🚀 Advanced Features

### 🧠 Persistent AI Memory
Unlike standard AI chats, TaskPilot-AI utilizes **LangGraph's checkpointing system**. The agent remembers your name, previous tasks, and research context across multiple prompts within a single session.

### 📚 Document Intelligence (RAG)
Armed with a dedicated RAG pipeline, the system can parse **PDF** and **TXT** files. It converts text into high-dimensional vectors stored in a local **FAISS** index for millisecond-latency retrieval.

### 🛑 Real-time Stop Control
Integrated `AbortController` functionality allowing users to instantly cancel a running agent mission if the task scope changes.

### 📥 Report Exporting
Instantly **Copy to Clipboard** or **Download as Markdown** directly from the dashboard. The reports are formatted for professional use with tables and bold headers.

### 📱 Premium Responsive UI
A fluid, modern dashboard designed for all screen sizes. Features a dynamic timeline with tool-specific icons (Search, Lookup, Synthesize).

### 🔒 Security-First Rendering
All AI reports are processed through **DOMPurify** before being rendered, ensuring zero risk of XSS or malicious code injection from hallucinated outputs.

---

## ⚙️ Setup & Installation

### 1. Requirements
*   Python 3.9+ or **Docker**
*   Google Gemini API Key ([Get one here](https://ai.google.dev))

### 2. Manual Installation
```bash
# Clone the repository
git clone https://github.com/avy2025/TaskPilotAI.git
cd TaskPilotAI

# Install dependencies
pip install -r requirements.txt
```

### 3. Docker Installation (Recommended)
```bash
# Start with one command
docker-compose up
```

### 4. Setup Environment
Create a `.env` file in the root directory:
```env
# Required for LangGraph Agent
GEMINI_API_KEY=your_gemini_key

# Required for RAG Embeddings
OPENAI_API_KEY=your_openai_key
```

### 5. Run the Application (Manual)
```bash
python main.py
```
Open your browser at **[http://localhost:8000](http://localhost:8000)**.

---

## 📂 Project Structure
*   `main.py`: FastAPI server & SSE routing.
*   `agent.py`: LangGraph agent architecture & tool definitions.
*   `rag/`: Core RAG logic (Vector store, Embeddings, Parsers).
*   `index.html`: Premium dashboard UI.
*   `style.css`: Responsive design system & animations.
*   `script.js`: SSE handling & UI state management.
*   `Dockerfile` & `docker-compose.yml`: Containerization logic.
*   `uploads/`: Temporary storage for uploaded documents.

---
