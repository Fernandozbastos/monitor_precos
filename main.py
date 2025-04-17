#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Sistema de Monitoramento de Preços
----------------------------------
Este programa monitora preços de produtos em sites de concorrentes
e registra o histórico de variações para análise competitiva.
"""

import os
import sys
import time
from utils import verificar_arquivos_sistema, depurar_logs, criar_backup, limpar_tela
from database import (
    adicionar_produto,
    remover_produto,
    listar_dominios_seletores,
    remover_dominio_seletor,
    listar_clientes,
    visualizar_historico
)
from scheduler import (
    monitorar_todos_produtos,
    configurar_agendamento,
    executar_agendador,
    restaurar_agendamento,
    carregar_configuracao_agendamento
)
from auth import (
    realizar_login,
    verificar_arquivo_usuarios,
    adicionar_usuario,
    alterar_senha,
    desativar_usuario,
    listar_usuarios,
    alterar_cliente_atual,
    obter_cliente_atual
)
from grupos import (
    verificar_arquivo_grupos,
    obter_grupos_usuario,
    obter_clientes_usuario,
    adicionar_cliente_grupo_usuario,
    adicionar_cliente_a_todos_grupos_admin
)

from admin import menu_administracao

# Versão do programa
__version__ = '1.0.0'

# Variáveis globais para controle de sessão
usuario_logado = None
tipo_usuario = None
cliente_atual = None

def exibir_cabecalho():
    """Exibe o cabeçalho do programa com informações de versão."""
    print("\n" + "=" * 50)
    print(f"   SISTEMA DE MONITORAMENTO DE PREÇOS v{__version__}")
    print("=" * 50)
    print("Desenvolvido por: Sua Empresa")
    if usuario_logado:
        grupos = obter_grupos_usuario(usuario_logado)
        grupos_str = ", ".join(grupos) if grupos else "Nenhum"
        print(f"Usuário: {usuario_logado} ({tipo_usuario})")
        print(f"Grupos: {grupos_str}")
        if cliente_atual:
            print(f"Cliente atual: {cliente_atual}")
        else:
            print("Cliente atual: Nenhum selecionado")
    print("-" * 50)

def exibir_menu_principal():
    """Exibe o menu principal de opções do sistema."""
    print("\nMENU PRINCIPAL")
    print("1. Produtos")
    print("2. Administração")
    print("3. Selecionar Cliente")
    
    print("S. Alterar senha")
    print("L. Logout")
    print("0. Sair")

def menu_gerenciar_produtos():
    """Submenu para gerenciamento de produtos."""
    global cliente_atual
    
    # Verifica se um cliente está selecionado
    if not cliente_atual:
        print("\nNenhum cliente selecionado. Por favor, selecione um cliente primeiro.")
        if not selecionar_cliente():
            return  # Volta ao menu principal se não conseguir selecionar um cliente
    
    while True:
        limpar_tela()
        exibir_cabecalho()
        
        print(f"\nGERENCIAMENTO DE PRODUTOS - Cliente: {cliente_atual}")
        print("1. Adicionar novo produto")
        print("2. Remover produto monitorado")
        print("3. Visualizar histórico de preços")
        print("0. Voltar ao menu principal")
        
        opcao = input("\nEscolha uma opção (0-3): ")
        
        if opcao == '1':
            # Adiciona produto para o cliente atual
            adicionar_produto(cliente=cliente_atual, usuario_atual=usuario_logado)
            
            # Se o usuário não for admin, adiciona o cliente ao grupo do usuário
            if tipo_usuario != 'admin':
                adicionar_cliente_grupo_usuario(usuario_logado, cliente_atual, usuario_logado)
                
            input("\nPressione Enter para continuar...")
            
        elif opcao == '2':
            remover_produto(usuario_atual=usuario_logado)
            input("\nPressione Enter para continuar...")
            
        elif opcao == '3':
            # Passa o cliente atual para filtrar automaticamente o histórico
            visualizar_historico(usuario_atual=usuario_logado, cliente_filtro=cliente_atual)
            input("\nPressione Enter para continuar...")
            
        elif opcao == '0':
            return
            
        else:
            print("Opção inválida. Tente novamente.")
            input("\nPressione Enter para continuar...")

def selecionar_cliente():
    """
    Interface para o usuário selecionar um cliente para trabalhar.
    Filtra os clientes com base nos grupos do usuário.
    
    Returns:
        bool: True se um cliente foi selecionado com sucesso, False caso contrário
    """
    global cliente_atual
    
    limpar_tela()
    exibir_cabecalho()
    
    print("\nSELEÇÃO DE CLIENTE")
    print("-" * 40)
    
    # Lista de todos os clientes no sistema
    todos_clientes = []
    
    try:
        import pandas as pd
        
        # Primeiro busca no arquivo de clientes
        if os.path.isfile('clientes.csv'):
            df_clientes = pd.read_csv('clientes.csv')
            todos_clientes.extend(df_clientes['cliente'].unique().tolist())
        
        # Complementa com clientes do arquivo de produtos (caso falte algum)
        if os.path.isfile('produtos_monitorados.csv'):
            df_produtos = pd.read_csv('produtos_monitorados.csv')
            todos_clientes.extend(df_produtos['cliente'].unique().tolist())
        
        # Remove duplicatas
        todos_clientes = list(set(todos_clientes))
    except Exception as e:
        print(f"Erro ao carregar clientes: {str(e)}")
    
    # Determina quais clientes o usuário pode acessar
    if tipo_usuario == 'admin' or "admin" in obter_grupos_usuario(usuario_logado):
        # Administradores podem ver todos os clientes
        clientes_disponiveis = todos_clientes
    else:
        # Usuários comuns veem apenas os clientes de seus grupos
        clientes_autorizados = obter_clientes_usuario(usuario_logado)
        clientes_disponiveis = [c for c in todos_clientes if c in clientes_autorizados]
    
    # Adicionar opção para criar novo cliente
    tem_opcoes = False
    
    if clientes_disponiveis:
        tem_opcoes = True
        print("\nClientes disponíveis:")
        for i, cliente in enumerate(clientes_disponiveis, 1):
            print(f"{i}. {cliente}")
    else:
        print("\nNenhum cliente disponível para seleção.")
    
    print(f"{len(clientes_disponiveis) + 1}. Criar novo cliente")
    print("0. Voltar ao menu principal")
    
    opcao = input("\nSelecione um cliente (0 para cancelar): ")
    
    if opcao == '0':
        return False
    
    try:
        escolha = int(opcao)
        
        if tem_opcoes and 1 <= escolha <= len(clientes_disponiveis):
            # Selecionou um cliente existente
            cliente_selecionado = clientes_disponiveis[escolha - 1]
            
            # Atualiza o cliente atual no sistema
            cliente_atual = cliente_selecionado
            alterar_cliente_atual(usuario_logado, cliente_atual)
            
            print(f"\nCliente '{cliente_atual}' selecionado com sucesso!")
            input("\nPressione Enter para continuar...")
            return True
        
        elif escolha == len(clientes_disponiveis) + 1:
            # Criar novo cliente
            novo_cliente = input("\nDigite o nome do novo cliente: ")
            
            if not novo_cliente:
                print("Nome de cliente inválido.")
                input("\nPressione Enter para tentar novamente...")
                return selecionar_cliente()
            
            # Verifica se o cliente já existe no sistema
            if novo_cliente in todos_clientes:
                # Se o cliente já existe, mas o usuário não tem acesso
                if novo_cliente not in clientes_disponiveis and tipo_usuario != 'admin' and "admin" not in obter_grupos_usuario(usuario_logado):
                    print(f"\nO cliente '{novo_cliente}' já existe, mas você não tem acesso a ele.")
                    print("Apenas administradores podem adicionar acesso a clientes existentes.")
                    input("\nPressione Enter para tentar novamente...")
                    return selecionar_cliente()
            
            # Adiciona o cliente ao sistema
            from database import adicionar_cliente
            sucesso = adicionar_cliente(novo_cliente, usuario_atual=usuario_logado)
            
            if sucesso:
                # Atualiza o cliente atual no sistema
                cliente_atual = novo_cliente
                alterar_cliente_atual(usuario_logado, cliente_atual)
                
                print(f"\nNovo cliente '{cliente_atual}' criado e selecionado!")
                input("\nPressione Enter para continuar...")
                return True
            else:
                print("Falha ao criar novo cliente.")
                input("\nPressione Enter para tentar novamente...")
                return selecionar_cliente()
        
        else:
            print("Opção inválida.")
            input("\nPressione Enter para tentar novamente...")
            return selecionar_cliente()
            
    except ValueError:
        print("Entrada inválida. Digite um número.")
        input("\nPressione Enter para tentar novamente...")
        return selecionar_cliente()

def menu_administracao_sistema():
    """
    Menu de administração do sistema.
    Controla o acesso às funcionalidades com base no tipo de usuário.
    """
    while True:
        limpar_tela()
        exibir_cabecalho()
        
        print("\nADMINISTRAÇÃO DO SISTEMA")
        
        # Opções disponíveis para todos os usuários
        print("1. Executar monitoramento agora")
        
        # Opções disponíveis apenas para administradores
        if tipo_usuario == 'admin':
            print("2. Configurar monitoramento automático")
            print("3. Iniciar agendador")
            print("4. Gerenciar domínios e seletores")
            print("5. Criar backup do sistema")
            print("6. Painel de administração")
        
        print("0. Voltar ao menu principal")
        
        opcao = input("\nEscolha uma opção: ")
        
        if opcao == '1':
            # Disponível para todos
            print("\nExecutando monitoramento de todos os produtos...")
            resultado = monitorar_todos_produtos(usuario_atual=usuario_logado)
            if resultado:
                print("Monitoramento concluído com sucesso!")
            else:
                print("Monitoramento concluído, mas com possíveis falhas.")
            input("\nPressione Enter para continuar...")
            
        elif opcao == '2' and tipo_usuario == 'admin':
            # Apenas admin
            info_agendamento, sucesso = configurar_agendamento()
            if sucesso and info_agendamento:
                from scheduler import salvar_configuracao_agendamento
                salvar_configuracao_agendamento(info_agendamento)
            input("\nPressione Enter para continuar...")
            
        elif opcao == '3' and tipo_usuario == 'admin':
            # Apenas admin
            print("\nO agendador será iniciado. O sistema ficará em execução.")
            print("Para encerrar o agendador, pressione Ctrl+C a qualquer momento.")
            input("Pressione Enter para iniciar o agendador...")
            executar_agendador()
            
        elif opcao == '4' and tipo_usuario == 'admin':
            # Apenas admin
            menu_gerenciar_dominios()
            
        elif opcao == '5' and tipo_usuario == 'admin':
            # Apenas admin
            print("\nCriando backup do sistema...")
            resultado = criar_backup()
            if resultado:
                print("Backup criado com sucesso!")
            else:
                print("Houve um erro ao criar o backup.")
            input("\nPressione Enter para continuar...")
            
        elif opcao == '6' and tipo_usuario == 'admin':
            # Apenas admin - acesso ao painel completo de administração
            menu_administracao(usuario_logado)
            
        elif opcao == '0':
            return
            
        else:
            print("Opção inválida ou sem permissão. Tente novamente.")
            input("\nPressione Enter para continuar...")

def menu_gerenciar_dominios():
    """Submenu para gerenciamento de domínios, plataformas e seletores."""
    while True:
        print("\nGERENCIAMENTO DE DOMÍNIOS, PLATAFORMAS E SELETORES")
        print("1. Listar domínios e seletores")
        print("2. Remover domínio e seletor")
        print("3. Listar plataformas e seletores")
        print("4. Remover plataforma e seletor")
        print("0. Voltar ao menu anterior")
        
        opcao = input("\nEscolha uma opção (0-4): ")
        
        if opcao == '1':
            listar_dominios_seletores()
            input("\nPressione Enter para continuar...")
        elif opcao == '2':
            remover_dominio_seletor()
            input("\nPressione Enter para continuar...")
        elif opcao == '3':
            listar_plataformas_seletores()
            input("\nPressione Enter para continuar...")
        elif opcao == '4':
            remover_plataforma_seletor()
            input("\nPressione Enter para continuar...")
        elif opcao == '0':
            return
        else:
            print("Opção inválida. Tente novamente.")
            input("\nPressione Enter para continuar...")

def alterar_senha_usuario():
    """Interface para o usuário alterar sua própria senha."""
    print("\nALTERAR SENHA")
    senha_atual = input("Senha atual: ")
    nova_senha = input("Nova senha: ")
    confirmacao = input("Confirme a nova senha: ")
    
    if nova_senha != confirmacao:
        print("As senhas não coincidem!")
        return
        
    resultado = alterar_senha(usuario_logado, senha_atual, nova_senha)
    if resultado:
        print("Senha alterada com sucesso!")
    else:
        print("Falha ao alterar senha. Verifique se a senha atual está correta.")

def iniciar_sistema():
    """
    Inicializa o sistema, verificando arquivos necessários,
    carregando configurações salvas e realizando migração se necessário.
    """
    print("Inicializando sistema...")
    
    # Verifica se os arquivos do sistema existem e cria se necessário
    status_arquivos = verificar_arquivos_sistema()
    for arquivo, status in status_arquivos.items():
        print(f"- {arquivo}: {status}")
    
    # Garante que o arquivo de usuários existe
    verificar_arquivo_usuarios()
    print("- usuarios.json: Verificado")
    
    # Garante que o arquivo de grupos existe
    verificar_arquivo_grupos()
    print("- grupos.json: Verificado")
    
    # Verifica se é necessário migrar para o novo formato de dados
    need_migration = False
    try:
        import pandas as pd
        if os.path.isfile('produtos_monitorados.csv'):
            # Verifica se o arquivo de produtos tem a coluna 'seletor_css'
            df = pd.read_csv('produtos_monitorados.csv')
            if 'seletor_css' in df.columns:
                need_migration = True
                
        # Se existir produtos_monitorados.csv mas não urls_monitoradas.csv, pode ser necessário migrar
        if os.path.isfile('produtos_monitorados.csv') and not os.path.isfile('urls_monitoradas.csv'):
            need_migration = True
            
        if need_migration:
            print("\nDetectado formato antigo de dados ou falta de arquivos necessários.")
            print("Iniciando migração para o novo formato...")
            from database import migrar_para_novo_formato
            success = migrar_para_novo_formato()
            
            if success:
                print("Migração concluída com sucesso!")
            else:
                print("Houve problemas durante a migração. Algumas funcionalidades podem não funcionar corretamente.")
    except Exception as e:
        print(f"Erro ao verificar necessidade de migração: {e}")
        print("Criando estrutura básica para evitar erros futuros...")
        try:
            # Garantir que o arquivo de URLs existe mesmo que vazio
            if not os.path.isfile('urls_monitoradas.csv'):
                import pandas as pd
                pd.DataFrame(columns=['url', 'dominio', 'seletor_css']).to_csv('urls_monitoradas.csv', index=False)
        except Exception as e2:
            print(f"Erro ao criar arquivo de URLs: {e2}")
    
    # Tenta restaurar agendamento anterior
    config = carregar_configuracao_agendamento()
    if config:
        print("\nEncontrada configuração de agendamento anterior:")
        tipo = config.get("tipo", "desconhecido")
        if tipo == "diario":
            print(f"- Monitoramento diário às {config.get('horario')}")
        elif tipo == "semanal":
            print(f"- Monitoramento semanal às {config.get('horario')} de {config.get('dia')}")
        elif tipo == "mensal":
            print(f"- Monitoramento mensal no dia {config.get('dia')} às {config.get('horario')}")
        
        restaurar = input("Deseja restaurar este agendamento? (s/n): ")
        if restaurar.lower() == 's':
            restaurar_agendamento()
    
    depurar_logs("Sistema inicializado com sucesso")

def fazer_login():
    """
    Solicita as credenciais do usuário e realiza o login.
    
    Returns:
        bool: True se o login foi bem-sucedido, False caso contrário
    """
    global usuario_logado, tipo_usuario, cliente_atual
    
    autenticado, username, tipo, ultimo_cliente = realizar_login()
    
    if autenticado:
        usuario_logado = username
        tipo_usuario = tipo
        cliente_atual = ultimo_cliente
        depurar_logs(f"Usuário {username} ({tipo}) fez login", "INFO")
        
        # Se tiver um cliente anterior, usa-o como cliente atual
        if cliente_atual:
            print(f"Cliente '{cliente_atual}' selecionado automaticamente.")
        
        return True
    else:
        return False

def fazer_logout():
    """Realiza o logout do usuário atual."""
    global usuario_logado, tipo_usuario, cliente_atual
    
    if usuario_logado:
        depurar_logs(f"Usuário {usuario_logado} fez logout", "INFO")
        usuario_logado = None
        tipo_usuario = None
        cliente_atual = None
        print("\nLogout realizado com sucesso!")
        return True
    return False

def menu_principal():
    """
    Exibe e processa o menu principal do sistema.
    Esta é a função principal que controla o fluxo do programa.
    """
    global usuario_logado, tipo_usuario, cliente_atual
    
    # Inicializa o sistema primeiro
    iniciar_sistema()
    
    # Solicita login antes de mostrar o menu principal
    if not fazer_login():
        print("\nNão foi possível realizar o login. O programa será encerrado.")
        sys.exit(1)
    
    while True:
        try:
            # Limpa a tela 
            limpar_tela()
                
            exibir_cabecalho()
            exibir_menu_principal()
            
            opcao = input("\nEscolha uma opção: ").upper()
            
            if opcao == '1':
                menu_gerenciar_produtos()
                
            elif opcao == '2':
                menu_administracao_sistema()
                
            elif opcao == '3':
                selecionar_cliente()
                
            elif opcao == 'S':
                alterar_senha_usuario()
                input("\nPressione Enter para continuar...")
                
            elif opcao == 'L':
                if fazer_logout():
                    # Após logout, solicita novo login
                    if not fazer_login():
                        print("\nNão foi possível realizar o login. O programa será encerrado.")
                        depurar_logs("Tentativa de login após logout falhou", "WARNING")
                        sys.exit(1)
                
            elif opcao == '0':
                print("\nSaindo do sistema. Até logo!")
                depurar_logs(f"Sistema encerrado pelo usuário {usuario_logado}", "INFO")
                sys.exit(0)
                
            else:
                print("Opção inválida. Tente novamente.")
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n\nOperação interrompida pelo usuário.")
            continuar = input("Deseja voltar ao menu principal? (s/n): ")
            if continuar.lower() != 's':
                print("\nSaindo do sistema. Até logo!")
                depurar_logs(f"Sistema encerrado pelo usuário {usuario_logado} (KeyboardInterrupt)", "INFO")
                sys.exit(0)
                
        except Exception as e:
            erro = f"Erro inesperado: {str(e)}"
            print(f"\n{erro}")
            depurar_logs(erro, "ERROR")
            input("\nPressione Enter para continuar...")

if __name__ == "__main__":
    try:
        menu_principal()
    except Exception as e:
        depurar_logs(f"Erro fatal: {str(e)}", "ERROR")
        print(f"\nErro fatal: {str(e)}")
        print("O programa será encerrado.")
        sys.exit(1)