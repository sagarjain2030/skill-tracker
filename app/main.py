# app/main.py
from fastapi import FastAPI,Response
import os

app = FastAPI()

@app.get("/favicon.ico")
def favicon():
    return Response(status_code=204)

@app.api_route("/", methods=["GET", "HEAD"])
def health():
    return {"status": "ok"}

@app.api_route("/version", methods=["GET", "HEAD"])
def version():
    return {
        "commit": os.getenv("RENDER_GIT_COMMIT", "unknown"),
        "service": os.getenv("RENDER_SERVICE_NAME", "unknown"),
    }