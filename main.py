#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Sistema de Monitoramento de Preços
----------------------------------
Este programa monitora preços de produtos em sites de concorrentes
e registra o histórico de variações para análise competitiva.
Versão com menus otimizados para diferentes perfis de usuário.
"""

import os
import sys
import time
import traceback
from utils import depurar_logs, criar_backup, limpar_tela
from database_bd import (
    adicionar_produto,
    remover_produto,
    listar_dominios_seletores,
    remover_dominio_seletor,
    listar_plataformas_seletores,
    remover_plataforma_seletor,
    listar_clientes,
    visualizar_historico,
    adicionar_cliente,
    listar_produtos
)
from scheduler import (
    monitorar_todos_produtos,
    configurar_agendamento,
    executar_agendador,
    restaurar_agendamento,
    carregar_configuracao_agendamento,
    salvar_configuracao_agendamento
)
from auth_bd import (
    realizar_login,
    alterar_senha,
    alterar_cliente_atual,
    obter_cliente_atual,
    listar_usuarios
)
from grupos_bd import (
    obter_grupos_usuario,
    obter_clientes_usuario,
    usuario_pode_acessar_cliente,
    listar_grupos
)

from admin import menu_administracao

# Versão do programa
__version__ = '1.1.0'

# Variáveis globais para controle de sessão
usuario_logado = None
tipo_usuario = None
cliente_atual = None

#----------------------------------------------------------
# FUNÇÕES COMUNS E UTILITÁRIAS
#----------------------------------------------------------

def exibir_cabecalho():
    """Exibe o cabeçalho do programa com informações de versão."""
    print("\n" + "=" * 60)
    print(f"   SISTEMA DE MONITORAMENTO DE PREÇOS v{__version__}")
    print("=" * 60)
    print("Desenvolvido por: Bastin Marketing")
    if usuario_logado:
        grupos = obter_grupos_usuario(usuario_logado)
        grupos_str = ", ".join(grupos) if grupos else "Nenhum"
        print(f"Usuário: {usuario_logado} ({tipo_usuario})")
        
        if cliente_atual:
            print(f"Cliente atual: {cliente_atual}")
        else:
            print("Cliente atual: Nenhum selecionado")
    print("-" * 60)

def inicializar_banco_dados():
    """
    Inicializa o banco de dados SQLite.
    
    Returns:
        bool: True se a inicialização foi bem-sucedida, False caso contrário
    """
    try:
        from database_config import inicializar_banco_dados
        
        print("Inicializando banco de dados SQLite...")
        sucesso = inicializar_banco_dados()
        
        if sucesso:
            print("Banco de dados inicializado com sucesso!")
            
            # Verificar se é necessário migrar dados de arquivos CSV
            if os.path.isfile('produtos_monitorados.csv') and not os.path.isfile('migrado_para_bd.flag'):
                print("\nArquivos CSV encontrados. Deseja migrar os dados para o banco de dados? (s/n): ")
                resposta = input().lower()
                
                if resposta == 's':
                    from database_config import migrar_dados_csv_para_sqlite
                    
                    print("Iniciando migração de dados...")
                    sucesso_migracao = migrar_dados_csv_para_sqlite()
                    
                    if sucesso_migracao:
                        print("Migração concluída com sucesso!")
                        # Criar flag para marcar que a migração foi realizada
                        with open('migrado_para_bd.flag', 'w') as f:
                            f.write('1')
                    else:
                        print("Houve problemas durante a migração. Verifique os logs.")
        else:
            print("Falha ao inicializar banco de dados.")
            
        return sucesso
        
    except Exception as e:
        print(f"Erro ao inicializar banco de dados: {str(e)}")
        return False

def fazer_login():
    """
    Solicita as credenciais do usuário e realiza o login.
    
    Returns:
        bool: True se o login foi bem-sucedido, False caso contrário
    """
    global usuario_logado, tipo_usuario, cliente_atual
    
    try:
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
            
    except Exception as e:
        print(f"Erro ao realizar login: {e}")
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

def selecionar_cliente():
    """
    Interface para o usuário selecionar um cliente para trabalhar.
    Filtra os clientes com base nos grupos do usuário.
    
    Returns:
        bool: True se um cliente foi selecionado com sucesso, False caso contrário
    """
    global cliente_atual, usuario_logado
    
    limpar_tela()
    exibir_cabecalho()
    
    print("\nSELEÇÃO DE CLIENTE")
    print("-" * 40)
    
    # Lista de clientes que o usuário pode acessar
    clientes_disponiveis = listar_clientes(usuario_logado)
    
    # Adicionar opção para criar novo cliente
    tem_opcoes = False
    
    if clientes_disponiveis:
        tem_opcoes = True
        print("\nClientes disponíveis:")
        for i, cliente in enumerate(clientes_disponiveis, 1):
            marcador = "* " if cliente == cliente_atual else "  "
            print(f"{marcador}{i}. {cliente}")
            
        if cliente_atual:
            print("\n* Cliente atualmente selecionado")
    else:
        print("\nNenhum cliente disponível para seleção.")
    
    print(f"\n{len(clientes_disponiveis) + 1}. Criar novo cliente")
    print("0. Voltar ao menu anterior")
    
    opcao = input("\nSelecione uma opção (0 para cancelar): ")
    
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
            
            # Adiciona o cliente ao sistema
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

def menu_gerenciar_dominios():
    """Submenu para gerenciamento de domínios, plataformas e seletores."""
    while True:
        limpar_tela()
        exibir_cabecalho()
        
        print("\nGERENCIAMENTO DE DOMÍNIOS E SELETORES")
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
    print("-" * 40)
    senha_atual = input("Senha atual: ")
    nova_senha = input("Nova senha: ")
    confirmacao = input("Confirme a nova senha: ")
    
    if nova_senha != confirmacao:
        print("\nAs senhas não coincidem!")
        return
        
    resultado = alterar_senha(usuario_logado, senha_atual, nova_senha)
    if resultado:
        print("\nSenha alterada com sucesso!")
    else:
        print("\nFalha ao alterar senha. Verifique se a senha atual está correta.")

#----------------------------------------------------------
# MENUS DO USUÁRIO REGULAR
#----------------------------------------------------------

def exibir_menu_principal_usuario():
    """Exibe o menu principal para usuários regulares."""
    print("\nMENU PRINCIPAL")
    print("1. Monitoramento de Preços")
    print("2. Clientes")
    print("3. Meu Perfil")
    print("4. Ajuda")
    print("L. Logout")
    print("0. Sair")

def menu_monitoramento_precos_usuario():
    """Submenu de monitoramento de preços para usuários regulares."""
    global cliente_atual
    
    # Verifica se um cliente está selecionado
    if not cliente_atual:
        print("\nNenhum cliente selecionado. Por favor, selecione um cliente primeiro.")
        if not selecionar_cliente():
            return  # Volta ao menu principal se não conseguir selecionar um cliente
    
    while True:
        limpar_tela()
        exibir_cabecalho()
        
        print(f"\nMONITORAMENTO DE PREÇOS - Cliente: {cliente_atual}")
        print("1. Adicionar produto")
        print("2. Listar meus produtos")
        print("3. Executar monitoramento agora")
        print("4. Histórico de preços")
        print("0. Voltar ao menu principal")
        
        opcao = input("\nEscolha uma opção (0-4): ")
        
        if opcao == '1':
            # Adiciona produto para o cliente atual
            adicionar_produto(cliente=cliente_atual, usuario_atual=usuario_logado)
            input("\nPressione Enter para continuar...")
            
        elif opcao == '2':
            # Lista produtos do usuário para o cliente atual
            produtos = listar_produtos(cliente=cliente_atual, usuario_atual=usuario_logado)
            
            if produtos:
                print(f"\nProdutos monitorados para '{cliente_atual}':")
                print(f"{'ID':<5} | {'Produto':<30} | {'Concorrente':<20} | {'URL':<50}")
                print("-" * 110)
                
                for p in produtos:
                    print(f"{p['id']:<5} | {p['produto'][:30]:<30} | {p['concorrente'][:20]:<20} | {p['url'][:50]}")
            else:
                print(f"\nNenhum produto encontrado para '{cliente_atual}'.")
                
            input("\nPressione Enter para continuar...")
            
        elif opcao == '3':
            # Executa monitoramento
            print("\nExecutando monitoramento para seus produtos...")
            resultado = monitorar_todos_produtos(usuario_atual=usuario_logado)
            if resultado:
                print("Monitoramento concluído com sucesso!")
            else:
                print("Monitoramento concluído, mas com possíveis falhas.")
            input("\nPressione Enter para continuar...")
            
        elif opcao == '4':
            # Visualiza histórico
            visualizar_historico(usuario_atual=usuario_logado, cliente_filtro=cliente_atual)
            input("\nPressione Enter para continuar...")
            
        elif opcao == '0':
            return
            
        else:
            print("Opção inválida. Tente novamente.")
            input("\nPressione Enter para continuar...")

def menu_clientes_usuario():
    """Submenu de gestão de clientes para usuários regulares."""
    global cliente_atual
    
    while True:
        limpar_tela()
        exibir_cabecalho()
        
        print("\nCLIENTES")
        print("1. Selecionar cliente")
        print("2. Adicionar novo cliente")
        print("3. Listar meus clientes")
        print("0. Voltar ao menu principal")
        
        opcao = input("\nEscolha uma opção (0-3): ")
        
        if opcao == '1':
            # Seleciona cliente
            selecionar_cliente()
            
        elif opcao == '2':
            # Adiciona novo cliente
            nome_cliente = input("\nDigite o nome do novo cliente: ")
            
            if nome_cliente:
                resultado = adicionar_cliente(nome_cliente, usuario_atual=usuario_logado)
                
                if resultado:
                    print(f"\nCliente '{nome_cliente}' adicionado com sucesso!")
                    
                    # Pergunta se deseja selecionar o cliente recém-criado
                    selecionar = input("Deseja selecionar este cliente agora? (s/n): ")
                    if selecionar.lower() == 's':
                        cliente_atual = nome_cliente
                        alterar_cliente_atual(usuario_logado, cliente_atual)
                        print(f"Cliente '{cliente_atual}' selecionado!")
                else:
                    print("\nErro ao adicionar cliente.")
            else:
                print("\nNome de cliente inválido.")
                
            input("\nPressione Enter para continuar...")
            
        elif opcao == '3':
            # Lista clientes do usuário
            clientes = obter_clientes_usuario(usuario_logado)
            
            if clientes:
                print("\nMeus clientes:")
                for i, cliente in enumerate(clientes, 1):
                    marcador = "* " if cliente == cliente_atual else "  "
                    print(f"{marcador}{i}. {cliente}")
                    
                print("\n* Cliente atualmente selecionado")
            else:
                print("\nVocê não tem acesso a nenhum cliente.")
                
            input("\nPressione Enter para continuar...")
            
        elif opcao == '0':
            return
            
        else:
            print("Opção inválida. Tente novamente.")
            input("\nPressione Enter para continuar...")

def menu_perfil_usuario():
    """Submenu de perfil do usuário."""
    while True:
        limpar_tela()
        exibir_cabecalho()
        
        print("\nMEU PERFIL")
        print("1. Alterar senha")
        print("2. Ver meus grupos")
        print("3. Ver log de atividades")
        print("0. Voltar ao menu principal")
        
        opcao = input("\nEscolha uma opção (0-3): ")
        
        if opcao == '1':
            # Altera senha
            alterar_senha_usuario()
            input("\nPressione Enter para continuar...")
            
        elif opcao == '2':
            # Mostra grupos do usuário
            grupos = obter_grupos_usuario(usuario_logado)
            
            print("\nMeus grupos:")
            if grupos:
                for i, grupo in enumerate(grupos, 1):
                    print(f"{i}. {grupo}")
            else:
                print("Você não pertence a nenhum grupo.")
                
            input("\nPressione Enter para continuar...")
            
        elif opcao == '3':
            # Mostra log de atividades do usuário
            print("\nLOG DE ATIVIDADES")
            print("-" * 50)
            
            # Verifica se o arquivo de log existe
            if os.path.isfile('monitor_precos.log'):
                try:
                    with open('monitor_precos.log', 'r', encoding='utf-8') as f:
                        linhas = f.readlines()
                        
                    # Filtra linhas relacionadas ao usuário atual
                    logs_usuario = [linha for linha in linhas if usuario_logado in linha]
                    
                    if logs_usuario:
                        # Mostra as últimas 20 entradas (ou menos se não houver tantas)
                        for linha in logs_usuario[-20:]:
                            print(linha.strip())
                        
                        if len(logs_usuario) > 20:
                            print(f"\n...e mais {len(logs_usuario) - 20} entradas anteriores.")
                    else:
                        print("Nenhuma atividade registrada.")
                except Exception as e:
                    print(f"Erro ao ler arquivo de log: {e}")
            else:
                print("Arquivo de log não encontrado.")
                
            input("\nPressione Enter para continuar...")
            
        elif opcao == '0':
            return
            
        else:
            print("Opção inválida. Tente novamente.")
            input("\nPressione Enter para continuar...")

def menu_ajuda_usuario():
    """Submenu de ajuda para usuários."""
    while True:
        limpar_tela()
        exibir_cabecalho()
        
        print("\nAJUDA")
        print("1. Tutoriais")
        print("2. Sobre o sistema")
        print("3. Reportar problema")
        print("0. Voltar ao menu principal")
        
        opcao = input("\nEscolha uma opção (0-3): ")
        
        if opcao == '1':
            # Tutoriais
            print("\nTUTORIAIS")
            print("-" * 50)
            print("1. Como adicionar um produto")
            print("2. Como interpretar o histórico de preços")
            print("3. Como selecionar clientes")
            print("0. Voltar")
            
            tutorial = input("\nSelecione um tutorial (0-3): ")
            
            if tutorial == '1':
                print("\nCOMO ADICIONAR UM PRODUTO")
                print("-" * 50)
                print("1. Primeiro, selecione um cliente no menu 'Clientes'")
                print("2. Vá para o menu 'Monitoramento de Preços'")
                print("3. Escolha a opção 'Adicionar produto'")
                print("4. Preencha as informações solicitadas:")
                print("   - Nome do produto")
                print("   - Nome do concorrente")
                print("   - URL do produto")
                print("5. O sistema verificará automaticamente o melhor seletor CSS")
                print("   para extrair o preço da página web.")
                print("6. Após confirmar, o produto será monitorado automaticamente")
                
            elif tutorial == '2':
                print("\nCOMO INTERPRETAR O HISTÓRICO DE PREÇOS")
                print("-" * 50)
                print("1. No menu 'Monitoramento de Preços', escolha 'Histórico de preços'")
                print("2. Selecione o produto desejado (ou 'todos' para ver todos)")
                print("3. O histórico será exibido em ordem cronológica:")
                print("   - Data: quando o preço foi registrado")
                print("   - Concorrente: de qual concorrente é este preço")
                print("   - Preço: valor do produto na data registrada")
                print("   - URL: link para o produto no site do concorrente")
                print("4. Compare os preços ao longo do tempo para analisar tendências")
                
            elif tutorial == '3':
                print("\nCOMO SELECIONAR CLIENTES")
                print("-" * 50)
                print("1. No menu principal, escolha 'Clientes'")
                print("2. Escolha a opção 'Selecionar cliente'")
                print("3. Você verá a lista de clientes disponíveis")
                print("4. Digite o número correspondente ao cliente desejado")
                print("5. O cliente selecionado ficará ativo para todas as operações")
                print("   até que você selecione outro cliente")
                
            input("\nPressione Enter para continuar...")
                
        elif opcao == '2':
            # Sobre o sistema
            print("\nSOBRE O SISTEMA")
            print("-" * 50)
            print(f"Sistema de Monitoramento de Preços v{__version__}")
            print("Desenvolvido por: Fernando Bastos")
            print("Copyright © 2025 Bastin Marketing. Todos os direitos reservados.")
            print("\nEste software permite monitorar preços de produtos em sites")
            print("de concorrentes e acompanhar a evolução dos valores ao longo do tempo.")
            print("\nPrincipais funcionalidades:")
            print("- Monitoramento automático de preços")
            print("- Registro de histórico de preços")
            print("- Gestão de múltiplos clientes")
            print("- Controle de acesso por usuário")
            
            input("\nPressione Enter para continuar...")
            
        elif opcao == '3':
            # Reportar problema
            print("\nREPORTAR PROBLEMA")
            print("-" * 50)
            print("Se você encontrou um problema no sistema, por favor forneça")
            print("as informações solicitadas abaixo para nos ajudar a resolvê-lo:")
            
            descricao = input("\nDescrição do problema: ")
            passos = input("Passos para reproduzir: ")
            
            if descricao and passos:
                # Registrar o problema no log
                depurar_logs(f"PROBLEMA REPORTADO por {usuario_logado}: {descricao}", "WARNING")
                depurar_logs(f"PASSOS: {passos}", "WARNING")
                
                print("\nProblema reportado com sucesso!")
                print("Nossa equipe técnica analisará o caso e tomará as medidas necessárias.")
            else:
                print("\nPor favor, forneça uma descrição do problema e os passos para reproduzí-lo.")
                
            input("\nPressione Enter para continuar...")
            
        elif opcao == '0':
            return
            
        else:
            print("Opção inválida. Tente novamente.")
            input("\nPressione Enter para continuar...")

#----------------------------------------------------------
# MENUS DO ADMINISTRADOR
#----------------------------------------------------------

def exibir_menu_principal_admin():
    """Exibe o menu principal para administradores."""
    print("\nMENU PRINCIPAL (ADMINISTRADOR)")
    print("1. Monitoramento de Preços")
    print("2. Gestão de Clientes")
    print("3. Administração")
    print("4. Ferramentas")
    print("L. Logout")
    print("0. Sair")

def menu_monitoramento_precos_admin():
    """Submenu de monitoramento de preços para administradores."""
    global cliente_atual
    
    while True:
        limpar_tela()
        exibir_cabecalho()
        
        print("\nMONITORAMENTO DE PREÇOS (ADMINISTRADOR)")
        print("1. Adicionar produto")
        print("2. Listar todos os produtos")
        print("3. Remover produto")
        print("4. Executar monitoramento manual")
        print("5. Configurar agendamento automático (2x por semana)")
        print("6. Visualizar fila de agendamento")
        print("7. Iniciar agendador automático")
        print("0. Voltar ao menu principal")
        
        opcao = input("\nEscolha uma opção (0-7): ")
        
        if opcao == '1':
            # Se não tiver cliente selecionado, pede para selecionar
            if not cliente_atual:
                print("\nNenhum cliente selecionado. Por favor, selecione um cliente primeiro.")
                if not selecionar_cliente():
                    continue  # Volta ao menu se não conseguir selecionar um cliente
            
            # Adiciona produto para o cliente atual
            adicionar_produto(cliente=cliente_atual, usuario_atual=usuario_logado)
            input("\nPressione Enter para continuar...")
            
        elif opcao == '2':
            # Lista todos os produtos
            if cliente_atual:
                print(f"\nListando produtos para o cliente: {cliente_atual}")
                produtos = listar_produtos(cliente=cliente_atual, usuario_atual=usuario_logado)
            else:
                print("\nListando todos os produtos:")
                produtos = listar_produtos(usuario_atual=usuario_logado)
            
            if produtos:
                print(f"{'ID':<5} | {'Cliente':<20} | {'Produto':<30} | {'Concorrente':<20}")
                print("-" * 80)
                
                for p in produtos:
                    print(f"{p['id']:<5} | {p['cliente'][:20]:<20} | {p['produto'][:30]:<30} | {p['concorrente'][:20]:<20}")
                    
                print(f"\nTotal: {len(produtos)} produtos")
            else:
                print("\nNenhum produto encontrado.")
                
            input("\nPressione Enter para continuar...")
            
        elif opcao == '3':
            # Remove produto
            remover_produto(usuario_atual=usuario_logado)
            input("\nPressione Enter para continuar...")
            
        elif opcao == '4':
            # Executa monitoramento manual
            print("\nExecutando monitoramento manual de todos os produtos...")
            print("Nota: Isto verificará todos os produtos imediatamente, independente da fila de agendamento.")
            print("      Os produtos verificados manualmente serão removidos da fila do dia.")
            
            confirmar = input("Deseja continuar? (s/n): ")
            if confirmar.lower() == 's':
                resultado = monitorar_todos_produtos(usuario_atual=usuario_logado, verificacao_manual=True)
                if resultado:
                    print("Monitoramento manual concluído com sucesso!")
                else:
                    print("Monitoramento manual concluído, mas com possíveis falhas.")
            
            input("\nPressione Enter para continuar...")
            
        elif opcao == '5':
            # Configura agendamento 2x por semana
            print("\nConfigurando agendamento automático (2x por semana)")
            print("Esta configuração determina quando o sistema processará a fila de produtos automaticamente.")
            
            info_agendamento, sucesso = configurar_agendamento()
            if sucesso and info_agendamento:
                salvar_configuracao_agendamento(info_agendamento)
                print("\nPara iniciar o agendador, use a opção 7 do menu.")
            
            input("\nPressione Enter para continuar...")
            
        elif opcao == '6':
            # Visualizar fila de agendamento
            print("\nFILA DE AGENDAMENTO")
            print("-" * 60)
            
            try:
                from database_config import criar_conexao
                
                conexao, cursor = criar_conexao()
                
                # Buscar todos os produtos na fila com suas informações
                cursor.execute('''
                SELECT fa.posicao_fila, fa.id_produto, c.nome as cliente, p.nome as produto, 
                       p.concorrente, fa.ultima_verificacao, fa.verificacao_manual
                FROM fila_agendamento fa
                JOIN produtos p ON fa.id_produto = p.id
                JOIN clientes c ON p.id_cliente = c.id
                ORDER BY fa.posicao_fila
                ''')
                
                fila = cursor.fetchall()
                conexao.close()
                
                if not fila:
                    print("Fila de agendamento vazia. Nenhum produto na fila.")
                else:
                    print(f"{'Pos.':<5} | {'ID Prod.':<8} | {'Cliente':<20} | {'Produto':<25} | {'Concorrente':<20} | {'Última Verificação':<20} | {'Status':<10}")
                    print("-" * 120)
                    
                    data_hoje = datetime.now().strftime('%Y-%m-%d')
                    
                    for item in fila:
                        ultima_verif = item['ultima_verificacao'] if item['ultima_verificacao'] else "Nunca"
                        
                        # Determinar status
                        if item['verificacao_manual'] == 1 and ultima_verif and ultima_verif.startswith(data_hoje):
                            status = "Verificado"
                        else:
                            status = "Na fila"
                        
                        print(f"{item['posicao_fila']:<5} | {item['id_produto']:<8} | {item['cliente'][:20]:<20} | {item['produto'][:25]:<25} | {item['concorrente'][:20]:<20} | {ultima_verif:<20} | {status:<10}")
                    
                    print(f"\nTotal: {len(fila)} produtos na fila")
                    
                    # Opções adicionais
                    print("\nOpções:")
                    print("1. Reorganizar fila (corrigir posições)")
                    print("2. Processar próximos 10 produtos da fila agora")
                    print("0. Voltar")
                    
                    sub_opcao = input("\nEscolha uma opção (0-2): ")
                    
                    if sub_opcao == '1':
                        # Reorganizar fila
                        from scheduler import reorganizar_fila
                        
                        if reorganizar_fila():
                            print("Fila reorganizada com sucesso!")
                        else:
                            print("Falha ao reorganizar fila.")
                    
                    elif sub_opcao == '2':
                        # Processar próximos produtos manualmente
                        from scheduler import processar_proximos_produtos
                        
                        print("\nProcessando próximos 10 produtos da fila...")
                        sucesso = processar_proximos_produtos(10)
                        
                        if sucesso:
                            print("Processamento concluído com sucesso!")
                        else:
                            print("Processamento concluído com possíveis falhas.")
                
            except Exception as e:
                print(f"Erro ao visualizar fila de agendamento: {e}")
            
            input("\nPressione Enter para continuar...")
            
        elif opcao == '7':
            # Inicia agendador
            print("\nO agendador será iniciado. O sistema ficará em execução.")
            print("Para encerrar o agendador, pressione Ctrl+C a qualquer momento.")
            
            # Verificar se o agendamento está configurado
            from scheduler import carregar_configuracao_agendamento
            
            config = carregar_configuracao_agendamento()
            if not config:
                print("\nNenhuma configuração de agendamento encontrada.")
                print("Por favor, configure o agendamento primeiro (opção 5).")
            else:
                dias = config.get('dias', [])
                horario = config.get('horario', '')
                
                print(f"\nAgendamento configurado para:")
                for dia in dias:
                    print(f"- {dia.capitalize()} às {horario}")
                
                confirmar = input("\nIniciar agendador com esta configuração? (s/n): ")
                if confirmar.lower() == 's':
                    input("Pressione Enter para iniciar o agendador...")
                    
                    from scheduler import executar_agendador
                    executar_agendador()
            
        elif opcao == '0':
            return
            
        else:
            print("Opção inválida. Tente novamente.")
            input("\nPressione Enter para continuar...")

def menu_gestao_clientes_admin():
    """Submenu de gestão de clientes para administradores."""
    global cliente_atual
    
    while True:
        limpar_tela()
        exibir_cabecalho()
        
        print("\nGESTÃO DE CLIENTES (ADMINISTRADOR)")
        print("1. Selecionar cliente")
        print("2. Adicionar cliente")
        print("3. Gerenciar todos os clientes")
        print("0. Voltar ao menu principal")
        
        opcao = input("\nEscolha uma opção (0-3): ")
        
        if opcao == '1':
            # Seleciona cliente
            selecionar_cliente()
            
        elif opcao == '2':
            # Adiciona novo cliente
            nome_cliente = input("\nDigite o nome do novo cliente: ")
            
            if nome_cliente:
                resultado = adicionar_cliente(nome_cliente, usuario_atual=usuario_logado)
                
                if resultado:
                    print(f"\nCliente '{nome_cliente}' adicionado com sucesso!")
                    
                    # Pergunta se deseja selecionar o cliente recém-criado
                    selecionar = input("Deseja selecionar este cliente agora? (s/n): ")
                    if selecionar.lower() == 's':
                        cliente_atual = nome_cliente
                        alterar_cliente_atual(usuario_logado, cliente_atual)
                        print(f"Cliente '{cliente_atual}' selecionado!")
                        
                    # Pergunta se deseja ver menu de administração para gerenciar grupos deste cliente
                    gerenciar = input("Deseja gerenciar grupos para este cliente? (s/n): ")
                    if gerenciar.lower() == 's':
                        # Integração com a função específica de admin para gerenciar grupos de clientes
                        from admin import menu_gerenciar_grupos
                        menu_gerenciar_grupos(usuario_logado)
                else:
                    print("\nErro ao adicionar cliente.")
            else:
                print("\nNome de cliente inválido.")
                
            input("\nPressione Enter para continuar...")
            
        elif opcao == '3':
            # Lista todos os clientes (admin vê todos)
            todos_clientes = listar_clientes(usuario_atual=usuario_logado)
            
            if todos_clientes:
                print("\nTodos os clientes:")
                for i, cliente in enumerate(todos_clientes, 1):
                    marcador = "* " if cliente == cliente_atual else "  "
                    print(f"{marcador}{i}. {cliente}")
                    
                print("\n* Cliente atualmente selecionado")
                
                # Opções adicionais para administradores
                print("\nOpções:")
                print("1. Associar cliente a um grupo")
                print("2. Ver histórico de um cliente")
                print("0. Voltar")
                
                sub_opcao = input("\nEscolha uma opção (0-2): ")
                
                if sub_opcao == '1':
                    # Integração com a função específica de admin para gerenciar grupos
                    from admin import menu_gerenciar_grupos
                    menu_gerenciar_grupos(usuario_logado)
                elif sub_opcao == '2':
                    # Selecionar cliente para ver histórico
                    try:
                        escolha = int(input("\nDigite o número do cliente para ver histórico (0 para cancelar): "))
                        
                        if 1 <= escolha <= len(todos_clientes):
                            cliente_escolhido = todos_clientes[escolha-1]
                            visualizar_historico(usuario_atual=usuario_logado, cliente_filtro=cliente_escolhido)
                    except ValueError:
                        print("Entrada inválida!")
            else:
                print("\nNenhum cliente cadastrado.")
                
            input("\nPressione Enter para continuar...")
            
        elif opcao == '0':
            return
            
        else:
            print("Opção inválida. Tente novamente.")
            input("\nPressione Enter para continuar...")

def menu_administracao_admin():
    """Submenu de administração para administradores."""
    while True:
        limpar_tela()
        exibir_cabecalho()
        
        print("\nADMINISTRAÇÃO")
        print("1. Gerenciar usuários")
        print("2. Gerenciar grupos")
        print("3. Domínios e seletores")
        print("4. Backup do sistema")
        print("5. Relatórios de atividade")
        print("0. Voltar ao menu principal")
        
        opcao = input("\nEscolha uma opção (0-5): ")
        
        if opcao == '1':
            # Gerenciar usuários (usando função da interface admin)
            from admin import menu_gerenciar_usuarios
            menu_gerenciar_usuarios(usuario_logado)
            
        elif opcao == '2':
            # Gerenciar grupos (usando função da interface admin)
            from admin import menu_gerenciar_grupos
            menu_gerenciar_grupos(usuario_logado)
            
        elif opcao == '3':
            # Gerenciar domínios e seletores
            menu_gerenciar_dominios()
            
        elif opcao == '4':
            # Criar backup do sistema
            print("\nCriando backup do sistema...")
            
            # Backup do banco de dados
            try:
                import shutil
                from datetime import datetime
                
                data_backup = datetime.now().strftime('%Y%m%d_%H%M%S')
                
                # Garantir que a pasta de backups existe
                if not os.path.exists('backups'):
                    os.makedirs('backups')
                
                # Backup do banco de dados
                shutil.copy2('monitor_precos.db', f"backups/monitor_precos.db.{data_backup}.bak")
                print(f"Backup do banco de dados criado: backups/monitor_precos.db.{data_backup}.bak")
                
                # Backup dos demais arquivos
                resultado = criar_backup()
                
                if resultado:
                    print("Backup completo criado com sucesso!")
                else:
                    print("Houve um erro ao criar o backup dos arquivos.")
            except Exception as e:
                print(f"Erro ao criar backup: {e}")
                
            input("\nPressione Enter para continuar...")
            
        elif opcao == '5':
            # Relatórios de atividade (usando função da interface admin)
            from admin import relatorio_atividade_sistema
            relatorio_atividade_sistema()
            
        elif opcao == '0':
            return
            
        else:
            print("Opção inválida. Tente novamente.")
            input("\nPressione Enter para continuar...")

def menu_ferramentas_admin():
    """Submenu de ferramentas para administradores."""
    while True:
        limpar_tela()
        exibir_cabecalho()
        
        print("\nFERRAMENTAS")
        print("1. Validação da estrutura de dados")
        print("2. Manutenção do banco")
        print("3. Logs do sistema")
        print("0. Voltar ao menu principal")
        
        opcao = input("\nEscolha uma opção (0-3): ")
        
        if opcao == '1':
            # Validação da estrutura de dados
            print("\nValidando estrutura de dados...")
            
            try:
                from auth_validacao import verificar_e_organizar_usuarios
                
                resultado = verificar_e_organizar_usuarios()
                
                if resultado:
                    print("Estrutura de usuários validada com sucesso!")
                else:
                    print("Houve problemas na validação da estrutura de usuários.")
                    
                # Verificar estrutura das outras tabelas
                from database_config import verificar_dados
                if verificar_dados():
                    print("Estrutura geral do banco de dados validada com sucesso!")
                else:
                    print("Houve problemas na validação do banco de dados.")
                    
            except Exception as e:
                print(f"Erro ao validar estrutura: {e}")
                
            input("\nPressione Enter para continuar...")
            
        elif opcao == '2':
            # Manutenção do banco
            print("\nMANUTENÇÃO DO BANCO DE DADOS")
            print("1. Verificar integridade")
            print("2. Otimizar (VACUUM)")
            print("3. Reconstruir índices")
            print("0. Voltar")
            
            sub_opcao = input("\nEscolha uma opção (0-3): ")
            
            try:
                from database_config import criar_conexao
                
                if sub_opcao == '1':
                    # Verificar integridade
                    print("\nVerificando integridade do banco de dados...")
                    
                    conexao, cursor = criar_conexao()
                    cursor.execute("PRAGMA integrity_check")
                    resultado = cursor.fetchone()
                    conexao.close()
                    
                    if resultado and resultado[0] == "ok":
                        print("Banco de dados íntegro!")
                    else:
                        print(f"Problemas encontrados: {resultado}")
                        
                elif sub_opcao == '2':
                    # Otimizar (VACUUM)
                    print("\nOtimizando banco de dados (VACUUM)...")
                    
                    conexao, cursor = criar_conexao()
                    cursor.execute("VACUUM")
                    conexao.close()
                    
                    print("Otimização concluída!")
                    
                elif sub_opcao == '3':
                    # Reconstruir índices
                    print("\nReconstruindo índices...")
                    
                    conexao, cursor = criar_conexao()
                    
                    # Reconstruir índices para as principais tabelas
                    for tabela in ["usuarios", "grupos", "clientes", "produtos", "historico_precos"]:
                        cursor.execute(f"REINDEX {tabela}")
                        
                    conexao.close()
                    print("Índices reconstruídos com sucesso!")
                    
            except Exception as e:
                print(f"Erro durante a manutenção: {e}")
                
            input("\nPressione Enter para continuar...")
            
        elif opcao == '3':
            # Logs do sistema
            print("\nLOGS DO SISTEMA")
            print("-" * 50)
            
            # Verifica se o arquivo de log existe
            if os.path.isfile('monitor_precos.log'):
                try:
                    with open('monitor_precos.log', 'r', encoding='utf-8') as f:
                        linhas = f.readlines()
                        
                    # Opções de filtragem
                    print("1. Mostrar últimas 50 entradas")
                    print("2. Filtrar por erro (ERROR)")
                    print("3. Filtrar por alerta (WARNING)")
                    print("4. Filtrar por usuário")
                    print("0. Voltar")
                    
                    sub_opcao = input("\nEscolha uma opção (0-4): ")
                    
                    if sub_opcao == '1':
                        # Mostrar últimas 50 entradas
                        print("\nÚltimas 50 entradas de log:")
                        print("-" * 80)
                        
                        for linha in linhas[-50:]:
                            print(linha.strip())
                            
                    elif sub_opcao == '2':
                        # Filtrar por erro
                        erros = [linha for linha in linhas if "[ERROR]" in linha]
                        
                        print(f"\nErros encontrados ({len(erros)}):")
                        print("-" * 80)
                        
                        for linha in erros[-50:]:  # Mostra até 50 erros mais recentes
                            print(linha.strip())
                            
                        if len(erros) > 50:
                            print(f"\n...e mais {len(erros) - 50} erros anteriores.")
                            
                    elif sub_opcao == '3':
                        # Filtrar por alerta
                        alertas = [linha for linha in linhas if "[WARNING]" in linha]
                        
                        print(f"\nAlertas encontrados ({len(alertas)}):")
                        print("-" * 80)
                        
                        for linha in alertas[-50:]:  # Mostra até 50 alertas mais recentes
                            print(linha.strip())
                            
                        if len(alertas) > 50:
                            print(f"\n...e mais {len(alertas) - 50} alertas anteriores.")
                            
                    elif sub_opcao == '4':
                        # Filtrar por usuário
                        usuario_filtro = input("\nDigite o nome do usuário: ")
                        
                        if usuario_filtro:
                            logs_usuario = [linha for linha in linhas if usuario_filtro in linha]
                            
                            print(f"\nLogs para o usuário '{usuario_filtro}' ({len(logs_usuario)}):")
                            print("-" * 80)
                            
                            for linha in logs_usuario[-50:]:  # Mostra até 50 entradas mais recentes
                                print(linha.strip())
                                
                            if len(logs_usuario) > 50:
                                print(f"\n...e mais {len(logs_usuario) - 50} entradas anteriores.")
                        else:
                            print("Nome de usuário inválido.")
                    
                except Exception as e:
                    print(f"Erro ao ler arquivo de log: {e}")
            else:
                print("Arquivo de log não encontrado.")
                
            input("\nPressione Enter para continuar...")
            
        elif opcao == '0':
            return
            
        else:
            print("Opção inválida. Tente novamente.")
            input("\nPressione Enter para continuar...")

#----------------------------------------------------------
# FUNÇÃO PRINCIPAL DO PROGRAMA
#----------------------------------------------------------

def menu_principal():
    """
    Função principal que controla o fluxo do programa.
    Gerencia o login e direciona para os menus adequados conforme o tipo de usuário.
    """
    global usuario_logado, tipo_usuario, cliente_atual
    
    # Inicializar o banco de dados
    if not inicializar_banco_dados():
        print("Falha ao inicializar banco de dados. O programa será encerrado.")
        sys.exit(1)
    
    # Solicita login antes de mostrar o menu principal
    if not fazer_login():
        print("\nNão foi possível realizar o login. O programa será encerrado.")
        sys.exit(1)
    
    # Loop principal do menu
    while True:
        try:
            # Limpa a tela 
            limpar_tela()
            exibir_cabecalho()
            
            # Exibe o menu de acordo com o tipo de usuário
            if tipo_usuario == 'admin':
                exibir_menu_principal_admin()
            else:
                exibir_menu_principal_usuario()
            
            opcao = input("\nEscolha uma opção: ").upper()
            
            # Opções comuns para todos os tipos de usuário
            if opcao == '0':
                print("\nSaindo do sistema. Até logo!")
                depurar_logs(f"Sistema encerrado pelo usuário {usuario_logado}", "INFO")
                sys.exit(0)
                
            elif opcao == 'L':
                # Logout
                logout_sucesso = fazer_logout()
                
                if logout_sucesso:
                    # Após logout, solicita novo login
                    if not fazer_login():
                        print("\nNão foi possível realizar o login. O programa será encerrado.")
                        depurar_logs("Tentativa de login após logout falhou", "WARNING")
                        sys.exit(1)
                        
            # Menu para administradores
            elif tipo_usuario == 'admin':
                if opcao == '1':
                    menu_monitoramento_precos_admin()
                elif opcao == '2':
                    menu_gestao_clientes_admin()
                elif opcao == '3':
                    menu_administracao_admin()
                elif opcao == '4':
                    menu_ferramentas_admin()
                else:
                    print("Opção inválida. Tente novamente.")
                    time.sleep(1)
                    
            # Menu para usuários regulares
            else:
                if opcao == '1':
                    menu_monitoramento_precos_usuario()
                elif opcao == '2':
                    menu_clientes_usuario()
                elif opcao == '3':
                    menu_perfil_usuario()
                elif opcao == '4':
                    menu_ajuda_usuario()
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

#----------------------------------------------------------
# PONTO DE ENTRADA DO PROGRAMA
#----------------------------------------------------------

if __name__ == "__main__":
    try:
        menu_principal()
    except Exception as e:
        depurar_logs(f"Erro fatal: {str(e)}", "ERROR")
        print(f"\nErro fatal: {str(e)}")
        print("O programa será encerrado.")
        sys.exit(1)