import sqlite3


DATABASE = "database/bot.db"


def conectar():
    return sqlite3.connect(DATABASE)


def criar_tabelas():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY,
        level INTEGER DEFAULT 1,
        xp INTEGER DEFAULT 0,
        pixels INTEGER DEFAULT 0,
        conquistas TEXT DEFAULT ''
    )
    """)

    conn.commit()
    conn.close()


def criar_usuario(user_id):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM usuarios WHERE id = ?",
        (user_id,)
    )

    existe = cursor.fetchone()

    if not existe:
        cursor.execute(
            """
            INSERT INTO usuarios (id)
            VALUES (?)
            """,
            (user_id,)
        )

    conn.commit()
    conn.close()


def pegar_usuario(user_id):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT level, xp, pixels, conquistas
        FROM usuarios
        WHERE id = ?
        """,
        (user_id,)
    )

    dados = cursor.fetchone()

    conn.close()

    return dados