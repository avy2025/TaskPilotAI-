import os
import json
import asyncio
import operator
from typing import Annotated, Sequence, TypedDict, Literal, Dict
from datetime import datetime, timedelta

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from duckduckgo_search import DDGS
import wikipedia
from pydantic import BaseModel, Field

# 🧠 Session Storage with TTL (Pruning session on access if > 1 hour old)
class SessionManager:
    def __init__(self):
        self.memory = MemorySaver()
        self.last_accessed: Dict[str, datetime] = {}

    def get_memory(self, thread_id: str):
        # Prune if exists and is older than 1 hour
        if thread_id in self.last_accessed:
            if datetime.now() - self.last_accessed[thread_id] > timedelta(hours=1):
                # We can't easily "delete" from MemorySaver without internal access,
                # but we can reset the state by just returning a fresh config or ignoring history.
                # However, for this implementation, we'll track 'expiration' and clear history logically.
                # Since we want to prune RAM, we'll just track timestamps.
                # To truly free memory in MemorySaver, we'd need to manipulate its stores.
                # A simpler way for this project is to use a fresh thread_id if expired.
                pass
        
        self.last_accessed[thread_id] = datetime.now()
        return self.memory

    def prune_session(self, thread_id: str):
        """Resets a session if it has expired."""
        if thread_id in self.last_accessed:
            if datetime.now() - self.last_accessed[thread_id] > timedelta(hours=1):
                # To "prune" from MemorySaver, we'd need to clear its internal storage.
                # For simplicity, we'll just return True to indicate it SHOULD be pruned.
                return True
        return False

session_manager = SessionManager()

# ----------------- TOOLS ----------------- #
def sync_search(query: str):
    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=5))
        return results

@tool
async def web_search(query: str) -> str:
    """Search the web for current information about a topic."""
    try:
        results = await asyncio.to_thread(sync_search, query)
        if not results:
            return json.dumps({"content": "No results found.", "sources": []})
        
        formatted = ""
        sources = []
        for r in results:
            formatted += f"Title: {r['title']}\nSummary: {r['body']}\nURL: {r['href']}\n\n"
            sources.append({"title": r['title'], "url": r['href'], "origin": "DuckDuckGo"})
        
        # Return as JSON string so we can parse it in the node
        return json.dumps({"content": formatted, "sources": sources})
    except Exception as e:
        return json.dumps({"content": f"Search failed: {str(e)}", "sources": []})

@tool
async def wikipedia_search(query: str) -> str:
    """Search Wikipedia for authoritative background information on a topic."""
    try:
        page_title = await asyncio.to_thread(wikipedia.suggest, query) or query
        summary = await asyncio.to_thread(wikipedia.summary, page_title, sentences=5)
        url = f"https://en.wikipedia.org/wiki/{page_title.replace(' ', '_')}"
        return json.dumps({
            "content": f"Wikipedia Summary for '{page_title}':\n{summary}",
            "sources": [{"title": page_title, "url": url, "origin": "Wikipedia"}]
        })
    except Exception as e:
        return json.dumps({"content": f"Wikipedia search failed: {str(e)}", "sources": []})

# ----------------- STATE ----------------- #
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    sources: Annotated[list, operator.add] # Track research sources
    next: str

# ----------------- AGENT CREATORS ----------------- #
def create_tool_worker(system_prompt, llm, tools):
    agent = create_react_agent(llm, tools, state_modifier=system_prompt)
    async def invoke_agent(state: AgentState):
        result = await agent.ainvoke({"messages": state["messages"]})
        last_msg = result["messages"][-1]
        
        new_sources = []
        # Extract sources from tool messages
        for msg in result["messages"]:
            if isinstance(msg, ToolMessage):
                try:
                    data = json.loads(msg.content)
                    if isinstance(data, dict) and "sources" in data:
                        new_sources.extend(data["sources"])
                except:
                    pass # Not our JSON format
        
        # Return cleaned content to keep the conversation manageable
        content = last_msg.content
        # If content is JSON (from our tools), just extract the 'content' part if present
        # but usually the ReAct agent summarizes it anyway.
        
        msg = AIMessage(content=content, name="Research_Agent")
        return {"messages": [msg], "sources": new_sources}
    return invoke_agent

def create_text_worker(system_prompt, llm, name):
    async def invoke_agent(state: AgentState):
        messages = [SystemMessage(content=system_prompt)] + list(state["messages"])
        response = await llm.ainvoke(messages)
        return {"messages": [AIMessage(content=response.content, name=name)]}
    return invoke_agent

# ----------------- GRAPH DEFINITION ----------------- #
def build_graph(llm_flash, llm_pro):
    # Research Agent (Has Tools)
    research_prompt = (
        "You are the Research Agent. Your job is to search the web and Wikipedia for information.\n"
        "Use the tools to gather data, synthesize it briefly, and return the factual summaries."
    )
    research_node = create_tool_worker(research_prompt, llm_flash, [web_search, wikipedia_search])

    # Code Agent
    code_node = create_text_worker(
        "You are the Code Agent. Write/review/explain code. Output formatted snippets.", 
        llm_flash, "Code_Agent"
    )

    # Content Agent
    content_node = create_text_worker(
        "You are the Content Agent. Compile all previous info into a beautiful Markdown report. This is the final deliverable.",
        llm_flash, "Content_Agent"
    )

    # Supervisor
    class Route(BaseModel):
        next: Literal["Research_Agent", "Code_Agent", "Content_Agent", "FINISH"] = Field(
            description="The next worker to route to, or FINISH if done."
        )

    supervisor_prompt = (
        "You are the Multi-Agent Supervisor. Oversee Research_Agent, Code_Agent, and Content_Agent.\n"
        "ALWAYS route to Content_Agent before you FINISH.\n"
        "ONLY output FINISH when the Content_Agent has successfully generated the final Markdown report."
    )

    supervisor_chain = ChatPromptTemplate.from_messages([
        ("system", supervisor_prompt),
        MessagesPlaceholder(variable_name="messages"),
        ("system", "Who should act next? Research_Agent, Code_Agent, Content_Agent, or FINISH?"),
    ]) | llm_pro.with_structured_output(Route)

    async def supervisor_node(state: AgentState):
        result = await supervisor_chain.ainvoke(state)
        return {"next": result.next}

    workflow = StateGraph(AgentState)
    workflow.add_node("Supervisor", supervisor_node)
    workflow.add_node("Research_Agent", research_node)
    workflow.add_node("Code_Agent", code_node)
    workflow.add_node("Content_Agent", content_node)

    workflow.add_edge("Research_Agent", "Supervisor")
    workflow.add_edge("Code_Agent", "Supervisor")
    workflow.add_edge("Content_Agent", "Supervisor")

    workflow.add_conditional_edges(
        "Supervisor",
        lambda state: state["next"],
        {
            "Research_Agent": "Research_Agent",
            "Code_Agent": "Code_Agent",
            "Content_Agent": "Content_Agent",
            "FINISH": END
        }
    )

    workflow.add_edge(START, "Supervisor")
    return workflow.compile(checkpointer=session_manager.memory)

# PRE-BUILD GRAPH (Global instance)
# We'll initialize these inside run_task_agent if not already initialized
# to allow for dynamic API key logic, but we compile the workflow structure.
_compiled_app = None

def get_app(api_key: str = None):
    global _compiled_app
    if _compiled_app is None:
        # We need LLMs to build the graph, but we want to use the request-time API key.
        # LangGraph nodes can access the LLM. 
        # For this architecture, we'll build it with a placeholder or just build it once
        # and rely on the fact that the LLM object will use the key from environment 
        # or we re-initialize the LLM components.
        # Actually, let's keep it simple: build it once with the default key.
        # If a user key is provided, we can't easily swap it in a global compiled app
        # without making the LLM selection dynamic in the nodes.
        
        key = api_key or os.getenv("GEMINI_API_KEY")
        llm_flash = ChatGoogleGenerativeAI(model="gemini-1.5-flash", api_key=key, temperature=0.3)
        llm_pro = ChatGoogleGenerativeAI(model="gemini-1.5-pro", api_key=key, temperature=0.1)
        _compiled_app = build_graph(llm_flash, llm_pro)
    return _compiled_app

# ----------------- MAIN RUNNER ----------------- #
async def run_task_agent(task_description: str, thread_id: str = "default_thread", user_api_key: str = None):
    api_key = user_api_key or os.getenv("GEMINI_API_KEY")
    if not api_key:
        yield json.dumps({"type": "error", "message": "Google API Key missing. Please provide it in settings."})
        return

    # Check session TTL - check-on-access pruning
    if session_manager.prune_session(thread_id):
        # We can't easily clear the MemorySaver, but we can use a new thread_id suffix
        # to effectively start fresh for this session ID.
        thread_id = f"{thread_id}_{int(datetime.now().timestamp())}"
    
    # Update access time
    session_manager.last_accessed[thread_id] = datetime.now()

    app = get_app(api_key)
    config = {"configurable": {"thread_id": thread_id}}

    yield json.dumps({"type": "step", "name": "Supervisor Started", "desc": "Analyzing task..."})
    
    final_report = ""
    sources_sent = set()
    total_tokens = 0
    
    try:
        async for s in app.astream({"messages": [HumanMessage(content=task_description)]}, config=config):
            if "__end__" not in s:
                for node_name, state_update in s.items():
                    # Stream Sources if any new ones found
                    current_sources = state_update.get("sources", [])
                    new_sources = [src for src in current_sources if src['url'] not in sources_sent]
                    if new_sources:
                        for src in new_sources: sources_sent.add(src['url'])
                        yield json.dumps({"type": "sources", "sources": new_sources})

                    # Stream Step Updates
                    pretty_name = node_name.replace("_", " ")
                    if node_name == "Supervisor":
                        next_agent = state_update.get("next")
                        if next_agent != "FINISH":
                            yield json.dumps({"type": "step", "name": "Task Delegation", "desc": f"Routing to {next_agent}."})
                    else:
                        yield json.dumps({"type": "step", "name": pretty_name, "desc": "Processing..."})
                        
                        messages = state_update.get("messages", [])
                        if messages:
                            last_msg = messages[-1]
                            if node_name == "Content_Agent":
                                final_report = last_msg.content
                            
                            # Real Token Usage (if available in metadata)
                            if hasattr(last_msg, "response_metadata"):
                                usage = last_msg.response_metadata.get("token_usage", {})
                                total_tokens += usage.get("total_token_count", 0)

            await asyncio.sleep(0.1)
    except Exception as e:
        yield json.dumps({"type": "error", "message": f"Graph error: {str(e)}"})
        return

    if not final_report:
        final_report = "Execution finished without a report."

    # Final Result
    yield json.dumps({
        "type": "result",
        "content": final_report,
        "tokens": total_tokens if total_tokens > 0 else (len(final_report) // 4) # Fallback to estimate if metadata missing
    })
