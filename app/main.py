# app/main.py
from fastapi import FastAPI,Response

app = FastAPI()

@app.get("/favicon.ico")
def favicon():
    return Response(status_code=204)

@app.api_route("/", methods=["GET", "HEAD"])
def health():
    return {"status": "ok"}