"""
Wgrywa logo z c_logo/ do bucketa S3 i ustawia Company.image_url.

Konwencja nazw (slug = małe litery, jak w company_slugs):
  cloudara_1.png
  digmio_2.webp
  polionix_3.jpg
  reviver_4.png       ← Reviver AED (id 4)
  zentatez_5.png
  innovacini_6.webp
  magnerin_7.jpg
  bully_8.png
  reviver_9.webp      ← Reviver Gaming (id 9)
  lynkers_10.png

  python utils/upload_c_logos.py
"""

from __future__ import annotations

import mimetypes
import re
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
_UTILS = Path(__file__).resolve().parent
if str(_UTILS) not in sys.path:
    sys.path.insert(0, str(_UTILS))

from company_slugs import SLUG_BY_COMPANY_ID

from bucket import ALLOWED_IMAGE_TYPES, bucket_configured, upload_company_image
from db import SessionLocal
from models import Company

C_LOGO_DIR = _ROOT / "c_logo"

# cloudara_1 lub Cloudara_1 — ignorujemy wielkość liter w slug
_STEM_RE = re.compile(r"^([a-z0-9]+)_(\d+)$", re.IGNORECASE)


def _content_type(path: Path) -> str | None:
    mt, _ = mimetypes.guess_type(path.name)
    if mt and mt in ALLOWED_IMAGE_TYPES:
        return mt
    ext = path.suffix.lower()
    for ct, default_ext in ALLOWED_IMAGE_TYPES.items():
        if ext == default_ext or (ext == ".jpeg" and default_ext == ".jpg"):
            return ct
    return None


def _parse_stem(stem: str) -> tuple[str, int] | None:
    m = _STEM_RE.match(stem.strip())
    if not m:
        return None
    slug = m.group(1).lower()
    cid = int(m.group(2))
    return slug, cid


def main() -> None:
    if not bucket_configured():
        print(
            "Brak konfiguracji bucketa (ENDPOINT, BUCKET, ACCESS_KEY_ID, SECRET_ACCESS_KEY).",
            file=sys.stderr,
        )
        raise SystemExit(1)

    if not C_LOGO_DIR.is_dir():
        print(f"Brak folderu {C_LOGO_DIR}.", file=sys.stderr)
        raise SystemExit(1)

    files = sorted(
        p for p in C_LOGO_DIR.iterdir() if p.is_file() and not p.name.startswith(".")
    )
    if not files:
        print(f"Folder {C_LOGO_DIR} jest pusty.")
        return

    db = SessionLocal()
    ok, skipped = 0, 0
    try:
        for path in files:
            parsed = _parse_stem(path.stem)
            if not parsed:
                print(f"Pomijam (oczekiwane: slug_id, np. cloudara_1): {path.name}")
                skipped += 1
                continue
            slug, company_id = parsed
            expected = SLUG_BY_COMPANY_ID.get(company_id)
            if expected is None or slug != expected:
                print(
                    f"Pomijam — slug/id nie pasuje (id={company_id}, slug={slug!r}, "
                    f"oczekiwano {expected!r}): {path.name}"
                )
                skipped += 1
                continue

            company = db.get(Company, company_id)
            if company is None:
                print(f"Pomijam — brak firmy id={company_id}: {path.name}")
                skipped += 1
                continue

            ct = _content_type(path)
            if not ct:
                print(f"Pomijam — nierozpoznany typ: {path.name}")
                skipped += 1
                continue

            data = path.read_bytes()
            try:
                key = upload_company_image(
                    company_id,
                    data,
                    content_type=ct,
                    original_filename=path.name,
                )
            except ValueError as e:
                print(f"Błąd {path.name}: {e}")
                skipped += 1
                continue
            except Exception as e:
                print(f"Błąd uploadu {path.name}: {e}")
                skipped += 1
                continue

            company.image_url = key
            ok += 1
            print(f"OK {path.name} → firma id={company_id} → {key}")

        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    print(f"Zakończono: zaktualizowano {ok} firm, pominięto {skipped}.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Błąd: {e}", file=sys.stderr)
        raise SystemExit(1) from e
