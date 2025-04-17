#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo de autenticação para o Sistema de Monitoramento de Preços
----------------------------------------------------------------
Gerencia usuários, login e controle de acesso ao sistema.
"""

import os
import json
import hashlib
import getpass
from utils import depurar_logs
from grupos import criar_grupo_para_usuario, adicionar_usuario_grupo, obter_grupos_usuario


# Arquivo para armazenar os usuários
USUARIOS_FILE = 'usuarios.json'

def criar_hash_senha(senha):
    """
    Cria um hash seguro para a senha do usuário.
    
    Args:
        senha (str): Senha em texto plano
        
    Returns:
        str: Hash da senha
    """
    return hashlib.sha256(senha.encode()).hexdigest()

def verificar_arquivo_usuarios():
    """
    Verifica se o arquivo de usuários existe, e cria com um admin padrão se não existir.
    
    Returns:
        bool: True se o arquivo já existia ou foi criado com sucesso, False caso contrário
    """
    try:
        if not os.path.isfile(USUARIOS_FILE):
            # Cria o arquivo com um usuário admin padrão
            admin_password = criar_hash_senha("admin")
            usuarios_iniciais = {
                "admin": {
                    "senha": admin_password,
                    "nome": "Administrador",
                    "tipo": "admin",
                    "ativo": True,
                    "cliente_atual": ""  # Cliente selecionado atualmente pelo usuário
                }
            }
            
            with open(USUARIOS_FILE, 'w', encoding='utf-8') as f:
                json.dump(usuarios_iniciais, f, ensure_ascii=False, indent=4)
                
            depurar_logs("Arquivo de usuários criado com usuário admin padrão", "INFO")
            return True
        return True
    except Exception as e:
        depurar_logs(f"Erro ao verificar/criar arquivo de usuários: {str(e)}", "ERROR")
        return False

def carregar_usuarios():
    """
    Carrega os usuários do arquivo JSON.
    
    Returns:
        dict: Dicionário com os usuários ou um dicionário vazio em caso de erro
    """
    try:
        if os.path.isfile(USUARIOS_FILE):
            with open(USUARIOS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            verificar_arquivo_usuarios()
            with open(USUARIOS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        depurar_logs(f"Erro ao carregar usuários: {str(e)}", "ERROR")
        return {}

def salvar_usuarios(usuarios):
    """
    Salva o dicionário de usuários no arquivo JSON.
    
    Args:
        usuarios (dict): Dicionário com os dados dos usuários
    
    Returns:
        bool: True se o salvamento foi bem-sucedido, False caso contrário
    """
    try:
        with open(USUARIOS_FILE, 'w', encoding='utf-8') as f:
            json.dump(usuarios, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        depurar_logs(f"Erro ao salvar usuários: {str(e)}", "ERROR")
        return False

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
    usuarios = carregar_usuarios()
    
    if username in usuarios:
        usuario = usuarios[username]
        # Verifica se a conta está ativa
        if not usuario.get('ativo', True):
            depurar_logs(f"Tentativa de login com conta inativa: {username}", "WARNING")
            return False, None, None
            
        # Verifica se a senha corresponde
        senha_hash = criar_hash_senha(senha)
        if senha_hash == usuario['senha']:
            depurar_logs(f"Login bem-sucedido: {username}", "INFO")
            cliente_atual = usuario.get('cliente_atual', '')
            return True, usuario.get('tipo', 'usuario'), cliente_atual
    
    depurar_logs(f"Tentativa de login falhou: {username}", "WARNING")
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
        
    usuarios = carregar_usuarios()
    
    # Verifica se o usuário já existe
    if username in usuarios:
        depurar_logs(f"Tentativa de adicionar usuário já existente: {username} por {operador}", "WARNING")
        return False
    
    # Adiciona o novo usuário
    usuarios[username] = {
        "senha": criar_hash_senha(senha),
        "nome": nome,
        "tipo": tipo,
        "ativo": True,
        "cliente_atual": ""  # Inicialmente sem cliente selecionado
    }
    
    sucesso = salvar_usuarios(usuarios)
    if sucesso:
        depurar_logs(f"Novo usuário adicionado: {username} por {operador}", "INFO")
        
        # Se não for admin, cria um grupo pessoal para o usuário
        from grupos import criar_grupo_para_usuario, adicionar_usuario_grupo
        if tipo != 'admin':
            criar_grupo_para_usuario(username, nome)
        else:
            # Se for admin, adiciona-o ao grupo 'admin'
            adicionar_usuario_grupo('admin', username, operador)
    
    return sucesso

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
    
    usuarios = carregar_usuarios()
    usuarios[username]['senha'] = criar_hash_senha(nova_senha)
    
    sucesso = salvar_usuarios(usuarios)
    if sucesso:
        depurar_logs(f"Senha alterada para o usuário: {username}", "INFO")
    
    return sucesso

def alterar_cliente_atual(username, novo_cliente):
    """
    Altera o cliente atualmente selecionado pelo usuário.
    
    Args:
        username (str): Nome do usuário
        novo_cliente (str): Nome do novo cliente selecionado
        
    Returns:
        bool: True se o cliente foi alterado com sucesso, False caso contrário
    """
    usuarios = carregar_usuarios()
    
    if username not in usuarios:
        depurar_logs(f"Tentativa de alterar cliente atual para usuário inexistente: {username}", "WARNING")
        return False
    
    # Atualiza o cliente atual do usuário
    usuarios[username]['cliente_atual'] = novo_cliente
    
    sucesso = salvar_usuarios(usuarios)
    if sucesso:
        depurar_logs(f"Cliente atual alterado para '{novo_cliente}' pelo usuário: {username}", "INFO")
    
    return sucesso

def obter_cliente_atual(username):
    """
    Obtém o cliente atualmente selecionado pelo usuário.
    
    Args:
        username (str): Nome do usuário
        
    Returns:
        str: Nome do cliente atualmente selecionado, ou string vazia se nenhum cliente selecionado
    """
    usuarios = carregar_usuarios()
    
    if username in usuarios:
        return usuarios[username].get('cliente_atual', '')
    
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
    usuarios = carregar_usuarios()
    
    if username not in usuarios:
        return False
        
    # Impede a desativação do último admin
    if usuarios[username].get('tipo') == 'admin':
        # Conta quantos admins ativos existem
        admins_ativos = sum(1 for user in usuarios.values() 
                          if user.get('tipo') == 'admin' and user.get('ativo', True))
        
        if admins_ativos <= 1:
            depurar_logs(f"Tentativa de desativar o último admin: {username} por {operador}", "WARNING")
            return False
    
    usuarios[username]['ativo'] = False
    
    sucesso = salvar_usuarios(usuarios)
    if sucesso:
        depurar_logs(f"Usuário desativado: {username} por {operador}", "INFO")
    
    return sucesso

def listar_usuarios(mostrar_inativos=False):
    """
    Lista todos os usuários cadastrados no sistema.
    
    Args:
        mostrar_inativos (bool): Se True, mostra também usuários inativos
        
    Returns:
        list: Lista de dicionários com informações dos usuários
    """
    usuarios = carregar_usuarios()
    resultado = []
    
    for username, dados in usuarios.items():
        # Pula usuários inativos se não foi solicitado mostrar
        if not mostrar_inativos and not dados.get('ativo', True):
            continue
            
        # Não inclui a senha no resultado
        info_usuario = {
            'username': username,
            'nome': dados.get('nome', ''),
            'tipo': dados.get('tipo', 'usuario'),
            'ativo': dados.get('ativo', True),
            'cliente_atual': dados.get('cliente_atual', '')
        }
        resultado.append(info_usuario)
        
    return resultado

def realizar_login():
    """
    Interface para o usuário fazer login no sistema.
    
    Returns:
        tuple: (sucesso, username, tipo_usuario, cliente_atual) indicando o resultado do login
    """
    print("\n=== LOGIN ===")
    
    # Garante que o arquivo de usuários existe
    verificar_arquivo_usuarios()
    
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