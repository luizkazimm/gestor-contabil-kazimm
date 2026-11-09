import streamlit as st
import urllib.parse
import resend

def gerar_link_whatsapp(telefone, nome_empresa, descricao_conta, valor, data_venc, status):
    """Gera um link clicável do WhatsApp Web/App com a mensagem de cobrança formatada."""
    if not telefone or str(telefone).strip() == '-':
        return None
        
    telefone_limpo = "".join(filter(str.isdigit, str(telefone)))
    if len(telefone_limpo) < 10:  # Evita telefones inválidos
        return None
        
    venc_str = data_venc.strftime('%d/%m/%Y')
    valor_fmt = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    
    if status == "VENCIDA":
        mensagem = f"Olá! Consta em nosso sistema que a conta *{descricao_conta}* da empresa *{nome_empresa}*, no valor de *R$ {valor_fmt}*, venceu no dia *{venc_str}*. Por favor, verifique para evitar encargos."
    elif status == "HOJE":
        mensagem = f"Olá! Lembramos que a conta *{descricao_conta}* da empresa *{nome_empresa}*, no valor de *R$ {valor_fmt}*, vence *HOJE* ({venc_str})."
    else:
        mensagem = f"Olá! Lembramos que a conta *{descricao_conta}* da empresa *{nome_empresa}*, no valor de *R$ {valor_fmt}*, vence no dia *{venc_str}*."
        
    texto_url = urllib.parse.quote(mensagem)
    return f"https://wa.me/55{telefone_limpo}?text={texto_url}"


@st.dialog("✉️ Enviar Lembrete por E-mail")
def modal_enviar_email(nome_cliente, descricao, valor, vencimento):
    """Modal para confirmar o e-mail do destinatário e disparar a notificação via Resend."""
    st.markdown(f"**Conta/Guia:** {descricao} <br> **Vencimento:** {vencimento}", unsafe_allow_html=True)
    st.write("")
    email_dest = st.text_input("E-mail de Destino do Cliente", placeholder="cliente@email.com")
    
    if st.button("Disparar E-mail via Resend", type="primary", use_container_width=True):
        if email_dest:
            try:
                # Captura flexível da chave (na raiz, em [resend] ou em [focusnfe])
                chave_resend = (
                    st.secrets.get("RESEND_API_KEY")
                    or st.secrets.get("resend", {}).get("api_key")
                    or st.secrets.get("resend", {}).get("RESEND_API_KEY")
                    or st.secrets.get("focusnfe", {}).get("RESEND_API_KEY")
                )
                
                if not chave_resend:
                    st.error("Chave do Resend não encontrada no arquivo secrets.toml.")
                    st.stop()
                
                resend.api_key = chave_resend
                
                valor_fmt = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                
                resend.Emails.send({
                    "from": "Kazimm ERP <luizcasemiro@kazimm.com.br>", # Domínio validado no Resend
                    "to": email_dest,
                    "subject": f"⚠️ Lembrete de Vencimento: {descricao} - Kazimm",
                    "html": f"""
                    <div style="font-family: Arial, sans-serif; color: #333; max-width: 600px; border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px;">
                        <h3 style="color: #0176a1; margin-top: 0;">Lembrete de Conta a Pagar</h3>
                        <p>Olá, <strong>{nome_cliente}</strong>.</p>
                        <p>A conta/guia <strong>{descricao}</strong> no valor de <strong>R$ {valor_fmt}</strong> tem vencimento programado para <strong>{vencimento}</strong>.</p>
                        <p>Acesse o Kazimm ERP ou o portal oficial para liquidar a fatura e evitar encargos adicionais.</p>
                        <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 20px 0;">
                        <p style="font-size: 12px; color: #64748b; margin: 0;">Mensagem automática gerada pelo Kazimm Gestão e Tecnologia.</p>
                    </div>
                    """
                })
                st.toast(f"E-mail enviado com sucesso para {email_dest}!", icon="✅")
                st.rerun()
            except Exception as e:
                st.error(f"Erro na API do Resend: {e}")
        else:
            st.warning("Informe um e-mail válido para o disparo.")