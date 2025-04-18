#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo de gestão de grupos para o Sistema de Monitoramento de Preços
--------------------------------------------------------------------
Gerencia grupos, associação de clientes a grupos e usuários a grupos.
"""

import os
import json
from utils import depurar_logs

# Arquivo para armazenar os grupos
GRUPOS_FILE = 'grupos.json'

def verificar_arquivo_grupos():
    """
    Verifica se o arquivo de grupos existe, e cria com estrutura padrão se não existir.
    
    Returns:
        bool: True se o arquivo já existia ou foi criado com sucesso, False caso contrário
    """
    try:
        if not os.path.isfile(GRUPOS_FILE):
            # Cria o arquivo com grupos iniciais
            grupos_iniciais = {
                "admin": {
                    "nome": "Administradores",
                    "descricao": "Grupo de administradores com acesso a todos os clientes",
                    "clientes": [],  # Inicialmente vazio, será preenchido automaticamente
                    "usuarios": ["admin"]  # Admin tem acesso por padrão
                },
                "all": {
                    "nome": "Todos",
                    "descricao": "Grupo padrão que inclui todos os clientes",
                    "clientes": [],  # Inicialmente vazio, será preenchido automaticamente
                    "usuarios": ["admin"]  # Admin tem acesso a todos os grupos por padrão
                }
            }
            
            with open(GRUPOS_FILE, 'w', encoding='utf-8') as f:
                json.dump(grupos_iniciais, f, ensure_ascii=False, indent=4)
                
            depurar_logs("Arquivo de grupos criado com grupos padrão", "INFO")
            return True
        return True
    except Exception as e:
        depurar_logs(f"Erro ao verificar/criar arquivo de grupos: {str(e)}", "ERROR")
        return False

def carregar_grupos():
    """
    Carrega os grupos do arquivo JSON.
    
    Returns:
        dict: Dicionário com os grupos ou um dicionário vazio em caso de erro
    """
    try:
        if os.path.isfile(GRUPOS_FILE):
            with open(GRUPOS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            verificar_arquivo_grupos()
            with open(GRUPOS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        depurar_logs(f"Erro ao carregar grupos: {str(e)}", "ERROR")
        return {}

def salvar_grupos(grupos):
    """
    Salva o dicionário de grupos no arquivo JSON.
    
    Args:
        grupos (dict): Dicionário com os dados dos grupos
    
    Returns:
        bool: True se o salvamento foi bem-sucedido, False caso contrário
    """
    try:
        with open(GRUPOS_FILE, 'w', encoding='utf-8') as f:
            json.dump(grupos, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        depurar_logs(f"Erro ao salvar grupos: {str(e)}", "ERROR")
        return False

def criar_grupo_para_usuario(username, nome_usuario=None):
    """
    Cria um grupo personalizado para um novo usuário, se ainda não existir.
    
    Args:
        username (str): Nome de usuário para criar o grupo
        nome_usuario (str, optional): Nome completo do usuário para exibição
        
    Returns:
        bool: True se o grupo foi criado com sucesso, False caso contrário
    """
    grupos = carregar_grupos()
    
    # Verifica se já existe um grupo para este usuário
    if username in grupos:
        return True  # Grupo já existe, não precisa criar
    
    # Criar nome de exibição para o grupo se não foi fornecido
    nome_grupo = f"Grupo de {nome_usuario}" if nome_usuario else f"Grupo de {username}"
    
    # Adiciona o novo grupo específico para o usuário
    grupos[username] = {
        "nome": nome_grupo,
        "descricao": f"Grupo pessoal do usuário {username}",
        "clientes": [],
        "usuarios": [username]  # O usuário automaticamente pertence ao seu próprio grupo
    }
    
    sucesso = salvar_grupos(grupos)
    if sucesso:
        depurar_logs(f"Grupo pessoal criado para o usuário: {username}", "INFO")
    
    return sucesso

def adicionar_cliente_a_todos_grupos_admin(cliente):
    """
    Adiciona um cliente a todos os grupos de administração (admin e all).
    
    Args:
        cliente (str): Nome do cliente a ser adicionado
        
    Returns:
        bool: True se o cliente foi adicionado com sucesso, False caso contrário
    """
    grupos = carregar_grupos()
    
    # Verifica se os grupos admin e all existem
    grupos_admin = ["admin", "all"]
    alterado = False
    
    for grupo_id in grupos_admin:
        if grupo_id in grupos:
            if cliente not in grupos[grupo_id]["clientes"]:
                grupos[grupo_id]["clientes"].append(cliente)
                alterado = True
    
    if alterado:
        sucesso = salvar_grupos(grupos)
        if sucesso:
            depurar_logs(f"Cliente '{cliente}' adicionado aos grupos de administração", "INFO")
        return sucesso
    
    return True  # Não houve alterações necessárias

def criar_grupo(id_grupo, nome, descricao, operador=None):
    """
    Cria um novo grupo.
    
    Args:
        id_grupo (str): Identificador único para o grupo
        nome (str): Nome do grupo para exibição
        descricao (str): Descrição do grupo
        operador (str): Nome do usuário que está realizando a operação
        
    Returns:
        bool: True se o grupo foi criado com sucesso, False caso contrário
    """
    if not id_grupo or not nome:
        return False
        
    grupos = carregar_grupos()
    
    # Verifica se o ID do grupo já existe
    if id_grupo in grupos:
        depurar_logs(f"Tentativa de criar grupo com ID já existente: {id_grupo} por {operador}", "WARNING")
        return False
    
    # Adiciona o novo grupo
    grupos[id_grupo] = {
        "nome": nome,
        "descricao": descricao,
        "clientes": [],
        "usuarios": []
    }
    
    sucesso = salvar_grupos(grupos)
    if sucesso:
        depurar_logs(f"Novo grupo criado: {id_grupo} ({nome}) por {operador}", "INFO")
    
    return sucesso

def remover_grupo(id_grupo, operador=None):
    """
    Remove um grupo existente.
    
    Args:
        id_grupo (str): ID do grupo a ser removido
        operador (str): Nome do usuário que está realizando a operação
        
    Returns:
        bool: True se o grupo foi removido com sucesso, False caso contrário
    """
    grupos = carregar_grupos()
    
    # Verifica se o grupo existe
    if id_grupo not in grupos:
        depurar_logs(f"Tentativa de remover grupo inexistente: {id_grupo} por {operador}", "WARNING")
        return False
    
    # Impede a remoção dos grupos padrão (admin, all) e grupos pessoais de usuários
    if id_grupo in ["admin", "all"]:
        depurar_logs(f"Tentativa de remover grupo padrão '{id_grupo}' por {operador}", "WARNING")
        return False
    
    # Remove o grupo
    del grupos[id_grupo]
    
    sucesso = salvar_grupos(grupos)
    if sucesso:
        depurar_logs(f"Grupo removido: {id_grupo} por {operador}", "INFO")
    
    return sucesso

def adicionar_cliente_grupo_usuario(usuario, cliente, operador=None):
    """
    Adiciona um cliente ao grupo pessoal do usuário e aos grupos de administração.
    
    Args:
        usuario (str): Nome do usuário dono do grupo
        cliente (str): Nome do cliente a ser adicionado
        operador (str): Nome do usuário que está realizando a operação
        
    Returns:
        bool: True se o cliente foi adicionado com sucesso, False caso contrário
    """
    # Primeiro, adiciona aos grupos de administração
    adicionar_cliente_a_todos_grupos_admin(cliente)
    
    # Em seguida, adiciona ao grupo pessoal do usuário
    grupos = carregar_grupos()
    
    # Verifica se o grupo do usuário existe
    if usuario not in grupos:
        depurar_logs(f"Tentativa de adicionar cliente a grupo de usuário inexistente: {usuario}", "WARNING")
        return False
    
    # Verifica se o cliente já está no grupo
    if cliente in grupos[usuario]["clientes"]:
        return True  # Cliente já está no grupo, não precisa adicionar
    
    # Adiciona o cliente ao grupo
    grupos[usuario]["clientes"].append(cliente)
    
    sucesso = salvar_grupos(grupos)
    if sucesso:
        depurar_logs(f"Cliente {cliente} adicionado ao grupo do usuário {usuario}", "INFO")
    
    return sucesso

def adicionar_cliente_grupo(id_grupo, cliente, operador=None):
    """
    Adiciona um cliente a um grupo.
    
    Args:
        id_grupo (str): ID do grupo
        cliente (str): Nome do cliente a ser adicionado
        operador (str): Nome do usuário que está realizando a operação
        
    Returns:
        bool: True se o cliente foi adicionado com sucesso, False caso contrário
    """
    grupos = carregar_grupos()
    
    # Verifica se o grupo existe
    if id_grupo not in grupos:
        depurar_logs(f"Tentativa de adicionar cliente a grupo inexistente: {id_grupo} por {operador}", "WARNING")
        return False
    
    # Verifica se o cliente já está no grupo
    if cliente in grupos[id_grupo]["clientes"]:
        depurar_logs(f"Cliente {cliente} já está no grupo {id_grupo}", "INFO")
        return True
    
    # Adiciona o cliente ao grupo
    grupos[id_grupo]["clientes"].append(cliente)
    
    sucesso = salvar_grupos(grupos)
    if sucesso:
        depurar_logs(f"Cliente {cliente} adicionado ao grupo {id_grupo} por {operador}", "INFO")
    
    return sucesso

def remover_cliente_grupo(id_grupo, cliente, operador=None):
    """
    Remove um cliente de um grupo.
    
    Args:
        id_grupo (str): ID do grupo
        cliente (str): Nome do cliente a ser removido
        operador (str): Nome do usuário que está realizando a operação
        
    Returns:
        bool: True se o cliente foi removido com sucesso, False caso contrário
    """
    grupos = carregar_grupos()
    
    # Verifica se o grupo existe
    if id_grupo not in grupos:
        depurar_logs(f"Tentativa de remover cliente de grupo inexistente: {id_grupo} por {operador}", "WARNING")
        return False
    
    # Verifica se o cliente está no grupo
    if cliente not in grupos[id_grupo]["clientes"]:
        depurar_logs(f"Cliente {cliente} não está no grupo {id_grupo}", "INFO")
        return False
    
    # Remove o cliente do grupo
    grupos[id_grupo]["clientes"].remove(cliente)
    
    sucesso = salvar_grupos(grupos)
    if sucesso:
        depurar_logs(f"Cliente {cliente} removido do grupo {id_grupo} por {operador}", "INFO")
    
    return sucesso

def adicionar_usuario_grupo(id_grupo, usuario, operador=None):
    """
    Adiciona um usuário a um grupo.
    
    Args:
        id_grupo (str): ID do grupo
        usuario (str): Nome do usuário a ser adicionado
        operador (str): Nome do usuário que está realizando a operação
        
    Returns:
        bool: True se o usuário foi adicionado com sucesso, False caso contrário
    """
    grupos = carregar_grupos()
    
    # Verifica se o grupo existe
    if id_grupo not in grupos:
        depurar_logs(f"Tentativa de adicionar usuário a grupo inexistente: {id_grupo} por {operador}", "WARNING")
        return False
    
    # Verifica se o usuário já está no grupo
    if usuario in grupos[id_grupo]["usuarios"]:
        depurar_logs(f"Usuário {usuario} já está no grupo {id_grupo}", "INFO")
        return True
    
    # Adiciona o usuário ao grupo
    grupos[id_grupo]["usuarios"].append(usuario)
    
    sucesso = salvar_grupos(grupos)
    if sucesso:
        depurar_logs(f"Usuário {usuario} adicionado ao grupo {id_grupo} por {operador}", "INFO")
    
    return sucesso

def remover_usuario_grupo(id_grupo, usuario, operador=None):
    """
    Remove um usuário de um grupo.
    
    Args:
        id_grupo (str): ID do grupo
        usuario (str): Nome do usuário a ser removido
        operador (str): Nome do usuário que está realizando a operação
        
    Returns:
        bool: True se o usuário foi removido com sucesso, False caso contrário
    """
    grupos = carregar_grupos()
    
    # Verifica se o grupo existe
    if id_grupo not in grupos:
        depurar_logs(f"Tentativa de remover usuário de grupo inexistente: {id_grupo} por {operador}", "WARNING")
        return False
    
    # Verifica se o usuário está no grupo
    if usuario not in grupos[id_grupo]["usuarios"]:
        depurar_logs(f"Usuário {usuario} não está no grupo {id_grupo}", "INFO")
        return False
    
    # Impede a remoção do usuário 'admin' do grupo 'admin' ou 'all'
    if (id_grupo == "admin" or id_grupo == "all") and usuario == "admin":
        depurar_logs(f"Tentativa de remover admin do grupo '{id_grupo}' por {operador}", "WARNING")
        return False
    
    # Impede a remoção de um usuário do seu próprio grupo pessoal
    if id_grupo == usuario:
        depurar_logs(f"Tentativa de remover usuário {usuario} do seu próprio grupo pessoal por {operador}", "WARNING")
        return False
    
    # Remove o usuário do grupo
    grupos[id_grupo]["usuarios"].remove(usuario)
    
    sucesso = salvar_grupos(grupos)
    if sucesso:
        depurar_logs(f"Usuário {usuario} removido do grupo {id_grupo} por {operador}", "INFO")
    
    return sucesso

def listar_grupos(mostrar_detalhes=False):
    """
    Lista todos os grupos cadastrados.
    
    Args:
        mostrar_detalhes (bool): Se True, mostra também clientes e usuários de cada grupo
        
    Returns:
        dict: Dicionário com informações dos grupos
    """
    return carregar_grupos()

def obter_grupos_usuario(username):
    """
    Obtém todos os grupos aos quais um usuário pertence.
    
    Args:
        username (str): Nome do usuário
        
    Returns:
        list: Lista com os IDs dos grupos aos quais o usuário pertence
    """
    grupos = carregar_grupos()
    grupos_do_usuario = []
    
    for id_grupo, dados in grupos.items():
        if username in dados["usuarios"]:
            grupos_do_usuario.append(id_grupo)
    
    return grupos_do_usuario

def obter_clientes_usuario(username):
    """
    Obtém todos os clientes que um usuário está autorizado a acessar,
    com base nos grupos aos quais o usuário pertence.
    
    Args:
        username (str): Nome do usuário
        
    Returns:
        list: Lista com os nomes dos clientes que o usuário pode acessar
    """
    grupos = carregar_grupos()
    grupos_do_usuario = obter_grupos_usuario(username)
    clientes_autorizados = []
    
    # Se o usuário é admin ou pertence ao grupo admin, retorna uma lista vazia 
    # que será interpretada como "todos os clientes"
    if username == "admin" or "admin" in grupos_do_usuario:
        return []
    
    # Se o usuário pertence a algum grupo
    for id_grupo in grupos_do_usuario:
        if id_grupo in grupos:
            # Adiciona os clientes do grupo à lista de autorizados
            clientes_autorizados.extend(grupos[id_grupo]["clientes"])
    
    # Remove duplicatas
    clientes_autorizados = list(set(clientes_autorizados))
    
    return clientes_autorizados


def usuario_pode_acessar_cliente(username, cliente):
    """
    Verifica se um usuário está autorizado a acessar um determinado cliente.
    
    Args:
        username (str): Nome do usuário
        cliente (str): Nome do cliente
        
    Returns:
        bool: True se o usuário pode acessar o cliente, False caso contrário
    """
    # Se o usuário pertence ao grupo admin, pode acessar qualquer cliente
    grupos_do_usuario = obter_grupos_usuario(username)
    if "admin" in grupos_do_usuario:
        return True
    
    # Obtém os clientes que o usuário pode acessar
    clientes_autorizados = obter_clientes_usuario(username)
    
    # Verifica se o cliente específico está na lista de autorizados
    return cliente in clientes_autorizados

def sincronizar_clientes(todos_clientes):
    """
    Sincroniza a lista completa de clientes do sistema com o grupo 'all' e 'admin'.
    
    Args:
        todos_clientes (list): Lista com todos os clientes do sistema
        
    Returns:
        bool: True se a sincronização foi bem-sucedida, False caso contrário
    """
    grupos = carregar_grupos()
    
    # Verifica se os grupos admin e all existem
    if "all" not in grupos or "admin" not in grupos:
        depurar_logs("Grupos 'all' ou 'admin' não encontrados durante sincronização de clientes", "WARNING")
        return False
    
    # Atualiza a lista de clientes dos grupos administrativos
    grupos["all"]["clientes"] = todos_clientes
    grupos["admin"]["clientes"] = todos_clientes
    
    sucesso = salvar_grupos(grupos)
    if sucesso:
        depurar_logs(f"Clientes sincronizados com grupos administrativos: {len(todos_clientes)} clientes", "INFO")
    
    return sucesso