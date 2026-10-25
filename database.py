import psycopg2
import streamlit as st
import pandas as pd
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
#Inicialização e carga inicial di banco
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

    # 1. Cria a tabela de clientes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id SERIAL PRIMARY KEY,
            nome TEXT NOT NULL,
            cnpj_cpf TEXT UNIQUE,
            regime TEXT
        )
    """)

    # 2. Cria a tabela de plano de contas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS plano_contas (
            id SERIAL PRIMARY KEY,
            codigo TEXT UNIQUE NOT NULL,
            descricao TEXT NOT NULL,
            tipo TEXT NOT NULL
        )
    """)

    # 3. Cria a tabela de lançamentos
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

    # 4. Configurações Fiscais (MEI / Certificado A1)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS configuracoes_fiscais (
            id SERIAL PRIMARY KEY,
            cnpj TEXT UNIQUE NOT NULL,
            razao_social TEXT NOT NULL,
            nome_fantasia TEXT,
            inscricao_municipal TEXT,
            regime_tributario TEXT DEFAULT 'MEI',
            nuvem_fiscal_empresa_id TEXT,
            certificado_ativo BOOLEAN DEFAULT FALSE,
            certificado_validade DATE
        )
    """)

# 5. Notas Fiscais (NFS-e)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notas_fiscais (
            id SERIAL PRIMARY KEY,
            numero_nfse TEXT,
            chave_acesso TEXT,
            data_emissao TIMESTAMPTZ DEFAULT NOW(),
            tomador_nome TEXT NOT NULL,
            tomador_documento TEXT NOT NULL,
            tomador_email TEXT,
            descricao_servico TEXT NOT NULL,
            codigo_servico TEXT NOT NULL,
            valor_total REAL NOT NULL,
            status TEXT DEFAULT 'processando',
            nuvem_fiscal_id TEXT,
            pdf_url TEXT,
            xml_url TEXT,
            mensagem_erro TEXT
        )
    """)

    conn.commit()
    popular_plano_contas_inicial(conn)
    cursor.close()
    conn.close()


# Mantém suporte para ambos os nomes
create_tables = init_db


# -------------------------------------------------------------
# 3. CONSULTAS OTIMIZADAS COM CACHE (Carregamento Ultrarrápido)
# -------------------------------------------------------------

@st.cache_data(ttl=300)
def carregar_clientes(user_id):
    """Busca os clientes do usuário logado e mantém em memória por 5 minutos."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT id, nome FROM clientes WHERE user_id = %s ORDER BY nome",
            (user_id,)
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

@st.cache_data(ttl=300)
def carregar_plano_contas(cliente_id=None):
    """Busca o plano de contas geral e do cliente ativo, mantendo em memória por 5 minutos."""
    conn = get_connection()
    try:
        query = """
            SELECT codigo, descricao, tipo 
            FROM plano_contas 
            WHERE cliente_id IS NULL OR cliente_id = %s 
            ORDER BY codigo ASC
        """
        df = pd.read_sql_query(query, conn, params=(cliente_id,))
        return df
    finally:
        conn.close()

@st.cache_data(ttl=120)
def carregar_lancamentos(cliente_id):
    """Carrega todos os lançamentos do MEI ativo em memória RAM."""
    conn = get_connection()
    try:
        query = """
            SELECT id, data, conta_debito, conta_credito, valor, historico 
            FROM lancamentos 
            WHERE cliente_id = %s 
            ORDER BY data DESC
        """
        df = pd.read_sql_query(query, conn, params=(cliente_id,))
        return df
    finally:
        conn.close()
#***********************************************************
# CARREGAR LANÇAMENTOS PELO CACHE
#***********************************************************
@st.cache_data(ttl=120)
def carregar_provisoes_pendentes(cliente_id):
    """Busca o valor das contas a pagar pendentes mantendo em memória."""
    conn = get_connection()
    try:
        query = "SELECT valor FROM provisoes WHERE cliente_id = %s AND status = 'Pendente'"
        df = pd.read_sql_query(query, conn, params=(cliente_id,))
        return df
    finally:
        conn.close()

def limpar_cache():
    """Limpa a memória para que alterações recentes apareçam na tela imediatamente."""
    st.cache_data.clear()