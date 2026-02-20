#!/usr/bin/env bash
set -euo pipefail

echo "[1/6] Comprobando Python..."
python3 --version

echo "[2/6] Creando entorno virtual (.venv) si no existe..."
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

echo "[3/6] Activando entorno virtual..."
source .venv/bin/activate

echo "[4/6] Actualizando pip..."
python -m pip install --upgrade pip

echo "[5/6] Instalando dependencias base..."
pip install \
  django \
  psycopg2-binary \
  google-api-python-client \
  google-auth \
  google-auth-oauthlib \
  cryptography

echo "[6/6] Verificando proyecto Django..."
python manage.py check

echo ""
echo "OK: Entorno preparado."
echo "Siguiente paso:"
echo "  source .venv/bin/activate"
echo "  python manage.py runserver"
