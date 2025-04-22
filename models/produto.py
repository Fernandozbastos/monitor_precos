#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Model que representa um produto monitorado no sistema.
"""

from datetime import datetime
from database.connector import DatabaseConnector
from utils.logger import Logger
from scraper.price_scraper import PriceScraper

class Produto:
    def __init__(self, id=None, id_cliente=None, nome=None, concorrente=None, 
                 url=None, id_plataforma=None, id_grupo=None, data_criacao=None):
        self.id = id
        self.id_cliente = id_cliente
        self.nome = nome
        self.concorrente = concorrente
        self.url = url
        self.id_plataforma = id_plataforma
        self.id_grupo = id_grupo
        self.data_criacao = data_criacao if data_criacao else datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.db = DatabaseConnector()
    
    def salvar(self):
        """
        Salva o produto no banco de dados.
        
        Returns:
            bool: True se a operação foi bem-sucedida, False caso contrário
        """
        try:
            conexao, cursor = self.db.criar_conexao()
            
            # Verificar se o produto já existe para este cliente e grupo
            cursor.execute('''
            SELECT id FROM produtos 
            WHERE id_cliente = ? AND nome = ? AND url = ? AND id_grupo = ?
            ''', (self.id_cliente, self.nome, self.url, self.id_grupo))
            
            resultado = cursor.fetchone()
            
            if resultado:
                self.id = resultado['id']
                
                # Atualizar produto existente
                cursor.execute('''
                UPDATE produtos 
                SET concorrente = ?, id_plataforma = ?
                WHERE id = ?
                ''', (self.concorrente, self.id_plataforma, self.id))
            else:
                # Inserir novo produto
                cursor.execute('''
                INSERT INTO produtos (id_cliente, nome, concorrente, url, id_plataforma, id_grupo, data_criacao)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (self.id_cliente, self.nome, self.concorrente, self.url, 
                      self.id_plataforma, self.id_grupo, self.data_criacao))
                
                self.id = cursor.lastrowid
            
            conexao.commit()
            conexao.close()
            
            # Adicionar o produto à fila de agendamento
            self.adicionar_a_fila()
            
            Logger.log(f"Produto '{self.nome}' (ID: {self.id}) salvo com sucesso", "INFO")
            return True
            
        except Exception as e:
            Logger.log(f"Erro ao salvar produto: {e}", "ERROR")
            return False
    
    def registrar_preco(self, seletor_css, verificacao_manual=False):
        """
        Registra o preço atual do produto.
        
        Args:
            seletor_css (str): Seletor CSS para extrair o preço
            verificacao_manual (bool): Se True, marca como verificação manual
            
        Returns:
            bool: True se a operação foi bem-sucedida, False caso contrário
        """
        try:
            scraper = PriceScraper()
            
            # Extrair o preço usando o seletor
            preco_texto = scraper.extrair_preco(self.url, seletor_css)
            
            if not preco_texto:
                Logger.log(f"Não foi possível extrair o preço para o produto ID {self.id}", "WARNING")
                return False
                
            valor = scraper.converter_preco(preco_texto)
            
            if valor is None:
                Logger.log(f"Não foi possível converter o preço '{preco_texto}' para o produto ID {self.id}", "WARNING")
                return False
            
            # Registrar o preço no histórico
            conexao, cursor = self.db.criar_conexao()
            data_hoje = datetime.now().strftime('%Y-%m-%d')
            
            cursor.execute('''
            INSERT INTO historico_precos (id_produto, preco, data) 
            VALUES (?, ?, ?)
            ''', (self.id, valor, data_hoje))
            
            conexao.commit()
            conexao.close()
            
            # Atualizar o status na fila de agendamento
            if verificacao_manual:
                self.remover_da_fila_do_dia()
                Logger.log(f"Preço R$ {valor:.2f} registrado para o produto ID {self.id} (verificação manual)", "INFO")
            else:
                self.mover_para_final_da_fila()
                Logger.log(f"Preço R$ {valor:.2f} registrado para o produto ID {self.id}", "INFO")
            
            return True
            
        except Exception as e:
            Logger.log(f"Erro ao registrar preço: {e}", "ERROR")
            return False
    
    def adicionar_a_fila(self):
        """
        Adiciona o produto à fila de agendamento.
        
        Returns:
            bool: True se a operação foi bem-sucedida, False caso contrário
        """
        try:
            conexao, cursor = self.db.criar_conexao()
            
            # Verificar se o produto já está na fila
            cursor.execute("SELECT id FROM fila_agendamento WHERE id_produto = ?", (self.id,))
            if cursor.fetchone():
                conexao.close()
                return True  # Produto já está na fila
            
            # Buscar a última posição da fila
            cursor.execute("SELECT MAX(posicao_fila) as ultima_posicao FROM fila_agendamento")
            resultado = cursor.fetchone()
            ultima_posicao = resultado['ultima_posicao'] if resultado and resultado['ultima_posicao'] is not None else 0
            
            # Adicionar o produto na última posição
            data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute('''
            INSERT INTO fila_agendamento (id_produto, posicao_fila, data_inclusao)
            VALUES (?, ?, ?)
            ''', (self.id, ultima_posicao + 1, data_atual))
            
            conexao.commit()
            conexao.close()
            
            Logger.log(f"Produto ID {self.id} adicionado à fila de agendamento", "INFO")
            return True
            
        except Exception as e:
            Logger.log(f"Erro ao adicionar produto à fila: {e}", "ERROR")
            return False
    
    def mover_para_final_da_fila(self):
        """
        Move o produto para o final da fila de agendamento.
        
        Returns:
            bool: True se a operação foi bem-sucedida, False caso contrário
        """
        try:
            conexao, cursor = self.db.criar_conexao()
            
            # Verificar se o produto está na fila
            cursor.execute("SELECT id FROM fila_agendamento WHERE id_produto = ?", (self.id,))
            if not cursor.fetchone():
                conexao.close()
                return self.adicionar_a_fila()  # Se não estiver na fila, adiciona
            
            # Buscar a última posição da fila
            cursor.execute("SELECT MAX(posicao_fila) as ultima_posicao FROM fila_agendamento")
            resultado = cursor.fetchone()
            ultima_posicao = resultado['ultima_posicao'] if resultado and resultado['ultima_posicao'] is not None else 0
            
            # Atualizar a posição do produto para o final da fila
            data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute('''
            UPDATE fila_agendamento 
            SET posicao_fila = ?, ultima_verificacao = ?, verificacao_manual = 0
            WHERE id_produto = ?
            ''', (ultima_posicao + 1, data_atual, self.id))
            
            # Reorganizar a fila (opcional, mas mantém os números sequenciais)
            cursor.execute('''
            SELECT id, id_produto, posicao_fila
            FROM fila_agendamento
            ORDER BY posicao_fila
            ''')
            
            produtos_fila = cursor.fetchall()
            
            for i, produto in enumerate(produtos_fila, 1):
                cursor.execute('''
                UPDATE fila_agendamento
                SET posicao_fila = ?
                WHERE id = ?
                ''', (i, produto['id']))
            
            conexao.commit()
            conexao.close()
            
            Logger.log(f"Produto ID {self.id} movido para o final da fila", "INFO")
            return True
            
        except Exception as e:
            Logger.log(f"Erro ao mover produto para o final da fila: {e}", "ERROR")
            return False
    
    def remover_da_fila_do_dia(self):
        """
        Marca o produto como verificado manualmente.
        
        Returns:
            bool: True se a operação foi bem-sucedida, False caso contrário
        """
        try:
            conexao, cursor = self.db.criar_conexao()
            
            # Verificar se o produto está na fila
            cursor.execute("SELECT id FROM fila_agendamento WHERE id_produto = ?", (self.id,))
            if not cursor.fetchone():
                conexao.close()
                return self.adicionar_a_fila()  # Se não estiver na fila, adiciona
            
            # Marcar o produto como verificado manualmente
            data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute('''
            UPDATE fila_agendamento 
            SET verificacao_manual = 1, ultima_verificacao = ?
            WHERE id_produto = ?
            ''', (data_atual, self.id))
            
            conexao.commit()
            conexao.close()
            
            Logger.log(f"Produto ID {self.id} removido da fila do dia (verificação manual)", "INFO")
            return True
            
        except Exception as e:
            Logger.log(f"Erro ao remover produto da fila do dia: {e}", "ERROR")
            return False
    
    def obter_historico(self):
        """
        Obtém o histórico de preços deste produto.
        
        Returns:
            list: Lista de dicionários com informações de preço e data
        """
        try:
            conexao, cursor = self.db.criar_conexao()
            
            cursor.execute('''
            SELECT id, preco, data
            FROM historico_precos
            WHERE id_produto = ?
            ORDER BY data DESC
            ''', (self.id,))
            
            historico = cursor.fetchall()
            conexao.close()
            
            resultado = []
            for registro in historico:
                resultado.append({
                    'id': registro['id'],
                    'preco': registro['preco'],
                    'data': registro['data']
                })
            
            return resultado
            
        except Exception as e:
            Logger.log(f"Erro ao obter histórico do produto: {e}", "ERROR")
            return []
    
    @classmethod
    def buscar_por_id(cls, id_produto):
        """
        Busca um produto pelo ID.
        
        Args:
            id_produto (int): ID do produto
            
        Returns:
            Produto: Objeto Produto ou None se não encontrado
        """
        try:
            db = DatabaseConnector()
            conexao, cursor = db.criar_conexao()
            
            cursor.execute('''
            SELECT * FROM produtos WHERE id = ?
            ''', (id_produto,))
            
            resultado = cursor.fetchone()
            conexao.close()
            
            if resultado:
                return cls(
                    id=resultado['id'],
                    id_cliente=resultado['id_cliente'],
                    nome=resultado['nome'],
                    concorrente=resultado['concorrente'],
                    url=resultado['url'],
                    id_plataforma=resultado['id_plataforma'],
                    id_grupo=resultado['id_grupo'],
                    data_criacao=resultado['data_criacao']
                )
            return None
            
        except Exception as e:
            Logger.log(f"Erro ao buscar produto por ID: {e}", "ERROR")
            return None
    
    @classmethod
    def listar_por_cliente(cls, id_cliente, id_grupo=None):
        """
        Lista todos os produtos de um cliente.
        
        Args:
            id_cliente (int): ID do cliente
            id_grupo (int, optional): ID do grupo para filtrar
            
        Returns:
            list: Lista de objetos Produto
        """
        try:
            db = DatabaseConnector()
            conexao, cursor = db.criar_conexao()
            
            if id_grupo:
                cursor.execute('''
                SELECT * FROM produtos 
                WHERE id_cliente = ? AND id_grupo = ?
                ORDER BY nome
                ''', (id_cliente, id_grupo))
            else:
                cursor.execute('''
                SELECT * FROM produtos 
                WHERE id_cliente = ?
                ORDER BY nome
                ''', (id_cliente,))
            
            resultados = cursor.fetchall()
            conexao.close()
            
            produtos = []
            for resultado in resultados:
                produtos.append(cls(
                    id=resultado['id'],
                    id_cliente=resultado['id_cliente'],
                    nome=resultado['nome'],
                    concorrente=resultado['concorrente'],
                    url=resultado['url'],
                    id_plataforma=resultado['id_plataforma'],
                    id_grupo=resultado['id_grupo'],
                    data_criacao=resultado['data_criacao']
                ))
            
            return produtos
            
        except Exception as e:
            Logger.log(f"Erro ao listar produtos por cliente: {e}", "ERROR")
            return []
    
    @classmethod
    def excluir(cls, id_produto):
        """
        Exclui um produto e seus registros relacionados.
        
        Args:
            id_produto (int): ID do produto
            
        Returns:
            bool: True se a operação foi bem-sucedida, False caso contrário
        """
        try:
            db = DatabaseConnector()
            conexao, cursor = db.criar_conexao()
            
            # Remover registros de histórico de preços
            cursor.execute("DELETE FROM historico_precos WHERE id_produto = ?", (id_produto,))
            
            # Remover da fila de agendamento
            cursor.execute("DELETE FROM fila_agendamento WHERE id_produto = ?", (id_produto,))
            
            # Remover o produto
            cursor.execute("DELETE FROM produtos WHERE id = ?", (id_produto,))
            
            conexao.commit()
            conexao.close()
            
            Logger.log(f"Produto ID {id_produto} excluído com sucesso", "INFO")
            return True
            
        except Exception as e:
            Logger.log(f"Erro ao excluir produto: {e}", "ERROR")
            return False