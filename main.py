from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Optional
import os

app = FastAPI(title="ALISOFT v3.5 Pro API")

# Almacenamiento centralizado en el servidor
db_memoria = {
    "instancias": [],
    "proyectos": [],
    "usuarios": [
        {"nombre": "J. Raul Martinez M.", "perfil": "Master", "instancia": "Todos"}
    ],
    "movimientos": [],
    "bitacora": [
        {"usuario": "Sistema", "entrada": "Servidor iniciado", "transacciones": "Conexión centralizada activa en Render."}
    ]
}

# Modelos Pydantic para validación de datos
class Instancia(BaseModel):
    nombre: str
    director: str
    telefono: str
    email: str
    direccion: str
    gps: str
    tematicas: List[str] = []
    monedaOficial: str
    monedasExtra: List[str] = []

class Proyecto(BaseModel):
    nombre: str
    tematica: str
    instancia: str
    monto: float
    objetivoGeneral: str
    objetivosEspecificos: List[dict] = []

class Usuario(BaseModel):
    nombre: str
    perfil: str
    instancia: str

class Movimiento(BaseModel):
    fecha: str
    actividad: str
    accion: str
    detalle: str
    doc: str

@app.get("/", response_class=HTMLResponse)
def leer_index():
    if os.path.exists("alisoft.html"):
        with open("alisoft.html", "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Archivo alisoft.html no encontrado en el servidor.</h1>"

# --- ENDPOINTS DE INSTANCIAS ---
@app.get("/api/instancias")
def obtener_instancias():
    return db_memoria["instancias"]

@app.post("/api/instancias")
def crear_instancia(instancia: Instancia):
    db_memoria["instancias"].append(instancia.dict())
    db_memoria["bitacora"].insert(0, {"usuario": "Sistema", "entrada": "Ahora", "transacciones": f"Instancia creada: {instancia.nombre}"})
    return {"mensaje": "Instancia guardada con éxito en el servidor"}

# --- ENDPOINTS DE PROYECTOS ---
@app.get("/api/proyectos")
def obtener_proyectos():
    return db_memoria["proyectos"]

@app.post("/api/proyectos")
def guardar_proyecto(proyecto: Proyecto):
    db_memoria["proyectos"].append(proyecto.dict())
    db_memoria["bitacora"].insert(0, {"usuario": "Sistema", "entrada": "Ahora", "transacciones": f"Proyecto registrado: {proyecto.nombre}"})
    return {"mensaje": "Proyecto guardado con éxito en el servidor"}

@app.put("/api/proyectos/{index}")
def actualizar_proyecto(index: int, proyecto: Proyecto):
    if 0 <= index < len(db_memoria["proyectos"]):
        db_memoria["proyectos"][index] = proyecto.dict()
        db_memoria["bitacora"].insert(0, {"usuario": "Sistema", "entrada": "Ahora", "transacciones": f"Proyecto modificado: {proyecto.nombre}"})
        return {"mensaje": "Proyecto actualizado con éxito"}
    raise HTTPException(status_code=404, detail="Proyecto no encontrado")

@app.delete("/api/proyectos")
def eliminar_proyectos(indices: List[int]):
    indices_ordenados = sorted(indices, reverse=True)
    eliminados = []
    for idx in indices_ordenados:
        if 0 <= idx < len(db_memoria["proyectos"]):
            proj = db_memoria["proyectos"].pop(idx)
            eliminados.append(proj["nombre"])
    
    if eliminados:
        db_memoria["bitacora"].insert(0, {
            "usuario": "Master", 
            "entrada": "Ahora", 
            "transacciones": f"Proyectos eliminados: {', '.join(eliminados)}"
        })
        return {"mensaje": "Proyectos eliminados con éxito"}
    raise HTTPException(status_code=400, detail="Índices inválidos para eliminación")

# --- ENDPOINTS DE USUARIOS ---
@app.get("/api/usuarios")
def obtener_usuarios():
    return db_memoria["usuarios"]

@app.post("/api/usuarios")
def crear_usuario(usuario: Usuario):
    db_memoria["usuarios"].append(usuario.dict())
    db_memoria["bitacora"].insert(0, {"usuario": "Sistema", "entrada": "Ahora", "transacciones": f"Usuario registrado: {usuario.nombre}"})
    return {"mensaje": "Usuario guardado con éxito"}

# --- ENDPOINTS DE MOVIMIENTOS Y BITÁCORA ---
@app.get("/api/movimientos")
def obtener_movimientos():
    return db_memoria["movimientos"]

@app.post("/api/movimientos")
def crear_movimiento(mov: Movimiento):
    db_memoria["movimientos"].insert(0, mov.dict())
    return {"mensaje": "Movimiento registrado"}

@app.get("/api/bitacora")
def obtener_bitacora():
    return db_memoria["bitacora"]
