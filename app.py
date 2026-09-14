import streamlit as st
from supabase import create_client

st.set_page_config(
    page_title="Kazimm Gestao", 
    page_icon="🏢",
    initial_sidebar_state="expanded"
    )

# 2. CSS CUSTOMIZADO GLOBAL
st.markdown("""
    <style>
    /* Corrigido: CSS para Centralizar a Logo de forma Robusta */
    div[data-testid="stImage"] img {
        display: block !important;
        margin-left: auto !important;
        margin-right: auto !important;
        margin-bottom: 15px !important;
    }

    /* 2. Botão Principal (Entrar) */
    div.stButton > button[kind="primary"] {
        background-color: #1E3A8A; /* Azul marinho */
        color: #FFFFFF;
        border: none;
        border-radius: 8px;
        font-weight: bold;
        font-size: 18px !important;
        padding: 10px;
        transition: background-color 0.3s ease;
    }

    /* 3. Efeito ao passar o mouse no botão (Hover) */
    div.stButton > button[kind="primary"]:hover {
        background-color: #2563EB; /* Azul de destaque */
        color: #FFFFFF;
    }

    /* 4. Títulos (st.title) */
    h1 {
        font-size: 26px !important;
    }

    /* 5. Subtítulos e Seções (st.subheader e h2/h3) */
    h2, h3 {
        font-size: 20px !important;
    }

    /* 6. Rótulos dos Campos ("E-mail", "Senha") */
    label[data-testid="stWidgetLabel"] p {
        font-size: 15px !important;
        font-weight: 600;
    }

    /* 7. Texto digitado nos campos */
    input {
        font-size: 16px !important;
    }

    /* 8. Legendas (st.caption) */
    [data-testid="stCaptionContainer"] p {
        font-size: 13px !important;
    }
    </style>
""", unsafe_allow_html=True)

# 1. CONEXÃO COM SUPABASE
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

# 2. CONTROLE DE SESSÃO
if 'user' not in st.session_state:
    st.session_state.user = None

# 3. FUNÇÕES DE LOGIN/LOGOUT
def login(email, password):
    try:
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        st.session_state.user = response.user
        st.rerun()
    except Exception:
        st.error("Login inválido. Verifique seu e-mail e senha.")

def logout():
    supabase.auth.sign_out()
    st.session_state.user = None
    st.rerun()

# 4. TELA DE LOGIN
def login_screen():
    #Cria 3 colunas e seleciona coluna central (col2)
    col1, col2, col3 = st.columns([1,2,1])

    with col2:
        #Logo Kazimm Gestão
        st.image("Logo.png", width=180)

        st.title("🔐 Kazimm Gestor Contabil")
        st.caption("Acesso restrito a clientes autorizados.")
    
        with st.form("login_form"):
            email = st.text_input("E-mail")
            senha = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar", type="primary", use_container_width=True):
                login(email, senha)
        st.caption("Versão - 1.01_a")
        
# 5. DEFINIÇÃO DAS PÁGINAS DO PORTAL
login_page = st.Page(login_screen, title="Login", icon="🔐")
gestor_page = st.Page("pages/1_Gestor_Contabil.py", title="Gestor Contábil", icon="📊")
contratos_page = st.Page("pages/2_Gerador_Contratos.py", title="Gerador de Contratos", icon="📝")

# 6. CONTROLE DE NAVEGAÇÃO DINÂMICO
if st.session_state.user is None:
    # Se deslogado: Oculta a barra lateral e exibe apenas a tela de login
    pg = st.navigation([login_page], position="hidden")
else:
    # Se logado: Exibe os dados do usuário, botão de sair e o menu de sistemas
    st.sidebar.write(f"👤 Logado como: **{st.session_state.user.email}**")
    if st.sidebar.button("Sair (Logout)"):
        logout()
    pg = st.navigation([gestor_page, contratos_page])

pg.run()