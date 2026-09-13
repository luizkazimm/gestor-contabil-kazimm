import psycopg2
import streamlit as st
import json
import os

def get_connection():
    # Puxa o bloco [supabase] do Secrets
    db = st.secrets["supabase"]

    # Conecta de forma nativa e segura, pedaço por pedaço
    return psycopg2.connect(
        host=db["host"],
        port=db["port"],
        dbname=db["dbname"],
        user=db["user"],
        password=db["password"],
        sslmode=db["sslmode"]
    )
def popular_plano_contas_inicial(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM plano_contas")
    total = cursor.fetchone()[0]

    if total == 0 and os.path.exists("plano_contas_inicial.json"):
        with open("plano_contas_inicial.json", "r", encoding="utf-8") as file:
            contas = json.load(file)
            
        for conta in contas:
            descricao = conta.get("descricao") or conta.get("nome")
            cursor.execute(
                """
                INSERT INTO plano_contas (codigo, descricao, tipo)
                VALUES (%s, %s, %s)
                """,
                (conta["codigo"], descricao, conta["tipo"])
            )
        conn.commit()
    cursor.close()    

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Cria a tabela de clientes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id SERIAL PRIMARY KEY,
            nome TEXT NOT NULL,
            cnpj_cpf TEXT UNIQUE,
            regime TEXT
        )
    """)

    # Cria a tabela de plano de contas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS plano_contas (
            id SERIAL PRIMARY KEY,
            codigo TEXT UNIQUE NOT NULL,
            descricao TEXT NOT NULL,
            tipo TEXT NOT NULL
        )
    """)

    # Cria a tabela de lançamentos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lancamentos (
            id SERIAL PRIMARY KEY,
            data TEXT NOT NULL,
            historico TEXT NOT NULL,
            valor REAL NOT NULL,
            conta_debito TEXT,
            conta_credito TEXT,
            cliente_id INTEGER REFERENCES clientes(id)
        )
    """)

    conn.commit()
    popular_plano_contas_inicial(conn)
    cursor.close()
    conn.close()


# Mantém suporte para ambos os nomes
create_tables = init_db
