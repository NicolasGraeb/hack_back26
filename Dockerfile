# FastAPI — hackathon (Gemini, PostgreSQL, Chroma, opcjonalnie S3)
# Budowanie: docker build -t hackathon-api .
# Uruchomienie: docker run --env-file .env -p 8000:8000 hackathon-api
# Albo: docker compose up --build

FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# psycopg2-binary ma koła dla Linuxa; libpq5 — bezpieczniej na runtime
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Port HTTP API
EXPOSE 8000

# --- Domyślne (nadpisz w runtime / docker-compose / Railway) ---
# Sekrety NIE wklejaj do obrazu — podawaj przy starcie kontenera.
ENV PORT=8000 \
    CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000 \
    RAG_TOP_K=6 \
    GEMINI_MODEL=gemini-3-flash-preview \
    GEMINI_EMBEDDING_MODEL=gemini-embedding-001 \
    REGION=auto \
    BUCKET_PRESIGN_EXPIRES=604800

# Wymagane w runtime (bez wartości w obrazie):
#   GEMINI_API_KEY       — Google AI (chat + embeddingi Chroma)
#   DATABASE_URL         — np. postgresql+psycopg2://user:pass@host:5432/db
# Opcjonalne:
#   CORS_ORIGINS         — lista po przecinku (domena frontu na produkcji)
#   SQLALCHEMY_CREATE_ALL=true — utwórz tabele przy starcie (tylko dev)
#   ENDPOINT, BUCKET, ACCESS_KEY_ID, SECRET_ACCESS_KEY — Railway bucket / S3 (logo)
#   NEXT_PUBLIC_API_URL  — ustawiane po stronie frontu, nie w tym kontenerze

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/')" || exit 1

CMD ["sh", "-c", "exec uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
