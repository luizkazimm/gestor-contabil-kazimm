import streamlit as st
import pandas as pd
from database import get_connection, init_db

# 1. Configuração da página (DEVE SER O PRIMEIRO COMANDO STREAMLIT)
st.set_page_config(page_title="Gestor Contábil Kazimm", layout="wide")

# --- TRAVA DE SEGURANÇA ---
if 'user' not in st.session_state or st.session_state.user is None:
    st.warning("🔒 Você precisa fazer login para acessar o Gestor Contábil.")
    st.stop()
    
#Título de Inicialização
st.title("Sistema de Gestão Contábil")
init_db()

# 4. Busca os Clientes do Usuário no Banco de Dados
conn = get_connection()
cursor = conn.cursor()
cursor.execute("SELECT id, nome FROM clientes WHERE user_id = %s", (st.session_state.user.id,))
clientes_cadastrados = cursor.fetchall()
conn.close()

# 5. Seletor do Cliente Ativo (Definição na Session State)
if clientes_cadastrados:
    opcoes_clientes = {cli[1]: cli[0] for cli in clientes_cadastrados}

# Barra lateral (sidebar) deixa o seletor visível em qualquer tela
    cliente_selecionado = st.sidebar.selectbox("🏢 Cliente em Atendimento", list(opcoes_clientes.keys()))

# Armazena o ID do cliente selecionado no estado da sessão
    st.session_state.cliente_id_ativo = opcoes_clientes[cliente_selecionado]
else:
    st.session_state.cliente_id_ativo = None
    st.info("Nenhum cliente cadastrado. Cadastre uma empresa para começar os lançamentos.")


def formatar_brl(valor):
    return f"R$ {valor:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")


# Menu Lateral
opcao = st.sidebar.selectbox(
    "Menu Navegação",
    [
        "Cadastrar Cliente",
        "Cadastrar Conta / Fornecedor",
        "Plano de Contas",
        "Novo Lançamento",
        "Importar Extrato / Excel",
        "Ver Lançamentos",
        "Relatório por Categoria",
    ],
)

# BLOCO CADASTRAR CLIENTES
if opcao == "Cadastrar Cliente":
    st.subheader("Cadastro de Clientes")

    # 1. Checa a quantidade de clientes já salvos para o usuário atual
    user_id_atual = st.session_state.user.id
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM clientes WHERE user_id = %s", (user_id_atual,))
    qtd_clientes = cursor.fetchone()[0]
    conn.close()

    # 2. Aplica a trava de 1 cliente
    if qtd_clientes >= 1:
        st.warning("⚠️ Seu plano atual permite o cadastro de apenas **1 cliente**.")
        st.info("Para cadastrar um novo cliente, exclua o registro atual no painel de gerenciamento.")
    else:


        with st.form("form_cliente"):
            col_cli1, col_cli2 = st.columns(2)
            with col_cli1:
                nome = st.text_input("Nome/Razão Social da Empresa")
                cnpj_cpf = st.text_input("CNPJ ou CPF")
            with col_cli2:
                regime = st.selectbox(
                    "Regime Contábil / Modelo de Digitação",
                    [
                        "Partida Dupla (Contabilidade Completa)",
                        "Lançamento Simples (MEI / Livro Caixa)",
                    ],
                )

            salvar = st.form_submit_button("Salvar Cliente")

        if salvar:
            if nome and cnpj_cpf:
                conn = get_connection()
                cursor = conn.cursor()
                try:
                    cursor.execute(
                        "INSERT INTO clientes (nome, cnpj_cpf, regime,user_id) VALUES (%s, %s, %s, %s)",
                        (nome, cnpj_cpf, regime, user_id_atual),
                    )
                    conn.commit()
                    st.success(f"Cliente '{nome}' cadastrado com sucesso no regime {regime}!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: Este CNPJ/CPF já está cadastrado:{e}")
                finally:
                    conn.close()
        #atenção a este campo, ele pode gerar erro    
            else:
                st.warning("Preencha todos os campos obrigatórios.")
            
    st.write("### Cliente Ativo")
    conn = get_connection()
    df_clientes_cad = pd.read_sql_query(
        'SELECT id, nome as "Razão Social", cnpj_cpf as "CNPJ/CPF", regime as "Regime Contábil" FROM clientes WHERE user_id = %s AND id = %s',
        conn,
        params=(st.session_state.user.id, st.session_state.cliente_id_ativo)
    )
    conn.close()

# Bloco de Alteração de REGIME - Simples / Completo (Dashboard)

    if not df_clientes_cad.empty:
        st.dataframe(
            df_clientes_cad.drop(columns=["id"]), use_container_width=True
        )
# =========================================================================
# BLOCOS DESATIVADOS / COMENTADOS PARA LIMPEZA DA INTERFACE (FUTURO DASHBOARD)
# =========================================================================
    
# --- BLOCO 1: ALTERAR REGIME DE CLIENTE EXISTENTE (DESATIVADO) ---
#        st.markdown("---")
#        st.subheader("✏️ Alterar Regime de Cliente Existente")
#
#        dict_cli_edit = dict(
#            zip(df_clientes_cad["Razão Social"], df_clientes_cad["id"])
#        )
#        cli_sel_edit = st.selectbox(
#            "Selecione o Cliente:", list(dict_cli_edit.keys())
#        )
#        id_cli_edit = dict_cli_edit[cli_sel_edit]
#
#        with st.form("form_editar_regime_cliente"):
#            novo_regime = st.selectbox(
#                "Novo Regime Contábil",
#                [
#                    "Lançamento Simples (MEI / Livro Caixa)",
#                    "Partida Dupla (Contabilidade Completa)",
#                ],
#            )
#            salvar_regime = st.form_submit_button(
#                "💾 Atualizar Regime do Cliente"
#            )
#
#            if salvar_regime:
#                conn = get_connection()
#                cursor = conn.cursor()
#                cursor.execute(
#                    "UPDATE clientes SET regime = ? WHERE id = %s",
#                    (novo_regime, id_cli_edit),
#                )
#                conn.commit()
#                conn.close()
#                st.success(
#                    f"Regime de '{cli_sel_edit}' atualizado para {novo_regime}!"
#                )
#
#                st.divider()
    
# --- BLOCO DE EXCLUSÃO DE CLIENTE (CORRIGIDO) ---
#    conn = get_connection()
#    cursor = conn.cursor()
#    cursor.execute("SELECT id, nome FROM clientes WHERE user_id = %s", (st.session_state.user.id,))
#    clientes_cadastrados = cursor.fetchall()
#    conn.close()


# =========================================================================
# BLOCOS DESATIVADOS / COMENTADOS PARA LIMPEZA DA INTERFACE (FUTURO DASHBOARD)
# =========================================================================

#    if clientes_cadastrados:
#        st.divider()
#        st.subheader("🗑️ Excluir Cliente")
#
#        opcoes_clientes = {cli[1]: cli[0] for cli in clientes_cadastrados}
#        cli_sel_edit = st.selectbox("Selecione o cliente para excluir", list(opcoes_clientes.keys()))
#        id_cli_edit = opcoes_clientes[cli_sel_edit]
#
#        with st.form("form_excluir_cliente"):
#            st.warning("⚠️ Atenção: Esta ação é irreversível.")
#            confirmar = st.checkbox(f"Confirmo que desejo excluir o cliente '{cli_sel_edit}'")
#            btn_excluir = st.form_submit_button("Excluir Cliente")
#
#        if btn_excluir:
#            if confirmar:
#                conn = get_connection()
#                cursor = conn.cursor()
#                cursor.execute("DELETE FROM clientes WHERE id = %s", (id_cli_edit,))
#                conn.commit()
#                conn.close()
#                st.success(f"Cliente '{cli_sel_edit}' excluído com sucesso!")
#                st.rerun()
#            else:
#                st.error("Marque a caixa de seleção para confirmar a exclusão.")            

# BLOCO CADASTRAR CONTAS

elif opcao == "Cadastrar Conta / Fornecedor":
    st.subheader("Cadastro de Contas no Plano de Contas / Fornecedores")

    with st.form("form_plano_contas"):
        codigo = st.text_input("Código da Conta", placeholder="Ex: 2.1.1.01.001")
        descricao = st.text_input(
            "Nome da Conta / Fornecedor", placeholder="Ex: Ambev Brasil S.A."
        )
        tipo_conta = st.selectbox(
            "Grupo / Tipo",
            ["Ativo", "Passivo", "Patrimônio Líquido", "Receita", "Despesa"],
        )
        salvar_conta = st.form_submit_button("Cadastrar Conta")

        if salvar_conta:
            if codigo and descricao:
                conn = get_connection()
                cursor = conn.cursor()
                try:
                    cursor.execute(
                        "INSERT INTO plano_contas (codigo, descricao, tipo) VALUES (%s, %s, %s)",
                        (codigo, descricao, tipo_conta)
                    )
                    conn.commit()
                    st.success(f"Conta '{codigo} - {descricao}' inserida com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao cadastrar conta: {e}")
                finally:
                    conn.close()
            else:
                st.error("Preencha o Código e o Nome da Conta.")

    st.markdown("---")
    st.write("### Plano de Contas Atual")
    #Trecho Modificado - 15/09/26 - Visualizar apenas o CLIENTE ativo
    conn = get_connection()
    df_plano = pd.read_sql_query(
        'SELECT id, codigo as "Código", descricao as "Nome da Conta", tipo as "Tipo" FROM plano_contas ORDER BY codigo ASC',
        conn
    )
    conn.close()

    #BLOCO DE EXCLUSÃO - Contas

    if not df_plano.empty:
        st.dataframe(
            df_plano.drop(columns=["id"]), use_container_width=True
        )

        st.markdown("---")
        st.subheader("✏️ Alterar ou Excluir Conta / Fornecedor")

        df_plano["label"] = (
            df_plano["Código"]
            + " - "
            + df_plano["Nome da Conta"]
            + " ("
            + df_plano["Tipo"]
            + ")"
        )
        dict_contas = dict(zip(df_plano["label"], df_plano["id"]))

        conta_selecionada_label = st.selectbox(
            "Selecione a Conta que deseja modificar ou excluir:",
            list(dict_contas.keys()),
        )
        id_conta_sel = dict_contas[conta_selecionada_label]

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT codigo, descricao, tipo FROM plano_contas WHERE id = %s",
            (id_conta_sel,),
        )
        reg_conta = cursor.fetchone()
        conn.close()

        if reg_conta:
            cod_atual, nome_atual, tipo_atual = reg_conta

            with st.form("form_editar_conta"):
                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    novo_codigo = st.text_input(
                        "Código da Conta", value=cod_atual
                    )
                with col_c2:
                    novo_nome = st.text_input(
                        "Nome da Conta / Fornecedor", value=nome_atual
                    )

                tipos_possiveis = [
                    "Ativo",
                    "Passivo",
                    "Patrimônio Líquido",
                    "Receita",
                    "Despesa",
                ]
                idx_tipo = (
                    tipos_possiveis.index(tipo_atual)
                    if tipo_atual in tipos_possiveis
                    else 0
                )
                novo_tipo = st.selectbox(
                    "Grupo / Tipo", tipos_possiveis, index=idx_tipo
                )

                salvar_edicao_conta = st.form_submit_button(
                    "💾 Salvar Alterações"
                )

                if salvar_edicao_conta:
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
                        except Exception:
                            st.error(
                                "Erro: Já existe outra conta cadastrada com esse código."
                            )
                        finally:
                            conn.close()
                    else:
                        st.error("Código e Nome não podem ficar vazios.")

            with st.expander("🗑️ Excluir esta Conta / Fornecedor"):
                st.warning(
                    f"Tem certeza que deseja apagar a conta '{cod_atual} - {nome_atual}'?"
                )
                if st.button(
                    "Confirmar Exclusão da Conta",
                    key=f"del_conta_{id_conta_sel}",
                    type="primary",
                ):
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute(
                        "DELETE FROM plano_contas WHERE id = ?", (id_conta_sel,)
                    )
                    conn.commit()
                    conn.close()
                    st.success("Conta excluída com sucesso!")
                    st.rerun()

#bloco de plano de contas

elif opcao == "Plano de Contas":
    st.subheader("📖 Visualização Estruturada do Plano de Contas")

    conn = get_connection()
    df_plano = pd.read_sql_query(
        'SELECT codigo as "Código", descricao as "Nome da Conta", tipo as "Grupo / Tipo" FROM plano_contas ORDER BY codigo ASC',
        conn,
    )
    conn.close()

    if df_plano.empty:
        st.info("Nenhuma conta cadastrada.")
    else:
        busca = st.text_input(
            "🔍 Buscar Conta por Código ou Nome", placeholder="Ex: Estoque ou 1.1.3"
        )
        if busca:
            df_plano = df_plano[
                df_plano["Código"].str.contains(busca, case=False)
                | df_plano["Nome da Conta"].str.contains(busca, case=False)
            ]

        tab_geral, tab_ativo, tab_passivo, tab_receitas, tab_despesas = st.tabs(
            [
                "📋 Visão Geral Completa",
                "🟢 1. Ativo",
                "🔴 2. Passivo & PL",
                "🔵 3. Receitas",
                "🟠 4. Despesas",
            ]
        )

        with tab_geral:
            st.dataframe(df_plano, use_container_width=True, height=450)

        with tab_ativo:
            st.markdown("#### **Grupo 1 - ATIVO (Bens e Direitos)**")
            st.dataframe(
                df_plano[df_plano["Grupo / Tipo"] == "Ativo"],
                use_container_width=True,
            )

        with tab_passivo:
            st.markdown(
                "#### **Grupo 2 - PASSIVO E PATRIMÔNIO LÍQUIDO (Obrigações e Capital)**"
            )
            st.dataframe(
                df_plano[
                    df_plano["Grupo / Tipo"].isin(
                        ["Passivo", "Patrimônio Líquido"]
                    )
                ],
                use_container_width=True,
            )

        with tab_receitas:
            st.markdown(
                "#### **Grupo 3 - RECEITAS (Faturamento da Operação)**"
            )
            st.dataframe(
                df_plano[df_plano["Grupo / Tipo"] == "Receita"],
                use_container_width=True,
            )

        with tab_despesas:
            st.markdown(
                "#### **Grupo 4 - DESPESAS (Gastos Operacionais)**"
            )
            st.dataframe(
                df_plano[df_plano["Grupo / Tipo"] == "Despesa"],
                use_container_width=True,
            )

        csv_plano = df_plano.to_csv(index=False, sep=";", decimal=",").encode(
            "utf-8-sig"
        )
        st.download_button(
            label="📥 Baixar Plano de Contas em Excel (.csv)",
            data=csv_plano,
            file_name="plano_de_contas.csv",
            mime="text/csv",
        )
#BLOCO DE LANÇAMENTOS - Novo lançamento

elif opcao == "Novo Lançamento":
    st.subheader("Registro de Lançamento Contábil")
    conn = get_connection()
    df_clientes = pd.read_sql_query("SELECT id, nome, regime FROM clientes", conn)
    df_contas = pd.read_sql_query(
        "SELECT codigo, descricao, tipo FROM plano_contas ORDER BY codigo ASC", conn
    )
    df_fornecedores_cad = pd.read_sql_query(
        """SELECT descricao FROM plano_contas WHERE tipo = 'Passivo' OR codigo LIKE '2.1.1%' ORDER BY descricao ASC""",
        conn,
    )
    conn.close()

    if df_clientes.empty:
        st.warning(
            "Nenhum cliente encontrado. Cadastre um cliente primeiro no menu ao lado."
        )
    else:
        dict_clientes_id = dict(zip(df_clientes["nome"], df_clientes["id"]))
        dict_clientes_regime = dict(
            zip(df_clientes["nome"], df_clientes["regime"])
        )

        cliente_selecionado = st.selectbox(
            "Selecione o Cliente", list(dict_clientes_id.keys())
        )
        regime_cliente = dict_clientes_regime[cliente_selecionado]

        st.info(f"📋 Modelo de Digitação Ativo: **{regime_cliente}**")

        plano_de_contas_full = [""] + [
            f"{row['codigo']} - {row['descricao']}"
            for _, row in df_contas.iterrows()
        ]

        estabelecimentos_frequentes = [
            "-- Digitar Outro / Nenhum --",
            "Supermercado Guanabara",
            "Supermarket",
            "Atacadão",
            "Assaí Atacadista",
            "Ambev",
            "Coca-Cola Femsa",
            "Grupo Petrópolis",
            "Heineken Brasil",
            "Drogaria Pacheco",
            "Droga Raia",
        ]

        for forn in df_fornecedores_cad["descricao"]:
            if forn not in estabelecimentos_frequentes:
                estabelecimentos_frequentes.append(forn)

        with st.form("form_lancamento", clear_on_submit=True):
            data = st.date_input("Data do Lançamento", format="DD/MM/YYYY")

            c_doc1, c_doc2, c_doc3 = st.columns(3)
            with c_doc1:
                tipo_doc = st.selectbox(
                    "Tipo de Documento",
                    [
                        "Cupom Fiscal (NFC-e)",
                        "Nota Fiscal (NF-e)",
                        "Recibo / Comprovante",
                        "Extrato / PIX",
                        "Sem Documento",
                    ],
                )
            with c_doc2:
                num_doc = st.text_input(
                    "Nº do Documento (Opcional)", placeholder="Ex: 1054"
                )
            with c_doc3:
                estab_sel = st.selectbox(
                    "Estabelecimento Recorrente", estabelecimentos_frequentes
                )
                estab_manual = st.text_input(
                    "Se 'Outro', digite aqui:", placeholder="Ex: Hortifruti do Zé"
                )

            estabelecimento = (
                estab_manual
                if estab_sel == "-- Digitar Outro / Nenhum --"
                else estab_sel
            )

            # Interface dinâmicamente ajustada para o Regime do Cliente
            if "Lançamento Simples" in regime_cliente:
                st.markdown("---")
                st.write("##### ⚡ Preenchimento Simplificado (Livro Caixa / MEI)")
                tipo_operacao = st.radio(
                    "Tipo de Lançamento",
                    ["(+) Entrada / Receita", "(-) Saída / Despesa ou Estoque"],
                    horizontal=True,
                )

                contas_disponiveis = (
                    df_contas[df_contas["tipo"] == "Receita"]
                    if "(+) Entrada" in tipo_operacao
                    else df_contas[df_contas["tipo"].isin(["Despesa", "Ativo"])]
                )

                opcoes_categoria = [""] + [
                    f"{row['codigo']} - {row['descricao']}"
                    for _, row in contas_disponiveis.iterrows()
                ]

                col_s1, col_s2 = st.columns(2)
                with col_s1:
                    conta_financeira = st.selectbox(
                        "Forma de Pagamento / Movimentação",
                        [
                            "1.1.1.01 - Caixa Geral",
                            "1.1.1.02 - Banco Conta Movimento",
                        ],
                    )
                with col_s2:
                    categoria_selecionada = st.selectbox(
                        "Categoria da Operação", opcoes_categoria
                    )

                if "(+) Entrada" in tipo_operacao:
                    conta_debito = conta_financeira
                    conta_credito = categoria_selecionada
                else:
                    conta_debito = categoria_selecionada
                    conta_credito = conta_financeira
            else:
                st.markdown("---")
                st.write("##### 🔄 Preenchimento por Partida Dupla")
                col1, col2 = st.columns(2)
                with col1:
                    conta_debito = st.selectbox(
                        "Conta Débito", plano_de_contas_full
                    )
                with col2:
                    conta_credito = st.selectbox(
                        "Conta Crédito", plano_de_contas_full
                    )

            valor = st.number_input(
                "Valor (R$)", min_value=0.00, step=0.01, format="%.2f"
            )

            historicos_padrao = [
                "Digitar Histórico do Zero",
                "Compra de material de limpeza e consumo conf.",
                "Compra de bebidas/estoque p/ revenda conf.",
                "Compra de ingredientes e insumos p/ refeições conf.",
                "Compra de embalagens e descartáveis conf.",
                "Venda diária de mercadorias conf.",
                "Pagamento de frete/carreto p/ entrega de bebidas conf.",
                "Troca / Aquisição de garrafas e vasilhames retornáveis conf.",
                "Pagamento de taxa de máquina de cartão ref. ao período",
            ]

            hist_selecionado = st.selectbox(
                "Histórico Padrão", historicos_padrao
            )
            complemento_hist = st.text_input(
                "Complemento / Detalhes do Histórico",
                placeholder="Ex: Aquisição de carnes e legumes para marmitas",
            )

            salvar_lanc = st.form_submit_button("Registrar Lançamento")

            if salvar_lanc:
                if conta_debito and conta_credito and valor > 0:
                    info_doc = tipo_doc
                    if num_doc.strip():
                        info_doc += f" nº {num_doc.strip()}"
                    if estabelecimento.strip():
                        info_doc += f" - {estabelecimento.strip()}"

                    doc_str = f"[{info_doc}]"

                    if hist_selecionado == "Digitar Histórico do Zero":
                        historico_final = f"{doc_str} {complemento_hist}".strip()
                    else:
                        historico_final = f"{doc_str} {hist_selecionado} {complemento_hist}".strip()

                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute(
                        """
                        INSERT INTO lancamentos (cliente_id, data, conta_debito, conta_credito, valor, historico)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                        (
                            dict_clientes_id[cliente_selecionado],
                            str(data),
                            conta_debito,
                            conta_credito,
                            valor,
                            historico_final,
                        ),
                    )
                    conn.commit()
                    conn.close()
                    st.success("Lançamento registrado com sucesso!")
                else:
                    st.error(
                        "Selecione a categoria / contas contábeis e insira um valor válido maior que zero."
                    )
#bloco de imprtação de extratos

elif opcao == "Importar Extrato / Excel":
    st.subheader("📥 Importação de Lançamentos em Lote (Excel / CSV)")

    conn = get_connection()
    clientes = pd.read_sql_query("SELECT id, nome FROM clientes", conn)
    df_contas = pd.read_sql_query(
        "SELECT codigo, descricao FROM plano_contas ORDER BY codigo ASC", conn
    )
    conn.close()

    if clientes.empty:
        st.warning(
            "Nenhum cliente cadastrado. Cadastre um cliente antes de importar."
        )
    else:
        dict_clientes = dict(zip(clientes["nome"], clientes["id"]))
        cliente_import = st.selectbox(
            "Selecione o Cliente para Importação", list(dict_clientes.keys())
        )

        arquivo = st.file_uploader(
            "Envie o arquivo do extrato ou planilha (.csv ou .xlsx)",
            type=["csv", "xlsx"],
        )

        if arquivo is not None:
            try:
                if arquivo.name.endswith(".csv"):
                    df_imp = pd.read_csv(arquivo, sep=None, engine="python")
                else:
                    df_imp = pd.read_excel(arquivo)

                st.write("### Pré-visualização do Arquivo Enviado:")
                st.dataframe(df_imp.head(5), use_container_width=True)

                st.markdown("---")
                st.subheader("Mapeamento das Colunas")

                colunas = list(df_imp.columns)
                col_data = st.selectbox("Coluna da Data", colunas)
                col_valor = st.selectbox("Coluna do Valor", colunas)
                col_hist = st.selectbox("Coluna do Histórico / Descrição", colunas)

                plano_de_contas = [""] + [
                    f"{row['codigo']} - {row['descricao']}"
                    for _, row in df_contas.iterrows()
                ]

                col_deb, col_cred = st.columns(2)
                with col_deb:
                    conta_deb_padrao = st.selectbox(
                        "Conta Débito Padrão para este arquivo", plano_de_contas
                    )
                with col_cred:
                    conta_cred_padrao = st.selectbox(
                        "Conta Crédito Padrão para este arquivo", plano_de_contas
                    )

                if st.button("🚀 Processar e Salvar Importação"):
                    if conta_deb_padrao and conta_cred_padrao:
                        conn = get_connection()
                        cursor = conn.cursor()
                        qtd = 0

                        for _, row in df_imp.iterrows():
                            dt_val = str(pd.to_datetime(row[col_data]).date())
                            val_raw = (
                                float(
                                    str(row[col_valor])
                                    .replace("R$", "")
                                    .replace(".", "")
                                    .replace(",", ".")
                                )
                                if isinstance(row[col_valor], str)
                                else float(row[col_valor])
                            )
                            val_abs = abs(val_raw)
                            hist_val = f"[Importado] {str(row[col_hist])}"

                            cursor.execute(
                                """
                                INSERT INTO lancamentos (cliente_id, data, conta_debito, conta_credito, valor, historico)
                                VALUES (%s, %s, %s, %s, %s, %s)
                            """,
                                (
                                    dict_clientes[cliente_import],
                                    dt_val,
                                    conta_deb_padrao,
                                    conta_cred_padrao,
                                    val_abs,
                                    hist_val,
                                ),
                            )
                            qtd += 1

                        conn.commit()
                        conn.close()
                        st.success(
                            f"{qtd} lançamentos importados com sucesso para {cliente_import}!"
                        )
                    else:
                        st.error("Selecione as contas de Débito e Crédito padrão.")
            except Exception as e:
                st.error(
                    f"Erro ao ler o arquivo. Verifique se o formato está correto: {e}"
                )
# BLOCO VERIFICAÇÃO DE LANÇAMENTOS
elif opcao == "Ver Lançamentos":
    st.subheader("Consulta e Relatório de Lançamentos")
    conn = get_connection()
    clientes = pd.read_sql_query("SELECT id, nome FROM clientes", conn)

    if clientes.empty:
        st.info("Nenhum cliente cadastrado.")
        conn.close()
    else:
        opcoes_clientes = ["Todos"] + list(clientes["nome"])
        cliente_filtro = st.selectbox("Filtrar por Cliente", opcoes_clientes)

        if cliente_filtro == "Todos":
            query = """
                SELECT 
                    l.id as "ID",
                    c.nome as "Cliente", 
                    l.data as "Data", 
                    l.conta_debito as "Conta Débito", 
                    l.conta_credito as "Conta Crédito", 
                    l.valor as "Valor", 
                    l.historico as "Histórico"
                FROM lancamentos l
                JOIN clientes c ON l.cliente_id = c.id
                ORDER BY l.data DESC, l.id DESC
            """
            df = pd.read_sql_query(query, conn)
        else:
            cliente_id = dict(zip(clientes["descricao"], clientes["id"]))[
                cliente_filtro
            ]
            query = """
                SELECT 
                    l.id as "ID",
                    c.nome as "Cliente", 
                    l.data as "Data", 
                    l.conta_debito as "Conta Débito", 
                    l.conta_credito as "Conta Crédito", 
                    l.valor as "Valor", 
                    l.historico as "Histórico"
                FROM lancamentos l
                JOIN clientes c ON l.cliente_id = c.id
                WHERE l.cliente_id = ?
                ORDER BY l.data DESC, l.id DESC
            """
            df = pd.read_sql_query(query, conn, params=(cliente_id,))

        conn.close()

        if df.empty:
            st.warning("Nenhum lançamento encontrado para este cliente.")
        else:
            df_exibicao = df.copy()
            df_exibicao["Data"] = pd.to_datetime(df_exibicao["Data"]).dt.strftime(
                "%d/%m/%Y"
            )
            df_exibicao["Valor"] = df_exibicao["Valor"].apply(formatar_brl)

            st.dataframe(df_exibicao, use_container_width=True)

            csv_data = df.to_csv(index=False, sep=";", decimal=",").encode(
                "utf-8-sig"
            )
            st.download_button(
                label="📥 Baixar Lançamentos em Excel (.csv)",
                data=csv_data,
                file_name=f"lancamentos_{cliente_filtro.lower().replace(' ', '_')}.csv",
                mime="text/csv",
            )

            st.markdown("---")
            st.subheader("✏️ Alterar ou Excluir Lançamento")

            df_opcoes = df_exibicao.copy()
            df_opcoes["label"] = (
                "ID "
                + df_opcoes["ID"].astype(str)
                + " | "
                + df_opcoes["Data"]
                + " | "
                + df_opcoes["Valor"]
                + " | "
                + df_opcoes["Histórico"].str.slice(0, 35)
            )

            dict_lancamentos = dict(zip(df_opcoes["label"], df_opcoes["ID"]))
            opcao_edit = st.selectbox(
                "Selecione o Lançamento que deseja modificar:",
                list(dict_lancamentos.keys()),
            )
            id_selecionado = dict_lancamentos[opcao_edit]

            conn = get_connection()
            c = conn.cursor()
            c.execute(
                "SELECT data, conta_debito, conta_credito, valor, historico FROM lancamentos WHERE id = %s",
                (id_selecionado,),
            )
            reg_atual = c.fetchone()

            df_contas = pd.read_sql_query(
                "SELECT codigo, nome FROM plano_contas ORDER BY codigo ASC", conn
            )
            conn.close()

            plano_de_contas = [""] + [
                f"{row['codigo']} - {row['descricao']}"
                for _, row in df_contas.iterrows()
            ]

            if reg_atual:
                data_db, debito_db, credito_db, valor_db, hist_db = reg_atual

                with st.form("form_editar_lancamento"):
                    col_ed1, col_ed2 = st.columns(2)
                    with col_ed1:
                        dt_val = pd.to_datetime(data_db).date()
                        nova_data = st.date_input(
                            "Data", value=dt_val, format="DD/MM/YYYY"
                        )
                    with col_ed2:
                        novo_valor = st.number_input(
                            "Valor (R$)",
                            value=float(valor_db),
                            min_value=0.01,
                            step=0.01,
                            format="%.2f",
                        )

                    idx_deb = (
                        plano_de_contas.index(debito_db)
                        if debito_db in plano_de_contas
                        else 0
                    )
                    idx_cred = (
                        plano_de_contas.index(credito_db)
                        if credito_db in plano_de_contas
                        else 0
                    )

                    col_c1, col_c2 = st.columns(2)
                    with col_c1:
                        nova_conta_debito = st.selectbox(
                            "Conta Débito", plano_de_contas, index=idx_deb
                        )
                    with col_c2:
                        nova_conta_credito = st.selectbox(
                            "Conta Crédito", plano_de_contas, index=idx_cred
                        )

                    novo_historico = st.text_area(
                        "Histórico Completo", value=hist_db
                    )

                    salvar_alteracao = st.form_submit_button(
                        "💾 Salvar Alterações"
                    )

                    if salvar_alteracao:
                        if (
                            nova_conta_debito
                            and nova_conta_credito
                            and novo_valor > 0
                        ):
                            conn = get_connection()
                            cursor = conn.cursor()
                            cursor.execute(
                                """
                                UPDATE lancamentos 
                                SET data = %s, conta_debito = %s, conta_credito = %s, valor = %s, historico = %s
                                WHERE id = %s
                            """,
                                (
                                    str(nova_data),
                                    nova_conta_debito,
                                    nova_conta_credito,
                                    novo_valor,
                                    novo_historico,
                                    id_selecionado,
                                ),
                            )
                            conn.commit()
                            conn.close()
                            st.success(
                                f"Lançamento ID {id_selecionado} atualizado com sucesso!"
                            )
                            st.rerun()
                        else:
                            st.error(
                                "Selecione as contas contábeis e informe um valor válido."
                            )

                with st.expander("🗑️ Excluir este Lançamento"):
                    st.warning(
                        f"Você tem certeza que deseja apagar o lançamento ID {id_selecionado}?"
                    )
                    if st.button(
                        "Confirmar Exclusão",
                        key=f"del_{id_selecionado}",
                        type="primary",
                    ):
                        conn = get_connection()
                        cursor = conn.cursor()
                        cursor.execute(
                            "DELETE FROM lancamentos WHERE id = %s",
                            (id_selecionado,),
                        )
                        conn.commit()
                        conn.close()
                        st.success(
                            f"Lançamento ID {id_selecionado} excluído com sucesso!"
                        )
                        st.rerun()

# BLOCO GERAR RELATÓRIOS

elif opcao == "Relatório por Categoria":
    st.subheader("📊 Relatório Agrupado por Conta / Categoria")

    conn = get_connection()
    clientes = pd.read_sql_query("SELECT id, nome FROM clientes", conn)

    if clientes.empty:
        st.info("Nenhum cliente cadastrado.")
        conn.close()
    else:
        opcoes_clientes = ["Todos"] + list(clientes["nome"])
        cliente_filtro = st.selectbox("Filtrar por Cliente", opcoes_clientes)

        if cliente_filtro == "Todos":
            query = "SELECT conta_debito, conta_credito, valor FROM lancamentos"
            df = pd.read_sql_query(query, conn)
        else:
            cliente_id = dict(zip(clientes["nome"], clientes["id"]))[
                cliente_filtro
            ]
            query = "SELECT conta_debito, conta_credito, valor FROM lancamentos WHERE cliente_id = %s"
            df = pd.read_sql_query(query, conn, params=(cliente_id,))

        conn.close()

        if df.empty:
            st.warning("Nenhum lançamento registrado para exibir no relatório.")
        else:
            df_deb = (
                df.groupby("conta_debito")["valor"]
                .sum()
                .reset_index()
                .rename(
                    columns={
                        "conta_debito": "Conta / Categoria",
                        "valor": "Total Débitos (Entradas / Despesas)",
                    }
                )
            )

            df_cred = (
                df.groupby("conta_credito")["valor"]
                .sum()
                .reset_index()
                .rename(
                    columns={
                        "conta_credito": "Conta / Categoria",
                        "valor": "Total Créditos (Saídas / Origens)",
                    }
                )
            )

            df_resumo = pd.merge(
                df_deb, df_cred, on="Conta / Categoria", how="outer"
            ).fillna(0)

            df_resumo_exibicao = df_resumo.copy()
            df_resumo_exibicao["Total Débitos (Entradas / Despesas)"] = df_resumo[
                "Total Débitos (Entradas / Despesas)"
            ].apply(formatar_brl)
            df_resumo_exibicao["Total Créditos (Saídas / Origens)"] = df_resumo[
                "Total Créditos (Saídas / Origens)"
            ].apply(formatar_brl)

            st.dataframe(df_resumo_exibicao, use_container_width=True)

            csv_resumo = df_resumo.to_csv(index=False, sep=";", decimal=",").encode(
                "utf-8-sig"
            )
            st.download_button(
                label="📥 Baixar Relatório por Categoria em Excel (.csv)",
                data=csv_resumo,
                file_name="relatorio_por_categoria.csv",
                mime="text/csv",
            )
