#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo de interface para usuários regulares.
"""

import os
import time
from utils.logger import Logger
from controllers.auth_controller import AuthController
from controllers.cliente_controller import ClienteController
from controllers.produto_controller import ProdutoController

class UsuarioView:
    def __init__(self, usuario_logado, tipo_usuario, cliente_atual):
        self.usuario_logado = usuario_logado
        self.tipo_usuario = tipo_usuario
        self.cliente_atual = cliente_atual
    
    def limpar_tela(self):
        """Limpa a tela do terminal."""
        if os.name == 'nt':  # Para Windows
            os.system('cls')
        else:  # Para Linux/Mac
            os.system('clear')
    
    def exibir_cabecalho(self):
        """Exibe o cabeçalho do programa com informações de versão."""
        print("\n" + "=" * 60)
        print("   SISTEMA DE MONITORAMENTO DE PREÇOS v1.1.0")
        print("=" * 60)
        print("Desenvolvido por: Bastin Marketing")
        if self.usuario_logado:
            grupos = AuthController.obter_grupos_usuario(self.usuario_logado)
            grupos_str = ", ".join(grupos) if grupos else "Nenhum"
            print(f"Usuário: {self.usuario_logado} ({self.tipo_usuario})")
            
            if self.cliente_atual:
                print(f"Cliente atual: {self.cliente_atual}")
            else:
                print("Cliente atual: Nenhum selecionado")
        print("-" * 60)
    
    def exibir_menu_principal(self):
        """
        Exibe o menu principal para usuários regulares.
        
        Returns:
            str: Opção escolhida pelo usuário
        """
        print("\nMENU PRINCIPAL")
        print("1. Monitoramento de Preços")
        print("2. Clientes")
        print("3. Meu Perfil")
        print("4. Ajuda")
        print("L. Logout")
        print("0. Sair")
        
        opcao = input("\nEscolha uma opção: ")
        
        if opcao == '1':
            self.menu_monitoramento_precos()
        elif opcao == '2':
            self.menu_clientes()
        elif opcao == '3':
            self.menu_perfil()
        elif opcao == '4':
            self.menu_ajuda()
        
        return opcao
    
    def selecionar_cliente(self):
        """
        Interface para o usuário selecionar um cliente para trabalhar.
        
        Returns:
            bool: True se um cliente foi selecionado com sucesso, False caso contrário
        """
        self.limpar_tela()
        self.exibir_cabecalho()
        
        print("\nSELEÇÃO DE CLIENTE")
        print("-" * 40)
        
        # Lista de clientes que o usuário pode acessar
        clientes_disponiveis = ClienteController.listar_clientes(self.usuario_logado)
        
        # Adicionar opção para criar novo cliente
        tem_opcoes = False
        
        if clientes_disponiveis:
            tem_opcoes = True
            print("\nClientes disponíveis:")
            for i, cliente in enumerate(clientes_disponiveis, 1):
                marcador = "* " if cliente['nome'] == self.cliente_atual else "  "
                print(f"{marcador}{i}. {cliente['nome']}")
                
            if self.cliente_atual:
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
                cliente_selecionado = clientes_disponiveis[escolha - 1]['nome']
                
                # Atualiza o cliente atual no sistema
                self.cliente_atual = cliente_selecionado
                AuthController.alterar_cliente_atual(self.usuario_logado, self.cliente_atual)
                
                print(f"\nCliente '{self.cliente_atual}' selecionado com sucesso!")
                input("\nPressione Enter para continuar...")
                return True
            
            elif escolha == len(clientes_disponiveis) + 1:
                # Criar novo cliente
                novo_cliente = input("\nDigite o nome do novo cliente: ")
                
                if not novo_cliente:
                    print("Nome de cliente inválido.")
                    input("\nPressione Enter para tentar novamente...")
                    return self.selecionar_cliente()
                
                # Adiciona o cliente ao sistema
                sucesso = ClienteController.adicionar_cliente(novo_cliente, usuario_atual=self.usuario_logado)
                
                if sucesso:
                    # Atualiza o cliente atual no sistema
                    self.cliente_atual = novo_cliente
                    AuthController.alterar_cliente_atual(self.usuario_logado, self.cliente_atual)
                    
                    print(f"\nNovo cliente '{self.cliente_atual}' criado e selecionado!")
                    input("\nPressione Enter para continuar...")
                    return True
                else:
                    print("Falha ao criar novo cliente.")
                    input("\nPressione Enter para tentar novamente...")
                    return self.selecionar_cliente()
            
            else:
                print("Opção inválida.")
                input("\nPressione Enter para tentar novamente...")
                return self.selecionar_cliente()
                
        except ValueError:
            print("Entrada inválida. Digite um número.")
            input("\nPressione Enter para tentar novamente...")
            return self.selecionar_cliente()
    
    def menu_monitoramento_precos(self):
        """Submenu de monitoramento de preços para usuários regulares."""
        # Verifica se um cliente está selecionado
        if not self.cliente_atual:
            print("\nNenhum cliente selecionado. Por favor, selecione um cliente primeiro.")
            if not self.selecionar_cliente():
                return  # Volta ao menu principal se não conseguir selecionar um cliente
        
        while True:
            self.limpar_tela()
            self.exibir_cabecalho()
            
            print(f"\nMONITORAMENTO DE PREÇOS - Cliente: {self.cliente_atual}")
            print("1. Adicionar produto")
            print("2. Listar meus produtos")
            print("3. Executar monitoramento agora")
            print("4. Histórico de preços")
            print("0. Voltar ao menu principal")
            
            opcao = input("\nEscolha uma opção (0-4): ")
            
            if opcao == '1':
                # Interface para adicionar produto
                print("\nADICIONAR PRODUTO")
                print("-" * 40)
                
                # O cliente já está selecionado
                produto = input("Nome do produto: ")
                concorrente = input("Nome do concorrente: ")
                url = input("URL do produto: ")
                
                if produto and concorrente and url:
                    resultado = ProdutoController.adicionar_produto(
                        cliente=self.cliente_atual,
                        produto=produto,
                        concorrente=concorrente,
                        url=url,
                        usuario_atual=self.usuario_logado
                    )
                    
                    if resultado:
                        print(f"\nProduto '{produto}' adicionado com sucesso!")
                    else:
                        print("\nFalha ao adicionar produto. Verifique os dados e tente novamente.")
                else:
                    print("\nTodos os campos são obrigatórios.")
                
                input("\nPressione Enter para continuar...")
                
            elif opcao == '2':
                # Lista produtos do usuário para o cliente atual
                produtos = ProdutoController.listar_produtos(cliente=self.cliente_atual, usuario_atual=self.usuario_logado)
                
                if produtos:
                    print(f"\nProdutos monitorados para '{self.cliente_atual}':")
                    print(f"{'ID':<5} | {'Produto':<30} | {'Concorrente':<20} | {'URL':<50}")
                    print("-" * 110)
                    
                    for p in produtos:
                        print(f"{p['id']:<5} | {p['produto'][:30]:<30} | {p['concorrente'][:20]:<20} | {p['url'][:50]}")
                else:
                    print(f"\nNenhum produto encontrado para '{self.cliente_atual}'.")
                    
                input("\nPressione Enter para continuar...")
                
            elif opcao == '3':
                # Executa monitoramento
                print("\nExecutando monitoramento para seus produtos...")
                resultado = ProdutoController.monitorar_todos_produtos(usuario_atual=self.usuario_logado)
                if resultado:
                    print("Monitoramento concluído com sucesso!")
                else:
                    print("Monitoramento concluído, mas com possíveis falhas.")
                input("\nPressione Enter para continuar...")
                
            elif opcao == '4':
                # Visualiza histórico
                self.visualizar_historico()
                input("\nPressione Enter para continuar...")
                
            elif opcao == '0':
                return
                
            else:
                print("Opção inválida. Tente novamente.")
                input("\nPressione Enter para continuar...")
    
    def menu_clientes(self):
        """Submenu de gestão de clientes para usuários regulares."""
        while True:
            self.limpar_tela()
            self.exibir_cabecalho()
            
            print("\nCLIENTES")
            print("1. Selecionar cliente")
            print("2. Adicionar novo cliente")
            print("3. Listar meus clientes")
            print("0. Voltar ao menu principal")
            
            opcao = input("\nEscolha uma opção (0-3): ")
            
            if opcao == '1':
                # Seleciona cliente
                self.selecionar_cliente()
                
            elif opcao == '2':
                # Adiciona novo cliente
                nome_cliente = input("\nDigite o nome do novo cliente: ")
                
                if nome_cliente:
                    resultado = ClienteController.adicionar_cliente(nome_cliente, usuario_atual=self.usuario_logado)
                    
                    if resultado:
                        print(f"\nCliente '{nome_cliente}' adicionado com sucesso!")
                        
                        # Pergunta se deseja selecionar o cliente recém-criado
                        selecionar = input("Deseja selecionar este cliente agora? (s/n): ")
                        if selecionar.lower() == 's':
                            self.cliente_atual = nome_cliente
                            AuthController.alterar_cliente_atual(self.usuario_logado, self.cliente_atual)
                            print(f"Cliente '{self.cliente_atual}' selecionado!")
                    else:
                        print("\nErro ao adicionar cliente.")
                else:
                    print("\nNome de cliente inválido.")
                    
                input("\nPressione Enter para continuar...")
                
            elif opcao == '3':
                # Lista clientes do usuário
                clientes = ClienteController.listar_clientes(self.usuario_logado)
                
                if clientes:
                    print("\nMeus clientes:")
                    for i, cliente in enumerate(clientes, 1):
                        marcador = "* " if cliente['nome'] == self.cliente_atual else "  "
                        print(f"{marcador}{i}. {cliente['nome']}")
                        
                    print("\n* Cliente atualmente selecionado")
                else:
                    print("\nVocê não tem acesso a nenhum cliente.")
                    
                input("\nPressione Enter para continuar...")
                
            elif opcao == '0':
                return
                
            else:
                print("Opção inválida. Tente novamente.")
                input("\nPressione Enter para continuar...")
    
    def menu_perfil(self):
        """Submenu de perfil do usuário."""
        while True:
            self.limpar_tela()
            self.exibir_cabecalho()
            
            print("\nMEU PERFIL")
            print("1. Alterar senha")
            print("2. Ver meus grupos")
            print("3. Ver log de atividades")
            print("0. Voltar ao menu principal")
            
            opcao = input("\nEscolha uma opção (0-3): ")
            
            if opcao == '1':
                # Altera senha
                print("\nALTERAR SENHA")
                print("-" * 40)
                
                senha_atual = input("Senha atual: ")
                nova_senha = input("Nova senha: ")
                confirmacao = input("Confirme a nova senha: ")
                
                if nova_senha != confirmacao:
                    print("\nAs senhas não coincidem!")
                else:
                    resultado = AuthController.alterar_senha(self.usuario_logado, senha_atual, nova_senha)
                    if resultado:
                        print("\nSenha alterada com sucesso!")
                    else:
                        print("\nFalha ao alterar senha. Verifique se a senha atual está correta.")
                
                input("\nPressione Enter para continuar...")
                
            elif opcao == '2':
                # Mostra grupos do usuário
                grupos = AuthController.obter_grupos_usuario(self.usuario_logado)
                
                print("\nMeus grupos:")
                if grupos:
                    for i, grupo in enumerate(grupos, 1):
                        print(f"{i}. {grupo}")
                else:
                    print("Você não pertence a nenhum grupo.")
                    
                input("\nPressione Enter para continuar...")
                
            elif opcao == '3':
                # Mostra log de atividades do usuário
                self.mostrar_log_atividades()
                input("\nPressione Enter para continuar...")
                
            elif opcao == '0':
                return
                
            else:
                print("Opção inválida. Tente novamente.")
                input("\nPressione Enter para continuar...")
    
    def mostrar_log_atividades(self):
        """Mostra o log de atividades do usuário atual."""
        print("\nLOG DE ATIVIDADES")
        print("-" * 50)
        
        # Verifica se o arquivo de log existe
        log_file = 'monitor_precos.log'
        if os.path.isfile(log_file):
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    linhas = f.readlines()
                    
                # Filtra linhas relacionadas ao usuário atual
                logs_usuario = [linha for linha in linhas if self.usuario_logado in linha]
                
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
    
    def visualizar_historico(self):
        """Interface para visualizar o histórico de preços."""
        print("\nHISTÓRICO DE PREÇOS")
        print("-" * 50)
        
        # Se temos cliente atual, mostra diretamente os produtos desse cliente
        if self.cliente_atual:
            from models.cliente import Cliente
            from models.produto import Produto
            
            cliente_obj = Cliente.buscar_por_nome(self.cliente_atual)
            if not cliente_obj:
                print(f"Cliente '{self.cliente_atual}' não encontrado.")
                return
            
            # Buscar produtos do cliente
            produtos = Produto.listar_por_cliente(cliente_obj.id)
            
            if not produtos:
                print(f"Não há produtos cadastrados para o cliente '{self.cliente_atual}'.")
                return
            
            print(f"\nProdutos disponíveis para o cliente '{self.cliente_atual}':")
            for i, p in enumerate(produtos, 1):
                print(f"{i}. {p.nome}")
            
            try:
                escolha = input("\nDigite o número do produto para ver o histórico (ou 'todos' para ver todos): ")
                
                if escolha.lower() == 'todos':
                    print(f"\nHistórico de preços de todos os produtos do cliente '{self.cliente_atual}':")
                    self._mostrar_historico_todos_produtos(produtos)
                else:
                    try:
                        indice = int(escolha) - 1
                        if 0 <= indice < len(produtos):
                            produto = produtos[indice]
                            print(f"\nHistórico de preços para '{produto.nome}':")
                            self._mostrar_historico_produto(produto)
                        else:
                            print("Opção inválida.")
                    except ValueError:
                        print("Entrada inválida. Digite um número ou 'todos'.")
            except Exception as e:
                print(f"Erro ao mostrar histórico: {e}")
        else:
            print("Nenhum cliente selecionado. Selecione um cliente primeiro.")
    
    def _mostrar_historico_produto(self, produto):
        """
        Mostra o histórico de preços de um produto específico.
        
        Args:
            produto: Objeto Produto
        """
        # Obter histórico do produto
        historico = produto.obter_historico()
        
        if not historico:
            print("Não há histórico de preços disponível para este produto.")
            return
        
        print(f"{'Data':<12} | {'Preço':<10}")
        print("-" * 25)
        
        for registro in historico:
            print(f"{registro['data']:<12} | R$ {registro['preco']:<8.2f}")
    
    def _mostrar_historico_todos_produtos(self, produtos):
        """
        Mostra o histórico de preços de todos os produtos.
        
        Args:
            produtos: Lista de objetos Produto
        """
        print(f"{'Produto':<30} | {'Data':<12} | {'Preço':<10}")
        print("-" * 57)
        
        for produto in produtos:
            historico = produto.obter_historico()
            if historico:
                for registro in historico:
                    print(f"{produto.nome[:30]:<30} | {registro['data']:<12} | R$ {registro['preco']:<8.2f}")
            else:
                print(f"{produto.nome[:30]:<30} | {'Sem histórico':<23}")
    
    def menu_ajuda(self):
        """Submenu de ajuda para usuários."""
        while True:
            self.limpar_tela()
            self.exibir_cabecalho()
            
            print("\nAJUDA")
            print("1. Tutoriais")
            print("2. Sobre o sistema")
            print("3. Reportar problema")
            print("0. Voltar ao menu principal")
            
            opcao = input("\nEscolha uma opção (0-3): ")
            
            if opcao == '1':
                self.mostrar_tutoriais()
                input("\nPressione Enter para continuar...")
                
            elif opcao == '2':
                self.mostrar_sobre_sistema()
                input("\nPressione Enter para continuar...")
                
            elif opcao == '3':
                self.reportar_problema()
                input("\nPressione Enter para continuar...")
                
            elif opcao == '0':
                return
                
            else:
                print("Opção inválida. Tente novamente.")
                input("\nPressione Enter para continuar...")
    
    def mostrar_tutoriais(self):
        """Mostra os tutoriais do sistema."""
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
            print("   - Preço: valor do produto na data registrada")
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
    
    def mostrar_sobre_sistema(self):
        """Mostra informações sobre o sistema."""
        print("\nSOBRE O SISTEMA")
        print("-" * 50)
        print("Sistema de Monitoramento de Preços v1.1.0")
        print("Desenvolvido por: Fernando Bastos")
        print("Copyright © 2025 Bastin Marketing. Todos os direitos reservados.")
        print("\nEste software permite monitorar preços de produtos em sites")
        print("de concorrentes e acompanhar a evolução dos valores ao longo do tempo.")
        print("\nPrincipais funcionalidades:")
        print("- Monitoramento automático de preços")
        print("- Registro de histórico de preços")
        print("- Gestão de múltiplos clientes")
        print("- Controle de acesso por usuário")
    
    def reportar_problema(self):
        """Interface para reportar um problema."""
        print("\nREPORTAR PROBLEMA")
        print("-" * 50)
        print("Se você encontrou um problema no sistema, por favor forneça")
        print("as informações solicitadas abaixo para nos ajudar a resolvê-lo:")
        
        descricao = input("\nDescrição do problema: ")
        passos = input("Passos para reproduzir: ")
        
        if descricao and passos:
            # Registrar o problema no log
            Logger.log(f"PROBLEMA REPORTADO por {self.usuario_logado}: {descricao}", "WARNING")
            Logger.log(f"PASSOS: {passos}", "WARNING")
            
            print("\nProblema reportado com sucesso!")
            print("Nossa equipe técnica analisará o caso e tomará as medidas necessárias.")
        else:
            print("\nPor favor, forneça uma descrição do problema e os passos para reproduzi-lo.")