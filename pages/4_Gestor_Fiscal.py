import streamlit as st
import pandas as pd
from datetime import datetime, date

from database import (
    get_connection,
    carregar_clientes,
    carregar_dados_cliente_ativo,
    carregar_config_fiscal,
    carregar_notas_fiscais,
    limpar_cache_fiscal,
    limpar_cache
)

from services.fiscal_service import (
    cadastrar_ou_atualizar_empresa,
    emitir_nfse,
    consultar_nfse as consultar_status_nfse,
    limpar_documento
)

# Garante o funcionamento da chamada na linha 242
consultar_status_nfse = consultar_nfse

# -------------------------------------------------------------
# CONFIGURAÇÃO DE SESSÃO E CONTEXTO MULTI-TENANT
# -------------------------------------------------------------
st.title("Gestor Fiscal - Emissor de NFS-e")

# RECUPERAÇÃO SEGURA DO ID DO UTILIZADOR (COMPATÍVEL COM OBJETO SUPABASE OU DICIONÁRIO)
user_obj = st.session_state.get("user")
user_id_atual = st.session_state.get("user_id")

#INÍCIO DO BLOCO
if not user_id_atual and user_obj:
    user_id_atual = getattr(user_obj, "id", None) or (user_obj.get("id") if isinstance(user_obj, dict) else None)

cliente_ativo_id = st.session_state.get("cliente_ativo_id")

# Seletor de empresa caso não esteja definido previamente
# Seletor de empresa caso não esteja definido previamente
if not cliente_ativo_id:
    meus_clientes = carregar_clientes(user_id_atual) if user_id_atual else []
    
    # Validação compatível com lista ou DataFrame
    tem_clientes = len(meus_clientes) > 0 if isinstance(meus_clientes, (list, tuple)) else not meus_clientes.empty

    if not tem_clientes:
        st.warning("⚠️ Nenhuma empresa vinculada ao utilizador atual. Cadastre ou selecione um cliente no menu anterior.")
        st.stop()
    else:
        # Montagem das opções suportando lista de tuplos, lista de dicionários ou DataFrame
        if isinstance(meus_clientes, list):
            if meus_clientes and isinstance(meus_clientes[0], (list, tuple)):
                opcoes_cli = {cli[0]: cli[1] for cli in meus_clientes}
            elif meus_clientes and isinstance(meus_clientes[0], dict):
                opcoes_cli = {cli["id"]: cli["nome"] for cli in meus_clientes}
            else:
                opcoes_cli = {cli: f"Cliente #{cli}" for cli in meus_clientes}
        else:
            opcoes_cli = dict(zip(meus_clientes["id"], meus_clientes["nome"]))

        cliente_ativo_id = st.sidebar.selectbox(
            "Selecione a Empresa Ativa:",
            options=list(opcoes_cli.keys()),
            format_func=lambda x: opcoes_cli[x]
        )
        st.session_state["cliente_ativo_id"] = cliente_ativo_id
#fim do bloco


# Carrega os dados cadastrais e fiscais da memória RAM
df_info_cli = carregar_dados_cliente_ativo(cliente_ativo_id)
df_cfg = carregar_config_fiscal(cliente_ativo_id)
df_notas = carregar_notas_fiscais(cliente_ativo_id)

nome_empresa = df_info_cli.iloc[0]["nome"] if not df_info_cli.empty else f"Empresa #{cliente_ativo_id}"
cnpj_empresa = df_info_cli.iloc[0]["cnpj_cpf"] if not df_info_cli.empty else ""

st.sidebar.markdown(f"**Empresa Ativa:**\n\n`{nome_empresa}`")
st.sidebar.caption(f"CNPJ: {cnpj_empresa}")
st.sidebar.divider()

# -------------------------------------------------------------
# NAVEGAÇÃO EM ABAS
# -------------------------------------------------------------
tab_emitir, tab_historico, tab_config = st.tabs([
    "⚡ Emitir Nova NFS-e",
    "📋 Histórico & Documentos",
    "⚙️ Configuração Fiscal"
])

# -------------------------------------------------------------
# ABA 1: EMISSÃO DA NOTA FISCAL
# -------------------------------------------------------------
with tab_emitir:
    if df_cfg.empty:
        st.warning("⚙️ É necessário salvar a **Configuração Fiscal** da empresa na aba correspondente antes de emitir a primeira nota.")
    else:
        cfg = df_cfg.iloc[0]
        st.markdown("##### Dados do Tomador (Cliente contratante)")
        
        with st.form("form_emissao_nfse", clear_on_submit=False):
            col_t1, col_t2 = st.columns([1, 2])
            with col_t1:
                tomador_doc = st.text_input("CPF ou CNPJ do Tomador *", placeholder="Apenas números ou formatado").strip()
            with col_t2:
                tomador_nome = st.text_input("Razão Social / Nome Completo *", placeholder="Nome do cliente").strip()
            
            tomador_email = st.text_input("E-mail para envio da Nota (Opcional)", placeholder="cliente@email.com").strip()
            
            st.markdown("##### Detalhes do Serviço Prestado")
            col_s1, col_s2, col_s3 = st.columns([1.5, 1, 1])
            with col_s1:
                item_lc = st.text_input(
                    "Item LC 116 / Código do Serviço *",
                    value=str(cfg.get("item_lista_servico") or "010701"),
                    help="Código de 6 dígitos da NFS-e Nacional: 2 dígitos do Item, 2 do Subitem e 2 do Desdobro (Ex: 010701, 010101)"
                ).strip()
            with col_s2:
                aliq_iss = st.number_input(
                    "Alíquota ISS (%)",
                    value=float(cfg.get("aliquota_iss") or 0.0),
                    step=0.5,
                    format="%.2f",
                    help="Para MEI opte por 0.00 (ISS recolhido no DAS)"
                )
            with col_s3:
                valor_servico = st.number_input("Valor Total (R$) *", min_value=1.00, step=10.0, format="%.2f")
            
            desc_servico = st.text_area(
                "Discriminação dos Serviços *",
                placeholder="Descreva as atividades executadas...",
                height=100
            ).strip()
            
            integrar_caixa = st.checkbox("🟢 Registrar automaticamente a receita no Livro Caixa Contábil", value=True)
            
            btn_transmitir = st.form_submit_button("🚀 Autorizar e Emitir NFS-e")
            
            if btn_transmitir:
                if not tomador_doc or not tomador_nome or not desc_servico or valor_servico <= 0:
                    st.error("Preencha todos os campos obrigatórios assinalados com (*).")
                else:
                    # Gera uma referência única para rastreamento (Idempotência)
                    timestamp_ref = datetime.now().strftime("%Y%m%d%H%M%S")
                    referencia_unica = f"kz_cli{cliente_ativo_id}_{timestamp_ref}"
                    
                    dados_envio = {
                        "data_emissao": datetime.now().strftime("%Y-%m-%d"),
                        "cnpj_prestador": cfg.get("cnpj", ""),
                        "inscricao_municipal": cfg.get("inscricao_municipal", ""),
                        "codigo_municipio": cfg.get("codigo_municipio", ""),
                        "tomador_documento": tomador_doc,
                        "tomador_nome": tomador_nome,
                        "tomador_email": tomador_email,
                        "descricao_servico": desc_servico,
                        "item_lista_servico": item_lc,
                        "aliquota_iss": aliq_iss,
                        "valor_total": valor_servico
                    }
                    
                    with st.status("Transmissão do documento fiscal em curso...", expanded=True) as status_box:
                        try:
                            status_box.write("1/3 Enviando lote para a Focus NFe...")
                            resposta_api = emitir_nfse(referencia_unica, dados_envio)
                            status_retorno = resposta_api.get("status", "processando_autorizacao")
                            
                            status_box.write("2/3 Gravando registro fiscal no Supabase...")
                            conn = get_connection()
                            cur = conn.cursor()
                            cur.execute(
                                """
                                INSERT INTO notas_fiscais (
                                    cliente_id, tomador_nome, tomador_documento, tomador_email,
                                    descricao_servico, codigo_servico, valor_total, status,
                                    nuvem_fiscal_id
                                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
                                """,
                                (
                                    cliente_ativo_id, tomador_nome, limpar_documento(tomador_doc), tomador_email,
                                    desc_servico, item_lc, valor_servico, status_retorno, referencia_unica
                                )
                            )
                            id_nota = cur.fetchone()[0]
                            
                            # Integração contábil imediata
                            if integrar_caixa:
                                status_box.write("3/3 Criando lançamento no Livro Caixa...")
                                cur.execute(
                                    """
                                    INSERT INTO lancamentos (cliente_id, data, conta_debito, conta_credito, valor, historico)
                                    VALUES (%s, CURRENT_DATE, '1.1.1.01 - Caixa Geral', '3.1.1 - Receita de Serviços', %s, %s)
                                    """,
                                    (cliente_ativo_id, valor_servico, f"[NFS-e Ref #{referencia_unica}] {tomador_nome} - {desc_servico[:40]}")
                                )
                            
                            conn.commit()
                            conn.close()
                            
                            limpar_cache()
                            limpar_cache_fiscal()
                            
                            status_box.update(label="✅ Documento transmitido com sucesso!", state="complete", expanded=False)
                            st.success(f"NFS-e registrada sob o protocolo interno #{id_nota}. Consulte o status na aba Histórico.")
                            st.rerun()
                        except Exception as e:
                            status_box.update(label="❌ Erro na emissão", state="error", expanded=True)
                            st.error(f"Falha na transmissão da NFS-e: {e}")

# -------------------------------------------------------------
# ABA 2: HISTÓRICO E DOWNLOADS (PDF / XML)
# -------------------------------------------------------------
with tab_historico:
    st.markdown("##### Histórico de Documentos Fiscais Emitidos")
    
    if df_notas.empty:
        st.info("Nenhuma NFS-e emitida para esta empresa até ao momento.")
    else:
        for _, row in df_notas.iterrows():
            with st.container(border=True):
                c_detalhe, c_val, c_status, c_acoes = st.columns([3, 1.2, 1.5, 1.8])
                
                with c_detalhe:
                    data_str = pd.to_datetime(row["data_emissao"]).strftime("%d/%m/%Y")
                    st.write(f"**Tomador:** {row['tomador_nome']}")
                    st.caption(f"Doc: {row['tomador_documento']} | Data: {data_str} | Ref: {row['referencia_externa']}")
                
                with c_val:
                    st.metric("Valor Total", f"R$ {row['valor_total']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                
                with c_status:
                    st_atual = str(row["status"]).lower()
                    if "autorizad" in st_atual:
                        st.success("🟢 Autorizada")
                        if row["numero_nfse"]:
                            st.caption(f"Nº: {row['numero_nfse']}")
                    elif "erro" in st_atual or "rejeitad" in st_atual:
                        st.error("🔴 Rejeitada / Erro")
                        if row["mensagem_erro"]:
                            st.caption(str(row["mensagem_erro"]))
                    else:
                        st.warning("🟡 Em Processamento")
                        if st.button("🔄 Consultar", key=f"btn_sync_{row['id']}"):
                            dados_consulta = consultar_status_nfse(row["referencia_externa"])
                            if dados_consulta:
                                status_novo = dados_consulta.get("status", st_atual)
                                numero = dados_consulta.get("numero")
                                url_pdf = dados_consulta.get("url_danfse") or dados_consulta.get("caminho_danfse")
                                url_xml = dados_consulta.get("caminho_xml_nota_fiscal")
                                msg_erro = dados_consulta.get("mensagem_sefaz") or dados_consulta.get("erros")
                                
                                conn = get_connection()
                                cur = conn.cursor()
                                cur.execute(
                                    """
                                    UPDATE notas_fiscais 
                                    SET status = %s, numero_nfse = %s, pdf_url = %s, xml_url = %s, mensagem_erro = %s
                                    WHERE id = %s
                                    """,
                                    (status_novo, numero, url_pdf, url_xml, str(msg_erro) if msg_erro else None, row["id"])
                                )
                                conn.commit()
                                conn.close()
                                
                                limpar_cache_fiscal()
                                st.rerun()
                
                with c_acoes:
                    c_pdf, c_xml = st.columns(2)
                    with c_pdf:
                        if pd.notna(row.get("pdf_url")) and row["pdf_url"]:
                            st.link_button("📄 PDF", row["pdf_url"], use_container_width=True)
                    with c_xml:
                        if pd.notna(row.get("xml_url")) and row["xml_url"]:
                            st.link_button("💾 XML", row["xml_url"], use_container_width=True)

# -------------------------------------------------------------
# ABA 3: CONFIGURAÇÃO FISCAL DO CLIENTE
# -------------------------------------------------------------
with tab_config:
    st.markdown("##### Dados Cadastrais Fiscais da Empresa")
    
    val_cnpj = df_cfg.iloc[0]["cnpj"] if not df_cfg.empty else cnpj_empresa
    val_razao = df_cfg.iloc[0]["razao_social"] if not df_cfg.empty else nome_empresa
    val_fantasia = df_cfg.iloc[0]["nome_fantasia"] if not df_cfg.empty else ""
    val_im = df_cfg.iloc[0]["inscricao_municipal"] if not df_cfg.empty else ""
    val_cod_mun = df_cfg.iloc[0]["codigo_municipio"] if not df_cfg.empty and "codigo_municipio" in df_cfg.columns else ""#Municipio
    val_item = df_cfg.iloc[0]["item_lista_servico"] if not df_cfg.empty and df_cfg.iloc[0]["item_lista_servico"] else "010701"
    val_aliq = float(df_cfg.iloc[0]["aliquota_iss"] or 0.0) if not df_cfg.empty else 0.0
    
    with st.form("form_dados_fiscais_empresa"):
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            cfg_cnpj = st.text_input("CNPJ da Empresa *", value=str(val_cnpj)).strip()
            cfg_razao = st.text_input("Razão Social *", value=str(val_razao)).strip()
            cfg_item = st.text_input("Item Padrão LC 116", value=str(val_item)).strip()
        with col_c2:
            cfg_fantasia = st.text_input("Nome Fantasia", value=str(val_fantasia)).strip()
            cfg_im = st.text_input("Inscrição Municipal", value=str(val_im)).strip()
            cfg_cod_mun = st.text_input("Código IBGE do Município *", value=str(val_cod_mun or ""), help="Código de 7 dígitos da cidade da empresa (ex: 3550308)").strip()
            cfg_aliq = st.number_input("Alíquota ISS Padrão (%)", value=val_aliq, step=0.5, format="%.2f")
        
        salvar_config = st.form_submit_button("💾 Guardar e Sincronizar Emitente")
        
    #Início do BLOCO
        if salvar_config:
            if not cfg_cnpj or not cfg_razao:
                st.error("CNPJ e Razão Social são campos obrigatórios.")
            else:
                try:
                    # 1. Salva imediatamente no banco local (Supabase)
                    conn = get_connection()
                    cur = conn.cursor()
                    if df_cfg.empty:
                        cur.execute(
                            """
                            INSERT INTO configuracoes_fiscais (
                            cliente_id, cnpj, razao_social, nome_fantasia, 
                            inscricao_municipal, item_lista_servico, aliquota_iss, codigo_municipio
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (cliente_ativo_id, cfg_cnpj, cfg_razao, cfg_fantasia, cfg_im, cfg_item, cfg_aliq, cfg_cod_mun)
                    )
                    else:
                        cur.execute(
                            """
                            UPDATE configuracoes_fiscais 
                            SET cnpj = %s, razao_social = %s, nome_fantasia = %s, 
                                inscricao_municipal = %s, item_lista_servico = %s, aliquota_iss = %s, codigo_municipio = %s 
                            WHERE cliente_id = %s
                            """,
                            (cfg_cnpj, cfg_razao, cfg_fantasia, cfg_im, cfg_item, cfg_aliq, cfg_cod_mun, cliente_ativo_id)
                        )
                    conn.commit()
                    conn.close()
                    limpar_cache_fiscal()

                    # 2. Tenta sincronizar com a Focus NFe
                    msg_aviso = ""
                    try:
                        cadastrar_ou_atualizar_empresa({
                            "cnpj": cfg_cnpj,
                            "razao_social": cfg_razao,
                            "nome_fantasia": cfg_fantasia,
                            "inscricao_municipal": cfg_im,
                            "regime_tributario": 1
                        })
                        st.success("✅ Configurações salvas e empresa sincronizada na Focus NFe com sucesso!")
                    except Exception as err_api:
                        st.warning(f"⚠️ Configurações salvas no Kazimm! A sincronização com a Focus NFe retornou: {err_api}")

                    st.rerun()

                except Exception as ex:
                    st.error(f"Erro ao salvar configurações no banco: {ex}")
        #FINAL DO BLOCO