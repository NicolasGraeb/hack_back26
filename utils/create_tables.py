"""
Tworzy wszystkie tabele w Postgres (SQLAlchemy create_all).

  python utils/create_tables.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import models  # noqa: F401, E402
from db import engine
from models import Base


def main() -> None:
    Base.metadata.create_all(bind=engine)
    print("OK: tabele utworzone (create_all).")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Błąd: {e}")
        print("Sprawdź Postgres i DATABASE_URL (.env).")
        raise SystemExit(1) from e
