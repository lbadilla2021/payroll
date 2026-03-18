FROM python:3.12-slim

# Carpeta de trabajo
WORKDIR /app

# Instalar dependencias del sistema (opcional pero recomendado)
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# 🔥 CLAVE para que funcione "from app.xxx"
ENV PYTHONPATH=/app/app

# Exponer puerto
EXPOSE 8000

# Ejecutar backend
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
