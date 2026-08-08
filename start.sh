#!/usr/bin/env bash
set -e

echo "===== DIAGNÓSTICO TEMPORÁRIO ====="
echo "--- pwd ---"
pwd
echo "--- ls -la /app ---"
ls -la /app || echo "/app não existe"
echo "--- ls -la /app/database ---"
ls -la /app/database || echo "/app/database não existe"
echo "--- sys.path do Python ---"
python -c "import sys; [print(p) for p in sys.path]"
echo "--- tentando importar database.database manualmente ---"
python -c "import database; print('database encontrado em:', database.__file__ if hasattr(database, \"__file__\") else database.__path__)"
echo "===== FIM DO DIAGNÓSTICO ====="

# Roda o bot do Discord em segundo plano
python main.py &
BOT_PID=$!

# Se o container for encerrado, mata o bot junto (evita processo órfão)
trap "kill $BOT_PID 2>/dev/null" EXIT

# Roda o site, escutando na porta que a plataforma definir (Railway injeta $PORT)
exec python -m uvicorn web.app:app --host 0.0.0.0 --port "${PORT:-8000}"