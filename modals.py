import streamlit as st
from database import salvar_novo_historico_padrao
from notificacoes import disparar_cobranca_nfse_email, gerar_link_whatsapp_cobranca_nfse
from datetime import date

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

# ==============================================================
# MODAL DE DISPARO DE COBRANÇA + NFS-e (EMAIL & WHATSAPP)
# ==============================================================
@st.dialog("🧾 Enviar NFS-e & Cobrança ao Cliente")
def modal_enviar_cobranca_nfse(nota_info):
    """
    Janela modal para envio integrado:
    - NFS-e oficial gerada na Focus NFe
    - Boleto anexado (opcional)
    - Pix Copia e Cola (opcional)
    """
    st.markdown(f"**Tomador:** {nota_info.get('tomador_nome', 'Cliente')}")
    st.caption(f"NFS-e Nº: **{nota_info.get('numero', 'S/N')}** | Valor do Serviço: **R$ {nota_info.get('valor', 0.0):,.2f}**")
    
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        email_dest = st.text_input("E-mail do Tomador", value=nota_info.get('tomador_email') or "")
    with col_d2:
        tel_dest = st.text_input("WhatsApp com DDD", value=nota_info.get('tomador_telefone') or "", placeholder="21999998888")

    dt_venc = st.date_input("Vencimento da Cobrança", value=date.today(), format="DD/MM/YYYY")
    venc_str = dt_venc.strftime("%d/%m/%Y")

    st.markdown("---")
    st.markdown("##### 📎 Dados de Pagamento (Boleto do seu Banco ou Pix)")
    
    arquivo_boleto = st.file_uploader(
        "Anexar Boleto do seu Banco (PDF Opcional)", 
        type=["pdf"], 
        key=f"up_bol_{nota_info.get('id')}"
    )
    
    pix_copia_cola = st.text_input(
        "Chave Pix ou Código Copia e Cola (Opcional)", 
        placeholder="Cole aqui o código Pix do seu banco...",
        key=f"pix_{nota_info.get('id')}"
    )

    st.markdown("---")
    col_b1, col_b2 = st.columns(2)

    # 1. DISPARO POR E-MAIL (RESEND COM ANEXOS)
    with col_b1:
        if st.button("✉️ Enviar por E-mail", type="primary", use_container_width=True):
            if not email_dest:
                st.warning("Preencha o e-mail do tomador.")
            else:
                boleto_bytes = arquivo_boleto.getvalue() if arquivo_boleto else None
                nome_bol = arquivo_boleto.name if arquivo_boleto else "boleto.pdf"
                
                with st.spinner("Empacotando NFS-e, Boleto e enviando..."):
                    sucesso, msg = disparar_cobranca_nfse_email(
                        destinatario_email=email_dest,
                        nome_tomador=nota_info.get('tomador_nome', 'Cliente'),
                        descricao_servico=nota_info.get('discriminacao', 'Prestação de Serviços'),
                        valor=float(nota_info.get('valor', 0.0)),
                        vencimento=venc_str,
                        url_pdf_nfse=nota_info.get('url_danfse'),
                        arquivo_boleto_bytes=boleto_bytes,
                        nome_arquivo_boleto=nome_bol,
                        pix_copia_cola=pix_copia_cola
                    )
                    if sucesso:
                        st.toast("✅ E-mail com NFS-e e Cobrança enviado com sucesso!", icon="🎉")
                        st.rerun()
                    else:
                        st.error(msg)

    # 2. DISPARO POR WHATSAPP (LINK DIRETO DA NFS-E + PIX)
    with col_b2:
        link_wa = gerar_link_whatsapp_cobranca_nfse(
            telefone=tel_dest,
            nome_tomador=nota_info.get('tomador_nome', 'Cliente'),
            descricao=nota_info.get('discriminacao', 'Serviço prestado'),
            valor=float(nota_info.get('valor', 0.0)),
            vencimento=venc_str,
            url_nfse=nota_info.get('url_danfse', ''),
            pix_copia_cola=pix_copia_cola
        )
        if link_wa:
            st.markdown(
                f"""
                <a href="{link_wa}" target="_blank" style="
                    display: flex; align-items: center; justify-content: center; gap: 6px;
                    width: 100%; background-color: #25D366; color: white; border-radius: 6px;
                    padding: 8px 0; font-weight: 600; font-size: 14px; text-decoration: none;
                ">
                    💬 Abrir WhatsApp
                </a>
                """,
                unsafe_allow_html=True
            )
        else:
            st.button("💬 WhatsApp Indisponível", disabled=True, use_container_width=True, help="Informe o telefone com DDD.")