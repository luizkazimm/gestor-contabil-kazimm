import streamlit as st

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

    /* Oculta círculo original preservando texto */
    div[role="radiogroup"] label input {
        display: none !important;
    }
    div[role="radiogroup"] label > div:first-child:not([data-testid="stMarkdownContainer"]) {
        display: none !important;
    }

    /* Cartão do Menu em Repouso */
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

    div[role="radiogroup"] label p {
        display: block !important;
        color: #334155 !important;
        font-weight: 600 !important;
        font-size: 0.90rem !important;
        margin: 0 !important;
        width: 100% !important;
    }

    /* Hover no Menu */
    div[role="radiogroup"] label:hover {
        border-color: #00A3B4 !important;
        background-color: #F0FDFA !important;
        transform: translateX(4px);
        box-shadow: 0 4px 12px rgba(0, 163, 180, 0.12) !important;
    }

    /* Cartão Ativo / Selecionado */
    div[role="radiogroup"] label:has(input:checked) {
        background: linear-gradient(135deg, #00A3B4 0%, #088395 100%) !important;
        border-color: #008290 !important;
        box-shadow: 0 4px 14px rgba(0, 163, 180, 0.35) !important;
        transform: translateX(4px);
    }

    div[role="radiogroup"] label:has(input:checked) p {
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
    Renderiza os 4 módulos principais do Kazimm em cartões horizontais no topo da página.
    """
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.page_link("pages/1_Gestor_Contabil.py", label="Gestor Contábil", icon="📊", use_container_width=True)
    with col2:
        st.page_link("pages/2_Gerador_Contratos.py", label="Gerador de Contratos", icon="📝", use_container_width=True)
    with col3:
        st.page_link("pages/3_Empregados_Previdencia.py", label="Empregados / Previdência", icon="👥", use_container_width=True)
    with col4:
        st.page_link("pages/4_Gestor_Fiscal.py", label="Gestor Fiscal", icon="📑", use_container_width=True)

    st.markdown("<div style='margin-bottom: 18px;'></div>", unsafe_allow_html=True)

    
# Alias de compatibilidade
aplicar_estilo_moderno = aplicar_tema_global