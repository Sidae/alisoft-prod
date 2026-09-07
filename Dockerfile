# Usar una imagen oficial y ligera de Python
FROM python:3.11-slim

# Directorio de trabajo dentro del contenedor
WORKDIR /app

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar las librerías de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el código fuente y archivos estáticos al contenedor
COPY . .

# Cloud Run asigna dinámicamente el puerto mediante la variable de entorno PORT
# Uvicorn levantará la aplicación FastAPI escuchando en todas las interfaces
CMD sh -c "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"