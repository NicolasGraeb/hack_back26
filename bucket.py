"""
Upload / odczyt obrazków firmy — Railway Bucket (S3-compatible).

Zmienne ze strony Credentials w Railway (lub referencje do bucketa):
  ENDPOINT, BUCKET, ACCESS_KEY_ID, SECRET_ACCESS_KEY, REGION (np. auto)
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path

# Dozwolone typy i max rozmiar (5 MB)
ALLOWED_IMAGE_TYPES: dict[str, str] = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}
MAX_IMAGE_BYTES = 5 * 1024 * 1024


def bucket_configured() -> bool:
    endpoint = os.getenv("ENDPOINT", "https://t3.storageapi.dev").strip() or os.getenv("BUCKET_ENDPOINT", "").strip()
    bucket = os.getenv("BUCKET", "spacious-pocket-axg1j1b4h").strip()
    ak = os.getenv("ACCESS_KEY_ID", "tid_LTXFkqZhqfKSWsB_QpqOorVbKvRgFyhtRtTRpgclXcurLpEyrG").strip()
    sk = os.getenv("SECRET_ACCESS_KEY", "tsec_YuOw1um+sijta-eMsIDAezGPtFzaWaDmjrSEvdddahRMGRWT65TfqZxkgEhknPutbXjbuC").strip()
    return bool(endpoint and bucket and ak and sk)


def _client():
    try:
        import boto3
    except ImportError as e:
        raise RuntimeError("Zainstaluj boto3: pip install boto3") from e

    endpoint = os.getenv("ENDPOINT", "https://t3.storageapi.dev").strip() or os.getenv("BUCKET_ENDPOINT", "").strip()
    bucket = os.getenv("BUCKET", "spacious-pocket-axg1j1b4h").strip()
    if not endpoint or not bucket:
        raise RuntimeError("Brak ENDPOINT lub BUCKET w środowisku.")

    region = os.getenv("REGION", "auto").strip() or "auto"
    return boto3.client(
        "s3",
        endpoint_url=endpoint.rstrip("/"),
        aws_access_key_id=os.getenv("ACCESS_KEY_ID", "tid_LTXFkqZhqfKSWsB_QpqOorVbKvRgFyhtRtTRpgclXcurLpEyrG").strip(),
        aws_secret_access_key=os.getenv("SECRET_ACCESS_KEY", "tsec_YuOw1um+sijta-eMsIDAezGPtFzaWaDmjrSEvdddahRMGRWT65TfqZxkgEhknPutbXjbuC").strip(),
        region_name=region,
    ), bucket


def upload_company_image(
    company_id: int,
    file_bytes: bytes,
    *,
    content_type: str,
    original_filename: str | None = None,
) -> str:
    """
    Wgrywa plik do bucketa. Zwraca klucz obiektu (zapisz w Company.image_url).
    """
    ct = content_type.split(";")[0].strip().lower()
    if ct not in ALLOWED_IMAGE_TYPES:
        raise ValueError(f"Niedozwolony typ pliku: {content_type}")
    if len(file_bytes) > MAX_IMAGE_BYTES:
        raise ValueError(f"Plik za duży (max {MAX_IMAGE_BYTES // (1024 * 1024)} MB).")

    ext = ALLOWED_IMAGE_TYPES[ct]
    if original_filename:
        suf = Path(original_filename).suffix.lower()
        if suf in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
            ext = suf if suf != ".jpeg" else ".jpg"

    key = f"companies/{company_id}/{uuid.uuid4().hex}{ext}"
    client, bucket = _client()
    client.put_object(
        Bucket=bucket,
        Key=key,
        Body=file_bytes,
        ContentType=ct,
    )
    return key


def presigned_get_url(object_key: str, *, expires_in: int = 3600) -> str:
    """Tymczasowy URL do odczytu prywatnego obiektu (np. przekierowanie z API)."""
    client, bucket = _client()
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": object_key},
        ExpiresIn=expires_in,
    )
