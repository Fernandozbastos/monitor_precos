#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo de gestão de grupos para o Sistema de Monitoramento de Preços
--------------------------------------------------------------------
Versão para banco de dados SQLite.
"""

from database_config import criar_conexao
from utils import depurar_logs
from datetime import datetime

def criar_grupo_para_usuario(username, nome_usuario=None):
    """
    Cria um grupo personalizado para um novo usuário, se ainda não existir.
    
    Args:
        username (str): Nome de usuário para criar o grupo
        nome_usuario (str, optional): Nome completo do usuário para exibição
        
    Returns:
        bool: True se o grupo foi criado com sucesso, False caso contrário
    """
    try:
        conexao, cursor = criar_conexao()
        
        # Verificar se já existe um grupo para este usuário
        cursor.execute("SELECT id FROM grupos WHERE id_grupo = ?", (username,))
        if cursor.fetchone():
            conexao.close()
            return True  # Grupo já existe
        
        # Criar nome de exibição para o grupo
        nome_grupo = f"Grupo de {nome_usuario}" if nome_usuario else f"Grupo de {username}"
        data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Criar o grupo
        cursor.execute('''
        INSERT INTO grupos (id_grupo, nome, descricao, data_criacao)
        VALUES (?, ?, ?, ?)
        ''', (username, nome_grupo, f"Grupo pessoal do usuário {username}", data_atual))
        
        # Obter ID do grupo criado
        cursor.execute("SELECT id FROM grupos WHERE id_grupo = ?", (username,))
        id_grupo = cursor.fetchone()['id']
        
        # Obter ID do usuário
        cursor.execute("SELECT id FROM usuarios WHERE username = ?", (username,))
        id_usuario = cursor.fetchone()['id']
        
        # Associar o usuário ao seu próprio grupo
        cursor.execute('''
        INSERT INTO usuarios_grupos (id_usuario, id_grupo, data_associacao)
        VALUES (?, ?, ?)
        ''', (id_usuario, id_grupo, data_atual))
        
        conexao.commit()
        conexao.close()
        
        depurar_logs(f"Grupo pessoal criado para o usuário: {username}", "INFO")
        return True
        
    except Exception as e:
        depurar_logs(f"Erro ao criar grupo para usuário: {e}", "ERROR")
        return False

def adicionar_cliente_a_todos_grupos_admin(cliente):
    """
    Adiciona um cliente a todos os grupos de administração (admin e all).
    
    Args:
        cliente (str): Nome do cliente a ser adicionado
        
    Returns:
        bool: True se o cliente foi adicionado com sucesso, False caso contrário
    """
    try:
        conexao, cursor = criar_conexao()
        
        # Verificar se o cliente existe
        cursor.execute("SELECT id FROM clientes WHERE nome = ?", (cliente,))
        resultado = cursor.fetchone()
        
        if not resultado:
            # Cliente não existe, criar primeiro
            data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute("INSERT INTO clientes (nome, data_criacao) VALUES (?, ?)", 
                          (cliente, data_atual))
            
            # Obter ID do cliente recém-criado
            cursor.execute("SELECT id FROM clientes WHERE nome = ?", (cliente,))
            resultado = cursor.fetchone()
        
        id_cliente = resultado['id']
        
        # Obter IDs dos grupos admin e all
        cursor.execute("SELECT id FROM grupos WHERE id_grupo = 'admin'")
        id_grupo_admin = cursor.fetchone()['id']
        
        cursor.execute("SELECT id FROM grupos WHERE id_grupo = 'all'")
        id_grupo_all = cursor.fetchone()['id']
        
        data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Associar cliente ao grupo admin
        cursor.execute('''
        INSERT OR IGNORE INTO clientes_grupos (id_cliente, id_grupo, data_associacao)
        VALUES (?, ?, ?)
        ''', (id_cliente, id_grupo_admin, data_atual))
        
        # Associar cliente ao grupo all
        cursor.execute('''
        INSERT OR IGNORE INTO clientes_grupos (id_cliente, id_grupo, data_associacao)
        VALUES (?, ?, ?)
        ''', (id_cliente, id_grupo_all, data_atual))
        
        conexao.commit()
        conexao.close()
        
        depurar_logs(f"Cliente '{cliente}' adicionado aos grupos de administração", "INFO")
        return True
        
    except Exception as e:
        depurar_logs(f"Erro ao adicionar cliente aos grupos de administração: {e}", "ERROR")
        return False

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
    
    try:
        conexao, cursor = criar_conexao()
        
        # Verificar se o grupo já existe
        cursor.execute("SELECT id FROM grupos WHERE id_grupo = ?", (id_grupo,))
        if cursor.fetchone():
            depurar_logs(f"Tentativa de criar grupo com ID já existente: {id_grupo} por {operador}", "WARNING")
            conexao.close()
            return False
        
        # Criar o grupo
        data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
        INSERT INTO grupos (id_grupo, nome, descricao, data_criacao)
        VALUES (?, ?, ?, ?)
        ''', (id_grupo, nome, descricao, data_atual))
        
        conexao.commit()
        conexao.close()
        
        depurar_logs(f"Novo grupo criado: {id_grupo} ({nome}) por {operador}", "INFO")
        return True
        
    except Exception as e:
        depurar_logs(f"Erro ao criar grupo: {e}", "ERROR")
        return False

def remover_grupo(id_grupo, operador=None):
    """
    Remove um grupo existente.
    
    Args:
        id_grupo (str): ID do grupo a ser removido
        operador (str): Nome do usuário que está realizando a operação
        
    Returns:
        bool: True se o grupo foi removido com sucesso, False caso contrário
    """
    try:
        conexao, cursor = criar_conexao()
        
        # Verificar se o grupo existe
        cursor.execute("SELECT id FROM grupos WHERE id_grupo = ?", (id_grupo,))
        resultado = cursor.fetchone()
        
        if not resultado:
            depurar_logs(f"Tentativa de remover grupo inexistente: {id_grupo} por {operador}", "WARNING")
            conexao.close()
            return False
        
        # Impedir a remoção dos grupos padrão
        if id_grupo in ["admin", "all"]:
            depurar_logs(f"Tentativa de remover grupo padrão '{id_grupo}' por {operador}", "WARNING")
            conexao.close()
            return False
        
        id_grupo_bd = resultado['id']
        
        # Remover associações de usuários com o grupo
        cursor.execute("DELETE FROM usuarios_grupos WHERE id_grupo = ?", (id_grupo_bd,))
        
        # Remover associações de clientes com o grupo
        cursor.execute("DELETE FROM clientes_grupos WHERE id_grupo = ?", (id_grupo_bd,))
        
        # Finalmente, remover o grupo
        cursor.execute("DELETE FROM grupos WHERE id = ?", (id_grupo_bd,))
        
        conexao.commit()
        conexao.close()
        
        depurar_logs(f"Grupo removido: {id_grupo} por {operador}", "INFO")
        return True
        
    except Exception as e:
        depurar_logs(f"Erro ao remover grupo: {e}", "ERROR")
        return False

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
    
    try:
        conexao, cursor = criar_conexao()
        
        # Verificar se o grupo do usuário existe
        cursor.execute("SELECT id FROM grupos WHERE id_grupo = ?", (usuario,))
        resultado_grupo = cursor.fetchone()
        
        if not resultado_grupo:
            depurar_logs(f"Tentativa de adicionar cliente a grupo de usuário inexistente: {usuario}", "WARNING")
            conexao.close()
            return False
        
        id_grupo = resultado_grupo['id']
        
        # Verificar se o cliente existe
        cursor.execute("SELECT id FROM clientes WHERE nome = ?", (cliente,))
        resultado_cliente = cursor.fetchone()
        
        if not resultado_cliente:
            # Cliente não existe, criar primeiro
            data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute("INSERT INTO clientes (nome, data_criacao) VALUES (?, ?)", 
                          (cliente, data_atual))
            
            # Obter ID do cliente recém-criado
            cursor.execute("SELECT id FROM clientes WHERE nome = ?", (cliente,))
            resultado_cliente = cursor.fetchone()
        
        id_cliente = resultado_cliente['id']
        
        # Verificar se a associação já existe
        cursor.execute('''
        SELECT id FROM clientes_grupos WHERE id_cliente = ? AND id_grupo = ?
        ''', (id_cliente, id_grupo))
        
        if cursor.fetchone():
            # Associação já existe
            conexao.close()
            return True
        
        # Criar a associação
        data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
        INSERT INTO clientes_grupos (id_cliente, id_grupo, data_associacao)
        VALUES (?, ?, ?)
        ''', (id_cliente, id_grupo, data_atual))
        
        conexao.commit()
        conexao.close()
        
        depurar_logs(f"Cliente {cliente} adicionado ao grupo do usuário {usuario}", "INFO")
        return True
        
    except Exception as e:
        depurar_logs(f"Erro ao adicionar cliente ao grupo do usuário: {e}", "ERROR")
        return False

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
    try:
        conexao, cursor = criar_conexao()
        
        # Verificar se o grupo existe
        cursor.execute("SELECT id FROM grupos WHERE id_grupo = ?", (id_grupo,))
        resultado_grupo = cursor.fetchone()
        
        if not resultado_grupo:
            depurar_logs(f"Tentativa de adicionar cliente a grupo inexistente: {id_grupo} por {operador}", "WARNING")
            conexao.close()
            return False
        
        id_grupo_bd = resultado_grupo['id']
        
        # Verificar se o cliente existe
        cursor.execute("SELECT id FROM clientes WHERE nome = ?", (cliente,))
        resultado_cliente = cursor.fetchone()
        
        if not resultado_cliente:
            # Cliente não existe, criar primeiro
            data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute("INSERT INTO clientes (nome, data_criacao) VALUES (?, ?)", 
                          (cliente, data_atual))
            
            # Obter ID do cliente recém-criado
            cursor.execute("SELECT id FROM clientes WHERE nome = ?", (cliente,))
            resultado_cliente = cursor.fetchone()
        
        id_cliente = resultado_cliente['id']
        
        # Verificar se a associação já existe
        cursor.execute('''
        SELECT id FROM clientes_grupos WHERE id_cliente = ? AND id_grupo = ?
        ''', (id_cliente, id_grupo_bd))
        
        if cursor.fetchone():
            depurar_logs(f"Cliente {cliente} já está no grupo {id_grupo}", "INFO")
            conexao.close()
            return True
        
        # Criar a associação
        data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
        INSERT INTO clientes_grupos (id_cliente, id_grupo, data_associacao)
        VALUES (?, ?, ?)
        ''', (id_cliente, id_grupo_bd, data_atual))
        
        conexao.commit()
        conexao.close()
        
        depurar_logs(f"Cliente {cliente} adicionado ao grupo {id_grupo} por {operador}", "INFO")
        return True
        
    except Exception as e:
        depurar_logs(f"Erro ao adicionar cliente ao grupo: {e}", "ERROR")
        return False

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
    try:
        conexao, cursor = criar_conexao()
        
        # Verificar se o grupo existe
        cursor.execute("SELECT id FROM grupos WHERE id_grupo = ?", (id_grupo,))
        resultado_grupo = cursor.fetchone()
        
        if not resultado_grupo:
            depurar_logs(f"Tentativa de remover cliente de grupo inexistente: {id_grupo} por {operador}", "WARNING")
            conexao.close()
            return False
        
        id_grupo_bd = resultado_grupo['id']
        
        # Verificar se o cliente existe
        cursor.execute("SELECT id FROM clientes WHERE nome = ?", (cliente,))
        resultado_cliente = cursor.fetchone()
        
        if not resultado_cliente:
            depurar_logs(f"Tentativa de remover cliente inexistente: {cliente} por {operador}", "WARNING")
            conexao.close()
            return False
        
        id_cliente = resultado_cliente['id']
        
        # Verificar se a associação existe
        cursor.execute('''
        SELECT id FROM clientes_grupos WHERE id_cliente = ? AND id_grupo = ?
        ''', (id_cliente, id_grupo_bd))
        
        if not cursor.fetchone():
            depurar_logs(f"Cliente {cliente} não está no grupo {id_grupo}", "INFO")
            conexao.close()
            return False
        
        # Remover a associação
        cursor.execute('''
        DELETE FROM clientes_grupos WHERE id_cliente = ? AND id_grupo = ?
        ''', (id_cliente, id_grupo_bd))
        
        conexao.commit()
        conexao.close()
        
        depurar_logs(f"Cliente {cliente} removido do grupo {id_grupo} por {operador}", "INFO")
        return True
        
    except Exception as e:
        depurar_logs(f"Erro ao remover cliente do grupo: {e}", "ERROR")
        return False

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
    try:
        conexao, cursor = criar_conexao()
        
        # Verificar se o grupo existe
        cursor.execute("SELECT id FROM grupos WHERE id_grupo = ?", (id_grupo,))
        resultado_grupo = cursor.fetchone()
        
        if not resultado_grupo:
            depurar_logs(f"Tentativa de adicionar usuário a grupo inexistente: {id_grupo} por {operador}", "WARNING")
            conexao.close()
            return False
        
        id_grupo_bd = resultado_grupo['id']
        
        # Verificar se o usuário existe
        cursor.execute("SELECT id FROM usuarios WHERE username = ?", (usuario,))
        resultado_usuario = cursor.fetchone()
        
        if not resultado_usuario:
            depurar_logs(f"Tentativa de adicionar usuário inexistente: {usuario} por {operador}", "WARNING")
            conexao.close()
            return False
        
        id_usuario = resultado_usuario['id']
        
        # Verificar se a associação já existe
        cursor.execute('''
        SELECT id FROM usuarios_grupos WHERE id_usuario = ? AND id_grupo = ?
        ''', (id_usuario, id_grupo_bd))
        
        if cursor.fetchone():
            depurar_logs(f"Usuário {usuario} já está no grupo {id_grupo}", "INFO")
            conexao.close()
            return True
        
        # Criar a associação
        data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
        INSERT INTO usuarios_grupos (id_usuario, id_grupo, data_associacao)
        VALUES (?, ?, ?)
        ''', (id_usuario, id_grupo_bd, data_atual))
        
        conexao.commit()
        conexao.close()
        
        depurar_logs(f"Usuário {usuario} adicionado ao grupo {id_grupo} por {operador}", "INFO")
        return True
        
    except Exception as e:
        depurar_logs(f"Erro ao adicionar usuário ao grupo: {e}", "ERROR")
        return False

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
    try:
        conexao, cursor = criar_conexao()
        
        # Verificar se o grupo existe
        cursor.execute("SELECT id FROM grupos WHERE id_grupo = ?", (id_grupo,))
        resultado_grupo = cursor.fetchone()
        
        if not resultado_grupo:
            depurar_logs(f"Tentativa de remover usuário de grupo inexistente: {id_grupo} por {operador}", "WARNING")
            conexao.close()
            return False
        
        id_grupo_bd = resultado_grupo['id']
        
        # Verificar se o usuário existe
        cursor.execute("SELECT id FROM usuarios WHERE username = ?", (usuario,))
        resultado_usuario = cursor.fetchone()
        
        if not resultado_usuario:
            depurar_logs(f"Tentativa de remover usuário inexistente: {usuario} por {operador}", "WARNING")
            conexao.close()
            return False
        
        id_usuario = resultado_usuario['id']
        
        # Verificar se a associação existe
        cursor.execute('''
        SELECT id FROM usuarios_grupos WHERE id_usuario = ? AND id_grupo = ?
        ''', (id_usuario, id_grupo_bd))
        
        if not cursor.fetchone():
            depurar_logs(f"Usuário {usuario} não está no grupo {id_grupo}", "INFO")
            conexao.close()
            return False
        
        # Impedir a remoção do usuário 'admin' do grupo 'admin' ou 'all'
        if (id_grupo == "admin" or id_grupo == "all") and usuario == "admin":
            depurar_logs(f"Tentativa de remover admin do grupo '{id_grupo}' por {operador}", "WARNING")
            conexao.close()
            return False
        
        # Impedir a remoção de um usuário do seu próprio grupo pessoal
        if id_grupo == usuario:
            depurar_logs(f"Tentativa de remover usuário {usuario} do seu próprio grupo pessoal por {operador}", "WARNING")
            conexao.close()
            return False
        
# Remover a associação
        cursor.execute('''
        DELETE FROM usuarios_grupos WHERE id_usuario = ? AND id_grupo = ?
        ''', (id_usuario, id_grupo_bd))
        
        conexao.commit()
        conexao.close()
        
        depurar_logs(f"Usuário {usuario} removido do grupo {id_grupo} por {operador}", "INFO")
        return True
        
    except Exception as e:
        depurar_logs(f"Erro ao remover usuário do grupo: {e}", "ERROR")
        return False

def listar_grupos(mostrar_detalhes=False):
    """
    Lista todos os grupos cadastrados.
    
    Args:
        mostrar_detalhes (bool): Se True, mostra também clientes e usuários de cada grupo
        
    Returns:
        dict: Dicionário com informações dos grupos
    """
    try:
        conexao, cursor = criar_conexao()
        
        # Obter todos os grupos
        cursor.execute("SELECT id, id_grupo, nome, descricao FROM grupos")
        grupos_raw = cursor.fetchall()
        
        grupos = {}
        
        for grupo in grupos_raw:
            id_grupo_bd = grupo['id']
            id_grupo = grupo['id_grupo']
            
            # Estrutura básica do grupo
            grupos[id_grupo] = {
                'nome': grupo['nome'],
                'descricao': grupo['descricao'],
                'clientes': [],
                'usuarios': []
            }
            
            if mostrar_detalhes:
                # Obter clientes do grupo
                cursor.execute('''
                SELECT c.nome 
                FROM clientes c
                JOIN clientes_grupos cg ON c.id = cg.id_cliente
                WHERE cg.id_grupo = ?
                ORDER BY c.nome
                ''', (id_grupo_bd,))
                
                clientes = [row['nome'] for row in cursor.fetchall()]
                grupos[id_grupo]['clientes'] = clientes
                
                # Obter usuários do grupo
                cursor.execute('''
                SELECT u.username 
                FROM usuarios u
                JOIN usuarios_grupos ug ON u.id = ug.id_usuario
                WHERE ug.id_grupo = ?
                ORDER BY u.username
                ''', (id_grupo_bd,))
                
                usuarios = [row['username'] for row in cursor.fetchall()]
                grupos[id_grupo]['usuarios'] = usuarios
        
        conexao.close()
        return grupos
        
    except Exception as e:
        depurar_logs(f"Erro ao listar grupos: {e}", "ERROR")
        return {}

def obter_grupos_usuario(username):
    """
    Obtém todos os grupos aos quais um usuário pertence.
    
    Args:
        username (str): Nome do usuário
        
    Returns:
        list: Lista com os IDs dos grupos aos quais o usuário pertence
    """
    try:
        conexao, cursor = criar_conexao()
        
        cursor.execute('''
        SELECT g.id_grupo 
        FROM grupos g
        JOIN usuarios_grupos ug ON g.id = ug.id_grupo
        JOIN usuarios u ON ug.id_usuario = u.id
        WHERE u.username = ?
        ORDER BY g.id_grupo
        ''', (username,))
        
        grupos = [row['id_grupo'] for row in cursor.fetchall()]
        
        conexao.close()
        return grupos
        
    except Exception as e:
        depurar_logs(f"Erro ao obter grupos do usuário: {e}", "ERROR")
        return []

def obter_clientes_usuario(username):
    """
    Obtém todos os clientes que um usuário está autorizado a acessar,
    com base nos grupos aos quais o usuário pertence.
    
    Args:
        username (str): Nome do usuário
        
    Returns:
        list: Lista com os nomes dos clientes que o usuário pode acessar
    """
    try:
        print(f"DEBUG: Obtendo clientes para o usuário {username}")
        
        conexao, cursor = criar_conexao()
        
        # Verificar se o usuário é admin ou pertence ao grupo admin
        cursor.execute('''
        SELECT u.tipo FROM usuarios u WHERE u.username = ?
        ''', (username,))
        resultado = cursor.fetchone()
        
        if resultado and resultado['tipo'] == 'admin':
            print(f"DEBUG: Usuário {username} é do tipo admin")
            # Usuário é admin, retorna todos os clientes
            cursor.execute("SELECT nome FROM clientes")
            todos_clientes = [row['nome'] for row in cursor.fetchall()]
            conexao.close()
            print(f"DEBUG: Retornando todos os clientes ({len(todos_clientes)})")
            return todos_clientes
        
        # Verificar se o usuário pertence ao grupo admin
        cursor.execute('''
        SELECT g.id_grupo 
        FROM grupos g
        JOIN usuarios_grupos ug ON g.id = ug.id_grupo
        JOIN usuarios u ON ug.id_usuario = u.id
        WHERE u.username = ? AND g.id_grupo = 'admin'
        ''', (username,))
        
        if cursor.fetchone():
            print(f"DEBUG: Usuário {username} pertence ao grupo admin")
            # Usuário pertence ao grupo admin, retorna todos os clientes
            cursor.execute("SELECT nome FROM clientes")
            todos_clientes = [row['nome'] for row in cursor.fetchall()]
            conexao.close()
            print(f"DEBUG: Retornando todos os clientes ({len(todos_clientes)})")
            return todos_clientes
        
        # Obter clientes dos grupos do usuário
        cursor.execute('''
        SELECT DISTINCT c.nome 
        FROM clientes c
        JOIN clientes_grupos cg ON c.id = cg.id_cliente
        JOIN grupos g ON cg.id_grupo = g.id
        JOIN usuarios_grupos ug ON g.id = ug.id_grupo
        JOIN usuarios u ON ug.id_usuario = u.id
        WHERE u.username = ?
        ORDER BY c.nome
        ''', (username,))
        
        clientes = [row['nome'] for row in cursor.fetchall()]
        
        print(f"DEBUG: Encontrados {len(clientes)} clientes para o usuário {username}")
        conexao.close()
        return clientes
        
    except Exception as e:
        import traceback
        print(f"Erro ao obter clientes do usuário: {e}")
        print(traceback.format_exc())
        return []

def usuario_pode_acessar_cliente(username, cliente):
    """
    Verifica se um usuário está autorizado a acessar um determinado cliente.
    
    Args:
        username (str): Nome do usuário
        cliente (str): Nome do cliente
        
    Returns:
        bool: True se o usuário pode acessar o cliente, False caso contrário
    """
    try:
        conexao, cursor = criar_conexao()
        
        # Verificar se o usuário é admin ou pertence ao grupo admin
        cursor.execute('''
        SELECT u.tipo FROM usuarios u WHERE u.username = ?
        ''', (username,))
        resultado = cursor.fetchone()
        
        if resultado and resultado['tipo'] == 'admin':
            # Usuário é admin, pode acessar qualquer cliente
            conexao.close()
            return True
            
        cursor.execute('''
        SELECT g.id_grupo 
        FROM grupos g
        JOIN usuarios_grupos ug ON g.id = ug.id_grupo
        JOIN usuarios u ON ug.id_usuario = u.id
        WHERE u.username = ? AND g.id_grupo = 'admin'
        ''', (username,))
        
        if cursor.fetchone():
            # Usuário pertence ao grupo admin, pode acessar qualquer cliente
            conexao.close()
            return True
        
        # Verificar se o usuário tem acesso ao cliente específico
        cursor.execute('''
        SELECT COUNT(*) as count
        FROM clientes c
        JOIN clientes_grupos cg ON c.id = cg.id_cliente
        JOIN grupos g ON cg.id_grupo = g.id
        JOIN usuarios_grupos ug ON g.id = ug.id_grupo
        JOIN usuarios u ON ug.id_usuario = u.id
        WHERE u.username = ? AND c.nome = ?
        ''', (username, cliente))
        
        resultado = cursor.fetchone()
        
        conexao.close()
        
        return resultado['count'] > 0
        
    except Exception as e:
        depurar_logs(f"Erro ao verificar acesso do usuário ao cliente: {e}", "ERROR")
        return False

def sincronizar_clientes(todos_clientes):
    """
    Sincroniza a lista completa de clientes do sistema com o grupo 'all' e 'admin'.
    
    Args:
        todos_clientes (list): Lista com todos os clientes do sistema
        
    Returns:
        bool: True se a sincronização foi bem-sucedida, False caso contrário
    """
    try:
        conexao, cursor = criar_conexao()
        
        # Obter IDs dos grupos all e admin
        cursor.execute("SELECT id FROM grupos WHERE id_grupo = 'all'")
        resultado_all = cursor.fetchone()
        
        cursor.execute("SELECT id FROM grupos WHERE id_grupo = 'admin'")
        resultado_admin = cursor.fetchone()
        
        if not resultado_all or not resultado_admin:
            depurar_logs("Grupos 'all' ou 'admin' não encontrados durante sincronização de clientes", "WARNING")
            conexao.close()
            return False
        
        id_grupo_all = resultado_all['id']
        id_grupo_admin = resultado_admin['id']
        
        data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Para cada cliente na lista
        for cliente in todos_clientes:
            # Verificar se o cliente existe
            cursor.execute("SELECT id FROM clientes WHERE nome = ?", (cliente,))
            resultado = cursor.fetchone()
            
            if not resultado:
                # Cliente não existe, criar primeiro
                cursor.execute("INSERT INTO clientes (nome, data_criacao) VALUES (?, ?)", 
                              (cliente, data_atual))
                
                # Obter ID do cliente recém-criado
                cursor.execute("SELECT id FROM clientes WHERE nome = ?", (cliente,))
                resultado = cursor.fetchone()
            
            id_cliente = resultado['id']
            
            # Associar ao grupo all
            cursor.execute('''
            INSERT OR IGNORE INTO clientes_grupos (id_cliente, id_grupo, data_associacao)
            VALUES (?, ?, ?)
            ''', (id_cliente, id_grupo_all, data_atual))
            
            # Associar ao grupo admin
            cursor.execute('''
            INSERT OR IGNORE INTO clientes_grupos (id_cliente, id_grupo, data_associacao)
            VALUES (?, ?, ?)
            ''', (id_cliente, id_grupo_admin, data_atual))
        
        conexao.commit()
        conexao.close()
        
        depurar_logs(f"Clientes sincronizados com grupos administrativos: {len(todos_clientes)} clientes", "INFO")
        return True
        
    except Exception as e:
        depurar_logs(f"Erro ao sincronizar clientes: {e}", "ERROR")
        return False