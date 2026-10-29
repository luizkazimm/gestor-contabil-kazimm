import streamlit as st
import pandas as pd
from datetime import datetime, date
from database import get_connection
from ui_theme import aplicar_tema_global, exibir_cabecalho, exibir_menu_modulos_topo

# -----------------------------------------------------------------------------
# 1. FUNÇÕES AUXILIARES E REGRAS DE ACESSO
# -----------------------------------------------------------------------------
def formatar_brl(valor):
    try:
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return "R$ 0,00"

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
                A gestão de funcionários, simulação da Guia DAE e cálculo automático de encargos (INSS e FGTS) são recursos do <strong>Plano MEI Pro</strong>.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.link_button("⭐ Fazer Upgrade Agora", "https://asaas.com/c/seu-link-asaas", type="primary")

# -----------------------------------------------------------------------------
# 2. VALIDAÇÃO DE SESSÃO E CLIENTE ATIVO
# -----------------------------------------------------------------------------
if 'user' not in st.session_state or st.session_state.user is None:
    st.warning("⚠️ Você precisa fazer login para acessar este módulo.")
    st.stop()

cliente_ativo_id = st.session_state.get("cliente_id_ativo")
if not cliente_ativo_id:
    st.warning("⚠️ Selecione um cliente ativo no Gestor Contábil antes de gerenciar a folha de pagamento.")
    st.stop()

# Busca dados cadastrais e plano do cliente
conn = get_connection()
df_cli = pd.read_sql_query(
    "SELECT nome, regime, COALESCE(plano, 'gratis') AS plano FROM clientes WHERE id = %s",
    conn, params=(cliente_ativo_id,)
)
conn.close()

if df_cli.empty:
    st.error("Cliente não localizado.")
    st.stop()

nome_cliente = df_cli.iloc[0]["nome"]
plano_cliente = str(df_cli.iloc[0]["plano"]).lower()

# Cabeçalho do Módulo
aplicar_tema_global()
exibir_cabecalho("Empregados / Previdência", "Gestão de Folha, Guias & eSocial")
exibir_menu_modulos_topo()

st.info(f"👤 Cliente Ativo: **{nome_cliente}** | Regime: **MEI** | 💳 **{REGRAS_PLANOS.get(plano_cliente, {}).get('nome', 'Plano Gratuito')}**")

# Trava Freemium
if not REGRAS_PLANOS.get(plano_cliente, {}).get("folha_pagamento", False):
    exibir_bloqueio_upgrade("Gestão de Empregado e Encargos MEI")
    st.stop()

# -----------------------------------------------------------------------------
# 3. INTERFACE OPERACIONAL (ABAS)
# -----------------------------------------------------------------------------
conn = get_connection()
df_emp = pd.read_sql_query(
    "SELECT * FROM empregados WHERE cliente_id = %s ORDER BY id DESC",
    conn, params=(cliente_ativo_id,)
)
conn.close()

emp_ativo = df_emp[df_emp["status"] == "Ativo"] if not df_emp.empty else pd.DataFrame()

tab_geral, tab_simulador, tab_cadastro = st.tabs([
    "📋 Empregado Ativo", 
    "🧮 Simulação da Guia DAE / Encargos", 
    "➕ Admissão / Cadastro"
])

# --- ABA 1: EMPREGADO ATIVO E RECIBO DE PAGAMENTO ---
with tab_geral:
    if emp_ativo.empty:
        st.info("ℹ️ Nenhum empregado ativo registrado para este cliente.")
    else:
        dados = emp_ativo.iloc[0]
        st.success(f"**Colaborador Ativo:** {dados['nome']}")
        
        c1, c2, c3 = st.columns(3)
        salario_base = float(dados['salario_base'])
        c1.metric("Salário Base", formatar_brl(salario_base))
        c2.metric("Função / Cargo", dados['cargo'])
        c3.metric("Data de Admissão", str(dados['data_admissao']))

        st.markdown("---")
        
        # --- NOVO BLOCO: EMISSÃO DO RECIBO DE PAGAMENTO (HOLERITE) ---
        st.markdown("#### 📄 Emissão do Recibo de Pagamento (Mensal)")
        
        col_r1, col_r2 = st.columns([1, 2])
        with col_r1:
            mes_ref = st.date_input("Mês de Referência", value=date.today())
            str_mes_ref = mes_ref.strftime("%m/%Y")
            
        with col_r2:
            st.write(" ") # Espaçamento
            st.write(" ")
            btn_recibo = st.button("Gerar Recibo (Pronto para Impressão)", type="primary")
            
        if btn_recibo:
            # Cálculos do recibo
            inss_retido = salario_base * 0.075
            salario_liquido = salario_base - inss_retido
            
            # Identificação do cliente
            conn = get_connection()
            df_empresa = pd.read_sql_query(
                "SELECT nome FROM clientes WHERE id = %s", 
                conn, params=(cliente_ativo_id,)
            )
            conn.close()
            nome_empresa_recibo = df_empresa.iloc[0]['nome'] if not df_empresa.empty else "Empregador não localizado"

            # 1. Função inteligente que gera a via formatada (mais compacta)
            def gerar_via(titulo_via):
                return f"""
                <div style="border: 2px solid #000; padding: 10px; font-family: Arial, sans-serif; background-color: #fff; color: #000; border-radius: 4px;">
                    <h3 style="text-align: center; margin-bottom: 2px; font-size: 14px; margin-top: 2px;">RECIBO DE PAGAMENTO DE SALÁRIO</h3>
                    <p style="text-align: center; margin-top: 0; font-size: 11px;">Referência: <strong>{str_mes_ref}</strong> &nbsp;|&nbsp; <strong>Via do {titulo_via}</strong></p>
                    
                    <div style="border-bottom: 1px solid #000; margin-bottom: 6px; padding-bottom: 4px; font-size: 11px;">
                        <strong>Empregador:</strong> {nome_empresa_recibo}<br>
                        <strong>Empregado:</strong> {dados['nome']} - <strong>CPF:</strong> {dados['cpf']}<br>
                        <strong>Cargo:</strong> {dados['cargo']}
                    </div>
                    
                    <table style="width: 100%; border-collapse: collapse; margin-bottom: 6px; font-size: 11px;">
                        <tr style="border-bottom: 1px solid #ccc;">
                            <th style="text-align: left; padding: 2px;">Descrição</th>
                            <th style="text-align: right; padding: 2px;">Proventos (R$)</th>
                            <th style="text-align: right; padding: 2px;">Descontos (R$)</th>
                        </tr>
                        <tr>
                            <td style="padding: 2px;">Salário Base Contratual</td>
                            <td style="text-align: right; padding: 2px;">{formatar_brl(salario_base).replace('R$ ', '')}</td>
                            <td style="text-align: right; padding: 2px;">-</td>
                        </tr>
                        <tr>
                            <td style="padding: 2px;">INSS Retido (7,5%)</td>
                            <td style="text-align: right; padding: 2px;">-</td>
                            <td style="text-align: right; padding: 2px;">{formatar_brl(inss_retido).replace('R$ ', '')}</td>
                        </tr>
                        <tr style="border-top: 1px solid #000; font-weight: bold;">
                            <td style="padding: 2px;">TOTAIS</td>
                            <td style="text-align: right; padding: 2px;">{formatar_brl(salario_base).replace('R$ ', '')}</td>
                            <td style="text-align: right; padding: 2px;">{formatar_brl(inss_retido).replace('R$ ', '')}</td>
                        </tr>
                    </table>
                    
                    <div style="border: 1px solid #000; padding: 4px; background-color: #f9f9f9; text-align: center; font-size: 13px;">
                        LÍQUIDO A RECEBER: <strong>{formatar_brl(salario_liquido)}</strong>
                    </div>
                    
                    <p style="margin-top: 10px; margin-bottom: 5px; font-size: 9px; text-align: justify;">
                        Declaro ter recebido a importância líquida acima discriminada, referente ao pagamento do meu salário do mês de referência.
                    </p>
                    
                    <div style="margin-top: 15px; margin-bottom: 5px; text-align: center; font-size: 11px;">
                        ________________________________________________________<br>
                        <strong>{dados['nome']}</strong><br>
                        Data: ___/___/______
                    </div>
                </div>
                """

            # 2. HTML Completo: Blindagem CSS com escala para caber na A4
            # 2. HTML Completo: Blindagem CSS (Correção do espaço em branco no topo)
            html_2_vias = f"""
            <style>
            @media print {{
                /* 1. Define margens bem estreitas na folha A4 */
                @page {{
                    margin: 5mm;
                    size: A4 portrait;
                }}

                /* 2. Destrói fisicamente o cabeçalho e menu para não deixarem buracos */
                header, footer, [data-testid="stHeader"], [data-testid="stSidebar"], [data-testid="stToolbar"] {{
                    display: none !important;
                }}

                /* 3. Oculta visualmente os outros elementos da página */
                body * {{
                    visibility: hidden !important;
                }}

                /* 4. Zera o espaçamento das "caixas" invisíveis do Streamlit */
                html, body, .stApp, .main, .block-container, [data-testid="stAppViewContainer"] {{
                    padding: 0 !important;
                    margin: 0 !important;
                }}
                
                /* 5. Traz apenas o nosso holerite de volta */
                #box-holerite, #box-holerite * {{
                    visibility: visible !important;
                }}
                
                /* 6. A MÁGICA: position: fixed prende o holerite no topo exato da folha branca */
                #box-holerite {{
                    position: fixed !important;
                    left: 0 !important;
                    top: 0 !important;
                    width: 100% !important;
                    padding: 0 !important;
                    margin: 0 !important;
                }}
            }}
            </style>

            <div id="box-holerite" style="max-width: 800px; margin: 0 auto; margin-top: 15px;">
                {gerar_via("EMPREGADOR")}
                
                <div class="nao-imprimir" style="border-top: 1px dashed #666; margin: 15px 0; text-align: center; font-size: 11px; color: #666; font-family: Arial;">
                    ✂️ Corte nesta linha ✂️
                </div>
                
                {gerar_via("EMPREGADO")}
            </div>
            """

            # Renderiza na tela
            st.html(html_2_vias)

            # 3. Botões Nativos de Ação
            col_b1, col_b2 = st.columns([1, 2])
            
            with col_b1:
                # Disparador JS que aciona o comando da impressora
                import streamlit.components.v1 as components
                components.html("""
                <button onclick="window.parent.print()" style="
                    background-color: #0284c7; color: white; border: none; 
                    padding: 9px 16px; border-radius: 6px; font-size: 14px; 
                    font-weight: bold; cursor: pointer; width: 100%;">
                    🖨️ Imprimir (2 Vias)
                </button>
                """, height=45)
                
            with col_b2:
                # Caso o cliente queira enviar as duas vias por WhatsApp/E-mail (Gera HTML Limpo)
                html_export = f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>Holerite</title></head><body style='padding: 20px; font-family: Arial;'>{gerar_via('EMPREGADOR')}<hr style='border: 1px dashed #000; margin: 20px 0;'>{gerar_via('EMPREGADO')}</body></html>"
                st.download_button(
                    label="📥 Baixar Arquivo do Holerite",
                    data=html_export,
                    file_name=f"Holerite_2vias_{str_mes_ref.replace('/', '_')}.html",
                    mime="text/html",
                    use_container_width=True
                )

        st.markdown("---")
        
        # --- FIM DO BLOCO DO RECIBO ---

        with st.expander("Encerrar Contrato / Demissão"):
            st.warning("Pela legislação, o MEI só pode possuir 1 funcionário ativo simultaneamente.")
            if st.button("Marcar como Inativo / Rescindido", type="secondary"):
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE empregados SET status = 'Inativo' WHERE id = %s", (int(dados['id']),))
                conn.commit()
                conn.close()
                st.success("Status atualizado para Inativo.")
                st.rerun()

# --- ABA 2: SIMULADOR DE ENCARGOS (GUIA DAE / eSOCIAL) ---
with tab_simulador:
    st.markdown("#### Apuração Mensal da Folha (Regime MEI)")
    st.caption("Cálculo oficial para MEI: INSS retido do trabalhador (7,5%), cota patronal do MEI (3%) e FGTS (8%).")

    salario_simulacao = float(emp_ativo.iloc[0]['salario_base']) if not emp_ativo.empty else 1518.00
    
    salario = st.number_input(
        "Salário Base Contratual (R$)", 
        min_value=1000.00, 
        value=float(salario_simulacao), 
        step=50.0
    )

    desc_inss_func = salario * 0.075
    salario_liquido = salario - desc_inss_func
    inss_patronal = salario * 0.03
    fgts_empresa = salario * 0.08
    
    total_guia_dae = desc_inss_func + inss_patronal + fgts_empresa
    custo_total_empresa = salario + inss_patronal + fgts_empresa

    col_f1, col_f2, col_f3 = st.columns(3)
    col_f1.metric("Salário Líquido a Pagar", formatar_brl(salario_liquido), help="Valor transferido para a conta do funcionário.")
    col_f2.metric("Guia DAE Única (eSocial)", formatar_brl(total_guia_dae), help="INSS Retido + INSS Patronal MEI + FGTS.")
    col_f3.metric("Custo Efetivo Total MEI", formatar_brl(custo_total_empresa), help="Salário Bruto + Encargos da Empresa.")

    st.markdown("---")
    st.write("**Composição da Guia Única (DAE):**")
    df_detalhe = pd.DataFrame([
        {"Rubrica": "INSS Empregado (Retenção 7,5%)", "Responsável": "Descontado do Empregado", "Valor": formatar_brl(desc_inss_func)},
        {"Rubrica": "INSS Patronal MEI (3,0%)", "Responsável": "Custo do Empregador", "Valor": formatar_brl(inss_patronal)},
        {"Rubrica": "FGTS Mensal (8,0%)", "Responsável": "Custo do Empregador", "Valor": formatar_brl(fgts_empresa)},
        {"Rubrica": "Total da Guia Única a Recolher", "Responsável": "Guia DAE do eSocial", "Valor": formatar_brl(total_guia_dae)}
    ])
    st.dataframe(df_detalhe, hide_index=True, use_container_width=True)

# --- ABA 3: CADASTRO / ADMISSÃO ---
with tab_cadastro:
    if not emp_ativo.empty:
        st.warning("⚠️ **Limite Legal Atingido:** O MEI só pode ter 1 empregado ativo. Para registrar outro, encerre o contrato vigente na primeira aba.")
    else:
        with st.form("form_novo_empregado", clear_on_submit=True):
            st.write("#### Ficha Cadastral de Admissão")
            col_c1, col_c2 = st.columns(2)
            nome_colab = col_c1.text_input("Nome Completo do Empregado")
            cpf_colab = col_c2.text_input("CPF (Apenas números)")

            col_c3, col_c4 = st.columns(2)
            cargo_colab = col_c3.text_input("Função / Cargo")
            salario_colab = col_c4.number_input("Salário Base (R$)", min_value=1412.00, value=1518.00, step=50.0)

            data_adm = st.date_input("Data de Admissão", value=date.today())

            btn_admitir = st.form_submit_button("Registrar Empregado", type="primary", use_container_width=True)

            if btn_admitir:
                if not nome_colab or not cpf_colab or not cargo_colab:
                    st.error("Preencha todos os campos obrigatórios.")
                else:
                    try:
                        conn = get_connection()
                        cursor = conn.cursor()
                        cursor.execute(
                            """
                            INSERT INTO empregados (cliente_id, nome, cpf, cargo, salario_base, data_admissao, status)
                            VALUES (%s, %s, %s, %s, %s, %s, 'Ativo')
                            """,
                            (cliente_ativo_id, nome_colab.strip(), cpf_colab.strip(), cargo_colab.strip(), salario_colab, data_adm)
                        )
                        conn.commit()
                        st.success("Colaborador admitido com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao cadastrar empregado: {e}")
                    finally:
                        conn.close()