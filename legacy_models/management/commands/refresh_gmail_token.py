from pathlib import Path
import os
import tempfile

from django.core.management.base import BaseCommand, CommandError
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from legacy_models.utils.secret_box import decrypt_file, encrypt_bytes, resolve_admin_password

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_TOKEN_FILE = str(PROJECT_ROOT / "secrets" / "tecnoges.fausti@gmail.com.gmail.storage")
SCOPES = ["https://mail.google.com/"]


class Command(BaseCommand):
    help = "Renueva/genera token OAuth de Gmail (plano o cifrado)."

    def add_arguments(self, parser):
        default_client_secret = sorted(PROJECT_ROOT.glob("client_secret*.json"))
        parser.add_argument(
            "--client-secret",
            default=str(default_client_secret[0]) if default_client_secret else str(PROJECT_ROOT / "client_secret.json"),
            help="Ruta al client_secret JSON plano.",
        )
        parser.add_argument("--client-secret-enc", default=None, help="Ruta al client_secret cifrado (.enc).")
        parser.add_argument("--token-file", default=DEFAULT_TOKEN_FILE, help="Ruta donde guardar token OAuth plano.")
        parser.add_argument("--token-file-enc", default=None, help="Ruta donde guardar token cifrado (.enc).")
        parser.add_argument("--write-encrypted", action="store_true", help="Forzar guardar token en formato cifrado.")
        parser.add_argument("--admin-username", default=None, help="Usuario admin/staff para descifrar/cifrar.")
        parser.add_argument("--admin-password", default=None, help="Password admin (si no, se pide por prompt).")
        parser.add_argument("--host", default="localhost", help="Host local para callback OAuth.")
        parser.add_argument("--port", type=int, default=8080, help="Puerto local para callback OAuth.")
        parser.add_argument("--open-browser", action="store_true", help="Abre navegador automaticamente.")
        parser.add_argument("--manual", action="store_true", help="Flujo manual: pega la URL final con code=...")

    def handle(self, *args, **options):
        client_secret = Path(options["client_secret"]).expanduser()
        token_file = Path(options["token_file"]).expanduser()
        client_secret_enc = Path(options["client_secret_enc"]).expanduser() if options["client_secret_enc"] else Path(str(client_secret) + ".enc")
        token_file_enc = Path(options["token_file_enc"]).expanduser() if options["token_file_enc"] else Path(str(token_file) + ".enc")

        use_client_secret_enc = client_secret_enc.exists()
        use_token_enc = token_file_enc.exists() or options["write_encrypted"]

        admin_password = None
        if use_client_secret_enc or use_token_enc:
            try:
                _, admin_password = resolve_admin_password(
                    admin_username=options["admin_username"],
                    admin_password=options["admin_password"],
                )
            except Exception as exc:
                raise CommandError(str(exc)) from exc

        temp_client_secret_path = None
        client_secret_for_flow = client_secret
        if use_client_secret_enc:
            try:
                plaintext = decrypt_file(client_secret_enc, admin_password)
            except Exception as exc:
                raise CommandError(f"No se pudo descifrar client_secret: {exc}") from exc
            with tempfile.NamedTemporaryFile(prefix="gmail_client_secret_", suffix=".json", delete=False) as tmp:
                tmp.write(plaintext)
                temp_client_secret_path = Path(tmp.name)
                client_secret_for_flow = temp_client_secret_path
        elif not client_secret.exists():
            raise CommandError(f"No existe client_secret JSON: {client_secret}")

        # Loopback OAuth usa http://localhost. oauthlib lo bloquea si no se habilita explícitamente.
        if options["host"] in {"localhost", "127.0.0.1"}:
            os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")

        try:
            flow = InstalledAppFlow.from_client_secrets_file(str(client_secret_for_flow), SCOPES)

            if options["manual"]:
                flow.redirect_uri = f"http://{options['host']}:{options['port']}/"
                auth_url, _ = flow.authorization_url(
                    access_type="offline",
                    prompt="consent",
                    include_granted_scopes="true",
                )
                self.stdout.write(self.style.WARNING("Abre esta URL en tu navegador y autoriza:"))
                self.stdout.write(auth_url)
                self.stdout.write("")
                self.stdout.write("Cuando termine, copia la URL final de redirección (la que contiene ?code=...) y pégala aquí.")
                auth_response = input("URL final: ").strip()
                if not auth_response:
                    raise CommandError("No se recibió URL de redirección.")
                flow.fetch_token(authorization_response=auth_response)
                creds = flow.credentials
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"Iniciando OAuth en http://{options['host']}:{options['port']}/ "
                        "(esperando callback)..."
                    )
                )
                self.stdout.write("Si no abre navegador, copia la URL que salga en consola y autorizala manualmente.")
                self.stdout.write("")
                creds = flow.run_local_server(
                    host=options["host"],
                    port=options["port"],
                    open_browser=options["open_browser"],
                    access_type="offline",
                    prompt="consent",
                )
        except Exception as exc:
            raise CommandError(f"No se pudo completar OAuth: {exc}") from exc
        finally:
            if temp_client_secret_path and temp_client_secret_path.exists():
                temp_client_secret_path.unlink(missing_ok=True)

        if use_token_enc:
            token_file_enc.parent.mkdir(parents=True, exist_ok=True)
            token_file_enc.write_bytes(encrypt_bytes(creds.to_json().encode("utf-8"), admin_password))
        else:
            token_file.parent.mkdir(parents=True, exist_ok=True)
            token_file.write_text(creds.to_json(), encoding="utf-8")

        try:
            service = build("gmail", "v1", credentials=creds)
            profile = service.users().getProfile(userId="me").execute()
        except Exception as exc:
            raise CommandError(f"Token guardado pero fallo la prueba Gmail API: {exc}") from exc

        self.stdout.write(self.style.SUCCESS("Token OAuth generado y guardado correctamente."))
        self.stdout.write(f"Cuenta autenticada: {profile.get('emailAddress', '(sin email)')}")
        if use_token_enc:
            self.stdout.write(f"Token cifrado: {token_file_enc}")
        else:
            self.stdout.write(f"Token plano: {token_file}")
