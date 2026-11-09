import streamlit as st
from database import salvar_novo_historico_padrao

# ==============================================================
# MODAL GLOBAL: CADASTRO DE HISTÓRICO PADRÃO
# ==============================================================
@st.dialog("➕ Cadastrar Novo Histórico Padrão")
def modal_novo_historico(cliente_id):
    st.markdown("Crie um modelo reutilizável para agilizar seus lançamentos contábeis.")
    
    nh_cod = st.text_input("Código de Referência", placeholder="Ex: INTERNET", key="dlg_nh_cod")
    nh_desc = st.text_input("Identificação / Título", placeholder="Ex: Pagamento de Internet Fibra", key="dlg_nh_desc")
    nh_texto = st.text_area("Texto do Histórico Padrão", placeholder="Ex: Pg. ref. plano de internet corporativa - Fatura:", key="dlg_nh_txt")
    
    if st.button("Salvar Histórico", type="primary", use_container_width=True, key="dlg_btn_salvar"):
        if nh_desc.strip() and nh_texto.strip():
            sucesso, msg = salvar_novo_historico_padrao(
                cliente_id=cliente_id,
                codigo=nh_cod or "GERAL",
                descricao=nh_desc,
                texto_padrao=nh_texto
            )
            if sucesso:
                st.toast("✅ Histórico padrão salvo com sucesso!", icon="🎉")
                st.rerun()  # Fecha o modal na hora e atualiza os selectboxes
            else:
                st.error(msg)
        else:
            st.warning("Preencha ao menos a Identificação e o Texto do histórico.")