import streamlit as st
import urllib.parse
import resend
import base64        # NOVO: Necessário para converter os PDFs em anexo para o Resend
import requests      # NOVO: Necessário para baixar o PDF da NFS-e direto da Focus NFe

# ==============================================================================
# 1. FUNÇÕES DO MÓDULO CONTAS A PAGAR & GUIA DAS-MEI (PERMANECEM 100% INTACTAS)
# ==============================================================================

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


# ==============================================================================
# 2. NOVAS FUNÇÕES: DISPARO DE NFS-e + COBRANÇA (BOLETO / PIX)
# ==============================================================================

def gerar_link_whatsapp_cobranca_nfse(telefone, nome_tomador, descricao, valor, vencimento, url_nfse, pix_copia_cola=None):
    """
    Gera link do WhatsApp para o tomador do serviço com:
    - Link oficial do PDF da NFS-e (Focus NFe)
    - Valor e Vencimento
    - Código Pix Copia e Cola formatado
    """
    if not telefone or str(telefone).strip() == '-':
        return None
        
    telefone_limpo = "".join(filter(str.isdigit, str(telefone)))
    if len(telefone_limpo) < 10:
        return None
        
    valor_fmt = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    
    msg = (
        f"Olá, *{nome_tomador}*!\n\n"
        f"Segue a sua Nota Fiscal de Serviços referente a: *{descricao}*.\n"
        f"💰 *Valor:* R$ {valor_fmt}\n"
        f"📅 *Vencimento:* {vencimento}\n\n"
        f"📄 *Visualizar NFS-e Oficial:* {url_nfse}\n"
    )
    
    if pix_copia_cola:
        msg += f"\n📱 *Pix Copia e Cola:*\n`{pix_copia_cola}`\n"
        
    msg += "\nCaso já tenha efetuado o pagamento, por favor desconsidere este aviso. Obrigado!"
    
    texto_encoded = urllib.parse.quote(msg)
    return f"https://wa.me/55{telefone_limpo}?text={texto_encoded}"


def disparar_cobranca_nfse_email(
    destinatario_email,
    nome_tomador,
    descricao_servico,
    valor,
    vencimento,
    url_pdf_nfse,
    arquivo_boleto_bytes=None,
    nome_arquivo_boleto="boleto_cobranca.pdf",
    pix_copia_cola=None
):
    """
    Dispara e-mail profissional via Resend anexando os arquivos em PDF:
    1. O PDF da NFS-e baixado da Focus NFe.
    2. O Boleto bancário enviado pelo usuário (se houver).
    3. Pix Copia e Cola em destaque no corpo do e-mail.
    """
    chave_resend = (
        st.secrets.get("RESEND_API_KEY")
        or st.secrets.get("resend", {}).get("api_key")
        or st.secrets.get("resend", {}).get("RESEND_API_KEY")
        or st.secrets.get("focusnfe", {}).get("RESEND_API_KEY")
    )

    if not chave_resend:
        return False, "Chave Resend não configurada no secrets.toml."

    resend.api_key = chave_resend
    anexos = []

    # 1. Faz o download silencioso do PDF da NFS-e a partir da Focus NFe
    if url_pdf_nfse:
        try:
            resp = requests.get(url_pdf_nfse, timeout=12)
            if resp.status_code == 200:
                nfse_b64 = base64.b64encode(resp.content).decode("utf-8")
                anexos.append({
                    "filename": "NFSe_Eletronica.pdf",
                    "content": nfse_b64
                })
        except Exception as e:
            print(f"Aviso ao baixar PDF da Focus NFe: {e}")

    # 2. Anexa o Boleto bancário enviado pelo MEI (caso tenha sido feito upload)
    if arquivo_boleto_bytes:
        try:
            boleto_b64 = base64.b64encode(arquivo_boleto_bytes).decode("utf-8")
            anexos.append({
                "filename": nome_arquivo_boleto,
                "content": boleto_b64
            })
        except Exception as e:
            print(f"Aviso ao converter boleto em base64: {e}")

    valor_fmt = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    
    # Bloco visual do Pix (Copia e Cola)
    bloco_pix = ""
    if pix_copia_cola:
        bloco_pix = f"""
        <div style="background-color: #f8fafc; border: 1px dashed #0176a1; padding: 12px; border-radius: 6px; margin: 15px 0;">
            <p style="margin: 0 0 6px 0; font-weight: bold; color: #0176a1; font-size: 13px;">📱 Pagamento via Pix (Copia e Cola):</p>
            <code style="word-break: break-all; font-size: 11px; color: #334155; display: block; background: #fff; padding: 8px; border-radius: 4px; border: 1px solid #cbd5e1;">{pix_copia_cola}</code>
        </div>
        """

    corpo_html = f"""
    <div style="font-family: Arial, sans-serif; color: #333; max-width: 620px; border: 1px solid #e2e8f0; border-radius: 8px; padding: 24px;">
        <h3 style="color: #0176a1; margin-top: 0;">Nota Fiscal de Serviços & Cobrança</h3>
        <p>Prezado(a) <strong>{nome_tomador}</strong>,</p>
        <p>Encaminhamos a sua Nota Fiscal de Serviços referente a: <em>{descricao_servico}</em>.</p>
        
        <table style="width: 100%; border-collapse: collapse; margin: 16px 0;">
            <tr style="background-color: #f1f5f9;">
                <td style="padding: 8px; font-weight: bold;">Valor dos Serviços:</td>
                <td style="padding: 8px; text-align: right; font-weight: bold; color: #00875a;">R$ {valor_fmt}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #e2e8f0;">Data de Vencimento:</td>
                <td style="padding: 8px; text-align: right; border-bottom: 1px solid #e2e8f0;">{vencimento}</td>
            </tr>
        </table>

        {bloco_pix}

        <p style="font-size: 13px; color: #475569;">
            📎 Os documentos originais em PDF (<strong>NFS-e Oficial</strong> e <strong>Boleto Bancário</strong>) encontram-se anexados a este e-mail.
        </p>

        <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 24px 0 12px 0;">
        <p style="font-size: 11px; color: #94a3b8; margin: 0;">Mensagem automática gerada pelo Kazimm ERP.</p>
    </div>
    """

    try:
        resend.Emails.send({
            "from": "Kazimm Faturamento <luizcasemiro@kazimm.com.br>",
            "to": destinatario_email,
            "subject": f"🧾 NFS-e & Cobrança: {descricao_servico} - Vencimento {vencimento}",
            "html": corpo_html,
            "attachments": anexos
        })
        return True, "E-mail de cobrança com anexos enviado com sucesso!"
    except Exception as e:
        return False, f"Erro no disparo via Resend: {e}"