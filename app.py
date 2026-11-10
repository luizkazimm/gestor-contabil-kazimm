import streamlit as st
from supabase import create_client
from ui_theme import aplicar_estilo_moderno, ICONES
from database import obter_empresa_usuario, salvar_empresa_onboarding

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
        st.session_state["user_id"] = response.user.id  # <-- Garante a gravação do UUID
        st.rerun()
    except Exception:
        st.error("Login inválido. Verifique seu e-mail e senha.")
        
def logout():
    try:
        supabase.auth.sign_out()
    except Exception:
        pass
    # Limpa 100% das chaves da sessão para evitar vazamento entre contas
    for key in list(st.session_state.keys()):
        del st.session_state[key]
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
# 6. CONTROLE DE NAVEGAÇÃO DINÂMICO E ONBOARDING MEI
# -----------------------------------------------------------------------------
if st.session_state.user is None:
    # Deslogado: renderiza estritamente a tela de login
    pg = st.navigation([login_page], position="hidden")
    pg.run()
    
else:
    usuario_atual = st.session_state.user
    user_id = getattr(usuario_atual, "id", None) or st.session_state.get("user_id")
    user_email = getattr(usuario_atual, "email", None)
    
    # 1. Busca se o usuário possui empresa vinculada
    empresa = obter_empresa_usuario(user_id, email_usuario=user_email)
    
    # -------------------------------------------------------------------------
    # 2. SE NÃO POSSUI EMPRESA: TELA CENTRALIZADA COM IDENTIDADE KAZIMM
    # -------------------------------------------------------------------------
    if not empresa:
        # Barra lateral limpa apenas com identificação e logout
        st.sidebar.write(f"👤 Logado como: **{usuario_atual.email}**")
        st.sidebar.caption("🔒 Configuração Inicial Obrigatória")
        if st.sidebar.button("Sair (Logout)"):
            logout()

        # Proporção harmonizada para centralizar o card em telas desktop e mobile
        col_esq, col_card, col_dir = st.columns([1.8, 1.8, 1.8])

        with col_card:
            # 1. Logotipo oficial preenchendo o card
            st.image("Logo.png", use_container_width=True)

            # 2. Cabeçalho com a tipografia e paleta oficial do Kazimm Gestão
            st.markdown(
                """
                <div style="text-align: center; margin-top: -6px; margin-bottom: 20px;">
                    <h2 style="font-family: 'Montserrat', sans-serif; color: #007791; font-weight: 800; margin: 0; font-size: 1.25rem; letter-spacing: -0.3px;">
                        ATIVAR MEU NEGÓCIO
                    </h2>
                    <p style="color: #64748B; font-size: 0.82rem; margin-top: 5px; line-height: 1.35;">
                        Informe os dados da sua empresa para liberar o painel financeiro, emissão de notas e contratos.
                    </p>
                </div>
                """, 
                unsafe_allow_html=True
            )

            # 3. Card com borda integrada ao ui_theme
            with st.form("form_onboarding_inicial", border=True):
                nome_empresa = st.text_input(
                    "Razão Social ou Nome Fantasia *", 
                    placeholder="Ex: Casemiro Consultoria MEI"
                )
                
                doc_empresa = st.text_input(
                    "CNPJ ou CPF do Titular *", 
                    placeholder="00.000.000/0001-00"
                )
                
                tel_empresa = st.text_input(
                    "WhatsApp para Notificações *", 
                    placeholder="21999999999"
                )
                
                email_empresa = st.text_input(
                    "E-mail Comercial", 
                    value=user_email or "",
                    help="E-mail que constará nos cabeçalhos de relatórios e cobranças."
                )

                st.write("")
                btn_concluir = st.form_submit_button(
                    "Concluir Cadastro e Ativar Sistema", 
                    type="primary", 
                    use_container_width=True
                )

                if btn_concluir:
                    if not nome_empresa.strip() or not doc_empresa.strip() or not tel_empresa.strip():
                        st.warning("Por favor, preencha todos os campos obrigatórios (*).")
                    else:
                        sucesso, resultado = salvar_empresa_onboarding(
                            user_id=user_id,
                            nome=nome_empresa,
                            cnpj_cpf=doc_empresa,
                            telefone=tel_empresa,
                            email=email_empresa
                        )
                        if sucesso:
                            st.session_state["cliente_id_ativo"] = resultado
                            st.success("Empresa ativada com sucesso! Carregando painel...")
                            st.rerun()
                        else:
                            st.error(resultado)

            # Rodapé sutil de versão
            st.markdown(
                """
                <p style="text-align: center; color: #94A3B8; font-size: 0.72rem; margin-top: 12px;">
                    Kazimm Gestão • Configuração de Conta MEI
                </p>
                """, 
                unsafe_allow_html=True
            )

        # Interrompe o fluxo aqui: NENHUM módulo ou página é carregada sem empresa
        st.stop()

    # 3. Se POSSUI empresa: Alimenta a sessão e registra TODOS os módulos no st.navigation
    nome_ativo = empresa["nome_normalizado"]
    regime_ativo = empresa["regime_normalizado"]
    plano_ativo = empresa["plano_normalizado"]
    cliente_id = empresa["id"]

    # ID do cliente para consultas no banco
    st.session_state["cliente_id_ativo"] = cliente_id

    # [CORREÇÃO]: Chaves lidas pelo Painel de Contexto (Img 1)
    st.session_state["cliente_ativo_nome"] = nome_ativo
    st.session_state["cliente_ativo_regime"] = regime_ativo
    st.session_state["cliente_ativo_plano"] = plano_ativo

    # Chaves legadas para compatibilidade com outras rotinas
    st.session_state["nome_empresa_ativa"] = nome_ativo
    st.session_state["regime_ativo"] = regime_ativo
    st.session_state["plano_ativo"] = plano_ativo

    st.sidebar.write(f"👤 Logado como: **{usuario_atual.email}**")
    st.sidebar.caption(f"🏢 Empresa ativa: **{empresa['nome_normalizado']}**")
    if st.sidebar.button("Sair (Logout)"):
        logout()

    # Registra todas as páginas para garantir o funcionamento do st.page_link nos módulos
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