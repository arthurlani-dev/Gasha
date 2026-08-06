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
        """
        INSERT OR IGNORE INTO usuarios (id)
        VALUES (?)
        """,
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
        """
        UPDATE usuarios
        SET xp = xp + ?
        WHERE id = ?
        """,
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