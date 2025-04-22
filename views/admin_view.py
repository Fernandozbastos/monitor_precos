#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo de interface para administradores.
"""

import os
import time
from utils.logger import Logger
from controllers.auth_controller import AuthController
from controllers.cliente_controller import ClienteController
from controllers.produto_controller import ProdutoController
from views.usuario_view import UsuarioView
from database.connector import DatabaseConnector

class AdminView(UsuarioView):
    def __init__(self, usuario_logado, tipo_usuario, cliente_atual):
        super().__init__(usuario_logado, tipo_usuario, cliente_atual)
    
    def exibir_menu_principal(self):
        """
        Exibe o menu principal para administradores.
        
        Returns:
            str: Opção escolhida pelo usuário
        """
        print("\nMENU PRINCIPAL (ADMINISTRADOR)")
        print("1. Monitoramento de Preços")
        print("2. Gestão de Clientes")
        print("3. Administração")
        print("4. Ferramentas")
        print("L. Logout")
        print("0. Sair")
        
        opcao = input("\nEscolha uma opção: ")
        
        if opcao == '1':
            self.menu_monitoramento_precos_admin()
        elif opcao == '2':
            self.menu_gestao_clientes_admin()
        elif opcao == '3':
            self.menu_administracao_admin()
        elif opcao == '4':
            self.menu_ferramentas_admin()
        
        return opcao
    
    def menu_monitoramento_precos_admin(self):
        """Submenu de monitoramento de preços para administradores."""
        while True:
            self.limpar_tela()
            self.exibir_cabecalho()
            
            print("\nMONITORAMENTO DE PREÇOS (ADMINISTRADOR)")
            print("1. Adicionar produto")
            print("2. Listar todos os produtos")
            print("3. Remover produto")
            print("4. Executar monitoramento manual")
            print("5. Configurar agendamento automático")
            print("6. Visualizar fila de agendamento")
            print("7. Iniciar agendador automático")
            print("0. Voltar ao menu principal")
            
            opcao = input("\nEscolha uma opção (0-7): ")
            
            if opcao == '1':
                # Se não tiver cliente selecionado, pede para selecionar
                if not self.cliente_atual:
                    print("\nNenhum cliente selecionado. Por favor, selecione um cliente primeiro.")
                    if not self.selecionar_cliente():
                        continue  # Volta ao menu se não conseguir selecionar um cliente
                
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
                # Lista todos os produtos
                if self.cliente_atual:
                    print(f"\nListando produtos para o cliente: {self.cliente_atual}")
                    produtos = ProdutoController.listar_produtos(cliente=self.cliente_atual, usuario_atual=self.usuario_logado)
                else:
                    print("\nListando todos os produtos:")
                    produtos = ProdutoController.listar_produtos(usuario_atual=self.usuario_logado)
                
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
                # Interface para remover produto
                print("\nREMOVER PRODUTO")
                print("-" * 40)
                
                # Listar todos os produtos para escolha
                produtos = ProdutoController.listar_produtos(usuario_atual=self.usuario_logado)
                
                if not produtos:
                    print("Não há produtos cadastrados para remover.")
                    input("\nPressione Enter para continuar...")
                    continue
                
                print("Produtos monitorados:")
                for i, p in enumerate(produtos, 1):
                    grupo_txt = f" (Grupo: {p['grupo']})" if p['grupo'] else ""
                    print(f"{i}. Cliente: {p['cliente']} - Produto: {p['produto']} - Concorrente: {p['concorrente']}{grupo_txt}")
                
                escolha = input("Digite o número do produto que deseja remover (0 para cancelar): ")
                
                if escolha == "0":
                    continue
                    
                try:
                    indice = int(escolha) - 1
                    if 0 <= indice < len(produtos):
                        # Produto selecionado para remoção
                        produto_remover = produtos[indice]
                        
                        # Confirmar remoção
                        confirmar = input(f"Confirma a remoção do produto '{produto_remover['produto']}' do cliente '{produto_remover['cliente']}'? (s/n): ")
                        
                        if confirmar.lower() == 's':
                            resultado = ProdutoController.remover_produto(produto_remover['id'], usuario_atual=self.usuario_logado)
                            
                            if resultado:
                                print("Produto removido com sucesso!")
                            else:
                                print("Falha ao remover produto.")
                    else:
                        print("Opção inválida.")
                except ValueError:
                    print("Entrada inválida. Digite um número.")
                
                input("\nPressione Enter para continuar...")
                
            elif opcao == '4':
                # Executa monitoramento manual
                print("\nExecutando monitoramento manual de todos os produtos...")
                print("Nota: Isto verificará todos os produtos imediatamente, independente da fila de agendamento.")
                print("      Os produtos verificados manualmente serão removidos da fila do dia.")
                
                confirmar = input("Deseja continuar? (s/n): ")
                if confirmar.lower() == 's':
                    resultado = ProdutoController.monitorar_todos_produtos(
                        usuario_atual=self.usuario_logado, 
                        verificacao_manual=True
                    )
                    if resultado:
                        print("Monitoramento manual concluído com sucesso!")
                    else:
                        print("Monitoramento manual concluído, mas com possíveis falhas.")
                
                input("\nPressione Enter para continuar...")
                
            elif opcao == '5':
                # Configurar agendamento
                self.configurar_agendamento()
                input("\nPressione Enter para continuar...")
                
            elif opcao == '6':
                # Visualizar fila de agendamento
                self.visualizar_fila_agendamento()
                input("\nPressione Enter para continuar...")
                
            elif opcao == '7':
                # Iniciar agendador
                self.iniciar_agendador()
                
            elif opcao == '0':
                return
                
            else:
                print("Opção inválida. Tente novamente.")
                input("\nPressione Enter para continuar...")
    
    def menu_gestao_clientes_admin(self):
        """Submenu de gestão de clientes para administradores."""
        while True:
            self.limpar_tela()
            self.exibir_cabecalho()
            
            print("\nGESTÃO DE CLIENTES (ADMINISTRADOR)")
            print("1. Selecionar cliente")
            print("2. Adicionar cliente")
            print("3. Gerenciar todos os clientes")
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
                            
                        # Pergunta se deseja ver menu de administração para gerenciar grupos deste cliente
                        gerenciar = input("Deseja gerenciar grupos para este cliente? (s/n): ")
                        if gerenciar.lower() == 's':
                            self.menu_gerenciar_grupos()
                    else:
                        print("\nErro ao adicionar cliente.")
                else:
                    print("\nNome de cliente inválido.")
                    
                input("\nPressione Enter para continuar...")
                
            elif opcao == '3':
                # Lista todos os clientes (admin vê todos)
                self.gerenciar_todos_clientes()
                
            elif opcao == '0':
                return
                
            else:
                print("Opção inválida. Tente novamente.")
                input("\nPressione Enter para continuar...")
    
    def gerenciar_todos_clientes(self):
        """Interface para gerenciar todos os clientes."""
        todos_clientes = ClienteController.listar_clientes(usuario_atual=self.usuario_logado)
        
        if todos_clientes:
            print("\nTodos os clientes:")
            for i, cliente in enumerate(todos_clientes, 1):
                marcador = "* " if cliente['nome'] == self.cliente_atual else "  "
                print(f"{marcador}{i}. {cliente['nome']}")
                
            print("\n* Cliente atualmente selecionado")
            
            # Opções adicionais para administradores
            print("\nOpções:")
            print("1. Associar cliente a um grupo")
            print("2. Ver histórico de um cliente")
            print("0. Voltar")
            
            sub_opcao = input("\nEscolha uma opção (0-2): ")
            
            if sub_opcao == '1':
                # Gerenciar grupos
                self.menu_gerenciar_grupos()
            elif sub_opcao == '2':
                # Selecionar cliente para ver histórico
                try:
                    escolha = int(input("\nDigite o número do cliente para ver histórico (0 para cancelar): "))
                    
                    if escolha == 0:
                        return
                    
                    if 1 <= escolha <= len(todos_clientes):
                        cliente_escolhido = todos_clientes[escolha-1]['nome']
                        # Guardar cliente atual original
                        cliente_original = self.cliente_atual
                        
                        # Temporariamente mudar para o cliente escolhido
                        self.cliente_atual = cliente_escolhido
                        self.visualizar_historico()
                        
                        # Restaurar cliente original
                        self.cliente_atual = cliente_original
                    else:
                        print("Opção inválida.")
                except ValueError:
                    print("Entrada inválida!")
        else:
            print("\nNenhum cliente cadastrado.")
            
        input("\nPressione Enter para continuar...")
    
    def menu_administracao_admin(self):
        """Submenu de administração para administradores."""
        while True:
            self.limpar_tela()
            self.exibir_cabecalho()
            
            print("\nADMINISTRAÇÃO")
            print("1. Gerenciar usuários")
            print("2. Gerenciar grupos")
            print("3. Domínios e seletores")
            print("4. Backup do sistema")
            print("5. Relatórios de atividade")
            print("0. Voltar ao menu principal")
            
            opcao = input("\nEscolha uma opção (0-5): ")
            
            if opcao == '1':
                # Gerenciar usuários
                self.menu_gerenciar_usuarios()
                
            elif opcao == '2':
                # Gerenciar grupos
                self.menu_gerenciar_grupos()
                
            elif opcao == '3':
                # Gerenciar domínios e seletores
                self.menu_gerenciar_dominios()
                
            elif opcao == '4':
                # Criar backup do sistema
                self.criar_backup_sistema()
                input("\nPressione Enter para continuar...")
                
            elif opcao == '5':
                # Relatórios de atividade
                self.relatorio_atividade_sistema()
                
            elif opcao == '0':
                return
                
            else:
                print("Opção inválida. Tente novamente.")
                input("\nPressione Enter para continuar...")
    
    def menu_gerenciar_usuarios(self):
        """Interface para gerenciar usuários do sistema."""
        while True:
            self.limpar_tela()
            self.exibir_cabecalho()
            
            print("\nGERENCIAMENTO DE USUÁRIOS")
            print("1. Listar todos os usuários")
            print("2. Adicionar novo usuário")
            print("3. Desativar usuário")
            print("4. Alterar senha de usuário")
            print("0. Voltar ao menu anterior")
            
            opcao = input("\nEscolha uma opção (0-4): ")
            
            if opcao == '1':
                # Lista todos os usuários do sistema
                print("\nLISTA DE USUÁRIOS")
                print("-" * 50)
                print(f"{'Username':<15} | {'Nome':<25} | {'Tipo':<10} | {'Status':<8}")
                print("-" * 50)
                
                mostrar_inativos = input("Mostrar usuários inativos? (s/n): ").lower() == 's'
                usuarios = AuthController.listar_usuarios(mostrar_inativos)
                
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
                
                resultado = AuthController.adicionar_usuario(username, senha, nome, tipo, self.usuario_logado)
                
                if resultado:
                    print(f"\nUsuário '{username}' adicionado com sucesso!")
                else:
                    print("\nFalha ao adicionar usuário. Verifique se o username já existe.")
                
                input("\nPressione Enter para continuar...")
                
            elif opcao == '3':
                # Desativa um usuário existente
                print("\nDESATIVAR USUÁRIO")
                print("-" * 50)
                
                # Lista usuários ativos para facilitar a escolha
                usuarios = AuthController.listar_usuarios(False)  # Apenas usuários ativos
                
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
                        if usuario_escolhido == self.usuario_logado:
                            print("\nVocê não pode desativar seu próprio usuário!")
                            input("\nPressione Enter para continuar...")
                            continue
                        
                        # Confirma a desativação
                        confirmacao = input(f"Tem certeza que deseja desativar '{usuario_escolhido}'? (s/n): ")
                        
                        if confirmacao.lower() == 's':
                            resultado = AuthController.desativar_usuario(usuario_escolhido, self.usuario_logado)
                            
                            if resultado:
                                print(f"\nUsuário '{usuario_escolhido}' desativado com sucesso!")
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
                usuarios = AuthController.listar_usuarios(True)  # Inclui usuários inativos
                
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
                        nova_senha = input("Digite a nova senha: ")
                        confirma_senha = input("Confirme a nova senha: ")
                        
                        if nova_senha == confirma_senha:
                            resultado = AuthController.alterar_senha_admin(usuario_escolhido, nova_senha, self.usuario_logado)
                            
                            if resultado:
                                print(f"\nSenha do usuário '{usuario_escolhido}' alterada com sucesso!")
                            else:
                                print("\nErro ao alterar senha.")
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
    
    def menu_gerenciar_grupos(self):
        """Interface para gerenciar grupos do sistema."""
        while True:
            self.limpar_tela()
            self.exibir_cabecalho()
            
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
                from models.grupo import Grupo
                grupos = Grupo.listar_todos()
                
                print("\nGRUPOS CADASTRADOS:")
                print("-" * 60)
                
                for grupo in grupos:
                    print(f"ID: {grupo.id_grupo}")
                    print(f"Nome: {grupo.nome}")
                    print(f"Descrição: {grupo.descricao}")
                    
                    # Obter clientes e usuários
                    clientes = grupo.obter_clientes()
                    usuarios = grupo.obter_usuarios()
                    
                    print(f"Clientes: {', '.join([c['nome'] for c in clientes]) if clientes else 'Nenhum'}")
                    print(f"Usuários: {', '.join([u['username'] for u in usuarios]) if usuarios else 'Nenhum'}")
                    print("-" * 60)
                
                input("\nPressione Enter para continuar...")
                
            elif opcao == '0':
                return
            # ... implementar as outras opções
    
    def menu_gerenciar_dominios(self):
        """Interface para gerenciar domínios e seletores."""
        while True:
            self.limpar_tela()
            self.exibir_cabecalho()
            
            print("\nGERENCIAMENTO DE DOMÍNIOS E SELETORES")
            print("1. Listar domínios cadastrados")
            print("2. Adicionar novo domínio/seletor")
            print("3. Testar seletor em URL")
            print("4. Listar plataformas")
            print("5. Adicionar plataforma")
            print("0. Voltar ao menu anterior")
            
            opcao = input("\nEscolha uma opção (0-5): ")
            
            if opcao == '1':
                # Listar domínios cadastrados
                self.listar_dominios()
                input("\nPressione Enter para continuar...")
                
            elif opcao == '2':
                # Adicionar novo domínio/seletor
                self.adicionar_dominio()
                input("\nPressione Enter para continuar...")
                
            elif opcao == '3':
                # Testar seletor em URL
                self.testar_seletor()
                input("\nPressione Enter para continuar...")
                
            elif opcao == '4':
                # Listar plataformas
                self.listar_plataformas()
                input("\nPressione Enter para continuar...")
                
            elif opcao == '5':
                # Adicionar plataforma
                self.adicionar_plataforma()
                input("\nPressione Enter para continuar...")
                
            elif opcao == '0':
                return
                
            else:
                print("Opção inválida. Tente novamente.")
                input("\nPressione Enter para continuar...")
    
    def menu_ferramentas_admin(self):
        """Submenu de ferramentas para administradores."""
        while True:
            self.limpar_tela()
            self.exibir_cabecalho()
            
            print("\nFERRAMENTAS DE ADMINISTRAÇÃO")
            print("1. Criar backup do sistema")
            print("2. Verificar estrutura do banco")
            print("3. Otimizar banco de dados")
            print("4. Reconstruir índices")
            print("5. Relatório de atividade")
            print("0. Voltar ao menu anterior")
            
            opcao = input("\nEscolha uma opção (0-5): ")
            
            if opcao == '1':
                # Criar backup
                self.criar_backup_sistema()
                input("\nPressione Enter para continuar...")
                
            elif opcao == '2':
                # Verificar estrutura do banco
                self.verificar_estrutura_banco()
                input("\nPressione Enter para continuar...")
                
            elif opcao == '3':
                # Otimizar banco de dados
                self.otimizar_banco()
                input("\nPressione Enter para continuar...")
                
            elif opcao == '4':
                # Reconstruir índices
                self.reconstruir_indices()
                input("\nPressione Enter para continuar...")
                
            elif opcao == '5':
                # Relatório de atividade
                self.relatorio_atividade_sistema()
                input("\nPressione Enter para continuar...")
                
            elif opcao == '0':
                return
                
            else:
                print("Opção inválida. Tente novamente.")
                input("\nPressione Enter para continuar...")
    
    def configurar_agendamento(self):
        """Interface para configurar o agendamento automático."""
        print("\nCONFIGURAR AGENDAMENTO AUTOMÁTICO")
        print("-" * 60)
        
        try:
            from controllers.scheduler_controller import SchedulerController
            
            # Obter configuração atual
            config = SchedulerController.obter_configuracao_agendamento()
            
            if config:
                print("Configuração atual:")
                print(f"Tipo: {config['tipo']}")
                print(f"Dias: {', '.join(config['dias']) if config['dias'] else 'Nenhum'}")
                print(f"Horário: {config['horario']}")
                print(f"Status: {'Ativo' if config['ativo'] else 'Inativo'}")
                print(f"Última execução: {config['ultima_execucao'] or 'Nunca'}")
            else:
                print("Nenhuma configuração de agendamento encontrada.")
            
            print("\nNova configuração:")
            
            # Seleção de dias da semana
            print("\nSelecione os dias da semana para execução:")
            print("1. Segunda-feira")
            print("2. Terça-feira")
            print("3. Quarta-feira")
            print("4. Quinta-feira")
            print("5. Sexta-feira")
            print("6. Sábado")
            print("7. Domingo")
            print("0. Confirmar seleção")
            
            dias_mapeamento = {
                '1': 'segunda',
                '2': 'terca',
                '3': 'quarta',
                '4': 'quinta',
                '5': 'sexta',
                '6': 'sabado',
                '7': 'domingo'
            }
            
            dias_selecionados = []
            
            while True:
                escolha = input("\nAdicione um dia ou confirme (0): ")
                
                if escolha == '0':
                    break
                    
                if escolha in dias_mapeamento and dias_mapeamento[escolha] not in dias_selecionados:
                    dias_selecionados.append(dias_mapeamento[escolha])
                    print(f"Dias selecionados: {', '.join(dias_selecionados)}")
            
            # Se nenhum dia foi selecionado, pergunte se deseja continuar
            if not dias_selecionados:
                continuar = input("Nenhum dia selecionado. Deseja continuar mesmo assim? (s/n): ")
                if continuar.lower() != 's':
                    print("Configuração cancelada.")
                    return
            
            # Horário de execução
            from utils.validators import Validators
            
            horario_valido = False
            while not horario_valido:
                horario = input("\nHorário de execução (formato HH:MM): ")
                
                if Validators.validar_formato_hora(horario):
                    horario_valido = True
                else:
                    print("Formato de hora inválido. Use o formato HH:MM (ex: 08:30)")
            
            # Configurar o agendamento
            resultado = SchedulerController.configurar_agendamento(dias_selecionados, horario)
            
            if resultado:
                print("\nAgendamento configurado com sucesso!")
                print(f"Dias: {', '.join(dias_selecionados) if dias_selecionados else 'Nenhum'}")
                print(f"Horário: {horario}")
            else:
                print("\nErro ao configurar agendamento.")
            
        except Exception as e:
            Logger.log(f"Erro ao configurar agendamento: {e}", "ERROR")
            print(f"Erro ao configurar agendamento: {e}")
    
    def visualizar_fila_agendamento(self):
        """Interface para visualizar a fila de agendamento."""
        print("\nFILA DE AGENDAMENTO")
        print("-" * 60)
        
        try:
            # Importar o controller de agendamento
            from controllers.scheduler_controller import SchedulerController
            
            # Obter produtos na fila
            produtos_ids = SchedulerController.obter_proximos_produtos_fila(100)  # Busca até 100 produtos
            
            if not produtos_ids:
                print("Não há produtos na fila de agendamento.")
                return
            
            print(f"Total de produtos na fila: {len(produtos_ids)}")
            print("\nPosição | Produto | Cliente | Concorrente | Última verificação")
            print("-" * 80)
            
            from models.produto import Produto
            from models.cliente import Cliente
            
            # Buscar informações detalhadas de cada produto
            for i, id_produto in enumerate(produtos_ids, 1):
                produto = Produto.buscar_por_id(id_produto)
                
                if produto:
                    # Buscar nome do cliente
                    cliente = Cliente.buscar_por_id(produto.id_cliente)
                    nome_cliente = cliente.nome if cliente else "Desconhecido"
                    
                    # Buscar data da última verificação
                    db = DatabaseConnector()
                    conexao, cursor = db.criar_conexao()
                    
                    cursor.execute('''
                    SELECT ultima_verificacao, verificacao_manual 
                    FROM fila_agendamento 
                    WHERE id_produto = ?
                    ''', (produto.id,))
                    
                    resultado = cursor.fetchone()
                    conexao.close()
                    
                    ultima_verificacao = resultado['ultima_verificacao'] if resultado and resultado['ultima_verificacao'] else "Nunca"
                    verificacao_manual = "(Manual)" if resultado and resultado['verificacao_manual'] == 1 else ""
                    
                    print(f"{i:<7} | {produto.nome[:20]:<20} | {nome_cliente[:15]:<15} | {produto.concorrente[:20]:<20} | {ultima_verificacao} {verificacao_manual}")
            
            # Mostrar informações adicionais
            print("\nInformações:")
            print("- Os produtos são verificados na ordem da fila")
            print("- Produtos verificados manualmente não são verificados automaticamente no mesmo dia")
            print("- Após verificação, o produto vai para o final da fila")
            
        except Exception as e:
            Logger.log(f"Erro ao visualizar fila de agendamento: {e}", "ERROR")
            print(f"Erro ao visualizar fila: {e}")
    
    def iniciar_agendador(self):
        """Interface para iniciar o agendador automático."""
        print("\nINICIAR AGENDADOR AUTOMÁTICO")
        print("-" * 60)
        print("ATENÇÃO: Esta operação iniciará o agendador em modo contínuo.")
        print("O sistema executará o monitoramento de preços nos dias e horários configurados.")
        print("Para encerrar o agendador, pressione Ctrl+C.\n")
        
        confirmar = input("Deseja iniciar o agendador agora? (s/n): ")
        
        if confirmar.lower() != 's':
            return
        
        try:
            from controllers.scheduler_controller import SchedulerController
            
            # Verificar se existe configuração
            config = SchedulerController.obter_configuracao_agendamento()
            
            if not config:
                print("\nNenhuma configuração de agendamento encontrada.")
                print("Por favor, configure o agendamento primeiro.")
                return
            
            if not config['ativo']:
                print("\nO agendamento está desativado. Deseja ativá-lo?")
                ativar = input("(s/n): ")
                
                if ativar.lower() == 's':
                    # Ativar o agendamento (essa função precisaria ser implementada)
                    # SchedulerController.ativar_agendamento()
                    pass
                else:
                    print("Operação cancelada.")
                    return
            
            print("\nIniciando agendador...")
            print(f"Configuração: {', '.join(config['dias'])} às {config['horario']}")
            print("\nO agendador está em execução. Pressione Ctrl+C para encerrar.")
            
            # Executar o agendador
            SchedulerController.executar_agendador()
            
        except KeyboardInterrupt:
            print("\nAgendador interrompido pelo usuário.")
        except Exception as e:
            Logger.log(f"Erro ao iniciar agendador: {e}", "ERROR")
            print(f"Erro ao iniciar agendador: {e}")
    
    def criar_backup_sistema(self):
        """Cria um backup completo do sistema."""
        print("\nCRIAR BACKUP DO SISTEMA")
        print("-" * 60)
        
        try:
            from controllers.admin_controller import AdminController
            
            print("Criando backup do sistema...")
            resultado = AdminController.criar_backup()
            
            if resultado:
                print("\nBackup criado com sucesso!")
            else:
                print("\nErro ao criar backup.")
                
        except Exception as e:
            Logger.log(f"Erro ao criar backup: {e}", "ERROR")
            print(f"Erro ao criar backup: {e}")
    
    def relatorio_atividade_sistema(self):
        """Gera um relatório de atividade do sistema."""
        print("\nRELATÓRIO DE ATIVIDADE DO SISTEMA")
        print("-" * 60)
        
        try:
            from controllers.admin_controller import AdminController
            
            # Solicitar o período do relatório
            print("\nSelecione o período do relatório:")
            print("1. Últimas 24 horas")
            print("2. Últimos 7 dias")
            print("3. Últimos 30 dias")
            print("4. Todo o histórico")
            
            opcao = input("\nEscolha uma opção (1-4): ")
            
            periodo = '24h'  # Valor padrão
            
            if opcao == '1':
                periodo = '24h'
            elif opcao == '2':
                periodo = '7d'
            elif opcao == '3':
                periodo = '30d'
            elif opcao == '4':
                periodo = 'all'
            else:
                print("Opção inválida. Usando período padrão (24h).")
            
            # Gerar o relatório
            print(f"\nGerando relatório para {periodo}...")
            relatorio = AdminController.relatorio_atividade(periodo)
            
            if relatorio and 'erro' not in relatorio:
                print(f"\nRELATÓRIO DE ATIVIDADE - {relatorio['periodo']}")
                print("-" * 60)
                print(f"Total de eventos: {relatorio['total_eventos']}")
                
                # Distribuição por nível
                print("\nDistribuição por nível:")
                for nivel, qtd in relatorio['distribuicao_nivel'].items():
                    print(f"- {nivel}: {qtd}")
                
                # Informações de login
                print(f"\nLogins: {relatorio['logins']['total']}")
                if relatorio['logins']['recentes']:
                    print("\nLogins recentes:")
                    for login in relatorio['logins']['recentes']:
                        print(f"- {login.strip()}")
                
                # Informações de monitoramento
                print(f"\nMonitoramentos: {relatorio['monitoramentos']['total']}")
                if relatorio['monitoramentos']['recentes']:
                    print("\nMonitoramentos recentes:")
                    for monitoramento in relatorio['monitoramentos']['recentes']:
                        print(f"- {monitoramento.strip()}")
            else:
                erro = relatorio.get('erro', 'Erro desconhecido ao gerar relatório.')
                print(f"\nErro ao gerar relatório: {erro}")
                
        except Exception as e:
            Logger.log(f"Erro ao gerar relatório de atividade: {e}", "ERROR")
            print(f"Erro ao gerar relatório de atividade: {e}")
    
    def listar_dominios(self):
        """Lista os domínios e seletores cadastrados."""
        print("\nDOMÍNIOS CADASTRADOS")
        print("-" * 60)
        
        try:
            db = DatabaseConnector()
            conexao, cursor = db.criar_conexao()
            
            cursor.execute("SELECT id, nome, seletor_css, data_criacao FROM dominios ORDER BY nome")
            dominios = cursor.fetchall()
            
            conexao.close()
            
            if dominios:
                print(f"{'ID':<5} | {'Domínio':<30} | {'Seletor CSS':<40} | {'Data Criação':<20}")
                print("-" * 100)
                
                for d in dominios:
                    print(f"{d['id']:<5} | {d['nome'][:30]:<30} | {d['seletor_css'][:40]:<40} | {d['data_criacao'][:20]:<20}")
                    
                print(f"\nTotal: {len(dominios)} domínios")
            else:
                print("Nenhum domínio cadastrado.")
                
        except Exception as e:
            Logger.log(f"Erro ao listar domínios: {e}", "ERROR")
            print(f"Erro ao listar domínios: {e}")

    def adicionar_dominio(self):
        """Adiciona um novo domínio com seletor CSS."""
        print("\nADICIONAR NOVO DOMÍNIO")
        print("-" * 60)
        
        try:
            dominio = input("Domínio (ex: amazon.com.br): ")
            seletor = input("Seletor CSS para preço: ")
            
            if not dominio or not seletor:
                print("Domínio e seletor são obrigatórios.")
                return
            
            from scraper.price_scraper import PriceScraper
            scraper = PriceScraper()
            
            # Salvar o seletor
            resultado = scraper.salvar_seletor(dominio, seletor)
            
            if resultado:
                print(f"\nDomínio '{dominio}' cadastrado com sucesso!")
                
                # Perguntar se deseja testar o seletor
                testar = input("Deseja testar o seletor agora? (s/n): ")
                if testar.lower() == 's':
                    self.testar_seletor(dominio, seletor)
            else:
                print("\nErro ao cadastrar domínio.")
                
        except Exception as e:
            Logger.log(f"Erro ao adicionar domínio: {e}", "ERROR")
            print(f"Erro ao adicionar domínio: {e}")

    def testar_seletor(self, dominio=None, seletor=None):
        """Testa um seletor CSS em uma URL."""
        print("\nTESTAR SELETOR CSS")
        print("-" * 60)
        
        try:
            if not dominio:
                url = input("URL do produto: ")
                seletor = input("Seletor CSS para preço: ")
            else:
                url = input(f"URL de produto em {dominio}: ")
            
            if not url:
                print("URL é obrigatória.")
                return
                
            from scraper.price_scraper import PriceScraper
            scraper = PriceScraper()
            
            print("\nTestando seletor...")
            preco_texto = scraper.extrair_preco(url, seletor)
            
            if preco_texto:
                valor = scraper.converter_preco(preco_texto)
                print(f"\nSeletor funcionou! Preço encontrado: {preco_texto}")
                if valor is not None:
                    print(f"Valor numérico: R$ {valor:.2f}")
            else:
                print("\nSeletor não encontrou o preço. Verifique a URL e o seletor.")
                
        except Exception as e:
            Logger.log(f"Erro ao testar seletor: {e}", "ERROR")
            print(f"Erro ao testar seletor: {e}")
            
    def listar_plataformas(self):
        """Lista as plataformas cadastradas."""
        print("\nPLATAFORMAS CADASTRADAS")
        print("-" * 60)
        
        try:
            db = DatabaseConnector()
            conexao, cursor = db.criar_conexao()
            
            cursor.execute("SELECT id, nome, seletor_css, data_criacao FROM plataformas ORDER BY nome")
            plataformas = cursor.fetchall()
            
            conexao.close()
            
            if plataformas:
                print(f"{'ID':<5} | {'Nome':<30} | {'Seletor CSS':<40} | {'Data Criação':<20}")
                print("-" * 100)
                
                for p in plataformas:
                    print(f"{p['id']:<5} | {p['nome'][:30]:<30} | {p['seletor_css'][:40]:<40} | {p['data_criacao'][:20]:<20}")
                    
                print(f"\nTotal: {len(plataformas)} plataformas")
            else:
                print("Nenhuma plataforma cadastrada.")
                
        except Exception as e:
            Logger.log(f"Erro ao listar plataformas: {e}", "ERROR")
            print(f"Erro ao listar plataformas: {e}")
    
    def adicionar_plataforma(self):
        """Adiciona uma nova plataforma."""
        print("\nADICIONAR NOVA PLATAFORMA")
        print("-" * 60)
        
        try:
            nome = input("Nome da plataforma (ex: Shopify, WooCommerce): ")
            seletor = input("Seletor CSS padrão para preço: ")
            
            if not nome or not seletor:
                print("Nome e seletor são obrigatórios.")
                return
            
            from scraper.price_scraper import PriceScraper
            scraper = PriceScraper()
            
            # Salvar a plataforma
            id_plataforma = scraper.salvar_plataforma(nome, seletor)
            
            if id_plataforma:
                print(f"\nPlataforma '{nome}' cadastrada com sucesso!")
            else:
                print("\nErro ao cadastrar plataforma.")
                
        except Exception as e:
            Logger.log(f"Erro ao adicionar plataforma: {e}", "ERROR")
            print(f"Erro ao adicionar plataforma: {e}")
    
    def verificar_estrutura_banco(self):
        """Verifica a estrutura do banco de dados."""
        print("\nVERIFICAR ESTRUTURA DO BANCO DE DADOS")
        print("-" * 60)
        
        try:
            from controllers.admin_controller import AdminController
            
            print("Verificando estrutura do banco de dados...")
            resultado = AdminController.validar_estrutura_banco()
            
            if resultado and 'erro' not in resultado:
                print("\nEstrutura do banco de dados:")
                
                # Tabelas
                print("\nTabelas:")
                for tabela, info in resultado['tabelas'].items():
                    print(f"- {tabela}: {info['colunas']} colunas")
                    print(f"  Colunas: {', '.join(info['estrutura'])}")
                
                # Índices
                print("\nÍndices:")
                for indice, info in resultado['indices'].items():
                    print(f"- {indice} (tabela: {info['tabela']})")
                
                # Integridade
                print(f"\nIntegridade do banco: {resultado['integridade']}")
                
                if resultado['integridade'] == 'ok':
                    print("O banco de dados está íntegro.")
                else:
                    print("Foram encontrados problemas de integridade no banco de dados.")
            else:
                erro = resultado.get('erro', 'Erro desconhecido ao verificar banco.')
                print(f"\nErro ao verificar estrutura do banco: {erro}")
                
        except Exception as e:
            Logger.log(f"Erro ao verificar estrutura do banco: {e}", "ERROR")
            print(f"Erro ao verificar estrutura do banco: {e}")
    
    def otimizar_banco(self):
        """Otimiza o banco de dados."""
        print("\nOTIMIZAR BANCO DE DADOS")
        print("-" * 60)
        
        try:
            from controllers.admin_controller import AdminController
            
            confirmar = input("Deseja otimizar o banco de dados agora? (s/n): ")
            
            if confirmar.lower() != 's':
                print("Operação cancelada.")
                return
            
            print("\nOtimizando banco de dados (VACUUM)...")
            resultado = AdminController.otimizar_banco()
            
            if resultado:
                print("Banco de dados otimizado com sucesso!")
            else:
                print("Erro ao otimizar banco de dados.")
                
        except Exception as e:
            Logger.log(f"Erro ao otimizar banco de dados: {e}", "ERROR")
            print(f"Erro ao otimizar banco de dados: {e}")
    
    def reconstruir_indices(self):
        """Reconstrói os índices do banco de dados."""
        print("\nRECONSTRUIR ÍNDICES DO BANCO DE DADOS")
        print("-" * 60)
        
        try:
            from controllers.admin_controller import AdminController
            
            confirmar = input("Deseja reconstruir os índices do banco de dados agora? (s/n): ")
            
            if confirmar.lower() != 's':
                print("Operação cancelada.")
                return
            
            print("\nReconstruindo índices...")
            resultado = AdminController.reconstruir_indices()
            
            if resultado:
                print("Índices reconstruídos com sucesso!")
            else:
                print("Erro ao reconstruir índices.")
                
        except Exception as e:
            Logger.log(f"Erro ao reconstruir índices: {e}", "ERROR")
            print(f"Erro ao reconstruir índices: {e}")