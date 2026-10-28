import streamlit as st

def aplicar_estilo_moderno():
    st.markdown("""
    <style>
    /* 1. Tipografia global limpa */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* 2. Barra lateral estilo Omie */
    [data-testid="stSidebar"] {
        background: #F8FAFC !important;
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

    /* 4. Estilo do Cartão (label) */
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

    /* OCULTA APENAS O CÍRCULO E O INPUT, PRESERVANDO O TEXTO */
    /* Esconde o input real para que não ocupe espaço */
    div[role="radiogroup"] label input {
        display: none !important;
    }
    
    /* Esconde a representação visual (bolinha) desenhada pelo Streamlit/BaseWeb */
    div[role="radiogroup"] label > div:first-child:not([data-testid="stMarkdownContainer"]) {
        display: none !important;
    }

    /* 5. Garante que o texto (p) seja exibido corretamente e preencha o botão */
    div[role="radiogroup"] label p {
        display: block !important;
        color: #334155 !important;
        font-weight: 600 !important;
        font-size: 0.90rem !important;
        margin: 0 !important;
        width: 100% !important;
    }

    /* Hover: Elevação sutil e borda verde-azulada */
    div[role="radiogroup"] label:hover {
        border-color: #00A3B4 !important;
        background-color: #F0FDFA !important;
        transform: translateX(4px);
        box-shadow: 0 4px 12px rgba(0, 163, 180, 0.12) !important;
    }

    /* 6. Cartão Ativo / Selecionado (Destaque Omie com Gradiente Turquesa) */
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

    /* 7. Botão Sair / Logout */
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
    </style>
    """, unsafe_allow_html=True)