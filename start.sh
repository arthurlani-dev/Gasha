#!/usr/bin/env bash
set -e

# Roda o bot do Discord em segundo plano
python main.py &
BOT_PID=$!

# Se o container for encerrado, mata o bot junto (evita processo órfão)
trap "kill $BOT_PID 2>/dev/null" EXIT

# Roda o site, escutando na porta que a plataforma definir (Railway injeta $PORT)
exec uvicorn web.app:app --host 0.0.0.0 --port "${PORT:-8000}"
