from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from legacy_models.utils.secret_box import encrypt_file, resolve_admin_password

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_TOKEN_FILE = str(PROJECT_ROOT / "secrets" / "tecnoges.fausti@gmail.com.gmail.storage")


class Command(BaseCommand):
    help = "Cifra secretos de Gmail con la password del admin y genera archivos .enc."

    def add_arguments(self, parser):
        default_client_secret = sorted(PROJECT_ROOT.glob("client_secret*.json"))
        parser.add_argument("--admin-username", default=None, help="Usuario admin/staff de Django.")
        parser.add_argument("--admin-password", default=None, help="Password admin (opcional, si no se pide por prompt).")
        parser.add_argument(
            "--client-secret",
            default=str(default_client_secret[0]) if default_client_secret else str(PROJECT_ROOT / "client_secret.json"),
            help="Ruta al client_secret JSON en texto plano.",
        )
        parser.add_argument("--token-file", default=DEFAULT_TOKEN_FILE, help="Ruta al token .gmail.storage en texto plano.")
        parser.add_argument("--client-secret-enc", default=None, help="Salida cifrada para client_secret (por defecto: <client-secret>.enc).")
        parser.add_argument("--token-file-enc", default=None, help="Salida cifrada para token (por defecto: <token-file>.enc).")

    def handle(self, *args, **options):
        try:
            username, password = resolve_admin_password(
                admin_username=options["admin_username"],
                admin_password=options["admin_password"],
            )
        except Exception as exc:
            raise CommandError(str(exc)) from exc

        client_secret = Path(options["client_secret"]).expanduser()
        token_file = Path(options["token_file"]).expanduser()
        client_secret_enc = Path(options["client_secret_enc"]).expanduser() if options["client_secret_enc"] else Path(str(client_secret) + ".enc")
        token_file_enc = Path(options["token_file_enc"]).expanduser() if options["token_file_enc"] else Path(str(token_file) + ".enc")

        if not client_secret.exists():
            raise CommandError(f"No existe client_secret plano: {client_secret}")
        if not token_file.exists():
            raise CommandError(f"No existe token plano: {token_file}")

        encrypt_file(client_secret, client_secret_enc, password)
        encrypt_file(token_file, token_file_enc, password)

        self.stdout.write(self.style.SUCCESS("Secretos cifrados correctamente."))
        self.stdout.write(f"Admin validado: {username}")
        self.stdout.write(f"Client secret cifrado: {client_secret_enc}")
        self.stdout.write(f"Token cifrado: {token_file_enc}")
        self.stdout.write(
            self.style.WARNING(
                "Recuerda excluir/retirar los archivos planos antes de subir a GitHub."
            )
        )
