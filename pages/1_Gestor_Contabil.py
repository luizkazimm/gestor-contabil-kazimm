import sys
from pathlib import Path
# Garante que o Linux encontre os módulos da raiz (ui_theme, database, etc.)
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from datetime import datetime, date
import streamlit as st
import io
import pandas as pd
import base64
from database import (
    get_connection, 
    init_db, 
    carregar_clientes, 
    carregar_plano_contas, 
    carregar_lancamentos,
    carregar_provisoes_pendentes,
    carregar_dados_cliente_ativo,
    carregar_todos_clientes_completos, 
    limpar_cache,
    carregar_historicos_padrao,
    salvar_novo_historico_padrao,
    verificar_e_agendar_das_mensal,
    validar_pertencimento_cliente
)

from supabase import create_client

from modals import modal_novo_historico
from notificacoes import gerar_link_whatsapp, modal_enviar_email

from ui_theme import (
    ICONES, 
    aplicar_tema_global, 
    exibir_navbar_superior, 
    exibir_banner_cliente_ativo, 
    exibir_botoes_modulos_navegacao, 
    exibir_rodape_institucional,
    exibir_cabecalho
)

# Aplica o CSS global (cores, fontes e remoção de marcas do Streamlit Cloud)
aplicar_tema_global()

exibir_cabecalho(
    titulo="Gestor Contábil", 
    subtitulo="VISÃO FINANCEIRA & LIVRO CAIXA", 
    versao="v1.0.2-beta"
)

# 3. IDENTIFICAÇÃO DO CLIENTE ATIVO (Conforme 1ª faixa interna do manuscrito)
with st.expander(
    f"{ICONES.get('cliente', ':material/person:')} Painel de Contexto e Módulos do Sistema", 
    expanded=True
):
    nome_ativo = st.session_state.get("cliente_ativo_nome", "Kazimm Gestão e Tecnologia")
    regime_ativo = st.session_state.get("cliente_ativo_regime", "MEI (Microempreendedor Individual)")
    plano_ativo = st.session_state.get("cliente_ativo_plano", "Plano MEI Pro")

    exibir_banner_cliente_ativo(nome_cliente=nome_ativo, regime=regime_ativo, plano=plano_ativo)

    # 4. BOTÕES DOS 4 MÓDULOS (Substitui o antigo 'exibir_menu_modulos_topo')
    exibir_botoes_modulos_navegacao(modulo_atual="contabil")


st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)

def processar_logo_empresa(arquivo_imagem):
    """Converte o arquivo de imagem enviado para string Base64 utilizável em tags HTML."""
    if arquivo_imagem is None:
        return None
    try:
        tipo = arquivo_imagem.type
        
        dados_bytes = arquivo_imagem.getvalue()
        if not dados_bytes:
            return None
        b64_string = base64.b64encode(dados_bytes).decode('utf-8')
        return f"data:{tipo};base64,{b64_string}"
    except Exception as e:
        st.error(f"Erro ao converter logotipo: {e}")
        return None
    
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
except Exception as e:
    supabase = None

REGRAS_PLANOS = {
    'gratis': {
        'nome': 'Plano MEI Gratuito',
        'limite_lancamentos_mes': 25,
        'importacao_lote': False,
        'provisoes': False,
        'dasn_simei': False,
        'partida_dupla': False,
        'folha_pagamento': False
    },
    'pro': {
        'nome': 'Plano MEI Pro',
        'limite_lancamentos_mes': 999999,
        'importacao_lote': True,
        'provisoes': True,
        'dasn_simei': True,
        'partida_dupla': False,
        'folha_pagamento': True
    },
    'contador': {
        'nome': 'Plano Escritório / Contador',
        'limite_lancamentos_mes': 999999,
        'importacao_lote': True,
        'provisoes': True,
        'dasn_simei': True,
        'partida_dupla': True,
        'folha_pagamento': True
    }
}

def exibir_bloqueio_upgrade(nome_recurso: str, plano_minimo: str = "pro"):
    """Exibe um card de paywall quando o usuário tenta acessar um recurso fora do seu plano."""
    st.warning(f"🔒 **Recurso Exclusivo do {REGRAS_PLANOS.get(plano_minimo, {}).get('nome', 'Plano Pago')}**")
    st.markdown(
        f"""
        <div style="background-color: #f8f9fa; border: 1px solid #e9ecef; border-radius: 8px; padding: 25px; margin: 15px 0;">
            <h4 style="color: #1e293b; margin-top: 0;">Desbloqueie o módulo de <strong>{nome_recurso}</strong></h4>
            <p style="color: #64748b; font-size: 14px; line-height: 1.5;">
                O cliente ativo está enquadrado no <strong>Plano Gratuito</strong>. Faça o upgrade para automatizar sua rotina fiscal e contábil sem limitações manuais.
            </p>
            <ul style="color: #475569; font-size: 13px;">
                <li>Importações em lote via extratos bancários (.OFX) e Excel;</li>
                <li>Agendamento e controle de Contas a Pagar e Guias DAS;</li>
                <li>Apuração anual automática com link direto para o portal DASN-SIMEI;</li>
                <li>Lançamentos contábeis mensais ilimitados.</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True
    )
    col_cta1, col_cta2 = st.columns([1, 2])
    with col_cta1:
        st.link_button(
            label="⭐ Fazer Upgrade Agora",
            url="https://www.asaas.com/000/c/serwm0gti8wzfqe7",
            type="primary",
            use_container_width=False
)
    with col_cta2:
        st.caption("Fale com o suporte ou gerencie sua assinatura pelo painel administrativo.")

if 'user' not in st.session_state or st.session_state.user is None:
    st.warning
    (" Você precisa fazer login para acessar o Gestor Contábil.")
    st.stop()
    

clientes_cadastrados = carregar_clientes(st.session_state.user.id)

if clientes_cadastrados:
    opcoes_clientes = {cli[1]: cli[0] for cli in clientes_cadastrados}

    cliente_selecionado = st.sidebar.selectbox("Cliente em Atendimento", list(opcoes_clientes.keys()))

    st.session_state.cliente_id_ativo = opcoes_clientes[cliente_selecionado]
else:
    st.session_state.cliente_id_ativo = None
    st.info("Nenhum cliente cadastrado. Cadastre uma empresa para começar os lançamentos.")


def formatar_brl(valor):
    return f"R$ {valor:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")

plano_usuario = st.session_state.get("plano_ativo", "gratis")
regras = REGRAS_PLANOS.get(plano_usuario, REGRAS_PLANOS['gratis'])

ICONES_MENU = {
    "Dashboard": f"{ICONES['dashboard']} Dashboard",
    "Cadastrar Contas": f"{ICONES['fornecedor']} Cadastrar Contas",
    "Lançamentos": f"{ICONES['adicionar']} Lançamentos",
    "Importação": f"{ICONES['importar']} Importação",
    "Contas a Pagar": f"{ICONES['provisoes']} Contas a Pagar",
    "Conciliação Bancária": f"{ICONES['conciliacao']} Conciliação Bancária",
    "Plano de Contas": f"{ICONES['plano_contas']} Plano de Contas",
    "Relatório por Categoria": f"{ICONES['dre']} Relatório por Categoria",
}

item_importacao = "Importação em Lote" if regras['importacao_lote'] else f"🔒 Importação em Lote (PRO)"
item_provisoes = "Contas a Pagar" if regras['provisoes'] else f"🔒 Contas a Pagar (PRO)"

menu_opcoes = [
    "Dashboard",
    "Cadastrar Contas",
    "Lançamentos",
    "Importação",
    item_provisoes,
    "Conciliação Bancária",
    "Plano de Contas",
    "Relatório por Categoria"
]

opcao = st.sidebar.radio(
    "Navegação Principal", 
    menu_opcoes,
    format_func=lambda x: ICONES_MENU.get(x, x)
)

cliente_ativo_id = st.session_state.get("cliente_id_ativo")

if cliente_ativo_id:
    # -------------------------------------------------------------------------
    # TRAVA DE SEGURANÇA MULTI-TENANT (ANTI-TAMPERING)
    # -------------------------------------------------------------------------
    user_obj = st.session_state.get("user")
    user_id_atual = st.session_state.get("user_id") or (getattr(user_obj, "id", None) if user_obj else None)
    # -----------------------------------------------------------------------------
    # TESTE TEMPORÁRIO DE SEGURANÇA (Para testar, descomente a linha abaixo):
    #cliente_ativo_id = 999999
    # -----------------------------------------------------------------------------
    # Se não identificar o usuário logado OU se a empresa NÃO pertencer a ele -> BLOQUEIO
    if not user_id_atual or not validar_pertencimento_cliente(cliente_ativo_id, user_id_atual):
        st.error("🚨 Acesso Não Autorizado: Esta empresa não pertence à sua conta.")
        st.session_state["cliente_id_ativo"] = None
        st.stop()

    # 1. Leitura 100% em memória RAM (zero latência na nuvem)
    df_lanc_global = carregar_lancamentos(cliente_ativo_id)
    df_prov_global = carregar_provisoes_pendentes(cliente_ativo_id)
    df_info_cli = carregar_dados_cliente_ativo(cliente_ativo_id)
           
    if not df_info_cli.empty:
        nome_empresa = df_info_cli.iloc[0]["nome"]
        regime_empresa = df_info_cli.iloc[0]["regime"]
        

        plano_cli = str(df_info_cli.iloc[0]["plano"]).lower()
        st.session_state["plano_ativo"] = plano_cli
        nome_plano_exibicao = REGRAS_PLANOS.get(plano_cli, {}).get("nome", "Plano MEI Gratuito")
        

        #st.info(f"{ICONES['cliente']} **Cliente Ativo em Atendimento:** {nome_empresa} | Regime: **{regime_empresa}** | {ICONES['cartao']} **{nome_plano_exibicao}**")


        filtro_caixa_fisico = "1.1.1.01|caixa geral|caixa físico|dinheiro"
        filtro_bancos = "1.1.1.02|1.1.1.03|banco|itau|bradesco|inter|nubank|cef|bb"

        # Receitas
        df_rec_g = df_lanc_global[df_lanc_global["conta_credito"].str.contains("3\.|Receita", case=False, na=False)]
        rec_g = df_rec_g["valor"].sum() if not df_rec_g.empty else 0.0
        rec_caixa_g = df_rec_g[df_rec_g["conta_debito"].str.contains(filtro_caixa_fisico, case=False, na=False)]["valor"].sum() if not df_rec_g.empty else 0.0
        rec_bancos_g = df_rec_g[df_rec_g["conta_debito"].str.contains(filtro_bancos, case=False, na=False)]["valor"].sum() if not df_rec_g.empty else 0.0

        # Despesas
        desp_g = df_lanc_global[df_lanc_global["conta_debito"].str.contains("4\.|Despesa|Estoque", case=False, na=False)]["valor"].sum() if not df_lanc_global.empty else 0.0
        
        # Saldo Caixa e Bancos
        ent_cx_g = df_lanc_global[df_lanc_global["conta_debito"].str.contains(filtro_caixa_fisico, case=False, na=False)]["valor"].sum() if not df_lanc_global.empty else 0.0
        sai_cx_g = df_lanc_global[df_lanc_global["conta_credito"].str.contains(filtro_caixa_fisico, case=False, na=False)]["valor"].sum() if not df_lanc_global.empty else 0.0
        saldo_disp_caixa_g = ent_cx_g - sai_cx_g
        
        ent_bc_g = df_lanc_global[df_lanc_global["conta_debito"].str.contains(filtro_bancos, case=False, na=False)]["valor"].sum() if not df_lanc_global.empty else 0.0
        sai_bc_g = df_lanc_global[df_lanc_global["conta_credito"].str.contains(filtro_bancos, case=False, na=False)]["valor"].sum() if not df_lanc_global.empty else 0.0
        saldo_disp_bancos_g = ent_bc_g - sai_bc_g
        
        saldo_g = saldo_disp_caixa_g + saldo_disp_bancos_g

        # Provisões (A Pagar) - Lendo diretamente dos agendamentos pendentes
        a_pagar_g = df_prov_global["valor"].sum() if not df_prov_global.empty else 0.0

        cor_saldo = "#00875a" if saldo_g >= 0 else "#de350b"
        col_m1, col_m2, col_m3, col_m4 = st.columns(4, gap="small")

        with col_m1:
            st.markdown(
                f"""<div style="border: 1px solid #0176a1; border-radius: 6px; padding: 8px; text-align: center; background-color: rgba(128, 128, 128, 0.05);">
<div style="font-size: 15px; color: #0176a1;"> Receita Realizada</div>
<div style="font-size: 20px; font-weight: bold; color: #00875a; margin: 2px 0;">{formatar_brl(rec_g)}</div>
<div style="font-size: 10px; color: #000000; line-height: 1.3;">Bancos: {formatar_brl(rec_bancos_g)}<br>Caixa: {formatar_brl(rec_caixa_g)}</div>
</div>""",
                unsafe_allow_html=True
            )

        with col_m2:
            st.markdown(
                f"""<div style="border: 1px solid #0176a1; border-radius: 6px; padding: 8px; text-align: center; background-color: rgba(128, 128, 128, 0.05);">
<div style="font-size: 15px; color: #0176a1;"> Despesas Pagas</div>
<div style="font-size: 20px; font-weight: bold; color: #de350b; margin: 2px 0;">{formatar_brl(desp_g)}</div>
<div style="font-size: 10px; color: transparent; line-height: 1.3;">&nbsp;<br>&nbsp;</div>
</div>""",
                unsafe_allow_html=True
            )

        with col_m3:
            st.markdown(
                f"""<div style="border: 1px solid #0176a1; border-radius: 6px; padding: 8px; text-align: center; background-color: rgba(128, 128, 128, 0.05);">
<div style="font-size: 15px; color: #0176a1;"> Saldo em Caixa/Banco</div>
<div style="font-size: 20px; font-weight: bold; color: {cor_saldo}; margin: 2px 0;">{formatar_brl(saldo_g)}</div>
<div style="font-size: 10px; color: #000000; line-height: 1.3;">Bancos: {formatar_brl(saldo_disp_bancos_g)}<br>Caixa: {formatar_brl(saldo_disp_caixa_g)}</div>
</div>""",
                unsafe_allow_html=True
            )

        with col_m4:
            st.markdown(
                f"""<div style="border: 1px solid #0176a1; border-radius: 6px; padding: 8px; text-align: center; background-color: rgba(128, 128, 128, 0.05);">
<div style="font-size: 15px; color: #0176a1;"> A Pagar (Guias/Parcelamento)</div>
<div style="font-size: 20px; font-weight: bold; color: #ff9900; margin: 2px 0;">{formatar_brl(a_pagar_g)}</div>
<div style="font-size: 10px; color: transparent; line-height: 1.3;">&nbsp;<br>&nbsp;</div>
</div>""",
                unsafe_allow_html=True
            )

else:
    st.warning(" Nenhum cliente selecionado. Escolha um cliente ativo na barra lateral para prosseguir.")

st.markdown("---")

if "Dashboard" in opcao or opcao == "Cadasrar Clientes":
    st.subheader("Gestão do Cliente - CADASTRO")

    user_id_atual = st.session_state.user.id
    cliente_ativo_id = st.session_state.get("cliente_id_ativo")


    qtd_clientes = len(clientes_cadastrados)


    if qtd_clientes < 1:
        st.info(f"{ICONES['bem_vindo']} Bem-vindo, Administrador! Cadastre a primeira empresa para ativar o sistema.")
        with st.form("form_cliente_inicial"):
            col_cli1, col_cli2, col_cli3 = st.columns(3)
            with col_cli1:
                nome = st.text_input("Razão Social / Nome")
                cnpj_cpf = st.text_input("CNPJ")
                cpf = st.text_input("CPF Titular")
            with col_cli2:
                regime = st.selectbox("Regime Contábil", ["MEI (Microempreendedor Individual)", "Simples Nacional"])
                limite_fat = st.selectbox("Limite Faturamento Anual", [81000.00, 251600.00], format_func=lambda x: f"R$ {x:,.2f} (MEI Geral)" if x == 81000 else f"R$ {x:,.2f} (MEI Caminhoneiro)")
                cap_social = st.number_input("Capital Social (R$)", value=1000.00, step=100.0)
            with col_cli3:
                dt_abertura = st.date_input("Data de Abertura", value=datetime.today().date(), format="DD/MM/YYYY")
                telefone = st.text_input("Telefone de Contato", placeholder="(00) 00000-0000")
                cnae = st.text_input("Código de Atividade (CNAE)")


            st.markdown("---")
            st.markdown("**Logotipo da Empresa (Aparecerá nos Contratos e Relatórios):**")
            arquivo_upd_logo = st.file_uploader(
                "Selecione o arquivo da sua marca", 
                type=["png", "jpg", "jpeg"], 
                key="upd_logo",
                help="Envie um arquivo PNG ou JPG de até 2MB. Recomenda-se imagem com fundo transparente."
            )


            if arquivo_upd_logo:
                st.image(arquivo_upd_logo, width=140, caption="Prévia do arquivo selecionado")
            btn_atualizar = st.form_submit_button(f"{ICONES['salvar']} Salvar Alterações do Cliente", use_container_width=True)

            if btn_atualizar:
                logo_b64 = processar_logo_empresa(arquivo_upd_logo)
                conn_up = get_connection()
                cursor_up = conn_up.cursor()

                try:
                    if logo_b64:
                        cursor_up.execute(
                            """
                            UPDATE clientes 
                            SET nome = %s, cnpj_cpf = %s, cpf = %s, regime = %s, 
                                capital_social = %s, data_abertura = %s, limite_faturamento = %s, 
                                telefone = %s, cnae_atividade = %s, logo_base64 = %s 
                            WHERE id = %s
                            """,
                            (e_nome, e_cnpj, e_cpf, e_regime, e_cap_social, e_dt_abertura.strftime("%Y-%m-%d"), e_limite, e_tel, e_cnae, logo_b64, id_cli_editar)
                        )
                    else:
                        cursor_up.execute(
                            """
                            UPDATE clientes 
                            SET nome = %s, cnpj_cpf = %s, cpf = %s, regime = %s, 
                            capital_social = %s, data_abertura = %s, limite_faturamento = %s, 
                            telefone = %s, cnae_atividade = %s 
                            WHERE id = %s
                            """,
                            (e_nome, e_cnpj, e_cpf, e_regime, e_cap_social, e_dt_abertura.strftime("%Y-%m-%d"), e_limite, e_tel, e_cnae, id_cli_editar)
                        )
                    conn_up.commit()
                                        

                    st.session_state["msg_sucesso"] = "Logotipo e dados atualizados com sucesso!"
                    st.rerun()
                except Exception as err_up:
                    conn_up.rollback()
                    st.error(f"Erro ao salvar no banco: {err_up}")
                finally:
                    conn_up.close()      
            st.caption(f"{ICONES['dicas']} **Dica:** Prefira imagens em formato **PNG com fundo transparente** e tamanho de até **2 MB** para melhor enquadramento nos contratos e relatórios.")
            
            salvar = st.form_submit_button(f"{ICONES['salvar']} Cadastrar Primeira Empresa", use_container_width=True)

        
        if salvar:
            if nome and cnpj_cpf:
                # [NOVO]: Recupera o UUID do usuário logado na sessão
                user_id_logado = st.session_state.get("user_id") or getattr(st.session_state.get("user"), "id", None)
                
                logo_proc = processar_logo_empresa(arquivo_logo)
                conn = get_connection()
                cursor = conn.cursor()
                try:
                    cursor.execute(
                        """
                        INSERT INTO clientes (nome, cnpj_cpf, cpf, regime, capital_social, data_abertura, limite_faturamento, telefone, cnae, user_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (nome, cnpj_cpf, cpf, regime, cap_social, dt_abertura.strftime("%Y-%m-%d"), limite_fat, telefone, cnae, str(user_id_logado))
                    )
                    conn.commit()
                    limpar_cache()
                    st.success(f"Empresa '{nome}' cadastrada com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao cadastrar: {e}")
                finally:
                    conn.close()
            else:
                st.warning("Preencha a Razão Social e o CNPJ.")

    
    else:
        if not cliente_ativo_id:
            st.warning("Selecione um cliente ativo na barra lateral para visualizar o Dashboard.")
        else:
            conn = get_connection()
            
    
            try:
                df_clientes_cad = pd.read_sql_query(
                    """
                    SELECT 
                        id, 
                        nome as "Razão Social", 
                        cnpj_cpf as "CNPJ", 
                        COALESCE(cpf, '-') as "CPF Titular",
                        regime as "Regime Contábil",
                        COALESCE(capital_social, 0.00) as "Capital Social",
                        data_abertura as "Data Abertura",
                        COALESCE(limite_faturamento, 81000.00) as "Limite Faturamento (R$)",
                        COALESCE(telefone, '-') as "Telefone",
                        COALESCE(cnae_atividade, '-') as "CNAE / Atividade",
                        logo_base64
                    FROM clientes 
                    WHERE id = %s
                    """,
                    conn,
                    params=(cliente_ativo_id,),
                )
            except Exception as err_sql:
    
                conn.rollback()
                st.error(f"Aviso de leitura cadastral: {err_sql}")
                df_clientes_cad = pd.read_sql_query(
                    """
                    SELECT 
                        id, 
                        nome as "Razão Social", 
                        cnpj_cpf as "CNPJ", 
                        '-' as "CPF Titular",
                        regime as "Regime Contábil",
                        0.00 as "Capital Social",
                        NULL as "Data Abertura",
                        81000.00 as "Limite Faturamento (R$)",
                        '-' as "Telefone",
                        '-' as "CNAE / Atividade"
                    FROM clientes 
                    WHERE id = %s
                    """,
                    conn,
                    params=(cliente_ativo_id,),
                )

    
            conn.close()
    
            df_lancamentos = carregar_lancamentos(cliente_ativo_id)
            df_provisoes = carregar_provisoes_pendentes(cliente_ativo_id)
            a_pagar_tot = df_provisoes["valor"].sum() if not df_provisoes.empty else 0.0


    
            if not df_clientes_cad.empty:
                row_cli = df_clientes_cad.iloc[0]
                
                dt_abertura_str = row_cli['Data Abertura'].strftime('%d/%m/%Y') if pd.notna(row_cli['Data Abertura']) else '-'
                cap_social_val = float(row_cli['Capital Social']) if row_cli['Capital Social'] else 0.0
                limite_val = float(row_cli['Limite Faturamento (R$)']) if row_cli['Limite Faturamento (R$)'] else 81000.0

                with st.container(border=True):
                    st.caption("Ficha Cadastral do Cliente Ativo (Dados CCMEI)")
                    col_logo, col_c1, col_c2, col_c3 = st.columns([1, 2, 2, 2])
                    
                    with col_logo:
                        if pd.notna(row_cli.get('logo_base64')) and row_cli.get('logo_base64'):
                            st.image(row_cli['logo_base64'], use_container_width=True)
                        else:
                            st.info("Sem Logo")
                    
                    with col_c1:
                        st.write(f"**Empresa:** {row_cli['Razão Social']}")
                        st.write(f"**CNPJ:** {row_cli['CNPJ']}")
                        st.write(f"**CPF Titular:** {row_cli['CPF Titular']}")
                    with col_c2:
                        st.write(f"**Regime:** {row_cli['Regime Contábil']}")
                        st.write(f"**Capital Social:** {formatar_brl(cap_social_val)}")
                        st.write(f"**Data de Abertura:** {dt_abertura_str}")
                    with col_c3:
                        st.write(f"**Telefone:** {row_cli['Telefone']}")
                        st.write(f"**CNAE:** {row_cli['CNAE / Atividade']}")
                        st.write(f"**Teto MEI:** {formatar_brl(limite_val)}")

            st.divider()

    
            st.markdown("##### Painel de Controle Financeiro (MEI)")

    
            rec_tot = df_lancamentos[
                df_lancamentos["conta_credito"].str.contains("3\.|Receita", case=False, na=False)
            ]["valor"].sum() if not df_lancamentos.empty else 0.0

    
            desp_tot = df_lancamentos[
                df_lancamentos["conta_debito"].str.contains("4\.|Despesa|Estoque", case=False, na=False)
            ]["valor"].sum() if not df_lancamentos.empty else 0.0

    
            filtro_caixa = "1.1.1|Caixa|Banco"
            ent_caixa = df_lancamentos[
                df_lancamentos["conta_debito"].str.contains(filtro_caixa, case=False, na=False)
            ]["valor"].sum() if not df_lancamentos.empty else 0.0

            sai_caixa = df_lancamentos[
                df_lancamentos["conta_credito"].str.contains(filtro_caixa, case=False, na=False)
            ]["valor"].sum() if not df_lancamentos.empty else 0.0

            saldo_caixa = ent_caixa - sai_caixa
    
            filtro_caixa_fisico = "1.1.1.01|caixa geral|caixa físico|dinheiro"
            filtro_bancos = "1.1.1.02|1.1.1.03|banco|itau|bradesco|inter|nubank|cef|bb"

            df_rec = df_lancamentos[df_lancamentos["conta_credito"].str.contains("3\.|Receita", case=False, na=False)]
            rec_caixa = df_rec[df_rec["conta_debito"].str.contains(filtro_caixa_fisico, case=False, na=False)]["valor"].sum() if not df_rec.empty else 0.0
            rec_bancos = df_rec[df_rec["conta_debito"].str.contains(filtro_bancos, case=False, na=False)]["valor"].sum() if not df_rec.empty else 0.0

            ent_cx = df_lancamentos[df_lancamentos["conta_debito"].str.contains(filtro_caixa_fisico, case=False, na=False)]["valor"].sum() if not df_lancamentos.empty else 0.0
            sai_cx = df_lancamentos[df_lancamentos["conta_credito"].str.contains(filtro_caixa_fisico, case=False, na=False)]["valor"].sum() if not df_lancamentos.empty else 0.0
            saldo_disp_caixa = ent_cx - sai_cx

            ent_bc = df_lancamentos[df_lancamentos["conta_debito"].str.contains(filtro_bancos, case=False, na=False)]["valor"].sum() if not df_lancamentos.empty else 0.0
            sai_bc = df_lancamentos[df_lancamentos["conta_credito"].str.contains(filtro_bancos, case=False, na=False)]["valor"].sum() if not df_lancamentos.empty else 0.0
            saldo_disp_bancos = ent_bc - sai_bc
            
    
            percentual_real = (rec_tot / limite_val) * 100 if limite_val > 0 else 0.0
            st.markdown(f"##### Acompanhamento do Limite Anual MEI (Teto: {formatar_brl(limite_val)})")
            
            col_m1, col_m2 = st.columns([3, 1])
            with col_m1:
                st.progress(min(percentual_real / 100.0, 1.0))
                st.caption(f"Faturado: **{formatar_brl(rec_tot)}** de **{formatar_brl(limite_val)}** ({percentual_real:.1f}%)")
            with col_m2:
                if percentual_real <= 80:
                    st.success("🟢 Faturamento Regular")
                elif percentual_real <= 100:
                    st.warning(f"{ICONES['alerta']} Próximo ao Teto MEI")
                else:
                    st.error(f"{ICONES['erro_grave']} Teto MEI Excedido")

            st.divider()

    
            st.markdown("##### Despesas por Categoria")
            if not df_lancamentos.empty:
                df_despesas = df_lancamentos[df_lancamentos["conta_debito"].str.contains("4\.|Despesa|Estoque", case=False, na=False)].copy()
                if not df_despesas.empty:
                    df_cat = df_despesas.groupby("conta_debito")["valor"].sum().reset_index()
                    df_cat.columns = ["Categoria / Fornecedor", "Valor"]
                    df_cat = df_cat.sort_values(by="Valor", ascending=False)

                    try:
                        import plotly.express as px
                        fig = px.pie(
                            df_cat, 
                            names="Categoria / Fornecedor", 
                            values="Valor", 
                            hole=0.4, 
                            color_discrete_sequence=px.colors.qualitative.Set3
                        )
                        fig.update_traces(textposition='inside', textinfo='percent')
                        fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=300)
                        st.plotly_chart(fig, use_container_width=True)
                    except Exception:
                        st.bar_chart(df_cat.set_index("Categoria / Fornecedor"))
                else:
                    st.info(" Nenhuma despesa registrada para exibir no gráfico.")
            else:
                st.info(" Nenhum lançamento registrado.")

    
        EMAILS_ADMIN = [
            "luizcasemiro@kazimm.com.br",
            "luizti.kazimm@gmail.com"
        ]

        if st.session_state.user.email in EMAILS_ADMIN:
            st.divider()
            with st.expander(
                f"{ICONES.get('configuracoes', ':material/settings:')} Painel de Administração de Clientes (Exclusivo Contador)", 
                expanded=False
            ):
            
                tab_edit, tab_novo, tab_usuario, tab_lista = st.tabs([
                    " Editar Cliente", 
                    " Cadastrar Novo Cliente", 
                    " Criar Acesso (Login)", 
                    " Carteira de Clientes"
                ])

    
                with tab_edit:
    
                        df_todos_cli = carregar_todos_clientes_completos()
    

                        if df_todos_cli.empty:
                            st.info(f"{ICONES['atencao']} Nenhum cliente cadastrado para edição.")
                        else:
                            dict_cli_edit = {f"ID #{row['id']} - {row['nome']} ({row['cnpj_cpf']})": row['id'] for _, row in df_todos_cli.iterrows()}
                            cli_sel_rotulo = st.selectbox("🔍 Selecione o cliente para alterar dados:", options=list(dict_cli_edit.keys()))
                            id_cli_editar = dict_cli_edit[cli_sel_rotulo]
                            row_edit = df_todos_cli[df_todos_cli["id"] == id_cli_editar].iloc[0]

                            with st.form("form_editar_cliente_admin"):
                                st.markdown(f"##### Alterando dados do Cliente **ID #{id_cli_editar}**")
                                col_e1, col_e2, col_e3 = st.columns(3)
                                with col_e1:
                                    e_nome = st.text_input("Razão Social / Nome", value=str(row_edit['nome']))
                                    e_cnpj = st.text_input("CNPJ", value=str(row_edit['cnpj_cpf']))
                                    e_cpf = st.text_input("CPF Titular", value=str(row_edit['cpf']))
                                with col_e2:
                                    reg_index = 0 if "MEI" in str(row_edit['regime']) else 1
                                    e_regime = st.selectbox("Regime Contábil", ["MEI (Microempreendedor Individual)", "Simples Nacional"], index=reg_index)
                                    lim_val = float(row_edit['limite'])
                                    lim_index = 0 if lim_val == 81000.0 else 1
                                    e_limite = st.selectbox("Limite Faturamento", [81000.00, 251600.00], index=lim_index, format_func=lambda x: f"R$ {x:,.2f} (MEI Geral)" if x == 81000 else f"R$ {x:,.2f} (MEI Caminhoneiro)")
                                    e_cap_social = st.number_input("Capital Social (R$)", value=float(row_edit['capital_social']), step=100.0)
                                with col_e3:
                                    dt_abert_val = pd.to_datetime(row_edit['data_abertura']).date() if pd.notna(row_edit['data_abertura']) else datetime.today().date()
                                    e_dt_abertura = st.date_input("Data de Abertura", value=dt_abert_val, format="DD/MM/YYYY")
                                    e_tel = st.text_input("Telefone", value=str(row_edit['telefone']))
                                    e_cnae = st.text_input("CNAE / Atividade", value=str(row_edit['cnae']))

    
                                st.markdown("---")
                                arquivo_upd_logo = st.file_uploader("Atualizar Logotipo (Opcional)", type=["png", "jpg", "jpeg"], key="upd_logo")

                                if arquivo_upd_logo is not None:
    
                                    if arquivo_upd_logo.size > 2 * 1024 * 1024:
                                        st.error(f"{ICONES['alerta']} O arquivo selecionado excede o limite de 2 MB. Reduza a imagem e tente novamente.")
                                    else:
    
                                        logo_b64 = processar_logo_empresa(arquivo_upd_logo)
                                
                                btn_atualizar = st.form_submit_button(f"{ICONES['salvar']} Salvar Alterações do Cliente")

                                if btn_atualizar:
                                    logo_b64 = processar_logo_empresa(arquivo_upd_logo)
                                    conn_up = get_connection()
                                    cursor_up = conn_up.cursor()
                                    
                                    if logo_b64:
    
                                        cursor_up.execute(
                                            "UPDATE clientes SET nome = %s, cnpj_cpf = %s, cpf = %s, regime = %s, capital_social = %s, data_abertura = %s, limite_faturamento = %s, telefone = %s, cnae_atividade = %s, logo_base64 = %s WHERE id = %s",
                                            (e_nome, e_cnpj, e_cpf, e_regime, e_cap_social, e_dt_abertura.strftime("%Y-%m-%d"), e_limite, e_tel, e_cnae, logo_b64, id_cli_editar)
                                        )
                                    else:
    
                                        cursor_up.execute(
                                            "UPDATE clientes SET nome = %s, cnpj_cpf = %s, cpf = %s, regime = %s, capital_social = %s, data_abertura = %s, limite_faturamento = %s, telefone = %s, cnae_atividade = %s WHERE id = %s",
                                            (e_nome, e_cnpj, e_cpf, e_regime, e_cap_social, e_dt_abertura.strftime("%Y-%m-%d"), e_limite, e_tel, e_cnae, id_cli_editar)
                                        )
                                        
                                    conn_up.commit()
                                    conn_up.close()
                                    st.success(f"Dados do cliente '{e_nome}' atualizados!")
                                    st.rerun()

    
                with tab_novo:
                        with st.form("form_adicionar_empresa", clear_on_submit=True):
                            st.markdown("##### Adicionar Novo MEI à sua Carteira")
                            col_n1, col_n2, col_n3 = st.columns(3)
                            with col_n1:
                                n_nome = st.text_input("Razão Social / Nome")
                                n_cnpj = st.text_input("CNPJ")
                                n_cpf = st.text_input("CPF Titular")
                            with col_n2:
                                n_regime = st.selectbox("Regime", ["MEI (Microempreendedor Individual)", "Simples Nacional"], key="n_reg")
                                n_limite = st.selectbox("Limite Faturamento", [81000.00, 251600.00], key="n_lim", format_func=lambda x: f"R$ {x:,.2f} (MEI Geral)" if x == 81000 else f"R$ {x:,.2f} (MEI Caminhoneiro)")
                                n_cap_social = st.number_input("Capital Social (R$)", value=1000.00, step=100.0)
                            with col_n3:
                                n_dt_abertura = st.date_input("Data de Abertura", value=datetime.today().date(), format="DD/MM/YYYY")
                                n_tel = st.text_input("Telefone")
                                n_cnae = st.text_input("CNAE / Atividade")

                            st.markdown("---")
                            arquivo_novo_logo = st.file_uploader("Enviar Logotipo (Opcional)", type=["png", "jpg", "jpeg"], key="upd_novo_logo")

                            btn_cad_novo = st.form_submit_button(" Adicionar Empresa")

                            if btn_cad_novo:
                                if n_nome and n_cnpj:
                                    # [NOVO]: Recupera o UUID do usuário logado na sessão
                                    user_id_logado = st.session_state.get("user_id") or getattr(st.session_state.get("user"), "id", None)
                                    
                                    logo_b64 = processar_logo_empresa(arquivo_novo_logo)
                                    conn_add = get_connection()
                                    cursor_add = conn_add.cursor()
                                    cursor_add.execute(
                                        """
                                        INSERT INTO clientes (nome, cnpj_cpf, cpf, regime, capital_social, data_abertura, limite_faturamento, telefone, cnae, user_id)
                                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                        """,
                                        (n_nome, n_cnpj, n_cpf, n_regime, n_cap_social, n_dt_abertura.strftime("%Y-%m-%d"), n_limite_fat, n_telefone, n_cnae, str(user_id_logado))
                                    )
                                    conn_add.commit()
                                    conn_add.close()
                                    limpar_cache()
                                    st.toast(f"Empresa '{n_nome}' adicionada com sucesso!", icon="✅")
                                    st.rerun()
                                else:
                                    st.warning("Preencha Razão Social e CNPJ.")

    
                with tab_usuario:
    
                    df_cli_vinc = df_todos_cli[['id', 'nome', 'cnpj_cpf']]
                    
                    if df_cli_vinc.empty:
                        st.info("Cadastre uma empresa na carteira antes de criar um login de acesso.")
                    else:
                        dict_cli_vinc = {
                            f"ID #{row['id']} - {row['nome']} ({row['cnpj_cpf']})": row['id'] 
                            for _, row in df_cli_vinc.iterrows()
                        }

                        with st.form("form_criar_acesso_login", clear_on_submit=True):
                            st.markdown("##### Criar Novo Login e Vincular à Empresa")
                            
                            cli_destino_rotulo = st.selectbox(
                                "Selecione a Empresa para liberar o acesso:", 
                                options=list(dict_cli_vinc.keys())
                            )
                            u_email = st.text_input("E-mail do Cliente / Usuário", placeholder="exemplo@gmail.com").strip().lower()
                            u_senha = st.text_input("Senha Provisória (mínimo 6 caracteres)", type="password")

                            btn_criar_user = st.form_submit_button(f"{ICONES['salvar']} Salvar e Liberar Acesso do Cliente")

                            if btn_criar_user:
                                if u_email and len(u_senha) >= 6:
                                    id_empresa_alvo = dict_cli_vinc[cli_destino_rotulo]
                                    user_id_criado = None

    
                                    try:
                                        res = supabase.auth.sign_up({"email": u_email, "password": u_senha})
                                        if res and res.user:
                                            user_id_criado = res.user.id
                                    except Exception:
                                        pass

    
                                    try:
                                        conn_up_user = get_connection()
                                        cursor_up_user = conn_up_user.cursor()

                                        if user_id_criado:
                                            cursor_up_user.execute(
                                                "UPDATE clientes SET user_id = %s WHERE id = %s",
                                                (user_id_criado, id_empresa_alvo)
                                            )
                                        else:
                                            cursor_up_user.execute(
                                                """
                                                UPDATE clientes 
                                                SET user_id = (SELECT id FROM auth.users WHERE LOWER(email) = LOWER(%s) LIMIT 1) 
                                                WHERE id = %s
                                                """,
                                                (u_email, id_empresa_alvo)
                                            )

                                        conn_up_user.commit()

    
                                        cursor_up_user.execute("SELECT user_id FROM clientes WHERE id = %s", (id_empresa_alvo,))
                                        checar_vincu = cursor_up_user.fetchone()
                                        conn_up_user.close()

                                        if checar_vincu and checar_vincu[0] is not None:
                                            limpar_cache()
                                            st.toast(f"Acesso liberado com sucesso para {u_email}!", icon="🔑")
                                            st.rerun()
    
                                        else:
                                            st.warning(f"O usuário **{u_email}** ainda não existe no Supabase Auth. Certifique-se de que o e-mail está correto.")

                                    except Exception as e:
                                        st.error(f"Erro ao vincular empresa ao usuário: {e}")
                                else:
                                    st.warning("Informe um e-mail válido e uma senha com pelo menos 6 caracteres.")

    
                with tab_lista:
                    st.markdown("##### Carteira de Clientes Cadastrados")
    

                    df_todos_clientes = df_todos_cli.rename(columns={
                        "nome": "Razão Social", "cnpj_cpf": "CNPJ", "cpf": "CPF Titular",
                        "regime": "Regime Contábil", "capital_social": "Capital Social",
                        "data_abertura": "Abertura", "limite": "Teto (R$)", "telefone": "Telefone", "cnae": "CNAE"
                    })

                    if df_todos_clientes.empty:
                        st.info("Nenhum cliente cadastrado até o momento.")
                    else:
                        st.dataframe(df_todos_clientes, use_container_width=True, hide_index=True)

elif opcao == "Cadastrar Contas":
    st.markdown(f"#### {ICONES.get('fornecedor', ':material/domain:')} Gestão de Contas e Fornecedores")

    cliente_ativo_id = st.session_state.get("cliente_id_ativo")

    if not cliente_ativo_id:
        st.warning("Nenhum cliente selecionado. Escolha um cliente ativo na barra lateral para prosseguir.")
    else:
        conn = get_connection()
        df_cliente = pd.read_sql_query(
            "SELECT id, nome, regime FROM clientes WHERE id = %s AND user_id = %s", 
            conn, 
            params=(cliente_ativo_id, st.session_state.user.id)
        )
        conn.close()

        if df_cliente.empty:
            st.error("Erro de segurança: Cliente não encontrado ou sem permissão.")
        else:
            nome_cliente = df_cliente.iloc[0]["nome"]
            regime_cliente = df_cliente.iloc[0]["regime"]

            # 1. Carregamento unificado do Plano de Contas para as abas operacionais
            conn = get_connection()
            df_plano = pd.read_sql_query(
                'SELECT id, codigo as "Código", descricao as "Nome da Conta", tipo as "Tipo" '
                'FROM plano_contas WHERE cliente_id IS NULL OR cliente_id = %s ORDER BY codigo ASC',
                conn,
                params=(cliente_ativo_id,)
            )
            conn.close()

            # 2. Painel rolável autônomo (Área reservada que não empurra o cabeçalho)
            with st.container(height=580, border=True):
                
                # 3. Abas de Funções conforme o padrão do manuscrito
                tab_cadastro, tab_edicao, tab_visualizacao = st.tabs([
                    f"{ICONES.get('adicionar', ':material/add_circle:')} Cadastrar Nova Conta",
                    f"{ICONES.get('editar', ':material/edit:')} Alterar ou Excluir",
                    f"{ICONES.get('plano_contas', ':material/account_tree:')} Plano de Contas Atual"
                ])

                # ------------------------------------------------------------------
                # ABA 1: CADASTRO DE CONTAS / FORNECEDORES
                # ------------------------------------------------------------------
                with tab_cadastro:
                    st.markdown("##### Novo Registro no Plano de Contas")
                    
                    with st.form("form_cadastrar_conta_nova", clear_on_submit=True):
                        col_c1, col_c2 = st.columns([1, 2])
                        with col_c1:
                            codigo = st.text_input("Código da Conta", placeholder="Ex: 4.1.1.08")
                            tipo_conta = st.selectbox(
                                "Grupo / Tipo",
                                ["Despesa", "Receita", "Ativo", "Passivo", "Patrimônio Líquido"],
                            )
                        with col_c2:
                            descricao = st.text_input("Nome da Conta / Fornecedor", placeholder="Ex: Posto Shell Ltda")
                        
                        salvar_conta = st.form_submit_button(
                            "Cadastrar Conta", 
                            type="primary", 
                            icon=ICONES.get("adicionar", ":material/add:")
                        )

                        if salvar_conta:
                            if codigo and descricao:
                                conn = get_connection()
                                cursor = conn.cursor()
                                try:
                                    cursor.execute(
                                        "INSERT INTO plano_contas (codigo, descricao, tipo, cliente_id) VALUES (%s, %s, %s, %s)",
                                        (codigo, descricao, tipo_conta, cliente_ativo_id),
                                    )
                                    conn.commit()
                                    st.success(f"Conta '{codigo} - {descricao}' inserida com sucesso!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Erro ao salvar no banco: {e}")
                                finally:
                                    conn.close()
                            else:
                                st.error("Preencha o Código e o Nome da Conta.")

                # ------------------------------------------------------------------
                # ABA 2: ALTERAÇÃO E EXCLUSÃO
                # ------------------------------------------------------------------
                with tab_edicao:
                    st.markdown("##### Gerenciamento de Registros Existentes")

                    if not df_plano.empty:
                        df_plano["label"] = (
                            df_plano["Código"] + " - " + df_plano["Nome da Conta"] + " (" + df_plano["Tipo"] + ")"
                        )
                        dict_contas = dict(zip(df_plano["label"], df_plano["id"]))

                        conta_sel_label = st.selectbox(
                            "Selecione para Modificar:", 
                            list(dict_contas.keys()), 
                            key="sb_modificar_conta_unica"
                        )
                        id_conta_sel = dict_contas[conta_sel_label]

                        # 1. Consulta incluindo cliente_id (exatamente 4 colunas para desempacotar)
                        conn = get_connection()
                        cursor = conn.cursor()
                        cursor.execute(
                            "SELECT codigo, descricao, tipo, cliente_id FROM plano_contas WHERE id = %s", 
                            (id_conta_sel,)
                        )
                        reg_conta = cursor.fetchone()
                        conn.close()

                        if reg_conta:
                            cod_atual, nome_atual, tipo_atual, dono_conta_id = reg_conta
                            eh_conta_padrao = (dono_conta_id is None)

                            if eh_conta_padrao:
                                st.info(f"{ICONES.get('fornecedor', ':material/domain:')} Esta é uma conta do **Plano Padrão do Sistema** (somente leitura para garantir a integridade contábil).")

                            # 2. Formulário dedicado apenas à Edição
                            with st.form("form_editar_conta_unica"):
                                col_e1, col_e2 = st.columns([1, 2])
                                with col_e1:
                                    novo_codigo = st.text_input("Código", value=cod_atual, disabled=eh_conta_padrao)
                                    tipos_possiveis = ["Despesa", "Receita", "Ativo", "Passivo", "Patrimônio Líquido"]
                                    idx_tipo = tipos_possiveis.index(tipo_atual) if tipo_atual in tipos_possiveis else 0
                                    novo_tipo = st.selectbox("Grupo / Tipo", tipos_possiveis, index=idx_tipo, disabled=eh_conta_padrao)
                                with col_e2:
                                    novo_nome = st.text_input("Nome / Fornecedor", value=nome_atual, disabled=eh_conta_padrao)

                                salvar_edicao = st.form_submit_button(
                                    "Salvar Alterações", 
                                    icon=ICONES.get("salvar", ":material/save:"),
                                    disabled=eh_conta_padrao
                                )

                                if salvar_edicao:
                                    if novo_codigo and novo_nome:
                                        conn = get_connection()
                                        cursor = conn.cursor()
                                        try:
                                            cursor.execute(
                                                "UPDATE plano_contas SET codigo = %s, descricao = %s, tipo = %s WHERE id = %s",
                                                (novo_codigo, novo_nome, novo_tipo, id_conta_sel),
                                            )
                                            conn.commit()
                                            st.success("Conta atualizada com sucesso!")
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Erro ao atualizar: {e}")
                                        finally:
                                            conn.close()
                                    else:
                                        st.error("Preencha todos os campos.")

                            # 3. Sanfona de Exclusão (FORA do st.form e liberada apenas para contas do cliente)
                            if not eh_conta_padrao:
                                with st.expander("Excluir esta Conta"):
                                    st.caption("Atenção: A exclusão removerá o registro do catálogo deste cliente.")
                                    if st.button(
                                        "Confirmar Exclusão", 
                                        key=f"del_c_m2_{id_conta_sel}", 
                                        type="primary", 
                                        icon=ICONES.get("excluir", ":material/delete:"),
                                        use_container_width=True
                                    ):
                                        conn = get_connection()
                                        cursor = conn.cursor()
                                        cursor.execute("DELETE FROM plano_contas WHERE id = %s", (id_conta_sel,))
                                        conn.commit()
                                        conn.close()
                                        st.success("Conta excluída com sucesso!")
                                        st.rerun()
                    else:
                        st.info("Nenhuma conta cadastrada para modificar.")

                # ------------------------------------------------------------------
                # ABA 3: VISUALIZAÇÃO DO PLANO DE CONTAS VIGENTE
                # ------------------------------------------------------------------
                with tab_visualizacao:
                    st.markdown("##### Estrutura Atualizada do Plano de Contas")
                    if not df_plano.empty:
                        df_exibicao_plano = df_plano.drop(columns=["id", "label"], errors="ignore")
                        st.dataframe(
                            df_exibicao_plano, 
                            use_container_width=True, 
                            height=460
                        )
                    else:
                        st.info("Nenhuma conta cadastrada no momento.")                

# ==============================================================================
# BLOCO PLANO DE CONTAS - ESTRUTURA SLIM EM ABAS
# ==============================================================================
elif opcao == "Plano de Contas":
    st.markdown(f"#### {ICONES.get('plano_contas', ':material/account_tree:')} Estrutura do Plano de Contas")

    cliente_ativo_id = st.session_state.get("cliente_id_ativo")

    if not cliente_ativo_id:
        st.warning(f"{ICONES.get('alerta', ':material/warning:')} Nenhum cliente selecionado. Escolha um cliente ativo na barra lateral para prosseguir.")
    else:
        conn = get_connection()
        try:
            # 1. Validação de segurança e permissão de acesso ao cliente
            df_cliente = pd.read_sql_query(
                "SELECT id, nome, regime FROM clientes WHERE id = %s AND user_id = %s", 
                conn, 
                params=(cliente_ativo_id, st.session_state.user.id)
            )

            if df_cliente.empty:
                st.error("Erro de segurança: Cliente não encontrado ou sem permissão de acesso.")
                df_plano = pd.DataFrame()
            else:
                # 2. Carregamento do plano de contas (padrão global + específicas do cliente)
                df_plano = pd.read_sql_query(
                    """
                    SELECT 
                        codigo as "Código", 
                        descricao as "Nome da Conta / Fornecedor", 
                        tipo as "Grupo / Tipo",
                        CASE 
                            WHEN cliente_id IS NULL THEN '🌐 Padrão do Sistema'
                            ELSE '🏢 Específica da Empresa'
                        END AS "Origem"
                    FROM plano_contas 
                    WHERE cliente_id IS NULL OR cliente_id = %s
                    ORDER BY codigo ASC
                    """,
                    conn,
                    params=(cliente_ativo_id,)
                )
        except Exception as e:
            st.error(f"Erro ao carregar o plano de contas: {e}")
            df_plano = pd.DataFrame()
        finally:
            conn.close()

        if not df_cliente.empty:
            if df_plano.empty:
                st.info("Nenhuma conta cadastrada no Plano de Contas.")
            else:
                # Contentor delimitado com altura fixa de 580px
                with st.container(height=580, border=True):
                    
                    # Barra superior: Busca rápida à esquerda e Download (.CSV) à direita
                    col_b1, col_b2 = st.columns([3, 1.2], vertical_alignment="bottom")
                    with col_b1:
                        busca = st.text_input(
                            "Buscar Conta ou Fornecedor:",
                            placeholder="Ex: Combustível, Ambev, 4.1.1 ou Caixa...",
                            key="txt_busca_plano_contas"
                        )
                    with col_b2:
                        csv_plano = df_plano.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig")
                        st.download_button(
                            label="Exportar (.CSV)",
                            data=csv_plano,
                            file_name="plano_de_contas_kazimm.csv",
                            mime="text/csv",
                            icon=ICONES.get("extrato", ":material/download:"),
                            use_container_width=True,
                            key="btn_download_plano_contas"
                        )

                    # Filtro dinâmico da tabela em memória
                    if busca:
                        df_plano = df_plano[
                            df_plano["Código"].str.contains(busca, case=False, na=False)
                            | df_plano["Nome da Conta / Fornecedor"].str.contains(busca, case=False, na=False)
                        ]

                    tab_geral, tab_receitas, tab_despesas, tab_financeiro = st.tabs([
                        f"{ICONES.get('dashboard', ':material/view_list:')} Visão Geral",
                        f"{ICONES.get('adicionar', ':material/trending_up:')} Receitas (Grupo 3)",
                        f"{ICONES.get('provisoes', ':material/trending_down:')} Despesas & Fornecedores (Grupo 4)",
                        f"{ICONES.get('conciliacao', ':material/account_balance:')} Caixas e Bancos (Grupo 1)"
                    ])

                    # ----------------------------------------------------------
                    # ABA 1: VISÃO GERAL COMPLETA
                    # ----------------------------------------------------------
                    with tab_geral:
                        st.caption(f"Total de contas listadas: **{len(df_plano)}**")
                        st.dataframe(
                            df_plano, 
                            use_container_width=True, 
                            hide_index=True, 
                            height=430
                        )

                    # ----------------------------------------------------------
                    # ABA 2: RECEITAS / FATURAMENTO (GRUPO 3)
                    # ----------------------------------------------------------
                    with tab_receitas:
                        df_rec = df_plano[df_plano["Grupo / Tipo"] == "Receita"]
                        st.caption(f"Contas de Receita identificadas: **{len(df_rec)}**")
                        st.dataframe(
                            df_rec, 
                            use_container_width=True, 
                            hide_index=True, 
                            height=430
                        )

                    # ----------------------------------------------------------
                    # ABA 3: DESPESAS, CUSTOS & FORNECEDORES (GRUPO 4 / PASSIVO)
                    # ----------------------------------------------------------
                    with tab_despesas:
                        df_desp = df_plano[df_plano["Grupo / Tipo"].isin(["Despesa", "Passivo"])]
                        st.caption(f"Contas de Despesas e Fornecedores: **{len(df_desp)}**")
                        st.dataframe(
                            df_desp, 
                            use_container_width=True, 
                            hide_index=True, 
                            height=430
                        )

                    # ----------------------------------------------------------
                    # ABA 4: CAIXAS E CONTAS BANCÁRIAS (GRUPO 1 / ATIVO)
                    # ----------------------------------------------------------
                    with tab_financeiro:
                        df_fin = df_plano[df_plano["Grupo / Tipo"] == "Ativo"]
                        st.caption(f"Contas Financeiras e Patrimoniais: **{len(df_fin)}**")
                        st.dataframe(
                            df_fin, 
                            use_container_width=True, 
                            hide_index=True, 
                            height=430
                        )

#BLOCO BOTÃO ÚNICO - LANÇAMENTOS

elif opcao == "Lançamentos":
    st.markdown(f"#### {ICONES.get('lancamentos', ':material/edit_note:')} Livro Caixa e Movimentações Contábeis")

    cliente_ativo_id = st.session_state.get("cliente_id_ativo")

    if not cliente_ativo_id:
        st.warning("Nenhum cliente selecionado. Escolha um cliente ativo na barra lateral para prosseguir.")
    else:
        # Área delimitada que mantém o cabeçalho fixo no topo da aplicação
        with st.container(height=580, border=True):
            
            tab_novo, tab_consulta = st.tabs([
                f"{ICONES.get('adicionar', ':material/add_circle:')} Novo Lançamento",
                f"{ICONES.get('lancamentos', ':material/search:')} Consulta e Histórico"
            ])
            
                
            # --------------------------------------------------------------
            # ABA 1: NOVO LANÇAMENTO
            # --------------------------------------------------------------
            with tab_novo:
                st.markdown("##### Inclusão de Entrada ou Saída")

                plano_atual = st.session_state.get("plano_ativo", "gratis")
                limite_mes = REGRAS_PLANOS.get(plano_atual, {}).get("limite_lancamentos_mes", 25)

                from datetime import datetime
                mes_atual_cod = datetime.now().strftime("%Y-%m")
                
                if not df_lanc_global.empty and "data" in df_lanc_global.columns:
                    total_mes = int(df_lanc_global[df_lanc_global["data"].astype(str).str.startswith(mes_atual_cod)].shape[0])
                else:
                    total_mes = 0

                if total_mes < limite_mes and plano_atual == "gratis":
                    st.info(f"{ICONES['plano_contas']} **Consumo do Plano Gratuito:** {total_mes} de {limite_mes} lançamentos utilizados neste mês.")

                if total_mes >= limite_mes:
                    st.error(f"{ICONES['alerta']} **Limite mensal atingido ({total_mes} de {limite_mes} lançamentos) para o período de {mes_atual_cod}.**")
                    exibir_bloqueio_upgrade("Lançamentos Ilimitados", plano_minimo="pro")
                    st.stop()

                regime_cliente = regime_empresa if 'regime_empresa' in locals() else "MEI (Microempreendedor Individual)"
                cliente_selecionado = nome_empresa if 'nome_empresa' in locals() else "Cliente"
                df_contas = carregar_plano_contas(cliente_ativo_id)

                # -------------------------------------------------------------------------
                # FILTRAGEM INTELIGENTE DO PLANO DE CONTAS (SEM ALTERAR O BANCO)
                # -------------------------------------------------------------------------
                # 1. Contas Financeiras: Apenas Caixas e Bancos do Grupo 1.1.1 (ignorando títulos pai)
                df_fin = df_contas[
                    df_contas["codigo"].str.startswith("1.1.1.") &
                    ~df_contas["codigo"].isin(["1.1.1", "1.1.1.02", "1.1.1.03"])
                ]
                if not df_fin.empty:
                    opcoes_financeiras = [f"{row['codigo']} - {row['descricao']}" for _, row in df_fin.iterrows()]
                else:
                    opcoes_financeiras = ["1.1.1.01 - Caixa Geral", "1.1.1.02.01 - Banco CORA"]

                # 2. Despesas: Apenas contas analíticas do Grupo 4 (com 4 ou 5 níveis, ex: 4.1.1.03.01)
                df_desp = df_contas[
                    df_contas["codigo"].str.startswith("4.1.1.") &
                    (df_contas["codigo"].str.count(r"\.") >= 3)
                ]
                if not df_desp.empty:
                    opcoes_fornecedores_despesa = [""] + [f"{row['codigo']} - {row['descricao']}" for _, row in df_desp.iterrows()]
                else:
                    opcoes_fornecedores_despesa = [""] + [f"{row['codigo']} - {row['descricao']}" for _, row in df_contas.iterrows()]

                # 3. Receitas: Apenas contas analíticas do Grupo 3 (ex: 3.1.1.01, 3.2.1.01)
                df_rec = df_contas[
                    df_contas["codigo"].str.startswith("3.") &
                    (df_contas["codigo"].str.count(r"\.") >= 2)
                ]
                if not df_rec.empty:
                    opcoes_rec = [""] + [f"{row['codigo']} - {row['descricao']}" for _, row in df_rec.iterrows()]
                else:
                    opcoes_rec = [""] + [f"{row['codigo']} - {row['descricao']}" for _, row in df_contas.iterrows()]

                # --------------------------------------------------------------
                # [ALTERAÇÃO 1]: CARREGAMENTO DINÂMICO VIA BANCO DE DADOS
                # --------------------------------------------------------------
                # Substitui a lista estática pela busca no Supabase através do database.py
                historicos_padrao = carregar_historicos_padrao(cliente_ativo_id)

                # --------------------------------------------------------------
                # [ALTERAÇÃO 2]: BOTÃO PARA CRIAR NOVO HISTÓRICO PADRÃO
                # Posicionado fora do formulário para evitar erros de form aninhado
                # --------------------------------------------------------------
                col_topo_info, col_topo_btn = st.columns([3, 1])
                with col_topo_btn:
                    if st.button("➕ Novo Histórico Padrão", use_container_width=True, key="btn_abrir_modal_hp"):
                        modal_novo_historico(cliente_ativo_id)
                        
                        if st.button("Salvar Histórico", type="primary", use_container_width=True, key="btn_salvar_nh"):
                            if nh_desc and nh_texto:
                                sucesso, msg = salvar_novo_historico_padrao(
                                    cliente_id=cliente_ativo_id,
                                    codigo=nh_cod or "GERAL",
                                    descricao=nh_desc,
                                    texto_padrao=nh_texto
                                )
                                if sucesso:
                                    st.success(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)
                            else:
                                st.warning("Preencha ao menos o Título e o Texto do histórico.")


                # Roteamento por Regime Tributário
                if "Lançamento Simples" in regime_cliente or "MEI" in str(regime_cliente):
                    tab_entrada, tab_saida = st.tabs([
                        "(+) ENTRADAS / RECEITAS", 
                        "(-) SAÍDAS / DESPESAS E ESTOQUE"
                    ])

                    with tab_entrada:
                        with st.form("form_entrada", clear_on_submit=True):
                            st.markdown(f"{ICONES['transmissao']} ####Registrar Entrada de Caixas / Receitas")
                            data = st.date_input("Data do Lançamento", format="DD/MM/YYYY", key="dt_ent")

                            c_doc1, c_doc2, c_doc3 = st.columns(3)
                            with c_doc1:
                                tipo_doc = st.selectbox(
                                    "Tipo de Documento",
                                    ["Cupom Fiscal (NFC-e)", "Nota Fiscal (NF-e)", "Recibo / Comprovante", "Extrato / PIX", "Sem Documento"],
                                    key="td_ent"
                                )
                            with c_doc2:
                                num_doc = st.text_input("Nº do Documento (Opcional)", placeholder="Ex: 1054", key="nd_ent")
                            with c_doc3:
                                nome_cliente_rec = st.text_input("Cliente / Pagador (Opcional)", placeholder="Ex: Cliente João Silva", key="em_ent")

                            col_s1, col_s2 = st.columns(2)
                            with col_s1:
                                conta_financeira = st.selectbox(
                                    "Conta de Destino (Onde o dinheiro entrou)",
                                    opcoes_financeiras,
                                    key="cf_ent"
                                )
                            with col_s2:
                                categoria = st.selectbox("Categoria da Receita", opcoes_rec, key="cat_ent")

                            valor = st.number_input("Valor da Receita (R$)", min_value=0.00, step=0.01, format="%.2f", key="val_ent")
                            hist_sel = st.selectbox("Histórico Padrão", historicos_padrao, key="hp_ent")
                            comp_hist = st.text_input("Complemento do Histórico", placeholder="Ex: Vendas do dia em cartão e dinheiro", key="ch_ent")

                            salvar_ent = st.form_submit_button("Registrar Entrada")

                            if salvar_ent:
                                if not conta_financeira:
                                    st.warning(f"{ICONES['alerta']} Selecione a **Conta de Destino** (onde o dinheiro entrou).")
                                elif not categoria:
                                    st.warning(f"{ICONES['alerta']} Selecione a **Categoria da Receita**.")
                                elif valor <= 0:
                                    st.warning(f"{ICONES['alerta']} O **Valor da Receita** deve ser maior que R$ 0,00.")
                                else:
                                    # Montagem flexível dos dados do documento
                                    info_doc = f"[{tipo_doc}" + (f" nº {num_doc.strip()}" if num_doc.strip() else "") + (f" - {nome_cliente_rec.strip()}" if nome_cliente_rec.strip() else "") + "]"
                                    
                                    # Montagem do histórico sem travar se o campo estiver vazio
                                    partes = [info_doc]
                                    if hist_sel and hist_sel != "Digitar Histórico do Zero":
                                        partes.append(hist_sel.strip())
                                    if comp_hist.strip():
                                        partes.append(comp_hist.strip())
                                    
                                    hist_final = " ".join(partes)

                                    conn = get_connection()
                                    cursor = conn.cursor()
                                    try:
                                        cursor.execute(
                                            """
                                            INSERT INTO lancamentos (cliente_id, data, conta_debito, conta_credito, valor, historico) 
                                            VALUES (%s, %s, %s, %s, %s, %s)
                                            """,
                                            (cliente_ativo_id, str(data), conta_financeira, categoria, float(valor), hist_final.strip())
                                        )
                                        conn.commit()
                                    finally:
                                        cursor.close()
                                        conn.close()

                                    limpar_cache()
                                    st.success(f"{ICONES['sucesso']} Entrada registrada com sucesso!")
                                    st.rerun()

                    with tab_saida:
                        with st.form("form_saida", clear_on_submit=True):
                            st.markdown("##### Registrar Pagamento de Despesa / Fornecedor")
                            data = st.date_input("Data do Lançamento", format="DD/MM/YYYY", key="dt_sai")

                            c_doc1, c_doc2 = st.columns(2)
                            with c_doc1:
                                tipo_doc = st.selectbox(
                                    "Tipo de Documento",
                                    ["Cupom Fiscal (NFC-e)", "Nota Fiscal (NF-e)", "Recibo / Comprovante", "Extrato / PIX", "Sem Documento"],
                                    key="td_sai"
                                )
                            with c_doc2:
                                num_doc = st.text_input("Nº do Documento (Opcional)", placeholder="Ex: 1054", key="nd_sai")

                            col_s1, col_s2 = st.columns(2)
                            with col_s1:
                                conta_financeira = st.selectbox(
                                    "Forma de Pagamento (De onde saiu o dinheiro)",
                                    opcoes_financeiras,
                                    key="cf_sai"
                                )
                            with col_s2:
                                categoria = st.selectbox(
                                    "Fornecedor / Conta de Despesa (Grupo 4)", 
                                    opcoes_fornecedores_despesa, 
                                    key="cat_sai"
                                )

                            valor = st.number_input("Valor da Despesa (R$)", min_value=0.00, step=0.01, format="%.2f", key="val_sai")
                            hist_sel = st.selectbox("Histórico Padrão", historicos_padrao, key="hp_sai")
                            comp_hist = st.text_input("Complemento do Histórico", placeholder="Ex: Aquisição de combustíveis e insumos", key="ch_sai")

                            salvar_sai = st.form_submit_button("Registrar Saída")

                            if salvar_sai:
                                if not conta_financeira:
                                    st.warning(f"{ICONES['alerta']} Selecione a **Forma de Pagamento** (de onde saiu o dinheiro).")
                                elif not categoria:
                                    st.warning(f"{ICONES['alerta']} Selecione o **Fornecedor / Conta de Despesa**.")
                                elif valor <= 0:
                                    st.warning(f"{ICONES['alerta']} O **Valor da Despesa** deve ser maior que R$ 0,00.")
                                elif hist_sel == "Digitar Histórico do Zero" and not comp_hist.strip():
                                    st.warning(f"{ICONES['alerta']} Você escolheu 'Digitar Histórico do Zero'. Por favor, escreva o **Complemento do Histórico**.")
                                else:
                                    info_doc = f"[{tipo_doc}" + (f" nº {num_doc.strip()}" if num_doc.strip() else "") + "]"
                                    hist_final = f"{info_doc} {comp_hist.strip()}" if hist_sel == "Digitar Histórico do Zero" else f"{info_doc} {hist_sel} {comp_hist.strip()}"

                                    conn = get_connection()
                                    cursor = conn.cursor()
                                    try:
                                        cursor.execute(
                                            """
                                            INSERT INTO lancamentos (cliente_id, data, conta_debito, conta_credito, valor, historico) 
                                            VALUES (%s, %s, %s, %s, %s, %s)
                                            """,
                                            (cliente_ativo_id, str(data), categoria, conta_financeira, float(valor), hist_final.strip())
                                        )
                                        conn.commit()
                                    finally:
                                        cursor.close()
                                        conn.close()

                                    limpar_cache()
                                    st.success(f"{ICONES['sucesso']} Saída registrada com sucesso!")
                                    st.rerun()

                else:
                    with st.form("form_partida_dupla", clear_on_submit=True):
                        st.markdown("##### Preenchimento por Partida Dupla")
                        data = st.date_input("Data do Lançamento", format="DD/MM/YYYY")

                        col1, col2 = st.columns(2)
                        with col1:
                            conta_debito = st.selectbox("Conta Débito", [""] + [f"{r['codigo']} - {r['descricao']}" for _, r in df_contas.iterrows()])
                        with col2:
                            conta_credito = st.selectbox("Conta Crédito", [""] + [f"{r['codigo']} - {r['descricao']}" for _, r in df_contas.iterrows()])

                        valor = st.number_input("Valor (R$)", min_value=0.00, step=0.01, format="%.2f")
                        hist_sel = st.selectbox("Histórico Padrão", historicos_padrao)
                        comp_hist = st.text_input("Complemento do Histórico")

                        salvar_pd = st.form_submit_button("Registrar Lançamento")

                        if salvar_pd:
                            if not conta_debito:
                                st.warning(f"{ICONES['alerta']} Selecione a **Conta Débito**.")
                            elif not conta_credito:
                                st.warning(f"{ICONES['alerta']} Selecione a **Conta Crédito**.")
                            elif valor <= 0:
                                st.warning(f"{ICONES['alerta']} O **Valor** do lançamento deve ser maior que R$ 0,00.")
                            elif hist_sel == "Digitar Histórico do Zero" and not comp_hist.strip():
                                st.warning(f"{ICONES['alerta']} Você escolheu 'Digitar Histórico do Zero'. Por favor, preencha o **Complemento do Histórico**.")
                            else:
                                hist_final = comp_hist if hist_sel == "Digitar Histórico do Zero" else f"{hist_sel} {comp_hist}"
                                conn = get_connection()
                                cursor = conn.cursor()
                                cursor.execute(
                                    "INSERT INTO lancamentos (cliente_id, data, conta_debito, conta_credito, valor, historico) VALUES (%s, %s, %s, %s, %s, %s)",
                                    (cliente_ativo_id, str(data), conta_debito, conta_credito, valor, hist_final.strip())
                                )
                                conn.commit()
                                conn.close()
                                limpar_cache()
                                st.success(f"{ICONES['sucesso']} Lançamento em Partida Dupla registrado!")
                                st.rerun()

            # --------------------------------------------------------------
            # ABA 2: CONSULTA / HISTÓRICO (Livro Caixa e Manutenção)
            # --------------------------------------------------------------
            with tab_consulta:
                st.markdown("##### Histórico de Movimentações Registradas")

                # Carregamento dos lançamentos e dados cadastrais do cliente ativo
                df_clientes_cad = df_info_cli if 'df_info_cli' in locals() else pd.DataFrame()
                df_lancamentos = carregar_lancamentos(cliente_ativo_id)

                if not df_clientes_cad.empty:
                    row_cli = df_clientes_cad.iloc[0]
                    with st.container(border=True):
                        st.caption("Ficha Cadastral do Cliente Ativo")
                        col_c1, col_c2, col_c3 = st.columns([2, 1.5, 1.5])
                        with col_c1:
                            st.write(f"**Empresa:** {row_cli.get('Razão Social', '-')}")
                            st.write(f"**CNPJ/CPF:** {row_cli.get('CNPJ/CPF', '-')}")
                        with col_c2:
                            st.write(f"**Regime:** {row_cli.get('Regime Contábil', '-')}")
                            st.write(f"**Telefone:** {row_cli.get('Telefone', '-')}")
                        with col_c3:
                            st.write(f"**CNAE:** {row_cli.get('CNAE / Atividade', '-')}")
                            limite_val = float(row_cli['Limite Faturamento (R$)']) if row_cli.get('Limite Faturamento (R$)') else 81000.0
                            st.write(f"**Teto MEI:** {formatar_brl(limite_val)}")

                st.divider()

                if df_lancamentos.empty:
                    st.info("Nenhum lançamento encontrado para este cliente.")
                else:
                    df_lancamentos["data_dt"] = pd.to_datetime(df_lancamentos["data"], errors="coerce").dt.date
                    df_lancamentos = df_lancamentos.dropna(subset=["data_dt"])

                    with st.expander("Filtros de Busca e Auditoria", expanded=True):
                        col_f1, col_f2, col_f3 = st.columns(3)

                        min_data = df_lancamentos["data_dt"].min()
                        max_data = df_lancamentos["data_dt"].max()

                        with col_f1:
                            datas_sel = st.date_input(
                                "Período",
                                value=(min_data, max_data),
                                format="DD/MM/YYYY",
                                key="dt_filtro_consulta"
                            )
                            if isinstance(datas_sel, (tuple, list)) and len(datas_sel) == 2:
                                data_inicio, data_fim = datas_sel
                            else:
                                data_inicio, data_fim = min_data, max_data

                        with col_f2:
                            tipo_sel = st.selectbox(
                                "Tipo de Operação",
                                ["Todos", "🟢 Receitas (Entradas)", "🔴 Despesas (Saídas)"],
                                key="sb_tipo_operacao_filtro"
                            )

                        contas_unicas = sorted(list(
                            set(df_lancamentos["conta_debito"].dropna().unique()).union(
                            set(df_lancamentos["conta_credito"].dropna().unique()))
                        ))
                        
                        with col_f3:
                            conta_sel = st.selectbox(
                                "Conta / Categoria",
                                ["Todas"] + contas_unicas,
                                key="sb_conta_filtro"
                            )

                    # Aplicação dos Filtros Selecionados
                    df_filtrado = df_lancamentos.copy()

                    df_filtrado = df_filtrado[
                        (df_filtrado["data_dt"] >= data_inicio) & 
                        (df_filtrado["data_dt"] <= data_fim)
                    ]

                    if tipo_sel == "🟢 Receitas (Entradas)":
                        df_filtrado = df_filtrado[
                            df_filtrado["conta_credito"].str.contains("3\.|Receita", case=False, na=False)
                        ]
                    elif tipo_sel == "🔴 Despesas (Saídas)":
                        df_filtrado = df_filtrado[
                            df_filtrado["conta_debito"].str.contains("4\.|Despesa|Estoque", case=False, na=False)
                        ]

                    if conta_sel != "Todas":
                        df_filtrado = df_filtrado[
                            (df_filtrado["conta_debito"] == conta_sel) | 
                            (df_filtrado["conta_credito"] == conta_sel)
                        ]

                    # Indicadores do Período Filtrado
                    total_registros = len(df_filtrado)
                    soma_valor = df_filtrado["valor"].sum() if not df_filtrado.empty else 0.0

                    col_r1, col_r2 = st.columns([2, 1])
                    with col_r1:
                        st.caption(f"Exibindo **{total_registros}** lançamento(s) encontrado(s)")
                    with col_r2:
                        st.markdown(f"**Total do Período Filtrado:** `{formatar_brl(soma_valor)}`")

                    # Grid de Dados do Histórico
                    df_exibir = df_filtrado.copy()
                    df_exibir["Data"] = df_exibir["data_dt"].apply(lambda x: x.strftime("%d/%m/%Y") if pd.notna(x) else "")
                    df_exibir["Valor"] = df_exibir["valor"].apply(formatar_brl)

                    cols_exibicao = ["id", "Data", "conta_debito", "conta_credito", "Valor", "historico"]
                    
                    st.dataframe(
                        df_exibir[cols_exibicao].rename(columns={
                            "id": "ID",
                            "conta_debito": "Conta Débito",
                            "conta_credito": "Conta Crédito",
                            "historico": "Histórico / Documento"
                        }),
                        use_container_width=True,
                        hide_index=True,
                        height=280
                    )

                    st.divider()

                    # Sanfona de Manutenção (Alteração / Exclusão)
                    with st.expander(
                        f"{ICONES.get('ferramentas', ':material/build:')} Central de Manutenção (Alterar / Excluir Lançamento)", 
                        expanded=False
                    ):
                        if df_filtrado.empty:
                            st.info("Nenhum lançamento disponível para alteração/exclusão com os filtros atuais.")
                        else:
                            dict_lancamentos = {}
                            for _, r in df_filtrado.iterrows():
                                dt_fmt = r["data_dt"].strftime("%d/%m/%Y") if pd.notna(r["data_dt"]) else ""
                                v_fmt = formatar_brl(r["valor"])
                                rotulo = f"ID #{r['id']} | {dt_fmt} | {v_fmt} | {str(r['historico'])[:40]}"
                                dict_lancamentos[rotulo] = r["id"]

                            item_selecionado_rotulo = st.selectbox(
                                "Selecione o lançamento que deseja Alterar ou Excluir:",
                                options=list(dict_lancamentos.keys()),
                                key="sb_sel_lanc_manutencao"
                            )

                            id_alvo = dict_lancamentos[item_selecionado_rotulo]
                            row_alvo = df_lancamentos[df_lancamentos["id"] == id_alvo].iloc[0]

                            tab_alt, tab_exc = st.tabs(["Alterar Lançamento", "Excluir Lançamento"])

                            # SUB-ABA: EDITAR LANÇAMENTO
                            with tab_alt:
                                df_plano = carregar_plano_contas(cliente_ativo_id)

                                if not df_plano.empty:
                                    lista_contas = (df_plano['codigo'].astype(str) + " - " + df_plano['descricao'].astype(str)).tolist()
                                else:
                                    lista_contas = []

                                c_deb_atual = str(row_alvo["conta_debito"])
                                c_cred_atual = str(row_alvo["conta_credito"])

                                if c_deb_atual and c_deb_atual not in lista_contas:
                                    lista_contas.append(c_deb_atual)
                                if c_cred_atual and c_cred_atual not in lista_contas:
                                    lista_contas.append(c_cred_atual)

                                lista_contas = sorted(list(set(lista_contas)))

                                idx_deb = lista_contas.index(c_deb_atual) if c_deb_atual in lista_contas else 0
                                idx_cred = lista_contas.index(c_cred_atual) if c_cred_atual in lista_contas else 0

                                with st.form(f"form_editar_lanc_{id_alvo}"):
                                    col_e1, col_e2 = st.columns(2)
                                    
                                    with col_e1:
                                        data_edit = st.date_input("Data do Lançamento", value=row_alvo["data_dt"], format="DD/MM/YYYY")
                                        c_deb_edit = st.selectbox("Conta Débito", options=lista_contas, index=idx_deb)
                                        val_edit = st.number_input("Valor (R$)", value=float(row_alvo["valor"]), step=0.01)
                                        
                                    with col_e2:
                                        c_cred_edit = st.selectbox("Conta Crédito", options=lista_contas, index=idx_cred)
                                        hist_edit = st.text_area("Histórico / Documento", value=str(row_alvo["historico"]))

                                    btn_salvar_edit = st.form_submit_button(
                                        "Salvar Alterações",
                                        icon=ICONES.get("salvar", ":material/save:")
                                    )

                                    if btn_salvar_edit:
                                        conn_act = get_connection()
                                        cursor_act = conn_act.cursor()
                                        cursor_act.execute(
                                            """
                                            UPDATE lancamentos 
                                            SET data = %s, conta_debito = %s, conta_credito = %s, valor = %s, historico = %s
                                            WHERE id = %s AND cliente_id = %s
                                            """,
                                            (data_edit.strftime("%Y-%m-%d"), c_deb_edit, c_cred_edit, val_edit, hist_edit, id_alvo, cliente_ativo_id)
                                        )
                                        conn_act.commit()
                                        conn_act.close()
                                        limpar_cache()
                                        st.success(f"Lançamento ID #{id_alvo} atualizado com sucesso!")
                                        st.rerun()

                            # SUB-ABA: EXCLUIR LANÇAMENTO
                            with tab_exc:
                                st.warning(f"{ICONES['alerta']} Tem certeza que deseja excluir o lançamento **ID #{id_alvo}**?")
                                st.write(f"**Data:** {row_alvo['data_dt'].strftime('%d/%m/%Y') if pd.notna(row_alvo['data_dt']) else ''} | **Valor:** {formatar_brl(row_alvo['valor'])}")
                                st.write(f"**Histórico:** {row_alvo['historico']}")

                                if st.button(
                                    f"{ICONES.get('excluir', ':material/delete:')} Confirmar Exclusão do Lançamento",
                                    key=f"btn_excluir_lanc_{id_alvo}",
                                    type="primary"
                                ):
                                    conn_del = get_connection()
                                    cur_del = conn_del.cursor()
                                    try:
                                        cur_del.execute(
                                            "DELETE FROM lancamentos WHERE id = %s AND cliente_id = %s",
                                            (id_alvo, cliente_ativo_id)
                                        )
                                        conn_del.commit()
                                    finally:
                                        cur_del.close()
                                        conn_del.close() 
                
# FINAL DO BLOCO
                        
# ==============================================================================
# BLOCO IMPORTAÇÃO - UNIFICADO E ALINHADO
# ==============================================================================
elif opcao == "Importação":
    st.markdown(f"{ICONES.get('importar', ':material/upload_file:')} Central de Importação de Movimentações")

    cliente_ativo_id = st.session_state.get("cliente_id_ativo")

    if not cliente_ativo_id:
        st.warning("Nenhum cliente selecionado. Escolha um cliente ativo na barra lateral para prosseguir.")
    else:
        # Contentor rolável com altura controlada
        with st.container(height=580, border=True):
            
            tab_planilhas, tab_extratos = st.tabs([
                f"{ICONES.get('importar', ':material/table_view:')} Carga em Lote (Excel / CSV / OFX)",
                f"{ICONES.get('extrato', ':material/receipt_long:')} Planilha do Cliente (Simples)"
            ])

            # --------------------------------------------------------------
            # ABA 1: IMPORTAÇÃO EM LOTE (Com Paywall para Plano Grátis)
            # --------------------------------------------------------------
            with tab_planilhas:
                st.markdown("##### Carga e Classificação em Lote")

                if not regras.get('importacao_lote', False):
                    st.info("ℹ️ Carregue centenas de lançamentos de uma só vez a partir de arquivos OFX ou de planilhas padronizadas.")
                    exibir_bloqueio_upgrade("Importação em Lote via Planilhas e OFX", plano_minimo="pro")
                else:
                    st.caption("Importe dezenas de transações de uma só vez a partir do extrato bancário (.OFX) ou de uma planilha (.xlsx / .csv).")

                    conn = get_connection()
                    try:
                        df_contas = pd.read_sql_query(
                            "SELECT codigo, descricao AS nome, tipo FROM plano_contas WHERE cliente_id = %s OR cliente_id IS NULL ORDER BY codigo ASC",
                            conn, params=(cliente_ativo_id,)
                        )
                    finally:
                        conn.close()

                    lista_todas_contas = [f"{r['codigo']} - {r['nome']}" for _, r in df_contas.iterrows()]
                    contas_bancos = [c for c in lista_todas_contas if c.startswith("1.1.1") or "Banco" in c or "Caixa" in c]
                    contas_receitas = [c for c in lista_todas_contas if c.startswith("3.") or "Receita" in c]
                    contas_despesas = [c for c in lista_todas_contas if c.startswith("4.") or "Despesa" in c or "Estoque" in c]

                    tipo_origem = st.radio(
                        "Selecione o formato do arquivo:",
                        ["Extrato Bancário (.OFX)", "Planilha Padrão (.xlsx / .csv)"],
                        horizontal=True,
                        key="radio_tipo_origem_lote"
                    )

                    st.markdown("---")
                    dados_processados = []

                    if tipo_origem == "Extrato Bancário (.OFX)":
                        col_b1, col_b2 = st.columns([1.5, 2])
                        with col_b1:
                            conta_destino_ofx = st.selectbox(
                                "Qual conta bancária representa este extrato?",
                                contas_bancos,
                                help="Ex: 1.1.1.02.01 - Banco CORA",
                                key="sb_conta_dest_ofx"
                            )
                        with col_b2:
                            arquivo_ofx = st.file_uploader(
                                "Selecione o arquivo .OFX baixado do banco", 
                                type=["ofx"],
                                key="upload_arquivo_ofx"
                            )

                        if arquivo_ofx:
                            try:
                                from ofxparse import OfxParser
                                import io

                                conteudo_bytes = io.BytesIO(arquivo_ofx.read())
                                ofx = OfxParser.parse(conteudo_bytes)

                                for transacao in ofx.account.statement.transactions:
                                    v = float(transacao.amount)
                                    dt = transacao.date.strftime('%Y-%m-%d')
                                    memo = str(transacao.memo).strip()
                                    tipo_mov = "Entrada" if v > 0 else "Saída"

                                    dados_processados.append({
                                        "Data": dt,
                                        "Tipo": tipo_mov,
                                        "Valor": abs(v),
                                        "Histórico / Descrição": memo,
                                        "Conta Contrapartida": "" 
                                    })

                                st.success(f"{ICONES['sucesso']} Extrato lido com sucesso: **{len(dados_processados)} transações** identificadas!")
                            except Exception as e:
                                st.error(f"Erro ao processar arquivo OFX: {e}")

                    else:
                        col_p1, col_p2 = st.columns([1.2, 2])
                        with col_p1:
                            st.write("**Planilha Modelo:**")
                            st.caption("Baixe o template padrão para preencher com seus dados:")
                            df_exemplo = pd.DataFrame([
                                {
                                    "Data": "2026-01-15", 
                                    "Tipo": "Entrada", 
                                    "Valor": 1500.00, 
                                    "Descricao": "Serviço Prestado Empresa X", 
                                    "Conta_Banco": contas_bancos[0] if contas_bancos else "1.1.1.01 - Caixa", 
                                    "Categoria": contas_receitas[0] if contas_receitas else "3.2.1 - Serviços"
                                },
                                {
                                    "Data": "2026-01-18", 
                                    "Tipo": "Saída", 
                                    "Valor": 180.50, 
                                    "Descricao": "Material de Escritório", 
                                    "Conta_Banco": contas_bancos[0] if contas_bancos else "1.1.1.01 - Caixa", 
                                    "Categoria": contas_despesas[0] if contas_despesas else "4.1.1 - Despesas"
                                }
                            ])
                            csv_modelo = df_exemplo.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig")
                            st.download_button(
                                "📥 Baixar Modelo (.CSV)", 
                                data=csv_modelo, 
                                file_name="modelo_importacao_kazimm.csv", 
                                mime="text/csv",
                                key="btn_download_modelo_csv"
                            )

                        with col_p2:
                            arquivo_planilha = st.file_uploader(
                                "Selecione sua planilha preenchida", 
                                type=["xlsx", "csv"],
                                key="upload_arquivo_planilha"
                            )

                        if arquivo_planilha:
                            try:
                                if arquivo_planilha.name.endswith(".csv"):
                                    df_upload = pd.read_csv(arquivo_planilha, sep=None, engine="python", decimal=",")
                                else:
                                    df_upload = pd.read_excel(arquivo_planilha)

                                df_upload.columns = [c.strip().lower() for c in df_upload.columns]
                                for _, row in df_upload.iterrows():
                                    dados_processados.append({
                                        "Data": str(row.get("data", "")),
                                        "Tipo": "Entrada" if "ent" in str(row.get("tipo", "")).lower() else "Saída",
                                        "Valor": float(row.get("valor", 0.0)),
                                        "Histórico / Descrição": str(row.get("descricao", row.get("historico", ""))),
                                        "Conta Contrapartida": str(row.get("categoria", ""))
                                    })
                                st.success(f"{ICONES['sucesso']} Planilha lida com sucesso: **{len(dados_processados)} transações** encontradas!")
                            except Exception as e:
                                st.error(f"Erro ao processar planilha: {e}")

                    if dados_processados:
                        st.markdown("---")
                        st.write(f"{ICONES['pesquisar']} #### Revisão e Classificação dos Lançamentos")
                        st.caption("Classifique as contrapartidas diretamente na tabela abaixo antes de confirmar a importação.")

                        for item in dados_processados:
                            if not item["Conta Contrapartida"]:
                                memo_upper = item["Histórico / Descrição"].upper()
                                
                                if item["Tipo"] == "Entrada":
                                    if any(k in memo_upper for k in ["VENDA", "MERCADORIA", "PRODUTO"]):
                                        item["Conta Contrapartida"] = next((c for c in contas_receitas if "Mercadoria" in c or "Comércio" in c), contas_receitas[0] if contas_receitas else "")
                                    else:
                                        item["Conta Contrapartida"] = next((c for c in contas_receitas if "Serviço" in c or "Servico" in c), contas_receitas[0] if contas_receitas else "")
                                else:
                                    if any(k in memo_upper for k in ["TARIFA", "TAXA", "IOF", "ANUIDADE", "MANUTENCAO"]):
                                        item["Conta Contrapartida"] = next((c for c in contas_despesas if "Financeira" in c or "Tarifa" in c or "Banc" in c), contas_despesas[0] if contas_despesas else "")
                                    elif any(k in memo_upper for k in ["PECA", "PEÇAS", "FORNECEDOR", "COMPRA", "MATERIAL"]):
                                        item["Conta Contrapartida"] = next((c for c in contas_despesas if "Estoque" in c or "Custo" in c or "Fornecedor" in c), contas_despesas[0] if contas_despesas else "")
                                    else:
                                        item["Conta Contrapartida"] = next((c for c in contas_despesas if "Gerais" in c or "Operacional" in c or "Despesa" in c), contas_despesas[0] if contas_despesas else "")

                        df_previa = pd.DataFrame(dados_processados)

                        df_editado = st.data_editor(
                            df_previa,
                            column_config={
                                "Data": st.column_config.TextColumn("Data", disabled=True),
                                "Tipo": st.column_config.TextColumn("Tipo", disabled=True),
                                "Valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f", disabled=True),
                                "Histórico / Descrição": st.column_config.TextColumn("Histórico Bancário", disabled=True),
                                "Conta Contrapartida": st.column_config.SelectboxColumn(
                                    "Categoria / Conta de Destino",
                                    help="Defina para qual conta de receita ou despesa esse lançamento deve ir.",
                                    options=lista_todas_contas,
                                    required=True
                                )
                            },
                            hide_index=True,
                            use_container_width=True,
                            key="editor_importacao_lote"
                        )

                        conta_banco_final = conta_destino_ofx if tipo_origem == "Extrato Bancário (.OFX)" else contas_bancos[0]

                        if st.button("Confirmar e Importar Todos os Lançamentos", type="primary", use_container_width=True, key="btn_confirmar_lote_final"):
                            progresso = st.progress(0)
                            linhas_finais = df_editado.to_dict(orient="records")
                            total = len(linhas_finais)
                            sucessos = 0

                            conn = get_connection()
                            cursor = conn.cursor()

                            try:
                                for i, item in enumerate(linhas_finais):
                                    data_val = item["Data"]
                                    tipo_mov = item["Tipo"]
                                    valor_val = float(item["Valor"])
                                    hist_val = f"[Importação em Lote] {item['Histórico / Descrição']}".strip()
                                    contrapartida = item["Conta Contrapartida"]

                                    if tipo_mov == "Entrada":
                                        c_debito = conta_banco_final
                                        c_credito = contrapartida
                                    else:
                                        c_debito = contrapartida
                                        c_credito = conta_banco_final

                                    cursor.execute(
                                        "INSERT INTO lancamentos (cliente_id, data, conta_debito, conta_credito, valor, historico) VALUES (%s, %s, %s, %s, %s, %s)",
                                        (cliente_ativo_id, data_val, c_debito, c_credito, valor_val, hist_val)
                                    )
                                    sucessos += 1
                                    progresso.progress((i + 1) / total)

                                conn.commit()
                                limpar_cache()
                                st.success(f"Pronto! **{sucessos} lançamentos** foram importados e classificados com sucesso!")
                                st.balloons()

                            except Exception as err:
                                conn.rollback()
                                st.error(f"Erro ao salvar lançamentos em lote: {err}")
                            finally:
                                conn.close()

            # --------------------------------------------------------------
            # ABA 2: IMPORTAR EXTRATO / PLANILHA DO CLIENTE (Simples)
            # --------------------------------------------------------------
            with tab_extratos:
                st.markdown("##### Planilha Simplificada do Cliente (Leitura Automática)")
                st.info("Envie a planilha do cliente para realizar a leitura e o registro automático no Livro Caixa.")

                arquivo = st.file_uploader(
                    "Selecione a planilha do cliente", 
                    type=["xlsx", "xls", "xlsm"],
                    key="upload_planilha_cliente_simples"
                )

                if arquivo is not None:
                    try:
                        df = pd.read_excel(arquivo)
                        
                        st.write("##### Pré-visualização da planilha carregada:")
                        st.dataframe(df.head(10), use_container_width=True)

                        if st.button("Processar e Importar Lançamentos", use_container_width=True, key="btn_proc_planilha_simples"):
                            conn = get_connection()
                            cursor = conn.cursor()
                            importados = 0

                            for idx, row in df.iterrows():
                                data_val = pd.to_datetime(row.get("Data"), errors="coerce")
                                if pd.isna(data_val):
                                    continue
                                data_str = data_val.strftime("%Y-%m-%d")

                                desc = str(row.get("Descrição", "") or "").strip()
                                cat = str(row.get("Categoria", "") or "").strip()
                                if cat.lower() in ["nan", "none", ""]:
                                    cat = "Despesas Gerais"

                                doc_num = row.get("Nfe / Cupom") or row.get("NFe_Cupom/Série") or row.get("NFe") or ""
                                serie_num = row.get("Série") or ""
                                
                                doc_str = str(doc_num).strip() if pd.notna(doc_num) and str(doc_num).lower() not in ["nan", "none"] else ""
                                serie_str = str(serie_num).strip() if pd.notna(serie_num) and str(serie_num).lower() not in ["nan", "none"] else ""
                                
                                doc_info = f"{doc_str} (Série {serie_str})" if (doc_str and serie_str) else (doc_str or serie_str or "S/N")

                                val_saida = float(row.get("Valor Saída", 0) if pd.notna(row.get("Valor Saída")) else 0)
                                val_entrada = float(row.get("Valor Entrada", 0) if pd.notna(row.get("Valor Entrada")) else 0)

                                historico = f"{desc} | Doc: {doc_info} | Cat: {cat}".strip(" |")

                                if val_entrada > 0:
                                    cursor.execute(
                                        """
                                        INSERT INTO lancamentos (cliente_id, data, conta_debito, conta_credito, valor, historico)
                                        VALUES (%s, %s, '1.1.1 - Caixa Geral', '3.1.1 - Receita de Vendas/Serviços', %s, %s)
                                        """,
                                        (cliente_ativo_id, data_str, val_entrada, historico)
                                    )
                                    importados += 1

                                if val_saida > 0:
                                    conta_debito_despesa = f"4.1.1 - {cat}"
                                    cursor.execute(
                                        """
                                        INSERT INTO lancamentos (cliente_id, data, conta_debito, conta_credito, valor, historico)
                                        VALUES (%s, %s, %s, '1.1.1 - Caixa Geral', %s, %s)
                                        """,
                                        (cliente_ativo_id, data_str, conta_debito_despesa, val_saida, historico)
                                    )
                                    importados += 1

                            conn.commit()
                            limpar_cache()
                            conn.close()

                            st.success(f"Importação concluída! **{importados}** registros foram salvos no banco de dados do cliente.")
                            st.rerun()

                    except Exception as e:
                        st.error(f"Erro ao processar o arquivo Excel: {e}")

# ==============================================================================
# BLOCO CONTAS A PAGAR E PROVISÕES - UNIFICADO E ROLÁVEL
# ==============================================================================
elif "Contas a Pagar" in str(opcao) or opcao == item_provisoes:
    st.markdown(f"#### {ICONES.get('provisoes', ':material/schedule:')} Gestão de Contas a Pagar e Provisões")

    # 1. Validação centralizada de permissões do plano (Paywall Freemium)
    if not regras.get('provisoes', False):
        st.info("ℹ️ Controle guias de impostos (DAS), parcelamentos e contas futuras com baixa automática no Livro Caixa.")
        exibir_bloqueio_upgrade("Contas a Pagar e Provisões Financeiras", plano_minimo="pro")
    else:
        cliente_ativo_id = st.session_state.get("cliente_id_ativo")

        if not cliente_ativo_id:
            st.warning(f"{ICONES.get('alerta', ':material/warning:')} Nenhum cliente selecionado. Escolha um cliente ativo na barra lateral para prosseguir.")
        else:
            conn = get_connection()
            df_cliente = pd.read_sql_query(
                "SELECT id, nome, regime, cnpj_cpf, cnae_atividade, telefone FROM clientes WHERE id = %s AND user_id = %s", 
                conn, 
                params=(cliente_ativo_id, st.session_state.user.id)
            )
            conn.close()

            if df_cliente.empty:
                st.error("Erro de segurança: Cliente não encontrado ou sem permissão de acesso.")
            else:
                # 2. Painel rolável com altura fixa (padrão de ergonomia ERP)
                with st.container(height=580, border=True):
                    
                    tab_pendentes, tab_agendar, tab_historico = st.tabs([
                        f"{ICONES.get('pendente', ':material/pending_actions:')} Contas Pendentes",
                        f"{ICONES.get('adicionar', ':material/add_circle:')} Agendar Nova Obrigação",
                        f"{ICONES.get('lancamentos', ':material/history:')} Histórico de Pagas"
                    ])

                    # Carregamento centralizado de provisões do cliente
                    conn = get_connection()
                    df_provisoes = pd.read_sql_query(
                        """
                        SELECT id, descricao, tipo, valor, data_vencimento, status 
                        FROM provisoes 
                        WHERE cliente_id = %s 
                        ORDER BY status DESC, data_vencimento ASC
                        """,
                        conn,
                        params=(cliente_ativo_id,)
                    )
                    conn.close()

                    df_pendentes = df_provisoes[df_provisoes["status"] == "Pendente"] if not df_provisoes.empty else pd.DataFrame()
                    df_pagas = df_provisoes[df_provisoes["status"] == "Pago"] if not df_provisoes.empty else pd.DataFrame()

                    # ----------------------------------------------------------
                    # ABA 1: CONTAS PENDENTES, EMISSÃO DAS & LIQUIDAÇÃO
                    # ----------------------------------------------------------
                    with tab_pendentes:
                        # 1. Executa a checagem automática do DAS-MEI em segundo plano
                        cnae_cli = df_cliente.iloc[0].get("cnae_atividade", "") if not df_cliente.empty else ""
                        agendou_novo, val_gerado = verificar_e_agendar_das_mensal(cliente_ativo_id, cnae_cli)
                        if agendou_novo:
                            st.toast(f"🔔 Guia DAS-MEI deste mês agendada automaticamente: R$ {val_gerado:.2f}", icon="📅")
                            st.rerun()

                        total_pendente = df_pendentes["valor"].sum() if not df_pendentes.empty else 0.0
                        
                        col_tot1, col_tot2 = st.columns([2, 1])
                        with col_tot1:
                            st.markdown(f"##### Obrigações em Aberto")
                        with col_tot2:
                            st.markdown(f"<div style='text-align: right; font-size: 0.9rem;'>Total Pendente: <strong>{formatar_brl(total_pendente)}</strong></div>", unsafe_allow_html=True)

                        if df_pendentes.empty:
                            st.success("Tudo em dia! Nenhuma conta ou guia pendente para este cliente.")
                        else:
                            from datetime import date
                            hoje = date.today()
                            cnpj_raw = "".join(filter(str.isdigit, str(df_cliente.iloc[0].get("cnpj_cpf", ""))))

                            for idx, row in df_pendentes.iterrows():
                                dt_venc = pd.to_datetime(row['data_vencimento']).date()
                                dias_restantes = (dt_venc - hoje).days
                                eh_das = (row['tipo'] == 'Guia DAS')

                                # Régua de Alertas (Vencida vs Vencendo em 5 dias vs No prazo)
                                if dias_restantes < 0:
                                    status_badge = f"<span style='background-color: #fee2e2; color: #dc2626; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 11px;'>🔴 VENCIDA HÁ {abs(dias_restantes)} DIA(S)</span>"
                                    cor_borda = "#ef4444"
                                elif dias_restantes <= 5:
                                    txt_alerta = "VENCE HOJE" if dias_restantes == 0 else f"VENCE EM {dias_restantes} DIA(S)"
                                    status_badge = f"<span style='background-color: #fef3c7; color: #b45309; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 11px;'>🟡 {txt_alerta}</span>"
                                    cor_borda = "#f59e0b"
                                else:
                                    status_badge = f"<span style='background-color: #e0f2fe; color: #0369a1; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 11px;'>🟢 Vence em {dias_restantes} dias</span>"
                                    cor_borda = "#e2e8f0"

                                with st.container(border=True):
                                    col_info, col_acao = st.columns([3, 1.4], vertical_alignment="center")
                                    
                                    with col_info:
                                        venc_formatado = dt_venc.strftime('%d/%m/%Y')
                                        st.markdown(f"**Vencimento: {venc_formatado}** — `{row['tipo']}` &nbsp; {status_badge}", unsafe_allow_html=True)
                                        st.write(f"**{row['descricao']}**")
                                        st.caption(f"Valor a Liquidar: **{formatar_brl(row['valor'])}**")

                                    with col_acao:
                                        # Se for Guia DAS, exibe o botão no estilo oficial Kazimm + CNPJ para cópia
                                        if eh_das:
                                            url_pgmei = "https://www8.receita.fazenda.gov.br/SimplesNacional/Aplicacoes/ATSPO/pgmei.app/Identificacao"
                                            
                                            # Botão estilizado no padrão Kazimm (Azul institucional #0176a1)
                                            st.markdown(
                                                f"""
                                                <a href="{url_pgmei}" target="_blank" style="
                                                    display: flex;
                                                    align-items: center;
                                                    justify-content: center;
                                                    gap: 6px;
                                                    width: 100%;
                                                    background-color: #f0f7fa;
                                                    color: #0176a1;
                                                    border: 1.5px solid #0176a1;
                                                    border-radius: 6px;
                                                    padding: 6px 10px;
                                                    font-weight: 600;
                                                    font-size: 13px;
                                                    text-decoration: none;
                                                    margin-bottom: 8px;
                                                    transition: all 0.2s ease;
                                                ">
                                                    🌐 Emitir no PGMEI
                                                </a>
                                                """,
                                                unsafe_allow_html=True
                                            )
                                            
                                            # Exibe o CNPJ com botão nativo de 1 clique para copiar
                                            if cnpj_raw:
                                                st.code(cnpj_raw, language=None)
                                        # ==============================================================
                                        # RÉGUA DE AVISOS (WHATSAPP E E-MAIL)
                                        # ==============================================================
                                        st.markdown("<div style='margin-top: 8px;'></div>", unsafe_allow_html=True)
                                        col_wa, col_em = st.columns(2, gap="small")
                                        
                                        # 1. Recupera dados do cliente logado
                                        telefone_cli = df_cliente.iloc[0].get("telefone", "")
                                        nome_cli = df_cliente.iloc[0].get("nome", "Cliente")
                                        
                                        status_wa = "VENCIDA" if dias_restantes < 0 else ("HOJE" if dias_restantes == 0 else "AVENCER")
                                        link_wa = gerar_link_whatsapp(telefone_cli, nome_cli, row['descricao'], row['valor'], dt_venc, status_wa)
                                        
                                        # 2. Renderiza os botões (Estilo Pill / Pílula)
                                        with col_wa:
                                            if link_wa:
                                                st.markdown(
                                                    f"""
                                                    <a href="{link_wa}" target="_blank" style="
                                                        display: flex; align-items: center; justify-content: center; gap: 4px;
                                                        background-color: #25D366; color: white; border-radius: 4px; padding: 6px 0;
                                                        font-weight: 600; font-size: 13px; text-decoration: none; transition: 0.2s;
                                                    " title="Cobrar via WhatsApp">
                                                        💬 Whats
                                                    </a>
                                                    """, unsafe_allow_html=True
                                                )
                                            else:
                                                st.button("💬 Whats", disabled=True, help="Telefone do cliente não cadastrado.", key=f"wa_dis_{row['id']}")

                                        with col_em:
                                            if st.button("✉️ E-mail", key=f"btn_email_{row['id']}", help="Disparar aviso por e-mail", use_container_width=True):
                                                modal_enviar_email(nome_cli, row['descricao'], row['valor'], venc_formatado)
                                                
                                        st.markdown("<div style='margin-bottom: 8px;'></div>", unsafe_allow_html=True)

                                    

                                        if st.button(
                                            "Pagar / Baixar", 
                                            key=f"btn_baixa_prov_{row['id']}", 
                                            icon=ICONES.get("sucesso", ":material/check_circle:"),
                                            type="primary",
                                            use_container_width=True
                                        ):
                                            conn_baixa = get_connection()
                                            cursor_baixa = conn_baixa.cursor()
                                            
                                            # Atualiza status da obrigação
                                            cursor_baixa.execute("UPDATE provisoes SET status = 'Pago' WHERE id = %s", (row['id'],))
                                            
                                            # Registra a saída correspondente no Livro Caixa
                                            conta_saida_desc = "4.1.2 - Impostos e Taxas (DAS)" if eh_das else "4.1.1 - Despesas Operacionais"
                                            cursor_baixa.execute(
                                                """
                                                INSERT INTO lancamentos (cliente_id, data, conta_debito, conta_credito, valor, historico)
                                                VALUES (%s, CURRENT_DATE, %s, '1.1.1.02 - Banco Conta Movimento', %s, %s)
                                                """,
                                                (cliente_ativo_id, conta_saida_desc, row['valor'], f"Pagamento baixado de provisão: {row['descricao']}")
                                            )
                                            conn_baixa.commit()
                                            conn_baixa.close()
                                            limpar_cache()
                                            
                                            st.success(f"Conta '{row['descricao']}' liquidada com sucesso!")
                                            st.rerun()
                                            
                                            st.success(f"Conta '{row['descricao']}' liquidada com sucesso!")
                                            st.rerun()

                    # ----------------------------------------------------------
                    # ABA 2: AGENDAR NOVA OBRIGAÇÃO / GUIA
                    # ----------------------------------------------------------
                    with tab_agendar:
                        st.markdown("##### Registo de Nova Obrigação Futura")
                        
                        with st.form("form_nova_provisao_slim", clear_on_submit=True):
                            col_p1, col_p2 = st.columns([2, 1])
                            with col_p1:
                                desc_provisao = st.text_input(
                                    "Descrição da Obrigação", 
                                    placeholder="Ex: Guia DAS Mensal - 10/2026 ou Parcelamento RFB 02/10"
                                )
                            with col_p2:
                                tipo_provisao = st.selectbox(
                                    "Tipo de Conta", 
                                    ["Guia DAS", "Parcelamento RFB", "Aluguel", "Fornecedor / Compra", "Outros"]
                                )

                            col_p3, col_p4 = st.columns([1, 1])
                            with col_p3:
                                valor_provisao = st.number_input("Valor (R$)", min_value=0.01, step=10.0, format="%.2f")
                            with col_p4:
                                data_venc = st.date_input("Data de Vencimento")

                            salvar_prov = st.form_submit_button(
                                "Agendar Conta a Pagar", 
                                type="primary",
                                icon=ICONES.get("adicionar", ":material/add:"),
                                use_container_width=True
                            )

                            if salvar_prov:
                                if desc_provisao and valor_provisao > 0:
                                    conn_ins = get_connection()
                                    cursor_ins = conn_ins.cursor()
                                    cursor_ins.execute(
                                        """
                                        INSERT INTO provisoes (cliente_id, descricao, tipo, valor, data_vencimento, status)
                                        VALUES (%s, %s, %s, %s, %s, 'Pendente')
                                        """,
                                        (cliente_ativo_id, desc_provisao, tipo_provisao, valor_provisao, data_venc)
                                    )
                                    conn_ins.commit()
                                    conn_ins.close()
                                    limpar_cache()
                                    st.success(f"Obrigação '{desc_provisao}' agendada com sucesso!")
                                    st.rerun()
                                else:
                                    st.warning("Preencha a descrição e indique um valor válido.")

                    # ----------------------------------------------------------
                    # ABA 3: HISTÓRICO DE OBRIGAÇÕES LIQUIDADAS
                    # ----------------------------------------------------------
                    with tab_historico:
                        st.markdown("##### Obrigações Já Liquidadas")
                        if df_pagas.empty:
                            st.info("Nenhuma conta liquidada no histórico deste cliente.")
                        else:
                            total_pago = df_pagas["valor"].sum()
                            st.caption(f"Volume Total Liquidado: **{formatar_brl(total_pago)}**")

                            df_pagas_exib = df_pagas.copy()
                            df_pagas_exib["Data Vencimento"] = pd.to_datetime(df_pagas_exib["data_vencimento"]).dt.strftime('%d/%m/%Y')
                            df_pagas_exib["Valor (R$)"] = df_pagas_exib["valor"].apply(formatar_brl)

                            st.dataframe(
                                df_pagas_exib[["Data Vencimento", "descricao", "tipo", "Valor (R$)", "status"]].rename(columns={
                                    "descricao": "Descrição",
                                    "tipo": "Categoria",
                                    "status": "Status"
                                }),
                                use_container_width=True,
                                hide_index=True,
                                height=420
                            )


# ==============================================================================
# BLOCO CONCILIAÇÃO BANCÁRIA - ESTRUTURA SLIM EM ABAS
# ==============================================================================
elif opcao == "Conciliação Bancária":
    st.markdown(f"#### {ICONES.get('conciliacao', ':material/sync_alt:')} Conciliação Bancária & Evolução de Saldos")

    cliente_ativo_id = st.session_state.get("cliente_id_ativo") or st.session_state.get("cliente_id")

    if not cliente_ativo_id:
        st.warning(f"{ICONES.get('alerta', ':material/warning:')} Selecione um cliente ativo na barra lateral para prosseguir.")
    else:
        df_lancamentos = pd.DataFrame()
        conn = get_connection()
        try:
            df_lancamentos = pd.read_sql(
                "SELECT * FROM lancamentos WHERE cliente_id = %s ORDER BY data ASC;", 
                conn, 
                params=(cliente_ativo_id,)
            )
        except Exception as e:
            st.error(f"Erro ao carregar lançamentos para a conciliação: {e}")
        finally:
            conn.close()

        if df_lancamentos.empty:
            st.info("Nenhum lançamento encontrado para este cliente para realizar a conciliação.")
        else:
            df_conc = df_lancamentos.copy()
            df_conc['data_dt'] = pd.to_datetime(df_conc['data'], errors='coerce')
            df_conc = df_conc.dropna(subset=['data_dt'])
            df_conc['mes_ano'] = df_conc['data_dt'].dt.strftime('%Y-%m')

            # Mapeamento dinâmico das contas de Caixa e Bancos
            contas_deb = df_conc['conta_debito'].dropna().unique().tolist()
            contas_cred = df_conc['conta_credito'].dropna().unique().tolist()
            todas_contas = sorted(list(set(contas_deb + contas_cred)))
            
            contas_bancarias = [c for c in todas_contas if any(k in c.lower() for k in ['banco', 'caixa', '1.1.1'])]
            if not contas_bancarias:
                contas_bancarias = todas_contas

            # Área de trabalho delimitada (container rolável)
            with st.container(height=580, border=True):
                
                # Seletor de Conta e Saldo Inicial no topo da área rolável
                col_c1, col_c2 = st.columns([2, 1])
                with col_c1:
                    conta_sel = st.selectbox(
                        "Conta Bancária / Caixa em Análise:", 
                        contas_bancarias,
                        key="sb_conc_conta_ativa"
                    )
                with col_c2:
                    saldo_ini = st.number_input(
                        "Saldo Inicial da Conta (R$):", 
                        value=0.00, 
                        step=100.00, 
                        format="%.2f",
                        key="num_conc_saldo_inicial"
                    )

                if conta_sel:
                    # Apuração da evolução mensal de saldos
                    meses_unicos = sorted(df_conc['mes_ano'].unique())
                    dados_conc = []
                    saldo_acum = saldo_ini

                    for m in meses_unicos:
                        df_mes = df_conc[df_conc['mes_ano'] == m]
                        entradas = df_mes[df_mes['conta_debito'] == conta_sel]['valor'].sum()
                        saidas = df_mes[df_mes['conta_credito'] == conta_sel]['valor'].sum()
                        saldo_mes = entradas - saidas
                        saldo_final = saldo_acum + saldo_mes

                        dt_ref = pd.to_datetime(m + "-01")
                        meses_pt = {
                            1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
                            7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'
                        }
                        mes_label = f"{meses_pt[dt_ref.month]}/{dt_ref.year}"

                        dados_conc.append({
                            'Mês/Ano': mes_label,
                            'Saldo Anterior': saldo_acum,
                            'Entradas (R$)': entradas,
                            'Saídas (R$)': saidas,
                            'Resultado do Mês': saldo_mes,
                            'Saldo Final (Calculado)': saldo_final
                        })
                        saldo_acum = saldo_final

                    df_conciliado = pd.DataFrame(dados_conc)

                    tab_fechamento, tab_analitico = st.tabs([
                        f"{ICONES.get('dre', ':material/table_chart:')} Fechamento Mensal",
                        f"{ICONES.get('lancamentos', ':material/receipt_long:')} Extrato Analítico da Conta"
                    ])

                    # ----------------------------------------------------------
                    # ABA 1: FECHAMENTO MENSAL & EVOLUÇÃO
                    # ----------------------------------------------------------
                    with tab_fechamento:
                        tot_ent = df_conciliado['Entradas (R$)'].sum() if not df_conciliado.empty else 0.0
                        tot_sai = df_conciliado['Saídas (R$)'].sum() if not df_conciliado.empty else 0.0
                        saldo_atual = df_conciliado['Saldo Final (Calculado)'].iloc[-1] if not df_conciliado.empty else saldo_ini

                        # Cartões de métricas compactos
                        m1, m2, m3, m4 = st.columns(4)
                        m1.metric("Saldo Inicial", f"R$ {saldo_ini:,.2f}")
                        m2.metric("Total Entradas", f"R$ {tot_ent:,.2f}")
                        m3.metric("Total Saídas", f"R$ {tot_sai:,.2f}")
                        m4.metric("Saldo Atual", f"R$ {saldo_atual:,.2f}")

                        st.markdown("##### Resumo de Saldos e Resultados")
                        df_exib = df_conciliado.copy()
                        for c in ['Saldo Anterior', 'Entradas (R$)', 'Saídas (R$)', 'Resultado do Mês', 'Saldo Final (Calculado)']:
                            df_exib[c] = df_exib[c].apply(lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

                        st.dataframe(df_exib, use_container_width=True, hide_index=True, height=280)

                    # ----------------------------------------------------------
                    # ABA 2: EXTRATO ANALÍTICO (Livro Razão da Conta)
                    # ----------------------------------------------------------
                    with tab_analitico:
                        st.markdown(f"##### Movimentações Detalhadas — `{conta_sel}`")
                        
                        df_conta_det = df_conc[
                            (df_conc['conta_debito'] == conta_sel) | 
                            (df_conc['conta_credito'] == conta_sel)
                        ].copy()

                        if df_conta_det.empty:
                            st.info("Nenhuma movimentação registrada especificamente nesta conta.")
                        else:
                            df_conta_det['Tipo'] = df_conta_det['conta_debito'].apply(
                                lambda c: "🟢 Entrada" if c == conta_sel else "🔴 Saída"
                            )
                            df_conta_det['Data'] = df_conta_det['data_dt'].dt.strftime('%d/%m/%Y')
                            df_conta_det['Valor (R$)'] = df_conta_det['valor'].apply(formatar_brl)
                            df_conta_det['Contrapartida'] = df_conta_det.apply(
                                lambda r: r['conta_credito'] if r['conta_debito'] == conta_sel else r['conta_debito'], 
                                axis=1
                            )

                            cols_view = ['Data', 'Tipo', 'Valor (R$)', 'Contrapartida', 'historico']
                            st.dataframe(
                                df_conta_det[cols_view].rename(columns={
                                    'historico': 'Histórico / Documento'
                                }),
                                use_container_width=True,
                                hide_index=True,
                                height=380
                            )

# ==============================================================================
# BLOCO RELATÓRIOS E AUDITORIA - CONTAINER SLIM EM 4 ABAS
# ==============================================================================
elif "Relatório" in str(opcao):
    st.markdown(f"#### {ICONES.get('dre', ':material/analytics:')} Central de Relatórios & Apuração Contábil")

    cliente_ativo_id = st.session_state.get("cliente_id_ativo")

    if not cliente_ativo_id:
        st.warning(f"{ICONES.get('alerta', ':material/warning:')} Nenhum cliente selecionado. Escolha um cliente ativo na barra lateral para prosseguir.")
    else:
        conn = get_connection()
        try:
            df_cliente = pd.read_sql_query(
                "SELECT id, nome, cnpj_cpf, regime FROM clientes WHERE id = %s AND user_id = %s", 
                conn, 
                params=(cliente_ativo_id, st.session_state.user.id)
            )
            df_lancamentos = pd.read_sql_query(
                "SELECT conta_debito, conta_credito, valor, data, historico FROM lancamentos WHERE cliente_id = %s",
                conn,
                params=(cliente_ativo_id,)
            )
        except Exception as e:
            st.error(f"Erro ao carregar dados dos relatórios: {e}")
            df_cliente, df_lancamentos = pd.DataFrame(), pd.DataFrame()
        finally:
            conn.close()

        if df_cliente.empty:
            st.error("Erro de segurança: Cliente não encontrado ou sem permissão de acesso.")
        elif df_lancamentos.empty:
            st.info(f"{ICONES.get('atencao', ':material/info:')} Nenhum lançamento registrado para este cliente para gerar relatórios.")
        else:
            nome_cliente = df_cliente.iloc[0]["nome"]
            cnpj_cliente = df_cliente.iloc[0]["cnpj_cpf"]
            regime_cliente = df_cliente.iloc[0]["regime"]

            # Área de trabalho delimitada (Container rolável padrão ERP)
            with st.container(height=580, border=True):
                
                tab_gerencial, tab_oficial, tab_anual, tab_manutencao = st.tabs([
                    f"{ICONES.get('dre', ':material/table_chart:')} Relatório Gerencial (DRE)", 
                    f"{ICONES.get('relatorios', ':material/description:')} Relatório Oficial MEI (Imprimível)",
                    f"{ICONES.get('agenda', ':material/event_note:')} Declaração Anual (DASN-SIMEI)",
                    f"{ICONES.get('ferramentas', ':material/build:')} Backup & Manutenção"
                ])

                # --------------------------------------------------------------
                # ABA 1: RELATÓRIO GERENCIAL (EVOLUÇÃO & CATEGORIAS)
                # --------------------------------------------------------------
                with tab_gerencial:
                    st.markdown("##### Evolução Mensal (Receitas vs. Despesas)")
                    
                    df_gerencial = df_lancamentos.copy()
                    df_gerencial['data_dt'] = pd.to_datetime(df_gerencial['data'], errors='coerce')
                    df_gerencial = df_gerencial.dropna(subset=['data_dt'])
                    
                    meses_pt = {1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun', 7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'}
                    df_gerencial['mes_ano_cod'] = df_gerencial['data_dt'].dt.strftime('%Y-%m')
                    
                    meses_unicos = sorted(df_gerencial['mes_ano_cod'].unique())
                    dados_mensais = []
                    
                    for m in meses_unicos:
                        df_m = df_gerencial[df_gerencial['mes_ano_cod'] == m]
                        rec_m = df_m[df_m['conta_credito'].str.contains('3\.|Receita', case=False, na=False)]['valor'].sum()
                        desp_m = df_m[df_m['conta_debito'].str.contains('4\.|Despesa|Estoque', case=False, na=False)]['valor'].sum()
                        saldo_m = rec_m - desp_m
                        
                        dt_ref = pd.to_datetime(m + "-01")
                        label_m = f"{meses_pt[dt_ref.month]}/{dt_ref.year}"
                        
                        dados_mensais.append({
                            "Mês/Ano": label_m,
                            "Receitas": rec_m,
                            "Despesas": desp_m,
                            "Saldo Líquido": saldo_m
                        })
                        
                    if dados_mensais:
                        df_evolucao = pd.DataFrame(dados_mensais)
                        
                        df_evolucao_exib = df_evolucao.copy()
                        df_evolucao_exib["Receitas"] = df_evolucao_exib["Receitas"].apply(formatar_brl)
                        df_evolucao_exib["Despesas"] = df_evolucao_exib["Despesas"].apply(formatar_brl)
                        df_evolucao_exib["Saldo Líquido"] = df_evolucao_exib["Saldo Líquido"].apply(formatar_brl)
                        
                        st.dataframe(df_evolucao_exib, use_container_width=True, hide_index=True)
                        
                        try:
                            import plotly.graph_objects as go
                            fig_bar = go.Figure()
                            fig_bar.add_trace(go.Bar(x=df_evolucao["Mês/Ano"], y=df_evolucao["Receitas"], name="Receitas", marker_color="#10B981"))
                            fig_bar.add_trace(go.Bar(x=df_evolucao["Mês/Ano"], y=df_evolucao["Despesas"], name="Despesas", marker_color="#EF4444"))
                            fig_bar.update_layout(
                                barmode='group', 
                                height=300, 
                                margin=dict(t=10, b=10, l=10, r=10), 
                                legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5)
                            )
                            st.plotly_chart(fig_bar, use_container_width=True)
                        except Exception:
                            st.bar_chart(df_evolucao.set_index("Mês/Ano")[["Receitas", "Despesas"]])

                    st.markdown("---")
                    st.markdown("##### Acumulado por Categoria (Saldo Líquido no Período)")

                    filtro_caixa_banco = "1.1.1|Caixa|Banco"
                    df_entradas = (df_lancamentos[~df_lancamentos["conta_credito"].str.contains(filtro_caixa_banco, case=False, na=False)]
                        .groupby("conta_credito")["valor"].sum().reset_index().rename(columns={"conta_credito": "conta", "valor": "entradas"}))
                    df_saidas = (df_lancamentos[~df_lancamentos["conta_debito"].str.contains(filtro_caixa_banco, case=False, na=False)]
                        .groupby("conta_debito")["valor"].sum().reset_index().rename(columns={"conta_debito": "conta", "valor": "saidas"}))
                    df_total = pd.merge(df_entradas, df_saidas, on="conta", how="outer").fillna(0.0)

                    dados_relatorio = []
                    for _, row in df_total.iterrows():
                        conta_nome = str(row["conta"])
                        v_ent, v_sai = float(row["entradas"]), float(row["saidas"])

                        if conta_nome.startswith("3") or "Receita" in conta_nome:
                            val_liquido = v_ent - v_sai
                            if val_liquido != 0: 
                                dados_relatorio.append({"Grupo": "🟢 Receitas", "Categoria / Conta": conta_nome, "Total (R$)": val_liquido})
                        elif conta_nome.startswith("4") or "Despesa" in conta_nome or "Estoque" in conta_nome:
                            val_liquido = v_sai - v_ent
                            if val_liquido != 0: 
                                dados_relatorio.append({"Grupo": "🔴 Despesas", "Categoria / Conta": conta_nome, "Total (R$)": val_liquido})
                        else:
                            val_liquido = v_ent - v_sai
                            if val_liquido != 0:
                                grupo_label = "🔄 Patrimonial / Entrada" if val_liquido > 0 else "🔄 Patrimonial / Saída"
                                dados_relatorio.append({"Grupo": grupo_label, "Categoria / Conta": conta_nome, "Total (R$)": abs(val_liquido)})

                    df_agrupado = pd.DataFrame(dados_relatorio)

                    if not df_agrupado.empty:
                        df_exibicao = df_agrupado.copy()
                        df_exibicao["Valor Formatado"] = df_exibicao["Total (R$)"].apply(formatar_brl)
                        st.dataframe(df_exibicao[["Grupo", "Categoria / Conta", "Valor Formatado"]], use_container_width=True, height=280, hide_index=True)

                        csv_rel = df_agrupado.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig")
                        st.download_button(
                            label="Exportar Relatório Gerencial (.csv)", 
                            data=csv_rel, 
                            file_name=f"relatorio_gerencial_{nome_cliente.replace(' ', '_').lower()}.csv", 
                            mime="text/csv",
                            icon=ICONES.get("extrato", ":material/download:"),
                            key="btn_down_rel_gerencial"
                        )

                # --------------------------------------------------------------
                # ABA 2: RELATÓRIO OFICIAL MEI (DOCUMENTO IMPRIMÍVEL A4)
                # --------------------------------------------------------------
                with tab_oficial:
                    st.markdown("##### Relatório Mensal das Receitas Brutas (Modelo Oficial)")
                    st.caption("Documento mensal obrigatório do MEI. Selecione o mês e utilize o botão de impressão dentro do relatório.")

                    df_oficial = df_lancamentos.copy()
                    df_oficial['data_dt'] = pd.to_datetime(df_oficial['data'], errors='coerce')
                    df_oficial = df_oficial.dropna(subset=['data_dt'])
                    
                    df_oficial['mes_ano_cod'] = df_oficial['data_dt'].dt.strftime('%Y-%m')
                    df_oficial['mes_ano_label'] = df_oficial['data_dt'].apply(lambda x: f"{meses_pt[x.month]}/{x.year}")
                    
                    meses_disponiveis = df_oficial[['mes_ano_cod', 'mes_ano_label']].drop_duplicates().sort_values('mes_ano_cod', ascending=False)
                    
                    if meses_disponiveis.empty:
                        st.info("Nenhuma data válida encontrada nos lançamentos para apuração oficial.")
                    else:
                        dict_meses = dict(zip(meses_disponiveis['mes_ano_label'], meses_disponiveis['mes_ano_cod']))
                        mes_selecionado = st.selectbox("Selecione o Período de Apuração:", list(dict_meses.keys()), key="sb_mes_oficial_mei")
                        cod_mes = dict_meses[mes_selecionado]

                        df_mes = df_oficial[
                            (df_oficial['mes_ano_cod'] == cod_mes) & 
                            (df_oficial['conta_credito'].str.contains('^3\.|^Receita', case=False, na=False, regex=True))
                        ]

                        v_I, v_II = 0.0, 0.0     # Comércio
                        v_IV, v_V = 0.0, 0.0     # Indústria
                        v_VII, v_VIII = 0.0, 0.0 # Serviços
                        
                        for _, row in df_mes.iterrows():
                            val = float(row['valor'])
                            conta = str(row['conta_credito']).lower()
                            hist = str(row['historico']).lower()

                            if "empréstimo" in conta or "emprestimo" in hist or "reembolso" in conta or "reembolso" in hist:
                                continue

                            sem_doc = "sem documento" in hist

                            if "serviço" in conta or "servico" in conta:
                                if sem_doc: v_VII += val
                                else: v_VIII += val
                            elif "indústria" in conta or "industria" in conta or "industrializado" in conta:
                                if sem_doc: v_IV += val
                                else: v_V += val
                            elif "comércio" in conta or "comercio" in conta or "venda" in conta or "mercadoria" in conta:
                                if sem_doc: v_I += val
                                else: v_II += val

                        v_III = v_I + v_II
                        v_VI = v_IV + v_V
                        v_IX = v_VII + v_VIII
                        v_X = v_III + v_VI + v_IX

                        html_relatorio = f"""
                        <!DOCTYPE html>
                        <html>
                        <head>
                            <meta charset="utf-8">
                            <title>Relatorio_Mensal_{mes_selecionado.replace('/', '_')}_{nome_cliente.replace(' ', '_')}</title>
                            <style>
                                @page {{
                                    size: A4 portrait;
                                    margin: 10mm 12mm 10mm 12mm;
                                }}
                                @media print {{
                                    body {{
                                        background-color: #ffffff !important;
                                        margin: 0 !important;
                                        padding: 0 !important;
                                    }}
                                    .no-print {{
                                        display: none !important;
                                    }}
                                    #relatorio-mei {{
                                        border: 1px solid #000 !important;
                                        box-shadow: none !important;
                                        margin: 0 auto !important;
                                        padding: 20px !important;
                                        width: 100% !important;
                                        max-width: 100% !important;
                                    }}
                                }}
                                body {{
                                    font-family: Arial, sans-serif;
                                    background-color: transparent;
                                    margin: 0;
                                    padding: 6px;
                                }}
                                .btn-print-bar {{
                                    display: flex;
                                    justify-content: flex-end;
                                    margin-bottom: 14px;
                                }}
                                .btn-print {{
                                    background-color: #0F172A;
                                    color: #FFFFFF;
                                    border: none;
                                    padding: 9px 18px;
                                    font-size: 13px;
                                    font-weight: 600;
                                    border-radius: 6px;
                                    cursor: pointer;
                                    display: inline-flex;
                                    align-items: center;
                                    gap: 8px;
                                    box-shadow: 0 1px 3px rgba(0,0,0,0.15);
                                    transition: background-color 0.2s ease;
                                }}
                                .btn-print:hover {{
                                    background-color: #1E293B;
                                }}
                                #relatorio-mei {{
                                    font-family: Arial, sans-serif;
                                    color: #000;
                                    background: #fff;
                                    max-width: 760px;
                                    margin: 0 auto;
                                    border: 1px solid #333;
                                    padding: 24px 28px;
                                    line-height: 1.35;
                                    font-size: 11.5px;
                                    box-sizing: border-box;
                                }}
                            </style>
                        </head>
                        <body>
                            <div class="no-print btn-print-bar">
                                <button class="btn-print" onclick="window.print()">
                                    🖨️ Imprimir Folha Oficial (A4 Retrato / Salvar PDF)
                                </button>
                            </div>

                            <div id="relatorio-mei">
                                <h3 style="text-align: center; margin-top: 0; margin-bottom: 18px; font-size: 15px; letter-spacing: 0.5px;">RELATÓRIO MENSAL DAS RECEITAS BRUTAS</h3>
                                
                                <p style="margin: 4px 0;"><strong>CNPJ:</strong> {cnpj_cliente}</p>
                                <p style="margin: 4px 0;"><strong>Empreendedor Individual:</strong> {nome_cliente}</p>
                                <p style="margin: 4px 0;"><strong>Período de Apuração:</strong> {mes_selecionado}</p>
                                
                                <table style="width: 100%; border-collapse: collapse; margin-top: 14px; font-size: 11px;">
                                    <tr>
                                        <td colspan="2" style="background-color: #f1f5f9; border: 1px solid #333; padding: 6px; font-weight: bold; text-align: center;">RECEITA BRUTA MENSAL - REVENDA DE MERCADORIAS (COMÉRCIO)</td>
                                    </tr>
                                    <tr>
                                        <td style="border: 1px solid #333; padding: 5px; width: 75%;">I - Revenda de mercadorias com dispensa de emissão de documento fiscal</td>
                                        <td style="border: 1px solid #333; padding: 5px; text-align: right;">{formatar_brl(v_I)}</td>
                                    </tr>
                                    <tr>
                                        <td style="border: 1px solid #333; padding: 5px;">II - Revenda de mercadorias com documento fiscal emitido</td>
                                        <td style="border: 1px solid #333; padding: 5px; text-align: right;">{formatar_brl(v_II)}</td>
                                    </tr>
                                    <tr>
                                        <td style="border: 1px solid #333; padding: 5px; font-weight: bold;">III - Total das receitas com revenda de mercadorias (I + II)</td>
                                        <td style="border: 1px solid #333; padding: 5px; text-align: right; font-weight: bold;">{formatar_brl(v_III)}</td>
                                    </tr>
                                    
                                    <tr>
                                        <td colspan="2" style="background-color: #f1f5f9; border: 1px solid #333; padding: 6px; font-weight: bold; text-align: center;">RECEITA BRUTA MENSAL - VENDA DE PRODUTOS INDUSTRIALIZADOS (INDÚSTRIA)</td>
                                    </tr>
                                    <tr>
                                        <td style="border: 1px solid #333; padding: 5px;">IV - Venda de produtos industrializados com dispensa de documento fiscal</td>
                                        <td style="border: 1px solid #333; padding: 5px; text-align: right;">{formatar_brl(v_IV)}</td>
                                    </tr>
                                    <tr>
                                        <td style="border: 1px solid #333; padding: 5px;">V - Venda de produtos industrializados com documento fiscal emitido</td>
                                        <td style="border: 1px solid #333; padding: 5px; text-align: right;">{formatar_brl(v_V)}</td>
                                    </tr>
                                    <tr>
                                        <td style="border: 1px solid #333; padding: 5px; font-weight: bold;">VI - Total das receitas com produtos industrializados (IV + V)</td>
                                        <td style="border: 1px solid #333; padding: 5px; text-align: right; font-weight: bold;">{formatar_brl(v_VI)}</td>
                                    </tr>

                                    <tr>
                                        <td colspan="2" style="background-color: #f1f5f9; border: 1px solid #333; padding: 6px; font-weight: bold; text-align: center;">RECEITA BRUTA MENSAL - PRESTAÇÃO DE SERVIÇOS</td>
                                    </tr>
                                    <tr>
                                        <td style="border: 1px solid #333; padding: 5px;">VII - Prestação de serviços com dispensa de emissão de documento fiscal</td>
                                        <td style="border: 1px solid #333; padding: 5px; text-align: right;">{formatar_brl(v_VII)}</td>
                                    </tr>
                                    <tr>
                                        <td style="border: 1px solid #333; padding: 5px;">VIII - Prestação de serviços com documento fiscal emitido</td>
                                        <td style="border: 1px solid #333; padding: 5px; text-align: right;">{formatar_brl(v_VIII)}</td>
                                    </tr>
                                    <tr>
                                        <td style="border: 1px solid #333; padding: 5px; font-weight: bold;">IX - Total das receitas com prestação de serviços (VII + VIII)</td>
                                        <td style="border: 1px solid #333; padding: 5px; text-align: right; font-weight: bold;">{formatar_brl(v_IX)}</td>
                                    </tr>

                                    <tr>
                                        <td style="border: 1px solid #333; padding: 7px; font-weight: bold; text-align: right; background-color: #e2e8f0;">X - Total geral das receitas brutas no mês (III + VI + IX)</td>
                                        <td style="border: 1px solid #333; padding: 7px; text-align: right; font-weight: bold; background-color: #e2e8f0;">{formatar_brl(v_X)}</td>
                                    </tr>
                                </table>
                                
                                <div style="margin-top: 32px;">
                                    <p style="margin: 4px 0;"><strong>LOCAL E DATA:</strong> ______________________________, ____/____/________</p>
                                    <div style="margin-top: 26px; text-align: center; width: 320px;">
                                        <hr style="border: 0; border-top: 1px solid #000; margin-bottom: 4px;">
                                        <p style="margin: 0; font-size: 11px;">ASSINATURA DO EMPRESÁRIO</p>
                                    </div>
                                </div>

                                <div style="margin-top: 24px; border: 1px solid #333; padding: 8px 12px; font-size: 10px; background: #fafafa;">
                                    <p style="margin: 0 0 4px 0; font-weight: bold;">ENCONTRAM-SE ANEXADOS A ESTE RELATÓRIO:</p>
                                    <ul style="margin: 0; padding-left: 18px;">
                                        <li>Os documentos fiscais comprobatórios das entradas de mercadorias e serviços tomados referentes ao período;</li>
                                        <li>As notas fiscais relativas às operações ou prestações realizadas eventualmente emitidas.</li>
                                    </ul>
                                </div>
                            </div>
                        </body>
                        </html>
                        """
                        st.components.v1.html(html_relatorio, height=680, scrolling=True)

                # --------------------------------------------------------------
                # ABA 3: DECLARAÇÃO ANUAL MEI (DASN-SIMEI) - PROTEGIDA POR PLANO
                # --------------------------------------------------------------
                with tab_anual:
                    st.markdown("##### Preparação para a Declaração Anual (DASN-SIMEI)")
                    st.caption("Resumo anual do faturamento consolidado por atividade econômica.")

                    # Blindagem efetiva do Paywall
                    if not regras.get('dasn_simei', False):
                        exibir_bloqueio_upgrade("Declaração Anual Consolidada (DASN-SIMEI)", plano_minimo="pro")
                    else:
                        df_anual = df_lancamentos.copy()
                        df_anual['data_dt'] = pd.to_datetime(df_anual['data'], errors='coerce')
                        df_anual = df_anual.dropna(subset=['data_dt'])
                        df_anual['ano_cod'] = df_anual['data_dt'].dt.strftime('%Y')

                        anos_disponiveis = sorted(df_anual['ano_cod'].unique(), reverse=True)

                        if not anos_disponiveis:
                            st.info("Nenhum lançamento válido encontrado para apuração anual.")
                        else:
                            ano_selecionado = st.selectbox("Selecione o Ano-Calendário para Apuração:", anos_disponiveis, key="sb_ano_dasn")

                            df_ano = df_anual[
                                (df_anual['ano_cod'] == ano_selecionado) & 
                                (df_anual['conta_credito'].str.contains('^3\.|^Receita', case=False, na=False, regex=True))
                            ]

                            v_comercio_industria = 0.0
                            v_servicos = 0.0

                            for _, row in df_ano.iterrows():
                                val = float(row['valor'])
                                conta = str(row['conta_credito']).lower()
                                hist = str(row['historico']).lower()

                                if "empréstimo" in conta or "emprestimo" in hist or "reembolso" in conta or "reembolso" in hist:
                                    continue

                                if "serviço" in conta or "servico" in conta:
                                    v_servicos += val
                                elif any(k in conta for k in ["indústria", "industria", "industrializado", "comércio", "comercio", "venda", "mercadoria"]):
                                    v_comercio_industria += val

                            v_total_ano = v_comercio_industria + v_servicos

                            st.markdown(f"###### Valores Consolidados — Exercício `{ano_selecionado}`")

                            col_a1, col_a2, col_a3 = st.columns(3)
                            
                            # 1. COMÉRCIO / INDÚSTRIA (AZUL NATIVO)
                            with col_a1:
                                st.info(
                                    f"{ICONES['empresa']} **Comércio / Indústria**\n\n"
                                    f"## **{formatar_brl(v_comercio_industria)}**"
                                )
                                st.caption("Receita de revenda e produtos")
                            # 2. PRESTAÇÃO DE SERVIÇOS (VERDE NATIVO)
                            with col_a2:
                                st.success(
                                    f"{ICONES['ferramentas']} **Prestação de Serviços**\n\n"
                                    f"## **{formatar_brl(v_servicos)}**"
                                )
                                st.caption("Receita exclusiva de serviços")

                            # 3. RECEITA BRUTA TOTAL (AMARELO / DOURADO NATIVO)
                            with col_a3:
                                st.warning(
                                    f"{ICONES['receita_federal']} **Receita Bruta Total**\n\n"
                                    f"## **{formatar_brl(v_total_ano)}**"
                                )
                                st.caption("Soma de todas as atividades")

                            st.divider()

                            col_btn1, col_btn2 = st.columns([2.5, 1.5], vertical_alignment="center")
                            with col_btn1:
                                st.markdown("**Transmitir Declaração:** Com os valores consolidados acima, acesse o portal oficial da Receita Federal:")
                            with col_btn2:
                                st.link_button(
                                    "🌐 Portal DASN-SIMEI (Receita)", 
                                    "https://www8.receita.fazenda.gov.br/SimplesNacional/Aplicacoes/ATSPO/dasnsimei.app/Identificacao", 
                                    type="primary", 
                                    use_container_width=True
                                )

                # --------------------------------------------------------------
                # ABA 4: BACKUP & MANUTENÇÃO (CARGA, EXPORTAÇÃO E RESET)
                # --------------------------------------------------------------
                with tab_manutencao:
                    st.markdown("##### Central de Manutenção e Gestão da Base de Lançamentos")
                    st.caption("Exporte backups completos, substitua dados em lote ou realize a limpeza dos registros deste cliente.")

                    col_exp, col_imp = st.columns(2)

                    # Coluna 1: Exportação & Limpeza
                    with col_exp:
                        st.markdown("###### 1. Backup Completo e Limpeza")
                        
                        df_export_lanc = carregar_lancamentos(cliente_ativo_id)

                        if not df_export_lanc.empty:
                            csv_lanc = df_export_lanc.to_csv(index=False, sep=";", encoding="utf-8-sig")
                            from datetime import date
                            st.download_button(
                                label="📥 Baixar Backup Atual (.csv)",
                                data=csv_lanc,
                                file_name=f"backup_lancamentos_cli_{cliente_ativo_id}_{date.today().strftime('%Y%m%d')}.csv",
                                mime="text/csv",
                                use_container_width=True,
                                key="btn_download_backup_cli"
                            )
                        else:
                            st.info("Nenhum lançamento registrado para exportar.")

                        st.markdown("---")
                        st.markdown(f"**{ICONES.get('excluir', ':material/delete_forever:')} Exclusão em Bloco (Reset da Base)**")
                        st.caption("⚠️ Atenção: Esta ação removerá permanentemente TODOS os lançamentos deste cliente.")
                        
                        if st.button(
                            "Apagar TODOS os Lançamentos deste Cliente", 
                            type="secondary",
                            key="btn_apagar_todos_lancamentos"
                        ):
                            conn_del = get_connection()
                            try:
                                with conn_del.cursor() as cur:
                                    cur.execute("DELETE FROM lancamentos WHERE cliente_id = %s;", (cliente_ativo_id,))
                                conn_del.commit()
                                limpar_cache()
                                st.success("Base de lançamentos do cliente limpa com sucesso!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erro ao apagar lançamentos: {e}")
                            finally:
                                conn_del.close()

                    # Coluna 2: Carga e Substituição em Lote
                    with col_imp:
                        st.markdown("###### 2. Carga e Substituição de Dados")
                        st.caption("Substitui integralmente os lançamentos deste cliente pelos dados do arquivo enviado.")
                        
                        file_lanc = st.file_uploader(
                            "Selecione o arquivo de Lançamentos (.csv):", 
                            type=["csv"], 
                            key="up_lanc_substituicao"
                        )
                        
                        if file_lanc is not None:
                            if st.button(
                                "Confirmar Substituição Total dos Lançamentos", 
                                type="primary", 
                                use_container_width=True,
                                key="btn_confirmar_subst_lanc"
                            ):
                                with st.status("Processando e sincronizando lançamentos...") as status:
                                    try:
                                        import io

                                        file_bytes = file_lanc.getvalue()
                                        df_novos_lanc = None

                                        for enc in ['utf-8-sig', 'utf-8', 'cp1252', 'latin1', 'iso-8859-1']:
                                            try:
                                                df_temp = pd.read_csv(io.BytesIO(file_bytes), sep=";", encoding=enc)
                                                if len(df_temp.columns) >= 3:
                                                    df_novos_lanc = df_temp
                                                    break
                                            except Exception:
                                                continue

                                        if df_novos_lanc is None:
                                            status.update(label="Falha na leitura do arquivo CSV.", state="error")
                                            st.error("Não foi possível ler o arquivo. Certifique-se de que o delimitador seja ponto e vírgula (;).")
                                            st.stop()

                                        def limpar_texto(txt):
                                            if not isinstance(txt, str):
                                                return str(txt)
                                            try:
                                                if 'Ã' in txt or 'Â' in txt:
                                                    return txt.encode('latin1').decode('utf-8')
                                            except Exception:
                                                pass
                                            return txt

                                        conn_sub = get_connection()
                                        try:
                                            with conn_sub.cursor() as cur:
                                                # Limpa lançamentos anteriores
                                                cur.execute("DELETE FROM lancamentos WHERE cliente_id = %s;", (cliente_ativo_id,))

                                                for _, row in df_novos_lanc.iterrows():
                                                    hist_raw = str(row.get('historico', row.get('descricao', '')))
                                                    hist_val = limpar_texto(hist_raw)

                                                    raw_date = str(row['data']).strip()
                                                    dt_parsed = pd.to_datetime(raw_date, dayfirst=True, errors='coerce')
                                                    data_final = dt_parsed.strftime('%Y-%m-%d') if pd.notnull(dt_parsed) else raw_date

                                                    val_raw = str(row['valor']).replace('R$', '').strip()
                                                    if ',' in val_raw and '.' in val_raw:
                                                        val_raw = val_raw.replace('.', '').replace(',', '.')
                                                    elif ',' in val_raw:
                                                        val_raw = val_raw.replace(',', '.')
                                                    valor_final = float(val_raw)

                                                    c_cred = limpar_texto(str(row.get('conta_credito', '')))
                                                    c_deb = limpar_texto(str(row.get('conta_debito', '')))

                                                    cur.execute(
                                                        """
                                                        INSERT INTO lancamentos (cliente_id, data, historico, valor, conta_debito, conta_credito)
                                                        VALUES (%s, %s, %s, %s, %s, %s)
                                                        """,
                                                        (cliente_ativo_id, data_final, hist_val, valor_final, c_deb, c_cred)
                                                    )
                                            conn_sub.commit()
                                            limpar_cache()
                                            status.update(label="Carga concluída com sucesso!", state="complete")
                                            st.success(f"{len(df_novos_lanc)} lançamentos substituídos com sucesso!")
                                            st.rerun()
                                        except Exception as e:
                                            conn_sub.rollback()
                                            status.update(label="Erro durante a gravação.", state="error")
                                            st.error(f"Erro ao gravar novos dados: {e}")
                                        finally:
                                            conn_sub.close()

                                    except Exception as e:
                                        st.error(f"Erro geral no processamento: {e}")

# Fim do arquivo 1_Gestor_Contabil.py
exibir_rodape_institucional(versao="v1.0.2-beta", status_servico="Supabase Conectado")

