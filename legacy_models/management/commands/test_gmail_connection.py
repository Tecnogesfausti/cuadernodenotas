from pathlib import Path
import json

from django.core.management.base import BaseCommand, CommandError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from legacy_models.utils.secret_box import decrypt_file, encrypt_bytes, resolve_admin_password

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_TOKEN_FILE = str(PROJECT_ROOT / "secrets" / "tecnoges.fausti@gmail.com.gmail.storage")
SCOPES = ["https://mail.google.com/"]


class Command(BaseCommand):
    help = "Prueba conexion Gmail API usando token OAuth (plano o cifrado)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--token-file",
            default=DEFAULT_TOKEN_FILE,
            help="Ruta al token OAuth plano JSON.",
        )
        parser.add_argument(
            "--token-file-enc",
            default=None,
            help="Ruta token cifrado (.enc). Si existe, se usa en prioridad.",
        )
        parser.add_argument("--admin-username", default=None, help="Usuario admin/staff para descifrar.")
        parser.add_argument("--admin-password", default=None, help="Password admin (si no, se pide por prompt).")
        parser.add_argument(
            "--labels",
            action="store_true",
            help="Si se indica, lista las primeras 10 etiquetas de Gmail.",
        )

    def handle(self, *args, **options):
        token_file = Path(options["token_file"]).expanduser()
        token_file_enc = Path(options["token_file_enc"]).expanduser() if options["token_file_enc"] else Path(str(token_file) + ".enc")

        using_encrypted = token_file_enc.exists()
        admin_password = None

        if using_encrypted:
            try:
                _, admin_password = resolve_admin_password(
                    admin_username=options["admin_username"],
                    admin_password=options["admin_password"],
                )
            except Exception as exc:
                raise CommandError(str(exc)) from exc
        elif not token_file.exists():
            raise CommandError(f"No existe token file: {token_file}")

        try:
            if using_encrypted:
                token_json = decrypt_file(token_file_enc, admin_password).decode("utf-8")
                token_data = json.loads(token_json)
                creds = Credentials.from_authorized_user_info(token_data, SCOPES)
            else:
                creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)
        except Exception as exc:
            raise CommandError(f"No se pudo leer token OAuth: {exc}") from exc

        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as exc:
                raise CommandError(f"Token expirado y no se pudo refrescar: {exc}") from exc
            if using_encrypted:
                token_file_enc.write_bytes(encrypt_bytes(creds.to_json().encode("utf-8"), admin_password))
            else:
                token_file.write_text(creds.to_json(), encoding="utf-8")

        if not creds.valid:
            raise CommandError("Credenciales invalidas: requiere renovar consentimiento OAuth.")

        try:
            service = build("gmail", "v1", credentials=creds)
            profile = service.users().getProfile(userId="me").execute()
        except HttpError as exc:
            raise CommandError(f"Error Gmail API: {exc}") from exc
        except Exception as exc:
            raise CommandError(f"No se pudo conectar con Gmail API: {exc}") from exc

        email = profile.get("emailAddress", "(sin email)")
        total_messages = profile.get("messagesTotal", 0)
        total_threads = profile.get("threadsTotal", 0)

        self.stdout.write(self.style.SUCCESS("Conexion Gmail API OK"))
        self.stdout.write(f"Cuenta: {email}")
        self.stdout.write(f"Mensajes: {total_messages}")
        self.stdout.write(f"Hilos: {total_threads}")

        if options["labels"]:
            labels = service.users().labels().list(userId="me").execute().get("labels", [])
            self.stdout.write("Etiquetas (max 10):")
            for item in labels[:10]:
                self.stdout.write(f"- {item.get('name')}")
