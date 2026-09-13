import json
import os
import sqlite3


def get_connection():
    return sqlite3.connect("gestor_contabil.db")


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Tabela de Clientes com a nova coluna de Regime Contábil
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cnpj_cpf TEXT UNIQUE NOT NULL,
            regime TEXT DEFAULT 'Partida Dupla (Contabilidade Completa)'
        )
    """)

    # Adiciona a coluna 'regime' caso o banco já exista sem ela
    cursor.execute("PRAGMA table_info(clientes)")
    colunas = [col[1] for col in cursor.fetchall()]
    if "regime" not in colunas:
        cursor.execute(
            "ALTER TABLE clientes ADD COLUMN regime TEXT DEFAULT 'Partida Dupla (Contabilidade Completa)'"
        )
        conn.commit()

    # 2. Tabela de Lançamentos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lancamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER,
            data TEXT,
            conta_debito TEXT,
            conta_credito TEXT,
            valor REAL,
            historico TEXT,
            FOREIGN KEY (cliente_id) REFERENCES clientes (id)
        )
    """)

    # 3. Tabela do Plano de Contas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS plano_contas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT NOT NULL,
            nome TEXT NOT NULL,
            tipo TEXT NOT NULL
        )
    """)

    cursor.execute(
        "SELECT COUNT(*), COUNT(DISTINCT codigo) FROM plano_contas"
    )
    res = cursor.fetchone()
    total = res[0] if res else 0
    distintos = res[1] if res else 0

    if total > distintos or total == 0:
        cursor.execute("DROP TABLE IF EXISTS plano_contas_temp")
        cursor.execute("""
            CREATE TABLE plano_contas_temp AS 
            SELECT codigo, nome, tipo 
            FROM plano_contas 
            GROUP BY codigo
        """)
        cursor.execute("DROP TABLE plano_contas")
        cursor.execute("""
            CREATE TABLE plano_contas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT UNIQUE NOT NULL,
                nome TEXT NOT NULL,
                tipo TEXT NOT NULL
            )
        """)
        cursor.execute("""
            INSERT OR IGNORE INTO plano_contas (codigo, nome, tipo) 
            SELECT codigo, nome, tipo FROM plano_contas_temp
        """)
        cursor.execute("DROP TABLE IF EXISTS plano_contas_temp")
        conn.commit()

    cursor.execute("SELECT COUNT(*) FROM plano_contas")
    if cursor.fetchone()[0] == 0 and os.path.exists(
        "plano_contas_inicial.json"
    ):
        with open("plano_contas_inicial.json", "r", encoding="utf-8") as f:
            contas = json.load(f)
            contas_tuplas = [
                (c["codigo"], c["nome"], c["tipo"]) for c in contas
            ]
            cursor.executemany(
                "INSERT OR IGNORE INTO plano_contas (codigo, nome, tipo) VALUES (?, ?, ?)",
                contas_tuplas,
            )
        conn.commit()

    conn.close()