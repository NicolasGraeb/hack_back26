"""
Dodaje brakujące rekordy do tabeli `categories` (unikalna nazwa).

Nie usuwa ani nie modyfikuje istniejących wierszy — bezpieczne do wielokrotnego uruchomienia.

  python utils/seed_categories.py

Wymaga skonfigurowanej bazy (jak reszta projektu) i utworzonych tabel.
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from sqlalchemy import select
from sqlalchemy.orm import Session

from db import SessionLocal
from models import Category

# Kategorie z demo (seed_demo_data) + dodatkowe branżowe (startupy / IT).
CATEGORY_NAMES: list[str] = [
    "Edge AI, Web3 i quantum-safe",
    "Robotyka i autonomiczne systemy",
    "Rendering rozproszony i GPU",
    "Medtech, wearables i drony",
    "Środowisko, wody i biomimetyka",
    "FinTech, CBDC i smart money",
    "Biotech i neuro-nutrycja",
    "Food-tech i personalizacja napojów",
    "Gaming, BCI i interfejsy haptyczne",
    "Pet-tech i mięso in vitro",
    "SaaS i cloud",
    "Cyberbezpieczeństwo",
    "E-commerce i marketplace",
    "Logistyka i supply chain",
    "EdTech",
    "PropTech i smart city",
    "CleanTech i OZE",
    "HealthTech",
    "AgriTech",
    "SpaceTech i satelity",
    "HR Tech i rekrutacja",
    "LegalTech",
    "InsurTech",
    "Marketing automation",
    "IoT i smart home",
]


def upsert_categories(session: Session) -> tuple[int, int]:
    """Zwraca (dodane, już_było)."""
    added = 0
    skipped = 0
    for name in CATEGORY_NAMES:
        name = name.strip()
        if not name:
            continue
        exists = session.scalar(select(Category.id).where(Category.name == name))
        if exists is not None:
            skipped += 1
            continue
        session.add(Category(name=name))
        added += 1
    session.commit()
    return added, skipped


def main() -> None:
    with SessionLocal() as session:
        added, skipped = upsert_categories(session)
    print(f"Kategorie: dodano {added}, bez zmian (już w bazie) {skipped}.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Błąd: {e}", file=sys.stderr)
        raise SystemExit(1) from e
