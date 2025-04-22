#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Controlador para operações com produtos.
"""

from models.produto import Produto
from models.cliente import Cliente
from models.grupo import Grupo
from utils.logger import Logger
from scraper.price_scraper import PriceScraper

class ProdutoController:
    @staticmethod
    def adicionar_produto(cliente=None, produto=None, concorrente=None, url=None, usuario_atual=None):
        """
        Adiciona um novo produto para monitoramento.
        
        Args:
            cliente (str): Nome do cliente
            produto (str): Nome do produto
            concorrente (str): Nome do concorrente
            url (str): URL do produto
            usuario_atual (str): Nome do usuário que está adicionando o produto
            
        Returns:
            bool: True se o produto foi adicionado com sucesso, False caso contrário
        """
        from controllers.auth_controller import AuthController
        
        # Validar parâmetros
        if not cliente or not produto or not concorrente or not url:
            return False
        
        # Verificar permissão do usuário para este cliente
        if usuario_atual and not AuthController.verificar_permissao_cliente(usuario_atual, cliente):
            Logger.log(f"Usuário {usuario_atual} tentou adicionar produto para cliente não autorizado: {cliente}", "WARNING")
            return False
        
        try:
            # Buscar cliente
            cliente_obj = Cliente.buscar_por_nome(cliente)
            
            if not cliente_obj:
                # Cliente não existe, criar
                cliente_obj = Cliente(nome=cliente)
                if not cliente_obj.salvar():
                    return False
            
            # Determinar o grupo do usuário
            id_grupo = None
            
            if usuario_atual:
                if usuario_atual == "admin" or AuthController.verificar_pertence_grupo(usuario_atual, "admin"):
                    # Admin usa o grupo 'admin'
                    grupo = Grupo.buscar_por_id_grupo("admin")
                    if grupo:
                        id_grupo = grupo.id
                else:
                    # Usuário comum usa seu grupo pessoal
                    grupo = Grupo.buscar_por_id_grupo(usuario_atual)
                    if grupo:
                        id_grupo = grupo.id
            
            if not id_grupo:
                # Se não encontrou grupo, usa o grupo 'admin' como padrão
                grupo = Grupo.buscar_por_id_grupo("admin")
                if grupo:
                    id_grupo = grupo.id
                else:
                    Logger.log("Grupo 'admin' não encontrado", "ERROR")
                    return False
            
            # Extrair o domínio da URL para buscar seletor
            scraper = PriceScraper()
            dominio = scraper.extrair_dominio(url)
            
            # Buscar seletor CSS adequado para a URL
            seletor_css = scraper.obter_seletor_para_url(url)
            
            if not seletor_css:
                Logger.log(f"Não foi possível obter um seletor CSS para a URL: {url}", "WARNING")
                return False
            
            # Testar o seletor
            preco_teste = scraper.extrair_preco(url, seletor_css)
            
            if not preco_teste:
                Logger.log(f"Teste de seletor falhou para URL: {url}", "WARNING")
                return False
            
            # Criar e salvar o produto
            novo_produto = Produto(
                id_cliente=cliente_obj.id,
                nome=produto,
                concorrente=concorrente,
                url=url,
                id_grupo=id_grupo
            )
            
            if not novo_produto.salvar():
                return False
            
            # Registrar preço inicial
            novo_produto.registrar_preco(seletor_css)
            
            # Adicionar produto à fila de agendamento
            novo_produto.adicionar_a_fila()
            
            Logger.log(f"Produto '{produto}' do cliente '{cliente}' adicionado por {usuario_atual}", "INFO")
            return True
            
        except Exception as e:
            Logger.log(f"Erro ao adicionar produto: {e}", "ERROR")
            return False
    
    @staticmethod
    def remover_produto(id_produto, usuario_atual=None):
        """
        Remove um produto da lista de monitoramento.
        
        Args:
            id_produto (int): ID do produto a ser removido
            usuario_atual (str): Nome do usuário que está removendo o produto
            
        Returns:
            bool: True se o produto foi removido com sucesso, False caso contrário
        """
        try:
            from controllers.auth_controller import AuthController
            
            # Buscar o produto
            produto = Produto.buscar_por_id(id_produto)
            
            if not produto:
                return False
            
            # Buscar o cliente do produto
            cliente = Cliente.buscar_por_id(produto.id_cliente)
            
            if not cliente:
                return False
            
            # Verificar permissão do usuário para este cliente
            if usuario_atual and not AuthController.verificar_permissao_cliente(usuario_atual, cliente.nome):
                Logger.log(f"Usuário {usuario_atual} tentou remover produto para cliente não autorizado: {cliente.nome}", "WARNING")
                return False
            
            # Excluir o produto
            if not Produto.excluir(id_produto):
                return False
            
            Logger.log(f"Produto ID {id_produto} removido por {usuario_atual}", "INFO")
            return True
            
        except Exception as e:
            Logger.log(f"Erro ao remover produto: {e}", "ERROR")
            return False
    
    @staticmethod
    def listar_produtos(cliente=None, usuario_atual=None):
        """
        Lista os produtos monitorados, opcionalmente filtrados por cliente.
        
        Args:
            cliente (str): Nome do cliente para filtrar
            usuario_atual (str): Nome do usuário atual
            
        Returns:
            list: Lista dos produtos encontrados
        """
        try:
            from controllers.auth_controller import AuthController
            from controllers.cliente_controller import ClienteController
            
            # Lista para armazenar os produtos
            produtos_resultado = []
            
            # Se um cliente específico foi informado
            if cliente:
                # Buscar cliente
                cliente_obj = Cliente.buscar_por_nome(cliente)
                
                if not cliente_obj:
                    return []
                
                # Verificar permissão do usuário para este cliente
                if usuario_atual and not AuthController.verificar_permissao_cliente(usuario_atual, cliente):
                    Logger.log(f"Usuário {usuario_atual} tentou listar produtos para cliente não autorizado: {cliente}", "WARNING")
                    return []
                
                # Buscar produtos do cliente
                produtos = Produto.listar_por_cliente(cliente_obj.id)
                
                # Converter para formato de dicionário
                for p in produtos:
                    produtos_resultado.append({
                        'id': p.id,
                        'cliente': cliente,
                        'produto': p.nome,
                        'concorrente': p.concorrente,
                        'url': p.url,
                        'grupo': None  # Será preenchido depois
                    })
            else:
                # Listar todos os clientes que o usuário tem acesso
                clientes_permitidos = ClienteController.listar_clientes(usuario_atual)
                
                for cliente_info in clientes_permitidos:
                    # Buscar produtos de cada cliente
                    cliente_obj = Cliente.buscar_por_id(cliente_info['id'])
                    if cliente_obj:
                        produtos = Produto.listar_por_cliente(cliente_obj.id)
                        
                        # Adicionar à lista de resultados
                        for p in produtos:
                            produtos_resultado.append({
                                'id': p.id,
                                'cliente': cliente_obj.nome,
                                'produto': p.nome,
                                'concorrente': p.concorrente,
                                'url': p.url,
                                'grupo': None  # Será preenchido depois
                            })
            
            # Obter informações dos grupos
            for produto in produtos_resultado:
                p_obj = Produto.buscar_por_id(produto['id'])
                if p_obj and p_obj.id_grupo:
                    grupo = Grupo.buscar_por_id(p_obj.id_grupo)
                    if grupo:
                        produto['grupo'] = grupo.id_grupo
            
            return produtos_resultado
            
        except Exception as e:
            Logger.log(f"Erro ao listar produtos: {e}", "ERROR")
            return []
    
    @staticmethod
    def monitorar_todos_produtos(usuario_atual=None, verificacao_manual=False, limite_produtos=None):
        """
        Monitora produtos cadastrados, extraindo e registrando seus preços.
        
        Args:
            usuario_atual (str): Nome do usuário que solicitou o monitoramento
            verificacao_manual (bool): Se True, marca os produtos como verificados manualmente
            limite_produtos (int): Limita o número de produtos a serem verificados
            
        Returns:
            bool: True se pelo menos um produto foi monitorado com sucesso, False caso contrário
        """
        try:
            scraper = PriceScraper()
            
            # Se é um monitoramento automático e temos um limite, usamos a fila
            if not verificacao_manual and limite_produtos:
                from controllers.scheduler_controller import SchedulerController
                produtos_ids = SchedulerController.obter_proximos_produtos_fila(limite_produtos)
                
                if not produtos_ids:
                    Logger.log("Fila de agendamento vazia", "INFO")
                    return True
                
                produtos = []
                for id_produto in produtos_ids:
                    produto = Produto.buscar_por_id(id_produto)
                    if produto:
                        produtos.append(produto)
            else:
                # Buscar produtos com base nas permissões do usuário
                produtos_info = ProdutoController.listar_produtos(usuario_atual=usuario_atual)
                
                produtos = []
                for info in produtos_info:
                    produto = Produto.buscar_por_id(info['id'])
                    if produto:
                        produtos.append(produto)
            
            if not produtos:
                Logger.log("Não há produtos para monitorar", "INFO")
                return False
            
            Logger.log(f"Iniciando monitoramento de {len(produtos)} produtos", "INFO")
            
            sucesso = False
            produtos_verificados = 0
            
            for produto in produtos:
                # Buscar seletor CSS adequado para a URL
                seletor_css = scraper.obter_seletor_para_url(produto.url)
                
                if not seletor_css:
                    Logger.log(f"Não foi possível obter um seletor CSS para o produto ID {produto.id}", "WARNING")
                    continue
                
                # Registrar preço
                if produto.registrar_preco(seletor_css, verificacao_manual):
                    sucesso = True
                    produtos_verificados += 1
                
                import time
                time.sleep(0.5)  # Pausa pequena entre requisições
            
            Logger.log(f"Monitoramento concluído: {produtos_verificados}/{len(produtos)} produtos verificados", "INFO")
            return sucesso
            
        except Exception as e:
            Logger.log(f"Erro ao executar monitoramento: {e}", "ERROR")
            return False