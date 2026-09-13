import psycopg2
import streamlit as st


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
    conn.close()


# Mantém suporte para ambos os nomes
create_tables = init_db
