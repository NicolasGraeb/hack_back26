"""
Dodaje kolumny contact_phone, contact_email do istniejącej tabeli companies (PostgreSQL).

  python utils/migrate_company_contact.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from sqlalchemy import text

from db import engine


def main() -> None:
    stmts = [
        "ALTER TABLE companies ADD COLUMN IF NOT EXISTS contact_phone TEXT",
        "ALTER TABLE companies ADD COLUMN IF NOT EXISTS contact_email TEXT",
    ]
    with engine.begin() as conn:
        for s in stmts:
            conn.execute(text(s))
    print("OK: companies.contact_phone, companies.contact_email")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Błąd: {e}", file=sys.stderr)
        raise SystemExit(1) from e
