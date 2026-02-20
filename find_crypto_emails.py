#!/usr/bin/env python3
import argparse
import base64
import html
import json
import os
import re
from pathlib import Path

import django
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from legacy_models.utils.secret_box import decrypt_file, encrypt_bytes, resolve_admin_password


PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_TOKEN_FILE = str(PROJECT_ROOT / "secrets" / "tecnoges.fausti@gmail.com.gmail.storage")
SCOPES = ["https://mail.google.com/"]

# Patrones típicos:
# - Dirección Ethereum (0x + 40 hex)
# - Cadenas hex largas (hashes/identificadores)
ETH_ADDRESS_RE = re.compile(r"\b0x[a-fA-F0-9]{40}\b")
LONG_HEX_RE = re.compile(r"\b[a-fA-F0-9]{48,128}\b")


def decode_body_part(part_body):
    data = part_body.get("data")
    if not data:
        return ""
    decoded = base64.urlsafe_b64decode(data.encode("utf-8"))
    return decoded.decode("utf-8", errors="ignore")


def extract_text(payload):
    mime_type = payload.get("mimeType", "")
    if mime_type in {"text/plain", "text/html"}:
        text = decode_body_part(payload.get("body", {}))
        if mime_type == "text/html":
            # Limpieza básica para poder buscar sobre texto.
            text = re.sub(r"<[^>]+>", " ", text)
            text = html.unescape(text)
        return text

    text_parts = []
    for part in payload.get("parts", []):
        text_parts.append(extract_text(part))
    return "\n".join(x for x in text_parts if x)


def find_crypto_tokens(text):
    matches = set()
    matches.update(ETH_ADDRESS_RE.findall(text))
    for token in LONG_HEX_RE.findall(text):
        # Evita duplicar la parte hexadecimal de una dirección ETH ya detectada.
        if not token.startswith("0x"):
            matches.add(token)
    return sorted(matches)


def get_header(headers, name):
    for h in headers:
        if h.get("name", "").lower() == name.lower():
            return h.get("value", "")
    return ""


def main():
    parser = argparse.ArgumentParser(
        description="Lista correos con posibles cadenas crypto hexadecimales."
    )
    parser.add_argument(
        "--token-file",
        default=DEFAULT_TOKEN_FILE,
        help="Ruta del token OAuth Gmail (.gmail.storage).",
    )
    parser.add_argument(
        "--token-file-enc",
        default=None,
        help="Ruta token cifrado (.enc). Si existe, se usa en prioridad.",
    )
    parser.add_argument("--admin-username", default=None, help="Usuario admin/staff para descifrar.")
    parser.add_argument("--admin-password", default=None, help="Password admin (si no, se pide por prompt).")
    parser.add_argument(
        "--max",
        type=int,
        default=200,
        help="Máximo de mensajes a revisar.",
    )
    parser.add_argument(
        "--query",
        default="",
        help="Filtro Gmail opcional (q=). Ej: newer_than:30d",
    )
    args = parser.parse_args()

    token_file = Path(args.token_file).expanduser()
    token_file_enc = Path(args.token_file_enc).expanduser() if args.token_file_enc else Path(str(token_file) + ".enc")
    using_encrypted = token_file_enc.exists()
    admin_password = None

    if using_encrypted:
        _, admin_password = resolve_admin_password(
            admin_username=args.admin_username,
            admin_password=args.admin_password,
        )
        token_json = decrypt_file(token_file_enc, admin_password).decode("utf-8")
        token_data = json.loads(token_json)
        creds = Credentials.from_authorized_user_info(token_data, SCOPES)
    else:
        if not token_file.exists():
            raise SystemExit(f"No existe token file: {token_file}")
        creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        if using_encrypted:
            token_file_enc.write_bytes(encrypt_bytes(creds.to_json().encode("utf-8"), admin_password))
        else:
            token_file.write_text(creds.to_json(), encoding="utf-8")

    service = build("gmail", "v1", credentials=creds)

    found = 0
    checked = 0
    request = service.users().messages().list(userId="me", q=args.query, maxResults=min(args.max, 500))
    response = request.execute()
    messages = response.get("messages", [])

    while messages and checked < args.max:
        for msg_meta in messages:
            if checked >= args.max:
                break
            checked += 1
            msg = (
                service.users()
                .messages()
                .get(userId="me", id=msg_meta["id"], format="full")
                .execute()
            )
            payload = msg.get("payload", {})
            text = extract_text(payload)
            tokens = find_crypto_tokens(text)
            if not tokens:
                continue

            headers = payload.get("headers", [])
            subject = get_header(headers, "Subject")
            sender = get_header(headers, "From")
            date = get_header(headers, "Date")

            found += 1
            print("=" * 90)
            print(f"Message ID: {msg.get('id')}")
            print(f"Date      : {date}")
            print(f"From      : {sender}")
            print(f"Subject   : {subject}")
            print("Matches   :")
            for token in tokens:
                print(f"  - {token}")

        if checked >= args.max:
            break
        next_token = response.get("nextPageToken")
        if not next_token:
            break
        request = service.users().messages().list(
            userId="me",
            q=args.query,
            pageToken=next_token,
            maxResults=min(args.max - checked, 500),
        )
        response = request.execute()
        messages = response.get("messages", [])

    print("-" * 90)
    print(f"Mensajes revisados: {checked}")
    print(f"Mensajes con matches crypto: {found}")


if __name__ == "__main__":
    main()
