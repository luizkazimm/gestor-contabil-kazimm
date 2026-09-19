import streamlit as st
from supabase import create_client

st.set_page_config(
    page_title="Kazimm Gestao", 
    page_icon="🏢",
    initial_sidebar_state="expanded"
    )

# -----------------------------------------------------------------------------
# ESTILO ELEGANTE E PROPORCIONAL DA TELA DE LOGIN (APP.PY)
# -----------------------------------------------------------------------------
st.markdown("""
    <!-- Carregamento das Fontes Montserrat e Inter -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Montserrat:wght@600;700&display=swap" rel="stylesheet">

    <style>
    /* 1. TÍTULO PRINCIPAL DE LOGIN */
    h1, [data-testid="stMarkdownContainer"] h1, .stApp h1 {
        font-family: 'Montserrat', sans-serif !important;
        font-size: 1.35rem !important;
        font-weight: 700 !important;
        color: #0F172A !important;
        margin-bottom: 0.25rem !important;
        letter-spacing: -0.02em !important;
    }

    /* Subtítulo e descrições */
    p, [data-testid="stMarkdownContainer"] p {
        font-family: 'Inter', sans-serif !important;
        font-size: 0.85rem !important;
        color: #64748B !important;
    }

    /* 2. RÓTULOS DOS CAMPOS (E-mail / Senha) */
    label, [data-testid="stWidgetLabel"] p {
        font-family: 'Inter', sans-serif !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        color: #1E293B !important;
    }

    /* 3. CAIXAS DE DADOS (Com borda visível e fundo grafite suave) */
    div[data-baseweb="input"] {
        background-color: #F8FAFC !important;
        border: 1.5px solid #CBD5E1 !important;
        border-radius: 8px !important;
        transition: all 0.2s ease-in-out !important;
    }

    div[data-baseweb="input"]:focus-within {
        border-color: #1E3A8A !important;
        background-color: #FFFFFF !important;
        box-shadow: 0px 0px 0px 3px rgba(30, 58, 138, 0.15) !important;
    }

    /* 4. BOTÃO ENTRAR COM ALTURA FIXA E PROPORCIONAL (42px) */
    div.stButton > button, 
    div.stFormSubmitButton > button {
        background-color: #1E3A8A !important;
        color: #FFFFFF !important;
        border-radius: 8px !important;
        border: none !important;
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        height: 42px !important;
        min-height: 42px !important;
        max-height: 42px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        padding: 0 1rem !important;
        transition: all 0.25s ease-in-out !important;
    }

    /* Texto interno do botão em branco */
    div.stButton > button *, 
    div.stFormSubmitButton > button * {
        color: #FFFFFF !important;
    }

    /* Efeito de destaque no Hover */
    div.stButton > button:hover, 
    div.stFormSubmitButton > button:hover {
        background-color: #2563EB !important;
        color: #FFFFFF !important;
        box-shadow: 0px 4px 12px rgba(37, 99, 235, 0.35) !important;
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