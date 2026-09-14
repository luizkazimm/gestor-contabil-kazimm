import sqlite3

def inicializar_banco():
    # Conecta (ou cria) o arquivo de banco de dados
    conn = sqlite3.connect('gestor_contabil.db')
    cursor = conn.cursor()

    # 1. Tabela de Clientes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cnpj_cpf TEXT UNIQUE NOT NULL
        )
    ''')

    # 2. Tabela de Plano de Contas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS plano_contas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT NOT NULL,
            nome TEXT NOT NULL,
            tipo TEXT NOT NULL -- Ex: Ativo, Passivo, Receita, Despesa
        )
    ''')

    # 3. Tabela de Lançamentos Contábeis
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lancamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER NOT NULL,
            data TEXT NOT NULL,
            conta_debito TEXT NOT NULL,
            conta_credito TEXT NOT NULL,
            valor REAL NOT NULL,
            historico TEXT NOT NULL,
            FOREIGN KEY (cliente_id) REFERENCES clientes (id)
        )
    ''')

    conn.commit()
    conn.close()
    print("Banco de dados 'gestor_contabil.db' estruturado com sucesso!")

if __name__ == "__main__":
    inicializar_banco()