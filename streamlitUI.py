# streamlitUI.py
import uuid
import streamlit as st
import apibridge as API

st.set_page_config(page_title="AI Chat", layout="centered")

@st.dialog("File Upload")
def uploadfiles():
    uploaded = st.file_uploader("Add files", accept_multiple_files=True)
    if uploaded:
        st.session_state.uploaded_files.extend([f.name for f in uploaded])
    if st.session_state.uploaded_files:
        st.caption("Files: " + ", ".join(st.session_state.uploaded_files))


if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.messages = []
    st.session_state.settings = {
        "web_search": True,
        "image_generation": True,
        "data_analysis": True,
        "think": False,
    }
    st.session_state.uploaded_files = []

st.title("AI Chat")
st.caption("Tool-calling chat with RAG, web search, images & data analysis.")

cols = st.columns([1, 1, 1])
with cols[0]:
    if st.button("Check health"):
        try:
            hc = API.health_check()
            txt = hc.get("result", str(hc))
        except Exception as e:  # noqa: BLE001
            txt = f"Health check failed: {type(e).__name__}: {e}"
        st.session_state.messages.append({"role": "assistant", "content": f"[Health check]\n{txt}"})
with cols[2]:
    with st.popover("Chat controls"):
        st.caption("Capabilities")
        for key, label, desc in [
            ("web_search", "Web Search", "Use tools to browse the web."),
            ("image_generation", "Image Generation", "Generate or edit images."),
            ("data_analysis", "Data Analysis", "Analyze files and data tables."),
            ("think", "Think", "Enhanced step-by-step reasoning."),
        ]:
            st.session_state.settings[key] = st.checkbox(
                label, value=st.session_state.settings[key], help=desc
            )
with cols[1]:
    if st.button("Add Files"):
        uploadfiles()
    
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

prompt = st.chat_input("Send a message...")
if prompt:
    user_msg = {"role": "user", "content": prompt}
    st.session_state.messages.append(user_msg)

    payload = {
        "messages": st.session_state.messages,
        "settings": st.session_state.settings,
        "session_id": st.session_state.session_id,
    }

    try:
        chat_response = API.chat(payload)
        content = chat_response.get("response", "") or "Backend returned an empty response."
        reply = {"role": "assistant", "content": content}
    except Exception as e:  # noqa: BLE001
        reply = {"role": "assistant", "content": f"Error while calling backend: {type(e).__name__}: {e}"}

    st.session_state.messages.append(reply)
    st.rerun()
