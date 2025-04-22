#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo de autenticação para o Sistema de Monitoramento de Preços
----------------------------------------------------------------
Versão para banco de dados SQLite.
"""

import hashlib
import getpass
from utils import depurar_logs
from database_config import criar_conexao
from datetime import datetime

def criar_hash_senha(senha):
    """
    Cria um hash seguro para a senha do usuário.
    
    Args:
        senha (str): Senha em texto plano
        
    Returns:
        str: Hash da senha
    """
    return hashlib.sha256(senha.encode()).hexdigest()

def autenticar_usuario(username, senha):
    """
    Verifica se as credenciais de um usuário são válidas.
    
    Args:
        username (str): Nome de usuário
        senha (str): Senha do usuário
        
    Returns:
        tuple: (sucesso, tipo_usuario, cliente_atual) onde sucesso é um booleano indicando 
               se a autenticação foi bem-sucedida, tipo_usuario é o tipo do usuário
               ('admin' ou 'usuario') e cliente_atual é o cliente atualmente selecionado
    """
    try:
        conexao, cursor = criar_conexao()
        
        # Obter dados do usuário
        cursor.execute("SELECT * FROM usuarios WHERE username = ?", (username,))
        usuario = cursor.fetchone()
        
        if usuario:
            # Verificar se a conta está ativa
            if not usuario['ativo']:
                depurar_logs(f"Tentativa de login com conta inativa: {username}", "WARNING")
                conexao.close()
                return False, None, None
                
            # Verificar se a senha corresponde
            senha_hash = criar_hash_senha(senha)
            if senha_hash == usuario['senha']:
                # Atualizar último acesso
                data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute("UPDATE usuarios SET ultimo_acesso = ? WHERE id = ?", 
                              (data_atual, usuario['id']))
                conexao.commit()
                
                depurar_logs(f"Login bem-sucedido: {username}", "INFO")
                
                cliente_atual = usuario['cliente_atual'] or ''
                conexao.close()
                return True, usuario['tipo'], cliente_atual
        
        conexao.close()
        depurar_logs(f"Tentativa de login falhou: {username}", "WARNING")
        return False, None, None
        
    except Exception as e:
        depurar_logs(f"Erro durante autenticação: {e}", "ERROR")
        return False, None, None

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
        conexao, cursor = criar_conexao()
        
        # Verificar se o usuário já existe
        cursor.execute("SELECT id FROM usuarios WHERE username = ?", (username,))
        if cursor.fetchone():
            depurar_logs(f"Tentativa de adicionar usuário já existente: {username} por {operador}", "WARNING")
            conexao.close()
            return False
        
        # Adicionar o novo usuário
        data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        senha_hash = criar_hash_senha(senha)
        
        cursor.execute('''
        INSERT INTO usuarios (username, senha, nome, tipo, ativo, data_criacao)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (username, senha_hash, nome, tipo, 1, data_atual))
        
# Obter o ID do usuário recém-criado
        cursor.execute("SELECT id FROM usuarios WHERE username = ?", (username,))
        id_usuario = cursor.fetchone()['id']
        
        # Associar usuário aos grupos apropriados
        if tipo == 'admin':
            # Obter IDs dos grupos admin e all
            cursor.execute("SELECT id FROM grupos WHERE id_grupo = 'admin'")
            id_grupo_admin = cursor.fetchone()['id']
            
            cursor.execute("SELECT id FROM grupos WHERE id_grupo = 'all'")
            id_grupo_all = cursor.fetchone()['id']
            
            # Associar aos grupos admin e all
            cursor.execute('''
            INSERT INTO usuarios_grupos (id_usuario, id_grupo, data_associacao)
            VALUES (?, ?, ?)
            ''', (id_usuario, id_grupo_admin, data_atual))
            
            cursor.execute('''
            INSERT INTO usuarios_grupos (id_usuario, id_grupo, data_associacao)
            VALUES (?, ?, ?)
            ''', (id_usuario, id_grupo_all, data_atual))
        else:
            # Para usuários comuns, associar apenas ao grupo 'all'
            cursor.execute("SELECT id FROM grupos WHERE id_grupo = 'all'")
            id_grupo_all = cursor.fetchone()['id']
            
            cursor.execute('''
            INSERT INTO usuarios_grupos (id_usuario, id_grupo, data_associacao)
            VALUES (?, ?, ?)
            ''', (id_usuario, id_grupo_all, data_atual))
            
            # Criar grupo pessoal para o usuário
            from grupos_bd import criar_grupo_para_usuario
            criar_grupo_para_usuario(username, nome)
        
        conexao.commit()
        conexao.close()
        
        depurar_logs(f"Novo usuário adicionado: {username} por {operador}", "INFO")
        return True
        
    except Exception as e:
        depurar_logs(f"Erro ao adicionar usuário: {e}", "ERROR")
        return False

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
    # Verifica se as credenciais atuais são válidas
    autenticado, _, _ = autenticar_usuario(username, senha_atual)
    if not autenticado:
        return False
    
    try:
        conexao, cursor = criar_conexao()
        
        # Atualizar a senha
        senha_hash = criar_hash_senha(nova_senha)
        cursor.execute("UPDATE usuarios SET senha = ? WHERE username = ?", 
                      (senha_hash, username))
        
        conexao.commit()
        conexao.close()
        
        depurar_logs(f"Senha alterada para o usuário: {username}", "INFO")
        return True
        
    except Exception as e:
        depurar_logs(f"Erro ao alterar senha: {e}", "ERROR")
        return False

# No arquivo auth_bd.py, modifique a função alterar_cliente_atual

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
        conexao, cursor = criar_conexao()
        
        # Adicionando log para debug
        depurar_logs(f"Tentando alterar cliente atual para usuário {username}: {novo_cliente}", "INFO")
        
        # Verificar se o usuário existe
        cursor.execute("SELECT id FROM usuarios WHERE username = ?", (username,))
        resultado = cursor.fetchone()
        
        if not resultado:
            depurar_logs(f"Usuário não encontrado ao alterar cliente atual: {username}", "WARNING")
            conexao.close()
            return False
        
        # Atualizar o cliente atual
        cursor.execute("UPDATE usuarios SET cliente_atual = ? WHERE username = ?", 
                      (novo_cliente, username))
        
        conexao.commit()
        conexao.close()
        
        depurar_logs(f"Cliente atual alterado para '{novo_cliente}' pelo usuário: {username}", "INFO")
        return True
        
    except Exception as e:
        depurar_logs(f"Erro ao alterar cliente atual: {e}", "ERROR")
        return False

def obter_cliente_atual(username):
    """
    Obtém o cliente atualmente selecionado pelo usuário.
    
    Args:
        username (str): Nome do usuário
        
    Returns:
        str: Nome do cliente atualmente selecionado, ou string vazia se nenhum cliente selecionado
    """
    try:
        conexao, cursor = criar_conexao()
        
        cursor.execute("SELECT cliente_atual FROM usuarios WHERE username = ?", (username,))
        resultado = cursor.fetchone()
        
        conexao.close()
        
        if resultado:
            return resultado['cliente_atual'] or ''
        
        return ''
        
    except Exception as e:
        depurar_logs(f"Erro ao obter cliente atual: {e}", "ERROR")
        return ''

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
        conexao, cursor = criar_conexao()
        
        # Verificar se o usuário existe
        cursor.execute("SELECT id, tipo FROM usuarios WHERE username = ?", (username,))
        usuario = cursor.fetchone()
        
        if not usuario:
            conexao.close()
            return False
        
        # Impedir a desativação do último admin
        if usuario['tipo'] == 'admin':
            # Contar quantos admins ativos existem
            cursor.execute("SELECT COUNT(*) as count FROM usuarios WHERE tipo = 'admin' AND ativo = 1")
            resultado = cursor.fetchone()
            admins_ativos = resultado['count']
            
            if admins_ativos <= 1:
                depurar_logs(f"Tentativa de desativar o último admin: {username} por {operador}", "WARNING")
                conexao.close()
                return False
        
        # Desativar o usuário
        cursor.execute("UPDATE usuarios SET ativo = 0 WHERE username = ?", (username,))
        
        conexao.commit()
        conexao.close()
        
        depurar_logs(f"Usuário desativado: {username} por {operador}", "INFO")
        return True
        
    except Exception as e:
        depurar_logs(f"Erro ao desativar usuário: {e}", "ERROR")
        return False

def listar_usuarios(mostrar_inativos=False):
    """
    Lista todos os usuários cadastrados no sistema.
    
    Args:
        mostrar_inativos (bool): Se True, mostra também usuários inativos
        
    Returns:
        list: Lista de dicionários com informações dos usuários
    """
    try:
        conexao, cursor = criar_conexao()
        
        if mostrar_inativos:
            # Mostrar todos os usuários
            cursor.execute("SELECT username, nome, tipo, ativo, cliente_atual FROM usuarios")
        else:
            # Mostrar apenas usuários ativos
            cursor.execute("SELECT username, nome, tipo, ativo, cliente_atual FROM usuarios WHERE ativo = 1")
        
        usuarios = cursor.fetchall()
        conexao.close()
        
        # Converter para lista de dicionários
        resultado = []
        for usuario in usuarios:
            info_usuario = {
                'username': usuario['username'],
                'nome': usuario['nome'],
                'tipo': usuario['tipo'],
                'ativo': bool(usuario['ativo']),
                'cliente_atual': usuario['cliente_atual'] or ''
            }
            resultado.append(info_usuario)
        
        return resultado
        
    except Exception as e:
        depurar_logs(f"Erro ao listar usuários: {e}", "ERROR")
        return []

def realizar_login():
    """
    Interface para o usuário fazer login no sistema.
    
    Returns:
        tuple: (sucesso, username, tipo_usuario, cliente_atual) indicando o resultado do login
    """
    print("\n=== LOGIN ===")
    
    # Solicita as credenciais
    tentativas = 0
    max_tentativas = 3
    
    while tentativas < max_tentativas:
        username = input("Usuário: ")
        # getpass oculta a senha durante a digitação
        try:
            senha = getpass.getpass("Senha: ")
        except Exception:
            # Fallback caso getpass não funcione no ambiente
            senha = input("Senha (visível): ")
        
        autenticado, tipo_usuario, cliente_atual = autenticar_usuario(username, senha)
        
        if autenticado:
            print(f"\nBem-vindo, {username}!")
            return True, username, tipo_usuario, cliente_atual
        else:
            tentativas += 1
            restantes = max_tentativas - tentativas
            if restantes > 0:
                print(f"Credenciais inválidas. Você tem mais {restantes} tentativa(s).")
            else:
                print("Número máximo de tentativas excedido.")
    
    return False, None, None, None