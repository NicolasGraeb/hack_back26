import json
import os
import re
from contextlib import asynccontextmanager
from datetime import datetime
from decimal import Decimal
from typing import Literal

import models  # noqa: F401 — tabele w metadata
from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from google import genai
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from bucket import bucket_configured, presigned_get_url, upload_company_image
from config import get_settings
from constants import DEV_FIXED_USER_ID
from db import engine, get_db
from models import Announcement, Base, Category, Company, User
from prompts import build_chat_prompt, build_rag_prompt
from vectorstore import init_or_load_vectorstore

settings = get_settings()


class QueryRequest(BaseModel):
    company_profile: str
    question: str = Field(
        default="Jakie dofinansowania mogą pasować do mojej działalności?",
    )


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    surname: str
    email: str


class CategoryPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class CompanyPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    nip_krs: str
    user_id: int
    address: str | None
    image_url: str | None
    contact_phone: str | None = None
    contact_email: str | None = None
    categories: list[CategoryPublic] = Field(default_factory=list)


class CompanyMini(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    nip_krs: str
    address: str | None = None
    contact_phone: str | None = None
    contact_email: str | None = None
    categories: list[CategoryPublic] = Field(default_factory=list)


class AnnouncementPublic(BaseModel):
    id: int
    company_id: int
    created_at: datetime
    salary_min: str | None
    salary_max: str | None
    description: str | None
    company: CompanyMini | None = None


class AnnouncementCreateIn(BaseModel):
    """Nowe ogłoszenie dla firmy zalogowanego użytkownika (dev: DEV_FIXED_USER_ID)."""

    description: str = Field(min_length=1, max_length=50_000)
    salary_min: Decimal | None = None
    salary_max: Decimal | None = None

    @model_validator(mode="after")
    def salaries_order(self):
        if self.salary_min is not None and self.salary_max is not None:
            if self.salary_min > self.salary_max:
                raise ValueError("salary_min nie może być większe niż salary_max")
        return self


class MeResponse(BaseModel):
    user: UserPublic
    company: CompanyPublic | None


class ChatMessageIn(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessageIn] = Field(default_factory=list)


class ChatTrackOut(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str = ""
    label: str = ""
    summary: str = ""
    bullets: list[str] = Field(default_factory=list)


class ChatStructuredOut(BaseModel):
    model_config = ConfigDict(extra="ignore")

    headline: str = ""
    lead: str = ""
    tracks: list[ChatTrackOut] = Field(default_factory=list)
    sources_line: str | None = None
    follow_up: str | None = None


class ChatResponse(BaseModel):
    """structured — odpowiedź do custom UI; reply_plain — gdy model nie zwrócił poprawnego JSON."""

    structured: ChatStructuredOut | None = None
    reply_plain: str | None = None


def _company_to_public(c: Company) -> CompanyPublic:
    return CompanyPublic(
        id=c.id,
        name=c.name,
        nip_krs=c.nip_krs,
        user_id=c.user_id,
        address=c.address,
        image_url=c.image_url,
        contact_phone=c.contact_phone,
        contact_email=c.contact_email,
        categories=[CategoryPublic.model_validate(x) for x in c.categories],
    )


def _extract_chat_json_dict(text: str) -> dict | None:
    t = text.strip()
    if "```" in t:
        m = re.search(r"```(?:json)?\s*([\s\S]*?)```", t, re.IGNORECASE)
        if m:
            t = m.group(1).strip()
    try:
        obj = json.loads(t)
    except json.JSONDecodeError:
        return None
    return obj if isinstance(obj, dict) else None


def _announcement_to_public(a: Announcement) -> AnnouncementPublic:
    c = a.company
    mini = None
    if c is not None:
        mini = CompanyMini(
            id=c.id,
            name=c.name,
            nip_krs=c.nip_krs,
            address=c.address,
            contact_phone=c.contact_phone,
            contact_email=c.contact_email,
            categories=[CategoryPublic.model_validate(x) for x in c.categories],
        )
    return AnnouncementPublic(
        id=a.id,
        company_id=a.company_id,
        created_at=a.created_at,
        salary_min=str(a.salary_min) if a.salary_min is not None else None,
        salary_max=str(a.salary_max) if a.salary_max is not None else None,
        description=a.description,
        company=mini,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.sqlalchemy_create_all:
        Base.metadata.create_all(bind=engine)
    app.state.gemini = genai.Client(api_key=settings.gemini_api_key)
    app.state.chroma = init_or_load_vectorstore()
    yield


app = FastAPI(title="Fundusze RAG", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    ok = getattr(app.state, "chroma", None) is not None
    return {"status": "running", "chroma": "ok" if ok else "err"}


@app.get("/me", response_model=MeResponse)
def get_me(db: Session = Depends(get_db)):
    """Zalogowany użytkownik (dev: zawsze `DEV_FIXED_USER_ID`)."""
    stmt = (
        select(User)
        .where(User.id == DEV_FIXED_USER_ID)
        .options(
            joinedload(User.company).selectinload(Company.categories),
        )
    )
    user = db.execute(stmt).unique().scalar_one_or_none()
    if user is None:
        raise HTTPException(404, detail="Użytkownik nie istnieje.")
    co = user.company
    return MeResponse(
        user=UserPublic.model_validate(user),
        company=_company_to_public(co) if co is not None else None,
    )


@app.get("/categories", response_model=list[CategoryPublic])
def list_categories(db: Session = Depends(get_db)):
    rows = db.scalars(select(Category).order_by(Category.name)).all()
    return [CategoryPublic.model_validate(c) for c in rows]


@app.get("/companies", response_model=list[CompanyPublic])
def list_companies(db: Session = Depends(get_db)):
    rows = db.scalars(
        select(Company)
        .options(selectinload(Company.categories))
        .order_by(Company.name),
    ).all()
    return [_company_to_public(c) for c in rows]


@app.get("/companies/{company_id}", response_model=CompanyPublic)
def get_company(company_id: int, db: Session = Depends(get_db)):
    c = db.scalars(
        select(Company)
        .where(Company.id == company_id)
        .options(selectinload(Company.categories)),
    ).first()
    if c is None:
        raise HTTPException(404, detail="Firma nie istnieje.")
    return _company_to_public(c)


@app.get("/announcements", response_model=list[AnnouncementPublic])
def list_announcements(
    company_id: int | None = Query(default=None, description="Opcjonalny filtr po firmie"),
    db: Session = Depends(get_db),
):
    stmt = (
        select(Announcement)
        .options(
            selectinload(Announcement.company).selectinload(Company.categories),
        )
        .order_by(Announcement.created_at.desc())
    )
    if company_id is not None:
        stmt = stmt.where(Announcement.company_id == company_id)
    rows = db.scalars(stmt).all()
    return [_announcement_to_public(a) for a in rows]


@app.post("/announcements", response_model=AnnouncementPublic)
def create_announcement(body: AnnouncementCreateIn, db: Session = Depends(get_db)):
    """Tworzy ogłoszenie dla firmy powiązanej z kontem z /me (bez przekazywania company_id)."""
    stmt = select(User).where(User.id == DEV_FIXED_USER_ID).options(joinedload(User.company))
    user = db.execute(stmt).unique().scalar_one_or_none()
    if user is None:
        raise HTTPException(404, detail="Użytkownik nie istnieje.")
    co = user.company
    if co is None:
        raise HTTPException(
            400,
            detail="Brak firmy przypisanej do konta — nie można dodać ogłoszenia.",
        )

    desc = body.description.strip()
    ann = Announcement(
        company_id=co.id,
        description=desc,
        salary_min=body.salary_min,
        salary_max=body.salary_max,
    )
    db.add(ann)
    db.commit()
    db.refresh(ann)

    loaded = db.scalars(
        select(Announcement)
        .where(Announcement.id == ann.id)
        .options(
            selectinload(Announcement.company).selectinload(Company.categories),
        ),
    ).first()
    if loaded is None:
        raise HTTPException(500, detail="Nie udało się odczytać utworzonego ogłoszenia.")
    return _announcement_to_public(loaded)


@app.post("/chat", response_model=ChatResponse)
async def chat_ai(body: ChatRequest):
    g = getattr(app.state, "gemini", None)
    if not g:
        raise HTTPException(500, detail="Brak inicjalizacji Gemini.")

    lines: list[str] = []
    for m in body.messages:
        label = (
            "Użytkownik"
            if m.role == "user"
            else ("Asystent" if m.role == "assistant" else "System")
        )
        lines.append(f"{label}: {m.content}")
    transcript = "\n\n".join(lines) if lines else "(brak wiadomości)"

    prompt = build_chat_prompt(transcript)
    try:
        r = g.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
        )
        text = (r.text or "").strip()
        if not text:
            return ChatResponse(
                structured=None,
                reply_plain="Nie udało się wygenerować odpowiedzi — spróbuj ponownie.",
            )
        raw = _extract_chat_json_dict(text)
        if raw is not None:
            try:
                structured = ChatStructuredOut.model_validate(raw)
                if structured.headline or structured.tracks:
                    return ChatResponse(structured=structured, reply_plain=None)
            except ValidationError:
                pass
        return ChatResponse(structured=None, reply_plain=text)
    except Exception as e:
        raise HTTPException(500, detail=f"Gemini: {e!s}") from e


@app.post("/ask")
async def ask(body: QueryRequest):
    g = getattr(app.state, "gemini", None)
    vs = getattr(app.state, "chroma", None)
    if not g or not vs:
        raise HTTPException(500, detail="Brak inicjalizacji.")

    q = f"{body.company_profile} {body.question}"
    docs = vs.similarity_search(q, k=settings.rag_top_k)
    ctx = "\n\n---\n\n".join(d.page_content for d in docs)
    prompt = build_rag_prompt(ctx, body.company_profile, body.question)

    try:
        r = g.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
        )
        return r.text
    except Exception as e:
        raise HTTPException(500, detail=f"Gemini: {e!s}") from e


def _presign_ttl() -> int:
    return int(os.getenv("BUCKET_PRESIGN_EXPIRES", "604800"))


@app.post("/companies/{company_id}/logo")
async def upload_company_logo(
    company_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Wgrywa obrazek firmy do Railway Bucket; w bazie zapisuje klucz obiektu w image_url."""
    if not bucket_configured():
        raise HTTPException(
            503,
            detail="Brak konfiguracji bucketa: ENDPOINT, BUCKET, ACCESS_KEY_ID, SECRET_ACCESS_KEY.",
        )
    company = db.get(Company, company_id)
    if company is None:
        raise HTTPException(404, detail="Firma nie istnieje.")

    data = await file.read()
    ct = file.content_type or "application/octet-stream"
    try:
        key = upload_company_image(
            company_id,
            data,
            content_type=ct,
            original_filename=file.filename,
        )
    except ValueError as e:
        raise HTTPException(400, detail=str(e)) from e
    except RuntimeError as e:
        raise HTTPException(503, detail=str(e)) from e

    company.image_url = key
    db.commit()
    return {
        "object_key": key,
        "logo_url": f"/companies/{company_id}/logo",
        "hint": "W image_url jest klucz S3; obrazek pokazuj przez GET /companies/{id}/logo",
    }


@app.get("/companies/{company_id}/logo")
def get_company_logo(company_id: int, db: Session = Depends(get_db)):
    """
    Jeśli image_url to https://... — przekierowanie tam.
    Jeśli to klucz w buckecie — presigned GET (bucket Railway jest prywatny).
    """
    company = db.get(Company, company_id)
    if company is None or not company.image_url:
        raise HTTPException(404, detail="Brak logo.")

    url = company.image_url.strip()
    if url.startswith("http://") or url.startswith("https://"):
        return RedirectResponse(url, status_code=302)

    if not bucket_configured():
        raise HTTPException(
            503,
            detail="Brak konfiguracji bucketa — nie można wygenerować presigned URL.",
        )
    try:
        signed = presigned_get_url(url, expires_in=_presign_ttl())
    except Exception as e:
        raise HTTPException(502, detail=f"Błąd bucketa: {e!s}") from e
    return RedirectResponse(signed, status_code=302)
