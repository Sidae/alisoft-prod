from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import os

app = FastAPI(title="ALISOFT v3.5 Pro", version="3.5.0")

@app.get("/", response_class=HTMLResponse)
async def read_index():
    # Lee el archivo HTML completo de ALISOFT para servirlo en el navegador
    html_path = "alisoft.html"
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Error: Archivo alisoft.html no encontrado en el servidor.</h1>"