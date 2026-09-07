from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Optional
import os
import psycopg2
from psycopg2.extras import RealDictCursor

app = FastAPI(title="ALISOFT v3.5 Pro - PostgreSQL Production")

# Obtener la URL de conexión a PostgreSQL desde las variables de entorno de Render
DATABASE_URL = os.environ.get("DATABASE_URL")

def get_db_connection():
    if not DATABASE_URL:
        raise HTTPException(status_code=500, detail="DATABASE_URL no está configurada en el servidor.")
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn

# Inicializar tablas en PostgreSQL al arrancar el servidor
def init_db():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Tabla de Instancias
        cur.execute("""
            CREATE TABLE IF NOT EXISTS instancias (
                id SERIAL PRIMARY KEY,
                nombre TEXT UNIQUE NOT NULL,
                director TEXT,
                telefono TEXT,
                email TEXT,
                direccion TEXT,
                gps TEXT,
                tematicas TEXT[],
                moneda_oficial TEXT,
                monedas_extra TEXT[]
            );
        """)
        
        # Tabla de Proyectos
        cur.execute("""
            CREATE TABLE IF NOT EXISTS proyectos (
                id SERIAL PRIMARY KEY,
                nombre TEXT NOT NULL,
                tematica TEXT,
                instancia TEXT,
                monto NUMERIC,
                objetivo_general TEXT,
                objetivos_especificos JSONB
            );
        """)

        # Tabla de Usuarios
        cur.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id SERIAL PRIMARY KEY,
                nombre TEXT NOT NULL,
                perfil TEXT,
                instancia TEXT
            );
        """)

        # Insertar usuario Master por defecto si no existe
        cur.execute("SELECT COUNT(*) FROM usuarios WHERE perfil = 'Master';")
        if cur.fetchone()['count'] == 0:
            cur.execute(
                "INSERT INTO usuarios (nombre, perfil, instancia) VALUES (%s, %s, %s);",
                ("J. Raul Martinez M.", "Master", "Todos")
            )

        # Tabla de Movimientos de Campo
        cur.execute("""
            CREATE TABLE IF NOT EXISTS movimientos (
                id SERIAL PRIMARY KEY,
                fecha TEXT,
                actividad TEXT,
                accion TEXT,
                detalle TEXT,
                doc TEXT
            );
        """)

        # Tabla de Bitácora
        cur.execute("""
            CREATE TABLE IF NOT EXISTS bitacora (
                id SERIAL PRIMARY KEY,
                usuario TEXT,
                entrada TEXT,
                transacciones TEXT
            );
        """)

        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error al inicializar la base de datos: {e}")

@app.on_event("startup")
def startup_event():
    init_db()

# Modelos Pydantic
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
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM instancias ORDER BY id DESC;")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    # Mapear nombres de columnas de SQL al formato esperado por el frontend
    resultado = []
    for r in rows:
        resultado.append({
            "id": r["id"],
            "nombre": r["nombre"],
            "director": r["director"],
            "telefono": r["telefono"],
            "email": r["email"],
            "direccion": r["direccion"],
            "gps": r["gps"],
            "tematicas": r["tematicas"] or [],
            "monedaOficial": r["moneda_oficial"],
            "monedasExtra": r["monedas_extra"] or []
        })
    return resultado

@app.post("/api/instancias")
def crear_instancia(instancia: Instancia):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO instancias (nombre, director, telefono, email, direccion, gps, tematicas, moneda_oficial, monedas_extra)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
        """, (
            instancia.nombre, instancia.director, instancia.telefono, instancia.email,
            instancia.direccion, instancia.gps, instancia.tematicas, instancia.monedaOficial, instancia.monedasExtra
        ))
        cur.execute(
            "INSERT INTO bitacora (usuario, entrada, transacciones) VALUES (%s, NOW()::text, %s);",
            ("Master", f"Instancia creada: {instancia.nombre}")
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cur.close()
        conn.close()
    return {"mensaje": "Instancia guardada con éxito en PostgreSQL"}

@app.delete("/api/instancias")
def eliminar_instancias(nombres: List[str]):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        for nombre in nombres:
            cur.execute("DELETE FROM instancias WHERE nombre = %s;", (nombre,))
        cur.execute(
            "INSERT INTO bitacora (usuario, entrada, transacciones) VALUES (%s, NOW()::text, %s);",
            ("Master", f"Instancias eliminadas: {', '.join(nombres)}")
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cur.close()
        conn.close()
    return {"mensaje": "Instancias eliminadas correctamente"}

# --- ENDPOINTS DE PROYECTOS ---
@app.get("/api/proyectos")
def obtener_proyectos():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM proyectos ORDER BY id DESC;")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    resultado = []
    for r in rows:
        resultado.append({
            "id": r["id"],
            "nombre": r["nombre"],
            "tematica": r["tematica"],
            "instancia": r["instancia"],
            "monto": float(r["monto"]),
            "objetivoGeneral": r["objetivo_general"],
            "objetivosEspecificos": r["objetivos_especificos"] or []
        })
    return resultado

@app.post("/api/proyectos")
def guardar_proyecto(proyecto: Proyecto):
    import json
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO proyectos (nombre, tematica, instancia, monto, objetivo_general, objetivos_especificos)
            VALUES (%s, %s, %s, %s, %s, %s);
        """, (
            proyecto.nombre, proyecto.tematica, proyecto.instancia,
            proyecto.monto, proyecto.objetivoGeneral, json.dumps(proyecto.objetivosEspecificos)
        ))
        cur.execute(
            "INSERT INTO bitacora (usuario, entrada, transacciones) VALUES (%s, NOW()::text, %s);",
            ("Master", f"Proyecto registrado: {proyecto.nombre}")
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cur.close()
        conn.close()
    return {"mensaje": "Proyecto guardado con éxito en PostgreSQL"}

@app.put("/api/proyectos/{proy_id}")
def actualizar_proyecto(proy_id: int, proyecto: Proyecto):
    import json
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE proyectos 
            SET nombre = %s, tematica = %s, instancia = %s, monto = %s, objetivo_general = %s, objetivos_especificos = %s
            WHERE id = %s;
        """, (
            proyecto.nombre, proyecto.tematica, proyecto.instancia,
            proyecto.monto, proyecto.objetivoGeneral, json.dumps(proyecto.objetivosEspecificos), proy_id
        ))
        cur.execute(
            "INSERT INTO bitacora (usuario, entrada, transacciones) VALUES (%s, NOW()::text, %s);",
            ("Master", f"Proyecto modificado ID {proy_id}: {proyecto.nombre}")
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cur.close()
        conn.close()
    return {"mensaje": "Proyecto actualizado con éxito"}

@app.delete("/api/proyectos")
def eliminar_proyectos(ids: List[int]):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        for proy_id in ids:
            cur.execute("DELETE FROM proyectos WHERE id = %s;", (proy_id,))
        cur.execute(
            "INSERT INTO bitacora (usuario, entrada, transacciones) VALUES (%s, NOW()::text, %s);",
            ("Master", f"Proyectos eliminados IDs: {ids}")
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cur.close()
        conn.close()
    return {"mensaje": "Proyectos eliminados con éxito"}

# --- ENDPOINTS DE USUARIOS ---
@app.get("/api/usuarios")
def obtener_usuarios():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM usuarios ORDER BY id DESC;")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(r) for r in rows]

@app.post("/api/usuarios")
def crear_usuario(usuario: Usuario):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO usuarios (nombre, perfil, instancia) VALUES (%s, %s, %s);",
            (usuario.nombre, usuario.perfil, usuario.instancia)
        )
        cur.execute(
            "INSERT INTO bitacora (usuario, entrada, transacciones) VALUES (%s, NOW()::text, %s);",
            ("Master", f"Usuario registrado: {usuario.nombre}")
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cur.close()
        conn.close()
    return {"mensaje": "Usuario guardado con éxito"}

# --- MOVIMIENTOS Y BITÁCORA ---
@app.get("/api/movimientos")
def obtener_movimientos():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM movimientos ORDER BY id DESC;")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(r) for r in rows]

@app.post("/api/movimientos")
def crear_movimiento(mov: Movimiento):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO movimientos (fecha, actividad, accion, detalle, doc) VALUES (%s, %s, %s, %s, %s);",
            (mov.fecha, mov.actividad, mov.accion, mov.detalle, mov.doc)
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cur.close()
        conn.close()
    return {"mensaje": "Movimiento registrado"}

@app.get("/api/bitacora")
def obtener_bitacora():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT usuario, entrada, transacciones FROM bitacora ORDER BY id DESC LIMIT 50;")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(r) for r in rows]
