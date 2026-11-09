import streamlit as st
from supabase import create_client
from ui_theme import aplicar_estilo_moderno
from ui_theme import aplicar_estilo_moderno, ICONES

# -----------------------------------------------------------------------------
# CONFIGURAÇÃO GERAL DA PÁGINA
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Kazimm Gestão", 
    page_icon="assets/favicon.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Aplica o tema visual centralizado (ui_theme.py)
aplicar_estilo_moderno()


# -----------------------------------------------------------------------------
# 1. CONEXÃO COM SUPABASE
# -----------------------------------------------------------------------------
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()


# -----------------------------------------------------------------------------
# 2. CONTROLE DE SESSÃO
# -----------------------------------------------------------------------------
if 'user' not in st.session_state:
    st.session_state.user = None


# -----------------------------------------------------------------------------
# 3. FUNÇÕES DE AUTENTICAÇÃO (LOGIN / LOGOUT)
# -----------------------------------------------------------------------------
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


# -----------------------------------------------------------------------------
# 4. TELA DE LOGIN HARMONIZADA E CENTRALIZADA
# -----------------------------------------------------------------------------
def login_screen():
    # Proporção refinada [2.3, 1.4, 2.3] que encaixa o card perfeitamente em telas wide
    col_esq, col_card, col_dir = st.columns([2.3, 1.4, 2.3])

    with col_card:
        # A logo passa a preencher exatamente 100% da largura do formulário (sem sobras)
        st.image("Logo.png", use_container_width=True)

        # Cabeçalho integrado com a tipografia oficial Kazimm
        st.markdown(
            """
            <div style="text-align: center; margin-top: -6px; margin-bottom: 16px;">
                <h2 style="font-family: 'Montserrat', sans-serif; color: #007791; font-weight: 800; margin: 0; font-size: 1.35rem; letter-spacing: -0.4px;">
                    GESTOR CONTÁBIL
                </h2>
                <p style="color: #64748B; font-size: 0.82rem; margin-top: 4px;">
                    Acesso restrito a clientes autorizados.
                </p>
            </div>
            """, 
            unsafe_allow_html=True
        )
    
        # Formulário com borda limpa controlada pelo ui_theme
        with st.form("login_form", border=True):
            email = st.text_input("E-mail", placeholder="seu.email@kazimm.com.br")
            senha = st.text_input("Senha", type="password", placeholder="••••••••")
            
            st.write("")
            btn_entrar = st.form_submit_button("Entrar", type="primary", use_container_width=True)
            if btn_entrar:
                login(email, senha)

        # Rodapé da versão centralizado
        st.markdown(
            """
            <p style="text-align: center; color: #94A3B8; font-size: 0.74rem; margin-top: 10px;">
                Versão - 1.01_a
            </p>
            """, 
            unsafe_allow_html=True
        )


# -----------------------------------------------------------------------------
# 5. DEFINIÇÃO DAS PÁGINAS DO PORTAL (COM MATERIAL SYMBOLS)
# -----------------------------------------------------------------------------
login_page = st.Page(
    login_screen, 
    title="Login", 
    icon=":material/lock:"
)

gestor_page = st.Page(
    "pages/1_Gestor_Contabil.py", 
    title="Gestor Contábil", 
    icon=ICONES.get("contabil", ":material/account_balance:")
)

contratos_page = st.Page(
    "pages/2_Gerador_Contratos.py", 
    title="Gerador de Contratos", 
    icon=ICONES.get("contratos", ":material/contract:")
)

empregados_page = st.Page(
    "pages/3_Empregados_Previdencia.py", 
    title="Empregados / Previdência", 
    icon=ICONES.get("previdencia", ":material/badge:")
)

fiscal_page = st.Page(
    "pages/4_Gestor_Fiscal.py", 
    title="Gestor Fiscal", 
    icon=ICONES.get("fiscal", ":material/receipt_long:")
)

# -----------------------------------------------------------------------------
# 6. CONTROLE DE NAVEGAÇÃO DINÂMICO
# -----------------------------------------------------------------------------
if st.session_state.user is None:
    # Se deslogado: oculta navegação e renderiza tela de login central
    pg = st.navigation([login_page], position="hidden")
else:
    # Se logado: barra lateral com identificação do usuário e logout
    st.sidebar.write(f"👤 Logado como: **{st.session_state.user.email}**")
    if st.sidebar.button("Sair (Logout)"):
        logout()

    pg = st.navigation(
        [
            gestor_page,
            contratos_page,
            empregados_page,
            fiscal_page
        ],
        position="hidden"
    )
    
pg.run()