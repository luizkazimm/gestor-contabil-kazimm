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
        "Novo Lançamento",
        "Provisões (Contas a Pagar)",  # <-- NOVO MENU ADICIONADO AQUI
        "Importar Extrato / Excel",
        "Ver Lançamentos",
        "Plano de Contas",
        "Relatório por Categoria"
    ]
)
# BLOCO CADASTRAR / GERENCIAR CLIENTES (PAINEL DO ADMINISTRADOR)
if opcao == "Cadastrar Cliente":
    st.subheader("🏢 Gestão do Cliente & Dashboard MEI")

    user_id_atual = st.session_state.user.id
    cliente_ativo_id = st.session_state.get("cliente_id_ativo")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM clientes WHERE user_id = %s", (user_id_atual,))
    qtd_clientes = cursor.fetchone()[0]
    conn.close()

    # IF 1: PRIMEIRO ACESSO (SEM NENHUM CLIENTE NO BANCO)
    if qtd_clientes < 1:
        st.info("👋 Bem-vindo, Administrador! Cadastre a primeira empresa para ativar o sistema.")
        with st.form("form_cliente_inicial"):
            col_cli1, col_cli2 = st.columns(2)
            with col_cli1:
                nome = st.text_input("Nome / Razão Social")
                cnpj_cpf = st.text_input("CNPJ ou CPF")
                telefone = st.text_input("Telefone de Contato", placeholder="(00) 00000-0000")
            with col_cli2:
                regime = st.selectbox("Regime Contábil", ["MEI (Microempreendedor Individual)", "Simples Nacional"])
                limite_fat = st.selectbox("Limite de Faturamento Anual", [81000.00, 246000.00], format_func=lambda x: f"R$ {x:,.2f} (MEI Geral)" if x == 81000 else f"R$ {x:,.2f} (MEI Caminhoneiro)")
                cnae = st.text_input("Código de Atividade (CNAE)", placeholder="Ex: 47.12-1-00")

            salvar = st.form_submit_button("💾 Cadastrar Primeira Empresa", use_container_width=True)

        if salvar:
            if nome and cnpj_cpf:
                conn = get_connection()
                cursor = conn.cursor()
                try:
                    cursor.execute(
                        """
                        INSERT INTO clientes (nome, cnpj_cpf, regime, limite_faturamento, telefone, cnae_atividade, user_id) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                        (nome, cnpj_cpf, regime, limite_fat, telefone, cnae, user_id_atual),
                    )
                    conn.commit()
                    st.success(f"Empresa '{nome}' cadastrada com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao cadastrar: {e}")
                finally:
                    conn.close()
            else:
                st.warning("Preencha a Razão Social e o CNPJ/CPF.")

    # DASHBOARD + PAINEL DE CONTROLE DO ADMINISTRADOR
    else:
        conn = get_connection()
        try:
            df_clientes_cad = pd.read_sql_query(
                """
                SELECT 
                    id, 
                    nome as "Razão Social", 
                    cnpj_cpf as "CNPJ/CPF", 
                    regime as "Regime Contábil",
                    COALESCE(limite_faturamento, 81000.00) as "Limite Faturamento (R$)",
                    COALESCE(telefone, '-') as "Telefone",
                    COALESCE(cnae_atividade, '-') as "CNAE / Atividade"
                FROM clientes 
                WHERE user_id = %s AND id = %s
                """,
                conn,
                params=(user_id_atual, cliente_ativo_id),
            )
        except Exception:
            df_clientes_cad = pd.read_sql_query(
                "SELECT id, nome as 'Razão Social', cnpj_cpf as 'CNPJ/CPF', regime as 'Regime Contábil', 81000.00 as 'Limite Faturamento (R$)', '-' as 'Telefone', '-' as 'CNAE / Atividade' FROM clientes WHERE user_id = %s AND id = %s",
                conn,
                params=(user_id_atual, cliente_ativo_id),
            )

        df_lancamentos = pd.read_sql_query(
            "SELECT data, conta_debito, conta_credito, valor, historico FROM lancamentos WHERE cliente_id = %s",
            conn,
            params=(cliente_ativo_id,),
        )
        conn.close()

        # 1. FICHA TÉCNICA DO CLIENTE ATIVO
        if not df_clientes_cad.empty:
            row_cli = df_clientes_cad.iloc[0]
            with st.container(border=True):
                st.caption("📋 Ficha Cadastral do Cliente Ativo")
                col_c1, col_c2, col_c3 = st.columns([2, 1.5, 1.5])
                with col_c1:
                    st.write(f"**Empresa:** {row_cli['Razão Social']}")
                    st.write(f"**CNPJ/CPF:** {row_cli['CNPJ/CPF']}")
                with col_c2:
                    st.write(f"**Regime:** {row_cli['Regime Contábil']}")
                    st.write(f"**Telefone:** {row_cli['Telefone']}")
                with col_c3:
                    st.write(f"**CNAE:** {row_cli['CNAE / Atividade']}")
                    limite_val = float(row_cli['Limite Faturamento (R$)']) if row_cli['Limite Faturamento (R$)'] else 81000.0
                    st.write(f"**Teto MEI:** {formatar_brl(limite_val)}")

        st.divider()

        # 2. PAINEL DE METRICAS (KPIS)
        st.subheader("📊 Painel de Controle Financeiro (MEI)")
        if df_lancamentos.empty:
            st.info("💡 Nenhum lançamento encontrado no momento.")
        else:
            mask_entrada = df_lancamentos["conta_debito"].str.contains("1.1.1", na=False) & ~df_lancamentos["conta_credito"].str.contains("1.1.1", na=False)
            mask_saida = df_lancamentos["conta_credito"].str.contains("1.1.1", na=False) & ~df_lancamentos["conta_debito"].str.contains("1.1.1", na=False)

            total_receitas = df_lancamentos[mask_entrada]["valor"].sum() if any(mask_entrada) else 0.0
            total_despesas = df_lancamentos[mask_saida]["valor"].sum() if any(mask_saida) else 0.0

            if total_receitas == 0 and total_despesas == 0:
                total_receitas = df_lancamentos[df_lancamentos["conta_credito"].str.contains("3\.|Receita", case=False, na=False)]["valor"].sum()
                total_despesas = df_lancamentos[df_lancamentos["conta_debito"].str.contains("4\.|Despesa|Estoque", case=False, na=False)]["valor"].sum()

            saldo_liquido = total_receitas - total_despesas

            conn_prov = get_connection()
            cursor_prov = conn_prov.cursor()
            cursor_prov.execute("SELECT COALESCE(SUM(valor), 0.0) FROM provisoes WHERE cliente_id = %s AND status = 'Pendente'", (cliente_ativo_id,))
            res_provisao = cursor_prov.fetchone()
            total_a_pagar = float(res_provisao[0]) if res_provisao else 0.0
            conn_prov.close()

            with st.container(border=True):
                st.caption("💡 Resumo Financeiro & Compromissos")
                c_kpi1, c_kpi2, c_kpi3, c_kpi4 = st.columns(4)
                c_kpi1.metric("🟢 Receita Realizada", formatar_brl(total_receitas))
                c_kpi2.metric("🔴 Despesas Pagas", formatar_brl(total_despesas))
                c_kpi3.metric("⚖️ Saldo em Caixa", formatar_brl(saldo_liquido))
                c_kpi4.metric("🟡 A Pagar (Provisões)", formatar_brl(total_a_pagar))

            st.divider()

            # TETO MEI
            limite_mei = float(df_clientes_cad.iloc[0]["Limite Faturamento (R$)"]) if not df_clientes_cad.empty and df_clientes_cad.iloc[0]["Limite Faturamento (R$)"] else 81000.00
            st.write(f"##### 🎯 Acompanhamento do Limite Anual MEI (Teto: {formatar_brl(limite_mei)})")
            percentual_mei = min(total_receitas / limite_mei, 1.0)
            percentual_real = (total_receitas / limite_mei) * 100

            col_m1, col_m2 = st.columns([3, 1])
            with col_m1:
                st.progress(percentual_mei)
                st.caption(f"Faturado: **{formatar_brl(total_receitas)}** de **{formatar_brl(limite_mei)}** ({percentual_real:.1f}%)")
            with col_m2:
                if percentual_real < 80:
                    st.success("🟢 Faturamento Regular")
                elif percentual_real <= 100:
                    st.warning("🟡 Atenção: Próximo ao Limite!")
                else:
                    st.error("🔴 Alerta: Limite Ultrapassado!")

            st.divider()
            st.write("##### 📌 Despesas por Categoria")
            df_despesas_cat = df_lancamentos[mask_saida].copy()
            if df_despesas_cat.empty:
                df_despesas_cat = df_lancamentos[df_lancamentos["conta_debito"].str.contains("4\.|Despesa", case=False, na=False)].copy()

            if not df_despesas_cat.empty:
                df_grafico = df_despesas_cat.groupby("conta_debito")["valor"].sum().reset_index()
                df_grafico.columns = ["Categoria / Fornecedor", "Valor"]
                df_grafico = df_grafico.sort_values(by="Valor", ascending=False)

                try:
                    import plotly.express as px
                    fig = px.pie(df_grafico, names="Categoria / Fornecedor", values="Valor", hole=0.4, color_discrete_sequence=px.colors.qualitative.Set3)
                    fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=300)
                    st.plotly_chart(fig, use_container_width=True)
                except ImportError:
                    st.bar_chart(df_grafico.set_index("Categoria / Fornecedor"))

        # -----------------------------------------------------------------
        # 3. FERRAMENTAS DO ADMINISTRADOR (EXIBIDO APENAS PARA O CONTADOR)
        # -----------------------------------------------------------------
        # Insira aqui os e-mails com permissão total no sistema
        EMAILS_ADMIN = [
            "luizcasemiro@kazimm.com.br","luizti.kazimm@gmail.com"  # Seu e-mail de Administrador
        ]

        # A aba só será desenhada na tela se o e-mail logado estiver na lista acima
        if st.session_state.user.email in EMAILS_ADMIN:
            st.divider()
            with st.expander("⚙️ Painel de Administração de Clientes (Exclusivo Contador)", expanded=False):
                tab_edit, tab_novo, tab_usuario, tab_lista = st.tabs(["✏️ Editar Cliente Ativo", "➕ Cadastrar Novo Cliente", "👤 Criar Acesso (Login)", "📋 Carteira de Clientes"])

                # ABA 1: EDITAR CLIENTE SELECIONADO
                with tab_edit:
                    if not df_clientes_cad.empty:
                        row_edit = df_clientes_cad.iloc[0]
                        with st.form("form_editar_cliente_admin"):
                            st.markdown(f"##### Alterar dados de: **{row_edit['Razão Social']}**")
                            col_e1, col_e2 = st.columns(2)
                            with col_e1:
                                e_nome = st.text_input("Razão Social / Nome", value=str(row_edit['Razão Social']))
                                e_cnpj = st.text_input("CNPJ / CPF", value=str(row_edit['CNPJ/CPF']))
                                e_tel = st.text_input("Telefone", value=str(row_edit['Telefone']))
                            with col_e2:
                                e_regime = st.selectbox("Regime Contábil", ["MEI (Microempreendedor Individual)", "Simples Nacional"], index=0 if "MEI" in str(row_edit['Regime Contábil']) else 1)
                                lim_atual = float(row_edit['Limite Faturamento (R$)']) if row_edit['Limite Faturamento (R$)'] else 81000.0
                                e_limite = st.selectbox("Limite Faturamento", [81000.00, 246000.00], index=0 if lim_atual == 81000 else 1, format_func=lambda x: f"R$ {x:,.2f} (MEI Geral)" if x == 81000 else f"R$ {x:,.2f} (MEI Caminhoneiro)")
                                e_cnae = st.text_input("CNAE", value=str(row_edit['CNAE / Atividade']))

                            btn_atualizar = st.form_submit_button("💾 Salvar Alterações do Cliente", use_container_width=True)

                            if btn_atualizar:
                                conn_up = get_connection()
                                cursor_up = conn_up.cursor()
                                cursor_up.execute(
                                    """
                                    UPDATE clientes 
                                    SET nome = %s, cnpj_cpf = %s, regime = %s, limite_faturamento = %s, telefone = %s, cnae_atividade = %s
                                    WHERE id = %s AND user_id = %s
                                    """,
                                    (e_nome, e_cnpj, e_regime, e_limite, e_tel, e_cnae, cliente_ativo_id, user_id_atual)
                                )
                                conn_up.commit()
                                conn_up.close()
                                st.success("Dados do cliente atualizados!")
                                st.rerun()

                # ABA 2: CADASTRAR UM NOVO CLIENTE NA CARTEIRA
                with tab_novo:
                    with st.form("form_novo_cliente_admin"):
                        st.markdown("##### Adicionar Novo MEI à sua Carteira")
                        col_n1, col_n2 = st.columns(2)
                        with col_n1:
                            n_nome = st.text_input("Razão Social")
                            n_cnpj = st.text_input("CNPJ ou CPF")
                            n_tel = st.text_input("Telefone")
                        with col_n2:
                            n_regime = st.selectbox("Regime", ["MEI (Microempreendedor Individual)", "Simples Nacional"], key="n_reg")
                            n_limite = st.selectbox("Limite Faturamento", [81000.00, 246000.00], key="n_lim", format_func=lambda x: f"R$ {x:,.2f} (MEI Geral)" if x == 81000 else f"R$ {x:,.2f} (MEI Caminhoneiro)")
                            n_cnae = st.text_input("CNAE / Atividade")

                        btn_cad_novo = st.form_submit_button("➕ Adicionar Empresa", use_container_width=True)

                        if btn_cad_novo:
                            if n_nome and n_cnpj:
                                conn_add = get_connection()
                                cursor_add = conn_add.cursor()
                                cursor_add.execute(
                                    """
                                    INSERT INTO clientes (nome, cnpj_cpf, regime, limite_faturamento, telefone, cnae_atividade, user_id)
                                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                                    """,
                                    (n_nome, n_cnpj, n_regime, n_limite, n_tel, n_cnae, user_id_atual)
                                )
                                conn_add.commit()
                                conn_add.close()
                                st.success(f"Empresa '{n_nome}' adicionada! Selecione-a na barra lateral.")
                                st.rerun()
                            else:
                                st.warning("Preencha Razão Social e CNPJ/CPF.")
                # ABA 3: CRIAR NOVO LOGIN DE USUÁRIO
                with tab_usuario:
                    with st.form("form_criar_usuario_admin"):
                        st.markdown("##### Criar Novo Login de Acesso")
                        u_email = st.text_input("E-mail do Cliente / Usuário")
                        u_senha = st.text_input("Senha Provisória (mínimo 6 caracteres)", type="password")

                        btn_criar_user = st.form_submit_button("🔑 Criar Conta de Acesso", use_container_width=True)

                        if btn_criar_user:
                            if u_email and len(u_senha) >= 6:
                                try:
                                    res = supabase.auth.sign_up({"email": u_email, "password": u_senha})
                                    st.success(f"Login criado com sucesso para **{u_email}**!")
                                except Exception as e:
                                    st.error(f"Erro ao criar conta: {e}")
                            else:
                                st.warning("Informe um e-mail válido e uma senha com pelo menos 6 caracteres.")

                # ABA 4: LISTA COMPLETA DA CARTEIRA DE CLIENTES
                with tab_lista:
                    st.markdown("##### 🏢 Carteira de Clientes Cadastrados")
                
                    conn_lista = get_connection()
                    df_todos_clientes = pd.read_sql_query(
                        """
                        SELECT 
                            id as "ID",
                            nome as "Razão Social / Nome", 
                            cnpj_cpf as "CNPJ / CPF", 
                            regime as "Regime Contábil",
                            COALESCE(limite_faturamento, 81000.00) as "Teto (R$)",
                            COALESCE(telefone, '-') as "Telefone",
                            COALESCE(cnae_atividade, '-') as "CNAE"
                        FROM clientes 
                        ORDER BY nome ASC
                        """,
                        conn_lista
                    )
                    conn_lista.close()

                    if df_todos_clientes.empty:
                        st.info("💡 Nenhum cliente cadastrado até o momento.")
                    else:
                        st.dataframe(
                            df_todos_clientes, 
                            use_container_width=True,
                            hide_index=True
                        )
# Fim do bloco Cadastrar Clientes

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

# BLOCO CADASTRAR CONTAS / FORNECEDORES (COM BANNER DE CLIENTE ATIVO)
elif opcao == "Cadastrar Conta / Fornecedor":
    st.subheader("⚙️ Gestão de Contas e Fornecedores")

    cliente_ativo_id = st.session_state.get("cliente_id_ativo")

    if not cliente_ativo_id:
        st.warning("⚠️ Nenhum cliente selecionado. Escolha um cliente ativo na barra lateral para prosseguir.")
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
            
            # Banner informativo do Cliente Ativo
            st.info(f"📋 Cliente Ativo em Atendimento: **{nome_cliente}** | Regime: **{regime_cliente}**")

            # -----------------------------------------------------------------
            # FORMULÁRIOS LADO A LADO
            # -----------------------------------------------------------------
            col_cadastro, col_edicao = st.columns(2)

            # COLUNA ESQUERDA: CADASTRO
            with col_cadastro:
                st.markdown("##### ➕ Cadastro de Contas no Plano de Contas / Fornecedor")
                with st.form("form_cadastrar_conta_nova", clear_on_submit=True):
                    codigo = st.text_input("Código da Conta", placeholder="Ex: 4.1.1.08")
                    descricao = st.text_input("Nome da Conta / Fornecedor", placeholder="Ex: Posto Shell Ltda")
                    tipo_conta = st.selectbox(
                        "Grupo / Tipo",
                        ["Despesa", "Receita", "Ativo", "Passivo", "Patrimônio Líquido"],
                    )
                    salvar_conta = st.form_submit_button("➕ Cadastrar Conta", use_container_width=True)

                    if salvar_conta:
                        if codigo and descricao:
                            conn = get_connection()
                            cursor = conn.cursor()
                            try:
                                cursor.execute(
                                    "INSERT INTO plano_contas (codigo, descricao, tipo) VALUES (%s, %s, %s)",
                                    (codigo, descricao, tipo_conta),
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

            # COLUNA DIREITA: ALTERAÇÃO / EXCLUSÃO
            with col_edicao:
                st.markdown("##### ✏️ Alterar ou Excluir Conta / Fornecedor")
                
                conn = get_connection()
                df_plano = pd.read_sql_query(
                    'SELECT id, codigo as "Código", descricao as "Nome da Conta", tipo as "Tipo" FROM plano_contas ORDER BY codigo ASC',
                    conn,
                )
                conn.close()

                if not df_plano.empty:
                    df_plano["label"] = (
                        df_plano["Código"] + " - " + df_plano["Nome da Conta"] + " (" + df_plano["Tipo"] + ")"
                    )
                    dict_contas = dict(zip(df_plano["label"], df_plano["id"]))

                    conta_sel_label = st.selectbox("Selecione para Modificar:", list(dict_contas.keys()), key="sb_modificar_conta_unica")
                    id_conta_sel = dict_contas[conta_sel_label]

                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("SELECT codigo, descricao, tipo FROM plano_contas WHERE id = %s", (id_conta_sel,))
                    reg_conta = cursor.fetchone()
                    conn.close()

                    if reg_conta:
                        cod_atual, nome_atual, tipo_atual = reg_conta

                        with st.form("form_editar_conta_unica"):
                            novo_codigo = st.text_input("Código", value=cod_atual)
                            novo_nome = st.text_input("Nome / Fornecedor", value=nome_atual)

                            tipos_possiveis = ["Despesa", "Receita", "Ativo", "Passivo", "Patrimônio Líquido"]
                            idx_tipo = tipos_possiveis.index(tipo_atual) if tipo_atual in tipos_possiveis else 0
                            novo_tipo = st.selectbox("Grupo / Tipo", tipos_possiveis, index=idx_tipo)

                            salvar_edicao = st.form_submit_button("💾 Salvar Alterações", use_container_width=True)

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

                        with st.expander("🗑️ Excluir esta Conta"):
                            st.caption("Atenção: A exclusão removerá o registro do catálogo.")
                            if st.button("Confirmar Exclusão", key=f"del_c_m2_{id_conta_sel}", type="primary", use_container_width=True):
                                conn = get_connection()
                                cursor = conn.cursor()
                                cursor.execute("DELETE FROM plano_contas WHERE id = %s", (id_conta_sel,))
                                conn.commit()
                                conn.close()
                                st.success("Conta excluída!")
                                st.rerun()
                else:
                    st.info("Nenhuma conta cadastrada para modificar.")

            # -----------------------------------------------------------------
            # TABELA INFERIOR: PLANO DE CONTAS ATUAL
            # -----------------------------------------------------------------
            st.markdown("---")
            st.write("### 📖 Plano de Contas Atual")
            if 'df_plano' in locals() and not df_plano.empty:
                df_exibicao_plano = df_plano.drop(columns=["id", "label"], errors="ignore")
                st.dataframe(df_exibicao_plano, use_container_width=True, height=350)
            else:
                st.info("Nenhuma conta cadastrada no momento.")
                
# fim do bloco

# BLOCO DE PLANO DE CONTAS (COM BANNER DE CLIENTE ATIVO)
elif opcao == "Plano de Contas":
    st.subheader("📖 Plano de Contas Simplificado (MEI)")

    cliente_ativo_id = st.session_state.get("cliente_id_ativo")

    if not cliente_ativo_id:
        st.warning("⚠️ Nenhum cliente selecionado. Escolha um cliente ativo na barra lateral para prosseguir.")
    else:
        conn = get_connection()
        # 1. Busca os dados do cliente ativo para exibição no banner
        df_cliente = pd.read_sql_query(
            "SELECT id, nome, regime FROM clientes WHERE id = %s AND user_id = %s", 
            conn, 
            params=(cliente_ativo_id, st.session_state.user.id)
        )

        if df_cliente.empty:
            st.error("Erro de segurança: Cliente não encontrado ou sem permissão.")
            conn.close()
        else:
            nome_cliente = df_cliente.iloc[0]["nome"]
            regime_cliente = df_cliente.iloc[0]["regime"]
            
            # Banner informativo do Cliente Ativo
            st.info(f"📋 Cliente Ativo em Atendimento: **{nome_cliente}** | Regime: **{regime_cliente}**")

            # 2. Busca as contas cadastradas no Plano de Contas
            df_plano = pd.read_sql_query(
                'SELECT codigo as "Código", descricao as "Nome da Conta / Fornecedor", tipo as "Grupo / Tipo" FROM plano_contas ORDER BY codigo ASC',
                conn,
            )
            conn.close()

            if df_plano.empty:
                st.info("Nenhuma conta cadastrada no Plano de Contas.")
            else:
                busca = st.text_input(
                    "🔍 Buscar Conta ou Fornecedor", placeholder="Ex: Combustível, Ambev ou 4.1.1"
                )
                if busca:
                    df_plano = df_plano[
                        df_plano["Código"].str.contains(busca, case=False, na=False)
                        | df_plano["Nome da Conta / Fornecedor"].str.contains(busca, case=False, na=False)
                    ]

                tab_geral, tab_receitas, tab_despesas, tab_financeiro = st.tabs(
                    [
                        "📋 Visão Geral",
                        "🟢 Receitas (Entradas)",
                        "🔴 Despesas & Fornecedores (Saídas)",
                        "💼 Caixas e Bancos",
                    ]
                )

                with tab_geral:
                    st.dataframe(df_plano, use_container_width=True, height=400)

                with tab_receitas:
                    st.markdown("##### 🟢 Contas de Receita (Faturamento MEI)")
                    st.dataframe(
                        df_plano[df_plano["Grupo / Tipo"] == "Receita"],
                        use_container_width=True,
                        height=300
                    )

                with tab_despesas:
                    st.markdown("##### 🔴 Contas de Despesa e Fornecedores")
                    st.dataframe(
                        df_plano[df_plano["Grupo / Tipo"].isin(["Despesa", "Passivo"])],
                        use_container_width=True,
                        height=300
                    )

                with tab_financeiro:
                    st.markdown("##### 💼 Movimentação Financeira (Caixa / Contas Bancárias)")
                    st.dataframe(
                        df_plano[df_plano["Grupo / Tipo"] == "Ativo"],
                        use_container_width=True,
                        height=300
                    )

                st.markdown("---")
                csv_plano = df_plano.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig")
                st.download_button(
                    label="📥 Baixar Plano de Contas em Excel (.csv)",
                    data=csv_plano,
                    file_name="plano_de_contas_mei.csv",
                    mime="text/csv",
                )
# Fim do BLOCO

# BLOCO DE LANÇAMENTOS - Novo lançamento
elif opcao == "Novo Lançamento":
    st.subheader("Registro de Lançamento Contábil")
    conn = get_connection()
    df_clientes = pd.read_sql_query(
        "SELECT id, nome, regime FROM clientes WHERE user_id = %s AND id = %s", 
        conn, 
        params=(st.session_state.user.id, st.session_state.cliente_id_ativo)
    )
    df_contas = pd.read_sql_query(
        "SELECT codigo, descricao, tipo FROM plano_contas ORDER BY codigo ASC", 
        conn
    )
    # Busca especificamente as contas do Grupo 4 (Despesas / Fornecedores 4.1.1...)
    df_despesas_grupo4 = pd.read_sql_query(
        "SELECT codigo, descricao FROM plano_contas WHERE tipo = 'Despesa' OR codigo LIKE '4.1%' ORDER BY codigo ASC",
        conn
    )
    conn.close()

    if df_clientes.empty:
        st.warning("Nenhum cliente selecionado. Escolha um cliente ativo na barra lateral.")
    else:
        dict_clientes_id = dict(zip(df_clientes["nome"], df_clientes["id"]))
        dict_clientes_regime = dict(zip(df_clientes["nome"], df_clientes["regime"]))

        cliente_selecionado = list(dict_clientes_id.keys())[0]
        regime_cliente = dict_clientes_regime[cliente_selecionado]

        st.info(f"📋 Cliente Ativo: **{cliente_selecionado}** | Regime: **{regime_cliente}**")

        # Monta a lista formatada de Fornecedores / Despesas (Grupo 4.1.1...)
        opcoes_fornecedores_despesa = [""] + [
            f"{row['codigo']} - {row['descricao']}" for _, row in df_despesas_grupo4.iterrows()
        ]

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

        # --- ESTRUTURA MEI / LIVRO CAIXA ---
        if "Lançamento Simples" in regime_cliente:
            tab_entrada, tab_saida = st.tabs([
                "🟢 (+) ENTRADAS / RECEITAS", 
                "🔴 (-) SAÍDAS / DESPESAS E ESTOQUE"
            ])

            # -----------------------------------------------------------------
            # ABA 1: ENTRADAS / RECEITAS
            # -----------------------------------------------------------------
            with tab_entrada:
                with st.form("form_entrada", clear_on_submit=True):
                    st.markdown("##### ⚡ Registrar Entrada de Caixas / Receitas")
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
                            ["1.1.1.01 - Caixa Geral", "1.1.1.02 - Banco Conta Movimento"],
                            key="cf_ent"
                        )
                    with col_s2:
                        df_rec = df_contas[df_contas["tipo"] == "Receita"]
                        opcoes_rec = [""] + [f"{r['codigo']} - {r['descricao']}" for _, r in df_rec.iterrows()]
                        categoria = st.selectbox("Categoria da Receita", opcoes_rec, key="cat_ent")

                    valor = st.number_input("Valor da Receita (R$)", min_value=0.00, step=0.01, format="%.2f", key="val_ent")
                    hist_sel = st.selectbox("Histórico Padrão", historicos_padrao, key="hp_ent")
                    comp_hist = st.text_input("Complemento do Histórico", placeholder="Ex: Vendas do dia em cartão e dinheiro", key="ch_ent")

                    salvar_ent = st.form_submit_button("🟢 Registrar Entrada")

                    if salvar_ent:
                        if categoria and valor > 0:
                            info_doc = f"[{tipo_doc}" + (f" nº {num_doc.strip()}" if num_doc.strip() else "") + (f" - {nome_cliente_rec.strip()}" if nome_cliente_rec.strip() else "") + "]"
                            hist_final = f"{info_doc} {comp_hist.strip()}" if hist_sel == "Digitar Histórico do Zero" else f"{info_doc} {hist_sel} {comp_hist.strip()}"

                            conn = get_connection()
                            cursor = conn.cursor()
                            cursor.execute(
                                "INSERT INTO lancamentos (cliente_id, data, conta_debito, conta_credito, valor, historico) VALUES (%s, %s, %s, %s, %s, %s)",
                                (dict_clientes_id[cliente_selecionado], str(data), conta_financeira, categoria, valor, hist_final.strip())
                            )
                            conn.commit()
                            conn.close()
                            st.success("Entrada registrada com sucesso!")
                            st.rerun() #Limpa registro
                        else:
                            st.error("Selecione a Categoria da Receita e informe um valor maior que zero.")

            # -----------------------------------------------------------------
            # ABA 2: SAÍDAS / DESPESAS (Com lista do Grupo 4.1.1...)
            # -----------------------------------------------------------------
            with tab_saida:
                with st.form("form_saida", clear_on_submit=True):
                    st.markdown("##### ⚡ Registrar Pagamento de Despesa / Fornecedor")
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
                            ["1.1.1.01 - Caixa Geral", "1.1.1.02 - Banco Conta Movimento"],
                            key="cf_sai"
                        )
                    with col_s2:
                        # Seleção direta do Grupo 4.1.1...
                        categoria = st.selectbox(
                            "Fornecedor / Conta de Despesa (Grupo 4)", 
                            opcoes_fornecedores_despesa, 
                            key="cat_sai"
                        )

                    valor = st.number_input("Valor da Despesa (R$)", min_value=0.00, step=0.01, format="%.2f", key="val_sai")
                    hist_sel = st.selectbox("Histórico Padrão", historicos_padrao, key="hp_sai")
                    comp_hist = st.text_input("Complemento do Histórico", placeholder="Ex: Aquisição de combustíveis e insumos", key="ch_sai")

                    salvar_sai = st.form_submit_button("🔴 Registrar Saída")

                    if salvar_sai:
                        if categoria and valor > 0:
                            info_doc = f"[{tipo_doc}" + (f" nº {num_doc.strip()}" if num_doc.strip() else "") + "]"
                            hist_final = f"{info_doc} {comp_hist.strip()}" if hist_sel == "Digitar Histórico do Zero" else f"{info_doc} {hist_sel} {comp_hist.strip()}"

                            conn = get_connection()
                            cursor = conn.cursor()
                            cursor.execute(
                                "INSERT INTO lancamentos (cliente_id, data, conta_debito, conta_credito, valor, historico) VALUES (%s, %s, %s, %s, %s, %s)",
                                (dict_clientes_id[cliente_selecionado], str(data), categoria, conta_financeira, valor, hist_final.strip())
                            )
                            conn.commit()
                            conn.close()
                            st.success("Saída registrada com sucesso!")
                            st.rerun() #Limpa campo
                        else:
                            st.error("Selecione o Fornecedor / Conta de Despesa e informe um valor maior que zero.")

        # --- PARTIDA DUPLA COMPLETA ---
        else:
            with st.form("form_partida_dupla", clear_on_submit=True):
                st.markdown("##### 🔄 Preenchimento por Partida Dupla")
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
                    if conta_debito and conta_credito and valor > 0:
                        hist_final = comp_hist if hist_sel == "Digitar Histórico do Zero" else f"{hist_sel} {comp_hist}"
                        conn = get_connection()
                        cursor = conn.cursor()
                        cursor.execute(
                            "INSERT INTO lancamentos (cliente_id, data, conta_debito, conta_credito, valor, historico) VALUES (%s, %s, %s, %s, %s, %s)",
                            (dict_clientes_id[cliente_selecionado], str(data), conta_debito, conta_credito, valor, hist_final.strip())
                        )
                        conn.commit()
                        conn.close()
                        st.success("Lançamento em Partida Dupla registrado!")
# Fim do BLOCO

# BLOCO PROVISÕES / CONTAS A PAGAR (COM BAIXA AUTOMÁTICA)
elif "Provisões" in opcao:
    st.subheader("📌 Provisões / Contas a Pagar")

    cliente_ativo_id = st.session_state.get("cliente_id_ativo")

    if not cliente_ativo_id:
        st.warning("⚠️ Nenhum cliente selecionado. Escolha um cliente ativo na barra lateral para prosseguir.")
    else:
        conn = get_connection()
        # 1. Dados do cliente ativo para o banner
        df_cliente = pd.read_sql_query(
            "SELECT id, nome, regime FROM clientes WHERE id = %s AND user_id = %s", 
            conn, 
            params=(cliente_ativo_id, st.session_state.user.id)
        )

        if df_cliente.empty:
            st.error("Erro de segurança: Cliente não encontrado ou sem permissão.")
            conn.close()
        else:
            nome_cliente = df_cliente.iloc[0]["nome"]
            regime_cliente = df_cliente.iloc[0]["regime"]

            st.info(f"📋 Cliente Ativo em Atendimento: **{nome_cliente}** | Regime: **{regime_cliente}**")

            # -----------------------------------------------------------------
            # FORMULÁRIO DE CADASTRO DE PROVISÃO
            # -----------------------------------------------------------------
            with st.expander("➕ Agendar Nova Guia / Conta a Pagar", expanded=True):
                with st.form("form_nova_provisao", clear_on_submit=True):
                    col_p1, col_p2, col_p3 = st.columns([2, 1, 1])
                    
                    with col_p1:
                        desc_provisao = st.text_input("Descrição da Obrigação", placeholder="Ex: Guia DAS Mensal - 10/2026 ou Parcelamento RFB 02/10")
                    with col_p2:
                        tipo_provisao = st.selectbox("Tipo de Conta", ["Guia DAS", "Parcelamento RFB", "Aluguel", "Fornecedor / Compra", "Outros"])
                        valor_provisao = st.number_input("Valor R$", min_value=0.01, step=10.0, format="%.2f")
                    with col_p3:
                        data_venc = st.date_input("Data de Vencimento")
                        st.markdown("<br>", unsafe_allow_html=True)
                        salvar_prov = st.form_submit_button("💾 Agendar Provisão", use_container_width=True)

                    if salvar_prov:
                        if desc_provisao and valor_provisao > 0:
                            cursor = conn.cursor()
                            cursor.execute(
                                """
                                INSERT INTO provisoes (cliente_id, descricao, tipo, valor, data_vencimento, status)
                                VALUES (%s, %s, %s, %s, %s, 'Pendente')
                                """,
                                (cliente_ativo_id, desc_provisao, tipo_provisao, valor_provisao, data_venc)
                            )
                            conn.commit()
                            st.success(f"Provisão '{desc_provisao}' agendada com sucesso!")
                            st.rerun()
                        else:
                            st.warning("Preencha a descrição e um valor válido.")

            st.markdown("---")

            # 2. Busca provisões cadastradas
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

            if df_provisoes.empty:
                st.info("💡 Nenhuma conta a pagar agendada para este cliente.")
            else:
                df_pendentes = df_provisoes[df_provisoes["status"] == "Pendente"]
                df_pagas = df_provisoes[df_provisoes["status"] == "Pago"]

                # KPIs Rápidos
                total_pendente = df_pendentes["valor"].sum() if not df_pendentes.empty else 0.0
                st.write(f"##### ⌛ Guias e Contas Pendentes (Total: **{formatar_brl(total_pendente)}**)")

                if df_pendentes.empty:
                    st.success("🎉 Nenhuma conta pendente no momento!")
                else:
                    for idx, row in df_pendentes.iterrows():
                        col_info, col_acao = st.columns([3, 1])
                        
                        with col_info:
                            venc_formatado = pd.to_datetime(row['data_vencimento']).strftime('%d/%m/%Y')
                            st.write(f"🗓️ **Vencimento: {venc_formatado}** | **{row['descricao']}** ({row['tipo']})")
                            st.caption(f"Valor a Pagar: **{formatar_brl(row['valor'])}** | Status: 🟡 **{row['status']}**")

                        with col_acao:
                            # Botão de baixa rápida que liquida e lança no caixa
                            if st.button("✅ Pagar / Dar Baixa", key=f"btn_pago_{row['id']}", use_container_width=True):
                                conn_baixa = get_connection()
                                cursor_baixa = conn_baixa.cursor()
                                
                                # Atualiza status na tabela de provisões
                                cursor_baixa.execute("UPDATE provisoes SET status = 'Pago' WHERE id = %s", (row['id'],))
                                
                                # Gera lançamento automático de saída no Livro Caixa
                                cursor_baixa.execute(
                                    """
                                    INSERT INTO lancamentos (cliente_id, data, conta_debito, conta_credito, valor, historico)
                                    VALUES (%s, CURRENT_DATE, '4.1.1 - Despesas Operacionais', '1.1.1 - Caixa Geral', %s, %s)
                                    """,
                                    (cliente_ativo_id, row['valor'], f"Pagamento baixado de provisão: {row['descricao']}")
                                )
                                conn_baixa.commit()
                                conn_baixa.close()
                                
                                st.success(f"Conta '{row['descricao']}' baixada e registrada no Livro Caixa!")
                                st.rerun()
                        st.markdown("<hr style='margin: 5px 0;'>", unsafe_allow_html=True)

                # Histórico de Contas Pagas
                if not df_pagas.empty:
                    with st.expander("✅ Ver Histórico de Contas Já Pagas", expanded=False):
                        df_pagas_exib = df_pagas.copy()
                        df_pagas_exib["valor"] = df_pagas_exib["valor"].apply(formatar_brl)
                        st.dataframe(
                            df_pagas_exib[["data_vencimento", "descricao", "tipo", "valor", "status"]],
                            use_container_width=True
                        )
#Fim do Bloco

# BLOCO IMPORTAR EXTRATO / PLANILHA EXCEL
elif opcao == "Importar Extrato / Excel":
    st.subheader("📥 Importação de Planilha do Cliente (Excel)")

    cliente_ativo_id = st.session_state.get("cliente_id_ativo")

    if not cliente_ativo_id:
        st.warning("⚠️ Selecione um cliente ativo na barra lateral antes de importar.")
    else:
        st.info("Envie a planilha do cliente para realizar a leitura e o registro automático no Livro Caixa.")

        # Aceita arquivos .xlsx, .xls e .xlsm (com macros)
        arquivo = st.file_uploader("Selecione a planilha do cliente", type=["xlsx", "xls", "xlsm"])

        if arquivo is not None:
            try:
                df = pd.read_excel(arquivo)
                
                st.write("##### 🔍 Pré-visualização da planilha carregada:")
                st.dataframe(df.head(10), use_container_width=True)

                if st.button("🚀 Processar e Importar Lançamentos", use_container_width=True):
                    conn = get_connection()
                    cursor = conn.cursor()
                    importados = 0

                    for idx, row in df.iterrows():
                        # Trata a data
                        data_val = pd.to_datetime(row.get("Data"), errors="coerce")
                        if pd.isna(data_val):
                            continue
                        data_str = data_val.strftime("%Y-%m-%d")

                        # Trata descrição e categoria
                        desc = str(row.get("Descrição", "") or "").strip()
                        cat = str(row.get("Categoria", "") or "").strip()
                        if cat.lower() in ["nan", "none", ""]:
                            cat = "Despesas Gerais"

                        # Mapeia colunas de nota fiscal e série da planilha
                        doc_num = row.get("Nfe / Cupom") or row.get("NFe_Cupom/Série") or row.get("NFe") or ""
                        serie_num = row.get("Série") or ""
                        
                        doc_str = str(doc_num).strip() if pd.notna(doc_num) and str(doc_num).lower() not in ["nan", "none"] else ""
                        serie_str = str(serie_num).strip() if pd.notna(serie_num) and str(serie_num).lower() not in ["nan", "none"] else ""
                        
                        doc_info = f"{doc_str} (Série {serie_str})" if (doc_str and serie_str) else (doc_str or serie_str or "S/N")

                        # Trata valores monetários
                        val_saida = float(row.get("Valor Saída", 0) if pd.notna(row.get("Valor Saída")) else 0)
                        val_entrada = float(row.get("Valor Entrada", 0) if pd.notna(row.get("Valor Entrada")) else 0)

                        # Formata o histórico do lançamento
                        historico = f"{desc} | Doc: {doc_info} | Cat: {cat}".strip(" |")

                        # 1. ENTRADAS (RECEITAS)
                        if val_entrada > 0:
                            cursor.execute(
                                """
                                INSERT INTO lancamentos (cliente_id, data, conta_debito, conta_credito, valor, historico)
                                VALUES (%s, %s, '1.1.1 - Caixa Geral', '3.1.1 - Receita de Vendas/Serviços', %s, %s)
                                """,
                                (cliente_ativo_id, data_str, val_entrada, historico)
                            )
                            importados += 1

                        # 2. SAÍDAS (DESPESAS)
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
                    conn.close()

                    st.success(f"🎉 Importação concluída! **{importados}** registros foram salvos no banco de dados do cliente.")
                    st.rerun()

            except Exception as e:
                st.error(f"Erro ao processar o arquivo Excel: {e}")#Fim do Bloco

# BLOCO VER LANÇAMENTOS (RESTRIÇÃO STRICTA AO CLIENTE ATIVO + BANNER)
elif "Ver Lançamentos" in opcao:
    st.subheader("📋 Consultar, Alterar e Excluir Lançamentos")

    cliente_ativo_id = st.session_state.get("cliente_id_ativo")

    if not cliente_ativo_id:
        st.warning("⚠️ Nenhum cliente selecionado. Escolha um cliente ativo na barra lateral para prosseguir.")
    else:
        conn = get_connection()
        
        # 1. Busca os dados do cliente ativo para exibição no banner
        df_cliente = pd.read_sql_query(
            "SELECT id, nome, regime FROM clientes WHERE id = %s AND user_id = %s", 
            conn, 
            params=(cliente_ativo_id, st.session_state.user.id)
        )

        if df_cliente.empty:
            st.error("Erro de segurança: Cliente não encontrado ou sem permissão.")
            conn.close()
        else:
            nome_cliente = df_cliente.iloc[0]["nome"]
            regime_cliente = df_cliente.iloc[0]["regime"]

            # Caixa informativa do Cliente Ativo
            st.info(f"📋 Cliente Ativo em Atendimento: **{nome_cliente}** | Regime: **{regime_cliente}**")

            # 2. Consulta de lançamentos restrita ao cliente ativo da sessão
            df_lancamentos = pd.read_sql_query(
                """
                SELECT 
                    id, 
                    data as "Data", 
                    conta_debito as "Conta Débito", 
                    conta_credito as "Conta Crédito", 
                    valor as "Valor (R$)", 
                    historico as "Histórico" 
                FROM lancamentos 
                WHERE cliente_id = %s 
                ORDER BY data DESC, id DESC
                """,
                conn,
                params=(cliente_ativo_id,)
            )
            
            # 3. Busca o plano de contas para popular os seletores de edição
            df_contas = pd.read_sql_query(
                "SELECT codigo, descricao FROM plano_contas ORDER BY codigo ASC", 
                conn
            )
            conn.close()

            if df_lancamentos.empty:
                st.info("💡 Nenhum lançamento encontrado para o cliente ativo.")
            else:
                # Tabela de visualização dos lançamentos
                st.write("##### 📑 Lançamentos Registrados")
                st.dataframe(df_lancamentos, use_container_width=True, height=300)

                st.markdown("---")
                st.write("##### ✏️ Alterar ou Excluir Lançamento")

                # Formata rótulos para a seleção do lançamento
                df_lancamentos["label"] = (
                    "ID " + df_lancamentos["id"].astype(str) + " | " +
                    df_lancamentos["Data"].astype(str) + " | R$ " +
                    df_lancamentos["Valor (R$)"].apply(lambda x: f"{x:,.2f}") + " | " +
                    df_lancamentos["Histórico"]
                )
                dict_lancamentos = dict(zip(df_lancamentos["label"], df_lancamentos["id"]))

                lanc_sel_label = st.selectbox("Selecione o Lançamento para modificar:", list(dict_lancamentos.keys()))
                id_lanc_sel = dict_lancamentos[lanc_sel_label]

                # Busca os dados do lançamento para preencher o formulário
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT data, conta_debito, conta_credito, valor, historico FROM lancamentos WHERE id = %s AND cliente_id = %s",
                    (id_lanc_sel, cliente_ativo_id)
                )
                reg_lanc = cursor.fetchone()
                conn.close()

                if reg_lanc:
                    dt_atu, deb_atu, cred_atu, val_atu, hist_atu = reg_lanc
                    plano_de_contas = [""] + [f"{r['codigo']} - {r['descricao']}" for _, r in df_contas.iterrows()]

                    with st.form("form_editar_lancamento_ativo"):
                        col_ed1, col_ed2 = st.columns(2)
                        with col_ed1:
                            nova_dt = st.date_input("Data", value=pd.to_datetime(dt_atu).date(), format="DD/MM/YYYY")
                            
                            idx_deb = plano_de_contas.index(deb_atu) if deb_atu in plano_de_contas else 0
                            novo_deb = st.selectbox("Conta Débito", plano_de_contas, index=idx_deb)
                            
                            novo_val = st.number_input("Valor (R$)", value=float(val_atu), min_value=0.00, step=0.01, format="%.2f")

                        with col_ed2:
                            idx_cred = plano_de_contas.index(cred_atu) if cred_atu in plano_de_contas else 0
                            novo_cred = st.selectbox("Conta Crédito", plano_de_contas, index=idx_cred)
                            
                            novo_hist = st.text_input("Histórico", value=hist_atu)

                        salvar_ed_lanc = st.form_submit_button("💾 Salvar Alterações", use_container_width=True)

                        if salvar_ed_lanc:
                            if novo_deb and novo_cred and novo_val > 0:
                                conn = get_connection()
                                cursor = conn.cursor()
                                cursor.execute(
                                    """
                                    UPDATE lancamentos 
                                    SET data = %s, conta_debito = %s, conta_credito = %s, valor = %s, historico = %s 
                                    WHERE id = %s AND cliente_id = %s
                                    """,
                                    (str(nova_dt), novo_deb, novo_cred, novo_val, novo_hist, id_lanc_sel, cliente_ativo_id)
                                )
                                conn.commit()
                                conn.close()
                                st.success("Lançamento atualizado com sucesso!")
                                st.rerun()
                            else:
                                st.error("Preencha as contas e um valor maior que zero.")

                    with st.expander("🗑️ Excluir este Lançamento"):
                        st.caption("Atenção: Esta ação removerá o registro do histórico.")
                        if st.button("Confirmar Exclusão", key=f"del_l_m6_{id_lanc_sel}", type="primary", use_container_width=True):
                            conn = get_connection()
                            cursor = conn.cursor()
                            cursor.execute("DELETE FROM lancamentos WHERE id = %s AND cliente_id = %s", (id_lanc_sel, cliente_ativo_id))
                            conn.commit()
                            conn.close()
                            st.success("Lançamento excluído com sucesso!")
                            st.rerun()
#Fim do bloco

# BLOCO RELATÓRIO POR CATEGORIA (RESTRIÇÃO STRICTA AO CLIENTE ATIVO + LADO A LADO)
elif "Relatório por Categoria" in opcao or "Relatório" in opcao:
    st.subheader("📊 Relatório Financeiro por Categoria")

    cliente_ativo_id = st.session_state.get("cliente_id_ativo")

    if not cliente_ativo_id:
        st.warning("⚠️ Nenhum cliente selecionado. Escolha um cliente ativo na barra lateral para prosseguir.")
    else:
        conn = get_connection()
        # 1. Dados do cliente ativo para o banner
        df_cliente = pd.read_sql_query(
            "SELECT id, nome, regime FROM clientes WHERE id = %s AND user_id = %s", 
            conn, 
            params=(cliente_ativo_id, st.session_state.user.id)
        )

        if df_cliente.empty:
            st.error("Erro de segurança: Cliente não encontrado ou sem permissão.")
            conn.close()
        else:
            nome_cliente = df_cliente.iloc[0]["nome"]
            regime_cliente = df_cliente.iloc[0]["regime"]

            # Banner Informativo do Cliente Ativo
            st.info(f"📋 Cliente Ativo em Atendimento: **{nome_cliente}** | Regime: **{regime_cliente}**")

            # 2. Busca todos os lançamentos do cliente ativo
            df_lancamentos = pd.read_sql_query(
                "SELECT conta_debito, conta_credito, valor, data FROM lancamentos WHERE cliente_id = %s",
                conn,
                params=(cliente_ativo_id,)
            )
            conn.close()

            if df_lancamentos.empty:
                st.info("💡 Nenhum lançamento encontrado para montar o relatório do cliente ativo.")
            else:
                # Separa e agrupa Receitas (Entradas) e Despesas (Saídas)
                df_entradas = (
                    df_lancamentos[~df_lancamentos["conta_credito"].str.contains("1.1.1", na=False)]
                    .groupby("conta_credito")["valor"]
                    .sum()
                    .reset_index()
                )
                df_entradas.columns = ["Categoria / Conta", "Total (R$)"]
                df_entradas["Grupo"] = "🟢 Receitas"

                df_saidas = (
                    df_lancamentos[~df_lancamentos["conta_debito"].str.contains("1.1.1", na=False)]
                    .groupby("conta_debito")["valor"]
                    .sum()
                    .reset_index()
                )
                df_saidas.columns = ["Categoria / Conta", "Total (R$)"]
                df_saidas["Grupo"] = "🔴 Despesas"

                df_agrupado = pd.concat([df_entradas, df_saidas], ignore_index=True)

                if df_agrupado.empty:
                    df_agrupado = df_lancamentos.groupby("conta_debito")["valor"].sum().reset_index()
                    df_agrupado.columns = ["Categoria / Conta", "Total (R$)"]
                    df_agrupado["Grupo"] = "Movimentação"

                df_exibicao = df_agrupado.copy()
                df_exibicao["Valor Formatado"] = df_exibicao["Total (R$)"].apply(formatar_brl)

                st.markdown("---")

                # -----------------------------------------------------------------
                # LAYOUT LADO A LADO: TABELA (ESQUERDA) VS GRÁFICO (DIREITA)
                # -----------------------------------------------------------------
                col_tabela, col_grafico = st.columns([1, 1])

                with col_tabela:
                    st.write("##### 📋 Acumulado por Categoria")
                    st.dataframe(
                        df_exibicao[["Grupo", "Categoria / Conta", "Valor Formatado"]],
                        use_container_width=True,
                        height=360
                    )

                with col_grafico:
                    st.write("##### 📈 Distribuição Geral")
                    try:
                        import plotly.express as px
                        fig = px.pie(
                            df_agrupado,
                            names="Categoria / Conta",
                            values="Total (R$)",
                            color="Grupo",
                            color_discrete_map={"🟢 Receitas": "#2ca02c", "🔴 Despesas": "#d62728"},
                            hole=0.35,
                        )
                        fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=360)
                        st.plotly_chart(fig, use_container_width=True)
                    except Exception:
                        st.bar_chart(df_agrupado.set_index("Categoria / Conta")["Total (R$)"])

                st.markdown("---")

                # Botão para exportar o relatório consolidado
                csv_rel = df_agrupado.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig")
                st.download_button(
                    label="📥 Baixar Relatório por Categoria (.csv)",
                    data=csv_rel,
                    file_name=f"relatorio_categoria_{nome_cliente.replace(' ', '_').lower()}.csv",
                    mime="text/csv",
                )
# Fim do Bloco                