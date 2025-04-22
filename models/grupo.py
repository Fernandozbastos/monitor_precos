#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Model que representa um grupo no sistema.
"""

from datetime import datetime
from database.connector import DatabaseConnector

class Grupo:
    def __init__(self, id=None, id_grupo=None, nome=None, descricao=None, data_criacao=None):
        self.id = id
        self.id_grupo = id_grupo
        self.nome = nome
        self.descricao = descricao
        self.data_criacao = data_criacao if data_criacao else datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.db = DatabaseConnector()
    
    def salvar(self):
        """
        Salva o grupo no banco de dados.
        
        Returns:
            bool: True se a operação foi bem-sucedida, False caso contrário
        """
        try:
            conexao, cursor = self.db.criar_conexao()
            
            # Verificar se o grupo já existe
            cursor.execute("SELECT id FROM grupos WHERE id_grupo = ?", (self.id_grupo,))
            resultado = cursor.fetchone()
            
            if resultado:
                self.id = resultado['id']
                
                # Atualizar grupo existente
                cursor.execute('''
                UPDATE grupos 
                SET nome = ?, descricao = ?
                WHERE id = ?
                ''', (self.nome, self.descricao, self.id))
            else:
                # Inserir novo grupo
                cursor.execute('''
                INSERT INTO grupos (id_grupo, nome, descricao, data_criacao)
                VALUES (?, ?, ?, ?)
                ''', (self.id_grupo, self.nome, self.descricao, self.data_criacao))
                
                self.id = cursor.lastrowid
            
            conexao.commit()
            conexao.close()
            
            from utils.logger import Logger
            Logger.log(f"Grupo '{self.id_grupo}' salvo com sucesso", "INFO")
            return True
            
        except Exception as e:
            from utils.logger import Logger
            Logger.log(f"Erro ao salvar grupo: {str(e)}", "ERROR")
            return False
    
    def adicionar_usuario(self, id_usuario):
        """
        Adiciona um usuário ao grupo.
        
        Args:
            id_usuario (int): ID do usuário
            
        Returns:
            bool: True se a operação foi bem-sucedida, False caso contrário
        """
        try:
            conexao, cursor = self.db.criar_conexao()
            
            # Verificar se a associação já existe
            cursor.execute('''
            SELECT id FROM usuarios_grupos WHERE id_usuario = ? AND id_grupo = ?
            ''', (id_usuario, self.id))
            
            if cursor.fetchone():
                conexao.close()
                return True  # Associação já existe
            
            # Criar a associação
            data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute('''
            INSERT INTO usuarios_grupos (id_usuario, id_grupo, data_associacao)
            VALUES (?, ?, ?)
            ''', (id_usuario, self.id, data_atual))
            
            conexao.commit()
            conexao.close()
            
            from utils.logger import Logger
            Logger.log(f"Usuário ID {id_usuario} adicionado ao grupo {self.id_grupo}", "INFO")
            return True
            
        except Exception as e:
            from utils.logger import Logger
            Logger.log(f"Erro ao adicionar usuário ao grupo: {str(e)}", "ERROR")
            return False
    
    def remover_usuario(self, id_usuario):
        """
        Remove um usuário do grupo.
        
        Args:
            id_usuario (int): ID do usuário
            
        Returns:
            bool: True se a operação foi bem-sucedida, False caso contrário
        """
        try:
            # Verificar casos especiais
            conexao, cursor = self.db.criar_conexao()
            
            # Obter nome de usuário
            cursor.execute("SELECT username FROM usuarios WHERE id = ?", (id_usuario,))
            resultado = cursor.fetchone()
            
            if not resultado:
                conexao.close()
                return False  # Usuário não existe
            
            username = resultado['username']
            
            # Verificar casos especiais
            if (self.id_grupo == "admin" or self.id_grupo == "all") and username == "admin":
                conexao.close()
                from utils.logger import Logger
                Logger.log(f"Tentativa de remover admin do grupo '{self.id_grupo}'", "WARNING")
                return False
            
            # Impedir a remoção de um usuário do seu próprio grupo pessoal
            if self.id_grupo == username:
                conexao.close()
                from utils.logger import Logger
                Logger.log(f"Tentativa de remover usuário {username} do seu próprio grupo pessoal", "WARNING")
                return False
            
            # Verificar se a associação existe
            cursor.execute('''
            SELECT id FROM usuarios_grupos WHERE id_usuario = ? AND id_grupo = ?
            ''', (id_usuario, self.id))
            
            if not cursor.fetchone():
                conexao.close()
                return False  # Associação não existe
            
            # Remover a associação
            cursor.execute('''
            DELETE FROM usuarios_grupos WHERE id_usuario = ? AND id_grupo = ?
            ''', (id_usuario, self.id))
            
            conexao.commit()
            conexao.close()
            
            from utils.logger import Logger
            Logger.log(f"Usuário {username} removido do grupo {self.id_grupo}", "INFO")
            return True
            
        except Exception as e:
            from utils.logger import Logger
            Logger.log(f"Erro ao remover usuário do grupo: {str(e)}", "ERROR")
            return False
    
    def adicionar_cliente(self, id_cliente):
        """
        Adiciona um cliente ao grupo.
        
        Args:
            id_cliente (int): ID do cliente
            
        Returns:
            bool: True se a operação foi bem-sucedida, False caso contrário
        """
        try:
            conexao, cursor = self.db.criar_conexao()
            
            # Verificar se a associação já existe
            cursor.execute('''
            SELECT id FROM clientes_grupos WHERE id_cliente = ? AND id_grupo = ?
            ''', (id_cliente, self.id))
            
            if cursor.fetchone():
                conexao.close()
                return True  # Associação já existe
            
            # Criar a associação
            data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute('''
            INSERT INTO clientes_grupos (id_cliente, id_grupo, data_associacao)
            VALUES (?, ?, ?)
            ''', (id_cliente, self.id, data_atual))
            
            conexao.commit()
            conexao.close()
            
            from utils.logger import Logger
            Logger.log(f"Cliente ID {id_cliente} adicionado ao grupo {self.id_grupo}", "INFO")
            return True
            
        except Exception as e:
            from utils.logger import Logger
            Logger.log(f"Erro ao adicionar cliente ao grupo: {str(e)}", "ERROR")
            return False
    
    def remover_cliente(self, id_cliente):
        """
        Remove um cliente do grupo.
        
        Args:
            id_cliente (int): ID do cliente
            
        Returns:
            bool: True se a operação foi bem-sucedida, False caso contrário
        """
        try:
            conexao, cursor = self.db.criar_conexao()
            
            # Verificar se a associação existe
            cursor.execute('''
            SELECT id FROM clientes_grupos WHERE id_cliente = ? AND id_grupo = ?
            ''', (id_cliente, self.id))
            
            if not cursor.fetchone():
                conexao.close()
                return False  # Associação não existe
            
            # Remover a associação
            cursor.execute('''
            DELETE FROM clientes_grupos WHERE id_cliente = ? AND id_grupo = ?
            ''', (id_cliente, self.id))
            
            conexao.commit()
            conexao.close()
            
            from utils.logger import Logger
            Logger.log(f"Cliente ID {id_cliente} removido do grupo {self.id_grupo}", "INFO")
            return True
            
        except Exception as e:
            from utils.logger import Logger
            Logger.log(f"Erro ao remover cliente do grupo: {str(e)}", "ERROR")
            return False
    
    def obter_usuarios(self):
        """
        Obtém todos os usuários associados ao grupo.
        
        Returns:
            list: Lista de dicionários com informações dos usuários
        """
        try:
            conexao, cursor = self.db.criar_conexao()
            
            cursor.execute('''
            SELECT u.id, u.username, u.nome, u.tipo, u.ativo
            FROM usuarios u
            JOIN usuarios_grupos ug ON u.id = ug.id_usuario
            WHERE ug.id_grupo = ?
            ORDER BY u.username
            ''', (self.id,))
            
            resultados = cursor.fetchall()
            conexao.close()
            
            # Converter para lista de dicionários
            usuarios = []
            for resultado in resultados:
                usuarios.append({
                    'id': resultado['id'],
                    'username': resultado['username'],
                    'nome': resultado['nome'],
                    'tipo': resultado['tipo'],
                    'ativo': bool(resultado['ativo'])
                })
            
            return usuarios
            
        except Exception as e:
            from utils.logger import Logger
            Logger.log(f"Erro ao obter usuários do grupo: {str(e)}", "ERROR")
            return []
    
    def obter_clientes(self):
        """
        Obtém todos os clientes associados ao grupo.
        
        Returns:
            list: Lista de dicionários com informações dos clientes
        """
        try:
            conexao, cursor = self.db.criar_conexao()
            
            cursor.execute('''
            SELECT c.id, c.nome
            FROM clientes c
            JOIN clientes_grupos cg ON c.id = cg.id_cliente
            WHERE cg.id_grupo = ?
            ORDER BY c.nome
            ''', (self.id,))
            
            resultados = cursor.fetchall()
            conexao.close()
            
            # Converter para lista de dicionários
            clientes = []
            for resultado in resultados:
                clientes.append({
                    'id': resultado['id'],
                    'nome': resultado['nome']
                })
            
            return clientes
            
        except Exception as e:
            from utils.logger import Logger
            Logger.log(f"Erro ao obter clientes do grupo: {str(e)}", "ERROR")
            return []
    
    @classmethod
    def sincronizar_grupo_all(cls, todos_clientes_ids):
        """
        Sincroniza o grupo 'all' com todos os clientes fornecidos.
        
        Args:
            todos_clientes_ids (list): Lista de IDs de todos os clientes
            
        Returns:
            bool: True se a operação foi bem-sucedida, False caso contrário
        """
        try:
            grupo_all = cls.buscar_por_id_grupo('all')
            
            if not grupo_all:
                from utils.logger import Logger
                Logger.log("Grupo 'all' não encontrado durante sincronização", "ERROR")
                return False
            
            # Adicionar todos os clientes ao grupo 'all'
            for id_cliente in todos_clientes_ids:
                grupo_all.adicionar_cliente(id_cliente)
            
            from utils.logger import Logger
            Logger.log(f"Grupo 'all' sincronizado com {len(todos_clientes_ids)} clientes", "INFO")
            return True
            
        except Exception as e:
            from utils.logger import Logger
            Logger.log(f"Erro ao sincronizar grupo 'all': {str(e)}", "ERROR")
            return False
    
    @classmethod
    def buscar_por_id(cls, id_grupo):
        """
        Busca um grupo pelo ID.
        
        Args:
            id_grupo (int): ID do grupo
            
        Returns:
            Grupo: Objeto Grupo ou None se não encontrado
        """
        try:
            db = DatabaseConnector()
            conexao, cursor = db.criar_conexao()
            
            cursor.execute("SELECT * FROM grupos WHERE id = ?", (id_grupo,))
            resultado = cursor.fetchone()
            
            conexao.close()
            
            if resultado:
                return cls(
                    id=resultado['id'],
                    id_grupo=resultado['id_grupo'],
                    nome=resultado['nome'],
                    descricao=resultado['descricao'],
                    data_criacao=resultado['data_criacao']
                )
            return None
            
        except Exception as e:
            from utils.logger import Logger
            Logger.log(f"Erro ao buscar grupo por ID: {str(e)}", "ERROR")
            return None
    
    @classmethod
    def buscar_por_id_grupo(cls, id_grupo_str):
        """
        Busca um grupo pelo ID do grupo (campo id_grupo).
        
        Args:
            id_grupo_str (str): ID do grupo (campo id_grupo)
            
        Returns:
            Grupo: Objeto Grupo ou None se não encontrado
        """
        try:
            db = DatabaseConnector()
            conexao, cursor = db.criar_conexao()
            
            cursor.execute("SELECT * FROM grupos WHERE id_grupo = ?", (id_grupo_str,))
            resultado = cursor.fetchone()
            
            conexao.close()
            
            if resultado:
                return cls(
                    id=resultado['id'],
                    id_grupo=resultado['id_grupo'],
                    nome=resultado['nome'],
                    descricao=resultado['descricao'],
                    data_criacao=resultado['data_criacao']
                )
            return None
            
        except Exception as e:
            from utils.logger import Logger
            Logger.log(f"Erro ao buscar grupo por ID de grupo: {str(e)}", "ERROR")
            return None
    
    @classmethod
    def listar_todos(cls):
        """
        Lista todos os grupos cadastrados.
        
        Returns:
            list: Lista de objetos Grupo
        """
        try:
            db = DatabaseConnector()
            conexao, cursor = db.criar_conexao()
            
            cursor.execute("SELECT * FROM grupos ORDER BY id_grupo")
            resultados = cursor.fetchall()
            
            conexao.close()
            
            grupos = []
            for resultado in resultados:
                grupos.append(cls(
                    id=resultado['id'],
                    id_grupo=resultado['id_grupo'],
                    nome=resultado['nome'],
                    descricao=resultado['descricao'],
                    data_criacao=resultado['data_criacao']
                ))
            
            return grupos
            
        except Exception as e:
            from utils.logger import Logger
            Logger.log(f"Erro ao listar grupos: {str(e)}", "ERROR")
            return []
    
    @classmethod
    def excluir(cls, id_grupo_str):
        """
        Exclui um grupo e suas associações.
        
        Args:
            id_grupo_str (str): ID do grupo (campo id_grupo)
            
        Returns:
            bool: True se a operação foi bem-sucedida, False caso contrário
        """
        try:
            # Impedir a remoção dos grupos padrão
            if id_grupo_str in ["admin", "all"]:
                from utils.logger import Logger
                Logger.log(f"Tentativa de remover grupo padrão '{id_grupo_str}'", "WARNING")
                return False
            
            grupo = cls.buscar_por_id_grupo(id_grupo_str)
            
            if not grupo:
                return False
            
            db = DatabaseConnector()
            conexao, cursor = db.criar_conexao()
            
            # Remover associações de usuários com o grupo
            cursor.execute("DELETE FROM usuarios_grupos WHERE id_grupo = ?", (grupo.id,))
            
            # Remover associações de clientes com o grupo
            cursor.execute("DELETE FROM clientes_grupos WHERE id_grupo = ?", (grupo.id,))
            
            # Finalmente, remover o grupo
            cursor.execute("DELETE FROM grupos WHERE id = ?", (grupo.id,))
            
            conexao.commit()
            conexao.close()
            
            from utils.logger import Logger
            Logger.log(f"Grupo '{id_grupo_str}' excluído com sucesso", "INFO")
            return True
            
        except Exception as e:
            from utils.logger import Logger
            Logger.log(f"Erro ao excluir grupo: {str(e)}", "ERROR")
            return False