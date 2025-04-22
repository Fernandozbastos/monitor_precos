#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo de interface para o menu principal do sistema.
"""

import os
import sys
import time
from utils.logger import Logger
from views.admin_view import AdminView
from views.usuario_view import UsuarioView
from controllers.auth_controller import AuthController

class MenuView:
    def __init__(self):
        self.usuario_logado = None
        self.tipo_usuario = None
        self.cliente_atual = None
    
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
            from controllers.auth_controller import AuthController
            grupos = AuthController.obter_grupos_usuario(self.usuario_logado)
            grupos_str = ", ".join(grupos) if grupos else "Nenhum"
            print(f"Usuário: {self.usuario_logado} ({self.tipo_usuario})")
            
            if self.cliente_atual:
                print(f"Cliente atual: {self.cliente_atual}")
            else:
                print("Cliente atual: Nenhum selecionado")
        print("-" * 60)
    
    def fazer_login(self):
        """
        Solicita as credenciais do usuário e realiza o login.
        
        Returns:
            bool: True se o login foi bem-sucedido, False caso contrário
        """
        print("\n=== LOGIN ===")
        
        # Solicita as credenciais
        tentativas = 0
        max_tentativas = 3
        
        while tentativas < max_tentativas:
            username = input("Usuário: ")
            try:
                import getpass
                senha = getpass.getpass("Senha: ")
            except Exception:
                # Fallback caso getpass não funcione no ambiente
                senha = input("Senha (visível): ")
            
            sucesso, usuario, tipo, cliente_atual = AuthController.autenticar(username, senha)
            
            if sucesso:
                self.usuario_logado = username
                self.tipo_usuario = tipo
                self.cliente_atual = cliente_atual
                print(f"\nBem-vindo, {username}!")
                
                # Se tiver um cliente anterior, usa-o como cliente atual
                if self.cliente_atual:
                    print(f"Cliente '{self.cliente_atual}' selecionado automaticamente.")
                
                return True
            else:
                tentativas += 1
                restantes = max_tentativas - tentativas
                if restantes > 0:
                    print(f"Credenciais inválidas. Você tem mais {restantes} tentativa(s).")
                else:
                    print("Número máximo de tentativas excedido.")
        
        return False
    
    def fazer_logout(self):
        """
        Realiza o logout do usuário atual.
        
        Returns:
            bool: True se o logout foi realizado com sucesso, False caso contrário
        """
        if self.usuario_logado:
            Logger.log(f"Usuário {self.usuario_logado} fez logout", "INFO")
            self.usuario_logado = None
            self.tipo_usuario = None
            self.cliente_atual = None
            print("\nLogout realizado com sucesso!")
            return True
        return False
    
    def iniciar(self):
        """
        Inicia o fluxo principal do sistema.
        """
        # Inicializar o banco de dados
        from database.connector import DatabaseConnector
        db = DatabaseConnector()
        if not db.inicializar_banco_dados():
            print("Falha ao inicializar banco de dados. O programa será encerrado.")
            sys.exit(1)
        
        # Solicita login antes de mostrar o menu principal
        if not self.fazer_login():
            print("\nNão foi possível realizar o login. O programa será encerrado.")
            sys.exit(1)
        
        # Loop principal do menu
        while True:
            try:
                # Limpa a tela 
                self.limpar_tela()
                self.exibir_cabecalho()
                
                # Direciona para a view específica conforme o tipo de usuário
                if self.tipo_usuario == 'admin':
                    admin_view = AdminView(self.usuario_logado, self.tipo_usuario, self.cliente_atual)
                    opcao = admin_view.exibir_menu_principal()
                else:
                    usuario_view = UsuarioView(self.usuario_logado, self.tipo_usuario, self.cliente_atual)
                    opcao = usuario_view.exibir_menu_principal()
                
                # Opções comuns para todos os tipos de usuário
                if opcao == '0':
                    print("\nSaindo do sistema. Até logo!")
                    Logger.log(f"Sistema encerrado pelo usuário {self.usuario_logado}", "INFO")
                    sys.exit(0)
                    
                elif opcao.upper() == 'L':
                    # Logout
                    logout_sucesso = self.fazer_logout()
                    
                    if logout_sucesso:
                        # Após logout, solicita novo login
                        if not self.fazer_login():
                            print("\nNão foi possível realizar o login. O programa será encerrado.")
                            Logger.log("Tentativa de login após logout falhou", "WARNING")
                            sys.exit(1)
                # Menu para administradores
                elif self.tipo_usuario == 'admin':
                    # As opções específicas são tratadas na AdminView
                    pass
                # Menu para usuários regulares
                else:
                    # As opções específicas são tratadas na UsuarioView
                    pass
                    
            except KeyboardInterrupt:
                print("\n\nOperação interrompida pelo usuário.")
                continuar = input("Deseja voltar ao menu principal? (s/n): ")
                if continuar.lower() != 's':
                    print("\nSaindo do sistema. Até logo!")
                    Logger.log(f"Sistema encerrado pelo usuário {self.usuario_logado} (KeyboardInterrupt)", "INFO")
                    sys.exit(0)
                    
            except Exception as e:
                erro = f"Erro inesperado: {str(e)}"
                print(f"\n{erro}")
                Logger.log(erro, "ERROR")
                input("\nPressione Enter para continuar...")