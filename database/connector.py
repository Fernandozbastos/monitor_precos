#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo de conexão com o banco de dados para o Sistema de Monitoramento de Preços.
"""

import os
import sqlite3
from datetime import datetime
from utils.logger import Logger

class DatabaseConnector:
    # Caminho do banco de dados
    DB_FILE = 'monitor_precos.db'
    
    def criar_conexao(self):
        """
        Cria uma conexão com o banco de dados SQLite.
        
        Returns:
            tuple: (conexao, cursor) para interagir com o banco de dados
        """
        conexao = sqlite3.connect(self.DB_FILE)
        conexao.row_factory = sqlite3.Row  # Permite acessar colunas pelo nome
        cursor = conexao.cursor()
        return conexao, cursor
    
    def inicializar_banco_dados(self):
        """
        Cria as tabelas do banco de dados se não existirem.
        
        Returns:
            bool: True se a inicialização foi bem-sucedida, False caso contrário
        """
        try:
            conexao, cursor = self.criar_conexao()
            
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
            
            # Tabela de fila de agendamento
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS fila_agendamento (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_produto INTEGER NOT NULL,
                posicao_fila INTEGER NOT NULL,
                data_inclusao TEXT NOT NULL,
                ultima_verificacao TEXT,
                verificacao_manual INTEGER DEFAULT 0,
                FOREIGN KEY (id_produto) REFERENCES produtos (id),
                UNIQUE(id_produto)
            )
            ''')
            
            # Criar índice para otimizar consultas
            cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_fila_posicao ON fila_agendamento (posicao_fila)
            ''')
            
            conexao.commit()
            conexao.close()
            
            # Criar grupos padrão e usuário admin
            self._criar_dados_padrao()
            
            Logger.log("Banco de dados inicializado com sucesso", "INFO")
            return True
            
        except Exception as e:
            Logger.log(f"Erro ao inicializar banco de dados: {e}", "ERROR")
            return False
    
    def _criar_dados_padrao(self):
        """
        Cria grupos padrão (admin e all) e usuário admin se não existirem.
        """
        try:
            conexao, cursor = self.criar_conexao()
            
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
            
            # Verificar se o usuário 'admin' já existe
            cursor.execute("SELECT id FROM usuarios WHERE username = 'admin'")
            if not cursor.fetchone():
                import hashlib
                senha_hash = hashlib.sha256('admin'.encode()).hexdigest()
                
                cursor.execute('''
                INSERT INTO usuarios (username, senha, nome, tipo, ativo, data_criacao)
                VALUES (?, ?, ?, ?, ?, ?)
                ''', ('admin', senha_hash, 'Administrador', 'admin', 1, data_atual))
                
                # Obter ID do usuário admin
                cursor.execute("SELECT id FROM usuarios WHERE username = 'admin'")
                id_usuario = cursor.fetchone()['id']
                
                # Obter ID dos grupos admin e all
                cursor.execute("SELECT id FROM grupos WHERE id_grupo = 'admin'")
                id_grupo_admin = cursor.fetchone()['id']
                
                cursor.execute("SELECT id FROM grupos WHERE id_grupo = 'all'")
                id_grupo_all = cursor.fetchone()['id']
                
                # Associar usuário admin aos grupos admin e all
                cursor.execute('''
                INSERT OR IGNORE INTO usuarios_grupos (id_usuario, id_grupo, data_associacao)
                VALUES (?, ?, ?)
                ''', (id_usuario, id_grupo_admin, data_atual))
                
                cursor.execute('''
                INSERT OR IGNORE INTO usuarios_grupos (id_usuario, id_grupo, data_associacao)
                VALUES (?, ?, ?)
                ''', (id_usuario, id_grupo_all, data_atual))
            
            conexao.commit()
            conexao.close()
            
            Logger.log("Dados padrão verificados/criados com sucesso", "INFO")
            return True
            
        except Exception as e:
            Logger.log(f"Erro ao criar dados padrão: {e}", "ERROR")
            return False
    
def executar_query(self, query, params=None):
        """
        Executa uma query SQL no banco de dados.
        
        Args:
            query (str): Query SQL a ser executada
            params (tuple, optional): Parâmetros para a query
            
        Returns:
            list: Lista com os resultados da query
        """
        try:
            conexao, cursor = self.criar_conexao()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
                
            resultados = cursor.fetchall()
            conexao.commit()
            conexao.close()
            
            return [dict(resultado) for resultado in resultados]
            
        except Exception as e:
            Logger.log(f"Erro ao executar query: {e}", "ERROR")
            return []
    
def executar_comando(self, comando, params=None):
        """
        Executa um comando SQL no banco de dados (INSERT, UPDATE, DELETE).
        
        Args:
            comando (str): Comando SQL a ser executado
            params (tuple, optional): Parâmetros para o comando
            
        Returns:
            bool: True se a operação foi bem-sucedida, False caso contrário
        """
        try:
            conexao, cursor = self.criar_conexao()
            
            if params:
                cursor.execute(comando, params)
            else:
                cursor.execute(comando)
                
            conexao.commit()
            conexao.close()
            
            return True
            
        except Exception as e:
            Logger.log(f"Erro ao executar comando SQL: {e}", "ERROR")
            return False