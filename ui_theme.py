from pathlib import Path
import streamlit as st

# Localiza a raiz do projeto e o arquivo exato da Logo
DIR_RAIZ = Path(__file__).resolve().parent
CAMINHO_LOGO = DIR_RAIZ / "assets" / "Logo.png"

# Dicionário Central de Ícones (Google Material Symbols)
ICONES = {
    # Módulos principais (Barra Superior)
    "contabil": ":material/account_balance:",       # 🏛️ Módulo Contábil
    "contratos": ":material/contract:",             # 📜 Módulo de Contratos
    "previdencia": ":material/badge:",              # 🪪 Módulo Previdência
    "fiscal": ":material/receipt_long:",            # 🧾 Módulo Fiscal

    # Menu Lateral - Gestor Contábil
    "dashboard": ":material/dashboard:",            # 🖥️ Dashboard principal
    "fornecedor": ":material/domain_add:",          # 🏢➕ Cadastrar Conta/Fornecedor
    "provisoes": ":material/pending_actions:",      # ⏳ Provisões / Pendências
    "extrato": ":material/file_present:",           # 📄 Importar Extrato
    "lancamentos": ":material/receipt_long:",       # 🧾 Ver Lançamentos
    "conciliacao": ":material/balance:",            # ⚖️ Conciliação Bancária
    "plano_contas": ":material/account_tree:",      # 🗂️ Plano de Contas
    "dre": ":material/analytics:",                  # 📊 DRE / Relatório por Categoria

    # Ações e Operações (CRUD)
    "adicionar": ":material/add_circle:",           # ➕ Adicionar / Novo (Botões de ação)
    "salvar": ":material/save:",                    # 💾 Salvar dados
    "editar": ":material/edit:",                    # ✏️ Editar registro
    "excluir": ":material/delete:",                 # 🗑️ Excluir / Apagar
    "importar": ":material/upload_file:",           # ⬆️ Importar lote (Upload)
    "exportar": ":material/download:",              # 📥 Exportar / Download
    "pesquisar": ":material/search:",               # 🔍 Pesquisar na tabela
    "filtrar": ":material/filter_alt:",             # 🎛️ Filtrar resultados

    # Métricas e Financeiro
    "receita": ":material/trending_up:",            # 📈 Receita (Seta para Cima)
    "despesa": ":material/trending_down:",          # 📉 Despesa (Seta para Baixo)
    "saldo": ":material/savings:",                  # 💰 Saldo / Porquinho
    "receita_federal": ":material/account_balance:",# 🏛️ Receita Federal / Bancos
    "planilhas": ":material/table_chart:",          # 📊 Planilhas / Tabelas de dados

    # Avisos, Status e Feedbacks
    "sucesso": ":material/check_circle:",           # ✅ Operação concluída
    "erro": ":material/error:",                     # ❌ Erro comum / Falha
    "erro_grave": ":material/gpp_bad:",             # 🚨 Erro Grave / Exclusão
    "alerta": ":material/warning:",                 # ⚠️ Alerta (Aviso importante)
    "atencao": ":material/lightbulb:",              # 💡 Atenção (Informativo / Ideia)
    "dicas": ":material/push_pin:",                 # 📌 Dicas / Fixado
    "bem_vindo": ":material/waving_hand:",          # 👋 Mensagem de Bem-vindo

    # Utilitários e Sistema
    "cliente": ":material/person:",                 # 👤 Cliente logado / Pessoa
    "cartao": ":material/credit_card:",             # 💳 Plano ativo / Cartão
    "configuracoes": ":material/settings:",         # ⚙️ Configurações do sistema
    "ferramentas": ":material/build:",              # 🛠️ Ferramentas extras
    "global": ":material/language:",                # 🌐 Global / Web
    "empresa": ":material/domain:",                 # 🏢 Empresa genérica
    "pastas": ":material/folder:",                  # 📂 Pastas / Diretórios
    "agenda": ":material/calendar_month:",          # 📆 Agenda / Prazos
    "reciclagem": ":material/sync:",                # 🔄 Reciclagem / Atualizar sincronização
    "transmissao": ":material/rocket_launch:",      # 🚀 Transmissão de eventos (eSocial/NF)
    "relatorios": ":material/description:",         # 📄 Relatórios textuais
}
def aplicar_tema_global():
    """
    Injeta as regras visuais padronizadas em toda a aplicação (Estilo Kazimm / Montserrat)
    """
    st.markdown("""
    <style>
    /* ========================================================
       REDUÇÃO DE MARGENS E APROVEITAMENTO DE TELA (PADRÃO ERP)
       ======================================================== */
    /* Elimina o vazio superior nativo de 5rem/6rem do Streamlit */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        max-width: 98% !important;
    }

    /* Oculta o cabeçalho original vazio mantendo a barra de navegação acessível */
    header[data-testid="stHeader"] {
        background-color: transparent !important;
        height: 0px !important;
    }

    /* ========================================================
       ESTILIZAÇÃO DAS ABAS DE FUNÇÕES (st.tabs) E ÁREA ROLÁVEL
       ======================================================== */
    /* Barra horizontal de navegação das abas */
    div[data-testid="stTabs"] [role="tablist"] {
        gap: 8px !important;
        border-bottom: 2px solid #E2E8F0 !important;
        padding-bottom: 2px !important;
        margin-bottom: 12px !important;
    }

    /* Cada aba individual */
    div[data-testid="stTabs"] [role="tab"] {
        font-family: 'Inter', sans-serif !important;
        font-size: 0.82rem !important;
        font-weight: 600 !important;
        color: #64748B !important;
        background-color: transparent !important;
        border: none !important;
        border-radius: 6px 6px 0 0 !important;
        padding: 6px 14px !important;
        transition: all 0.2s ease !important;
    }

    /* Aba ativa / selecionada */
    div[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
        color: #007791 !important;
        border-bottom: 3px solid #00A3B4 !important;
        font-weight: 700 !important;
    }

    /* Contentor com rolamento interno elegante */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 8px !important;
        border: 1px solid #E2E8F0 !important;
        background-color: #FFFFFF !important;
    }

    /* ========================================================
       COMPACTAÇÃO DOS BOTÕES DE NAVEGAÇÃO (st.page_link)
       ======================================================== */
    div[data-testid="stPageLink"] a,
    [data-testid="stPageLink-NavLink"] {
        padding: 4px 10px !important;
        min-height: 34px !important;
        height: 34px !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 6px !important;
        background-color: #FFFFFF !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 6px !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.02) !important;
        transition: all 0.15s ease-in-out !important;
    }

    /* Reduz o texto interno e zera espaçamentos residuais */
    div[data-testid="stPageLink"] a p,
    [data-testid="stPageLink-NavLink"] span {
        font-size: 0.78rem !important;
        line-height: 1 !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    /* Efeito hover elegante */
    div[data-testid="stPageLink"] a:hover,
    [data-testid="stPageLink-NavLink"]:hover {
        border-color: #00A3B4 !important;
        background-color: #F0FDFA !important;
        color: #007791 !important;
    }


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
       COMPACTAÇÃO DAS COLUNAS E CARDS DE MÉTRICAS
       ======================================================== */
    /* Reduz o vão horizontal entre as 4 colunas de métricas */
    div[data-testid="stHorizontalBlock"] {
        gap: 10px !important;
    }

    /* Reduz o respiro vertical dentro das colunas */
    div[data-testid="column"] {
        padding: 0 !important;
    }

    /* Se os seus cards usam div com borda (estilo container de métrica) */
    div[data-testid="column"] > div {
        margin-bottom: 4px !important;
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

    /* 1. Oculta o botão "Manage app" e selos no canto inferior direito */
    div[class*="viewerBadge"],
    [data-testid="manage-app-button"],
    #manage-app-button,
    .viewerBadge_container {
        display: none !important;
        visibility: hidden !important;
    }

    /* 2. Oculta a barra superior nativa (botões "Fork", GitHub e menu de 3 pontinhos) */
    [data-testid="stToolbar"],
    [data-testid="stDecoration"] {
        display: none !important;
        visibility: hidden !important;
    }

    /* 3. Neutraliza o cabeçalho e rodapé vazios do Streamlit */
    #MainMenu, footer {
        display: none !important;
        visibility: hidden !important;
    }

    </style>
    """, unsafe_allow_html=True)
    


def exibir_cabecalho(
    titulo: str, 
    subtitulo: str = "Plataforma de Gestão Integrada", 
    versao: str = "v1.0.2-beta",
    logo_b64: str = None
):
    """
    Renderiza o cabeçalho compacto (Slim ERP) com logo dinâmica, 
    identificação do módulo e versão alinhada à direita.
    """
    col_logo, col_texto, col_versao = st.columns([1.3, 7.2, 1.5], vertical_alignment="center")

    with col_logo:
        # 1. Se vier logo em Base64 do cliente/empresa ativa, renderiza ela
        if logo_b64:
            st.markdown(
                f'<img src="{logo_b64}" style="max-height: 42px; width: auto; object-fit: contain;">', 
                unsafe_allow_html=True
            )
        # 2. Se não, usa a logo oficial do arquivo local
        elif CAMINHO_LOGO.exists():
            st.image(str(CAMINHO_LOGO), width=135)
        # 3. Fallback de texto caso a imagem não seja encontrada
        else:
            st.markdown("<h3 style='color:#007791; margin:0; font-weight:800;'>KAZIMM</h3>", unsafe_allow_html=True)

    with col_texto:
        # Tipografia enxuta e proporcional (estilo Omie / Conta Azul)
        st.markdown(f"""
        <div style="font-family: 'Montserrat', sans-serif; margin-left: 6px; line-height: 1.15;">
            <div style="font-size: 0.72rem; font-weight: 700; color: #00A3B4; text-transform: uppercase; letter-spacing: 0.8px;">
                {subtitulo}
            </div>
            <div style="font-size: 1.35rem; color: #007791; font-weight: 800; letter-spacing: -0.3px; margin-top: 1px;">
                {titulo}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_versao:
        st.markdown(f"""
        <div style="display: flex; justify-content: flex-end; align-items: center;">
            <span style="background: #F1F5F9; color: #475569; font-size: 0.72rem; font-weight: 600; padding: 3px 8px; border-radius: 6px; border: 1px solid #E2E8F0;">
                {versao}
            </span>
        </div>
        """, unsafe_allow_html=True)

    # Linha divisória ultra-fina e colada ao cabeçalho (sem espaços mortos)
    st.markdown("<hr style='margin: 6px 0 10px 0; border: none; border-top: 1px solid #E2E8F0;'>", unsafe_allow_html=True)

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
# ==============================================================================
# COMPONENTES ESTRUTURAIS WHITE-LABEL (NAVBAR, CONTEXTO E RODAPÉ)
# ==============================================================================

def exibir_navbar_superior(modulo_ativo: str = "Gestor Contábil", versao: str = "v1.0.2-beta"):
    """
    Renderiza a barra superior unificada conforme o topo do manuscrito:
    [LOGO KAZIMM] -------- [MÓDULO ATIVO] -------- [VERSÃO / AMBIENTE]
    """
    html_navbar = f"""<div style="display: flex; justify-content: space-between; align-items: center; background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 10px 20px; margin-bottom: 16px; box-shadow: 0 2px 6px rgba(0,0,0,0.03);">
    <div style="display: flex; align-items: center; gap: 8px;">
        <span style="font-family: 'Montserrat', sans-serif; font-size: 1.25rem; font-weight: 800; color: #007791; letter-spacing: -0.5px;">KAZIMM</span>
        <span style="background: #F0FDFA; color: #00A3B4; font-size: 0.72rem; font-weight: 700; padding: 2px 8px; border-radius: 6px; border: 1px solid #CCFBF1;">SaaS</span>
    </div>
    <div style="display: flex; align-items: center; gap: 8px; background: linear-gradient(135deg, #00A3B4 0%, #007791 100%); color: #FFFFFF; padding: 6px 18px; border-radius: 20px; font-size: 0.88rem; font-weight: 600; box-shadow: 0 2px 8px rgba(0, 163, 180, 0.25);">
        <span>{modulo_ativo}</span>
    </div>
    <div style="display: flex; align-items: center; gap: 10px;">
        <span style="background: #F1F5F9; color: #475569; font-size: 0.75rem; font-weight: 600; padding: 4px 10px; border-radius: 6px;">{versao}</span>
    </div>
</div>"""
    st.markdown(html_navbar, unsafe_allow_html=True)


def exibir_banner_cliente_ativo(
    nome_cliente: str, 
    regime: str = "MEI (Microempreendedor Individual)", 
    plano: str = "Plano MEI Pro", 
    cnpj: str = "", 
    **kwargs
):
    """
    Banner de contexto ultra-slim:
    [Ícone + Cliente Ativo + Regime + CNPJ] ---------------- [Tag Plano]
    """
    cnpj_html = f'<span style="color: #94A3B8; font-size: 0.78rem;"> • CNPJ: {cnpj}</span>' if cnpj else ""

    html_banner = (
        f'<div style="display: flex; justify-content: space-between; align-items: center; '
        f'background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; '
        f'padding: 6px 14px; margin-bottom: 8px;">'
        f'<div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">'
        f'<span style="color: #007791; display: inline-flex; align-items: center;">'
        f'<svg style="width: 16px; height: 16px;" viewBox="0 0 24 24" fill="currentColor">'
        f'<path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>'
        f'</svg>'
        f'</span>'
        f'<span style="color: #64748B; font-size: 0.80rem; font-weight: 600;">Cliente Ativo:</span>'
        f'<strong style="color: #0F172A; font-size: 0.86rem;">{nome_cliente}</strong>'
        f'<span style="color: #CBD5E1;">|</span>'
        f'<span style="color: #64748B; font-size: 0.80rem;">Regime: <strong>{regime}</strong></span>'
        f'{cnpj_html}'
        f'</div>'
        f'<div>'
        f'<span style="background-color: #E0F2FE; color: #007791; font-size: 0.72rem; font-weight: 700; padding: 2px 10px; border-radius: 10px; border: 1px solid #BAE6FD;">'
        f'{plano}'
        f'</span>'
        f'</div>'
        f'</div>'
    )
    st.markdown(html_banner, unsafe_allow_html=True)

def exibir_botoes_modulos_navegacao(modulo_atual: str = "contabil"):
    """
    Exibe os 4 botões de navegação rápida entre módulos (conforme a 2ª linha do manuscrito).
    Utiliza st.page_link para troca instantânea de rotas sem recarregar a sessão.
    """
    modulos = [
        {
            "id": "contabil",
            "nome": "Gestor Contábil",
            "page": "pages/1_Gestor_Contabil.py",
            "icon": ICONES.get("contabil", ":material/account_balance:")
        },
        {
            "id": "contratos",
            "nome": "Gerador de Contratos",
            "page": "pages/2_Gerador_Contratos.py",
            "icon": ICONES.get("contratos", ":material/contract:")
        },
        {
            "id": "previdencia",
            "nome": "Empregados / Folha",
            "page": "pages/3_Empregados_Previdencia.py",
            "icon": ICONES.get("previdencia", ":material/badge:")
        },
        {
            "id": "fiscal",
            "nome": "Gestor Fiscal",
            "page": "pages/4_Gestor_Fiscal.py",
            "icon": ICONES.get("fiscal", ":material/receipt_long:")
        },
    ]

    col1, col2, col3, col4 = st.columns(4)
    for col, m in zip([col1, col2, col3, col4], modulos):
        with col:
            rotulo = f"**{m['nome']}**" if m["id"] == modulo_atual else m["nome"]
            st.page_link(m["page"], label=rotulo, icon=m["icon"], use_container_width=True)


def exibir_rodape_institucional(versao: str = "v1.0.2-beta", status_servico: str = "Supabase Conectado"):
    """
    Renderiza o rodapé institucional com o ponto verde pulsante.
    """
    html_rodape = f"""<style>
@keyframes pulse-green {{
    0% {{ transform: scale(0.95); box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.7); }}
    70% {{ transform: scale(1); box-shadow: 0 0 0 6px rgba(34, 197, 94, 0); }}
    100% {{ transform: scale(0.95); box-shadow: 0 0 0 0 rgba(34, 197, 94, 0); }}
}}
.status-dot {{
    width: 8px;
    height: 8px;
    background-color: #22C55E;
    border-radius: 50%;
    display: inline-block;
    animation: pulse-green 2s infinite;
}}
</style>
<div style="margin-top: 40px; padding-top: 14px; padding-bottom: 8px; border-top: 1px solid #E2E8F0; display: flex; justify-content: space-between; align-items: center; font-size: 0.78rem; color: #64748B;">
    <div>© 2026 <strong>Kazimm Gestão & Tecnologia</strong> • Todos os direitos reservados.</div>
    <div style="display: flex; align-items: center; gap: 16px;">
        <div style="display: flex; align-items: center; gap: 6px;">
            <span class="status-dot"></span>
            <span style="font-weight: 600; color: #166534;">{status_servico}</span>
        </div>
        <span>•</span>
        <span style="background: #F1F5F9; padding: 2px 8px; border-radius: 4px; font-weight: 600;">{versao}</span>
        <span>•</span>
        <a href="#" style="color: #007791; text-decoration: none; font-weight: 600;">Suporte VIP</a>
    </div>
</div>"""
    st.markdown(html_rodape, unsafe_allow_html=True)

# Alias de compatibilidade
aplicar_estilo_moderno = aplicar_tema_global