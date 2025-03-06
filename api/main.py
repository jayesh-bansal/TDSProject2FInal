from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import HTMLResponse
import httpx
import json
import uvicorn

app = FastAPI()

# LLM API details
AIPROXY_TOKEN = ""
BASE_URL = "http://aiproxy.sanand.workers.dev/openai/v1"
LLM_MODEL = "gpt-4o-mini"


async def call_llm(question: str):
    url = f"{BASE_URL}/chat/completions"
    headers = {"Authorization": f"Bearer {AIPROXY_TOKEN}",
               "Content-Type": "application/json"}
    messages = [{"role": "system", "content": "You are a helpful AI assistant. who provide just answer for the asked question"},
            {"role": "user", "content": f"Question: {question}"}]

    payload = {
        "model": "gpt-4o-mini",
        "messages": messages,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:  # Increase timeout
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()  # Raise error for non-200 responses
        return response.json()["choices"][0]["message"]["content"]


@app.get("/", response_class=HTMLResponse)
async def serve_form():
    """Serves the HTML form."""
    with open("index.html", "r") as file:
        return HTMLResponse(content=file.read())


@app.post("/api/")
async def receive_question(question: str = Form(...), file: UploadFile = File(None)):
    """Handles form submission, processes question via LLM, and returns response."""
    # llm_response = await call_llm(question)
    return {"question": question,"filename": file.filename if file else "No file uploaded"}
