import streamlit as st

# Dicionário Central de Ícones (Google Material Symbols)
ICONES = {
    # Módulos principais (Barra Superior)
    "contabil": ":material/account_balance:",
    "contratos": ":material/contract:",
    "previdencia": ":material/badge:",
    "fiscal": ":material/receipt_long:",

    # Seções internas do Gestor Contábil
    "dashboard": ":material/dashboard:",
    "fornecedor": ":material/domain_add:",
    "adicionar": ":material/add_circle:",
    "importar": ":material/upload_file:",
    "provisoes": ":material/pending_actions:",
    "extrato": ":material/file_present:",
    "lancamentos": ":material/receipt_long:",
    "conciliacao": ":material/balance:",
    "plano_contas": ":material/account_tree:",
    "dre": ":material/analytics:",

    # Ações e Operações Financeiras
    "adicionar": ":material/add_circle:",
    "salvar": ":material/save:",
    "editar": ":material/edit:",
    "excluir": ":material/delete:",
    "filtrar": ":material/filter_alt:",
    "importar": ":material/upload_file:",
    "exportar": ":material/download:",
    "pesquisar": ":material/search:",

    # Métricas e Status
    "receita": ":material/trending_up:",
    "despesa": ":material/trending_down:",
    "saldo": ":material/savings:",
    "alerta": ":material/warning:",
    "sucesso": ":material/check_circle:",
    "erro": ":material/error:",

    # Banner informativo
    "cliente": ":material/person:",
    "cartao": ":material/credit_card:",
}
def aplicar_tema_global():
    """
    Injeta as regras visuais padronizadas em toda a aplicação (Estilo Kazimm / Montserrat)
    """
    st.markdown("""
    <style>
    /* 1. Importação das fontes Montserrat e Inter */
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@600;700;800&family=Inter:wght@400;500;600&display=swap');

    html, body, .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Títulos padronizados em Montserrat */
    h1, h2, h3, [data-testid="stHeader"] {
        font-family: 'Montserrat', sans-serif !important;
    }

    /* 2. Barra lateral clean */
    [data-testid="stSidebar"] {
        background-color: #F8FAFC !important;
        border-right: 1px solid #E2E8F0;
    }

    /* 3. Container do Menu de Navegação */
    div[role="radiogroup"] {
        display: flex !important;
        flex-direction: column !important;
        gap: 8px !important;
        width: 100% !important;
        padding-top: 6px;
    }

    /* ========================================================
       CONTROLE DO RÁDIO: OCULTA APENAS A BOLINHA
       ======================================================== */

    /* 1. Oculta o input padrão */
    div[role="radiogroup"] label input {
        display: none !important;
    }

    /* 2. Oculta a bolinha (irmã direta do input ou primeiro item antes do texto) */
    div[role="radiogroup"] label input + div,
    div[role="radiogroup"] label > div:first-of-type:not(:last-child),
    div[role="radiogroup"] label > div > div:first-child:not(:last-child) {
        display: none !important;
    }

    /* 3. Cartão do Menu em Repouso */
    div[role="radiogroup"] label {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 10px !important;
        padding: 10px 14px !important;
        margin: 0 !important;
        cursor: pointer !important;
        transition: all 0.2s ease-in-out !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02) !important;
        display: flex !important;
        align-items: center !important;
        width: 100% !important;
    }

    /* 4. Garante o texto e ícone nítidos e alinhados */
    div[role="radiogroup"] label [data-testid="stMarkdownContainer"],
    div[role="radiogroup"] label [data-testid="stMarkdownContainer"] p {
        display: flex !important;
        align-items: center !important;
        gap: 8px !important;
        visibility: visible !important;
        opacity: 1 !important;
        color: #334155 !important;
        font-weight: 600 !important;
        font-size: 0.90rem !important;
        margin: 0 !important;
        width: 100% !important;
    }

    div[role="radiogroup"] label span[data-testid="stIconMaterial"] {
        color: #007791 !important;
        font-size: 1.25rem !important;
        display: inline-flex !important;
        align-items: center !important;
        visibility: visible !important;
    }

    /* 5. Efeito Hover no Cartão */
    div[role="radiogroup"] label:hover {
        border-color: #00A3B4 !important;
        background-color: #F0FDFA !important;
        transform: translateX(4px);
        box-shadow: 0 4px 12px rgba(0, 163, 180, 0.12) !important;
    }

    div[role="radiogroup"] label:hover span[data-testid="stIconMaterial"] {
        color: #00A3B4 !important;
    }

    /* 6. Cartão Ativo (Selecionado) */
    div[role="radiogroup"] label:has(input:checked) {
        background: linear-gradient(135deg, #00A3B4 0%, #007791 100%) !important;
        border-color: #007791 !important;
        box-shadow: 0 4px 14px rgba(0, 163, 180, 0.35) !important;
        transform: translateX(4px);
    }

    div[role="radiogroup"] label:has(input:checked) [data-testid="stMarkdownContainer"] p,
    div[role="radiogroup"] label:has(input:checked) span[data-testid="stIconMaterial"] {
        color: #FFFFFF !important;
        font-weight: 700 !important;
    }
    

    /* Botão Sair / Logout */
    div[data-testid="stSidebar"] button:has(p:contains("Sair")) {
        background-color: #FEE2E2 !important;
        border: 1px solid #FCA5A5 !important;
        color: #DC2626 !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }
    div[data-testid="stSidebar"] button:has(p:contains("Sair")):hover {
        background-color: #DC2626 !important;
        color: #FFFFFF !important;
    }

    /* Cards de Métricas (Dashboard) */
    [data-testid="stMetric"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 12px !important;
        padding: 14px 18px !important;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.04) !important;
        transition: transform 0.2s ease;
    }
    [data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(15, 23, 42, 0.08) !important;
    }
    /* Força o container principal a ocupar 100% da tela */
    .block-container {
        max-width: 98% !important;
        padding-left: 2.5rem !important;
        padding-right: 2.5rem !important;
        padding-top: 1.5rem !important;
    }

    /* Estilização dos Links de Página em Cartões Modernos no Topo */
    [data-testid="stPageLink"] a,
    div[data-testid="stPageLink-NavLink"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 10px !important;
        padding: 10px 14px !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03) !important;
        transition: all 0.2s ease-in-out !important;
        text-align: center !important;
        text-decoration: none !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
    }

    [data-testid="stPageLink"] a:hover,
    div[data-testid="stPageLink-NavLink"]:hover {
        border-color: #00A3B4 !important;
        background-color: #F0FDFA !important;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 163, 180, 0.15) !important;
    }

    /* Cartão Ativo (Página atual destacada em gradiente) */
    [data-testid="stPageLink"] a[aria-current="page"],
    div[data-testid="stPageLink-NavLink"][aria-current="page"] {
        background: linear-gradient(135deg, #00A3B4 0%, #007791 100%) !important;
        border-color: #007791 !important;
        box-shadow: 0 4px 14px rgba(0, 163, 180, 0.35) !important;
    }

    [data-testid="stPageLink"] a[aria-current="page"] p,
    [data-testid="stPageLink"] a[aria-current="page"] span,
    div[data-testid="stPageLink-NavLink"][aria-current="page"] p {
        color: #FFFFFF !important;
        font-weight: 700 !important;
    }

    /* ========================================================
       CONTROLE DOS ÍCONES (MATERIAL SYMBOLS) NOS CARTÕES
       ======================================================== */

    /* 1. Tamanho e Cor em Repouso */
    [data-testid="stPageLink"] span[data-testid="stIconMaterial"],
    div[data-testid="stPageLink-NavLink"] span[data-testid="stIconMaterial"] {
        font-size: 1.55rem !important;  /* <-- TAMANHO DO ÍCONE (ex: 1.2rem a 1.6rem) */
        color: #00A3BA !important;      /* <-- COR DO ÍCONE (Azul Petróleo da marca) */
        vertical-align: middle !important;
        transition: all 0.2s ease-in-out !important;
    }

    /* 2. Efeito ao Passar o Mouse (Hover) */
    [data-testid="stPageLink"]:hover span[data-testid="stIconMaterial"],
    div[data-testid="stPageLink-NavLink"]:hover span[data-testid="stIconMaterial"] {
        color: #00A3B4 !important;      /* Transição para Ciano/Turquesa */
        transform: scale(1.12);         /* Micro-animação de zoom */
    }

    /* 3. Ícone no Cartão Selecionado (Página Ativa) */
    [data-testid="stPageLink"] a[aria-current="page"] span[data-testid="stIconMaterial"],
    div[data-testid="stPageLink-NavLink"][aria-current="page"] span[data-testid="stIconMaterial"] {
        color: #FFFFFF !important;      /* Branco puro sobre o gradiente ativo */
    }

    </style>
    """, unsafe_allow_html=True)
    


def exibir_cabecalho(titulo: str, subtitulo: str = "Plataforma de Gestão Integrada"):
    """
    Renderiza o cabeçalho padronizado com a logo alinhada lado a lado com os títulos.
    """
    col_logo, col_texto = st.columns([1.2, 7], vertical_alignment="center")

    with col_logo:
        # Ajuste a largura (width) conforme necessário para a nitidez ideal
        st.image("assets/Logo.png", width=170)

    with col_texto:
        st.markdown(f"""
            <div style="font-family: 'Montserrat', sans-serif; margin-left: 8px;">
                <span style="font-size: 0.85rem; font-weight: 700; color: #00A3B4; text-transform: uppercase; letter-spacing: 1px; display: block; margin-bottom: 2px;">
                    {subtitulo}
                </span>
                <h1 style="margin: 0; padding: 0; font-size: 1.85rem; color: #007791; font-weight: 800; letter-spacing: -0.5px; line-height: 1.2;">
                    {titulo}
                </h1>
            </div>
        """, unsafe_allow_html=True)

    # Divisória sutil separando o cabeçalho dos cartões de navegação
    st.markdown("<hr style='margin: 12px 0 18px 0; border: none; border-top: 1px solid #E2E8F0;'>", unsafe_allow_html=True)
    

def exibir_menu_modulos_topo():
    """
    Renderiza os 4 módulos principais do Kazimm em cartões horizontais no topo,
    utilizando os ícones vetoriais centralizados.
    """
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.page_link("pages/1_Gestor_Contabil.py", label="Gestor Contábil", icon=ICONES["contabil"], use_container_width=True)
    with col2:
        st.page_link("pages/2_Gerador_Contratos.py", label="Gerador de Contratos", icon=ICONES["contratos"], use_container_width=True)
    with col3:
        st.page_link("pages/3_Empregados_Previdencia.py", label="Empregados / Previdência", icon=ICONES["previdencia"], use_container_width=True)
    with col4:
        st.page_link("pages/4_Gestor_Fiscal.py", label="Gestor Fiscal", icon=ICONES["fiscal"], use_container_width=True)

    st.markdown("<div style='margin-bottom: 18px;'></div>", unsafe_allow_html=True)
    
# Alias de compatibilidade
aplicar_estilo_moderno = aplicar_tema_global