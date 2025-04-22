#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de teste para o sistema de login
"""

import os
import sys
from auth import verificar_arquivo_usuarios, realizar_login

def main():
    print("\n=== TESTE DE LOGIN ===")
    print("Este script verifica se o sistema de login está funcionando corretamente.")
    
    print("\nVerificando arquivo de usuários...")
    resultado = verificar_arquivo_usuarios()
    
    if resultado:
        print("O arquivo de usuários existe ou foi criado com sucesso.")
        print("Informações de login padrão:")
        print("  Username: admin")
        print("  Senha: admin")
    else:
        print("ERRO: Não foi possível verificar ou criar o arquivo de usuários.")
        sys.exit(1)
    
    print("\nTentando realizar login...")
    sucesso, username, tipo = realizar_login()
    
    if sucesso:
        print(f"\nLogin realizado com sucesso!")
        print(f"Username: {username}")
        print(f"Tipo de usuário: {tipo}")
    else:
        print("\nFalha na tentativa de login.")
    
    input("\nPressione Enter para sair...")

if __name__ == "__main__":
    main()