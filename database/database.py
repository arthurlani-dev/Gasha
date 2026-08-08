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

    # !secret — pergunta anônima que junta respostas e revela depois
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS secrets (
            id SERIAL PRIMARY KEY,
            guild_id BIGINT,
            channel_id BIGINT NOT NULL,
            autor_id BIGINT NOT NULL,
            pergunta TEXT NOT NULL,
            criado_em BIGINT NOT NULL,
            publica_em BIGINT NOT NULL,
            publicado BOOLEAN DEFAULT FALSE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS secret_respostas (
            id SERIAL PRIMARY KEY,
            secret_id INTEGER NOT NULL REFERENCES secrets(id) ON DELETE CASCADE,
            autor_id BIGINT NOT NULL,
            resposta TEXT NOT NULL,
            criado_em BIGINT NOT NULL,
            UNIQUE (secret_id, autor_id)
        )
    """)

    # !friend — amizades entre usuários (dupla sempre guardada ordenada)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS amizades (
            usuario_a BIGINT NOT NULL,
            usuario_b BIGINT NOT NULL,
            criado_em BIGINT NOT NULL,
            PRIMARY KEY (usuario_a, usuario_b)
        )
    """)

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
# !secret — pergunta anônima com respostas reveladas depois de um tempo
# ---------------------------------------------------------------------------

def criar_secret(guild_id, channel_id, autor_id, pergunta, criado_em, publica_em):
    """Cria um secret e retorna o id gerado."""
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO secrets (guild_id, channel_id, autor_id, pergunta, criado_em, publica_em)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id
        """,
        (guild_id, channel_id, autor_id, pergunta, criado_em, publica_em)
    )

    secret_id = cursor.fetchone()[0]

    conn.commit()
    cursor.close()
    conn.close()
    return secret_id


def pegar_secret(secret_id):
    """Retorna (id, channel_id, pergunta, publica_em, publicado) ou None."""
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, channel_id, pergunta, publica_em, publicado FROM secrets WHERE id = %s",
        (secret_id,)
    )

    resultado = cursor.fetchone()
    cursor.close()
    conn.close()
    return resultado


def adicionar_resposta_secret(secret_id, autor_id, resposta, criado_em):
    """Registra a resposta anônima. Retorna False se o usuário já tinha respondido."""
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO secret_respostas (secret_id, autor_id, resposta, criado_em)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (secret_id, autor_id) DO NOTHING
        """,
        (secret_id, autor_id, resposta, criado_em)
    )

    registrado = cursor.rowcount > 0

    conn.commit()
    cursor.close()
    conn.close()
    return registrado


def pegar_respostas_secret(secret_id):
    """Lista só o texto das respostas (nunca o autor) — é isso que garante o anonimato."""
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT resposta FROM secret_respostas WHERE secret_id = %s ORDER BY criado_em ASC",
        (secret_id,)
    )

    resultado = [linha[0] for linha in cursor.fetchall()]
    cursor.close()
    conn.close()
    return resultado


def pegar_secrets_pendentes(agora):
    """Secrets cujo horário de revelação já chegou e ainda não foram publicados."""
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, channel_id, pergunta FROM secrets WHERE publicado = FALSE AND publica_em <= %s",
        (agora,)
    )

    resultado = cursor.fetchall()
    cursor.close()
    conn.close()
    return resultado


def marcar_secret_publicado(secret_id):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE secrets SET publicado = TRUE WHERE id = %s",
        (secret_id,)
    )

    conn.commit()
    cursor.close()
    conn.close()


# ---------------------------------------------------------------------------
# !friend — amizades
# ---------------------------------------------------------------------------

def sao_amigos(user_id_1, user_id_2):
    """Verifica se dois usuários já são amigos (a dupla é sempre guardada ordenada)."""
    usuario_a, usuario_b = sorted((user_id_1, user_id_2))

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT 1 FROM amizades WHERE usuario_a = %s AND usuario_b = %s",
        (usuario_a, usuario_b)
    )

    resultado = cursor.fetchone()
    cursor.close()
    conn.close()
    return resultado is not None


def adicionar_amizade(user_id_1, user_id_2, criado_em):
    usuario_a, usuario_b = sorted((user_id_1, user_id_2))

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO amizades (usuario_a, usuario_b, criado_em)
        VALUES (%s, %s, %s)
        ON CONFLICT (usuario_a, usuario_b) DO NOTHING
        """,
        (usuario_a, usuario_b, criado_em)
    )

    conn.commit()
    cursor.close()
    conn.close()


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