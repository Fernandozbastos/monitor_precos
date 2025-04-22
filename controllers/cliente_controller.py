#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Controlador para operações com clientes.
"""

from models.cliente import Cliente
from models.grupo import Grupo
from utils.logger import Logger

class ClienteController:
    @staticmethod
    def adicionar_cliente(nome_cliente, usuario_atual=None):
        """
        Adiciona um novo cliente ao sistema.
        
        Args:
            nome_cliente (str): Nome do novo cliente
            usuario_atual (str): Nome do usuário que está adicionando o cliente
            
        Returns:
            bool: True se o cliente foi adicionado com sucesso, False caso contrário
        """
        # Verificar se o nome é válido
        if not nome_cliente:
            return False
        
        try:
            # Verificar se o cliente já existe
            cliente_existente = Cliente.buscar_por_nome(nome_cliente)
            
            if cliente_existente:
                return True  # Cliente já existe
            
            # Criar novo cliente
            novo_cliente = Cliente(nome=nome_cliente)
            
            # Salvar o cliente
            if not novo_cliente.salvar():
                return False
            
            # Associar o cliente aos grupos apropriados
            # Se for admin, adiciona o cliente aos grupos de admin
            from controllers.auth_controller import AuthController
            usuario = AuthController.buscar_usuario_por_username(usuario_atual)
            
            if usuario and (usuario.tipo == 'admin' or AuthController.verificar_pertence_grupo(usuario_atual, 'admin')):
                # Adicionar cliente ao grupo admin
                grupo_admin = Grupo.buscar_por_id_grupo('admin')
                if grupo_admin:
                    grupo_admin.adicionar_cliente(novo_cliente.id)
                
                # Adicionar cliente ao grupo all
                grupo_all = Grupo.buscar_por_id_grupo('all')
                if grupo_all:
                    grupo_all.adicionar_cliente(novo_cliente.id)
            
            # Se não for admin, adiciona ao grupo pessoal do usuário
            elif usuario_atual:
                grupo_usuario = Grupo.buscar_por_id_grupo(usuario_atual)
                if grupo_usuario:
                    grupo_usuario.adicionar_cliente(novo_cliente.id)
                
                # Sempre adiciona ao grupo all
                grupo_all = Grupo.buscar_por_id_grupo('all')
                if grupo_all:
                    grupo_all.adicionar_cliente(novo_cliente.id)
            
            Logger.log(f"Cliente '{nome_cliente}' adicionado por {usuario_atual}", "INFO")
            return True
            
        except Exception as e:
            Logger.log(f"Erro ao adicionar cliente: {e}", "ERROR")
            return False
    
    @staticmethod
    def listar_clientes(usuario_atual=None):
        """
        Lista todos os clientes cadastrados, filtrados por permissão do usuário.
        
        Args:
            usuario_atual (str): Nome do usuário atual
            
        Returns:
            list: Lista de dicionários com informações dos clientes
        """
        try:
            # Se não tem usuário, retorna lista vazia
            if not usuario_atual:
                return []
            
            # Obter permissões do usuário
            from controllers.auth_controller import AuthController
            usuario = AuthController.buscar_usuario_por_username(usuario_atual)
            
            # Se for admin, pode ver todos os clientes
            if usuario and (usuario.tipo == 'admin' or AuthController.verificar_pertence_grupo(usuario_atual, 'admin')):
                clientes = Cliente.listar_todos()
                return [{'nome': c.nome, 'id': c.id} for c in clientes]
            
            # Caso contrário, filtra pelos grupos do usuário
            clientes_permitidos = []
            grupos_usuario = AuthController.obter_grupos_usuario(usuario_atual)
            
            for grupo_id in grupos_usuario:
                grupo = Grupo.buscar_por_id_grupo(grupo_id)
                if grupo:
                    clientes_grupo = grupo.obter_clientes()
                    for cliente in clientes_grupo:
                        if cliente['nome'] not in [c['nome'] for c in clientes_permitidos]:
                            clientes_permitidos.append(cliente)
            
            return clientes_permitidos
            
        except Exception as e:
            Logger.log(f"Erro ao listar clientes: {e}", "ERROR")
            return []