#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo de validação e organização da estrutura de usuários no banco de dados
---------------------------------------------------------------------------
Complemento para o módulo de autenticação, garantindo a integridade
e estrutura correta dos dados de usuários no banco SQLite.
"""

from utils import depurar_logs
from database_config import criar_conexao
from datetime import datetime

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

def validar_estrutura_usuarios():
    """
    Valida se os registros de usuários no banco de dados possuem a estrutura correta.
    
    Returns:
        tuple: (valido, correcoes) onde valido é um booleano indicando se a estrutura 
               está correta e correcoes é o número de correções realizadas
    """
    try:
        conexao, cursor = criar_conexao()
        
        # Verificar se a tabela existe
        cursor.execute('''
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='usuarios'
        ''')
        
        if not cursor.fetchone():
            depurar_logs("Tabela de usuários não existe no banco de dados", "ERROR")
            conexao.close()
            return False, 0
        
        # Verificar a estrutura da tabela
        cursor.execute("PRAGMA table_info(usuarios)")
        colunas = cursor.fetchall()
        
        colunas_existentes = [col['name'] for col in colunas]
        colunas_necessarias = ['username', 'senha', 'nome', 'tipo', 'ativo', 'cliente_atual', 'data_criacao', 'ultimo_acesso']
        
        # Verificar se todas as colunas necessárias existem
        colunas_faltantes = [col for col in colunas_necessarias if col not in colunas_existentes]
        
        if colunas_faltantes:
            depurar_logs(f"Faltam colunas na tabela de usuários: {', '.join(colunas_faltantes)}", "ERROR")
            conexao.close()
            return False, 0
        
        # Obter todos os usuários para validação
        cursor.execute("SELECT * FROM usuarios")
        usuarios = cursor.fetchall()
        
        correcoes = 0
        data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Verificar e corrigir cada usuário
        for usuario in usuarios:
            alteracoes = False
            
            # Verificar tipo
            if usuario['tipo'] not in ["admin", "usuario"]:
                cursor.execute("UPDATE usuarios SET tipo = ? WHERE id = ?", ("usuario", usuario['id']))
                alteracoes = True
                correcoes += 1
            
            # Verificar ativo (deve ser 0 ou 1)
            if usuario['ativo'] not in [0, 1]:
                cursor.execute("UPDATE usuarios SET ativo = ? WHERE id = ?", (1, usuario['id']))
                alteracoes = True
                correcoes += 1
            
            # Verificar nome (não pode ser vazio)
            if not usuario['nome']:
                novo_nome = f"Usuário {usuario['username']}"
                cursor.execute("UPDATE usuarios SET nome = ? WHERE id = ?", (novo_nome, usuario['id']))
                alteracoes = True
                correcoes += 1
            
            # Verificar data_criacao (não pode ser vazia)
            if not usuario['data_criacao']:
                cursor.execute("UPDATE usuarios SET data_criacao = ? WHERE id = ?", (data_atual, usuario['id']))
                alteracoes = True
                correcoes += 1
            
            if alteracoes:
                depurar_logs(f"Estrutura do usuário {usuario['username']} corrigida", "INFO")
        
        conexao.commit()
        conexao.close()
        
        if correcoes > 0:
            depurar_logs(f"Total de {correcoes} correções realizadas na estrutura de usuários", "INFO")
            return False, correcoes
        
        return True, 0
        
    except Exception as e:
        depurar_logs(f"Erro ao validar estrutura de usuários: {e}", "ERROR")
        return False, 0

def verificar_e_corrigir_banco():
    """
    Verifica se a tabela de usuários existe e tem a estrutura correta.
    
    Returns:
        bool: True se a tabela está correta ou foi corrigida com sucesso, False caso contrário
    """
    try:
        conexao, cursor = criar_conexao()
        
        # Verificar se a tabela existe
        cursor.execute('''
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='usuarios'
        ''')
        
        if not cursor.fetchone():
            depurar_logs("Tabela de usuários não existe, será criada pelo módulo database_config", "INFO")
            conexao.close()
            return True
            
        # Validar a estrutura dos usuários
        valido, correcoes = validar_estrutura_usuarios()
        
        conexao.close()
        
        if not valido and correcoes > 0:
            depurar_logs("Estrutura da tabela de usuários corrigida", "INFO")
            return True
        elif not valido and correcoes == 0:
            depurar_logs("Não foi possível corrigir todos os problemas na tabela de usuários", "WARNING")
            return False
        
        return True
        
    except Exception as e:
        depurar_logs(f"Erro ao verificar/corrigir tabela de usuários: {str(e)}", "ERROR")
        return False

def organizar_usuarios_por_tipo():
    """
    Verifica se os usuários estão organizados no banco de dados.
    Não há necessidade de reordenar fisicamente, mas adiciona um índice para consultas.
    
    Returns:
        bool: True se a operação foi bem-sucedida, False caso contrário
    """
    try:
        conexao, cursor = criar_conexao()
        
        # Verificar se já existe um índice para tipo de usuário
        cursor.execute('''
        SELECT name FROM sqlite_master 
        WHERE type='index' AND name='idx_usuarios_tipo'
        ''')
        
        if not cursor.fetchone():
            # Criar índice para tipo
            cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_usuarios_tipo ON usuarios(tipo)
            ''')
            
            depurar_logs("Índice criado para tipo de usuário", "INFO")
        
        conexao.commit()
        conexao.close()
        
        return True
    except Exception as e:
        depurar_logs(f"Erro ao organizar usuários por tipo: {str(e)}", "ERROR")
        return False

def verificar_e_organizar_usuarios():
    """
    Função principal para verificar, validar e organizar os usuários no banco de dados.
    Deve ser chamada pelo módulo auth_bd antes de trabalhar com os usuários.
    
    Returns:
        bool: True se os dados estão prontos para uso, False caso contrário
    """
    # Verifica e corrige a estrutura da tabela
    if not verificar_e_corrigir_banco():
        return False
        
    # Organiza os usuários (cria índices)
    return organizar_usuarios_por_tipo()