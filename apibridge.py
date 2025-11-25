from fastapi import FastAPI
from backend import AIClass
from typing import Dict, Any

AI = AIClass()
app = FastAPI()

@app.get("/health")
def health_check():
    return {"result": AI.health_check()}

@app.post("/chat")
def chat(payload: Dict[str, Any]):
    response = AI.chat(payload)
    return {"response": response}

@app.post("/chat_messageonly")
def chat_messageonly(data: Dict[str, Any]):
    prompt = data.get("prompt", "")
    system_prompt = data.get("system_prompt", "")
    model = data.get("model", "gpt-4o")
    response = AI.chat_message_only(prompt, system_prompt, model)
    return {"response": response}
