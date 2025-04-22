#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Model que representa o histórico de preços no sistema.
"""

from datetime import datetime
from database.connector import DatabaseConnector

class Historico:
    def __init__(self, id=None, id_produto=None, preco=None, data=None):
        self.id = id
        self.id_produto = id_produto
        self.preco = preco
        self.data = data if data else datetime.now().strftime('%Y-%m-%d')
        self.db = DatabaseConnector()
    
    def salvar(self):
        """
        Salva o registro de preço no histórico.
        
        Returns:
            bool: True se a operação foi bem-sucedida, False caso contrário
        """
        try:
            conexao, cursor = self.db.criar_conexao()
            
            # Inserir novo registro
            cursor.execute('''
            INSERT INTO historico_precos (id_produto, preco, data)
            VALUES (?, ?, ?)
            ''', (self.id_produto, self.preco, self.data))
            
            self.id = cursor.lastrowid
            
            conexao.commit()
            conexao.close()
            
            from utils.logger import Logger
            Logger.log(f"Preço {self.preco} registrado para o produto ID {self.id_produto}", "INFO")
            return True
            
        except Exception as e:
            from utils.logger import Logger
            Logger.log(f"Erro ao salvar histórico de preço: {str(e)}", "ERROR")
            return False
    
    @classmethod
    def buscar_por_produto(cls, id_produto):
        """
        Busca o histórico de preços de um produto.
        
        Args:
            id_produto (int): ID do produto
            
        Returns:
            list: Lista de objetos Historico
        """
        try:
            db = DatabaseConnector()
            conexao, cursor = db.criar_conexao()
            
            cursor.execute('''
            SELECT id, id_produto, preco, data
            FROM historico_precos
            WHERE id_produto = ?
            ORDER BY data DESC
            ''', (id_produto,))
            
            resultados = cursor.fetchall()
            conexao.close()
            
            historico = []
            for resultado in resultados:
                historico.append(cls(
                    id=resultado['id'],
                    id_produto=resultado['id_produto'],
                    preco=resultado['preco'],
                    data=resultado['data']
                ))
            
            return historico
            
        except Exception as e:
            from utils.logger import Logger
            Logger.log(f"Erro ao buscar histórico por produto: {str(e)}", "ERROR")
            return []
    
    @classmethod
    def obter_resumo_produto(cls, id_produto):
        """
        Obtém um resumo dos preços de um produto.
        
        Args:
            id_produto (int): ID do produto
            
        Returns:
            dict: Dicionário com dados resumidos (preço atual, mínimo, máximo, etc.)
        """
        try:
            db = DatabaseConnector()
            conexao, cursor = db.criar_conexao()
            
            cursor.execute('''
            SELECT 
                MAX(data) as ultima_data,
                (SELECT preco FROM historico_precos WHERE id_produto = ? ORDER BY data DESC LIMIT 1) as preco_atual,
                MIN(preco) as preco_minimo,
                MAX(preco) as preco_maximo,
                AVG(preco) as preco_medio,
                COUNT(*) as total_registros
            FROM historico_precos
            WHERE id_produto = ?
            ''', (id_produto, id_produto))
            
            resultado = cursor.fetchone()
            conexao.close()
            
            if resultado:
                return {
                    'ultima_data': resultado['ultima_data'],
                    'preco_atual': resultado['preco_atual'],
                    'preco_minimo': resultado['preco_minimo'],
                    'preco_maximo': resultado['preco_maximo'],
                    'preco_medio': resultado['preco_medio'],
                    'total_registros': resultado['total_registros']
                }
            
            return None
            
        except Exception as e:
            from utils.logger import Logger
            Logger.log(f"Erro ao obter resumo do produto: {str(e)}", "ERROR")
            return None