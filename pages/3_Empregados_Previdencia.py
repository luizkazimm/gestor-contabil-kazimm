import sys
from pathlib import Path

# Garante a localização da raiz no Windows e Linux
RAIZ_PROJETO = Path(__file__).resolve().parent.parent
if str(RAIZ_PROJETO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROJETO))

import streamlit as st
import pandas as pd
from datetime import datetime, date
from database import get_connection

# Importa estritamente o que já existe no seu ui_theme.py oficial
from ui_theme import (
    aplicar_tema_global, 
    exibir_cabecalho, 
    exibir_banner_cliente_ativo,
    exibir_botoes_modulos_navegacao,
    exibir_rodape_institucional, 
    ICONES
)

# -----------------------------------------------------------------------------
# 1. FUNÇÕES AUXILIARES LOCAIS
# -----------------------------------------------------------------------------
def formatar_brl(valor):
    try:
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return "R$ 0,00"

def limpar_cache():
    st.cache_data.clear()

# -----------------------------------------------------------------------------
# 2. CONFIGURAÇÃO E TEMA GLOBAL
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Empregados & Previdência | Kazimm ERP", layout="wide")
aplicar_tema_global()

REGRAS_PLANOS = {
    'gratis': {'folha_pagamento': False, 'nome': 'Plano MEI Gratuito'},
    'pro': {'folha_pagamento': True, 'nome': 'Plano MEI Pro'},
    'contador': {'folha_pagamento': True, 'nome': 'Plano Escritório / Contador'}
}

def exibir_bloqueio_upgrade(nome_recurso: str):
    st.warning("🔒 **Recurso Exclusivo do Plano Pro**")
    st.markdown(
        f"""
        <div style="background-color: #f8f9fa; border: 1px solid #e9ecef; border-radius: 8px; padding: 25px; margin: 15px 0;">
            <h4 style="color: #1e293b; margin-top: 0;">Desbloqueie o módulo de <strong>{nome_recurso}</strong></h4>
            <p style="color: #64748b; font-size: 14px; line-height: 1.5;">
                A gestão de funcionários, simulação da Guia DAE, férias e emissão do holerite oficial são recursos do <strong>Plano MEI Pro</strong>.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.link_button(
    label="⭐ Fazer Upgrade Agora",
    url="https://www.asaas.com/000/c/serwm0gti8wzfqe7",
    type="primary",
    use_container_width=False
)

# -----------------------------------------------------------------------------
# 3. VALIDAÇÃO DE SESSÃO E CLIENTE ATIVO
# -----------------------------------------------------------------------------
if 'user' not in st.session_state or st.session_state.user is None:
    st.warning("⚠️ Você precisa fazer login para acessar este módulo.")
    st.stop()

cliente_ativo_id = st.session_state.get("cliente_id_ativo")
if not cliente_ativo_id:
    st.warning(f"{ICONES['alerta']} Selecione um cliente ativo no Gestor Contábil antes de gerenciar a folha de pagamento.")
    st.stop()

# Carregamento dos dados cadastrais do cliente
conn = get_connection()
try:
    df_cli = pd.read_sql_query(
        "SELECT id, nome, regime, COALESCE(plano, 'gratis') AS plano FROM clientes WHERE id = %s",
        conn, params=(cliente_ativo_id,)
    )
finally:
    conn.close()

if df_cli.empty:
    st.error("Cliente não localizado.")
    st.stop()

nome_cliente = df_cli.iloc[0]["nome"]
regime_cliente = df_cli.iloc[0]["regime"] or "MEI (Microempreendedor Individual)"
plano_cliente = str(df_cli.iloc[0]["plano"]).lower()
plano_rotulo = REGRAS_PLANOS.get(plano_cliente, {}).get("nome", "Plano MEI Pro")

# -----------------------------------------------------------------------------
# 4. CABEÇALHO OFICIAL & SANFONA COM COMPONENTES NATIVOS DO UI_THEME
# -----------------------------------------------------------------------------
exibir_cabecalho(
    titulo="Empregados / Folha",
    subtitulo="DEPARTAMENTO PESSOAL & BENEFÍCIOS",
    versao="v1.0.2-beta"
)

# Sanfona nativa montada com os blocos que já existem no ui_theme.py
with st.expander("👤 Painel de Contexto e Módulos do Sistema", expanded=True):
    exibir_banner_cliente_ativo(
        nome_cliente=nome_cliente,
        regime=regime_cliente,
        plano=plano_rotulo
    )
    exibir_botoes_modulos_navegacao(modulo_atual="previdencia")

# Trava Freemium
if not REGRAS_PLANOS.get(plano_cliente, {}).get("folha_pagamento", False):
    exibir_bloqueio_upgrade("Gestão de Empregado e Encargos MEI")
    st.stop()

# -----------------------------------------------------------------------------
# 5. NAVEGAÇÃO LATERAL (5 BOTÕES OPERACIONAIS)
# -----------------------------------------------------------------------------
st.sidebar.markdown(f"### {ICONES['cliente']} Gestão de Pessoal")

opcoes_menu = [
    f"{ICONES['cliente']} Admissão",
    f"{ICONES['planilhas']} Tabelas",
    f"{ICONES['agenda']} Férias",
    f"{ICONES['reciclagem']} Vale Transporte",
    f"{ICONES['fiscal']} Folha de Pagamento"
]

opcao_selecionada = st.sidebar.radio("Selecione a Operação:", opcoes_menu)

# Carrega empregados do cliente ativo
conn = get_connection()
try:
    df_emp = pd.read_sql_query(
        "SELECT * FROM empregados WHERE cliente_id = %s ORDER BY id DESC",
        conn, params=(cliente_ativo_id,)
    )
finally:
    conn.close()

emp_ativo = df_emp[df_emp["status"] == "Ativo"] if not df_emp.empty else pd.DataFrame()

# -----------------------------------------------------------------------------
# 6. CONTAINER OPERACIONAL ROLÁVEL (580PX)
# -----------------------------------------------------------------------------
with st.container(height=580, border=True):

    # =========================================================================
    # 1. ADMISSÃO: DADOS CADASTRAIS DO EMPREGADO
    # =========================================================================
    if "Admissão" in opcao_selecionada:
        st.markdown(f"#### {ICONES['cliente']} Ficha Cadastral e Admissão de Empregado")
        
        tab_cad_ativo, tab_cad_novo = st.tabs([
            f"{ICONES['cliente']} Colaborador Ativo",
            f"{ICONES['adicionar']} Nova Admissão"
        ])

        with tab_cad_ativo:
            if emp_ativo.empty:
                st.info("ℹ️ Nenhum empregado ativo registrado para este cliente.")
            else:
                dados = emp_ativo.iloc[0]
                st.success(f"**Colaborador Ativo:** {dados['nome']}")
                
                c1, c2, c3, c4 = st.columns(4)
                salario_base = float(dados['salario_base'])
                c1.metric("Salário Base", formatar_brl(salario_base))
                c2.metric("Função / Cargo", dados['cargo'])
                c3.metric("CPF", dados['cpf'])
                data_adm_br = pd.to_datetime(dados['data_admissao']).strftime('%d/%m/%Y')
                c4.metric("Data de Admissão", data_adm_br)

                st.divider()

                with st.expander(f"{ICONES['alerta']} Encerramento Contratual / Rescisão"):
                    st.warning("Pela legislação, o MEI pode possuir apenas 1 funcionário ativo simultaneamente.")
                    if st.button("Marcar como Inativo / Rescindido", type="secondary", key="btn_rescindir_emp"):
                        conn_res = get_connection()
                        try:
                            with conn_res.cursor() as cur:
                                cur.execute("UPDATE empregados SET status = 'Inativo' WHERE id = %s", (int(dados['id']),))
                            conn_res.commit()
                            limpar_cache()
                            st.success("Contrato encerrado. O colaborador foi marcado como Inativo.")
                            st.rerun()
                        finally:
                            conn_res.close()

        with tab_cad_novo:
            if not emp_ativo.empty:
                st.warning("⚠️ **Limite Legal Atingido:** O MEI só pode ter 1 empregado ativo. Para registrar outro, encerre o contrato vigente na aba ao lado.")
            else:
                with st.form("form_novo_empregado_slim", clear_on_submit=True):
                    st.markdown("##### Formulário de Admissão (eSocial MEI)")
                    col_c1, col_c2 = st.columns(2)
                    nome_colab = col_c1.text_input("Nome Completo do Empregado")
                    cpf_colab = col_c2.text_input("CPF (Apenas números)", max_chars=14)

                    col_c3, col_c4 = st.columns(2)
                    cargo_colab = col_c3.text_input("Função / Cargo", placeholder="Ex: Auxiliar de Loja")
                    salario_colab = col_c4.number_input("Salário Base Contratual (R$)", min_value=1412.00, value=1518.00, step=50.0)

                    data_adm = st.date_input("Data de Admissão", value=date.today())

                    btn_admitir = st.form_submit_button(
                        "Registrar Admissão", 
                        type="primary", 
                        icon=ICONES["adicionar"],
                        use_container_width=True
                    )

                    if btn_admitir:
                        if not nome_colab or not cpf_colab or not cargo_colab:
                            st.error("Preencha todos os campos obrigatórios.")
                        else:
                            conn_adm = get_connection()
                            try:
                                with conn_adm.cursor() as cur:
                                    cur.execute(
                                        """
                                        INSERT INTO empregados (cliente_id, nome, cpf, cargo, salario_base, data_admissao, status)
                                        VALUES (%s, %s, %s, %s, %s, %s, 'Ativo')
                                        """,
                                        (cliente_ativo_id, nome_colab.strip(), cpf_colab.strip(), cargo_colab.strip(), salario_colab, data_adm)
                                    )
                                conn_adm.commit()
                                limpar_cache()
                                st.success("Colaborador admitido com sucesso!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erro ao cadastrar empregado: {e}")
                            finally:
                                conn_adm.close()

    # =========================================================================
    # 2. TABELAS: VALORES SALARIAIS E OBRIGAÇÕES (INSS/FGTS/PATRONAL)
    # =========================================================================
    elif "Tabelas" in opcao_selecionada:
        st.markdown(f"#### {ICONES['planilhas']} Parâmetros Salariais e Encargos da Guia DAE")
        st.caption("Alíquotas oficiais aplicáveis à folha de pagamento no regime MEI.")

        salario_base_vigente = float(emp_ativo.iloc[0]['salario_base']) if not emp_ativo.empty else 1518.00

        col_s1, col_s2 = st.columns([1.5, 2], vertical_alignment="center")
        with col_s1:
            salario_ref = st.number_input("Salário Base de Apuração (R$):", min_value=1412.00, value=salario_base_vigente, step=50.0)
        with col_s2:
            st.info(f"Colaborador de Referência: **{emp_ativo.iloc[0]['nome'] if not emp_ativo.empty else 'Base Padrão (Sem empregado ativo)'}**")

        # Cálculos oficiais
        desc_inss_func = salario_ref * 0.075
        inss_patronal = salario_ref * 0.03
        fgts_empresa = salario_ref * 0.08
        total_guia_dae = desc_inss_func + inss_patronal + fgts_empresa

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("INSS Retido (7,5%)", formatar_brl(desc_inss_func))
        m2.metric("INSS Patronal (3,0%)", formatar_brl(inss_patronal))
        m3.metric("FGTS Mensal (8,0%)", formatar_brl(fgts_empresa))
        m4.metric("Guia DAE Única", formatar_brl(total_guia_dae))

        st.markdown("##### Composição Discriminada da Guia do eSocial")
        df_obrigacoes = pd.DataFrame([
            {"Obrigação / Encargo": "INSS Empregado (Retenção)", "Alíquota": "7,50%", "Responsável": "Descontado do Trabalhador", "Impacto": "Dedução do Salário", "Valor (R$)": formatar_brl(desc_inss_func)},
            {"Obrigação / Encargo": "INSS Patronal Previdenciário", "Alíquota": "3,00%", "Responsável": "Custo do Empregador", "Impacto": "Despesa do MEI", "Valor (R$)": formatar_brl(inss_patronal)},
            {"Obrigação / Encargo": "FGTS Mensal", "Alíquota": "8,00%", "Responsável": "Custo do Empregador", "Impacto": "Depósito em Conta Vinculada", "Valor (R$)": formatar_brl(fgts_empresa)},
            {"Obrigação / Encargo": "Total da Guia Única DAE", "Alíquota": "18,50%", "Responsável": "Documento de Arrecadação", "Impacto": "Recolhimento Mensal", "Valor (R$)": formatar_brl(total_guia_dae)}
        ])
        st.dataframe(df_obrigacoes, hide_index=True, use_container_width=True)

    # =========================================================================
    # 3. FÉRIAS: CÁLCULO E ABONO PECUNIÁRIO
    # =========================================================================
    elif "Férias" in opcao_selecionada:
        st.markdown(f"#### {ICONES['agenda']} Simulador e Cálculo de Férias Regulamentares")

        if emp_ativo.empty:
            st.info("Nenhum empregado ativo cadastrado para realizar o cálculo de férias.")
        else:
            dados = emp_ativo.iloc[0]
            salario_base = float(dados['salario_base'])

            st.write(f"Colaborador: **{dados['nome']}** | Salário Base: **{formatar_brl(salario_base)}**")

            col_fer1, col_fer2 = st.columns(2)
            with col_fer1:
                dias_descanso = st.slider("Dias Totais de Descanso:", min_value=10, max_value=30, value=30, step=5)
            with col_fer2:
                vender_abono = st.checkbox("Converter 10 dias em dinheiro (Abono Pecuniário)?", value=False)
                adiantar_13 = st.checkbox("Adiantar 50% do 13º Salário nas Férias?", value=False)

            dias_gozo = (dias_descanso - 10) if vender_abono else dias_descanso
            remun_diaria = salario_base / 30.0

            valor_gozo = remun_diaria * dias_gozo
            terco_gozo = valor_gozo / 3.0
            
            valor_abono = (remun_diaria * 10.0) if vender_abono else 0.0
            terco_abono = (valor_abono / 3.0) if vender_abono else 0.0
            adiantamento_13_val = (salario_base * 0.5) if adiantar_13 else 0.0

            total_bruto_ferias = valor_gozo + terco_gozo + valor_abono + terco_abono + adiantamento_13_val

            st.divider()
            f1, f2, f3, f4 = st.columns(4)
            f1.metric("Dias de Descanso", f"{dias_gozo} dias")
            f2.metric("Remuneração + 1/3", formatar_brl(valor_gozo + terco_gozo))
            f3.metric("Abono Pecuniário", formatar_brl(valor_abono + terco_abono) if vender_abono else "R$ 0,00")
            f4.metric("Total Bruto a Receber", formatar_brl(total_bruto_ferias))

    # =========================================================================
    # 4. VALE TRANSPORTE: DESCONTO EM FOLHA & COMPRA
    # =========================================================================
    elif "Vale Transporte" in opcao_selecionada:
        st.markdown(f"#### {ICONES['reciclagem']} Apuração de Vale Transporte (Desconto e Custo)")

        if emp_ativo.empty:
            st.info("Nenhum empregado ativo cadastrado para apurar os cálculos de transporte.")
        else:
            dados = emp_ativo.iloc[0]
            salario_base = float(dados['salario_base'])

            col_vt1, col_vt2, col_vt3 = st.columns(3)
            with col_vt1:
                dias_uteis = st.number_input("Dias Úteis Previstos no Mês:", min_value=1, max_value=31, value=22)
            with col_vt2:
                gasto_diario = st.number_input("Gasto Diário Total com Passagens (R$):", min_value=1.0, value=10.0, step=0.5)
            with col_vt3:
                st.write(f"**Salário Contratual:** {formatar_brl(salario_base)}")

            custo_total_compra = dias_uteis * gasto_diario
            teto_desconto_6 = salario_base * 0.06
            desconto_folha = min(custo_total_compra, teto_desconto_6)
            custo_liquido_empresa = custo_total_compra - desconto_folha

            st.divider()
            vt1, vt2, vt3 = st.columns(3)
            vt1.metric("Custo de Compra (Passagens)", formatar_brl(custo_total_compra), help="Valor a ser adquirido em créditos/cartões de transporte.")
            vt2.metric("Desconto em Folha (Teto 6%)", formatar_brl(desconto_folha), help="Valor descontado no holerite do colaborador.")
            vt3.metric("Custo Final para o MEI", formatar_brl(custo_liquido_empresa), help="Parcela subsidiada pelo empregador.")

    # =========================================================================
    # 5. FOLHA DE PAGAMENTO & RECIBOS (EMPRESA & COLABORADOR)
    # =========================================================================
    elif "Folha de Pagamento" in opcao_selecionada:
        st.markdown(f"#### {ICONES['fiscal']} Central da Folha de Pagamento e Fechamento Mensal")

        if emp_ativo.empty:
            st.info("Cadastre um empregado ativo para gerar folhas e recibos de pagamento.")
        else:
            dados = emp_ativo.iloc[0]
            salario_base = float(dados['salario_base'])

            # Navegação em abas: Gestão da Empresa vs. Recibo do Trabalhador
            tab_folha_empresa, tab_recibo = st.tabs([
                f"{ICONES['planilhas']} Folha Consolidada da Empresa (Gerencial)",
                f"{ICONES['relatorios']} Recibo de Pagamento (Holerite 2 Vias)"
            ])

            # -----------------------------------------------------------------
            # ABA 1: FOLHA GERENCIAL DA EMPRESA (CONTROLE DE CUSTOS DO MEI)
            # -----------------------------------------------------------------
            with tab_folha_empresa:
                st.markdown("##### Resumo Mensal de Desembolso da Empresa")
                st.caption("Controle consolidado de proventos, retenções, encargos da Guia DAE e custo total da folha.")

                # Seleção de competência e variáveis do mês
                col_c1, col_c2, col_c3 = st.columns([1.2, 1, 1])
                with col_c1:
                    mes_comp = st.date_input("Competência / Mês:", value=date.today(), key="dp_folha_comp")
                    str_comp = mes_comp.strftime("%m/%Y")
                with col_c2:
                    horas_extras = st.number_input("Adicionais / Horas Extras (R$):", min_value=0.00, value=0.00, step=20.0, format="%.2f", key="num_he_folha")
                with col_c3:
                    outros_descontos = st.number_input("Outros Descontos / Faltas (R$):", min_value=0.00, value=0.00, step=20.0, format="%.2f", key="num_desc_folha")

                # Memória de cálculo da folha
                total_proventos = salario_base + horas_extras
                desc_inss_emp = total_proventos * 0.075
                total_descontos = desc_inss_emp + outros_descontos
                liquido_a_pagar = total_proventos - total_descontos

                # Encargos patronais MEI (recolhidos na Guia DAE do eSocial)
                inss_patronal = total_proventos * 0.03
                fgts_empresa = total_proventos * 0.08
                total_guia_dae = desc_inss_emp + inss_patronal + fgts_empresa
                custo_total_folha = liquido_a_pagar + total_guia_dae

                # Cartões de Visão Rápida para o Empreendedor
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Total Proventos", formatar_brl(total_proventos))
                m2.metric("Total Retenções", formatar_brl(total_descontos))
                m3.metric("Líquido a Pagar (Colaborador)", formatar_brl(liquido_a_pagar))
                m4.metric("Custo Efetivo Total MEI", formatar_brl(custo_total_folha))

                st.markdown("##### Espelho Discriminado da Folha de Pagamento")

                # Tabela detalhada por rubricas
                linhas_folha = [
                    {"Classificação": "Provento (+)", "Rubrica": "Salário Base Contratual", "Referência": "30 Dias", "Valor": formatar_brl(salario_base)},
                    {"Classificação": "Provento (+)", "Rubrica": "Adicionais / Horas Extras", "Referência": "-", "Valor": formatar_brl(horas_extras)},
                    {"Classificação": "Desconto (-)", "Rubrica": "INSS Retido do Empregado", "Referência": "7,50%", "Valor": formatar_brl(desc_inss_emp)},
                    {"Classificação": "Desconto (-)", "Rubrica": "Outras Deduções / Faltas", "Referência": "-", "Valor": formatar_brl(outros_descontos)},
                    {"Classificação": "Líquido (=)", "Rubrica": "Salário Líquido a Transferir", "Referência": "Conta Bancária", "Valor": formatar_brl(liquido_a_pagar)},
                    {"Classificação": "Encargo Patronal", "Rubrica": "INSS Patronal Previdenciário", "Referência": "3,00%", "Valor": formatar_brl(inss_patronal)},
                    {"Classificação": "Encargo Patronal", "Rubrica": "FGTS Mensal (Conta Vinculada)", "Referência": "8,00%", "Valor": formatar_brl(fgts_empresa)},
                    {"Classificação": "Guia Fiscal", "Rubrica": "Guia DAE eSocial (INSS + FGTS)", "Referência": "Documento Único", "Valor": formatar_brl(total_guia_dae)},
                ]
                df_folha_view = pd.DataFrame(linhas_folha)
                st.dataframe(df_folha_view, hide_index=True, use_container_width=True, height=270)

                # Exportação e Impressão do Espelho da Empresa
                col_exp1, col_exp2 = st.columns([1.2, 3], vertical_alignment="center")
                with col_exp1:
                    csv_folha = df_folha_view.to_csv(index=False, sep=";", encoding="utf-8-sig").encode("utf-8-sig")
                    st.download_button(
                        label="Exportar Folha (.csv)",
                        data=csv_folha,
                        file_name=f"folha_empresa_{str_comp.replace('/', '_')}_{dados['nome'].replace(' ', '_')}.csv",
                        mime="text/csv",
                        icon=ICONES["exportar"],
                        use_container_width=True,
                        key="btn_down_folha_empresa"
                    )
                with col_exp2:
                    st.caption("ℹ️ Utilize este espelho mensal para conciliação contábil e auditoria dos valores recolhidos no portal do eSocial.")

            # -----------------------------------------------------------------
            # ABA 2: RECIBO DO COLABORADOR (HOLERITE 2 VIAS A4)
            # -----------------------------------------------------------------
            with tab_recibo:
                col_r1, col_r2 = st.columns([1.2, 2], vertical_alignment="bottom")
                with col_r1:
                    mes_ref_h = st.date_input("Mês de Competência do Recibo:", value=date.today(), key="dp_recibo_comp")
                    str_mes_ref = mes_ref_h.strftime("%m/%Y")
                with col_r2:
                    btn_recibo = st.button("Gerar Recibo Oficial (2 Vias A4)", type="primary", icon=ICONES["relatorios"], key="btn_emitir_recibo")

                if btn_recibo:
                    inss_retido_rec = salario_base * 0.075
                    salario_liquido_rec = salario_base - inss_retido_rec

                    def gerar_via(titulo_via):
                        return f"""
                        <div style="border: 1px solid #333; padding: 10px; font-family: Arial, sans-serif; background-color: #fff; color: #000; border-radius: 4px; margin-bottom: 8px;">
                            <h4 style="text-align: center; margin: 2px 0; font-size: 13px;">RECIBO DE PAGAMENTO DE SALÁRIO</h4>
                            <p style="text-align: center; margin: 2px 0 6px 0; font-size: 10px;">Referência: <strong>{str_mes_ref}</strong> &nbsp;|&nbsp; <strong>Via do {titulo_via}</strong></p>
                            <div style="border-bottom: 1px solid #333; margin-bottom: 6px; padding-bottom: 4px; font-size: 10.5px;">
                                <strong>Empregador:</strong> {nome_cliente}<br>
                                <strong>Empregado:</strong> {dados['nome']} - <strong>CPF:</strong> {dados['cpf']}<br>
                                <strong>Cargo:</strong> {dados['cargo']}
                            </div>
                            <table style="width: 100%; border-collapse: collapse; font-size: 10px;">
                                <tr style="background: #f1f5f9; border-bottom: 1px solid #333;">
                                    <th style="text-align: left; padding: 3px;">Descrição</th>
                                    <th style="text-align: right; padding: 3px;">Proventos (R$)</th>
                                    <th style="text-align: right; padding: 3px;">Descontos (R$)</th>
                                </tr>
                                <tr>
                                    <td style="padding: 3px;">Salário Base Mensal</td>
                                    <td style="text-align: right; padding: 3px;">{formatar_brl(salario_base).replace('R$ ', '')}</td>
                                    <td style="text-align: right; padding: 3px;">-</td>
                                </tr>
                                <tr>
                                    <td style="padding: 3px;">INSS Retido em Folha (7,5%)</td>
                                    <td style="text-align: right; padding: 3px;">-</td>
                                    <td style="text-align: right; padding: 3px;">{formatar_brl(inss_retido_rec).replace('R$ ', '')}</td>
                                </tr>
                                <tr style="border-top: 1px solid #000; font-weight: bold;">
                                    <td style="padding: 3px;">TOTAIS</td>
                                    <td style="text-align: right; padding: 3px;">{formatar_brl(salario_base).replace('R$ ', '')}</td>
                                    <td style="text-align: right; padding: 3px;">{formatar_brl(inss_retido_rec).replace('R$ ', '')}</td>
                                </tr>
                            </table>
                            <div style="border: 1px solid #000; padding: 4px; background-color: #f8fafc; text-align: center; font-size: 12px; margin-top: 6px;">
                                LÍQUIDO A RECEBER: <strong>{formatar_brl(salario_liquido_rec)}</strong>
                            </div>
                            <p style="margin: 6px 0 2px 0; font-size: 8.5px; text-align: justify;">
                                Declaro ter recebido a importância líquida descrita acima referente à quitação do meu salário no período de referência indicado.
                            </p>
                            <div style="margin-top: 14px; text-align: center; font-size: 10px;">
                                ________________________________________________________<br>
                                <strong>{dados['nome']}</strong><br>
                                Data: ___/___/______
                            </div>
                        </div>
                        """

                    html_documento = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="utf-8">
                        <title>Holerite_{str_mes_ref.replace('/', '_')}</title>
                        <style>
                            @page {{ size: A4 portrait; margin: 8mm 10mm; }}
                            @media print {{
                                body {{ margin: 0; padding: 0; background: #fff; }}
                                .no-print {{ display: none !important; }}
                                #holerite-container {{ width: 100% !important; border: none !important; }}
                            }}
                            body {{ font-family: Arial, sans-serif; margin: 0; padding: 6px; }}
                            .btn-print-box {{ display: flex; justify-content: flex-end; margin-bottom: 10px; }}
                            .btn-print {{ background-color: #0F172A; color: #fff; border: none; padding: 8px 16px; border-radius: 6px; font-weight: bold; cursor: pointer; }}
                        </style>
                    </head>
                    <body>
                        <div class="no-print btn-print-box">
                            <button class="btn-print" onclick="window.print()">🖨️ Imprimir Recibo (2 Vias A4 Retrato)</button>
                        </div>
                        <div id="holerite-container" style="max-width: 760px; margin: 0 auto;">
                            {gerar_via("EMPREGADOR")}
                            <div style="border-top: 1px dashed #666; margin: 10px 0; text-align: center; font-size: 10px; color: #666;">
                                ✂️ Corte nesta linha pontilhada ✂️
                            </div>
                            {gerar_via("EMPREGADO")}
                        </div>
                    </body>
                    </html>
                    """
                    st.components.v1.html(html_documento, height=520, scrolling=True)

# -----------------------------------------------------------------------------
# 7. RODAPÉ INSTITUCIONAL NATIVO
# -----------------------------------------------------------------------------
exibir_rodape_institucional(versao="v1.0.2-beta", status_servico="Supabase Conectado")