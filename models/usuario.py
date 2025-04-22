#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Model que representa um usuário no sistema.
"""

import hashlib
from datetime import datetime
from database.connector import DatabaseConnector
from utils.logger import Logger

class Usuario:
    def __init__(self, id=None, username=None, senha=None, nome=None, tipo='usuario', 
                 ativo=True, cliente_atual=None, data_criacao=None, ultimo_acesso=None):
        self.id = id
        self.username = username
        self.senha = senha  # Senha em hash
        self.nome = nome
        self.tipo = tipo
        self.ativo = ativo
        self.cliente_atual = cliente_atual
        self.data_criacao = data_criacao if data_criacao else datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.ultimo_acesso = ultimo_acesso
        self.db = DatabaseConnector()
    
    def salvar(self):
        """
        Salva o usuário no banco de dados.
        
        Returns:
            bool: True se a operação foi bem-sucedida, False caso contrário
        """
        try:
            conexao, cursor = self.db.criar_conexao()
            
            # Verificar se o usuário já existe
            cursor.execute("SELECT id FROM usuarios WHERE username = ?", (self.username,))
            resultado = cursor.fetchone()
            
            if resultado:
                self.id = resultado['id']
                
                # Atualizar usuário existente
                cursor.execute('''
                UPDATE usuarios 
                SET nome = ?, tipo = ?, ativo = ?, cliente_atual = ?
                WHERE id = ?
                ''', (self.nome, self.tipo, 1 if self.ativo else 0, 
                      self.cliente_atual, self.id))
            else:
                # Inserir novo usuário
                cursor.execute('''
                INSERT INTO usuarios (username, senha, nome, tipo, ativo, cliente_atual, data_criacao)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (self.username, self.senha, self.nome, self.tipo,
                      1 if self.ativo else 0, self.cliente_atual, self.data_criacao))
                
                self.id = cursor.lastrowid
                
                # Criar grupo pessoal para o usuário se não for admin
                if self.tipo != 'admin':
                    from models.grupo import Grupo
                    grupo_usuario = Grupo(
                        id_grupo=self.username,
                        nome=f"Grupo de {self.nome}",
                        descricao=f"Grupo pessoal do usuário {self.username}"
                    )
                    grupo_usuario.salvar()
                    
                    # Associar usuário ao seu grupo pessoal
                    grupo_usuario.adicionar_usuario(self.id)
                
                # Associar usuário ao grupo 'all'
                grupo_all = Grupo.buscar_por_id_grupo('all')
                if grupo_all:
                    grupo_all.adicionar_usuario(self.id)
                
                # Se for admin, associar ao grupo 'admin'
                if self.tipo == 'admin':
                    grupo_admin = Grupo.buscar_por_id_grupo('admin')
                    if grupo_admin:
                        grupo_admin.adicionar_usuario(self.id)
            
            conexao.commit()
            conexao.close()
            
            Logger.log(f"Usuário {self.username} salvo com sucesso", "INFO")
            return True
            
        except Exception as e:
            Logger.log(f"Erro ao salvar usuário: {e}", "ERROR")
            return False
    
    def verificar_senha(self, senha):
        """
        Verifica se a senha fornecida corresponde à senha do usuário.
        
        Args:
            senha (str): Senha em texto plano
            
        Returns:
            bool: True se a senha está correta, False caso contrário
        """
        senha_hash = self._criar_hash_senha(senha)
        return senha_hash == self.senha
    
    def alterar_senha(self, nova_senha):
        """
        Altera a senha do usuário.
        
        Args:
            nova_senha (str): Nova senha em texto plano
            
        Returns:
            bool: True se a operação foi bem-sucedida, False caso contrário
        """
        try:
            conexao, cursor = self.db.criar_conexao()
            
            # Gerar hash da nova senha
            senha_hash = self._criar_hash_senha(nova_senha)
            
            # Atualizar a senha
            cursor.execute("UPDATE usuarios SET senha = ? WHERE id = ?", 
                          (senha_hash, self.id))
            
            conexao.commit()
            conexao.close()
            
            self.senha = senha_hash
            
            Logger.log(f"Senha alterada para o usuário: {self.username}", "INFO")
            return True
            
        except Exception as e:
            Logger.log(f"Erro ao alterar senha: {e}", "ERROR")
            return False
    
    def alterar_cliente_atual(self, cliente_atual):
        """
        Altera o cliente atualmente selecionado pelo usuário.
        
        Args:
            cliente_atual (str): Nome do novo cliente selecionado
            
        Returns:
            bool: True se a operação foi bem-sucedida, False caso contrário
        """
        try:
            conexao, cursor = self.db.criar_conexao()
            
            # Atualizar o cliente atual
            cursor.execute("UPDATE usuarios SET cliente_atual = ? WHERE id = ?", 
                          (cliente_atual, self.id))
            
            conexao.commit()
            conexao.close()
            
            self.cliente_atual = cliente_atual
            
            Logger.log(f"Cliente atual alterado para '{cliente_atual}' pelo usuário: {self.username}", "INFO")
            return True
            
        except Exception as e:
            Logger.log(f"Erro ao alterar cliente atual: {e}", "ERROR")
            return False
    
    def registrar_acesso(self):
        """
        Registra um acesso do usuário, atualizando o campo de último acesso.
        
        Returns:
            bool: True se a operação foi bem-sucedida, False caso contrário
        """
        try:
            conexao, cursor = self.db.criar_conexao()
            
            # Atualizar último acesso
            data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute("UPDATE usuarios SET ultimo_acesso = ? WHERE id = ?", 
                          (data_atual, self.id))
            
            conexao.commit()
            conexao.close()
            
            self.ultimo_acesso = data_atual
            
            Logger.log(f"Acesso registrado para o usuário: {self.username}", "INFO")
            return True
            
        except Exception as e:
            Logger.log(f"Erro ao registrar acesso: {e}", "ERROR")
            return False
    
    def desativar(self):
        """
        Desativa o usuário.
        
        Returns:
            bool: True se a operação foi bem-sucedida, False caso contrário
        """
        try:
            # Verificar se é o último admin
            if self.tipo == 'admin':
                conexao, cursor = self.db.criar_conexao()
                
                # Contar quantos admins ativos existem
                cursor.execute("SELECT COUNT(*) as count FROM usuarios WHERE tipo = 'admin' AND ativo = 1")
                resultado = cursor.fetchone()
                admins_ativos = resultado['count']
                
                conexao.close()
                
                if admins_ativos <= 1:
                    Logger.log(f"Tentativa de desativar o último admin: {self.username}", "WARNING")
                    return False
            
            conexao, cursor = self.db.criar_conexao()
            
            # Desativar o usuário
            cursor.execute("UPDATE usuarios SET ativo = 0 WHERE id = ?", (self.id,))
            
            conexao.commit()
            conexao.close()
            
            self.ativo = False
            
            Logger.log(f"Usuário desativado: {self.username}", "INFO")
            return True
            
        except Exception as e:
            Logger.log(f"Erro ao desativar usuário: {e}", "ERROR")
            return False
    
    def obter_grupos(self):
        """
        Obtém todos os grupos aos quais o usuário pertence.
        
        Returns:
            list: Lista de objetos Grupo
        """
        try:
            conexao, cursor = self.db.criar_conexao()
            
            cursor.execute('''
            SELECT g.id, g.id_grupo, g.nome, g.descricao, g.data_criacao
            FROM grupos g
            JOIN usuarios_grupos ug ON g.id = ug.id_grupo
            WHERE ug.id_usuario = ?
            ORDER BY g.id_grupo
            ''', (self.id,))
            
            resultados = cursor.fetchall()
            conexao.close()
            
            from models.grupo import Grupo
            grupos = []
            
            for resultado in resultados:
                grupos.append(Grupo(
                    id=resultado['id'],
                    id_grupo=resultado['id_grupo'],
                    nome=resultado['nome'],
                    descricao=resultado['descricao'],
                    data_criacao=resultado['data_criacao']
                ))
            
            return grupos
            
        except Exception as e:
            Logger.log(f"Erro ao obter grupos do usuário: {e}", "ERROR")
            return []
    
    def _criar_hash_senha(self, senha):
        """
        Cria um hash seguro para a senha do usuário.
        
        Args:
            senha (str): Senha em texto plano
            
        Returns:
            str: Hash da senha
        """
        return hashlib.sha256(senha.encode()).hexdigest()
    
    @classmethod
    def buscar_por_id(cls, id_usuario):
        """
        Busca um usuário pelo ID.
        
        Args:
            id_usuario (int): ID do usuário
            
        Returns:
            Usuario: Objeto Usuario ou None se não encontrado
        """
        try:
            db = DatabaseConnector()
            conexao, cursor = db.criar_conexao()
            
            cursor.execute("SELECT * FROM usuarios WHERE id = ?", (id_usuario,))
            resultado = cursor.fetchone()
            
            conexao.close()
            
            if resultado:
                return cls(
                    id=resultado['id'],
                    username=resultado['username'],
                    senha=resultado['senha'],
                    nome=resultado['nome'],
                    tipo=resultado['tipo'],
                    ativo=bool(resultado['ativo']),
                    cliente_atual=resultado['cliente_atual'],
                    data_criacao=resultado['data_criacao'],
                    ultimo_acesso=resultado['ultimo_acesso']
                )
            return None
            
        except Exception as e:
            Logger.log(f"Erro ao buscar usuário por ID: {e}", "ERROR")
            return None
    
    @classmethod
    def buscar_por_username(cls, username):
        """
        Busca um usuário pelo nome de usuário.
        
        Args:
            username (str): Nome de usuário
            
        Returns:
            Usuario: Objeto Usuario ou None se não encontrado
        """
        try:
            db = DatabaseConnector()
            conexao, cursor = db.criar_conexao()
            
            cursor.execute("SELECT * FROM usuarios WHERE username = ?", (username,))
            resultado = cursor.fetchone()
            
            conexao.close()
            
            if resultado:
                return cls(
                    id=resultado['id'],
                    username=resultado['username'],
                    senha=resultado['senha'],
                    nome=resultado['nome'],
                    tipo=resultado['tipo'],
                    ativo=bool(resultado['ativo']),
                    cliente_atual=resultado['cliente_atual'],
                    data_criacao=resultado['data_criacao'],
                    ultimo_acesso=resultado['ultimo_acesso']
                )
            return None
            
        except Exception as e:
            Logger.log(f"Erro ao buscar usuário por username: {e}", "ERROR")
            return None
    
    @classmethod
    def listar_todos(cls):
        """
        Lista todos os usuários cadastrados.
        
        Returns:
            list: Lista de objetos Usuario
        """
        try:
            db = DatabaseConnector()
            conexao, cursor = db.criar_conexao()
            
            cursor.execute("SELECT * FROM usuarios ORDER BY username")
            resultados = cursor.fetchall()
            
            conexao.close()
            
            usuarios = []
            for resultado in resultados:
                usuarios.append(cls(
                    id=resultado['id'],
                    username=resultado['username'],
                    senha=resultado['senha'],
                    nome=resultado['nome'],
                    tipo=resultado['tipo'],
                    ativo=bool(resultado['ativo']),
                    cliente_atual=resultado['cliente_atual'],
                    data_criacao=resultado['data_criacao'],
                    ultimo_acesso=resultado['ultimo_acesso']
                ))
            
            return usuarios
            
        except Exception as e:
            Logger.log(f"Erro ao listar usuários: {e}", "ERROR")
            return []