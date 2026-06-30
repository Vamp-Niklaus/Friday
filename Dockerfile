FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Copy backend requirements and install
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all backend code into the container
COPY backend/ .

EXPOSE 7860

# Hugging Face exposes port 7860 by default
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port 7860"]
