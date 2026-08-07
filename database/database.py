import sqlite3


DATABASE = "database/bot.db"


def conectar():
    conn = sqlite3.connect(DATABASE)
    # WAL permite bot e site (FastAPI) acessarem o banco ao mesmo tempo sem travar
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def criar_tabelas():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY,
            level INTEGER DEFAULT 1,
            xp INTEGER DEFAULT 0,
            pixels INTEGER DEFAULT 0,
            conquistas TEXT DEFAULT '',
            ultimo_clique_site INTEGER DEFAULT 0,
            streak_atual INTEGER DEFAULT 0
        )
    """)

    # Contadores globais do site (servidores, comandos executados, etc.)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS estatisticas (
            chave TEXT PRIMARY KEY,
            valor INTEGER DEFAULT 0
        )
    """)

    for chave in ("servidores", "comandos_executados"):
        cursor.execute(
            "INSERT OR IGNORE INTO estatisticas (chave, valor) VALUES (?, 0)",
            (chave,)
        )

    conn.commit()
    conn.close()

    _migrar_colunas()


def _migrar_colunas():
    """Adiciona colunas novas em bancos já existentes, sem apagar dados."""
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(usuarios)")
    colunas = [linha[1] for linha in cursor.fetchall()]

    if "ultimo_clique_site" not in colunas:
        cursor.execute(
            "ALTER TABLE usuarios ADD COLUMN ultimo_clique_site INTEGER DEFAULT 0"
        )

    if "streak_atual" not in colunas:
        cursor.execute(
            "ALTER TABLE usuarios ADD COLUMN streak_atual INTEGER DEFAULT 0"
        )

    conn.commit()
    conn.close()


def criar_usuario(user_id):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT OR IGNORE INTO usuarios (id) VALUES (?)",
        (user_id,)
    )

    conn.commit()
    conn.close()


def pegar_perfil(user_id):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, level, xp, pixels, conquistas
        FROM usuarios
        WHERE id = ?
        """,
        (user_id,)
    )

    resultado = cursor.fetchone()
    conn.close()
    return resultado


def adicionar_xp(user_id, quantidade):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE usuarios SET xp = xp + ? WHERE id = ?",
        (quantidade, user_id)
    )

    conn.commit()
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
        WHERE id = ?
        """,
        (user_id,)
    )

    conn.commit()
    conn.close()


def adicionar_pixels(user_id, quantidade):
    """Usado tanto pelo bot quanto pelo site."""
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE usuarios SET pixels = pixels + ? WHERE id = ?",
        (quantidade, user_id)
    )

    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Recompensa diária (/daily)
# ---------------------------------------------------------------------------

def pegar_estado_daily(user_id):
    """Retorna (pixels, ultimo_clique_site, streak_atual) ou None se o usuário não existir."""
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT pixels, ultimo_clique_site, streak_atual FROM usuarios WHERE id = ?",
        (user_id,)
    )

    resultado = cursor.fetchone()
    conn.close()
    return resultado


def registrar_claim_diario(user_id, agora, pixels_ganhos, novo_streak):
    """Soma os pixels ganhos e grava o novo horário/streak do claim diário."""
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE usuarios
        SET pixels = pixels + ?,
            ultimo_clique_site = ?,
            streak_atual = ?
        WHERE id = ?
        """,
        (pixels_ganhos, agora, novo_streak, user_id)
    )

    conn.commit()
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
        INSERT INTO estatisticas (chave, valor) VALUES (?, ?)
        ON CONFLICT(chave) DO UPDATE SET valor = excluded.valor
        """,
        (chave, valor)
    )

    conn.commit()
    conn.close()


def incrementar_estatistica(chave, quantidade=1):
    """Soma ao valor atual de uma estatística (ex: +1 comando executado)."""
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE estatisticas SET valor = valor + ? WHERE chave = ?",
        (quantidade, chave)
    )

    conn.commit()
    conn.close()


def pegar_estatisticas():
    """Números reais exibidos na seção 'Em números' do site."""
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT chave, valor FROM estatisticas")
    dados = dict(cursor.fetchall())

    cursor.execute("SELECT COUNT(*), COALESCE(SUM(pixels), 0) FROM usuarios")
    total_usuarios, total_pixels = cursor.fetchone()

    conn.close()

    return {
        "servidores": dados.get("servidores", 0),
        "usuarios": total_usuarios,
        "comandos_executados": dados.get("comandos_executados", 0),
        "pixels_distribuidos": total_pixels,
    }
