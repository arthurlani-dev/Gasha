import os
import time
import random
import secrets

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from database.database import (
    criar_usuario,
    pegar_perfil,
    adicionar_pixels,
    pegar_ultimo_clique_site,
    registrar_clique_site,
)


load_dotenv()

CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI")
SESSION_SECRET = os.getenv("SESSION_SECRET_KEY")

COOLDOWN_SEGUNDOS = int(os.getenv("COOLDOWN_SEGUNDOS", 60 * 60 * 12))  # 12h padrão
PIXELS_MIN = int(os.getenv("PIXELS_MIN", 20))
PIXELS_MAX = int(os.getenv("PIXELS_MAX", 60))

DISCORD_API = "https://discord.com/api"


app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET)
templates = Jinja2Templates(directory="site/templates")


@app.get("/")
async def home(request: Request):
    usuario = request.session.get("usuario")
    dados = None

    if usuario:
        dados = pegar_perfil(usuario["id"])

    return templates.TemplateResponse(
        "index.html",
        {"request": request, "usuario": usuario, "dados": dados}
    )


@app.get("/login")
async def login():
    state = secrets.token_urlsafe(16)

    url = (
        f"{DISCORD_API}/oauth2/authorize"
        f"?client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=identify"
        f"&state={state}"
    )

    return RedirectResponse(url)


@app.get("/callback")
async def callback(request: Request, code: str = None):
    if not code:
        return RedirectResponse("/")

    async with httpx.AsyncClient() as client:
        # Troca o code por um access_token
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
            return JSONResponse({"erro": "Falha na autenticação"}, status_code=400)

        # Busca os dados do usuário logado
        user_resp = await client.get(
            f"{DISCORD_API}/users/@me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        user_data = user_resp.json()

    user_id = int(user_data["id"])
    criar_usuario(user_id)

    request.session["usuario"] = {
        "id": user_id,
        "username": user_data["username"],
        "avatar": user_data.get("avatar"),
    }

    return RedirectResponse("/")


@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/")


@app.post("/clicar")
async def clicar(request: Request):
    usuario = request.session.get("usuario")

    if not usuario:
        return JSONResponse({"erro": "Você precisa estar logado."}, status_code=401)

    user_id = usuario["id"]
    agora = int(time.time())

    ultimo_clique = pegar_ultimo_clique_site(user_id)
    restante = COOLDOWN_SEGUNDOS - (agora - ultimo_clique)

    if restante > 0:
        return JSONResponse(
            {"erro": "Cooldown ativo", "segundos_restantes": restante},
            status_code=429,
        )

    pixels_ganhos = random.randint(PIXELS_MIN, PIXELS_MAX)

    adicionar_pixels(user_id, pixels_ganhos)
    registrar_clique_site(user_id, agora)

    return JSONResponse({
        "sucesso": True,
        "pixels_ganhos": pixels_ganhos,
        "proximo_clique_em": COOLDOWN_SEGUNDOS,
    })