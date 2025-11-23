import os
from typing import Dict, List, Optional

import requests
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import END, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode

DEFAULT_COMMANDS: Dict[str, str] = {
    "get_time": "Get the current time from the MCP time server.",
    "list_commands": "List the commands this agent can run.",
}


class MCPTimeClient:
    """Minimal MCP-style client that queries the time server."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def get_time(self) -> str:
        resp = requests.get(f"{self.base_url}/time", timeout=5)
        resp.raise_for_status()
        payload = resp.json()
        return payload.get("time", "")


def build_agent_graph(
    *,
    mcp_client: MCPTimeClient,
    model: Optional[ChatOpenAI] = None,
    commands: Dict[str, str] = None,
    checkpointer=None,
):
    commands = commands or DEFAULT_COMMANDS
    available_command_lines = "\n".join([f"- {key}: {value}" for key, value in commands.items()])
    system_message = SystemMessage(
        content=(
            "You are a LangGraph-based command routing agent. "
            "Use the available tools to satisfy user requests. "
            "If a request cannot be mapped to the available commands, respond with the list of commands and ask the user to choose one. "
            f"Available commands:\n{available_command_lines}"
        )
    )

    @tool("get_time")
    def get_time_tool():
        """Get the current time from the MCP time server."""
        try:
            current_time = mcp_client.get_time()
            return f"The MCP time server reports: {current_time}"
        except Exception as exc:  # pragma: no cover - defensive
            return f"Failed to fetch time from the MCP server: {exc}"

    @tool("list_commands")
    def list_commands_tool():
        """List the available commands the agent can execute."""
        return "Available commands:\n" + available_command_lines

    tools = [get_time_tool, list_commands_tool]
    llm = model or ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"), temperature=0)
    llm_with_tools = llm.bind_tools(tools)

    def call_model(state: MessagesState):
        messages = state.get("messages", [])
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [system_message] + list(messages)
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    tool_node = ToolNode(tools)
    graph = StateGraph(MessagesState)
    graph.add_node("model", call_model)
    graph.add_node("tools", tool_node)
    graph.set_entry_point("model")
    graph.add_conditional_edges(
        "model",
        lambda state: "tools" if state["messages"] and getattr(state["messages"][-1], "tool_calls", None) else END,
    )
    graph.add_edge("tools", "model")

    return graph.compile(checkpointer=checkpointer), commands, system_message
