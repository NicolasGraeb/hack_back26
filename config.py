import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()

DEFAULT_DATABASE_URL = (
 'postgresql://postgres:WsgGuekAxUMWldOIEFotcjfadNZjfzeo@postgres.railway.internal:5432/railway'
    #"postgresql+psycopg2://admin:admin@127.0.0.1:9191/postgres"
)


def get_database_url() -> str:
    return 'postgresql://postgres:WsgGuekAxUMWldOIEFotcjfadNZjfzeo@caboose.proxy.rlwy.net:21602/railway'
    #os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL).strip())


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str
    gemini_model: str
    rag_top_k: int
    cors_origins: tuple[str, ...]
    sqlalchemy_create_all: bool


@lru_cache
def get_settings() -> Settings:
    key = os.getenv("GEMINI_API_KEY", "AIzaSyBSaj4aD9osrkeGcDayug_3yWkq-BcZc_4").strip()
    if not key:
        raise ValueError("Ustaw GEMINI_API_KEY.")
    raw = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://localhost:3002,http://localhost:5173,frontend-hack26.vercel.app",
    )
    origins = tuple(x.strip() for x in raw.split(",") if x.strip())
    return Settings(
        gemini_api_key=key,
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-3-flash-preview").strip(),
        rag_top_k=int(os.getenv("RAG_TOP_K", "6")),
        cors_origins=origins,
        sqlalchemy_create_all=os.getenv("SQLALCHEMY_CREATE_ALL", "").lower()
        in ("1", "true", "yes"),
    )
