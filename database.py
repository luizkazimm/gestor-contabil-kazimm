import psycopg2
from psycopg2 import pool
import streamlit as st
import pandas as pd
import json
import os

# -------------------------------------------------------------
# 1. CONEXÃO COM POOL PERSISTENTE (SUPABASE)
# -------------------------------------------------------------
@st.cache_resource
def _iniciar_pool():
    """Mantém até 10 conexões TCP/SSL permanentemente abertas na memória do Streamlit Cloud."""
    db = st.secrets["supabase"]
    return pool.ThreadedConnectionPool(
        minconn=1,
        maxconn=10,
        host=db["host"],
        port=int(db["port"]),
        dbname=db["dbname"],
        user=db["user"],
        password=db["password"],
        sslmode=db["sslmode"]
    )

class ConexaoPoolWrapper:
    """Intercepta o conn.close() para devolver a conexão ao pool em vez de destruí-la."""
    def __init__(self, pool_obj, raw_conn):
        self._pool = pool_obj
        self._conn = raw_conn

    def close(self):
        if self._conn is not None:
            try:
                self._conn.rollback()  # Garante limpeza de transações pendentes
            except Exception:
                pass
            self._pool.putconn(self._conn)
            self._conn = None

    def commit(self):
        return self._conn.commit()

    def rollback(self):
        return self._conn.rollback()

    def cursor(self, *args, **kwargs):
        return self._conn.cursor(*args, **kwargs)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __getattr__(self, name):
        return getattr(self._conn, name)

def get_connection():
    """Retira uma conexão pré-aquecida do pool em milissegundos."""
    p = _iniciar_pool()
    raw_conn = p.getconn()
    return ConexaoPoolWrapper(p, raw_conn)

# -------------------------------------------------------------
# 2. ESTRUTURA DO BANCO (Executado apenas na instalação)
# -------------------------------------------------------------
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

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id SERIAL PRIMARY KEY,
            nome TEXT NOT NULL,
            cnpj_cpf TEXT UNIQUE,
            regime TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS plano_contas (
            id SERIAL PRIMARY KEY,
            codigo TEXT UNIQUE NOT NULL,
            descricao TEXT NOT NULL,
            tipo TEXT NOT NULL
        )
    """)

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

create_tables = init_db

# -------------------------------------------------------------
# 3. LEITURAS EM CACHE (MEMÓRIA RAM ULTRARRÁPIDA)
# -------------------------------------------------------------

@st.cache_data(ttl=300)
def carregar_clientes(user_id):
    """Busca os clientes do usuário logado e guarda em cache."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, nome FROM clientes WHERE user_id = %s ORDER BY nome", (user_id,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

@st.cache_data(ttl=300)
def carregar_plano_contas(cliente_id=None):
    """Busca o plano de contas mantendo em memória."""
    conn = get_connection()
    try:
        query = """
            SELECT codigo, descricao, tipo 
            FROM plano_contas 
            WHERE cliente_id IS NULL OR cliente_id = %s 
            ORDER BY codigo ASC
        """
        return pd.read_sql_query(query, conn, params=(cliente_id,))
    finally:
        conn.close()

@st.cache_data(ttl=120)
def carregar_lancamentos(cliente_id):
    """Busca os lançamentos do cliente ativo em memória."""
    conn = get_connection()
    try:
        query = """
            SELECT id, data, conta_debito, conta_credito, valor, historico 
            FROM lancamentos 
            WHERE cliente_id = %s 
            ORDER BY data DESC
        """
        return pd.read_sql_query(query, conn, params=(cliente_id,))
    finally:
        conn.close()

@st.cache_data(ttl=120)
def carregar_provisoes_pendentes(cliente_id):
    """Busca contas a pagar pendentes do cliente ativo em memória."""
    conn = get_connection()
    try:
        query = "SELECT valor FROM provisoes WHERE cliente_id = %s AND status = 'Pendente'"
        return pd.read_sql_query(query, conn, params=(cliente_id,))
    finally:
        conn.close()

@st.cache_data(ttl=300)
def carregar_dados_cliente_ativo(cliente_id):
    """Busca dados cadastrais básicos do cliente ativo em memória."""
    conn = get_connection()
    try:
        query = "SELECT nome, regime, COALESCE(plano, 'gratis') AS plano FROM clientes WHERE id = %s"
        return pd.read_sql_query(query, conn, params=(cliente_id,))
    finally:
        conn.close()

def limpar_cache():
    """Invalida apenas o cache de movimentações contábeis."""
    carregar_lancamentos.clear()
    
@st.cache_data(ttl=300)
def carregar_todos_clientes_completos():
    """Busca a carteira completa de clientes para o painel admin e guarda na RAM."""
    conn = get_connection()
    try:
        query = """
            SELECT id, nome, cnpj_cpf, COALESCE(cpf, '') as cpf, regime, 
                   COALESCE(capital_social, 0.00) as capital_social, data_abertura,
                   COALESCE(limite_faturamento, 81000.00) as limite, 
                   COALESCE(telefone, '') as telefone, COALESCE(cnae_atividade, '') as cnae 
            FROM clientes ORDER BY nome ASC
        """
        return pd.read_sql_query(query, conn)
    finally:
        conn.close()
