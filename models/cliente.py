#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Model que representa um cliente no sistema.
"""

from datetime import datetime
from database.connector import DatabaseConnector
from utils.logger import Logger

class Cliente:
    def __init__(self, id=None, nome=None, data_criacao=None):
        self.id = id
        self.nome = nome
        self.data_criacao = data_criacao if data_criacao else datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.db = DatabaseConnector()
    
    def salvar(self):
        """
        Salva o cliente no banco de dados.
        
        Returns:
            bool: True se a operação foi bem-sucedida, False caso contrário
        """
        try:
            conexao, cursor = self.db.criar_conexao()
            
            # Verificar se o cliente já existe
            cursor.execute("SELECT id FROM clientes WHERE nome = ?", (self.nome,))
            resultado = cursor.fetchone()
            
            if resultado:
                self.id = resultado['id']
                conexao.close()
                return True
            
            # Adicionar o novo cliente
            cursor.execute('''
            INSERT INTO clientes (nome, data_criacao)
            VALUES (?, ?)
            ''', (self.nome, self.data_criacao))
            
            self.id = cursor.lastrowid
            
            conexao.commit()
            conexao.close()
            
            Logger.log(f"Cliente '{self.nome}' salvo com sucesso", "INFO")
            return True
            
        except Exception as e:
            Logger.log(f"Erro ao salvar cliente: {str(e)}", "ERROR")
            return False
    
    @classmethod
    def buscar_por_id(cls, id_cliente):
        """
        Busca um cliente pelo ID.
        
        Args:
            id_cliente (int): ID do cliente
            
        Returns:
            Cliente: Objeto Cliente ou None se não encontrado
        """
        try:
            db = DatabaseConnector()
            conexao, cursor = db.criar_conexao()
            
            cursor.execute("SELECT * FROM clientes WHERE id = ?", (id_cliente,))
            resultado = cursor.fetchone()
            
            conexao.close()
            
            if resultado:
                return cls(
                    id=resultado['id'],
                    nome=resultado['nome'],
                    data_criacao=resultado['data_criacao']
                )
            return None
            
        except Exception as e:
            Logger.log(f"Erro ao buscar cliente por ID: {str(e)}", "ERROR")
            return None
    
    @classmethod
    def buscar_por_nome(cls, nome_cliente):
        """
        Busca um cliente pelo nome.
        
        Args:
            nome_cliente (str): Nome do cliente
            
        Returns:
            Cliente: Objeto Cliente ou None se não encontrado
        """
        try:
            db = DatabaseConnector()
            conexao, cursor = db.criar_conexao()
            
            cursor.execute("SELECT * FROM clientes WHERE nome = ?", (nome_cliente,))
            resultado = cursor.fetchone()
            
            conexao.close()
            
            if resultado:
                return cls(
                    id=resultado['id'],
                    nome=resultado['nome'],
                    data_criacao=resultado['data_criacao']
                )
            return None
            
        except Exception as e:
            Logger.log(f"Erro ao buscar cliente por nome: {str(e)}", "ERROR")
            return None
    
    @classmethod
    def listar_todos(cls):
        """
        Lista todos os clientes cadastrados.
        
        Returns:
            list: Lista de objetos Cliente
        """
        try:
            db = DatabaseConnector()
            conexao, cursor = db.criar_conexao()
            
            cursor.execute("SELECT * FROM clientes ORDER BY nome")
            resultados = cursor.fetchall()
            
            conexao.close()
            
            clientes = []
            for resultado in resultados:
                clientes.append(cls(
                    id=resultado['id'],
                    nome=resultado['nome'],
                    data_criacao=resultado['data_criacao']
                ))
            
            return clientes
            
        except Exception as e:
            Logger.log(f"Erro ao listar clientes: {str(e)}", "ERROR")
            return []
    
    @classmethod
    def excluir(cls, id_cliente):
        """
        Exclui um cliente do sistema.
        
        Args:
            id_cliente (int): ID do cliente
            
        Returns:
            bool: True se a operação foi bem-sucedida, False caso contrário
        """
        try:
            db = DatabaseConnector()
            conexao, cursor = db.criar_conexao()
            
            # Verificar se há produtos associados ao cliente
            cursor.execute("SELECT COUNT(*) as count FROM produtos WHERE id_cliente = ?", (id_cliente,))
            resultado = cursor.fetchone()
            
            if resultado and resultado['count'] > 0:
                Logger.log(f"Não é possível excluir cliente ID {id_cliente} pois possui produtos associados", "WARNING")
                conexao.close()
                return False
            
            # Remover associações com grupos
            cursor.execute("DELETE FROM clientes_grupos WHERE id_cliente = ?", (id_cliente,))
            
            # Remover o cliente
            cursor.execute("DELETE FROM clientes WHERE id = ?", (id_cliente,))
            
            conexao.commit()
            conexao.close()
            
            Logger.log(f"Cliente ID {id_cliente} excluído com sucesso", "INFO")
            return True
            
        except Exception as e:
            Logger.log(f"Erro ao excluir cliente: {str(e)}", "ERROR")
            return False