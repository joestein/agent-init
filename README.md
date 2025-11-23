# Agent Init

This repo hosts a small LangGraph-powered agent wired to an OpenAI model. It exposes:
- A FastAPI `/chat` endpoint for conversational commands.
- A minimal MCP-style time server (also FastAPI) the agent calls to retrieve the current time.
- A Streamlit UI that talks to the chat endpoint.

## Prerequisites
- Python 3.10+
- `OPENAI_API_KEY` in your environment (for the agent's LLM calls).

Install dependencies:
```bash
pip install -r requirements.txt
```

## Run the MCP time server
```bash
python time_mcp_server.py
# Serves on http://localhost:8001/time
```

## Run the LangGraph agent HTTP server
```bash
export OPENAI_API_KEY=sk-...
python agent_server.py
# Serves chat on http://localhost:8000/chat
```

Optional env vars:
- `MCP_TIME_SERVER_URL`: override the MCP time server base URL (default `http://localhost:8001`).
- `OPENAI_MODEL`: override the OpenAI model name (default `gpt-4o-mini`).
- `PORT`: override the agent server port (default `8000`).

Example chat payload:
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What time is it?", "session_id": "demo"}'
```

## Streamlit chat UI
```bash
export CHAT_API_URL=http://localhost:8000/chat
streamlit run streamlit_app.py
```
The UI displays the conversation and the available commands. Session IDs keep conversations separate.

## Run everything with Docker Compose
Build and run all services (MCP server, agent API, Streamlit UI):
```bash
export OPENAI_API_KEY=sk-...
docker compose up --build
```
Services:
- MCP time server on `http://localhost:8001/time`
- Agent API on `http://localhost:8000/chat`
- Streamlit UI on `http://localhost:8501`

## Available commands
- `get_time`: Fetch the current time via the MCP time server.
- `list_commands`: List the commands the agent can execute.
