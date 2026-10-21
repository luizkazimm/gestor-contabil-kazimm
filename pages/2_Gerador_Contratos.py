import streamlit as st
import pandas as pd
from datetime import datetime, date
from database import get_connection

# Tenta importar a biblioteca de valor por extenso
try:
    from num2words import num2words
    def valor_por_extenso(valor):
        return num2words(valor, lang='pt_BR', to='currency').capitalize()
except ImportError:
    def valor_por_extenso(valor):
        return "(Valor por extenso - Instale o num2words)"

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
        """<div style="background-color: #f8f9fa; border: 1px solid #e9ecef; border-radius: 8px; padding: 20px; margin: 15px 0;">
            <p style="color: #64748b; font-size: 14px; margin: 0;">O modelo de contrato completo é um recurso do <strong>Plano MEI Pro</strong>.</p>
        </div>""", unsafe_allow_html=True
    )
    st.link_button("⭐ Fazer Upgrade Agora", "https://asaas.com/c/seu-link-asaas", type="primary")

def montar_html_contrato(cliente_mei, dados_contrato):
    data_dt = pd.to_datetime(dados_contrato['data_inicio'])
    data_formatada = data_dt.strftime("%d/%m/%Y")
    
    # Formatação da data por extenso (segura para nuvem/Linux)
    meses_pt = {
        1: "janeiro", 2: "fevereiro", 3: "março", 4: "abril",
        5: "maio", 6: "junho", 7: "julho", 8: "agosto",
        9: "setembro", 10: "outubro", 11: "novembro", 12: "dezembro"
    }
    data_extenso = f"{data_dt.day:02d} de {meses_pt[data_dt.month]} de {data_dt.year}"
    
    # Formatação de Valores com Extenso
    valor_numerico = float(dados_contrato['valor_total'])
    valor_formatado = formatar_brl(valor_numerico)
    valor_extenso = valor_por_extenso(valor_numerico)
    string_valor_completa = f"{valor_formatado} ({valor_extenso})" # Ex: R$ 2.800,00 (Dois mil e oitocentos reais)
    
    # Número de Controle
    id_contrato = dados_contrato.get('id', 'PROV')
    num_controle = f"CTR-{data_dt.year}{data_dt.month:02d}-{str(id_contrato).zfill(4)}"

    # Montagem de Endereços Completos para facilitar no HTML
    end_cliente_completo = f"{dados_contrato['contratante_end']}, Bairro {dados_contrato.get('contratante_bairro','')}, {dados_contrato.get('contratante_cidade','')} - {dados_contrato.get('contratante_uf','')}, CEP: {dados_contrato.get('contratante_cep','')}"
    end_mei_completo = f"{dados_contrato.get('endereco_mei','')}, Bairro {dados_contrato.get('mei_bairro','')}, {dados_contrato.get('mei_cidade','')} - {dados_contrato.get('mei_uf','')}, CEP: {dados_contrato.get('mei_cep','')}"

    clausulas_extras_html = ""
    texto_extra = dados_contrato.get('clausulas_extras')
    if texto_extra and str(texto_extra).strip() not in ["None", ""]:
        clausulas_extras_html = f"<p style='text-align: justify; margin-top: 15px;'><strong>CLÁUSULA ADICIONAL</strong><br>{str(texto_extra).replace(chr(10), '<br>')}</p>"

    eh_modelo_pro = "PRO" in dados_contrato['modelo']

    if eh_modelo_pro:
        # 1. Monta a tag da Logo se existir no cadastro da empresa
        logo_b64 = cliente_mei.get('logo_base64')
        tag_logo = ""
        if pd.notna(logo_b64) and logo_b64:
            tag_logo = f'<img src="{logo_b64}" style="max-height: 60px; max-width: 220px; object-fit: contain;" alt="Logotipo">'

        # =====================================================================
        # CONTRATO (PLANO PRO) - ENCAPSULADO COM LOGO E FORMATAÇÃO DE IMPRESSÃO
        # =====================================================================
        html = f"""
        <div id="documento-contrato" style="font-family: Arial, Helvetica, sans-serif; font-size: 12px; line-height: 1.6; color: #111827; background: #ffffff; padding: 20px 30px; max-width: 820px; margin: 0 auto;">
            
            <!-- CABEÇALHO DO CONTRATO: LOGO À ESQUERDA E NÚMERO DE CONTROLE À DIREITA -->
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #0176A1; padding-bottom: 12px; margin-bottom: 25px;">
                <div style="text-align: left;">
                    {tag_logo}
                </div>
                <div style="text-align: right; font-size: 11px; color: #475569; line-height: 1.4;">
                    <strong style="color: #0176A1; font-size: 12px;">{num_controle}</strong><br>
                    <span>Emissão: {data_formatada}</span>
                </div>
            </div>

            <h3 style="text-align: center; text-transform: uppercase; font-size: 13px; font-weight: bold; margin-bottom: 25px; color: #0f172a; line-height: 1.4;">
                CONTRATO DE PRESTAÇÃO DE SERVIÇOS E GESTÃO EM TECNOLOGIA DA INFORMAÇÃO
            </h3>

            <p style="text-align: justify; margin-bottom: 14px;">
                <strong>CONTRATANTE</strong> – <strong>{dados_contrato['contratante_nome']}</strong>, localizada na {end_cliente_completo}, CNPJ: {dados_contrato['contratante_doc']}. Tendo como representante legal o(a) Sr.(ª) {dados_contrato.get('representante_nome', '')}, portador(a) do CPF/MF: {dados_contrato.get('representante_cpf', '')}.
            </p>

            <p style="text-align: justify; margin-bottom: 14px;">
                <strong>CONTRATADO</strong> - <strong>{cliente_mei['nome']}</strong>, localizado e estabelecido à {end_mei_completo}, CNPJ: {cliente_mei['cnpj_cpf']}.
            </p>

            <p style="text-align: justify; margin-bottom: 16px;">
                As partes acima identificadas têm, entre si, justo e acertado o presente CONTRATO DE PRESTAÇÃO DE SERVIÇOS DE GESTÃO DE TECNOLOGIA DA INFORMAÇÃO, que se regerá pelas cláusulas seguintes:
            </p>

            <p style="text-align: justify; margin-bottom: 14px;">
                <strong>1. OBJETO</strong><br>
                O presente contrato tem por objeto a contratação de serviços técnicos especializados para implantação, implementação e manutenção do sistema de Tecnologia da Informação a serem executados na sede da CONTRATANTE, compreendendo:<br>
                <em>{dados_contrato['objeto_servico'].replace(chr(10), '<br>')}</em>
            </p>

            <p style="text-align: justify; margin-bottom: 14px;">
                <strong>2. DA REMUNERAÇÃO E FORMA DE PAGAMENTO</strong><br>
                2.1. O CONTRATADO receberá mensalmente a título de remuneração pelos serviços prestados, a importância de <strong>{string_valor_completa}</strong>, com vencimento conforme acordado ({dados_contrato['forma_pagamento']}), depositados, transferido ou via PIX: {dados_contrato.get('chave_pix', '')} no banco: {dados_contrato.get('banco_conta', '')}.<br>
                2.2. As despesas com deslocamento até a sede da CONTRATANTE, quando para atender à chamados de alta criticidade, manutenção preventiva e auditorias, já estarão inclusos no pagamento mensal.
            </p>

            <p style="text-align: justify; margin-bottom: 14px;">
                <strong>3. DA VIGÊNCIA E RESCISÃO</strong><br>
                3.1. O presente contrato vigorará pelo prazo determinado de {dados_contrato.get('prazo_vigencia', 12)} meses contados da data de assinatura deste instrumento, sendo automaticamente renovado por igual período, podendo, após a primeira renovação ser rescindido a qualquer tempo mediante aviso prévio de {dados_contrato.get('prazo_aviso_previo', 60)} dias, por escrito.
            </p>

            <p style="text-align: justify; margin-bottom: 14px;">
                <strong>4. CONFIDENCIALIDADE</strong><br>
                4.1. Toda e qualquer informação técnica, administrativa ou comercial, transmitida verbalmente ou por escrito, que o CONTRATADO venha a ter acesso durante a prestação de serviços, ou que tenha sido fornecida pela CONTRATANTE ao CONTRATADO para esse fim, será considerada como estritamente confidencial pelo CONTRATADO, que se obriga a não revelar a terceiros e deverá ser utilizada única e exclusivamente para os serviços contratados.<br>
                4.2. É vedada a cópia ou qualquer outra forma de reprodução destas informações, exceto para o cumprimento de obrigações estabelecidas nos termos deste instrumento e de acordo com a legislação aplicável relativamente a direitos autorais e propriedade intelectual. Quando do término ou rescisão do presente contrato, o CONTRATADO obriga-se a devolver imediatamente à CONTRATANTE, todo e qualquer documento entregue a ele para execução dos serviços. Qualquer violação ao estipulado nesta cláusula facultará à CONTRATANTE a possibilidade de rescisão unilateral imediata deste.
            </p>

            <p style="text-align: justify; margin-bottom: 14px;">
                <strong>5. DA PROTEÇÃO DE DADOS (LGPD)</strong><br>
                5.1. O CONTRATADO, obriga-se a atuar no presente Contrato em conformidade com a Legislação vigente sobre Proteção de Dados Pessoais e as determinações de órgãos reguladores/fiscalizadores sobre a matéria, em especial a Lei 13.709/2018, além das demais normas e políticas de proteção de dados de cada país onde houver qualquer tipo de tratamento dos dados dos clientes, o que inclui os dados dos clientes desta. No manuseio dos dados o CONTRATADO deverá:<br>
                - Tratar os dados pessoais a que tiver acesso apenas de acordo com as instruções da CONTRATANTE e em conformidade com estas cláusulas, e que, na eventualidade, de não mais poder cumprir estas obrigações, por qualquer razão, concorda em informar de modo formal este fato imediatamente à CONTRATANTE, que terá o direito de rescindir o contrato sem qualquer ônus, multa ou encargo.<br>
                - Manter e utilizar medidas de segurança administrativas, técnicas e físicas apropriadas e suficientes para proteger a confidencialidade e integridade de todos os dados pessoais mantidos ou consultados/transmitidos eletronicamente, para garantir a proteção desses dados contra acesso não autorizado, destruição, uso, modificação, divulgação ou perda acidental ou indevida.<br>
                - Acessar os dados dentro de seu escopo e na medida abrangida por sua permissão de acesso (autorização) e que os dados pessoais não podem ser lidos, copiados, modificados ou removidos sem autorização expressa e por escrito da CONTRATANTE.<br>
                - Garantir a confidencialidade dos dados processados, assegurando que lidam com os dados pessoais sob responsabilidade da CONTRATANTE, bem como a manter quaisquer Dados Pessoais estritamente confidenciais e de não os utilizar para outros fins, com exceção da prestação de serviços à CONTRATANTE.<br>
                5.2. Os dados pessoais não poderão ser revelados a terceiros, com exceção da prévia autorização por escrito da CONTRATANTE, quer direta ou indiretamente, seja mediante a distribuição de cópias, resumos, compilações, extratos, análises, estudos ou outros meios que contenham ou de outra forma reflitam referidas Informações.<br>
                5.3. Caso o CONTRATADO seja obrigado por determinação legal a fornecer dados pessoais a uma autoridade pública, deverá informar previamente a CONTRATANTE para que esta tome as medidas que julgar cabíveis.<br>
                5.4. O CONTRATADO deverá notificar a CONTRATANTE em até 24 (vinte e quatro) horas a respeito de: qualquer não cumprimento (ainda que suspeito) das disposições legais relativas à proteção de Dados Pessoais pelo CONTRATADO, seus funcionários, ou terceiros autorizados; qualquer outra violação de segurança no âmbito das atividades e responsabilidades do CONTRATADO.<br>
                5.5. O CONTRATADO será integralmente responsável pelo pagamento de perdas e danos de ordem moral e material, bem como pelo ressarcimento do pagamento de qualquer multa ou penalidade imposta à CONTRATANTE e/ou a terceiros diretamente resultantes do descumprimento pelo CONTRATADO de qualquer das cláusulas previstas neste capítulo quanto a proteção e uso dos dados pessoais.
            </p>

            <p style="text-align: justify; margin-bottom: 14px;">
                <strong>6. DA INEXISTÊNCIA DE VÍNCULO TRABALHISTA</strong><br>
                Este contrato não estabelece qualquer vínculo empregatício entre a CONTRATANTE e o CONTRATADO e as pessoas que o CONTRATADO usar na execução da sua atividade.
            </p>

            {clausulas_extras_html}

            <p style="text-align: justify; margin-bottom: 14px;">
                <strong>7. DO FORO</strong><br>
                As partes elegem o foro da cidade de {dados_contrato['cidade_foro']}, com expressa renúncia a qualquer outro, por mais privilegiado que seja para dirimir questões oriundas da interpretação e execução do presente contrato.<br>
                E por estarem de pleno acordo com as cláusulas e condições aqui definidas, assinam o presente contrato em 2 (duas) vias de igual teor para todos os efeitos legais.
            </p>

            <p style="text-align: right; margin: 35px 0 25px 0; font-size: 12px">
                {dados_contrato['cidade_foro']}, {data_extenso}.
            </p>

            <!-- TABELA DE ASSINATURAS LADO A LADO -->
            <table style="width: 100%; border: none; margin-top: 40px; page-break-inside: avoid;">
                <tr>
                    <td style="width: 48%; border: none; text-align: center; vertical-align: top;">
                        ________________________________________<br>
                        <strong>{dados_contrato['contratante_nome']}</strong><br>
                        <span style="font-size: 11px;">Nome: {dados_contrato.get('representante_nome', '')}</span><br>
                        <span style="font-size: 11px;">CPF: {dados_contrato.get('representante_cpf', '')}</span>
                    </td>
                    <td style="width: 4%; border: none;"></td>
                    <td style="width: 48%; border: none; text-align: center; vertical-align: top;">
                        ________________________________________<br>
                        <strong>{cliente_mei['nome']}</strong><br>
                        <span style="font-size: 11px;">CPF/CNPJ: {cliente_mei['cnpj_cpf']}</span>
                    </td>
                </tr>
            </table>

        </div>
        """
    else:
        # =====================================================================
        # CONTRATO MODELO FREE SIMPLIFICADO
        # =====================================================================
        html = f"""
        <div id="documento-contrato" style="font-family: Arial, sans-serif; font-size: 13px; line-height: 1.6; color: #000; background: #fff; padding: 40px; max-width: 800px; margin: 0 auto;">
            <h3 style="text-align: center; margin-bottom: 25px;">CONTRATO SIMPLIFICADO DE PRESTAÇÃO DE SERVIÇOS</h3>
            <p style="text-align: justify;"><strong>CONTRATANTE:</strong> {dados_contrato['contratante_nome']}, CNPJ/CPF: {dados_contrato['contratante_doc']}, Endereço: {end_cliente_completo}.</p>
            <p style="text-align: justify;"><strong>CONTRATADO:</strong> {cliente_mei['nome']}, CNPJ/CPF: {cliente_mei['cnpj_cpf']}, Endereço: {end_mei_completo}.</p>
            <p style="text-align: justify;"><strong>CLÁUSULA 1 – OBJETO:</strong> Prestação dos serviços de: <em>{dados_contrato['objeto_servico']}</em>.</p>
            <p style="text-align: justify;"><strong>CLÁUSULA 2 – PREÇO:</strong> O valor pactuado é de <strong>{string_valor_completa}</strong>, pago da seguinte forma: {dados_contrato['forma_pagamento']}.</p>
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

# -----------------------------------------------------------------------------
# CSS DE IMPRESSÃO MULTI-PÁGINAS (Corrigido para Contratos Longos)
# -----------------------------------------------------------------------------
css_print_contrato = """
<style>
@media print {
    /* 1. Define tamanho A4 e margens oficiais de documentos */
    @page {
        margin: 20mm 15mm 20mm 15mm;
        size: A4 portrait;
    }

    /* 2. Remove completamente barras, botões e cabeçalhos da tela */
    [data-testid="stSidebar"],
    [data-testid="stHeader"],
    [data-testid="stToolbar"],
    header,
    footer,
    .stButton,
    .stDownloadButton,
    iframe,
    .nao-imprimir {
        display: none !important;
    }

    /* 3. Desbloqueia as restrições de rolagem e altura do Streamlit */
    html, body, .stApp, [data-testid="stAppViewContainer"], section.main, .block-container {
        overflow: visible !important;
        height: auto !important;
        min-height: auto !important;
        max-height: none !important;
        margin: 0 !important;
        padding: 0 !important;
        background: #ffffff !important;
    }

    /* 4. Permite que as 5 páginas fluam naturalmente no papel */
    #documento-contrato {
        display: block !important;
        visibility: visible !important;
        position: static !important;
        width: 100% !important;
        max-width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
        border: none !important;
        background: transparent !important;
    }

    #documento-contrato, #documento-contrato * {
        visibility: visible !important;
        color: #000000 !important;
    }

    /* 5. Evita quebras de página inadequadas no meio de parágrafos e assinaturas */
    p {
        orphans: 2;
        widows: 2;
    }
    table, .bloco-assinatura {
        page-break-inside: avoid !important;
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
    """
    SELECT id, nome, cnpj_cpf, regime, 
           COALESCE(plano, 'gratis') AS plano, 
           logo_base64 
    FROM clientes 
    WHERE user_id = %s 
    ORDER BY nome ASC
    """,
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
    
    # Trava de Segurança: Garante que a tag #documento-contrato sempre exista,
    # mesmo que o HTML colado do WordToHTML não tenha vindo com ela
    if 'id="documento-contrato"' not in html_final:
        html_final = f"""
        <div id="documento-contrato" style="font-family: Arial, sans-serif; font-size: 12px; line-height: 1.6; color: #000; padding: 20px;">
            {html_final}
        </div>
        """

    st.html(css_print_contrato + html_final)
    
    c1, c2 = st.columns([1, 2])
    with c1:
        import streamlit.components.v1 as components
        components.html("""<button onclick="window.parent.print()" style="background-color: #0284c7; color: white; border: none; padding: 10px; border-radius: 6px; font-weight: bold; width: 100%; cursor:pointer;">🖨️ Imprimir Contrato</button>""", height=45)
    with c2:
        st.download_button("📥 Baixar Documento (HTML)", f"<!DOCTYPE html><html><body>{html_final}</body></html>", f"Contrato_{dados_print['contratante_nome']}.html", "text/html", use_container_width=True)
    st.stop()

# -----------------------------------------------------------------------------
# MODO DE EDIÇÃO ISOLADA (Executa apenas ao clicar em "Editar Contrato")
# -----------------------------------------------------------------------------
if "contrato_editar" in st.session_state and st.session_state["contrato_editar"] is not None:
    dados_edit = st.session_state["contrato_editar"]
    
    st.button("⬅️ Cancelar Edição", on_click=lambda: st.session_state.update({"contrato_editar": None}))
    st.subheader(f"✏️ Editando Contrato #{dados_edit['id']}")

    with st.form("form_editar_contrato", clear_on_submit=False):
        
        # 1. Seletor que permite alterar entre Free e Pro
        opcoes_edicao = [
            "Contrato Padrão de Serviços (Gratuito)", 
            "🔒 Contrato Corporativo PRO (Com LGPD, NDA e Multas) - (PRO)"
        ]
        idx_modelo_ed = opcoes_edicao.index(dados_edit['modelo']) if dados_edit['modelo'] in opcoes_edicao else 0
        modelo_escolhido_ed = st.selectbox("Modelo de Contrato:", opcoes_edicao, index=idx_modelo_ed)
        eh_modelo_pro_ed = "PRO" in modelo_escolhido_ed
        
        st.markdown("### 1. Dados do Contratante (Cliente)")
        c_ed1, c_ed2 = st.columns(2)
        contratante_nome_ed = c_ed1.text_input("Empresa/Razão Social do Cliente", value=dados_edit.get('contratante_nome', ''))
        contratante_doc_ed = c_ed2.text_input("CNPJ ou CPF", value=dados_edit.get('contratante_doc', ''))
        
        contratante_end_ed = st.text_input("Logradouro", value=dados_edit.get('contratante_end', ''))
        ce1, ce2, ce3, ce4 = st.columns([3, 3, 1, 2])
        contratante_bairro_ed = ce1.text_input("Bairro", value=dados_edit.get('contratante_bairro', ''))
        contratante_cidade_ed = ce2.text_input("Cidade", value=dados_edit.get('contratante_cidade', ''))
        contratante_uf_ed = ce3.text_input("UF", value=dados_edit.get('contratante_uf', ''), max_chars=2, key="ed_uf_cli")
        contratante_cep_ed = ce4.text_input("CEP", value=dados_edit.get('contratante_cep', ''))
        
        representante_nome_ed = ""
        representante_cpf_ed = ""
        if eh_modelo_pro_ed:
            st.markdown("**Representante Legal:**")
            cr1, cr2 = st.columns(2)
            representante_nome_ed = cr1.text_input("Representante", value=dados_edit.get('representante_nome', ''))
            representante_cpf_ed = cr2.text_input("CPF Representante", value=dados_edit.get('representante_cpf', ''))

        st.markdown("### 2. Dados do Contratado (MEI)")
        endereco_mei_ed = st.text_input("Logradouro (MEI)", value=dados_edit.get('endereco_mei', ''))
        me1, me2, me3, me4 = st.columns([3, 3, 1, 2])
        mei_bairro_ed = me1.text_input("Bairro (MEI)", value=dados_edit.get('mei_bairro', ''))
        mei_cidade_ed = me2.text_input("Cidade (MEI)", value=dados_edit.get('mei_cidade', ''))
        mei_uf_ed = me3.text_input("UF (MEI)", value=dados_edit.get('mei_uf', ''), max_chars=2, key="ed_uf_mei")
        mei_cep_ed = me4.text_input("CEP (MEI)", value=dados_edit.get('mei_cep', ''))

        banco_conta_ed = ""
        chave_pix_ed = ""
        if eh_modelo_pro_ed:
            cb1, cb2 = st.columns(2)
            banco_conta_ed = cb1.text_input("Banco e Conta", value=dados_edit.get('banco_conta', ''))
            chave_pix_ed = cb2.text_input("Chave PIX", value=dados_edit.get('chave_pix', ''))

        st.markdown("### 3. Objeto e Valores")
        objeto_servico_ed = st.text_area("Descrição dos Serviços", value=dados_edit.get('objeto_servico', ''), height=80)
        c_v1, c_v2 = st.columns(2)
        valor_total_ed = c_v1.number_input("Valor Total (R$)", min_value=10.0, value=float(dados_edit.get('valor_total', 2800.0)), step=100.0)
        forma_pagamento_ed = c_v2.text_input("Condição de Pagamento", value=dados_edit.get('forma_pagamento', ''))

        st.markdown("### 4. Prazos e Foro")
        cp1, cp2, cp3 = st.columns(3)
        data_inicio_val = pd.to_datetime(dados_edit['data_inicio']).date()
        data_inicio_ed = cp1.date_input("Data de Início", value=data_inicio_val)
        prazo_vigencia_ed = cp2.number_input("Vigência (Meses)", value=int(dados_edit.get('prazo_vigencia') or 12))
        prazo_aviso_previo_ed = cp3.number_input("Aviso Prévio (Dias)", value=int(dados_edit.get('prazo_aviso_previo') or 60))
        cidade_foro_ed = st.text_input("Cidade (Foro)", value=dados_edit.get('cidade_foro', ''))

        clausulas_extras_ed = ""
        if eh_modelo_pro_ed:
            st.markdown("---")
            texto_cl_antigo = dados_edit.get('clausulas_extras') or ""
            clausulas_extras_ed = st.text_area("✨ Cláusulas Especiais", value=texto_cl_antigo)

        # 2. O comando UPDATE específico para salvar alterações
        if st.form_submit_button("💾 Salvar Alterações no Contrato", type="primary", use_container_width=True):
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE contratos 
                    SET modelo=%s, contratante_nome=%s, contratante_doc=%s, contratante_end=%s, 
                        contratante_bairro=%s, contratante_cidade=%s, contratante_uf=%s, contratante_cep=%s,
                        objeto_servico=%s, valor_total=%s, forma_pagamento=%s, data_inicio=%s, cidade_foro=%s, 
                        clausulas_extras=%s, representante_nome=%s, representante_cpf=%s, endereco_mei=%s,
                        mei_bairro=%s, mei_cidade=%s, mei_uf=%s, mei_cep=%s, 
                        banco_conta=%s, chave_pix=%s, prazo_vigencia=%s, prazo_aviso_previo=%s
                    WHERE id = %s
                """, (
                    modelo_escolhido_ed,
                    contratante_nome_ed, contratante_doc_ed, contratante_end_ed, 
                    contratante_bairro_ed, contratante_cidade_ed, contratante_uf_ed, contratante_cep_ed,
                    objeto_servico_ed, valor_total_ed, forma_pagamento_ed, data_inicio_ed, cidade_foro_ed, 
                    clausulas_extras_ed, representante_nome_ed, representante_cpf_ed, endereco_mei_ed,
                    mei_bairro_ed, mei_cidade_ed, mei_uf_ed, mei_cep_ed,
                    banco_conta_ed, chave_pix_ed, prazo_vigencia_ed, prazo_aviso_previo_ed, 
                    dados_edit['id']
                ))
                conn.commit()
                st.success("✅ Contrato atualizado com sucesso!")
                st.session_state["contrato_editar"] = None
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao atualizar: {e}")
            finally:
                if 'conn' in locals(): conn.close()
                
    st.stop() # Interrompe aqui para não renderizar as abas durante a edição    

# -----------------------------------------------------------------------------
# 4. INTERFACE PRINCIPAL
# -----------------------------------------------------------------------------
st.title("📑 Gestão de Contratos MEI")
st.info(f"👤 Contratado: **{cliente_info['nome']}** | CNPJ/CPF: **{cliente_info['cnpj_cpf']}**")

tab_novo, tab_historico = st.tabs(["📝 Elaborar Novo Contrato", "📂 Meus Contratos Salvos"])

with tab_novo:
    # 1. Adicionamos a opção vazia no início
    opcoes_modelos = [
        "-- Selecione um modelo --",
        "Contrato Padrão de Serviços (Gratuito)", 
        "🔒 Contrato Corporativo PRO (Com LGPD, NDA e Multas) - (PRO)"
    ]
    
    # Se o cliente for PRO, o sistema já "facilita" e seleciona o PRO (Índice 2). Se for Grátis, deixa no "Selecione" (Índice 0)
    idx_padrao_modelo = 2 if cliente_eh_pro else 0
    modelo_escolhido = st.selectbox("Modelo de Contrato:", opcoes_modelos, index=idx_padrao_modelo)
    
    # 2. A trava: Se ele não escolheu nada, exibe o aviso e para de desenhar a tela
    if modelo_escolhido == "-- Selecione um modelo --":
        st.info("👆 Por favor, selecione qual modelo de contrato você deseja gerar para abrir o formulário.")
        st.stop() # O st.stop() esconde tudo daqui pra baixo até ele escolher!
    
    eh_modelo_pro_form = "PRO" in modelo_escolhido
    if eh_modelo_pro_form and not cliente_eh_pro:
        exibir_bloqueio_upgrade()
    else:
        with st.form("form_contrato", clear_on_submit=True):
            st.subheader("1. Dados do Contratante (Cliente)")
            col1, col2 = st.columns(2)
            contratante_nome = col1.text_input("Empresa/Razão Social do Cliente")
            contratante_doc = col2.text_input("CNPJ ou CPF")
            
            st.markdown("**Endereço do Cliente:**")
            contratante_end = st.text_input("Logradouro (Rua, Avenida, Número)")
            c1, c2, c3, c4 = st.columns([3, 3, 1, 2])
            contratante_bairro = c1.text_input("Bairro (Cliente)")
            contratante_cidade = c2.text_input("Cidade (Cliente)")
            contratante_uf = c3.text_input("UF", max_chars=2, key="uf_cliente")
            contratante_cep = c4.text_input("CEP (Cliente)")
            
            representante_nome = ""
            representante_cpf = ""
            if eh_modelo_pro_form:
                st.markdown("**Representante Legal:**")
                c_rep1, c_rep2 = st.columns(2)
                representante_nome = c_rep1.text_input("Nome do Representante Legal (Assinante)")
                representante_cpf = c_rep2.text_input("CPF do Representante")

            st.subheader("2. Dados do Contratado (Seu MEI)")
            st.markdown("**Endereço Profissional (MEI):**")
            endereco_mei = st.text_input("Logradouro (Rua, Avenida, Número) - MEI")
            m1, m2, m3, m4 = st.columns([3, 3, 1, 2])
            mei_bairro = m1.text_input("Bairro (MEI)")
            mei_cidade = m2.text_input("Cidade (MEI)")
            mei_uf = m3.text_input("UF", max_chars=2, key="uf_mei")
            mei_cep = m4.text_input("CEP (MEI)")

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
                                contratante_bairro, contratante_cidade, contratante_uf, contratante_cep,
                                objeto_servico, valor_total, forma_pagamento, data_inicio, cidade_foro, 
                                clausulas_extras, representante_nome, representante_cpf, endereco_mei,
                                mei_bairro, mei_cidade, mei_uf, mei_cep, 
                                banco_conta, chave_pix, prazo_vigencia, prazo_aviso_previo
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
                        """, (
                            cliente_ativo_id, modelo_escolhido, contratante_nome, contratante_doc, contratante_end,
                            contratante_bairro, contratante_cidade, contratante_uf, contratante_cep,
                            objeto_servico, valor_total, forma_pagamento, data_inicio, cidade_foro, 
                            clausulas_extras, representante_nome, representante_cpf, endereco_mei,
                            mei_bairro, mei_cidade, mei_uf, mei_cep,
                            banco_conta, chave_pix, prazo_vigencia, prazo_aviso_previo
                        ))
                        novo_id = cursor.fetchone()[0]
                        conn.commit()
                        
                        st.session_state["contrato_print"] = {
                            'id': novo_id, 'modelo': modelo_escolhido, 'contratante_nome': contratante_nome, 
                            'contratante_doc': contratante_doc, 'contratante_end': contratante_end,
                            'contratante_bairro': contratante_bairro, 'contratante_cidade': contratante_cidade,
                            'contratante_uf': contratante_uf, 'contratante_cep': contratante_cep,
                            'representante_nome': representante_nome, 'representante_cpf': representante_cpf,
                            'endereco_mei': endereco_mei, 'mei_bairro': mei_bairro, 'mei_cidade': mei_cidade,
                            'mei_uf': mei_uf, 'mei_cep': mei_cep, 'banco_conta': banco_conta, 'chave_pix': chave_pix,
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
                st.write(f"**Modelo:** {row.get('modelo', 'Padrão')}")
                st.write(f"**Serviço:** {row['objeto_servico']}")
                
                # Exibe Imprimir e Editar lado a lado
                col_btn1, col_btn2 = st.columns(2)
                if col_btn1.button("🖨️ Ver / Imprimir", key=f"print_{row['id']}", type="primary", use_container_width=True):
                    st.session_state["contrato_print"] = row.to_dict()
                    st.rerun()
                if col_btn2.button("✏️ Editar Contrato", key=f"edit_{row['id']}", use_container_width=True):
                    st.session_state["contrato_editar"] = row.to_dict()
                    st.rerun()