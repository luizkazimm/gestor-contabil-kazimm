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

# MÉTODO VERIFICADOR (Segurança do Sistema)
def validar_pertencimento_cliente(cliente_id, user_id):
    """
    Trava de segurança Multi-tenant:
    Retorna True se e somente se o cliente_id pertencer de fato ao user_id logado.
    """
    if not cliente_id or not user_id:
        return False
        
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT 1 FROM clientes WHERE id = %s AND user_id = %s LIMIT 1",
            (cliente_id, str(user_id))
        )
        return cursor.fetchone() is not None
    except Exception as e:
        print(f"Erro na validação de segurança de empresa: {e}")
        return False
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
    """Busca os dados cadastrais completos da empresa ativa e guarda em memória."""
    conn = get_connection()
    try:
        query = """
            SELECT 
                id, 
                nome, 
                nome as "Razão Social",
                cnpj_cpf, 
                cnpj_cpf as "CNPJ",
                cnpj_cpf as "CNPJ/CPF",
                COALESCE(cpf, '-') as "CPF Titular",
                regime,
                regime as "Regime Contábil",
                COALESCE(capital_social, 0.00) as "Capital Social",
                data_abertura as "Data Abertura",
                COALESCE(limite_faturamento, 81000.00) as limite,
                COALESCE(limite_faturamento, 81000.00) as "Limite Faturamento (R$)",
                COALESCE(telefone, '-') as "Telefone",
                COALESCE(cnae_atividade, '-') as "CNAE",
                COALESCE(cnae_atividade, '-') as "CNAE / Atividade",
                logo_base64,
                COALESCE(plano, 'gratis') AS plano
            FROM clientes 
            WHERE id = %s
        """
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

# ==============================================================
# GESTÃO DE HISTÓRICOS PADRÃO DE LANÇAMENTO (POSTGRESQL NATIVO)
# ==============================================================
@st.cache_data(ttl=300)
def carregar_historicos_padrao(cliente_id=None):
    """
    Retorna a lista de textos de históricos padrão.
    Busca modelos globais do sistema e modelos criados pela empresa ativa.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        query = """
            SELECT texto_padrao 
            FROM historicos_padrao 
            WHERE cliente_id IS NULL OR cliente_id = %s 
            ORDER BY descricao ASC
        """
        cursor.execute(query, (cliente_id,))
        linhas = cursor.fetchall()
        
        modelos_banco = [linha[0] for linha in linhas if linha[0]]
        
        # Opção inicial padrão + modelos reais do banco
        return ["Digitar Histórico do Zero"] + modelos_banco
    except Exception as e:
        print(f"Erro ao carregar históricos padrão: {e}")
        # Fallback de segurança se a tabela não existir
        return [
            "Digitar Histórico do Zero",
            "Pg. Supermercado Premium de B.Roxo - NFc:",
            "Pg. Supermercado Real de Eden - NFc:",
            "Pg. Drogaria Ebenezer de Madureira - NFc",
            "Pg. Remar Hortifruti Ltda - NFc:",
            "Pg. Mercadinho Natural de B.Roxo - Recibo:",
            "Pg. Supermercados Feira Nova Ltda - NFc:",
            "Pg. Bazar Amigão de Madureita - NFc:"
        ]
    finally:
        cursor.close()
        conn.close()


def salvar_novo_historico_padrao(cliente_id=None, codigo="GERAL", descricao="", texto_padrao="", **kwargs):
    """Insere um novo modelo de histórico para a empresa ativa via PostgreSQL."""
    # Garante compatibilidade caso o parâmetro seja enviado como cliente_ativo_id
    if not cliente_id and "cliente_ativo_id" in kwargs:
        cliente_id = kwargs["cliente_ativo_id"]

    conn = get_connection()
    cursor = conn.cursor()
    try:
        query = """
            INSERT INTO historicos_padrao (cliente_id, codigo, descricao, texto_padrao)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(
            query, 
            (cliente_id, codigo.strip().upper(), descricao.strip(), texto_padrao.strip())
        )
        conn.commit()
        
        # Invalida o cache para recarregar o selectbox na hora
        carregar_historicos_padrao.clear()
        return True, "Histórico padrão salvo com sucesso!"
    except Exception as e:
        conn.rollback()
        return False, f"Erro ao cadastrar modelo: {e}"
    finally:
        cursor.close()
        conn.close()

        
# -------------------------------------------------------------
# 5. MÓDULO FISCAL & NFS-E (FOCUS NFE)
# -------------------------------------------------------------

@st.cache_data(ttl=300)
def carregar_config_fiscal(cliente_id):
    """Busca as configurações fiscais da empresa ativa na memória RAM."""
    conn = get_connection()
    try:
        query = """
            SELECT id, cliente_id, cnpj, razao_social, nome_fantasia, 
                   inscricao_municipal, regime_tributario, codigo_servico_padrao,
                   aliquota_iss, item_lista_servico, codigo_municipio
            FROM configuracoes_fiscais 
            WHERE cliente_id = %s 
            LIMIT 1
        """
        return pd.read_sql_query(query, conn, params=(cliente_id,))
    finally:
        conn.close()

@st.cache_data(ttl=60)
def carregar_notas_fiscais(cliente_id):
    """Busca o histórico de NFS-e emitidas para a empresa ativa."""
    conn = get_connection()
    try:
        query = """
            SELECT id, cliente_id, numero_nfse, chave_acesso, data_emissao, 
                   tomador_nome, tomador_documento, descricao_servico, 
                   valor_total, status, nuvem_fiscal_id AS referencia_externa, 
                   pdf_url, xml_url, mensagem_erro 
            FROM notas_fiscais 
            WHERE cliente_id = %s 
            ORDER BY data_emissao DESC
        """
        return pd.read_sql_query(query, conn, params=(cliente_id,))
    finally:
        conn.close()

def limpar_cache_fiscal():
    """Invalida cirurgicamente apenas o cache de configurações e notas fiscais."""
    carregar_config_fiscal.clear()
    carregar_notas_fiscais.clear()

# ==============================================================
# GESTÃO AUTOMÁTICA DA GUIA DAS-MEI (CONTAS A PAGAR)
# ==============================================================
SALARIO_MINIMO_VIGENTE = 1518.00  # Base oficial para apuração MEI (5% INSS)

def calcular_valor_das_mei(cnae_ou_atividade=""):
    """
    Calcula a contribuição mensal do MEI:
    - 5% do Salário Mínimo (INSS)
    - + R$ 1,00 de ICMS (Comércio/Indústria)
    - + R$ 5,00 de ISS (Prestação de Serviços)
    - + R$ 6,00 (Comércio + Serviços)
    """
    inss = SALARIO_MINIMO_VIGENTE * 0.05  # R$ 75,90
    icms = 0.00
    iss = 0.00
    
    txt = (cnae_ou_atividade or "").lower()
    
    # Identifica a atividade do MEI
    eh_comercio = any(k in txt for k in ["comércio", "comercio", "loja", "venda", "mercadoria", "indústria", "industria"])
    eh_servico = any(k in txt for k in ["serviço", "servico", "consultoria", "ti", "reparo", "manutenção", "transporte"])
    
    if eh_comercio and eh_servico:
        icms, iss = 1.00, 5.00
    elif eh_comercio:
        icms = 1.00
    else:
        # Padrão MEI ou Prestação de Serviços
        iss = 5.00
        
    return inss + icms + iss

def verificar_e_agendar_das_mensal(cliente_id, cnae_atividade=""):
    """
    Verifica se a Guia DAS do mês vigente já está agendada no Contas a Pagar.
    Se não estiver, cria automaticamente com vencimento fixo no dia 20.
    """
    from datetime import date
    hoje = date.today()
    mes_ano_ref = hoje.strftime("%m/%Y")
    descricao_guia = f"Guia DAS-MEI - Competência {mes_ano_ref}"
    data_vencimento = f"{hoje.year}-{hoje.month:02d}-20"
    
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # 1. Verifica se já existe a guia cadastrada para este mês
        cursor.execute(
            """
            SELECT id FROM provisoes 
            WHERE cliente_id = %s 
              AND tipo = 'Guia DAS' 
              AND descricao = %s
            LIMIT 1
            """,
            (cliente_id, descricao_guia)
        )
        existe = cursor.fetchone()
        
        # 2. Se não existir, agenda a obrigação automaticamente
        if not existe:
            valor_das = calcular_valor_das_mei(cnae_atividade)
            cursor.execute(
                """
                INSERT INTO provisoes (cliente_id, descricao, tipo, valor, data_vencimento, status)
                VALUES (%s, %s, 'Guia DAS', %s, %s, 'Pendente')
                """,
                (cliente_id, descricao_guia, valor_das, data_vencimento)
            )
            conn.commit()
            return True, valor_das
        return False, 0.0
    except Exception as e:
        conn.rollback()
        print(f"Aviso ao agendar DAS automático: {e}")
        return False, 0.0
    finally:
        cursor.close()
        conn.close()

# ==============================================================
# LEITURA DE NFS-e PARA COBRANÇA (COMPATIBILIDADE FOCUS NFE)
# ==============================================================
def carregar_nfse_cliente(cliente_id):
    """Retorna as notas fiscais emitidas para a empresa ativa prontas para cobrança."""
    conn = get_connection()
    try:
        query = """
            SELECT * FROM notas_fiscais
            WHERE cliente_id = %s
            ORDER BY id DESC
        """
        df = pd.read_sql_query(query, conn, params=(cliente_id,))
        
        if not df.empty:
            # 1. Mapeamento seguro do Valor da Nota
            if 'valor' not in df.columns:
                df['valor'] = df.get('valor_total', df.get('valor_servicos', 0.0))

            # 2. Mapeamento seguro da URL do PDF da Focus NFe
            if 'url_danfse' not in df.columns:
                df['url_danfse'] = df.get('pdf_url', df.get('caminho_danfe', ''))

            # 3. Mapeamento do Número da NFS-e
            if 'numero' not in df.columns:
                df['numero'] = df.get('numero_nfse', '')

            # 4. Mapeamento da Descrição do Serviço
            if 'discriminacao' not in df.columns:
                df['discriminacao'] = df.get('descricao_servico', 'Prestação de Serviços')

            # 5. Tratamento de campos de contato para não quebrar a tela com nulos
            for col in ['tomador_nome', 'tomador_email', 'tomador_telefone', 'status']:
                if col not in df.columns:
                    df[col] = ""
                else:
                    df[col] = df[col].fillna("")

        return df
    except Exception as e:
        print(f"Erro ao carregar notas fiscais para cobrança: {e}")
        return pd.DataFrame()
    finally:
        conn.close()
# ==============================================================
#verifica se o usuário logado já possui uma empresa configurada e pronta para operar
# ==============================================================
def obter_empresa_usuario(user_id: str, email_usuario: str = None):
    """
    Localiza a empresa do usuário logado por user_id ou por email (com auto-vínculo).
    Protegido contra ausência de colunas opcionais na tabela.
    """
    if not user_id and not email_usuario:
        return None
        
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # 1. Busca prioritária pelo user_id vinculado
        cursor.execute("SELECT * FROM clientes WHERE user_id = %s LIMIT 1", (str(user_id),))
        row = cursor.fetchone()
        
        # 2. Se não encontrou por user_id, verifica se a coluna 'email' existe na tabela antes de buscar
        if not row and email_usuario:
            cursor.execute(
                """
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'clientes' AND column_name = 'email'
                """
            )
            possui_coluna_email = cursor.fetchone() is not None
            
            if possui_coluna_email:
                cursor.execute("SELECT * FROM clientes WHERE email = %s LIMIT 1", (str(email_usuario).strip(),))
                row = cursor.fetchone()
                
                # Se achou pelo email, vincula o user_id no banco
                if row:
                    colunas_temp = [desc[0] for desc in cursor.description]
                    emp_temp = dict(zip(colunas_temp, row))
                    cli_id = emp_temp.get("id")
                    
                    cursor.execute(
                        "UPDATE clientes SET user_id = %s WHERE id = %s",
                        (str(user_id), cli_id)
                    )
                    conn.commit()
        
        if not row:
            return None
            
        colunas = [desc[0] for desc in cursor.description]
        empresa = dict(zip(colunas, row))
        
        empresa["nome_normalizado"] = (
            empresa.get("razao_social") 
            or empresa.get("nome") 
            or empresa.get("nome_fantasia") 
            or "Minha Empresa MEI"
        )
        empresa["regime_normalizado"] = (
            empresa.get("regime_contabil") 
            or empresa.get("regime") 
            or empresa.get("regime_tributario") 
            or "MEI (Microempreendedor Individual)"
        )
        empresa["plano_normalizado"] = empresa.get("plano") or "gratis"
        
        return empresa
        
    except Exception as e:
        print(f"Aviso ao consultar empresa: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

        
def salvar_empresa_onboarding(user_id: str, nome: str, cnpj_cpf: str, telefone: str, email: str):
    """
    Cadastra a empresa inicial do MEI vinculada ao seu user_id no primeiro acesso.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO clientes (user_id, nome, cnpj_cpf, regime, plano, email, telefone)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                str(user_id),
                nome.strip(),
                cnpj_cpf.strip(),
                "MEI (Microempreendedor Individual)",
                "gratis",
                email.strip(),
                telefone.strip()
            )
        )
        novo_id = cursor.fetchone()[0]
        conn.commit()
        return True, novo_id
    except Exception as e:
        conn.rollback()
        return False, f"Erro ao cadastrar empresa: {e}"
    finally:
        cursor.close()
        conn.close()