# CuadernoDeNotas

Proyecto Django para gestión de cuaderno de notas, conectado a base PostgreSQL existente, con vistas de evaluaciones por grupo/trimestre.

## Requisitos

- Python 3.11+
- PostgreSQL accesible desde la red
- Entorno virtual en `.venv`

## Arranque rápido

```bash
cd ~/Documents/django-app/cuadernodenotas
source .venv/bin/activate
python manage.py runserver
```

## Menú principal de evaluaciones

- URL: `http://localhost:8000/evaluaciones/`
- Flujo: seleccionar `grupo` + `trimestre` -> abrir tabla de asignatura.

## Seguridad de secretos Gmail (GitHub-safe)

Este repo está preparado para no subir secretos en claro:

- `client_secret*.json` (plano) -> **no subir**
- `*.gmail.storage` (plano) -> **no subir**
- `*.enc` -> secretos cifrados permitidos en repo

### 1) Cifrar secretos con password de admin Django

```bash
cd ~/Documents/django-app/cuadernodenotas
source .venv/bin/activate
python manage.py seal_gmail_secrets --admin-username <usuario_staff>
```

Genera:

- `<client_secret>.enc`
- `<token>.enc`

### 2) Renovar token OAuth guardándolo cifrado

```bash
python manage.py refresh_gmail_token \
  --admin-username <usuario_staff> \
  --write-encrypted \
  --manual
```

### 3) Probar conexión Gmail usando secreto cifrado

```bash
python manage.py test_gmail_connection --admin-username <usuario_staff> --labels
```

## Detección de cadenas crypto en correos

Script:

```bash
python find_crypto_emails.py --max 200 --query "newer_than:365d" --admin-username <usuario_staff>
```

Busca direcciones/strings hex largas dentro de mensajes Gmail.

## Notas para GitHub

- `.gitignore` ya excluye secretos en claro.
- Antes de `git push`, confirma que no haya archivos sensibles:

```bash
git status
git ls-files | grep -E "client_secret|gmail.storage"
```

Si sale alguno en claro, quítalo del índice:

```bash
git rm --cached <archivo_sensible>
```
