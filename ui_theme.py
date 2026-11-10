from pathlib import Path
import streamlit as st
import pandas as pd

# Localiza a raiz do projeto e o arquivo exato da Logo
DIR_RAIZ = Path(__file__).resolve().parent
CAMINHO_LOGO = DIR_RAIZ / "assets" / "Logo.png"

# =============================================================================
# DICIONÁRIO CENTRAL DE ÍCONES (GOOGLE MATERIAL SYMBOLS)
# =============================================================================
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
    Injeta as regras visuais padronizadas em toda a aplicação (Estilo Kazimm / Montserrat & Inter).
    """
    st.markdown("""
    <style>
    /* 1. Importação das fontes Montserrat e Inter */
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@600;700;800&family=Inter:wght@400;500;600;700&display=swap');

    html, body, .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    h1, h2, h3, [data-testid="stHeader"] {
        font-family: 'Montserrat', sans-serif !important;
    }

    /* ========================================================
       TÍTULOS DE MÓDULOS E SEÇÕES (####) - AZUL KAZIMM SUAVE
       ======================================================== */
    h4, [data-testid="stMarkdownContainer"] h4 {
        font-family: 'Montserrat', sans-serif !important;
        color: #0176A1 !important;
        font-weight: 600 !important;      /* Reduz o peso pesado para uma espessura elegante */
        font-size: 1.15rem !important;     /* Proporção harmoniosa sem poluir a tela */
        letter-spacing: -0.2px !important;
        margin-top: 4px !important;
        margin-bottom: 12px !important;
        display: flex !important;
        align-items: center !important;
        gap: 8px !important;
    }

    /* Garante que o ícone acompanhe exatamente o mesmo azul institucional */
    h4 span[data-testid="stIconMaterial"],
    [data-testid="stMarkdownContainer"] h4 span[data-testid="stIconMaterial"] {
        color: #0176A1 !important;
        font-size: 1.35rem !important;
        vertical-align: middle !important;
    }

    /* Subtítulos menores (#####) */
    h5, [data-testid="stMarkdownContainer"] h5 {
        font-family: 'Inter', sans-serif !important;
        color: #334155 !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        margin-bottom: 8px !important;
    }

    /* ========================================================
       REDUÇÃO DE MARGENS E APROVEITAMENTO DE TELA
       ======================================================== */
    .block-container {
        padding-top: 1.2rem !important;
        padding-bottom: 1.5rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        max-width: 98% !important;
    }

    header[data-testid="stHeader"] {
        background-color: transparent !important;
        height: 0px !important;
    }

    /* Oculta marca d'água nativa do Streamlit */
    div[class*="viewerBadge"],
    [data-testid="manage-app-button"],
    #manage-app-button,
    .viewerBadge_container,
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    #MainMenu, footer {
        display: none !important;
        visibility: hidden !important;
    }

    /* ========================================================
       BARRA LATERAL (SIDEBAR)
       ======================================================== */
    [data-testid="stSidebar"] {
        background-color: #F8FAFC !important;
        border-right: 1px solid #E2E8F0 !important;
    }

    div[role="radiogroup"] {
        display: flex !important;
        flex-direction: column !important;
        gap: 8px !important;
        width: 100% !important;
        padding-top: 6px;
    }

    /* Oculta totalmente a bolinha padrão do rádio */
    div[role="radiogroup"] label input,
    div[role="radiogroup"] label input + div,
    div[role="radiogroup"] label > div:first-of-type:not(:last-child),
    div[role="radiogroup"] label > div > div:first-child:not(:last-child) {
        display: none !important;
        visibility: hidden !important;
        width: 0px !important;
        height: 0px !important;
    }

    /* Cartão do Menu em Repouso (Inativo) */
    div[role="radiogroup"] label {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 8px !important;
        padding: 9px 14px !important;
        margin: 0 !important;
        cursor: pointer !important;
        transition: all 0.2s ease-in-out !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.02) !important;
        display: flex !important;
        align-items: center !important;
        width: 100% !important;
    }

    div[role="radiogroup"] label [data-testid="stMarkdownContainer"],
    div[role="radiogroup"] label [data-testid="stMarkdownContainer"] p {
        display: flex !important;
        align-items: center !important;
        gap: 8px !important;
        color: #334155 !important;
        font-weight: 600 !important;
        font-size: 0.88rem !important;
        margin: 0 !important;
        width: 100% !important;
    }

    div[role="radiogroup"] label span[data-testid="stIconMaterial"] {
        color: #007791 !important;
        font-size: 1.20rem !important;
        display: inline-flex !important;
        align-items: center !important;
    }

    /* Hover no Menu Lateral */
    div[role="radiogroup"] label:hover {
        border-color: #00A3B4 !important;
        background-color: #F0FDFA !important;
        transform: translateX(3px);
        box-shadow: 0 4px 10px rgba(0, 163, 180, 0.12) !important;
    }

    /* CARTÃO ATIVO (PADRÃO KAZIMM DA IMG 1) */
    div[role="radiogroup"] label:has(input:checked) {
        background: linear-gradient(135deg, #00A3B4 0%, #007791 100%) !important;
        border: 1px solid #007791 !important;
        box-shadow: 0 4px 12px rgba(0, 163, 180, 0.30) !important;
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

    /* ========================================================
       ESTRUTURA: CONTAINER 580PX, SANFONA & FORMULÁRIOS
       ======================================================== */
    /* Container principal de 580px: borda limpa, sem efeito de arame */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border: 1px solid #E2E8F0 !important;
        border-radius: 10px !important;
        background-color: #FFFFFF !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02) !important;
    }

    /* Sanfona de contexto (st.expander) */
    div[data-testid="stExpander"] {
        border: 1px solid #E2E8F0 !important;
        border-radius: 10px !important;
        background-color: #FFFFFF !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.02) !important;
        overflow: hidden;
    }

    div[data-testid="stExpander"] details {
        border: none !important;
    }

    div[data-testid="stForm"] {
        border: 1px solid #E2E8F0 !important;
        border-radius: 10px !important;
    }

    /* ========================================================
       CARDS DE MÉTRICAS (FINANCEIRO & DASHBOARD)
       ======================================================== */
    [data-testid="stMetric"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 10px !important;
        padding: 10px 14px !important;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.03) !important;
        transition: all 0.2s ease-in-out !important;
    }
    [data-testid="stMetric"]:hover {
        border-color: #00A3B4 !important;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 163, 180, 0.08) !important;
    }

    /* Rótulo superior da métrica (Ex: SALDO INICIAL, TOTAL ENTRADAS) */
    [data-testid="stMetricLabel"] p,
    [data-testid="stMetricLabel"] label,
    div[data-testid="stMetricLabel"] {
        font-family: 'Inter', sans-serif !important;
        font-size: 0.72rem !important;
        font-weight: 700 !important;
        color: #64748B !important;
        text-transform: uppercase !important;
        letter-spacing: 0.6px !important;
        margin-bottom: 2px !important;
    }

    /* Valor numérico principal da métrica */
    [data-testid="stMetricValue"] div,
    [data-testid="stMetricValue"] {
        font-family: 'Montserrat', sans-serif !important;
        font-size: 1.25rem !important; /* Reduz de 2.0rem para um tamanho corporativo elegante */
        font-weight: 700 !important;
        color: #0F172A !important;
        letter-spacing: -0.3px !important;
        line-height: 1.2 !important;
    }

    /* Indicador de variação/delta (se houver) */
    [data-testid="stMetricDelta"] {
        font-size: 0.75rem !important;
        font-weight: 600 !important;
    }
    /* ========================================================
       BOTÕES DE MÓDULOS NO TOPO (st.page_link)
       ======================================================== */
    /* Em repouso (Inativo) */
    div[data-testid="stPageLink"] a,
    [data-testid="stPageLink-NavLink"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 8px !important;
        padding: 6px 12px !important;
        min-height: 38px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 6px !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.02) !important;
        transition: all 0.15s ease-in-out !important;
        text-decoration: none !important;
    }

    div[data-testid="stPageLink"] a p,
    [data-testid="stPageLink-NavLink"] span {
        font-size: 0.80rem !important;
        line-height: 1 !important;
        margin: 0 !important;
        color: #475569 !important;
        font-weight: 600 !important;
    }

    div[data-testid="stPageLink"] span[data-testid="stIconMaterial"],
    div[data-testid="stPageLink-NavLink"] span[data-testid="stIconMaterial"] {
        font-size: 1.35rem !important;
        color: #007791 !important;
        vertical-align: middle !important;
        transition: all 0.2s ease-in-out !important;
    }

    /* Hover nos botões de módulo */
    div[data-testid="stPageLink"] a:hover,
    [data-testid="stPageLink-NavLink"]:hover {
        border-color: #00A3B4 !important;
        background-color: #F0FDFA !important;
        transform: translateY(-1px);
    }

    /* ========================================================
       BLOQUEIO FÍSICO DE CLIQUE PARA MÓDULOS DESABILITADOS
       ======================================================== */
    div[data-testid="stPageLink"] a[aria-disabled="true"],
    div[data-testid="stPageLink"] a[disabled],
    div[data-testid="stPageLink"] [aria-disabled="true"] {
        pointer-events: none !important; /* Desativa 100% da resposta ao clique no navegador */
        cursor: not-allowed !important;
        opacity: 0.55 !important;
        background-color: #F8FAFC !important;
        border: 1px solid #CBD5E1 !important;
        box-shadow: none !important;
        transform: none !important;
    }

    div[data-testid="stPageLink"] a[aria-disabled="true"] *,
    div[data-testid="stPageLink"] a[disabled] * {
        color: #94A3B8 !important;
    }  


    /* MÓDULO ATIVO (DESTAQUE CIANO SUAVE KAZIMM) */
    [data-testid="stPageLink"] a[aria-current="page"],
    [data-testid="stPageLink-NavLink"][aria-current="page"],
    div[data-testid="stPageLink"] a:has(strong) {
        background-color: #F0FDFA !important;
        border: 1.5px solid #00A3B4 !important;
        box-shadow: 0 2px 8px rgba(0, 163, 180, 0.15) !important;
    }

    [data-testid="stPageLink"] a[aria-current="page"] p,
    [data-testid="stPageLink"] a[aria-current="page"] span,
    div[data-testid="stPageLink"] a:has(strong) p,
    div[data-testid="stPageLink"] a:has(strong) strong {
        color: #007791 !important;
        font-weight: 700 !important;
    }

    [data-testid="stPageLink"] a[aria-current="page"] span[data-testid="stIconMaterial"],
    div[data-testid="stPageLink"] a:has(strong) span[data-testid="stIconMaterial"] {
        color: #00A3B4 !important;
    }

    /* ========================================================
       ABAS DE NAVEGAÇÃO INTERNA (st.tabs)
       ======================================================== */
    div[data-testid="stTabs"] [role="tablist"] {
        gap: 8px !important;
        border-bottom: 2px solid #E2E8F0 !important;
        padding-bottom: 2px !important;
        margin-bottom: 12px !important;
    }

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

    div[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
        color: #007791 !important;
        border-bottom: 3px solid #00A3B4 !important;
        font-weight: 700 !important;
    }

    /* ========================================================
       BOTÕES DE LINK (st.link_button COM TEXTO BRANCO NÍTIDO)
       ======================================================== */
    [data-testid="stLinkButton"] a,
    [data-testid="stLinkButton"] a *,
    [data-testid="stLinkButton"] a p,
    [data-testid="stLinkButton"] a span {
        color: #FFFFFF !important;
        fill: #FFFFFF !important;
        font-weight: 600 !important;
        text-decoration: none !important;
    }

    [data-testid="stLinkButton"] a:hover,
    [data-testid="stLinkButton"] a:hover * {
        color: #F8FAFC !important;
        text-decoration: none !important;
    }

    /* ========================================================
       BOTÕES UNIVERSAIS DO SISTEMA (st.button & st.form_submit_button)
       ======================================================== */
    /* 1. Botão Primário (Padrão Kazimm: Gradiente Ciano/Azul Petróleo) */
    div[data-testid="stButton"] button[kind="primary"],
    div[data-testid="stButton"] button[data-testid="baseButton-primary"],
    div[data-testid="stFormSubmitButton"] button[kind="primary"],
    div[data-testid="stFormSubmitButton"] button[data-testid="baseButton-primary"] {
        background: linear-gradient(135deg, #00A3B4 0%, #007791 100%) !important;
        border: 1px solid #007791 !important;
        border-radius: 8px !important;
        box-shadow: 0 2px 6px rgba(0, 119, 145, 0.25) !important;
        transition: all 0.2s ease-in-out !important;
    }

    /* Força texto, ícones e parágrafos em branco puro e nítido */
    div[data-testid="stButton"] button[kind="primary"] *,
    div[data-testid="stButton"] button[kind="primary"] p,
    div[data-testid="stButton"] button[kind="primary"] span,
    div[data-testid="stFormSubmitButton"] button[kind="primary"] *,
    div[data-testid="stFormSubmitButton"] button[kind="primary"] p,
    div[data-testid="stFormSubmitButton"] button[kind="primary"] span {
        color: #FFFFFF !important;
        fill: #FFFFFF !important;
        font-weight: 700 !important;
        letter-spacing: 0.3px !important;
    }

    /* Hover do Botão Primário */
    div[data-testid="stButton"] button[kind="primary"]:hover,
    div[data-testid="stFormSubmitButton"] button[kind="primary"]:hover {
        background: linear-gradient(135deg, #008D9C 0%, #005F74 100%) !important;
        border-color: #005F74 !important;
        box-shadow: 0 4px 12px rgba(0, 119, 145, 0.35) !important;
        transform: translateY(-1px) !important;
    }

    /* ========================================================
       BOTÃO SECUNDÁRIO PADRÃO KAZIMM (ESTILO PGMEI / OUTLINE SUAVE)
       ======================================================== */
    div[data-testid="stButton"] button[kind="secondary"],
    div[data-testid="stButton"] button[data-testid="baseButton-secondary"],
    div[data-testid="stButton"] button:not([kind="primary"]) {
        background-color: #F0F7FA !important;
        border: 1.5px solid #0176A1 !important;
        border-radius: 6px !important;
        height: 34px !important;
        min-height: 34px !important;
        padding: 0px 8px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 6px !important;
        transition: all 0.2s ease-in-out !important;
        width: 100% !important;
        box-sizing: border-box !important;
    }

    div[data-testid="stButton"] button[kind="secondary"] *,
    div[data-testid="stButton"] button[data-testid="baseButton-secondary"] *,
    div[data-testid="stButton"] button:not([kind="primary"]) * {
        color: #0176A1 !important;
        font-weight: 600 !important;
        font-size: 13px !important;
        line-height: 1 !important;
    }

    div[data-testid="stButton"] button[kind="secondary"]:hover,
    div[data-testid="stButton"] button:not([kind="primary"]):hover {
        background-color: #E0F2FE !important;
        border-color: #007791 !important;
        transform: translateY(-1px) !important;
    }
    
    div[data-testid="stButton"] button[kind="secondary"]:hover * {
        color: #007791 !important;
    }

    /* Hover do Botão Secundário */
    div[data-testid="stButton"] button[kind="secondary"]:hover,
    div[data-testid="stFormSubmitButton"] button[kind="secondary"]:hover {
        border-color: #00A3B4 !important;
        background-color: #F0FDFA !important;
        transform: translateY(-1px) !important;
    }

    div[data-testid="stButton"] button[kind="secondary"]:hover * {
        color: #007791 !important;
    }

    /* ========================================================
       TELA DE LOGIN CENTRALIZADA E PROPORCIONAL (APP.PY)
       ======================================================== */
    /* 1. Rótulos e caixas de entrada padronizadas */
    label, [data-testid="stWidgetLabel"] p {
        font-family: 'Inter', sans-serif !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        color: #1E293B !important;
    }

    div[data-baseweb="input"] {
        background-color: #F8FAFC !important;
        border: 1.5px solid #CBD5E1 !important;
        border-radius: 8px !important;
        transition: all 0.2s ease-in-out !important;
    }

    div[data-baseweb="input"]:focus-within {
        border-color: #007791 !important;
        background-color: #FFFFFF !important;
        box-shadow: 0px 0px 0px 3px rgba(0, 119, 145, 0.15) !important;
    }

    /* 2. Limita a largura máxima do formulário de login e adiciona sombra suave */
    form[data-testid="stForm"]:has(input[type="password"]) {
        max-width: 420px !important;
        margin: 0 auto !important;
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 12px !important;
        padding: 24px !important;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.04) !important;
    }

    

    /* Oculta marca d'água e menus nativos do Streamlit */
    #MainMenu {visibility: hidden; display: none !important;}
    header[data-testid="stHeader"] {visibility: hidden; display: none !important;}
    footer {visibility: hidden; display: none !important;}
    div[data-testid="stDecoration"] {display: none !important;}
    div[data-testid="stToolbar"] {display: none !important;}
    div[class*="viewerBadge"] {display: none !important;}
    .viewerBadge_container__1QSob {display: none !important;}
    #manage-app-button {display: none !important;}
    
    /* ========================================================
       DIVISORES E LINHAS HORIZONTAIS COMPACTAS (st.divider / ---)
       ======================================================== */
    hr, [data-testid="stDivider"] {
        margin-top: 8px !important;
        margin-bottom: 10px !important;
        border: none !important;
        border-top: 1px solid #E2E8F0 !important;
    }
    </style>
    """, unsafe_allow_html=True)


# =============================================================================
# CABEÇALHO SLIM INSTITUCIONAL
# =============================================================================
def exibir_cabecalho(
    titulo: str, 
    subtitulo: str = "Plataforma de Gestão Integrada", 
    versao: str = "v1.0.2-beta",
    logo_b64: str = None
):
    col_logo, col_texto, col_versao = st.columns([1.3, 7.2, 1.5], vertical_alignment="center")

    with col_logo:
        if logo_b64:
            st.markdown(
                f'<img src="{logo_b64}" style="max-height: 40px; width: auto; object-fit: contain;">', 
                unsafe_allow_html=True
            )
        elif CAMINHO_LOGO.exists():
            st.image(str(CAMINHO_LOGO), width=130)
        else:
            st.markdown("<h3 style='color:#007791; margin:0; font-weight:800;'>KAZIMM</h3>", unsafe_allow_html=True)

    with col_texto:
        st.markdown(f"""
        <div style="font-family: 'Montserrat', sans-serif; margin-left: 4px; line-height: 1.15;">
            <div style="font-size: 0.70rem; font-weight: 700; color: #00A3B4; text-transform: uppercase; letter-spacing: 0.8px;">
                {subtitulo}
            </div>
            <div style="font-size: 1.30rem; color: #007791; font-weight: 800; letter-spacing: -0.3px; margin-top: 1px;">
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

    st.markdown("<hr style='margin: 6px 0 10px 0; border: none; border-top: 1px solid #E2E8F0;'>", unsafe_allow_html=True)


# =============================================================================
# BANNER DE CONTEXTO DO CLIENTE ATIVO
# =============================================================================
def exibir_banner_cliente_ativo(
    nome_cliente: str, 
    regime: str = "MEI (Microempreendedor Individual)", 
    plano: str = "Plano MEI Pro", 
    cnpj: str = "", 
    **kwargs
):
    cnpj_html = f'<span style="color: #94A3B8; font-size: 0.78rem;"> • CNPJ: {cnpj}</span>' if cnpj else ""

    html_banner = (
        f'<div style="display: flex; justify-content: space-between; align-items: center; '
        f'background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; '
        f'padding: 8px 14px; margin-bottom: 8px;">'
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
        f'<span style="background-color: #E0F2FE; color: #007791; font-size: 0.72rem; font-weight: 700; padding: 3px 10px; border-radius: 12px; border: 1px solid #BAE6FD;">'
        f'{plano}'
        f'</span>'
        f'</div>'
        f'</div>'
    )
    st.markdown(html_banner, unsafe_allow_html=True)


# =============================================================================
# BOTÕES DE NAVEGAÇÃO GLOBAL ENTRE OS 4 MÓDULOS
# =============================================================================
def exibir_botoes_modulos_navegacao(modulo_atual: str = "contabil"):
    modulos = [
        {
            "id": "contabil",
            "nome": "Gestor Contábil",
            "page": "pages/1_Gestor_Contabil.py",
            "icon": ICONES.get("contabil", ":material/account_balance:"),
            "disable": False,
            "help":None
        },
        {
            "id": "contratos",
            "nome": "Gerador de Contratos",
            "page": "pages/2_Gerador_Contratos.py",
            "icon": ICONES.get("contratos", ":material/contract:"),
            "disabled": True,
            "help": "Estamos trabalhando neste módulo. Em breve disponível!"

        },
        {
            "id": "previdencia",
            "nome": "Empregados / Folha",
            "page": "pages/3_Empregados_Previdencia.py",
            "icon": ICONES.get("previdencia", ":material/badge:"),
            "disabled": False,
            "help":None
        },
        {
            "id": "fiscal",
            "nome": "Gestor Fiscal",
            "page": "pages/4_Gestor_Fiscal.py",
            "icon": ICONES.get("fiscal", ":material/receipt_long:"),
            "disabled": False,
            "help": None
        },
    ]

    col1, col2, col3, col4 = st.columns(4)
    for col, m in zip([col1, col2, col3, col4], modulos):
        with col:
            rotulo = f"**{m['nome']}**" if m["id"] == modulo_atual else m["nome"]
            st.page_link(
                m["page"], 
                label=rotulo, 
                icon=m["icon"], 
                disabled=m.get("disabled", False),
                help=m.get("help"),
                use_container_width=True
            )

# =============================================================================
# BARRA SUPERIOR UNIFICADA (NAVBAR)
# =============================================================================
def exibir_navbar_superior(modulo_ativo: str = "Gestor Contábil", versao: str = "v1.0.2-beta"):
    """
    Renderiza a barra superior unificada:
    [LOGO KAZIMM] -------- [MÓDULO ATIVO] -------- [VERSÃO / AMBIENTE]
    """
    html_navbar = f"""<div style="display: flex; justify-content: space-between; align-items: center; background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 10px 20px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.02);">
    <div style="display: flex; align-items: center; gap: 8px;">
        <span style="font-family: 'Montserrat', sans-serif; font-size: 1.25rem; font-weight: 800; color: #007791; letter-spacing: -0.5px;">KAZIMM</span>
        <span style="background: #F0FDFA; color: #00A3B4; font-size: 0.72rem; font-weight: 700; padding: 2px 8px; border-radius: 6px; border: 1px solid #CCFBF1;">SaaS</span>
    </div>
    <div style="display: flex; align-items: center; gap: 8px; background: linear-gradient(135deg, #00A3B4 0%, #007791 100%); color: #FFFFFF; padding: 6px 18px; border-radius: 20px; font-size: 0.88rem; font-weight: 600; box-shadow: 0 2px 8px rgba(0, 163, 180, 0.25);">
        <span>{modulo_ativo}</span>
    </div>
    <div style="display: flex; align-items: center; gap: 10px;">
        <span style="background: #F1F5F9; color: #475569; font-size: 0.75rem; font-weight: 600; padding: 4px 10px; border-radius: 6px; border: 1px solid #E2E8F0;">{versao}</span>
    </div>
</div>"""
    st.markdown(html_navbar, unsafe_allow_html=True)

# =============================================================================
# SANFONA UNIFICADA DE CONTEXTO
# =============================================================================
def exibir_painel_contexto(pagina_atual="contabil"):
    nome_cliente = st.session_state.get("cliente_nome_ativo", "Kazimm Gestão e Tecnologia")
    regime_cliente = st.session_state.get("cliente_regime_ativo", "MEI (Microempreendedor Individual)")
    plano_nome = st.session_state.get("plano_nome_ativo", "Plano MEI Pro")

    with st.expander("👤 Painel de Contexto e Módulos do Sistema", expanded=True):
        exibir_banner_cliente_ativo(nome_cliente=nome_cliente, regime=regime_cliente, plano=plano_nome)
        exibir_botoes_modulos_navegacao(modulo_atual=pagina_atual)


# =============================================================================
# RODAPÉ INSTITUCIONAL SLIM
# =============================================================================
def exibir_rodape_institucional(versao: str = "v1.0.2-beta", status_servico: str = "Supabase Conectado"):
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
<div style="margin-top: 30px; padding-top: 12px; padding-bottom: 8px; border-top: 1px solid #E2E8F0; display: flex; justify-content: space-between; align-items: center; font-size: 0.78rem; color: #64748B;">
    <div>© 2026 <strong>Kazimm Gestão & Tecnologia</strong> • Todos os direitos reservados.</div>
    <div style="display: flex; align-items: center; gap: 16px;">
        <div style="display: flex; align-items: center; gap: 6px;">
            <span class="status-dot"></span>
            <span style="font-weight: 600; color: #166534;">{status_servico}</span>
        </div>
        <span>•</span>
        <span style="background: #F1F5F9; padding: 2px 8px; border-radius: 4px; font-weight: 600;">{versao}</span>
        <span>•</span>
        <a href="[https://wa.me/5521972700481?text=Olá,%20estou%20testando%20o%20Kazimm%20ERP](https://wa.me/55SEUNUMERO?text=Olá,%20estou%20testando%20o%20Kazimm%20ERP)" style="color: #007791; text-decoration: none; font-weight: 600;">Suporte VIP</a>
    </div>
</div>"""
    st.markdown(html_rodape, unsafe_allow_html=True)


# =============================================================================
# UTILITÁRIOS GLOBAIS DE FORMATAÇÃO E CACHE (COLUNA ZERO / ESCOPO GLOBAL)
# =============================================================================
def formatar_brl(valor) -> str:
    if valor is None:
        return "R$ 0,00"
    try:
        if isinstance(valor, str):
            val_limpo = valor.replace("R$", "").strip()
            if "," in val_limpo and "." in val_limpo:
                val_limpo = val_limpo.replace(".", "").replace(",", ".")
            elif "," in val_limpo:
                val_limpo = val_limpo.replace(",", ".")
            num = float(val_limpo)
        else:
            num = float(valor)

        return f"R$ {num:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return "R$ 0,00"


def limpar_cache():
    st.cache_data.clear()


# Aliases de retrocompatibilidade
aplicar_estilo_moderno = aplicar_tema_global
exibir_menu_modulos_topo = exibir_botoes_modulos_navegacao