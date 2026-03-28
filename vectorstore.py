import os
from pathlib import Path

from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

ROOT = Path(__file__).resolve().parent
BAZA80_PATH = ROOT / "Baza80.txt"
PERSIST_DIR = ROOT / "data" / "chroma_db"
COLLECTION_NAME = "baza80_google"

# Obecne API Gemini: embedContent → gemini-embedding-001 (text-embedding-004 bywa 404 na v1beta)
DEFAULT_EMBEDDING_MODEL = "gemini-embedding-001"


def get_embeddings() -> GoogleGenerativeAIEmbeddings:
    api_key = os.getenv("GEMINI_API_KEY", "AIzaSyBSaj4aD9osrkeGcDayug_3yWkq-BcZc_4").strip()
    if not api_key:
        raise ValueError("Brak GEMINI_API_KEY")
    model = os.getenv("GEMINI_EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL).strip()
    return GoogleGenerativeAIEmbeddings(
        model=model,
        google_api_key=api_key,
    )


def _load_and_split_docs():
    if not BAZA80_PATH.is_file():
        BAZA80_PATH.write_text("Przykładowa treść bazy danych.", encoding="utf-8")
    raw = BAZA80_PATH.read_text(encoding="utf-8")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", " ", ""],
    )
    return splitter.create_documents([raw])


def init_or_load_vectorstore() -> Chroma:
    emb = get_embeddings()
    if PERSIST_DIR.exists() and any(PERSIST_DIR.iterdir()):
        print(f"Chroma: wczytuję {PERSIST_DIR}")
        return Chroma(
            collection_name=COLLECTION_NAME,
            embedding_function=emb,
            persist_directory=str(PERSIST_DIR),
        )
    print("Chroma: nowy indeks…")
    PERSIST_DIR.parent.mkdir(parents=True, exist_ok=True)
    docs = _load_and_split_docs()
    vs = Chroma.from_documents(
        documents=docs,
        embedding=emb,
        collection_name=COLLECTION_NAME,
        persist_directory=str(PERSIST_DIR),
    )
    print(f"Zaindeksowano {len(docs)} fragmentów.")
    return vs
