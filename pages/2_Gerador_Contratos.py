import streamlit as st
import pandas as pd
from datetime import datetime, date
from database import get_connection

# -----------------------------------------------------------------------------
# 1. FUNÇÕES AUXILIARES E FORMATAÇÃO
# -----------------------------------------------------------------------------
def formatar_brl(valor):
    try:
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return "R$ 0,00"

REGRAS_PLANOS = {
    'gratis': {'modelos_pro': False, 'nome': 'Plano MEI Gratuito'},
    'pro': {'modelos_pro': True, 'nome': 'Plano MEI Pro'},
    'contador': {'modelos_pro': True, 'nome': 'Plano Escritório / Contador'}
}

def exibir_bloqueio_upgrade():
    st.warning("🔒 **Modelo Exclusivo do Plano Pro**")
    st.markdown(
        """
        <div style="background-color: #f8f9fa; border: 1px solid #e9ecef; border-radius: 8px; padding: 20px; margin: 15px 0;">
            <p style="color: #64748b; font-size: 14px; margin: 0;">
                O modelo de contrato completo (com LGPD, Confidencialidade (NDA), Representantes e Dados Bancários) é um recurso do <strong>Plano MEI Pro</strong>.
            </p>
        </div>
        """, unsafe_allow_html=True
    )
    st.link_button("⭐ Fazer Upgrade Agora", "https://asaas.com/c/seu-link-asaas", type="primary")

def montar_html_contrato(cliente_mei, dados_contrato):
    # Formatação de Variáveis
    data_dt = pd.to_datetime(dados_contrato['data_inicio'])
    data_formatada = data_dt.strftime("%d/%m/%Y")
    valor_formatado = formatar_brl(dados_contrato['valor_total'])
    
    # Geração do Número de Controle (Ex: CTR-202610-0012)
    id_contrato = dados_contrato.get('id', 'PROV')
    num_controle = f"CTR-{data_dt.year}{data_dt.month:02d}-{str(id_contrato).zfill(4)}"

    # Verifica se há cláusulas extras
    clausulas_extras_html = ""
    texto_extra = dados_contrato.get('clausulas_extras')
    num_clausula_extra = "OITAVA" if "PRO" in dados_contrato['modelo'] else "SEXTA"
    if texto_extra and str(texto_extra).strip() not in ["None", ""]:
        clausulas_extras_html = f"""
        <p style="text-align: justify; margin-top: 15px;">
            <strong>CLÁUSULA {num_clausula_extra} – DAS CONDIÇÕES ESPECIAIS E ADICIONAIS</strong><br>
            {str(texto_extra).replace(chr(10), '<br>')}
        </p>
        """

    eh_modelo_pro = "PRO" in dados_contrato['modelo']

    if eh_modelo_pro:
        # =====================================================================
        # MODELO PRO (Baseado no documento oficial com LGPD e NDA)
        # =====================================================================
        html = f"""
        <div id="documento-contrato" style="font-family: Arial, sans-serif; font-size: 12px; line-height: 1.5; color: #000; background: #fff; padding: 40px; max-width: 800px; margin: 0 auto;">
            
            <div style="text-align: right; font-size: 11px; color: #555; margin-bottom: 20px;">
                <strong>Contrato:</strong> {num_controle}
            </div>

            <h3 style="text-align: center; text-transform: uppercase; margin-bottom: 25px; font-size: 14px;">
                CONTRATO DE PRESTAÇÃO DE SERVIÇOS E GESTÃO<br>EM TECNOLOGIA DA INFORMAÇÃO
            </h3>

            <p style="text-align: justify;">
                <strong>CONTRATANTE</strong> - <strong>{dados_contrato['contratante_nome']}</strong>, localizada na {dados_contrato['contratante_end']}, CNPJ/CPF: {dados_contrato['contratante_doc']}. Tendo como representante legal o(a) Sr(a). {dados_contrato.get('representante_nome', 'Não informado')}, portador(a) do CPF: {dados_contrato.get('representante_cpf', 'Não informado')}.
            </p>

            <p style="text-align: justify;">
                <strong>CONTRATADO</strong> - <strong>{cliente_mei['nome']}</strong>, estabelecido à {dados_contrato.get('endereco_mei', 'Não informado')}, CNPJ/CPF: {cliente_mei['cnpj_cpf']}.
            </p>

            <p style="text-align: justify;">
                As partes acima identificadas têm, entre si, justo e acertado o presente CONTRATO DE PRESTAÇÃO DE SERVIÇOS, que se regerá pelas cláusulas seguintes:
            </p>

            <p style="text-align: justify;"><strong>1. OBJETO</strong><br>
            O presente contrato tem por objeto a contratação de serviços técnicos especializados a serem executados, compreendendo:<br>
            <em>{dados_contrato['objeto_servico'].replace(chr(10), '<br>')}</em>
            </p>

            <p style="text-align: justify;"><strong>2. DA REMUNERAÇÃO E FORMA DE PAGAMENTO</strong><br>
            2.1. O CONTRATADO receberá mensalmente a título de remuneração pelos serviços prestados, a importância de <strong>{valor_formatado}</strong>, com vencimento conforme acordado ({dados_contrato['forma_pagamento']}), depositados/transferidos via PIX no banco: {dados_contrato.get('banco_conta', 'Não informado')}, Chave PIX: {dados_contrato.get('chave_pix', 'Não informada')}.
            </p>

            <p style="text-align: justify;"><strong>3. DA VIGÊNCIA E RESCISÃO</strong><br>
            3.1. O presente contrato vigorará pelo prazo determinado de {dados_contrato.get('prazo_vigencia', 12)} meses contados da data de assinatura, sendo automaticamente renovado por igual período, podendo ser rescindido a qualquer tempo mediante aviso prévio de {dados_contrato.get('prazo_aviso_previo', 60)} dias, por escrito.
            </p>

            <p style="text-align: justify;"><strong>4. CONFIDENCIALIDADE</strong><br>
            4.1. Toda e qualquer informação técnica, administrativa ou comercial transmitida será considerada como estritamente confidencial pelo CONTRATADO, que se obriga a não revelar a terceiros.<br>
            4.2. Quando do término ou rescisão do presente contrato, o CONTRATADO obriga-se a devolver imediatamente à CONTRATANTE todo e qualquer documento. Qualquer violação facultará à CONTRATANTE a possibilidade de rescisão unilateral imediata.
            </p>

            <p style="text-align: justify;"><strong>5. DA PROTEÇÃO DE DADOS (LGPD)</strong><br>
            5.1. O CONTRATADO obriga-se a atuar em conformidade com a Lei 13.709/2018 (LGPD), tratando os dados pessoais a que tiver acesso apenas de acordo com as instruções da CONTRATANTE.<br>
            5.2. O CONTRATADO deverá notificar a CONTRATANTE em até 24 horas a respeito de qualquer violação de segurança.<br>
            5.3. O CONTRATADO será integralmente responsável pelo pagamento de perdas e danos resultantes do descumprimento quanto à proteção de dados.
            </p>

            <p style="text-align: justify;"><strong>6. DA INEXISTÊNCIA DE VÍNCULO TRABALHISTA</strong><br>
            Este contrato não estabelece qualquer vínculo empregatício entre a CONTRATANTE e o CONTRATADO e as pessoas que o CONTRATADO usar na execução da sua atividade.
            </p>

            <p style="text-align: justify;"><strong>7. DO FORO</strong><br>
            As partes elegem o foro da cidade de {dados_contrato['cidade_foro']}, com expressa renúncia a qualquer outro.
            </p>

            {clausulas_extras_html}

            <br><p style="text-align: center;">{dados_contrato['cidade_foro']}, {data_formatada}.</p><br><br>
            
            <table style="width: 100%; border: none; text-align: center; margin-top: 30px;">
                <tr>
                    <td style="width: 50%; border: none;">
                        ________________________________________<br>
                        <strong>CONTRATANTE</strong><br>{dados_contrato.get('representante_nome', dados_contrato['contratante_nome'])}
                    </td>
                    <td style="width: 50%; border: none;">
                        ________________________________________<br>
                        <strong>CONTRATADO</strong><br>{cliente_mei['nome']}
                    </td>
                </tr>
            </table>
        </div>
        """
    else:
        # =====================================================================
        # MODELO FREE (Simplificado de 1 página)
        # =====================================================================
        html = f"""
        <div id="documento-contrato" style="font-family: Arial, sans-serif; font-size: 13px; line-height: 1.6; color: #000; background: #fff; padding: 40px; max-width: 800px; margin: 0 auto;">
            <h3 style="text-align: center; margin-bottom: 25px;">CONTRATO SIMPLIFICADO DE PRESTAÇÃO DE SERVIÇOS</h3>
            <p style="text-align: justify;"><strong>CONTRATANTE:</strong> {dados_contrato['contratante_nome']}, CNPJ/CPF: {dados_contrato['contratante_doc']}, Endereço: {dados_contrato['contratante_end']}.</p>
            <p style="text-align: justify;"><strong>CONTRATADO:</strong> {cliente_mei['nome']}, CNPJ/CPF: {cliente_mei['cnpj_cpf']}.</p>
            <p style="text-align: justify;"><strong>CLÁUSULA 1 – OBJETO:</strong> Prestação dos serviços de: <em>{dados_contrato['objeto_servico']}</em>.</p>
            <p style="text-align: justify;"><strong>CLÁUSULA 2 – PREÇO:</strong> O valor pactuado é de <strong>{valor_formatado}</strong>, pago da seguinte forma: {dados_contrato['forma_pagamento']}.</p>
            <p style="text-align: justify;"><strong>CLÁUSULA 3 – VÍNCULO E RESCISÃO:</strong> Não há vínculo trabalhista. O contrato vigora a partir de {data_formatada}. Rescisão livre mediante aviso prévio de 15 dias.</p>
            <p style="text-align: justify;"><strong>CLÁUSULA 4 – FORO:</strong> Comarca de {dados_contrato['cidade_foro']}.</p>
            {clausulas_extras_html}
            <br><p style="text-align: center;">{dados_contrato['cidade_foro']}, {data_formatada}.</p><br><br>
            <table style="width: 100%; border: none; text-align: center;">
                <tr>
                    <td style="width: 50%; border: none;">_____________________________<br>{dados_contrato['contratante_nome']}</td>
                    <td style="width: 50%; border: none;">_____________________________<br>{cliente_mei['nome']}</td>
                </tr>
            </table>
        </div>
        """
    return html

css_print_contrato = """
<style>
@media print {
    @page { margin: 15mm; size: A4 portrait; }
    header, footer, [data-testid="stHeader"], [data-testid="stSidebar"], [data-testid="stToolbar"] { display: none !important; }
    body * { visibility: hidden !important; }
    #documento-contrato, #documento-contrato * { visibility: visible !important; }
    #documento-contrato {
        position: absolute !important; left: 0 !important; top: 0 !important;
        width: 100% !important; border: none !important; padding: 0 !important; margin: 0 !important;
    }
}
</style>
"""

# -----------------------------------------------------------------------------
# 2. CONTROLE DE SESSÃO E CLIENTE
# -----------------------------------------------------------------------------
if 'user' not in st.session_state or st.session_state.user is None:
    st.warning("⚠️ Faça login para acessar o sistema.")
    st.stop()

conn = get_connection()
df_todos_clientes = pd.read_sql_query(
    "SELECT id, nome, cnpj_cpf, regime, COALESCE(plano, 'gratis') AS plano FROM clientes WHERE user_id = %s ORDER BY nome ASC",
    conn, params=(st.session_state.user.id,)
)
conn.close()

if df_todos_clientes.empty:
    st.warning("⚠️ Cadastre uma empresa no Gestor Contábil primeiro.")
    st.stop()

dict_clientes = dict(zip(df_todos_clientes["nome"], df_todos_clientes["id"]))
idx_padrao = list(dict_clientes.values()).index(st.session_state["cliente_id_ativo"]) if "cliente_id_ativo" in st.session_state and st.session_state["cliente_id_ativo"] in dict_clientes.values() else 0

st.sidebar.markdown("---")
cliente_ativo_id = dict_clientes[st.sidebar.selectbox("Cliente em Atendimento", list(dict_clientes.keys()), index=idx_padrao)]
st.session_state["cliente_id_ativo"] = cliente_ativo_id
cliente_info = df_todos_clientes[df_todos_clientes["id"] == cliente_ativo_id].iloc[0]
plano_cliente = str(cliente_info["plano"]).lower()
cliente_eh_pro = REGRAS_PLANOS.get(plano_cliente, {}).get("modelos_pro", False)

# -----------------------------------------------------------------------------
# 3. MODO DE IMPRESSÃO ISOLADA
# -----------------------------------------------------------------------------
if "contrato_print" in st.session_state and st.session_state["contrato_print"] is not None:
    dados_print = st.session_state["contrato_print"]
    st.button("⬅️ Voltar aos Contratos", on_click=lambda: st.session_state.update({"contrato_print": None}))
    html_final = montar_html_contrato(cliente_info, dados_print)
    st.html(css_print_contrato + html_final)
    c1, c2 = st.columns([1, 2])
    with c1:
        import streamlit.components.v1 as components
        components.html("""<button onclick="window.parent.print()" style="background-color: #0284c7; color: white; border: none; padding: 10px; border-radius: 6px; font-weight: bold; width: 100%; cursor:pointer;">🖨️ Imprimir Contrato</button>""", height=45)
    with c2:
        st.download_button("📥 Baixar Documento (HTML)", f"<!DOCTYPE html><html><body>{html_final}</body></html>", f"Contrato_{dados_print['contratante_nome']}.html", "text/html", use_container_width=True)
    st.stop()

# -----------------------------------------------------------------------------
# 4. INTERFACE PRINCIPAL
# -----------------------------------------------------------------------------
st.title("📑 Gestão de Contratos MEI")
st.info(f"👤 Contratado: **{cliente_info['nome']}** | CNPJ/CPF: **{cliente_info['cnpj_cpf']}**")

tab_novo, tab_historico = st.tabs(["📝 Elaborar Novo Contrato", "📂 Meus Contratos Salvos"])

with tab_novo:
    modelo_escolhido = st.selectbox("Modelo de Contrato:", [
        "Contrato Padrão de Serviços (Gratuito)", 
        "🔒 Contrato Corporativo PRO (Com LGPD, NDA e Multas) - (PRO)"
    ])
    
    eh_modelo_pro_form = "PRO" in modelo_escolhido
    if eh_modelo_pro_form and not cliente_eh_pro:
        exibir_bloqueio_upgrade()
    else:
        with st.form("form_contrato", clear_on_submit=True):
            st.subheader("1. Dados do Contratante (Cliente)")
            col1, col2 = st.columns(2)
            contratante_nome = col1.text_input("Empresa/Razão Social do Cliente")
            contratante_doc = col2.text_input("CNPJ ou CPF")
            contratante_end = st.text_input("Endereço Completo do Cliente")
            
            # Campos Extras do Contratante liberados se PRO
            representante_nome = ""
            representante_cpf = ""
            if eh_modelo_pro_form:
                c_rep1, c_rep2 = st.columns(2)
                representante_nome = c_rep1.text_input("Nome do Representante Legal (Assinante)")
                representante_cpf = c_rep2.text_input("CPF do Representante")

            st.subheader("2. Dados do Contratado (Seu MEI)")
            endereco_mei = st.text_input("Seu Endereço Profissional (Contratado)")
            banco_conta = ""
            chave_pix = ""
            if eh_modelo_pro_form:
                c_bnc1, c_bnc2 = st.columns(2)
                banco_conta = c_bnc1.text_input("Banco, Agência e Conta")
                chave_pix = c_bnc2.text_input("Chave PIX")

            st.subheader("3. Objeto e Valores")
            objeto_servico = st.text_area("Descrição detalhada dos serviços", height=80)
            col3, col4 = st.columns(2)
            valor_total = col3.number_input("Valor Mensal / Total (R$)", min_value=10.0, value=2800.0, step=100.0)
            forma_pagamento = col4.text_input("Condição de Pagamento", value="Até o 5º dia útil do mês subsequente")
            
            st.subheader("4. Prazos e Foro")
            col5, col6, col7 = st.columns(3)
            data_inicio = col5.date_input("Data de Início")
            prazo_vigencia = 12
            prazo_aviso_previo = 60
            if eh_modelo_pro_form:
                prazo_vigencia = col6.number_input("Vigência (Meses)", value=12)
                prazo_aviso_previo = col7.number_input("Aviso Prévio (Dias)", value=60)
            cidade_foro = st.text_input("Cidade (Foro)", value="Rio de Janeiro - RJ")

            clausulas_extras = ""
            if eh_modelo_pro_form:
                st.markdown("---")
                clausulas_extras = st.text_area("✨ Cláusulas Especiais (Opcional)", placeholder="Insira multas ou regras adicionais específicas.")

            if st.form_submit_button("💾 Salvar e Gerar Contrato", type="primary", use_container_width=True):
                if not contratante_nome or not objeto_servico:
                    st.error("Preencha ao menos o Nome do Cliente e a Descrição do Serviço.")
                else:
                    try:
                        conn = get_connection()
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO contratos (
                                cliente_id, modelo, contratante_nome, contratante_doc, contratante_end, 
                                objeto_servico, valor_total, forma_pagamento, data_inicio, cidade_foro, 
                                clausulas_extras, representante_nome, representante_cpf, endereco_mei, 
                                banco_conta, chave_pix, prazo_vigencia, prazo_aviso_previo
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
                        """, (
                            cliente_ativo_id, modelo_escolhido, contratante_nome, contratante_doc, contratante_end, 
                            objeto_servico, valor_total, forma_pagamento, data_inicio, cidade_foro, 
                            clausulas_extras, representante_nome, representante_cpf, endereco_mei, 
                            banco_conta, chave_pix, prazo_vigencia, prazo_aviso_previo
                        ))
                        novo_id = cursor.fetchone()[0]
                        conn.commit()
                        
                        # Carrega os dados na tela de impressão
                        st.session_state["contrato_print"] = {
                            'id': novo_id, 'modelo': modelo_escolhido, 'contratante_nome': contratante_nome, 
                            'contratante_doc': contratante_doc, 'contratante_end': contratante_end,
                            'representante_nome': representante_nome, 'representante_cpf': representante_cpf,
                            'endereco_mei': endereco_mei, 'banco_conta': banco_conta, 'chave_pix': chave_pix,
                            'objeto_servico': objeto_servico, 'valor_total': float(valor_total), 
                            'forma_pagamento': forma_pagamento, 'data_inicio': data_inicio, 'cidade_foro': cidade_foro, 
                            'prazo_vigencia': prazo_vigencia, 'prazo_aviso_previo': prazo_aviso_previo,
                            'clausulas_extras': clausulas_extras
                        }
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar no banco de dados: {e}")
                    finally:
                        if 'conn' in locals(): conn.close()

with tab_historico:
    st.markdown("#### Histórico de Documentos Gerados")
    conn = get_connection()
    df_hist = pd.read_sql_query("SELECT * FROM contratos WHERE cliente_id = %s ORDER BY id DESC", conn, params=(cliente_ativo_id,))
    conn.close()

    if df_hist.empty:
        st.info("Nenhum contrato salvo.")
    else:
        for idx, row in df_hist.iterrows():
            data_str = pd.to_datetime(row['data_inicio']).strftime('%d/%m/%Y')
            
            with st.expander(f"📄 Contrato #{row['id']} - {row['contratante_nome']} ({data_str})"):
                st.write(f"**Serviço:** {row['objeto_servico']}")
                if st.button("🖨️ Ver / Imprimir", key=f"print_{row['id']}", type="primary"):
                    st.session_state["contrato_print"] = row.to_dict()
                    st.rerun()