from fastapi import FastAPI, Form, File, UploadFile, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import httpx
import json
import uvicorn

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

@app.get("/", response_class=HTMLResponse)
async def serve_form():
    try:
        file_path = os.path.join(os.path.dirname(__file__), "index.html")
        with open(file_path, "r") as file:
            return HTMLResponse(content=file.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>index.html not found</h1>", status_code=404)


@app.post("/api")
@app.post("/api/")
async def receive_question(
    question: str = Form(..., min_length=1),
    file: Optional[UploadFile] = File(None)
):
    return {
        "question": question,
        "answer": "",
        "file received": file.filename if file else "No file uploaded",
    }
