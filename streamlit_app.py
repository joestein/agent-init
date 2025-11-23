import os
import uuid

import requests
import streamlit as st

API_URL = os.getenv("CHAT_API_URL", "http://localhost:8000/chat")

st.set_page_config(page_title="LangGraph Agent Chat", page_icon="LG")
st.title("LangGraph Agent Chat")

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []

st.sidebar.header("Session")
st.sidebar.text_input("Session ID", value=st.session_state.session_id, key="session_id")
st.sidebar.write(f"Chat API: {API_URL}")

for role, content in st.session_state.messages:
    with st.chat_message(role):
        st.markdown(content)

if prompt := st.chat_input("Ask the agent..."):
    st.session_state.messages.append(("user", prompt))
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        resp = requests.post(
            API_URL, json={"message": prompt, "session_id": st.session_state.session_id}, timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
        reply = data.get("response", "No response from agent.")
        commands = data.get("available_commands", {})
        footer = "\n\nAvailable commands:\n" + "\n".join(
            [f"- {k}: {v}" for k, v in commands.items()]
        )
        reply_with_commands = reply + footer
    except Exception as exc:  # pragma: no cover - defensive
        reply_with_commands = f"Request failed: {exc}"

    st.session_state.messages.append(("assistant", reply_with_commands))
    with st.chat_message("assistant"):
        st.markdown(reply_with_commands)
