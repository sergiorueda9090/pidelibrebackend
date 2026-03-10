# ============================================================
# Dockerfile — Backend Django (pidelibre)
# ============================================================
# Imagen base: Python 3.11 slim (Debian Bookworm)
# Servidor: Gunicorn en puerto 8000
# ============================================================

FROM python:3.11-slim-bookworm

# ── Variables de entorno para Python ─────────────────────────
# PYTHONDONTWRITEBYTECODE=1  → no crear archivos .pyc
# PYTHONUNBUFFERED=1         → logs en tiempo real (sin buffer)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# ── Instalar dependencias del sistema ────────────────────────
# pkg-config + default-libmysqlclient-dev → necesarios para compilar mysqlclient
# gcc → compilador C requerido por mysqlclient y Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    pkg-config \
    default-libmysqlclient-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# ── Directorio de trabajo dentro del contenedor ─────────────
WORKDIR /app

# ── Copiar archivo de dependencias ──────────────────────────
# Se copia primero para aprovechar la caché de Docker
COPY requiriments.txt .

# ── Instalar dependencias de Python ─────────────────────────
# Se excluye pywin32 (solo funciona en Windows)
RUN grep -iv "pywin32" requiriments.txt > requirements_linux.txt \
    && pip install --no-cache-dir -r requirements_linux.txt \
    && pip install --no-cache-dir gunicorn==23.0.0 \
    && rm requirements_linux.txt

# ── Copiar todo el código fuente ────────────────────────────
COPY . .

# ── Crear directorio de logs ────────────────────────────────
RUN mkdir -p /app/logs

# ── Puerto expuesto ─────────────────────────────────────────
EXPOSE 8000

# ── Comando de inicio ───────────────────────────────────────
# Gunicorn con 3 workers, binding en 0.0.0.0:8000
CMD ["gunicorn", "backend.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "3", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
