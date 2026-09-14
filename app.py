import streamlit as st
from supabase import create_client

st.set_page_config(page_title="Portal Kazimm", page_icon="🏢")

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
    st.title("🔐 Portal Kazimm")
    st.caption("Acesso restrito a clientes autorizados.")
    
    with st.form("login_form"):
        email = st.text_input("E-mail")
        senha = st.text_input("Senha", type="password")
        if st.form_submit_button("Entrar", type="primary"):
            login(email, senha)

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