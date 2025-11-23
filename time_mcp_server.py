import os
from datetime import datetime, timezone

from fastapi import FastAPI
import uvicorn

app = FastAPI(title="MCP Time Server", version="0.1.0")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/time")
def get_time():
    now = datetime.now(timezone.utc).isoformat()
    return {"time": now}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("MCP_TIME_PORT", "8001")))
