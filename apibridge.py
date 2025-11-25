from fastapi import FastAPI
from backend import AIClass

AI = AIClass()
app = FastAPI()

@app.get("/health")
def health_check():
    HPResult = AI.health_check()
    return {"result":HPResult}
