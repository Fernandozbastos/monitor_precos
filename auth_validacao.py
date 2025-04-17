#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo de validação e organização do arquivo de usuários
--------------------------------------------------------
Complemento para o módulo de autenticação, garantindo a integridade
e estrutura correta do arquivo usuarios.json.
"""

import os
import json
from utils import depurar_logs

# Estrutura padrão esperada para cada usuário
USUARIO_PADRAO = {
    "senha": "",
    "nome": "",
    "tipo": "usuario",
    "ativo": True,
    "email": "",
    "data_criacao": "",
    "ultimo_acesso": None,
    "permissoes": []
}

def validar_estrutura_usuarios(usuarios):
    """
    Valida se o dicionário de usuários possui a estrutura correta.
    
    Args:
        usuarios (dict): Dicionário com os usuários
        
    Returns:
        tuple: (valido, usuarios_corrigidos) onde valido é um booleano indicando
               se a estrutura está correta e usuarios_corrigidos é o dicionário
               corrigido com a estrutura adequada
    """
    if not isinstance(usuarios, dict):
        depurar_logs("Arquivo de usuários não é um dicionário válido", "ERROR")
        return False, {}
    
    usuarios_corrigidos = {}
    alteracoes = False
    
    for username, dados in usuarios.items():
        if not isinstance(dados, dict):
            depurar_logs(f"Dados inválidos para o usuário {username}", "WARNING")
            # Criar uma estrutura básica para o usuário inválido
            usuarios_corrigidos[username] = USUARIO_PADRAO.copy()
            usuarios_corrigidos[username]["senha"] = "RESETAR_SENHA"
            usuarios_corrigidos[username]["nome"] = f"Usuário {username}"
            alteracoes = True
            continue
            
        # Cria uma cópia para não modificar o original durante a iteração
        usuario_corrigido = {}
        
        # Verifica campos obrigatórios
        for campo, valor_padrao in USUARIO_PADRAO.items():
            if campo not in dados:
                usuario_corrigido[campo] = valor_padrao
                alteracoes = True
            else:
                usuario_corrigido[campo] = dados[campo]
        
        # Verifica tipos de dados
        if not isinstance(usuario_corrigido["senha"], str):
            usuario_corrigido["senha"] = str(usuario_corrigido["senha"])
            alteracoes = True
            
        if not isinstance(usuario_corrigido["nome"], str):
            usuario_corrigido["nome"] = f"Usuário {username}"
            alteracoes = True
            
        if usuario_corrigido["tipo"] not in ["admin", "usuario"]:
            usuario_corrigido["tipo"] = "usuario"
            alteracoes = True
            
        if not isinstance(usuario_corrigido["ativo"], bool):
            usuario_corrigido["ativo"] = bool(usuario_corrigido["ativo"])
            alteracoes = True
            
        if not isinstance(usuario_corrigido["permissoes"], list):
            usuario_corrigido["permissoes"] = []
            alteracoes = True
            
        # Mantém campos adicionais que possam existir
        for campo in dados:
            if campo not in USUARIO_PADRAO:
                usuario_corrigido[campo] = dados[campo]
        
        usuarios_corrigidos[username] = usuario_corrigido
    
    return not alteracoes, usuarios_corrigidos

def verificar_e_corrigir_arquivo(arquivo_usuarios='usuarios.json'):
    """
    Verifica se o arquivo de usuários existe, valida sua estrutura e corrige se necessário.
    
    Args:
        arquivo_usuarios (str): Caminho para o arquivo de usuários
    
    Returns:
        bool: True se o arquivo está correto ou foi corrigido com sucesso, False caso contrário
    """
    try:
        if not os.path.isfile(arquivo_usuarios):
            # Arquivo não existe, será criado pelo módulo auth
            return True
            
        # Carrega o arquivo existente
        with open(arquivo_usuarios, 'r', encoding='utf-8') as f:
            try:
                usuarios = json.load(f)
            except json.JSONDecodeError:
                depurar_logs(f"Arquivo {arquivo_usuarios} não é um JSON válido", "ERROR")
                # Cria backup do arquivo corrompido
                if os.path.getsize(arquivo_usuarios) > 0:
                    import datetime
                    backup_file = f"{arquivo_usuarios}.bak.{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
                    os.rename(arquivo_usuarios, backup_file)
                    depurar_logs(f"Backup do arquivo corrompido criado: {backup_file}", "INFO")
                return False
        
        # Valida e corrige a estrutura
        valido, usuarios_corrigidos = validar_estrutura_usuarios(usuarios)
        
        if not valido:
            depurar_logs("Estrutura do arquivo de usuários corrigida", "INFO")
            # Salva o arquivo corrigido
            with open(arquivo_usuarios, 'w', encoding='utf-8') as f:
                json.dump(usuarios_corrigidos, f, ensure_ascii=False, indent=4)
                
        return True
    except Exception as e:
        depurar_logs(f"Erro ao verificar/corrigir arquivo de usuários: {str(e)}", "ERROR")
        return False

def organizar_usuarios_por_tipo(usuarios):
    """
    Organiza o dicionário de usuários por tipo (admin primeiro, depois usuários)
    
    Args:
        usuarios (dict): Dicionário com os usuários
        
    Returns:
        dict: Dicionário organizado com admins primeiro, seguidos de usuários
    """
    # Separa admins e usuários regulares
    admins = {k: v for k, v in usuarios.items() if v.get('tipo') == 'admin'}
    regulares = {k: v for k, v in usuarios.items() if v.get('tipo') != 'admin'}
    
    # Ordena cada grupo por nome de usuário
    admins_ordenados = dict(sorted(admins.items()))
    regulares_ordenados = dict(sorted(regulares.items()))
    
    # Combina os dois grupos
    return {**admins_ordenados, **regulares_ordenados}

def atualizar_arquivo_usuarios():
    """
    Atualiza o arquivo de usuários organizando-o por tipo e garantindo sua estrutura.
    
    Returns:
        bool: True se a atualização foi bem-sucedida, False caso contrário
    """
    try:
        arquivo_usuarios = 'usuarios.json'
        
        # Verifica se o arquivo existe
        if not os.path.isfile(arquivo_usuarios):
            return True  # Será criado pelo módulo auth
            
        # Carrega o arquivo
        with open(arquivo_usuarios, 'r', encoding='utf-8') as f:
            try:
                usuarios = json.load(f)
            except json.JSONDecodeError:
                depurar_logs(f"Arquivo {arquivo_usuarios} não é um JSON válido", "ERROR")
                return False
        
        # Valida e corrige a estrutura
        _, usuarios_corrigidos = validar_estrutura_usuarios(usuarios)
        
        # Organiza por tipo
        usuarios_organizados = organizar_usuarios_por_tipo(usuarios_corrigidos)
        
        # Salva o arquivo organizado
        with open(arquivo_usuarios, 'w', encoding='utf-8') as f:
            json.dump(usuarios_organizados, f, ensure_ascii=False, indent=4)
            
        depurar_logs("Arquivo de usuários organizado com sucesso", "INFO")
        return True
    except Exception as e:
        depurar_logs(f"Erro ao organizar arquivo de usuários: {str(e)}", "ERROR")
        return False

# Função para integrar com o módulo auth original
def verificar_e_organizar_usuarios():
    """
    Função principal para verificar, validar e organizar o arquivo de usuários.
    Deve ser chamada pelo módulo auth antes de carregar os usuários.
    
    Returns:
        bool: True se o arquivo está pronto para uso, False caso contrário
    """
    # Verifica e corrige a estrutura do arquivo
    if not verificar_e_corrigir_arquivo():
        return False
        
    # Organiza o arquivo por tipo de usuário
    return atualizar_arquivo_usuarios()