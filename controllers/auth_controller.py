#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Controlador para autenticação e gerenciamento de usuários.
"""

import hashlib
from models.usuario import Usuario
from models.grupo import Grupo
from utils.logger import Logger

class AuthController:
    @staticmethod
    def autenticar(username, senha):
        """
        Autentica um usuário no sistema.
        
        Args:
            username (str): Nome de usuário
            senha (str): Senha do usuário
            
        Returns:
            tuple: (sucesso, usuario, tipo, cliente_atual) onde sucesso é um booleano indicando
                  se a autenticação foi bem-sucedida
        """
        try:
            # Buscar usuário pelo username
            usuario = Usuario.buscar_por_username(username)
            
            if not usuario:
                Logger.log(f"Tentativa de login com usuário inexistente: {username}", "WARNING")
                return False, None, None, None
            
            # Verificar se a conta está ativa
            if not usuario.ativo:
                Logger.log(f"Tentativa de login com conta inativa: {username}", "WARNING")
                return False, None, None, None
            
            # Verificar senha
            if not usuario.verificar_senha(senha):
                Logger.log(f"Tentativa de login falhou para: {username} (senha incorreta)", "WARNING")
                return False, None, None, None
            
            # Registrar acesso
            usuario.registrar_acesso()
            
            Logger.log(f"Login bem-sucedido: {username}", "INFO")
            return True, usuario, usuario.tipo, usuario.cliente_atual
            
        except Exception as e:
            Logger.log(f"Erro durante autenticação: {e}", "ERROR")
            return False, None, None, None
    
    @staticmethod
    def adicionar_usuario(username, senha, nome, tipo='usuario', operador=None):
        """
        Adiciona um novo usuário ao sistema.
        
        Args:
            username (str): Nome de usuário (único)
            senha (str): Senha do usuário
            nome (str): Nome completo/exibição do usuário
            tipo (str): Tipo de usuário ('admin' ou 'usuario')
            operador (str): Nome do usuário que está realizando a operação
            
        Returns:
            bool: True se o usuário foi adicionado com sucesso, False caso contrário
        """
        if not username or not senha or not nome:
            return False
        
        try:
            # Verificar se o usuário já existe
            usuario_existente = Usuario.buscar_por_username(username)
            if usuario_existente:
                Logger.log(f"Tentativa de adicionar usuário já existente: {username} por {operador}", "WARNING")
                return False
            
            # Criar hash da senha
            senha_hash = hashlib.sha256(senha.encode()).hexdigest()
            
            # Criar novo usuário
            novo_usuario = Usuario(
                username=username,
                senha=senha_hash,
                nome=nome,
                tipo=tipo
            )
            
            # Salvar o usuário
            if not novo_usuario.salvar():
                return False
            
            Logger.log(f"Novo usuário adicionado: {username} por {operador}", "INFO")
            return True
            
        except Exception as e:
            Logger.log(f"Erro ao adicionar usuário: {e}", "ERROR")
            return False
    
    @staticmethod
    def alterar_senha(username, senha_atual, nova_senha):
        """
        Altera a senha de um usuário existente.
        
        Args:
            username (str): Nome de usuário
            senha_atual (str): Senha atual do usuário
            nova_senha (str): Nova senha do usuário
            
        Returns:
            bool: True se a senha foi alterada com sucesso, False caso contrário
        """
        try:
            # Buscar usuário
            usuario = Usuario.buscar_por_username(username)
            
            if not usuario:
                return False
            
            # Verificar senha atual
            if not usuario.verificar_senha(senha_atual):
                return False
            
            # Alterar senha
            if not usuario.alterar_senha(nova_senha):
                return False
            
            Logger.log(f"Senha alterada para o usuário: {username}", "INFO")
            return True
            
        except Exception as e:
            Logger.log(f"Erro ao alterar senha: {e}", "ERROR")
            return False
    
    @staticmethod
    def desativar_usuario(username, operador=None):
        """
        Desativa um usuário do sistema (sem removê-lo).
        
        Args:
            username (str): Nome de usuário a ser desativado
            operador (str): Nome do usuário que está realizando a operação
            
        Returns:
            bool: True se o usuário foi desativado com sucesso, False caso contrário
        """
        try:
            # Buscar usuário
            usuario = Usuario.buscar_por_username(username)
            
            if not usuario:
                return False
            
            # Impedir a desativação do próprio operador
            if username == operador:
                Logger.log(f"Tentativa de desativar o próprio usuário: {operador}", "WARNING")
                return False
            
            # Desativar o usuário
            if not usuario.desativar():
                return False
            
            Logger.log(f"Usuário desativado: {username} por {operador}", "INFO")
            return True
            
        except Exception as e:
            Logger.log(f"Erro ao desativar usuário: {e}", "ERROR")
            return False
    
    @staticmethod
    def alterar_cliente_atual(username, novo_cliente):
        """
        Altera o cliente atualmente selecionado pelo usuário.
        
        Args:
            username (str): Nome do usuário
            novo_cliente (str): Nome do novo cliente selecionado
            
        Returns:
            bool: True se o cliente foi alterado com sucesso, False caso contrário
        """
        try:
            # Buscar usuário
            usuario = Usuario.buscar_por_username(username)
            
            if not usuario:
                Logger.log(f"Usuário não encontrado ao alterar cliente atual: {username}", "WARNING")
                return False
            
            # Alterar cliente atual
            if not usuario.alterar_cliente_atual(novo_cliente):
                return False
            
            Logger.log(f"Cliente atual alterado para '{novo_cliente}' pelo usuário: {username}", "INFO")
            return True
            
        except Exception as e:
            Logger.log(f"Erro ao alterar cliente atual: {e}", "ERROR")
            return False
    
    @staticmethod
    def listar_usuarios(mostrar_inativos=False):
        """
        Lista todos os usuários cadastrados no sistema.
        
        Args:
            mostrar_inativos (bool): Se True, mostra também usuários inativos
            
        Returns:
            list: Lista de dicionários com informações dos usuários
        """
        try:
            # Buscar todos os usuários
            usuarios = Usuario.listar_todos()
            
            # Filtrar por status se necessário
            if not mostrar_inativos:
                usuarios = [u for u in usuarios if u.ativo]
            
            # Converter para lista de dicionários
            resultado = []
            for usuario in usuarios:
                info_usuario = {
                    'username': usuario.username,
                    'nome': usuario.nome,
                    'tipo': usuario.tipo,
                    'ativo': usuario.ativo,
                    'cliente_atual': usuario.cliente_atual or ''
                }
                resultado.append(info_usuario)
            
            return resultado
            
        except Exception as e:
            Logger.log(f"Erro ao listar usuários: {e}", "ERROR")
            return []
    
    @staticmethod
    def obter_grupos_usuario(username):
        """
        Obtém os grupos aos quais um usuário pertence.
        
        Args:
            username (str): Nome do usuário
            
        Returns:
            list: Lista de IDs dos grupos aos quais o usuário pertence
        """
        try:
            # Buscar o usuário
            usuario = Usuario.buscar_por_username(username)
            
            if not usuario:
                return []
            
            # Obter os grupos do usuário
            grupos = usuario.obter_grupos()
            
            # Retornar apenas os IDs dos grupos
            return [grupo.id_grupo for grupo in grupos]
            
        except Exception as e:
            Logger.log(f"Erro ao obter grupos do usuário: {e}", "ERROR")
            return []
    
    @staticmethod
    def verificar_permissao_cliente(username, cliente):
        """
        Verifica se um usuário tem permissão para acessar um cliente.
        
        Args:
            username (str): Nome do usuário
            cliente (str): Nome do cliente
            
        Returns:
            bool: True se o usuário tem permissão, False caso contrário
        """
        try:
            usuario = Usuario.buscar_por_username(username)
            
            if not usuario:
                return False
            
            # Administradores têm acesso a todos os clientes
            if usuario.tipo == 'admin':
                return True
            
            # Buscar grupos do usuário
            grupos_usuario = usuario.obter_grupos()
            
            # Verificar se o usuário pertence ao grupo 'admin'
            if 'admin' in [g.id_grupo for g in grupos_usuario]:
                return True
            
            # Verificar para cada grupo se o cliente está associado
            for grupo in grupos_usuario:
                clientes_grupo = grupo.obter_clientes()
                if cliente in [c['nome'] for c in clientes_grupo]:
                    return True
            
            return False
            
        except Exception as e:
            Logger.log(f"Erro ao verificar permissão de cliente: {e}", "ERROR")
            return False
        
    @staticmethod
    def verificar_pertence_grupo(username, id_grupo):
        """
        Verifica se um usuário pertence a um grupo específico.
        
        Args:
            username (str): Nome do usuário
            id_grupo (str): ID do grupo
            
        Returns:
            bool: True se o usuário pertence ao grupo, False caso contrário
        """
        try:
            # Obter grupos do usuário
            grupos_usuario = AuthController.obter_grupos_usuario(username)
            
            # Verificar se o id_grupo está na lista
            return id_grupo in grupos_usuario
            
        except Exception as e:
            Logger.log(f"Erro ao verificar pertencimento a grupo: {e}", "ERROR")
            return False
            
    @staticmethod
    def alterar_senha_admin(username, nova_senha, operador=None):
        """
        Altera a senha de um usuário (função administrativa que não exige senha atual).
        
        Args:
            username (str): Nome do usuário
            nova_senha (str): Nova senha
            operador (str): Nome do usuário que está realizando a operação
            
        Returns:
            bool: True se a senha foi alterada com sucesso, False caso contrário
        """
        try:
            # Buscar usuário
            usuario = Usuario.buscar_por_username(username)
            
            if not usuario:
                return False
            
            # Alterar senha diretamente (sem verificar senha atual)
            if not usuario.alterar_senha(nova_senha):
                return False
            
            Logger.log(f"Senha alterada para o usuário {username} por {operador}", "INFO")
            return True
            
        except Exception as e:
            Logger.log(f"Erro ao alterar senha (admin): {e}", "ERROR")
            return False  
          
    @staticmethod
    def buscar_usuario_por_username(username):
        """
        Busca um usuário pelo nome de usuário.
        
        Args:
            username (str): Nome de usuário
            
        Returns:
            Usuario: Objeto Usuario ou None se não encontrado
        """
        return Usuario.buscar_por_username(username)    