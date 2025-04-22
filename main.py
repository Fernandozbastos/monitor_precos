#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Sistema de Monitoramento de Preços
----------------------------------
Este programa monitora preços de produtos em sites de concorrentes
e registra o histórico de variações para análise competitiva.
Versão com arquitetura MVC para melhor organização e manutenção.
"""

import sys
from utils.logger import Logger
from views.menu_view import MenuView

def verificar_dependencias():
    """Verifica se todas as dependências estão instaladas."""
    dependencias = {
        'requests': 'Para realizar requisições HTTP',
        'bs4': 'Para parsing de HTML',
        'selenium': 'Para extração em sites dinâmicos',
        'webdriver_manager': 'Para gerenciar o ChromeDriver',
        'schedule': 'Para agendamento de tarefas'
    }
    
    faltando = []
    
    for pacote, descricao in dependencias.items():
        try:
            __import__(pacote)
        except ImportError:
            faltando.append(f"{pacote} ({descricao})")
    
    if faltando:
        print("Dependências faltando:")
        for dep in faltando:
            print(f"- {dep}")
        print("\nInstale com o comando:")
        print(f"pip install {' '.join([p.split(' ')[0] for p in faltando])}")
        return False
    
    return True

def iniciar_sistema():
    """Função principal que inicia o sistema."""
    try:
        # Verificar dependências
        if not verificar_dependencias():
            sys.exit(1)
        
        Logger.log("Sistema iniciado", "INFO")
        
        # Iniciar interface principal
        menu = MenuView()
        menu.iniciar()
        
    except KeyboardInterrupt:
        print("\nPrograma encerrado pelo usuário.")
        Logger.log("Programa encerrado pelo usuário (KeyboardInterrupt)", "INFO")
        sys.exit(0)
        
    except Exception as e:
        print(f"\nErro fatal: {str(e)}")
        Logger.log(f"Erro fatal: {str(e)}", "ERROR")
        sys.exit(1)

if __name__ == "__main__":
    iniciar_sistema()