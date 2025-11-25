import os
from openai import OpenAI

class AIClass:

    def __init__(self):    
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    def health_check(self):
        response = self.client.responses.create(
            model="gpt-4o",
            instructions="You are a coding assistant that talks like a pirate.",
            input="How do I check if a Python object is an instance of a class?",
        )
        return response.output_text
    

    def chat(self, payload: dict, model: str = "gpt-4o"):
        """
        payload format:
        {
            "messages": [{ "role": "user"/"assistant", "content": "..." }],
            "settings": {...},
            "session_id": "..."
        }
        """
        print("Message received in backend:", payload)

        # --- extract last user message ---
        messages = payload.get("messages", [])
        last_user_msg = ""

        # reverse loop: en son user mesajını bul
        for m in reversed(messages):
            if m.get("role") == "user":
                last_user_msg = m.get("content", "")
                break

        if not last_user_msg:
            last_user_msg = "User sent an empty message."

        # --- LLM call ---
        response = self.client.responses.create(
            model=model,
            instructions="You are a helpful assistant.",
            input=last_user_msg,
        )

        print("Response generated in backend:", response.output_text)
        return response.output_text

    def chat_message_only(self, prompt: str, system_prompt: str = "", model="gpt-4o"):
        response = self.client.responses.create(
            model=model,
            instructions=system_prompt,
            input=prompt,
        )
        return response.output_text
