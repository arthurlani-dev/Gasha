import os
import sys
import time
import random
import secrets
from urllib.parse import urlencode

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv

# Permite importar database/database.py a partir da raiz do projeto,
# já que este arquivo mora em site/app.py
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from database.database import (
    criar_tabelas,
    criar_usuario,
    pegar_perfil,
    pegar_estado_daily,
    registrar_claim_diario,
    pegar_estatisticas,
)


load_dotenv()

# Garante que as tabelas existem mesmo se o site subir antes do bot
# (CREATE TABLE IF NOT EXISTS — não apaga nada que já exista)
criar_tabelas()

def _env(key: str, default: str | None = None) -> str | None:
    """Lê uma env var e remove espaços/quebras de linha acidentais
    (ex: valor colado com espaço extra no painel do Railway, ou um
    arquivo .env salvo com final de linha CRLF no Windows — ambos
    geram um caractere invisível grudado no valor e quebram a URL)."""
    valor = os.getenv(key, default)
    return valor.strip() if valor is not None else None


CLIENT_ID = _env("DISCORD_CLIENT_ID")
CLIENT_SECRET = _env("DISCORD_CLIENT_SECRET")
REDIRECT_URI = _env("DISCORD_REDIRECT_URI")
SESSION_SECRET = _env("SESSION_SECRET_KEY")

# Falha alto e claro no boot se essenciais para o login com Discord
# estiverem faltando, em vez de deixar o erro estourar só quando
# alguém clicar em "Sign in with Discord".
_faltando = [
    nome for nome, valor in (
        ("DISCORD_CLIENT_ID", CLIENT_ID),
        ("DISCORD_CLIENT_SECRET", CLIENT_SECRET),
        ("DISCORD_REDIRECT_URI", REDIRECT_URI),
        ("SESSION_SECRET_KEY", SESSION_SECRET),
    ) if not valor
]
if _faltando:
    print(
        f"[gasha] AVISO: variáveis de ambiente ausentes/vazias: {', '.join(_faltando)}. "
        "O login com Discord (/auth/discord/login) vai falhar até isso ser configurado."
    )
if REDIRECT_URI and not REDIRECT_URI.startswith(("http://", "https://")):
    print(
        f"[gasha] AVISO: DISCORD_REDIRECT_URI está sem o esquema (http/https): {REDIRECT_URI!r}. "
        "Corrija a variável no Railway para começar com 'https://'. "
        "Por segurança o app vai completar com https:// automaticamente por enquanto, "
        "mas isso só funciona se o valor cadastrado no Discord Developer Portal também "
        "tiver https:// na frente."
    )
    REDIRECT_URI = f"https://{REDIRECT_URI}"

COOLDOWN_SEGUNDOS = int(os.getenv("COOLDOWN_SEGUNDOS", 24 * 60 * 60))   # 24h
JANELA_STREAK_SEGUNDOS = int(os.getenv("JANELA_STREAK_SEGUNDOS", 48 * 60 * 60))  # 48h
PIXELS_MIN = int(os.getenv("PIXELS_MIN", 20))
PIXELS_MAX = int(os.getenv("PIXELS_MAX", 60))

DISCORD_API = "https://discord.com/api"


app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET)

BASE_DIR = os.path.dirname(__file__)
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


def avatar_url(user_id: str, avatar_hash: str | None) -> str | None:
    if not avatar_hash:
        return None
    return f"https://cdn.discordapp.com/avatars/{user_id}/{avatar_hash}.png"


def invite_url() -> str:
    """Link oficial de convite do bot (botão 'Add to Discord' do site)."""
    return (
        "https://discord.com/oauth2/authorize"
        "?client_id=1534767598317731893"
        "&permissions=139855211584"
        "&integration_type=0"
        "&scope=bot+applications.commands"
    )


# ---------------------------------------------------------------------------
# Páginas
# ---------------------------------------------------------------------------

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(request, "index.html", {"invite_url": invite_url()})


@app.get("/daily")
async def daily_page(request: Request):
    return templates.TemplateResponse(request, "daily.html", {"invite_url": invite_url()})


# ---------------------------------------------------------------------------
# Autenticação (Discord OAuth2)
# ---------------------------------------------------------------------------

@app.get("/auth/discord/login")
async def login():
    state = secrets.token_urlsafe(16)

    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "identify",
        "state": state,
    }
    url = f"{DISCORD_API}/oauth2/authorize?{urlencode(params)}"

    return RedirectResponse(url)


@app.get("/auth/discord/callback")
async def callback(request: Request, code: str | None = None):
    if not code:
        return RedirectResponse("/daily")

    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            f"{DISCORD_API}/oauth2/token",
            data={
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": REDIRECT_URI,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token_data = token_resp.json()
        access_token = token_data.get("access_token")

        if not access_token:
            return RedirectResponse("/daily")

        user_resp = await client.get(
            f"{DISCORD_API}/users/@me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        user_data = user_resp.json()

    user_id = int(user_data["id"])
    criar_usuario(user_id)

    request.session["usuario"] = {
        "id": str(user_id),
        "username": user_data.get("username", "usuario"),
        "avatarUrl": avatar_url(str(user_id), user_data.get("avatar")),
    }

    return RedirectResponse("/daily")


@app.get("/api/auth/me")
async def auth_me(request: Request):
    usuario = request.session.get("usuario")
    if not usuario:
        return JSONResponse({"erro": "Não autenticado"}, status_code=401)
    return JSONResponse(usuario)


@app.post("/api/auth/logout")
async def auth_logout(request: Request):
    request.session.clear()
    return JSONResponse({"sucesso": True})


# ---------------------------------------------------------------------------
# Recompensa diária
# ---------------------------------------------------------------------------

def _status_daily(user_id: int):
    estado = pegar_estado_daily(user_id)

    if estado is None:
        criar_usuario(user_id)
        estado = (0, 0, 0)

    pixels, ultimo_clique, streak_atual = estado
    agora = int(time.time())

    if ultimo_clique:
        restante = COOLDOWN_SEGUNDOS - (agora - ultimo_clique)
    else:
        restante = 0

    next_claim_at = (ultimo_clique + COOLDOWN_SEGUNDOS) * 1000 if restante > 0 else None

    # Se passou da janela de streak sem coletar, a sequência quebrou
    if ultimo_clique and (agora - ultimo_clique) > JANELA_STREAK_SEGUNDOS:
        streak_exibido = 0
    else:
        streak_exibido = streak_atual

    claimed_days = [i < streak_exibido for i in range(7)]

    return {
        "balance": pixels,
        "nextClaimAt": next_claim_at,
        "streak": streak_exibido,
        "claimedDays": claimed_days,
    }


@app.get("/api/daily/status")
async def daily_status(request: Request):
    usuario = request.session.get("usuario")
    if not usuario:
        return JSONResponse({"erro": "Não autenticado"}, status_code=401)

    return JSONResponse(_status_daily(int(usuario["id"])))


@app.post("/api/daily/claim")
async def daily_claim(request: Request):
    usuario = request.session.get("usuario")
    if not usuario:
        return JSONResponse({"erro": "Não autenticado"}, status_code=401)

    user_id = int(usuario["id"])
    estado = pegar_estado_daily(user_id)

    if estado is None:
        criar_usuario(user_id)
        estado = (0, 0, 0)

    pixels_atuais, ultimo_clique, streak_atual = estado
    agora = int(time.time())

    if ultimo_clique:
        restante = COOLDOWN_SEGUNDOS - (agora - ultimo_clique)
        if restante > 0:
            return JSONResponse(
                {"erro": "Cooldown ativo", "segundosRestantes": restante},
                status_code=409,
            )

    if ultimo_clique and (agora - ultimo_clique) <= JANELA_STREAK_SEGUNDOS:
        novo_streak = (streak_atual % 7) + 1
    else:
        novo_streak = 1

    pixels_ganhos = random.randint(PIXELS_MIN, PIXELS_MAX)
    registrar_claim_diario(user_id, agora, pixels_ganhos, novo_streak)

    novo_saldo = pixels_atuais + pixels_ganhos
    next_claim_at = (agora + COOLDOWN_SEGUNDOS) * 1000
    claimed_days = [i < novo_streak for i in range(7)]

    return JSONResponse({
        "amount": pixels_ganhos,
        "balance": novo_saldo,
        "nextClaimAt": next_claim_at,
        "streak": novo_streak,
        "claimedDays": claimed_days,
    })


# ---------------------------------------------------------------------------
# Estatísticas reais (seção "Em números" da home)
# ---------------------------------------------------------------------------

@app.get("/api/stats")
async def stats():
    return JSONResponse(pegar_estatisticas())
