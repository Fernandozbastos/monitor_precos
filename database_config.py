#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Configuração de Banco de Dados para o Sistema de Monitoramento de Preços
------------------------------------------------------------------------
Gerencia a conexão e a estrutura do banco de dados SQLite.
"""

import sqlite3
import os
import pandas as pd
from datetime import datetime
from utils import depurar_logs

# Caminho do banco de dados
DB_FILE = 'monitor_precos.db'

def criar_conexao():
    """
    Cria uma conexão com o banco de dados SQLite.
    
    Returns:
        tuple: (conexao, cursor) para interagir com o banco de dados
    """
    conexao = sqlite3.connect(DB_FILE)
    conexao.row_factory = sqlite3.Row  # Permite acessar colunas pelo nome
    cursor = conexao.cursor()
    return conexao, cursor

def inicializar_banco_dados():
    """
    Cria as tabelas do banco de dados se não existirem.
    
    Returns:
        bool: True se a inicialização foi bem-sucedida, False caso contrário
    """
    try:
        conexao, cursor = criar_conexao()
        
        # Tabela de plataformas
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS plataformas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE NOT NULL,
            seletor_css TEXT NOT NULL,
            data_criacao TEXT NOT NULL
        )
        ''')
        
        # Tabela de domínios
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS dominios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE NOT NULL,
            seletor_css TEXT NOT NULL,
            data_criacao TEXT NOT NULL
        )
        ''')
        
        # Tabela de usuários
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            nome TEXT NOT NULL,
            tipo TEXT NOT NULL,
            ativo INTEGER NOT NULL,
            cliente_atual TEXT,
            data_criacao TEXT NOT NULL,
            ultimo_acesso TEXT
        )
        ''')
        
        # Tabela de grupos
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS grupos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_grupo TEXT UNIQUE NOT NULL,
            nome TEXT NOT NULL,
            descricao TEXT NOT NULL,
            data_criacao TEXT NOT NULL
        )
        ''')
        
        # Tabela de associação entre usuários e grupos
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios_grupos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_usuario INTEGER NOT NULL,
            id_grupo INTEGER NOT NULL,
            data_associacao TEXT NOT NULL,
            FOREIGN KEY (id_usuario) REFERENCES usuarios (id),
            FOREIGN KEY (id_grupo) REFERENCES grupos (id),
            UNIQUE(id_usuario, id_grupo)
        )
        ''')
        
        # Tabela de clientes
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE NOT NULL,
            data_criacao TEXT NOT NULL
        )
        ''')
        
        # Tabela de associação entre clientes e grupos
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes_grupos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_cliente INTEGER NOT NULL,
            id_grupo INTEGER NOT NULL,
            data_associacao TEXT NOT NULL,
            FOREIGN KEY (id_cliente) REFERENCES clientes (id),
            FOREIGN KEY (id_grupo) REFERENCES grupos (id),
            UNIQUE(id_cliente, id_grupo)
        )
        ''')
        
        # Tabela de produtos
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_cliente INTEGER NOT NULL,
            nome TEXT NOT NULL,
            concorrente TEXT NOT NULL,
            url TEXT NOT NULL,
            id_plataforma INTEGER,
            id_grupo INTEGER NOT NULL,
            data_criacao TEXT NOT NULL,
            FOREIGN KEY (id_cliente) REFERENCES clientes (id),
            FOREIGN KEY (id_plataforma) REFERENCES plataformas (id),
            FOREIGN KEY (id_grupo) REFERENCES grupos (id)
        )
        ''')
        
        # Tabela de histórico de preços
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS historico_precos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_produto INTEGER NOT NULL,
            preco REAL NOT NULL,
            data TEXT NOT NULL,
            FOREIGN KEY (id_produto) REFERENCES produtos (id)
        )
        ''')
        
        # Tabela de configurações de agendamento
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS agendamento (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            dia TEXT,
            horario TEXT NOT NULL,
            ativo INTEGER NOT NULL,
            data_criacao TEXT NOT NULL,
            ultima_execucao TEXT
        )
        ''')
        
        conexao.commit()
        conexao.close()
        
        # Criar grupos padrão (admin e all)
        criar_grupos_padrao()
        
        # Criar usuário admin padrão se não existir
        criar_admin_padrao()
        
        # Verificar os dados
        verificar_dados()
        
        return True
    except Exception as e:
        depurar_logs(f"Erro ao inicializar banco de dados: {e}", "ERROR")
        return False

def criar_grupos_padrao():
    """Cria os grupos padrão (admin e all) se não existirem."""
    try:
        conexao, cursor = criar_conexao()
        
        data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Verificar se o grupo 'admin' já existe
        cursor.execute("SELECT id FROM grupos WHERE id_grupo = 'admin'")
        if not cursor.fetchone():
            cursor.execute('''
            INSERT INTO grupos (id_grupo, nome, descricao, data_criacao)
            VALUES (?, ?, ?, ?)
            ''', ('admin', 'Administradores', 'Grupo de administradores com acesso a todos os clientes', data_atual))
        
        # Verificar se o grupo 'all' já existe
        cursor.execute("SELECT id FROM grupos WHERE id_grupo = 'all'")
        if not cursor.fetchone():
            cursor.execute('''
            INSERT INTO grupos (id_grupo, nome, descricao, data_criacao)
            VALUES (?, ?, ?, ?)
            ''', ('all', 'Todos', 'Grupo padrão que inclui todos os clientes', data_atual))
        
        conexao.commit()
        conexao.close()
        depurar_logs("Grupos padrão criados/verificados com sucesso", "INFO")
        return True
    except Exception as e:
        depurar_logs(f"Erro ao criar grupos padrão: {e}", "ERROR")
        return False

def criar_admin_padrao():
    """Cria o usuário admin padrão se não existir."""
    try:
        conexao, cursor = criar_conexao()
        
        # Verificar se o usuário 'admin' já existe
        cursor.execute("SELECT id FROM usuarios WHERE username = 'admin'")
        if not cursor.fetchone():
            import hashlib
            senha_hash = hashlib.sha256('admin'.encode()).hexdigest()
            data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute('''
            INSERT INTO usuarios (username, senha, nome, tipo, ativo, data_criacao)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', ('admin', senha_hash, 'Administrador', 'admin', 1, data_atual))
            
            # Obter ID do usuário admin
            cursor.execute("SELECT id FROM usuarios WHERE username = 'admin'")
            id_usuario = cursor.fetchone()[0]
            
            # Obter ID dos grupos admin e all
            cursor.execute("SELECT id FROM grupos WHERE id_grupo = 'admin'")
            id_grupo_admin = cursor.fetchone()[0]
            
            cursor.execute("SELECT id FROM grupos WHERE id_grupo = 'all'")
            id_grupo_all = cursor.fetchone()[0]
            
            # Associar usuário admin aos grupos admin e all
            cursor.execute('''
            INSERT INTO usuarios_grupos (id_usuario, id_grupo, data_associacao)
            VALUES (?, ?, ?)
            ''', (id_usuario, id_grupo_admin, data_atual))
            
            cursor.execute('''
            INSERT INTO usuarios_grupos (id_usuario, id_grupo, data_associacao)
            VALUES (?, ?, ?)
            ''', (id_usuario, id_grupo_all, data_atual))
            
            depurar_logs("Usuário admin padrão criado com sucesso", "INFO")
        
        conexao.commit()
        conexao.close()
        return True
    except Exception as e:
        depurar_logs(f"Erro ao criar usuário admin padrão: {e}", "ERROR")
        return False

def verificar_dados():
    """
    Verifica se o banco de dados contém dados básicos necessários.
    """
    try:
        conexao, cursor = criar_conexao()
        
        # Verificar usuário admin
        cursor.execute("SELECT COUNT(*) as count FROM usuarios WHERE username = 'admin'")
        resultado = cursor.fetchone()
        if resultado['count'] == 0:
            depurar_logs("Usuário admin não encontrado. Criando...", "WARNING")
            criar_admin_padrao()
        
        # Verificar grupos padrão
        cursor.execute("SELECT COUNT(*) as count FROM grupos WHERE id_grupo IN ('admin', 'all')")
        resultado = cursor.fetchone()
        if resultado['count'] < 2:
            depurar_logs("Grupos padrão não encontrados. Criando...", "WARNING")
            criar_grupos_padrao()
        
        # Verificar quantidade de dados
        cursor.execute("SELECT COUNT(*) as count FROM clientes")
        resultado_clientes = cursor.fetchone()
        
        cursor.execute("SELECT COUNT(*) as count FROM produtos")
        resultado_produtos = cursor.fetchone()
        
        depurar_logs(f"Banco de dados contém {resultado_clientes['count']} clientes e {resultado_produtos['count']} produtos", "INFO")
        
        conexao.close()
        return True
    except Exception as e:
        depurar_logs(f"Erro ao verificar dados: {e}", "ERROR")
        return False

def migrar_dados_csv_para_sqlite():
    """
    Migra os dados dos arquivos CSV para o banco de dados SQLite.
    
    Returns:
        bool: True se a migração foi bem-sucedida, False caso contrário
    """
    try:
        depurar_logs("Iniciando migração de dados...", "INFO")
        
        # 1. Migrar plataformas
        if os.path.isfile('plataformas_seletores.json'):
            import json
            with open('plataformas_seletores.json', 'r', encoding='utf-8') as f:
                plataformas = json.load(f)
            
            conexao, cursor = criar_conexao()
            data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            for plataforma, seletor in plataformas.items():
                cursor.execute('''
                INSERT OR IGNORE INTO plataformas (nome, seletor_css, data_criacao)
                VALUES (?, ?, ?)
                ''', (plataforma, seletor, data_atual))
            
            conexao.commit()
            conexao.close()
            depurar_logs(f"Migradas {len(plataformas)} plataformas", "INFO")
        
        # 2. Migrar domínios
        if os.path.isfile('dominios_seletores.json'):
            import json
            with open('dominios_seletores.json', 'r', encoding='utf-8') as f:
                dominios = json.load(f)
            
            conexao, cursor = criar_conexao()
            data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            for dominio, seletor in dominios.items():
                cursor.execute('''
                INSERT OR IGNORE INTO dominios (nome, seletor_css, data_criacao)
                VALUES (?, ?, ?)
                ''', (dominio, seletor, data_atual))
            
            conexao.commit()
            conexao.close()
            depurar_logs(f"Migrados {len(dominios)} domínios", "INFO")
        
        # 3. Migrar usuários
        if os.path.isfile('usuarios.json'):
            import json
            with open('usuarios.json', 'r', encoding='utf-8') as f:
                usuarios = json.load(f)
            
            conexao, cursor = criar_conexao()
            data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            for username, dados in usuarios.items():
                cursor.execute('''
                INSERT OR IGNORE INTO usuarios (username, senha, nome, tipo, ativo, cliente_atual, data_criacao)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    username, 
                    dados.get('senha', ''), 
                    dados.get('nome', ''), 
                    dados.get('tipo', 'usuario'), 
                    1 if dados.get('ativo', True) else 0,
                    dados.get('cliente_atual', ''),
                    data_atual
                ))
            
            conexao.commit()
            conexao.close()
            depurar_logs(f"Migrados {len(usuarios)} usuários", "INFO")
        
        # 4. Migrar grupos e associações
        if os.path.isfile('grupos.json'):
            import json
            with open('grupos.json', 'r', encoding='utf-8') as f:
                grupos = json.load(f)
            
            conexao, cursor = criar_conexao()
            data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Migrar definições de grupos
            for id_grupo, dados in grupos.items():
                cursor.execute('''
                INSERT OR IGNORE INTO grupos (id_grupo, nome, descricao, data_criacao)
                VALUES (?, ?, ?, ?)
                ''', (
                    id_grupo,
                    dados.get('nome', id_grupo),
                    dados.get('descricao', ''),
                    data_atual
                ))
            
            # Migrar associações de usuários aos grupos
            for id_grupo, dados in grupos.items():
                # Obter o ID do grupo
                cursor.execute("SELECT id FROM grupos WHERE id_grupo = ?", (id_grupo,))
                resultado = cursor.fetchone()
                if resultado:
                    id_grupo_bd = resultado[0]
                    
                    # Associar usuários ao grupo
                    for username in dados.get('usuarios', []):
                        cursor.execute("SELECT id FROM usuarios WHERE username = ?", (username,))
                        resultado_usuario = cursor.fetchone()
                        if resultado_usuario:
                            id_usuario = resultado_usuario[0]
                            
                            cursor.execute('''
                            INSERT OR IGNORE INTO usuarios_grupos (id_usuario, id_grupo, data_associacao)
                            VALUES (?, ?, ?)
                            ''', (id_usuario, id_grupo_bd, data_atual))
            
            conexao.commit()
            conexao.close()
            depurar_logs(f"Migrados {len(grupos)} grupos e suas associações", "INFO")
        
        # 5. Migrar clientes
        clientes_existentes = set()
        
        # Primeiro, obter clientes do arquivo clientes.csv
        if os.path.isfile('clientes.csv'):
            df_clientes = pd.read_csv('clientes.csv')
            
            conexao, cursor = criar_conexao()
            data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            for _, row in df_clientes.iterrows():
                nome_cliente = row['cliente']
                if nome_cliente not in clientes_existentes:
                    cursor.execute('''
                    INSERT OR IGNORE INTO clientes (nome, data_criacao)
                    VALUES (?, ?)
                    ''', (nome_cliente, data_atual))
                    clientes_existentes.add(nome_cliente)
            
            conexao.commit()
            conexao.close()
            depurar_logs(f"Migrados {len(clientes_existentes)} clientes do arquivo clientes.csv", "INFO")
        
        # Depois, obter clientes do arquivo produtos_monitorados.csv
        if os.path.isfile('produtos_monitorados.csv'):
            df_produtos = pd.read_csv('produtos_monitorados.csv')
            
            conexao, cursor = criar_conexao()
            data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Migrar clientes que ainda não existem no banco
            clientes_produtos = df_produtos['cliente'].unique()
            novos_clientes = 0
            
            for nome_cliente in clientes_produtos:
                if nome_cliente not in clientes_existentes:
                    cursor.execute('''
                    INSERT OR IGNORE INTO clientes (nome, data_criacao)
                    VALUES (?, ?)
                    ''', (nome_cliente, data_atual))
                    clientes_existentes.add(nome_cliente)
                    novos_clientes += 1
            
            conexao.commit()
            conexao.close()
            depurar_logs(f"Migrados mais {novos_clientes} clientes do arquivo produtos_monitorados.csv", "INFO")
            
            # Migrar associações entre clientes e grupos
            if os.path.isfile('grupos.json'):
                with open('grupos.json', 'r', encoding='utf-8') as f:
                    grupos = json.load(f)
                
                conexao, cursor = criar_conexao()
                
                for id_grupo, dados in grupos.items():
                    # Obter o ID do grupo
                    cursor.execute("SELECT id FROM grupos WHERE id_grupo = ?", (id_grupo,))
                    resultado = cursor.fetchone()
                    if resultado:
                        id_grupo_bd = resultado[0]
                        
                        # Associar clientes ao grupo
                        for nome_cliente in dados.get('clientes', []):
                            cursor.execute("SELECT id FROM clientes WHERE nome = ?", (nome_cliente,))
                            resultado_cliente = cursor.fetchone()
                            if resultado_cliente:
                                id_cliente = resultado_cliente[0]
                                
                                cursor.execute('''
                                INSERT OR IGNORE INTO clientes_grupos (id_cliente, id_grupo, data_associacao)
                                VALUES (?, ?, ?)
                                ''', (id_cliente, id_grupo_bd, data_atual))
                
                conexao.commit()
                conexao.close()
                depurar_logs("Migradas associações entre clientes e grupos", "INFO")
        
        # 6. Migrar produtos
        if os.path.isfile('produtos_monitorados.csv'):
            df_produtos = pd.read_csv('produtos_monitorados.csv')
            
            # Verificar se a coluna 'plataforma' existe
            if 'plataforma' not in df_produtos.columns:
                df_produtos['plataforma'] = ''
            
            # Verificar se a coluna 'grupo' existe
            if 'grupo' not in df_produtos.columns:
                df_produtos['grupo'] = 'admin'
            
            conexao, cursor = criar_conexao()
            data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            produtos_migrados = 0
            
            for _, row in df_produtos.iterrows():
                # Obter ID do cliente
                cursor.execute("SELECT id FROM clientes WHERE nome = ?", (row['cliente'],))
                resultado_cliente = cursor.fetchone()
                if resultado_cliente:
                    id_cliente = resultado_cliente[0]
                    
                    # Obter ID do grupo
                    cursor.execute("SELECT id FROM grupos WHERE id_grupo = ?", (row['grupo'],))
                    resultado_grupo = cursor.fetchone()
                    if resultado_grupo:
                        id_grupo = resultado_grupo[0]
                        
                        # Obter ID da plataforma (se existir)
                        id_plataforma = None
                        if row['plataforma'] and row['plataforma'] != '':
                            cursor.execute("SELECT id FROM plataformas WHERE nome = ?", (row['plataforma'],))
                            resultado_plataforma = cursor.fetchone()
                            if resultado_plataforma:
                                id_plataforma = resultado_plataforma[0]
                        
                        # Inserir produto
                        cursor.execute('''
                        INSERT INTO produtos (id_cliente, nome, concorrente, url, id_plataforma, id_grupo, data_criacao)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            id_cliente,
                            row['produto'],
                            row['concorrente'],
                            row['url'],
                            id_plataforma,
                            id_grupo,
                            data_atual
                        ))
                        produtos_migrados += 1
            
            conexao.commit()
            conexao.close()
            depurar_logs(f"Migrados {produtos_migrados} produtos", "INFO")
        
        # 7. Migrar histórico de preços
        if os.path.isfile('historico_precos.csv'):
            df_historico = pd.read_csv('historico_precos.csv')
            
            conexao, cursor = criar_conexao()
            
            historico_migrado = 0
            
            for _, row in df_historico.iterrows():
                # Encontrar o produto correspondente
                cursor.execute('''
                SELECT p.id 
                FROM produtos p
                JOIN clientes c ON p.id_cliente = c.id
                WHERE c.nome = ? AND p.nome = ? AND p.concorrente = ? AND p.url = ?
                ''', (row['cliente'], row['produto'], row['concorrente'], row['url']))
                
                resultado_produto = cursor.fetchone()
                if resultado_produto:
                    id_produto = resultado_produto[0]
                    
                    # Inserir o registro de histórico
                    cursor.execute('''
                    INSERT INTO historico_precos (id_produto, preco, data)
                    VALUES (?, ?, ?)
                    ''', (
                        id_produto,
                        row['preco'],
                        row['data']
                    ))
                    historico_migrado += 1
            
            conexao.commit()
            conexao.close()
            depurar_logs(f"Migrados {historico_migrado} registros de histórico de preços", "INFO")
        
        # 8. Migrar configuração de agendamento
        if os.path.isfile('agendamento_config.json'):
            import json
            with open('agendamento_config.json', 'r', encoding='utf-8') as f:
                agendamento = json.load(f)
            
            conexao, cursor = criar_conexao()
            data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute('''
            INSERT INTO agendamento (tipo, dia, horario, ativo, data_criacao)
            VALUES (?, ?, ?, ?, ?)
            ''', (
                agendamento.get('tipo', ''),
                agendamento.get('dia', ''),
                agendamento.get('horario', ''),
                1,  # Ativo por padrão
                data_atual
            ))
            
            conexao.commit()
            conexao.close()
            depurar_logs("Migrada configuração de agendamento", "INFO")
        
        depurar_logs("Migração concluída com sucesso!", "INFO")
        return True
    except Exception as e:
        depurar_logs(f"Erro durante a migração: {e}", "ERROR")
        return False