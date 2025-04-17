#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo de administração para o Sistema de Monitoramento de Preços
----------------------------------------------------------------
Fornece funcionalidades exclusivas para usuários administradores.
"""

import os
from utils import depurar_logs, limpar_tela
from auth import (
    listar_usuarios,
    adicionar_usuario,
    desativar_usuario,
    alterar_senha
)
from grupos import (
    listar_grupos,
    criar_grupo,
    remover_grupo,
    adicionar_cliente_grupo,
    remover_cliente_grupo,
    adicionar_usuario_grupo,
    remover_usuario_grupo,
    sincronizar_clientes
)
from database import listar_clientes

def exibir_cabecalho_admin():
    """Exibe o cabeçalho da área de administração."""
    print("\n" + "=" * 50)
    print("   ADMINISTRAÇÃO DO SISTEMA")
    print("=" * 50)

def menu_gerenciar_usuarios(usuario_admin):
    """
    Menu para gerenciamento de usuários (exclusivo para administradores).
    
    Args:
        usuario_admin (str): Nome do usuário administrador que está logado
    """
    while True:
        limpar_tela()
        exibir_cabecalho_admin()
        
        print("\nGERENCIAMENTO DE USUÁRIOS")
        print("1. Listar todos os usuários")
        print("2. Adicionar novo usuário")
        print("3. Desativar usuário")
        print("4. Alterar senha de usuário")
        print("0. Voltar ao menu principal")
        
        opcao = input("\nEscolha uma opção (0-4): ")
        
        if opcao == '1':
            # Lista todos os usuários do sistema
            print("\nLISTA DE USUÁRIOS")
            print("-" * 50)
            print(f"{'Username':<15} | {'Nome':<25} | {'Tipo':<10} | {'Status':<8}")
            print("-" * 50)
            
            mostrar_inativos = input("Mostrar usuários inativos? (s/n): ").lower() == 's'
            usuarios = listar_usuarios(mostrar_inativos)
            
            for user in usuarios:
                status = "Ativo" if user['ativo'] else "Inativo"
                print(f"{user['username']:<15} | {user['nome'][:25]:<25} | {user['tipo']:<10} | {status:<8}")
            
            input("\nPressione Enter para continuar...")
            
        elif opcao == '2':
            # Adiciona um novo usuário
            print("\nADICIONAR NOVO USUÁRIO")
            print("-" * 50)
            
            username = input("Username: ")
            nome = input("Nome completo: ")
            senha = input("Senha: ")
            
            print("\nTipos de usuário:")
            print("1. Usuário regular (acesso limitado)")
            print("2. Administrador (acesso completo)")
            
            tipo_opcao = input("Escolha o tipo (1-2) [1]: ") or "1"
            tipo = "admin" if tipo_opcao == "2" else "usuario"
            
            resultado = adicionar_usuario(username, senha, nome, tipo, usuario_admin)
            
            if resultado:
                print(f"\nUsuário '{username}' adicionado com sucesso!")
                depurar_logs(f"Usuário '{username}' adicionado por {usuario_admin}", "INFO")
            else:
                print("\nFalha ao adicionar usuário. Verifique se o username já existe.")
            
            input("\nPressione Enter para continuar...")
            
        elif opcao == '3':
            # Desativa um usuário existente
            print("\nDESATIVAR USUÁRIO")
            print("-" * 50)
            
            # Lista usuários ativos para facilitar a escolha
            usuarios = listar_usuarios(False)  # Apenas usuários ativos
            
            print("\nUsuários ativos:")
            for i, user in enumerate(usuarios, 1):
                print(f"{i}. {user['username']} ({user['nome']}) - {user['tipo']}")
            
            try:
                escolha = int(input("\nDigite o número do usuário que deseja desativar (0 para cancelar): "))
                
                if escolha == 0:
                    continue
                    
                if 1 <= escolha <= len(usuarios):
                    usuario_escolhido = usuarios[escolha-1]['username']
                    
                    # Impede que o admin desative a si mesmo
                    if usuario_escolhido == usuario_admin:
                        print("\nVocê não pode desativar seu próprio usuário!")
                        input("\nPressione Enter para continuar...")
                        continue
                    
                    # Confirma a desativação
                    confirmacao = input(f"Tem certeza que deseja desativar '{usuario_escolhido}'? (s/n): ")
                    
                    if confirmacao.lower() == 's':
                        resultado = desativar_usuario(usuario_escolhido, usuario_admin)
                        
                        if resultado:
                            print(f"\nUsuário '{usuario_escolhido}' desativado com sucesso!")
                            depurar_logs(f"Usuário '{usuario_escolhido}' desativado por {usuario_admin}", "INFO")
                        else:
                            print("\nFalha ao desativar usuário. Verifique se não é o último administrador.")
                else:
                    print("\nOpção inválida.")
            except ValueError:
                print("\nEntrada inválida. Digite um número.")
            
            input("\nPressione Enter para continuar...")
            
        elif opcao == '4':
            # Altera a senha de um usuário (funcionalidade administrativa)
            print("\nALTERAR SENHA DE USUÁRIO")
            print("-" * 50)
            
            # Lista todos os usuários para facilitar a escolha
            usuarios = listar_usuarios(True)  # Inclui usuários inativos
            
            print("\nUsuários:")
            for i, user in enumerate(usuarios, 1):
                status = "Ativo" if user['ativo'] else "Inativo"
                print(f"{i}. {user['username']} ({user['nome']}) - {status}")
            
            try:
                escolha = int(input("\nDigite o número do usuário para alterar a senha (0 para cancelar): "))
                
                if escolha == 0:
                    continue
                    
                if 1 <= escolha <= len(usuarios):
                    usuario_escolhido = usuarios[escolha-1]['username']
                    
                    # Administrador pode alterar senha de qualquer usuário sem conhecer a senha atual
                    # Isso é uma funcionalidade administrativa para redefinir senhas
                    nova_senha = input("Digite a nova senha: ")
                    confirma_senha = input("Confirme a nova senha: ")
                    
                    if nova_senha == confirma_senha:
                        # Implementar a funcionalidade de alteração de senha administrativa
                        # Esta funcionalidade precisaria ser adicionada ao módulo de autenticação
                        print("\nFuncionalidade em implementação.")
                        depurar_logs(f"Tentativa de alteração de senha administrativa por {usuario_admin}", "INFO")
                    else:
                        print("\nAs senhas não coincidem!")
                else:
                    print("\nOpção inválida.")
            except ValueError:
                print("\nEntrada inválida. Digite um número.")
            
            input("\nPressione Enter para continuar...")
            
        elif opcao == '0':
            return
        else:
            print("\nOpção inválida. Tente novamente.")
            input("\nPressione Enter para continuar...")

def menu_gerenciar_grupos(usuario_admin):
    """
    Menu para gerenciamento de grupos (exclusivo para administradores).
    
    Args:
        usuario_admin (str): Nome do usuário administrador que está logado
    """
    while True:
        limpar_tela()
        exibir_cabecalho_admin()
        
        print("\nGERENCIAMENTO DE GRUPOS")
        print("1. Listar todos os grupos")
        print("2. Criar novo grupo")
        print("3. Remover grupo")
        print("4. Gerenciar clientes de um grupo")
        print("5. Gerenciar usuários de um grupo")
        print("6. Sincronizar grupo 'Todos'")
        print("0. Voltar ao menu anterior")
        
        opcao = input("\nEscolha uma opção (0-6): ")
        
        if opcao == '1':
            # Lista todos os grupos
            grupos = listar_grupos(True)
            
            print("\nGRUPOS CADASTRADOS:")
            print("-" * 60)
            
            for id_grupo, dados in grupos.items():
                print(f"ID: {id_grupo}")
                print(f"Nome: {dados['nome']}")
                print(f"Descrição: {dados['descricao']}")
                print(f"Clientes: {', '.join(dados['clientes']) if dados['clientes'] else 'Nenhum'}")
                print(f"Usuários: {', '.join(dados['usuarios']) if dados['usuarios'] else 'Nenhum'}")
                print("-" * 60)
            
            input("\nPressione Enter para continuar...")
            
        elif opcao == '2':
            # Cria um novo grupo
            print("\nCRIAR NOVO GRUPO")
            print("-" * 40)
            
            id_grupo = input("ID do grupo (apenas letras, números e underscores): ")
            
            # Valida o ID do grupo
            import re
            if not re.match(r'^[a-zA-Z0-9_]+$', id_grupo):
                print("ID inválido. Use apenas letras, números e underscores.")
                input("\nPressione Enter para continuar...")
                continue
                
            nome = input("Nome do grupo: ")
            descricao = input("Descrição do grupo: ")
            
            resultado = criar_grupo(id_grupo, nome, descricao, usuario_admin)
            
            if resultado:
                print(f"\nGrupo '{nome}' criado com sucesso!")
                
                # Perguntar se deseja adicionar clientes ao grupo
                adicionar_clientes = input("Deseja adicionar clientes ao grupo agora? (s/n): ")
                if adicionar_clientes.lower() == 's':
                    gerenciar_clientes_grupo(id_grupo, usuario_admin)
                    
                # Perguntar se deseja adicionar usuários ao grupo
                adicionar_usuarios = input("Deseja adicionar usuários ao grupo agora? (s/n): ")
                if adicionar_usuarios.lower() == 's':
                    gerenciar_usuarios_grupo(id_grupo, usuario_admin)
            else:
                print("\nFalha ao criar grupo. Verifique se o ID já existe.")
                
            input("\nPressione Enter para continuar...")
            
        elif opcao == '3':
            # Remove um grupo existente
            print("\nREMOVER GRUPO")
            print("-" * 40)
            
            # Lista os grupos para escolha
            grupos = listar_grupos()
            
            print("\nGrupos disponíveis:")
            for i, (id_grupo, dados) in enumerate(grupos.items(), 1):
                print(f"{i}. {dados['nome']} (ID: {id_grupo})")
            
            try:
                escolha = int(input("\nDigite o número do grupo que deseja remover (0 para cancelar): "))
                
                if escolha == 0:
                    continue
                    
                if 1 <= escolha <= len(grupos):
                    id_grupo = list(grupos.keys())[escolha-1]
                    
                    # Impede a remoção do grupo "all"
                    if id_grupo == "all":
                        print("\nO grupo 'Todos' (all) não pode ser removido!")
                        input("\nPressione Enter para continuar...")
                        continue
                    
                    # Confirma a remoção
                    confirmacao = input(f"Tem certeza que deseja remover o grupo '{grupos[id_grupo]['nome']}'? (s/n): ")
                    
                    if confirmacao.lower() == 's':
                        resultado = remover_grupo(id_grupo, usuario_admin)
                        
                        if resultado:
                            print(f"\nGrupo '{grupos[id_grupo]['nome']}' removido com sucesso!")
                        else:
                            print("\nFalha ao remover grupo.")
                else:
                    print("\nOpção inválida.")
            except ValueError:
                print("\nEntrada inválida. Digite um número.")
            
            input("\nPressione Enter para continuar...")
            
        elif opcao == '4':
            # Gerencia clientes de um grupo
            print("\nGERENCIAR CLIENTES DE UM GRUPO")
            print("-" * 40)
            
            # Lista os grupos para escolha
            grupos = listar_grupos()
            
            print("\nGrupos disponíveis:")
            for i, (id_grupo, dados) in enumerate(grupos.items(), 1):
                print(f"{i}. {dados['nome']} (ID: {id_grupo})")
            
            try:
                escolha = int(input("\nDigite o número do grupo para gerenciar clientes (0 para cancelar): "))
                
                if escolha == 0:
                    continue
                    
                if 1 <= escolha <= len(grupos):
                    id_grupo = list(grupos.keys())[escolha-1]
                    gerenciar_clientes_grupo(id_grupo, usuario_admin)
                else:
                    print("\nOpção inválida.")
            except ValueError:
                print("\nEntrada inválida. Digite um número.")
            
            input("\nPressione Enter para continuar...")
            
        elif opcao == '5':
            # Gerencia usuários de um grupo
            print("\nGERENCIAR USUÁRIOS DE UM GRUPO")
            print("-" * 40)
            
            # Lista os grupos para escolha
            grupos = listar_grupos()
            
            print("\nGrupos disponíveis:")
            for i, (id_grupo, dados) in enumerate(grupos.items(), 1):
                print(f"{i}. {dados['nome']} (ID: {id_grupo})")
            
            try:
                escolha = int(input("\nDigite o número do grupo para gerenciar usuários (0 para cancelar): "))
                
                if escolha == 0:
                    continue
                    
                if 1 <= escolha <= len(grupos):
                    id_grupo = list(grupos.keys())[escolha-1]
                    gerenciar_usuarios_grupo(id_grupo, usuario_admin)
                else:
                    print("\nOpção inválida.")
            except ValueError:
                print("\nEntrada inválida. Digite um número.")
            
            input("\nPressione Enter para continuar...")
            
        elif opcao == '6':
            # Sincroniza o grupo "all" com todos os clientes atuais
            print("\nSINCRONIZANDO GRUPO 'TODOS'...")
            
            # Obtém a lista completa de clientes
            todos_clientes = []
            try:
                import pandas as pd
                if os.path.isfile('produtos_monitorados.csv'):
                    df_produtos = pd.read_csv('produtos_monitorados.csv')
                    todos_clientes = df_produtos['cliente'].unique().tolist()
            except Exception as e:
                print(f"Erro ao ler clientes: {str(e)}")
            
            resultado = sincronizar_clientes(todos_clientes)
            
            if resultado:
                print(f"Grupo 'Todos' sincronizado com sucesso! ({len(todos_clientes)} clientes)")
            else:
                print("Falha ao sincronizar grupo 'Todos'.")
            
            input("\nPressione Enter para continuar...")
            
        elif opcao == '0':
            return
            
        else:
            print("\nOpção inválida. Tente novamente.")
            input("\nPressione Enter para continuar...")

def gerenciar_clientes_grupo(id_grupo, usuario_admin):
    """
    Interface para gerenciar os clientes de um grupo específico.
    
    Args:
        id_grupo (str): ID do grupo a ser gerenciado
        usuario_admin (str): Nome do usuário administrador que está logado
    """
    grupos = listar_grupos()
    
    # Verifica se o grupo existe
    if id_grupo not in grupos:
        print(f"\nGrupo com ID '{id_grupo}' não encontrado.")
        return
    
    nome_grupo = grupos[id_grupo]['nome']
    
    while True:
        limpar_tela()
        print(f"\nGERENCIAR CLIENTES DO GRUPO: {nome_grupo} ({id_grupo})")
        print("-" * 60)
        
        # Mostra os clientes atuais do grupo
        clientes_grupo = grupos[id_grupo]['clientes']
        
        print("\nClientes atuais do grupo:")
        if clientes_grupo:
            for i, cliente in enumerate(clientes_grupo, 1):
                print(f"{i}. {cliente}")
        else:
            print("Nenhum cliente associado a este grupo")
        
        print("\nOPÇÕES:")
        print("1. Adicionar cliente ao grupo")
        print("2. Remover cliente do grupo")
        print("0. Voltar ao menu anterior")
        
        opcao = input("\nEscolha uma opção (0-2): ")
        
        if opcao == '1':
            # Adiciona um cliente ao grupo
            print("\nADICIONAR CLIENTE AO GRUPO")
            
            # Obtém lista completa de clientes do sistema
            try:
                import pandas as pd
                if os.path.isfile('produtos_monitorados.csv'):
                    df_produtos = pd.read_csv('produtos_monitorados.csv')
                    todos_clientes = df_produtos['cliente'].unique().tolist()
                    
                    # Filtra para mostrar apenas clientes que não estão no grupo
                    clientes_disponiveis = [c for c in todos_clientes if c not in clientes_grupo]
                    
                    if not clientes_disponiveis:
                        print("Todos os clientes já estão associados a este grupo.")
                        input("\nPressione Enter para continuar...")
                        continue
                    
                    print("\nClientes disponíveis:")
                    for i, cliente in enumerate(clientes_disponiveis, 1):
                        print(f"{i}. {cliente}")
                    
                    try:
                        escolha = int(input("\nDigite o número do cliente que deseja adicionar (0 para cancelar): "))
                        
                        if escolha == 0:
                            continue
                            
                        if 1 <= escolha <= len(clientes_disponiveis):
                            cliente_escolhido = clientes_disponiveis[escolha-1]
                            
                            resultado = adicionar_cliente_grupo(id_grupo, cliente_escolhido, usuario_admin)
                            
                            if resultado:
                                print(f"\nCliente '{cliente_escolhido}' adicionado ao grupo com sucesso!")
                                # Atualiza os dados do grupo
                                grupos = listar_grupos()
                                clientes_grupo = grupos[id_grupo]['clientes']
                            else:
                                print("\nFalha ao adicionar cliente ao grupo.")
                        else:
                            print("\nOpção inválida.")
                    except ValueError:
                        print("\nEntrada inválida. Digite um número.")
                else:
                    print("Nenhum cliente cadastrado no sistema.")
            except Exception as e:
                print(f"Erro ao processar clientes: {str(e)}")
            
            input("\nPressione Enter para continuar...")
            
        elif opcao == '2':
            # Remove um cliente do grupo
            print("\nREMOVER CLIENTE DO GRUPO")
            
            if not clientes_grupo:
                print("Não há clientes para remover deste grupo.")
                input("\nPressione Enter para continuar...")
                continue
            
            print("\nClientes no grupo:")
            for i, cliente in enumerate(clientes_grupo, 1):
                print(f"{i}. {cliente}")
            
            try:
                escolha = int(input("\nDigite o número do cliente que deseja remover (0 para cancelar): "))
                
                if escolha == 0:
                    continue
                    
                if 1 <= escolha <= len(clientes_grupo):
                    cliente_escolhido = clientes_grupo[escolha-1]
                    
                    resultado = remover_cliente_grupo(id_grupo, cliente_escolhido, usuario_admin)
                    
                    if resultado:
                        print(f"\nCliente '{cliente_escolhido}' removido do grupo com sucesso!")
                        # Atualiza os dados do grupo
                        grupos = listar_grupos()
                        clientes_grupo = grupos[id_grupo]['clientes']
                    else:
                        print("\nFalha ao remover cliente do grupo.")
                else:
                    print("\nOpção inválida.")
            except ValueError:
                print("\nEntrada inválida. Digite um número.")
            
            input("\nPressione Enter para continuar...")
            
        elif opcao == '0':
            return
            
        else:
            print("\nOpção inválida. Tente novamente.")
            input("\nPressione Enter para continuar...")

def gerenciar_usuarios_grupo(id_grupo, usuario_admin):
    """
    Interface para gerenciar os usuários de um grupo específico.
    
    Args:
        id_grupo (str): ID do grupo a ser gerenciado
        usuario_admin (str): Nome do usuário administrador que está logado
    """
    grupos = listar_grupos()
    
    # Verifica se o grupo existe
    if id_grupo not in grupos:
        print(f"\nGrupo com ID '{id_grupo}' não encontrado.")
        return
    
    nome_grupo = grupos[id_grupo]['nome']
    
    while True:
        limpar_tela()
        print(f"\nGERENCIAR USUÁRIOS DO GRUPO: {nome_grupo} ({id_grupo})")
        print("-" * 60)
        
        # Mostra os usuários atuais do grupo
        usuarios_grupo = grupos[id_grupo]['usuarios']
        
        print("\nUsuários atuais do grupo:")
        if usuarios_grupo:
            for i, usuario in enumerate(usuarios_grupo, 1):
                print(f"{i}. {usuario}")
        else:
            print("Nenhum usuário associado a este grupo")
        
        print("\nOPÇÕES:")
        print("1. Adicionar usuário ao grupo")
        print("2. Remover usuário do grupo")
        print("0. Voltar ao menu anterior")
        
        opcao = input("\nEscolha uma opção (0-2): ")
        
        if opcao == '1':
            # Adiciona um usuário ao grupo
            print("\nADICIONAR USUÁRIO AO GRUPO")
            
            # Obtém lista completa de usuários do sistema
            lista_usuarios = listar_usuarios(True)  # Inclui inativos
            
            # Filtra para mostrar apenas usuários que não estão no grupo e estão ativos
            usuarios_disponiveis = [u['username'] for u in lista_usuarios 
                                   if u['username'] not in usuarios_grupo and u['ativo']]
            
            if not usuarios_disponiveis:
                print("Todos os usuários ativos já estão associados a este grupo.")
                input("\nPressione Enter para continuar...")
                continue
            
            print("\nUsuários disponíveis:")
            for i, username in enumerate(usuarios_disponiveis, 1):
                # Encontra o nome completo do usuário
                nome_completo = next((u['nome'] for u in lista_usuarios if u['username'] == username), "")
                print(f"{i}. {username} ({nome_completo})")
            
            try:
                escolha = int(input("\nDigite o número do usuário que deseja adicionar (0 para cancelar): "))
                
                if escolha == 0:
                    continue
                    
                if 1 <= escolha <= len(usuarios_disponiveis):
                    usuario_escolhido = usuarios_disponiveis[escolha-1]
                    
                    resultado = adicionar_usuario_grupo(id_grupo, usuario_escolhido, usuario_admin)
                    
                    if resultado:
                        print(f"\nUsuário '{usuario_escolhido}' adicionado ao grupo com sucesso!")
                        # Atualiza os dados do grupo
                        grupos = listar_grupos()
                        usuarios_grupo = grupos[id_grupo]['usuarios']
                    else:
                        print("\nFalha ao adicionar usuário ao grupo.")
                else:
                    print("\nOpção inválida.")
            except ValueError:
                print("\nEntrada inválida. Digite um número.")
            
            input("\nPressione Enter para continuar...")
            
        elif opcao == '2':
            # Remove um usuário do grupo
            print("\nREMOVER USUÁRIO DO GRUPO")
            
            if not usuarios_grupo:
                print("Não há usuários para remover deste grupo.")
                input("\nPressione Enter para continuar...")
                continue
            
            print("\nUsuários no grupo:")
            for i, usuario in enumerate(usuarios_grupo, 1):
                print(f"{i}. {usuario}")
            
            try:
                escolha = int(input("\nDigite o número do usuário que deseja remover (0 para cancelar): "))
                
                if escolha == 0:
                    continue
                    
                if 1 <= escolha <= len(usuarios_grupo):
                    usuario_escolhido = usuarios_grupo[escolha-1]
                    
                    # Impedir a remoção do admin do grupo "all"
                    if id_grupo == "all" and usuario_escolhido == "admin":
                        print("\nO usuário 'admin' não pode ser removido do grupo 'Todos'.")
                        input("\nPressione Enter para continuar...")
                        continue
                    
                    resultado = remover_usuario_grupo(id_grupo, usuario_escolhido, usuario_admin)
                    
                    if resultado:
                        print(f"\nUsuário '{usuario_escolhido}' removido do grupo com sucesso!")
                        # Atualiza os dados do grupo
                        grupos = listar_grupos()
                        usuarios_grupo = grupos[id_grupo]['usuarios']
                    else:
                        print("\nFalha ao remover usuário do grupo.")
                else:
                    print("\nOpção inválida.")
            except ValueError:
                print("\nEntrada inválida. Digite um número.")
            
            input("\nPressione Enter para continuar...")
            
        elif opcao == '0':
            return
            
        else:
            print("\nOpção inválida. Tente novamente.")
            input("\nPressione Enter para continuar...")

def relatorio_atividade_sistema():
    """
    Gera um relatório de atividade do sistema baseado nos logs.
    Esta função é exclusiva para administradores.
    """
    try:
        from datetime import datetime, timedelta
        
        print("\nRELATÓRIO DE ATIVIDADE DO SISTEMA")
        print("-" * 50)
        
        if not os.path.isfile('monitor_precos.log'):
            print("Arquivo de log não encontrado.")
            return
        
        # Solicita o período para o relatório
        print("\nPeríodo do relatório:")
        print("1. Últimas 24 horas")
        print("2. Últimos 7 dias")
        print("3. Últimos 30 dias")
        print("4. Todo o histórico")
        
        opcao = input("\nEscolha uma opção (1-4): ")
        
        # Determina a data de corte baseada na opção
        data_atual = datetime.now()
        data_corte = None
        
        if opcao == '1':
            data_corte = data_atual - timedelta(days=1)
            periodo = "Últimas 24 horas"
        elif opcao == '2':
            data_corte = data_atual - timedelta(days=7)
            periodo = "Últimos 7 dias"
        elif opcao == '3':
            data_corte = data_atual - timedelta(days=30)
            periodo = "Últimos 30 dias"
        elif opcao == '4':
            data_corte = datetime(1970, 1, 1)  # Data bem antiga para incluir tudo
            periodo = "Todo o histórico"
        else:
            print("\nOpção inválida. Usando últimas 24 horas.")
            data_corte = data_atual - timedelta(days=1)
            periodo = "Últimas 24 horas"
        
        # Carrega o arquivo de log
        with open('monitor_precos.log', 'r', encoding='utf-8') as f:
            linhas_log = f.readlines()
        
        # Filtra as linhas por data
        logs_filtrados = []
        
        for linha in linhas_log:
            try:
                # Formato esperado: [YYYY-MM-DD HH:MM:SS] [NIVEL] mensagem
                partes = linha.split('] [')
                if len(partes) >= 2:
                    data_str = partes[0].strip('[')
                    data_log = datetime.strptime(data_str, '%Y-%m-%d %H:%M:%S')
                    
                    if data_log >= data_corte:
                        logs_filtrados.append(linha)
            except:
                continue
        
        # Análise dos logs
        total_logs = len(logs_filtrados)
        logs_por_nivel = {"INFO": 0, "WARNING": 0, "ERROR": 0, "DEBUG": 0}
        acoes_login = []
        acoes_monitoramento = []
        
        for linha in logs_filtrados:
            # Conta logs por nível
            for nivel in logs_por_nivel.keys():
                if f"[{nivel}]" in linha:
                    logs_por_nivel[nivel] += 1
            
            # Identifica logins
            if "login" in linha.lower():
                acoes_login.append(linha)
            
            # Identifica monitoramentos
            if "monitoramento" in linha.lower():
                acoes_monitoramento.append(linha)
            
            # Você pode adicionar mais categorias conforme necessário
        
        # Exibe o relatório
        print(f"\nRelatório de atividade - {periodo}")
        print(f"Total de eventos: {total_logs}")
        print("\nDistribuição por nível:")
        for nivel, quantidade in logs_por_nivel.items():
            print(f"- {nivel}: {quantidade}")
        
        print(f"\nLogins ({len(acoes_login)}):")
        for i, log in enumerate(acoes_login[:5], 1):  # Mostra apenas os 5 mais recentes
            print(f"{i}. {log.strip()}")
        
        if len(acoes_login) > 5:
            print(f"... e mais {len(acoes_login) - 5} registro(s) de login.")
        
        print(f"\nMonitoramentos ({len(acoes_monitoramento)}):")
        for i, log in enumerate(acoes_monitoramento[:5], 1):  # Mostra apenas os 5 mais recentes
            print(f"{i}. {log.strip()}")
        
        if len(acoes_monitoramento) > 5:
            print(f"... e mais {len(acoes_monitoramento) - 5} registro(s) de monitoramento.")
        
    except Exception as e:
        print(f"\nErro ao gerar relatório: {str(e)}")
    
    input("\nPressione Enter para continuar...")

def menu_administracao(usuario_admin):
    """
    Menu principal de administração do sistema.
    
    Args:
        usuario_admin (str): Nome do usuário administrador que está logado
    """
    while True:
        limpar_tela()
        exibir_cabecalho_admin()
        
        print(f"\nAdministrador: {usuario_admin}")
        print("\nMENU ADMINISTRATIVO")
        print("1. Gerenciar usuários")
        print("2. Gerenciar grupos")
        print("3. Relatório de atividade do sistema")
        print("4. Criar backup completo")
        print("0. Voltar ao menu principal")
        
        opcao = input("\nEscolha uma opção (0-4): ")
        
        if opcao == '1':
            menu_gerenciar_usuarios(usuario_admin)
            
        elif opcao == '2':
            menu_gerenciar_grupos(usuario_admin)
            
        elif opcao == '3':
            relatorio_atividade_sistema()
            
        elif opcao == '4':
            from utils import criar_backup
            print("\nCriando backup completo do sistema...")
            resultado = criar_backup()
            
            if resultado:
                print("Backup criado com sucesso!")
            else:
                print("Houve um erro ao criar o backup.")
                
            input("\nPressione Enter para continuar...")
            
        elif opcao == '0':
            return
            
        else:
            print("\nOpção inválida. Tente novamente.")
            input("\nPressione Enter para continuar...")