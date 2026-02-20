import base64
import getpass
import json
import os
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from django.contrib.auth import authenticate, get_user_model
from django.core.exceptions import ValidationError


KDF_ITERATIONS = 390000


def _derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=KDF_ITERATIONS,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))


def encrypt_bytes(plaintext: bytes, password: str) -> bytes:
    salt = os.urandom(16)
    key = _derive_key(password, salt)
    fernet = Fernet(key)
    token = fernet.encrypt(plaintext)
    payload = {
        "v": 1,
        "iter": KDF_ITERATIONS,
        "salt": base64.urlsafe_b64encode(salt).decode("ascii"),
        "token": token.decode("ascii"),
    }
    return json.dumps(payload, indent=2).encode("utf-8")


def decrypt_bytes(cipher_payload: bytes, password: str) -> bytes:
    payload = json.loads(cipher_payload.decode("utf-8"))
    salt = base64.urlsafe_b64decode(payload["salt"].encode("ascii"))
    token = payload["token"].encode("ascii")
    key = _derive_key(password, salt)
    fernet = Fernet(key)
    try:
        return fernet.decrypt(token)
    except InvalidToken as exc:
        raise ValidationError("Password admin incorrecta o secreto cifrado inválido.") from exc


def encrypt_file(in_path: Path, out_path: Path, password: str) -> None:
    plaintext = in_path.read_bytes()
    encrypted = encrypt_bytes(plaintext, password)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(encrypted)


def decrypt_file(in_path: Path, password: str) -> bytes:
    return decrypt_bytes(in_path.read_bytes(), password)


def default_admin_username() -> str:
    user = get_user_model().objects.filter(is_superuser=True).order_by("id").first()
    if user:
        return user.get_username()
    user = get_user_model().objects.filter(is_staff=True).order_by("id").first()
    if user:
        return user.get_username()
    raise ValidationError("No existe usuario admin/staff en la base.")


def resolve_admin_password(admin_username: str | None = None, admin_password: str | None = None) -> tuple[str, str]:
    username = admin_username or default_admin_username()
    password = admin_password or getpass.getpass(f"Password admin ({username}): ")
    if not password:
        raise ValidationError("No se recibió password admin.")

    user = authenticate(username=username, password=password)
    if user is None or not user.is_staff:
        raise ValidationError("Credenciales admin inválidas (requiere usuario staff).")
    return username, password
