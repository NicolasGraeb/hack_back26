"""
Jednorazowo: dodaje kolumny contact_phone, contact_email do companies (PostgreSQL)
oraz wypełnia je fikcyjnymi danymi (jak w seed_demo_data).

  python utils/setup_company_contact.py

Wymaga DATABASE_URL w środowisku / .env (jak reszta projektu).
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from db import SessionLocal, engine
from models import Company
from utils.seed_demo_data import COMPANY_CONTACTS


def _alter_columns() -> None:
    stmts = [
        "ALTER TABLE companies ADD COLUMN IF NOT EXISTS contact_phone TEXT",
        "ALTER TABLE companies ADD COLUMN IF NOT EXISTS contact_email TEXT",
    ]
    with engine.begin() as conn:
        for s in stmts:
            conn.execute(text(s))


def _contact_for_row_index(i: int) -> tuple[str, str]:
    if i < len(COMPANY_CONTACTS):
        return COMPANY_CONTACTS[i]
    n = i + 1
    return (
        f"+48 22 555 {n:02d} {n:02d}",
        f"kontakt{n}@firma.demo",
    )


def _fill_contacts(session: Session) -> tuple[int, int]:
    companies = list(session.scalars(select(Company).order_by(Company.id)).all())
    updated = 0
    for i, co in enumerate(companies):
        phone, email = _contact_for_row_index(i)
        if co.contact_phone != phone or co.contact_email != email:
            co.contact_phone = phone
            co.contact_email = email
            updated += 1
    session.commit()
    return len(companies), updated


def main() -> None:
    print("1/2 Migracja kolumn (contact_phone, contact_email)…")
    _alter_columns()
    print("   OK.")

    print("2/2 Uzupełnianie kontaktów dla firm…")
    with SessionLocal() as session:
        total, updated = _fill_contacts(session)
    print(f"   OK: {total} firm w bazie, zaktualizowano wpisy: {updated}.")
    print("Gotowe.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Błąd: {e}", file=sys.stderr)
        raise SystemExit(1) from e
