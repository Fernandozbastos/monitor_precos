#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para migrar dados de arquivos CSV para banco de dados SQLite
-----------------------------------------------------------------
Este script realiza a migração completa do sistema de arquivos para banco de dados.
"""

import os
import sys
from database_config import inicializar_banco_dados, migrar_dados_csv_para_sqlite

def main():
    """Função principal para executar a migração."""
    print("=" * 50)
    print("MIGRAÇÃO PARA BANCO DE DADOS SQLITE")
    print("=" * 50)
    
    # Verificar se o banco de dados já existe
    if os.path.isfile('monitor_precos.db'):
        resposta = input("Um banco de dados já existe. Deseja sobrescrevê-lo? (s/n): ")
        if resposta.lower() != 's':
            print("Migração cancelada.")
            return
        
        try:
            os.rename('monitor_precos.db', 'monitor_precos.db.bak')
            print("Backup do banco de dados atual criado: monitor_precos.db.bak")
        except Exception as e:
            print(f"Erro ao criar backup do banco de dados: {e}")
            return
    
    print("\nPasso 1: Inicializando banco de dados...")
    if not inicializar_banco_dados():
        print("Falha ao inicializar banco de dados. Migração abortada.")
        return
    
    print("\nPasso 2: Migrando dados dos arquivos CSV para o banco de dados...")
    if not migrar_dados_csv_para_sqlite():
        print("Falha durante a migração de dados. O processo pode estar incompleto.")
        return
    
    # Criar flag para indicar que está usando banco de dados
    with open('usar_bd.flag', 'w') as f:
        f.write('1')
    
    print("\nMigração concluída com sucesso!")
    print("\nO sistema agora usará o banco de dados SQLite.")
    print("Os arquivos CSV originais não foram modificados e podem ser mantidos como backup.")
    
    resposta = input("\nDeseja iniciar o sistema agora? (s/n): ")
    if resposta.lower() == 's':
        # Tentar importar e executar o módulo main
        try:
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            from main import menu_principal
            menu_principal()
        except Exception as e:
            print(f"Erro ao iniciar o sistema: {e}")
            print("Por favor, inicie o sistema manualmente executando 'python main.py'")

if __name__ == "__main__":
    main()