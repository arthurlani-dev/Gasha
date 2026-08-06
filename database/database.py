import sqlite3


DATABASE = "database/bot.db"


def conectar():
    conn = sqlite3.connect(DATABASE)
    # WAL permite bot e site acessarem o banco ao mesmo tempo sem travar
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
            ultimo_clique_site INTEGER DEFAULT 0
        )
    """)

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


def pegar_ultimo_clique_site(user_id):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT ultimo_clique_site FROM usuarios WHERE id = ?",
        (user_id,)
    )

    resultado = cursor.fetchone()
    conn.close()

    return resultado[0] if resultado else 0


def registrar_clique_site(user_id, timestamp):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE usuarios SET ultimo_clique_site = ? WHERE id = ?",
        (timestamp, user_id)
    )

    conn.commit()
    conn.close()