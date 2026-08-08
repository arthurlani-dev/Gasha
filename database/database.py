import os

import psycopg2
from dotenv import load_dotenv


load_dotenv()

# Railway injeta essa variável automaticamente quando o Postgres está
# vinculado ao mesmo projeto (Variables -> Add Reference -> Postgres.DATABASE_URL)
DATABASE_URL = os.getenv("DATABASE_URL")


def conectar():
    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL não configurada. No Railway, vá em Variables -> "
            "Add Reference -> selecione o serviço Postgres -> DATABASE_URL. "
            "Localmente, copie a connection string da aba 'Connect' do "
            "Postgres no Railway e coloque no seu .env."
        )
    return psycopg2.connect(DATABASE_URL)


def criar_tabelas():
    conn = conectar()
    cursor = conn.cursor()

    # BIGINT é obrigatório aqui: IDs do Discord (snowflakes) não cabem
    # em INTEGER de 32 bits do Postgres.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id BIGINT PRIMARY KEY,
            level INTEGER DEFAULT 1,
            xp INTEGER DEFAULT 0,
            pixels INTEGER DEFAULT 0,
            conquistas TEXT DEFAULT '',
            ultimo_clique_site BIGINT DEFAULT 0,
            streak_atual INTEGER DEFAULT 0,
            ultimo_work BIGINT DEFAULT 0
        )
    """)

    # Garante a coluna em bancos criados antes do comando !work existir
    cursor.execute("""
        ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS ultimo_work BIGINT DEFAULT 0
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS estatisticas (
            chave TEXT PRIMARY KEY,
            valor BIGINT DEFAULT 0
        )
    """)

    for chave in ("servidores", "comandos_executados"):
        cursor.execute(
            "INSERT INTO estatisticas (chave, valor) VALUES (%s, 0) "
            "ON CONFLICT (chave) DO NOTHING",
            (chave,)
        )

    conn.commit()
    cursor.close()
    conn.close()


def criar_usuario(user_id):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO usuarios (id) VALUES (%s) ON CONFLICT (id) DO NOTHING",
        (user_id,)
    )

    conn.commit()
    cursor.close()
    conn.close()


def pegar_perfil(user_id):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, level, xp, pixels, conquistas
        FROM usuarios
        WHERE id = %s
        """,
        (user_id,)
    )

    resultado = cursor.fetchone()
    cursor.close()
    conn.close()
    return resultado


def adicionar_xp(user_id, quantidade):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE usuarios SET xp = xp + %s WHERE id = %s",
        (quantidade, user_id)
    )

    conn.commit()
    cursor.close()
    conn.close()


def subir_level(user_id):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE usuarios
        SET level = level + 1,
            pixels = pixels + 100,
            xp = 0
        WHERE id = %s
        """,
        (user_id,)
    )

    conn.commit()
    cursor.close()
    conn.close()


def adicionar_pixels(user_id, quantidade):
    """Usado tanto pelo bot quanto pelo site."""
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE usuarios SET pixels = pixels + %s WHERE id = %s",
        (quantidade, user_id)
    )

    conn.commit()
    cursor.close()
    conn.close()


# ---------------------------------------------------------------------------
# Recompensa diária (/daily)
# ---------------------------------------------------------------------------

def pegar_estado_daily(user_id):
    """Retorna (pixels, ultimo_clique_site, streak_atual) ou None se o usuário não existir."""
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT pixels, ultimo_clique_site, streak_atual FROM usuarios WHERE id = %s",
        (user_id,)
    )

    resultado = cursor.fetchone()
    cursor.close()
    conn.close()
    return resultado


def registrar_claim_diario(user_id, agora, pixels_ganhos, novo_streak):
    """Soma os pixels ganhos e grava o novo horário/streak do claim diário."""
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE usuarios
        SET pixels = pixels + %s,
            ultimo_clique_site = %s,
            streak_atual = %s
        WHERE id = %s
        """,
        (pixels_ganhos, agora, novo_streak, user_id)
    )

    conn.commit()
    cursor.close()
    conn.close()


# ---------------------------------------------------------------------------
# Comando !work
# ---------------------------------------------------------------------------

def pegar_estado_work(user_id):
    """Retorna o timestamp do último !work ou None se o usuário não existir."""
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT ultimo_work FROM usuarios WHERE id = %s",
        (user_id,)
    )

    resultado = cursor.fetchone()
    cursor.close()
    conn.close()
    return resultado


def registrar_work(user_id, agora, pixels_ganhos):
    """Soma os pixels ganhos no !work e grava o novo horário de cooldown."""
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE usuarios
        SET pixels = pixels + %s,
            ultimo_work = %s
        WHERE id = %s
        """,
        (pixels_ganhos, agora, user_id)
    )

    conn.commit()
    cursor.close()
    conn.close()


# ---------------------------------------------------------------------------
# Leaderstats
# ---------------------------------------------------------------------------

def obter_leaderboard_pixels(limite=10):
    """Retorna os usuários com mais pixels: lista de (id, pixels)."""
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, pixels
        FROM usuarios
        WHERE pixels > 0
        ORDER BY pixels DESC
        LIMIT %s
        """,
        (limite,)
    )

    resultado = cursor.fetchall()
    cursor.close()
    conn.close()
    return resultado


# ---------------------------------------------------------------------------
# Estatísticas do site (seção "Em números")
# ---------------------------------------------------------------------------

def definir_estatistica(chave, valor):
    """Sobrescreve o valor de uma estatística (ex: contagem de servidores)."""
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO estatisticas (chave, valor) VALUES (%s, %s)
        ON CONFLICT (chave) DO UPDATE SET valor = EXCLUDED.valor
        """,
        (chave, valor)
    )

    conn.commit()
    cursor.close()
    conn.close()


def incrementar_estatistica(chave, quantidade=1):
    """Soma ao valor atual de uma estatística (ex: +1 comando executado)."""
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE estatisticas SET valor = valor + %s WHERE chave = %s",
        (quantidade, chave)
    )

    conn.commit()
    cursor.close()
    conn.close()


def pegar_estatisticas():
    """Números reais exibidos na seção 'Em números' do site."""
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT chave, valor FROM estatisticas")
    dados = dict(cursor.fetchall())

    cursor.execute("SELECT COUNT(*), COALESCE(SUM(pixels), 0) FROM usuarios")
    total_usuarios, total_pixels = cursor.fetchone()

    cursor.close()
    conn.close()

    return {
        "servidores": dados.get("servidores", 0),
        "usuarios": total_usuarios,
        "comandos_executados": dados.get("comandos_executados", 0),
        "pixels_distribuidos": total_pixels,
    }