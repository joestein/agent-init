import os
from functools import lru_cache
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel

from agent_graph import MCPTimeClient, build_agent_graph, DEFAULT_COMMANDS


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    available_commands: Dict[str, str]


def _build_graph():
    mcp_base_url = os.getenv("MCP_TIME_SERVER_URL", "http://localhost:8001")
    client = MCPTimeClient(mcp_base_url)
    checkpointer = MemorySaver()
    compiled_graph, commands, system_message = build_agent_graph(mcp_client=client, checkpointer=checkpointer)
    return compiled_graph, commands, system_message


@lru_cache(maxsize=1)
def get_agent():
    graph, commands, system_message = _build_graph()
    return graph, commands, system_message


app = FastAPI(title="LangGraph Agent Server", version="0.1.0")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest):
    agent, commands, system_message = get_agent()
    session_id = payload.session_id or "default"
    config = {"configurable": {"thread_id": session_id}}

    try:
        state_snapshot = agent.get_state(config)
    except Exception:
        state_snapshot = None

    messages = [HumanMessage(content=payload.message)]
    if not state_snapshot or not state_snapshot.values.get("messages"):
        messages.insert(0, system_message)

    try:
        result = agent.invoke({"messages": messages}, config=config)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Agent invocation failed: {exc}")

    ai_messages = [msg for msg in result.get("messages", []) if isinstance(msg, AIMessage)]
    response_text = ai_messages[-1].content if ai_messages else "No response from agent."
    if isinstance(response_text, list):  # Handle structured content from the model
        response_text = "\n".join(
            [part.get("text", "") if isinstance(part, dict) else str(part) for part in response_text]
        )
    return ChatResponse(response=response_text, available_commands=commands or DEFAULT_COMMANDS)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
