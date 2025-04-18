#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo de acesso ao banco de dados para o Sistema de Monitoramento de Preços
---------------------------------------------------------------------------
Versão para banco de dados SQLite.
"""

import os
import pandas as pd
from database_config import criar_conexao
from scraper import extrair_dominio, extrair_preco
from utils import depurar_logs
from datetime import datetime

def carregar_plataformas_seletores():
    """
    Carrega o dicionário de plataformas e seus seletores CSS do banco de dados.
    
    Returns:
        dict: Dicionário com plataformas como chaves e seletores CSS como valores
    """
    try:
        conexao, cursor = criar_conexao()
        
        cursor.execute("SELECT nome, seletor_css FROM plataformas")
        resultados = cursor.fetchall()
        
        conexao.close()
        
        plataformas_seletores = {}
        for row in resultados:
            plataformas_seletores[row['nome']] = row['seletor_css']
        
        return plataformas_seletores
        
    except Exception as e:
        depurar_logs(f"Erro ao carregar plataformas e seletores: {e}", "ERROR")
        return {}

def salvar_plataformas_seletores(plataformas_seletores):
    """
    Salva o dicionário de plataformas e seletores CSS no banco de dados.
    
    Args:
        plataformas_seletores (dict): Dicionário com plataformas e seletores CSS
    """
    try:
        conexao, cursor = criar_conexao()
        data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        for plataforma, seletor in plataformas_seletores.items():
            # Verificar se a plataforma já existe
            cursor.execute("SELECT id FROM plataformas WHERE nome = ?", (plataforma,))
            resultado = cursor.fetchone()
            
            if resultado:
                # Atualizar seletor
                cursor.execute("UPDATE plataformas SET seletor_css = ? WHERE id = ?", 
                             (seletor, resultado['id']))
            else:
                # Inserir nova plataforma
                cursor.execute('''
                INSERT INTO plataformas (nome, seletor_css, data_criacao)
                VALUES (?, ?, ?)
                ''', (plataforma, seletor, data_atual))
        
        conexao.commit()
        conexao.close()
        
    except Exception as e:
        depurar_logs(f"Erro ao salvar plataformas e seletores: {e}", "ERROR")

def carregar_dominios_seletores():
    """
    Carrega o dicionário de domínios e seus seletores CSS do banco de dados.
    
    Returns:
        dict: Dicionário com domínios como chaves e seletores CSS como valores
    """
    try:
        conexao, cursor = criar_conexao()
        
        cursor.execute("SELECT nome, seletor_css FROM dominios")
        resultados = cursor.fetchall()
        
        conexao.close()
        
        dominios_seletores = {}
        for row in resultados:
            dominios_seletores[row['nome']] = row['seletor_css']
        
        return dominios_seletores
        
    except Exception as e:
        depurar_logs(f"Erro ao carregar domínios e seletores: {e}", "ERROR")
        return {}

def salvar_dominios_seletores(dominios_seletores):
    """
    Salva o dicionário de domínios e seletores CSS no banco de dados.
    
    Args:
        dominios_seletores (dict): Dicionário com domínios e seletores CSS
    """
    try:
        conexao, cursor = criar_conexao()
        data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        for dominio, seletor in dominios_seletores.items():
            # Verificar se o domínio já existe
            cursor.execute("SELECT id FROM dominios WHERE nome = ?", (dominio,))
            resultado = cursor.fetchone()
            
            if resultado:
                # Atualizar seletor
                cursor.execute("UPDATE dominios SET seletor_css = ? WHERE id = ?", 
                             (seletor, resultado['id']))
            else:
                # Inserir novo domínio
                cursor.execute('''
                INSERT INTO dominios (nome, seletor_css, data_criacao)
                VALUES (?, ?, ?)
                ''', (dominio, seletor, data_atual))
        
        conexao.commit()
        conexao.close()
        
    except Exception as e:
        depurar_logs(f"Erro ao salvar domínios e seletores: {e}", "ERROR")

def adicionar_produto(cliente=None, produto=None, concorrente=None, url=None, usuario_atual=None):
    """
    Adiciona um novo produto para monitoramento.
    Associa o produto a um grupo específico e cliente.
    
    Args:
        cliente (str, optional): Nome do cliente
        produto (str, optional): Nome do produto
        concorrente (str, optional): Nome do concorrente
        url (str, optional): URL do produto
        usuario_atual (str, optional): Nome do usuário que está adicionando o produto
        
    Returns:
        bool: True se o produto foi adicionado com sucesso, False caso contrário
    """
    from grupos_bd import usuario_pode_acessar_cliente, obter_grupos_usuario
    
    # Se não temos dados armazenados, pedimos ao usuário
    if cliente is None:
        cliente = input("Nome do cliente: ")
        
    # Verifica se o usuário tem permissão para adicionar produtos para este cliente
    if usuario_atual and not usuario_pode_acessar_cliente(usuario_atual, cliente):
        print(f"Você não tem permissão para adicionar produtos para o cliente '{cliente}'.")
        depurar_logs(f"Usuário {usuario_atual} tentou adicionar produto para cliente não autorizado: {cliente}", "WARNING")
        return False
        
    if produto is None:
        produto = input("Nome do produto: ")
    if concorrente is None:
        concorrente = input("Nome do concorrente: ")
    if url is None:
        url = input("URL do produto: ")
    
    # Determinar o grupo do usuário
    grupo_usuario = None
    if usuario_atual:
        if usuario_atual == "admin" or "admin" in obter_grupos_usuario(usuario_atual):
            grupo_usuario = "admin"
        else:
            grupos = obter_grupos_usuario(usuario_atual)
            # Filtra para obter apenas o grupo pessoal do usuário
            grupos_pessoais = [g for g in grupos if g != "all" and g != "admin"]
            if grupos_pessoais:
                grupo_usuario = grupos_pessoais[0]  # Usa o primeiro grupo pessoal encontrado
    
    if not grupo_usuario:
        grupo_usuario = "admin"  # Padrão se não encontrar grupo
    
    # Extrair o domínio da URL
    dominio = extrair_dominio(url)
    
    # NOVA FUNCIONALIDADE: Perguntar sobre a plataforma
    plataforma = input("Qual a plataforma de e-commerce? (Digite 'N' se não souber): ")
    
    # Carregar dicionário de domínios e seletores
    dominios_seletores = carregar_dominios_seletores()
    
    # Carregar dicionário de plataformas e seletores
    plataformas_seletores = carregar_plataformas_seletores()
    
    # Variável para armazenar o seletor CSS que será usado
    seletor_css = None
    
    try:
        conexao, cursor = criar_conexao()
        
        # Verificar se a URL já está sendo monitorada
        cursor.execute('''
        SELECT p.id, s.seletor_css 
        FROM produtos p
        JOIN dominios s ON s.nome = ?
        WHERE p.url = ?
        LIMIT 1
        ''', (dominio, url))
        
        resultado = cursor.fetchone()
        
        if resultado:
            # A URL já existe no sistema
            seletor_existente = resultado['seletor_css']
            print(f"\nEsta URL já está sendo monitorada com o seletor CSS: '{seletor_existente}'")
            
            usar_seletor_existente = input("Deseja usar o seletor existente? (s/n): ")
            if usar_seletor_existente.lower() == 's':
                seletor_css = seletor_existente
        
        # Se não encontrou a URL ou optou por não usar o seletor existente
        if seletor_css is None:
            # MODIFICAÇÃO: Verificar primeiramente pela plataforma, se informada
            if plataforma.upper() != 'N' and plataforma in plataformas_seletores:
                seletor_existente = plataformas_seletores[plataforma]
                print(f"\nA plataforma '{plataforma}' já tem um seletor CSS cadastrado: '{seletor_existente}'")
                
                usar_seletor_existente = input("Deseja usar o seletor existente? (s/n): ")
                if usar_seletor_existente.lower() == 's':
                    seletor_css = seletor_existente
                    
                    # Teste rápido para confirmar se o seletor existente funciona para esta URL
                    print(f"Testando seletor existente: {seletor_css}")
                    preco_teste = extrair_preco(url, seletor_css)
                    
                    if not preco_teste:
                        print("AVISO: O seletor existente não encontrou um preço válido para esta URL.")
                        usar_assim_mesmo = input("Deseja usar o seletor existente mesmo assim? (s/n): ")
                        if usar_assim_mesmo.lower() != 's':
                            seletor_css = None
            
            # Se não encontrou pela plataforma ou não funcionou, verifica pelo domínio (método original)
            if seletor_css is None and dominio in dominios_seletores:
                seletor_existente = dominios_seletores[dominio]
                print(f"\nO domínio '{dominio}' já tem um seletor CSS cadastrado: '{seletor_existente}'")
                
                usar_seletor_existente = input("Deseja usar o seletor existente? (s/n): ")
                if usar_seletor_existente.lower() == 's':
                    seletor_css = seletor_existente
                    
                    # Teste rápido para confirmar se o seletor existente funciona para esta URL
                    print(f"Testando seletor existente: {seletor_css}")
                    preco_teste = extrair_preco(url, seletor_css)
                    
                    if not preco_teste:
                        print("AVISO: O seletor existente não encontrou um preço válido para esta URL.")
                        usar_assim_mesmo = input("Deseja usar o seletor existente mesmo assim? (s/n): ")
                        if usar_assim_mesmo.lower() != 's':
                            seletor_css = None
            
            # Se não temos um seletor, pedimos ao usuário diretamente
            if seletor_css is None:
                seletor_css = input("Seletor CSS do elemento de preço (ex: .preco-produto, #preco): ")
        
        conexao.close()
        
        # Testar o seletor final
        print(f"Testando seletor final: {seletor_css}")
        preco_teste = extrair_preco(url, seletor_css)
        
        if preco_teste:
            print(f"Teste bem-sucedido! Preço encontrado: {preco_teste}")
            
            # Salvar o domínio e o seletor na base
            dominios_seletores[dominio] = seletor_css
            salvar_dominios_seletores(dominios_seletores)
            print(f"Seletor para o domínio '{dominio}' salvo com sucesso!")
            
            # NOVA FUNCIONALIDADE: Salvar o seletor para a plataforma se informada
            if plataforma.upper() != 'N':
                plataformas_seletores[plataforma] = seletor_css
                salvar_plataformas_seletores(plataformas_seletores)
                print(f"Seletor para a plataforma '{plataforma}' salvo com sucesso!")
            
            # Inserir o produto na base de dados
            try:
                conexao, cursor = criar_conexao()
                data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # 1. Verificar se o cliente existe
                cursor.execute("SELECT id FROM clientes WHERE nome = ?", (cliente,))
                resultado = cursor.fetchone()
                
                if not resultado:
                    # Cliente não existe, criar
                    cursor.execute('''
                    INSERT INTO clientes (nome, data_criacao) 
                    VALUES (?, ?)
                    ''', (cliente, data_atual))
                    
                    # Obter ID do cliente recém-criado
                    cursor.execute("SELECT id FROM clientes WHERE nome = ?", (cliente,))
                    resultado = cursor.fetchone()
                
                id_cliente = resultado['id']
                
                # 2. Obter ID do grupo
                cursor.execute("SELECT id FROM grupos WHERE id_grupo = ?", (grupo_usuario,))
                resultado = cursor.fetchone()
                
                if not resultado:
                    depurar_logs(f"Grupo {grupo_usuario} não encontrado ao adicionar produto", "ERROR")
                    conexao.close()
                    return False
                
                id_grupo = resultado['id']
                
                # 3. Verificar se a plataforma existe e obter seu ID
                id_plataforma = None
                if plataforma.upper() != 'N':
                    cursor.execute("SELECT id FROM plataformas WHERE nome = ?", (plataforma,))
                    resultado = cursor.fetchone()
                    
                    if resultado:
                        id_plataforma = resultado['id']
                
                # 4. Verificar se o produto já existe para este cliente e grupo
                cursor.execute('''
                SELECT id FROM produtos 
                WHERE id_cliente = ? AND nome = ? AND url = ? AND id_grupo = ?
                ''', (id_cliente, produto, url, id_grupo))
                
                resultado = cursor.fetchone()
                produto_existente = resultado is not None
                
                if produto_existente:
                    print(f"AVISO: O produto '{produto}' já existe para o cliente '{cliente}' neste grupo com esta URL.")
                    atualizar = input("Deseja atualizar as informações? (s/n): ")
                    if atualizar.lower() != 's':
                        print("Operação cancelada. O produto não foi alterado.")
                        conexao.close()
                        return False
                    
                    # Atualizar produto existente
                    cursor.execute('''
                    UPDATE produtos 
                    SET concorrente = ?, id_plataforma = ?
                    WHERE id = ?
                    ''', (concorrente, id_plataforma, resultado['id']))
                    
                    id_produto = resultado['id']
                else:
                    # Inserir novo produto
                    cursor.execute('''
                    INSERT INTO produtos (id_cliente, nome, concorrente, url, id_plataforma, id_grupo, data_criacao)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (id_cliente, produto, concorrente, url, id_plataforma, id_grupo, data_atual))
                    
                    # Obter ID do produto recém-criado
                    cursor.execute("SELECT last_insert_rowid() as id")
                    id_produto = cursor.fetchone()['id']
                
                conexao.commit()
                conexao.close()
                
                # 5. Adicionar o cliente aos grupos administrativos e do usuário
                from grupos_bd import adicionar_cliente_a_todos_grupos_admin, adicionar_cliente_grupo_usuario
                
                adicionar_cliente_a_todos_grupos_admin(cliente)
                
                # Se o usuário não for admin, adiciona ao grupo do usuário
                if usuario_atual and usuario_atual != "admin" and "admin" not in obter_grupos_usuario(usuario_atual):
                    adicionar_cliente_grupo_usuario(usuario_atual, cliente, usuario_atual)
                
                # 6. Registrar o preço atual
                from scraper import registrar_preco
                registrar_preco(
                    cliente=cliente,
                    produto=produto,
                    concorrente=concorrente,
                    url=url,
                    id_produto=id_produto,
                    seletor_css=seletor_css,
                    usuario_atual=usuario_atual
                )
                
                depurar_logs(f"Produto '{produto}' do cliente '{cliente}' adicionado por {usuario_atual} no grupo {grupo_usuario}", "INFO")
                print(f"Produto '{produto}' do cliente '{cliente}' adicionado com sucesso para monitoramento!")
                
                return True
                
            except Exception as e:
                depurar_logs(f"Erro ao inserir produto no banco de dados: {e}", "ERROR")
                print(f"Erro ao adicionar produto: {e}")
                return False
        else:
            print("Não foi possível encontrar o preço com o seletor fornecido.")
            tentar_novamente = input("Deseja tentar adicionar o produto novamente? (s/n): ")
            if tentar_novamente.lower() == 's':
                # Chama a função novamente, mas mantém os dados já fornecidos
                return adicionar_produto(cliente, produto, concorrente, url, usuario_atual)
            return False
            
    except Exception as e:
        depurar_logs(f"Erro ao adicionar produto: {e}", "ERROR")
        print(f"Erro ao adicionar produto: {e}")
        return False

def remover_produto(usuario_atual=None):
    """
    Remove um produto da lista de monitoramento.
    Filtra por produtos do grupo do usuário.
    
    Args:
        usuario_atual (str, optional): Nome do usuário que está removendo o produto
    """
    from grupos_bd import obter_grupos_usuario
    
    try:
        conexao, cursor = criar_conexao()
        
        # Determina os grupos do usuário
        if usuario_atual == "admin" or (usuario_atual and "admin" in obter_grupos_usuario(usuario_atual)):
            # Administradores veem todos os produtos
            cursor.execute('''
            SELECT p.id, c.nome as cliente, p.nome as produto, p.concorrente, p.url, g.id_grupo as grupo
            FROM produtos p
            JOIN clientes c ON p.id_cliente = c.id
            JOIN grupos g ON p.id_grupo = g.id
            ORDER BY c.nome, p.nome
            ''')
        else:
            if not usuario_atual:
                print("Usuário não identificado. Não é possível remover produtos.")
                conexao.close()
                return
                
            grupos = obter_grupos_usuario(usuario_atual)
            if not grupos:
                print("Você não tem acesso a nenhum grupo para remover produtos.")
                conexao.close()
                return
                
            # Filtra para obter apenas o grupo pessoal do usuário
            grupos_pessoais = [g for g in grupos if g != "all" and g != "admin"]
            if not grupos_pessoais:
                print("Você não tem um grupo pessoal. Não é possível remover produtos.")
                conexao.close()
                return
                
            grupo_usuario = grupos_pessoais[0]  # Usa o primeiro grupo pessoal encontrado
            
# Filtra produtos apenas do grupo do usuário
            cursor.execute('''
            SELECT p.id, c.nome as cliente, p.nome as produto, p.concorrente, p.url, g.id_grupo as grupo
            FROM produtos p
            JOIN clientes c ON p.id_cliente = c.id
            JOIN grupos g ON p.id_grupo = g.id
            WHERE g.id_grupo = ?
            ORDER BY c.nome, p.nome
            ''', (grupo_usuario,))
        
        produtos = cursor.fetchall()
        
        if not produtos:
            print("Não há produtos cadastrados para remover.")
            conexao.close()
            return
        
        print("Produtos monitorados:")
        for i, row in enumerate(produtos, 1):
            grupo_txt = f" (Grupo: {row['grupo']})" if row['grupo'] else ""
            print(f"{i}. Cliente: {row['cliente']} - Produto: {row['produto']} - Concorrente: {row['concorrente']}{grupo_txt}")
        
        escolha = input("Digite o número do produto que deseja remover (0 para cancelar): ")
        
        if escolha == "0":
            conexao.close()
            return
            
        try:
            indice = int(escolha) - 1
            if 0 <= indice < len(produtos):
                # Produto selecionado para remoção
                produto_removido = produtos[indice]
                
                # Remover registros de histórico de preços
                cursor.execute("DELETE FROM historico_precos WHERE id_produto = ?", (produto_removido['id'],))
                
                # Remover o produto
                cursor.execute("DELETE FROM produtos WHERE id = ?", (produto_removido['id'],))
                
                conexao.commit()
                conexao.close()
                
                grupo_info = f" do grupo {produto_removido['grupo']}" if produto_removido['grupo'] else ""
                depurar_logs(f"Produto '{produto_removido['produto']}' do cliente '{produto_removido['cliente']}'{grupo_info} removido por {usuario_atual}", "INFO")
                
                print("Produto removido com sucesso!")
            else:
                print("Opção inválida.")
                conexao.close()
        except ValueError:
            print("Entrada inválida. Digite um número.")
            conexao.close()
            
    except Exception as e:
        depurar_logs(f"Erro ao remover produto: {e}", "ERROR")
        print(f"Erro ao remover produto: {e}")

def listar_plataformas_seletores():
    """
    Lista todas as plataformas e seus seletores CSS salvos.
    """
    try:
        conexao, cursor = criar_conexao()
        
        cursor.execute("SELECT nome, seletor_css FROM plataformas ORDER BY nome")
        plataformas = cursor.fetchall()
        
        conexao.close()
        
        if not plataformas:
            print("Não há plataformas e seletores salvos.")
            return
        
        print("\nPlataformas e seletores cadastrados:")
        for i, plataforma in enumerate(plataformas, 1):
            print(f"{i}. {plataforma['nome']}: {plataforma['seletor_css']}")
            
    except Exception as e:
        depurar_logs(f"Erro ao listar plataformas e seletores: {e}", "ERROR")
        print(f"Erro ao listar plataformas: {e}")

def remover_plataforma_seletor():
    """
    Remove uma plataforma e seu seletor da base.
    """
    try:
        conexao, cursor = criar_conexao()
        
        cursor.execute("SELECT id, nome, seletor_css FROM plataformas ORDER BY nome")
        plataformas = cursor.fetchall()
        
        if not plataformas:
            print("Não há plataformas e seletores salvos para remover.")
            conexao.close()
            return
        
        print("\nPlataformas disponíveis para remoção:")
        for i, plataforma in enumerate(plataformas, 1):
            print(f"{i}. {plataforma['nome']}: {plataforma['seletor_css']}")
        
        escolha = input("Digite o número da plataforma que deseja remover (ou 'cancelar'): ")
        
        if escolha.lower() == 'cancelar':
            conexao.close()
            return
        
        try:
            indice = int(escolha) - 1
            if 0 <= indice < len(plataformas):
                plataforma_a_remover = plataformas[indice]
                
                # Remover a plataforma
                cursor.execute("DELETE FROM plataformas WHERE id = ?", (plataforma_a_remover['id'],))
                
                # Atualizar produtos que usavam esta plataforma
                cursor.execute("UPDATE produtos SET id_plataforma = NULL WHERE id_plataforma = ?", 
                             (plataforma_a_remover['id'],))
                
                conexao.commit()
                conexao.close()
                
                print(f"Plataforma '{plataforma_a_remover['nome']}' removida com sucesso!")
            else:
                print("Opção inválida.")
                conexao.close()
        except ValueError:
            print("Entrada inválida. Digite um número ou 'cancelar'.")
            conexao.close()
            
    except Exception as e:
        depurar_logs(f"Erro ao remover plataforma: {e}", "ERROR")
        print(f"Erro ao remover plataforma: {e}")

def listar_dominios_seletores():
    """
    Lista todos os domínios e seus seletores CSS salvos.
    """
    try:
        conexao, cursor = criar_conexao()
        
        cursor.execute("SELECT nome, seletor_css FROM dominios ORDER BY nome")
        dominios = cursor.fetchall()
        
        conexao.close()
        
        if not dominios:
            print("Não há domínios e seletores salvos.")
            return
        
        print("\nDomínios e seletores cadastrados:")
        for i, dominio in enumerate(dominios, 1):
            print(f"{i}. {dominio['nome']}: {dominio['seletor_css']}")
            
    except Exception as e:
        depurar_logs(f"Erro ao listar domínios e seletores: {e}", "ERROR")
        print(f"Erro ao listar domínios: {e}")

def remover_dominio_seletor():
    """
    Remove um domínio e seu seletor da base.
    """
    try:
        conexao, cursor = criar_conexao()
        
        cursor.execute("SELECT id, nome, seletor_css FROM dominios ORDER BY nome")
        dominios = cursor.fetchall()
        
        if not dominios:
            print("Não há domínios e seletores salvos para remover.")
            conexao.close()
            return
        
        print("\nDomínios disponíveis para remoção:")
        for i, dominio in enumerate(dominios, 1):
            print(f"{i}. {dominio['nome']}: {dominio['seletor_css']}")
        
        escolha = input("Digite o número do domínio que deseja remover (ou 'cancelar'): ")
        
        if escolha.lower() == 'cancelar':
            conexao.close()
            return
        
        try:
            indice = int(escolha) - 1
            if 0 <= indice < len(dominios):
                dominio_a_remover = dominios[indice]
                
                # Remover o domínio
                cursor.execute("DELETE FROM dominios WHERE id = ?", (dominio_a_remover['id'],))
                
                conexao.commit()
                conexao.close()
                
                print(f"Domínio '{dominio_a_remover['nome']}' removido com sucesso!")
            else:
                print("Opção inválida.")
                conexao.close()
        except ValueError:
            print("Entrada inválida. Digite um número ou 'cancelar'.")
            conexao.close()
            
    except Exception as e:
        depurar_logs(f"Erro ao remover domínio: {e}", "ERROR")
        print(f"Erro ao remover domínio: {e}")

def listar_clientes(usuario_atual=None):
    """
    Lista todos os clientes cadastrados e a quantidade de produtos monitorados para cada um.
    Filtra os clientes de acordo com os grupos aos quais o usuário pertence.
    
    Args:
        usuario_atual (str, optional): Nome do usuário logado atualmente
        
    Returns:
        list: Lista dos clientes disponíveis
    """
    from grupos_bd import obter_grupos_usuario, obter_clientes_usuario
    
    try:
        conexao, cursor = criar_conexao()
        
        # Verificar se estamos recebendo resultados do banco de dados
        cursor.execute("SELECT COUNT(*) as count FROM clientes")
        resultado = cursor.fetchone()
        total_clientes = resultado['count']
        
        print(f"DEBUG: Total de clientes no banco de dados: {total_clientes}")
        
        # Obtém a lista completa de clientes
        cursor.execute('''
        SELECT c.id, c.nome, COUNT(p.id) as num_produtos 
        FROM clientes c
        LEFT JOIN produtos p ON c.id = p.id_cliente
        GROUP BY c.id
        ORDER BY c.nome
        ''')
        
        todos_clientes = cursor.fetchall()
        
        # Exibe para debug
        print(f"DEBUG: Clientes encontrados no banco: {len(todos_clientes)}")
        for cliente in todos_clientes:
            print(f"DEBUG: Cliente: {cliente['nome']}, Produtos: {cliente['num_produtos']}")
        
        conexao.close()
        
        # Se um usuário está especificado, filtra a lista de acordo com as permissões
        clientes_permitidos = []
        if usuario_atual:
            # Se for admin, pode ver todos os clientes
            if usuario_atual == "admin" or usuario_atual in ["admin", "administrador"]:
                print(f"DEBUG: Usuário {usuario_atual} é admin, mostrando todos os clientes")
                clientes_permitidos = [{'nome': c['nome'], 'num_produtos': c['num_produtos']} for c in todos_clientes]
            else:
                # Filtra apenas os clientes que o usuário pode acessar
                print(f"DEBUG: Obtendo clientes autorizados para {usuario_atual}")
                clientes_autorizados = obter_clientes_usuario(usuario_atual)
                print(f"DEBUG: Clientes autorizados: {clientes_autorizados}")
                
                clientes_permitidos = [{'nome': c['nome'], 'num_produtos': c['num_produtos']} 
                                      for c in todos_clientes if c['nome'] in clientes_autorizados]
        else:
            # Se nenhum usuário especificado, mostra todos os clientes
            clientes_permitidos = [{'nome': c['nome'], 'num_produtos': c['num_produtos']} for c in todos_clientes]
        
        if not clientes_permitidos:
            print("Você não tem acesso a nenhum cliente.")
            return []
        
        print("\nClientes cadastrados:")
        for i, cliente in enumerate(clientes_permitidos, 1):
            print(f"{i}. {cliente['nome']} ({cliente['num_produtos']} produtos)")
            
        return [c['nome'] for c in clientes_permitidos]
        
    except Exception as e:
        import traceback
        print(f"Erro ao listar clientes: {e}")
        print(traceback.format_exc())
        return []

def listar_produtos(cliente=None, usuario_atual=None):
    """
    Lista os produtos monitorados, opcionalmente filtrados por cliente.
    
    Args:
        cliente (str, optional): Nome do cliente para filtrar
        usuario_atual (str, optional): Nome do usuário atual
        
    Returns:
        list: Lista dos produtos encontrados
    """
    try:
        from grupos_bd import obter_grupos_usuario
        
        print(f"DEBUG: Listando produtos para cliente={cliente}, usuario={usuario_atual}")
        
        conexao, cursor = criar_conexao()
        
        # Preparar a condição de filtro por cliente
        where_cliente = ""
        params = []
        
        if cliente:
            where_cliente = "AND c.nome = ?"
            params.append(cliente)
        
        # Determina os grupos do usuário para filtrar
        if usuario_atual == "admin" or (usuario_atual and "admin" in obter_grupos_usuario(usuario_atual)):
            # Administradores veem todos os produtos
            where_grupo = ""
        else:
            if not usuario_atual:
                print("Usuário não identificado. Não é possível listar produtos.")
                conexao.close()
                return []
                
            grupos = obter_grupos_usuario(usuario_atual)
            if not grupos:
                print("Você não tem acesso a nenhum grupo para listar produtos.")
                conexao.close()
                return []
                
            # Filtra para obter apenas o grupo pessoal do usuário
            grupos_pessoais = [g for g in grupos if g != "all" and g != "admin"]
            if not grupos_pessoais:
                print("Você não tem um grupo pessoal. Não é possível listar produtos.")
                conexao.close()
                return []
                
            grupo_usuario = grupos_pessoais[0]  # Usa o primeiro grupo pessoal encontrado
            
            # Filtrar por grupo do usuário
            where_grupo = "AND g.id_grupo = ?"
            params.append(grupo_usuario)
        
        # Consulta para listar produtos
        query = f'''
        SELECT p.id, c.nome as cliente, p.nome as produto, p.concorrente, p.url, g.id_grupo as grupo
        FROM produtos p
        JOIN clientes c ON p.id_cliente = c.id
        JOIN grupos g ON p.id_grupo = g.id
        WHERE 1=1 {where_cliente} {where_grupo}
        ORDER BY c.nome, p.nome
        '''
        
        cursor.execute(query, params)
        produtos = cursor.fetchall()
        
        print(f"DEBUG: Encontrados {len(produtos)} produtos")
        
        conexao.close()
        return produtos
        
    except Exception as e:
        import traceback
        print(f"Erro ao listar produtos: {e}")
        print(traceback.format_exc())
        return []

def visualizar_historico(usuario_atual=None, cliente_filtro=None):
    """
    Visualiza o histórico de preços com opções de filtro por cliente e produto.
    Consolida produtos com o mesmo nome.
    Filtra por grupo do usuário.
    
    Args:
        usuario_atual (str, optional): Nome do usuário logado atualmente
        cliente_filtro (str, optional): Nome do cliente para filtrar automaticamente
    """
    from grupos_bd import obter_grupos_usuario
    
    try:
        conexao, cursor = criar_conexao()
        
        # Determina os grupos do usuário para filtrar
        if usuario_atual == "admin" or (usuario_atual and "admin" in obter_grupos_usuario(usuario_atual)):
            # Administradores veem todo o histórico
            where_grupo = ""
            params = ()
        else:
            if not usuario_atual:
                print("Usuário não identificado. Não é possível visualizar o histórico.")
                conexao.close()
                return
                
            grupos = obter_grupos_usuario(usuario_atual)
            if not grupos:
                print("Você não tem acesso a nenhum grupo para visualizar o histórico.")
                conexao.close()
                return
                
            # Filtra para obter apenas o grupo pessoal do usuário
            grupos_pessoais = [g for g in grupos if g != "all" and g != "admin"]
            if not grupos_pessoais:
                print("Você não tem um grupo pessoal. Não é possível visualizar o histórico.")
                conexao.close()
                return
                
            grupo_usuario = grupos_pessoais[0]  # Usa o primeiro grupo pessoal encontrado
            
            # Filtrar por grupo do usuário
            where_grupo = "AND g.id_grupo = ?"
            params = (grupo_usuario,)
        
        # Se um cliente específico foi passado, filtra diretamente
        if cliente_filtro:
            # Verifica se o cliente existe
            cursor.execute("SELECT id FROM clientes WHERE nome = ?", (cliente_filtro,))
            resultado = cursor.fetchone()
            
            if resultado:
                id_cliente = resultado['id']
                
                # Buscar produtos do cliente (agrupados por nome do produto)
                cursor.execute(f'''
                SELECT DISTINCT p.nome 
                FROM produtos p
                JOIN grupos g ON p.id_grupo = g.id
                WHERE p.id_cliente = ? {where_grupo}
                ORDER BY p.nome
                ''', (id_cliente,) + params)
                
                produtos = cursor.fetchall()
                
                if not produtos:
                    print(f"Não há produtos com histórico para o cliente '{cliente_filtro}'.")
                    conexao.close()
                    return
                
                print(f"\nProdutos disponíveis para o cliente '{cliente_filtro}':")
                for i, p in enumerate(produtos, 1):
                    print(f"{i}. {p['nome']}")
                
                escolha_produto = input("\nDigite o número do produto que deseja visualizar (ou 'todos' para ver todos): ")
                
                if escolha_produto.lower() == 'todos':
                    print(f"\nHistórico de preços de todos os produtos do cliente '{cliente_filtro}':")
                    
                    # Buscar histórico de todos os produtos do cliente, agrupados por nome do produto e data
                    cursor.execute(f'''
                    SELECT h.data, p.nome as produto, p.concorrente, h.preco, p.url
                    FROM historico_precos h
                    JOIN produtos p ON h.id_produto = p.id
                    JOIN grupos g ON p.id_grupo = g.id
                    WHERE p.id_cliente = ? {where_grupo}
                    ORDER BY p.nome, h.data DESC
                    ''', (id_cliente,) + params)
                    
                    historico = cursor.fetchall()
                    
                    # Exibir os resultados
                    print(f"{'Data':<12} | {'Produto':<30} | {'Concorrente':<20} | {'Preço':<10} | {'URL':<50}")
                    print("-" * 120)
                    
                    for row in historico:
                        print(f"{row['data']:<12} | {row['produto'][:30]:<30} | {row['concorrente'][:20]:<20} | R$ {row['preco']:<8.2f} | {row['url'][:50]}")
                    
                else:
                    try:
                        indice_produto = int(escolha_produto) - 1
                        if 0 <= indice_produto < len(produtos):
                            nome_produto = produtos[indice_produto]['nome']
                            
                            print(f"\nHistórico de preços para '{nome_produto}' do cliente '{cliente_filtro}':")
                            
                            # Buscar histórico de todos os produtos com esse nome
                            cursor.execute(f'''
                            SELECT h.data, p.concorrente, h.preco, p.url
                            FROM historico_precos h
                            JOIN produtos p ON h.id_produto = p.id
                            JOIN grupos g ON p.id_grupo = g.id
                            WHERE p.id_cliente = ? AND p.nome = ? {where_grupo}
                            ORDER BY h.data DESC, p.concorrente
                            ''', (id_cliente, nome_produto) + params)
                            
                            historico = cursor.fetchall()
                            
                            # Exibir os resultados
                            print(f"{'Data':<12} | {'Concorrente':<20} | {'Preço':<10} | {'URL':<50}")
                            print("-" * 100)
                            
                            for row in historico:
                                print(f"{row['data']:<12} | {row['concorrente'][:20]:<20} | R$ {row['preco']:<8.2f} | {row['url'][:50]}")
                            
                        else:
                            print("Opção inválida.")
                    except ValueError:
                        print("Entrada inválida. Digite um número ou 'todos'.")
            else:
                print(f"Não há histórico para o cliente '{cliente_filtro}'.")
            
            conexao.close()
            return
        
        # Opção para filtrar por cliente primeiro
        cursor.execute(f'''
        SELECT DISTINCT c.id, c.nome
        FROM clientes c
        JOIN produtos p ON c.id = p.id_cliente
        JOIN grupos g ON p.id_grupo = g.id
        JOIN historico_precos h ON p.id = h.id_produto
        WHERE 1=1 {where_grupo}
        ORDER BY c.nome
        ''', params)
        
        clientes = cursor.fetchall()
        
        if not clientes:
            print("Não há histórico de preços disponível.")
            conexao.close()
            return
        
        print("\nClientes disponíveis:")
        for i, c in enumerate(clientes, 1):
            print(f"{i}. {c['nome']}")
        
        escolha_cliente = input("\nDigite o número do cliente que deseja visualizar (ou 'todos' para ver todos): ")
        
        if escolha_cliente.lower() == 'todos':
            # Buscar produtos distintos com histórico (pelo nome do produto)
            cursor.execute(f'''
            SELECT DISTINCT p.nome
            FROM produtos p
            JOIN grupos g ON p.id_grupo = g.id
            JOIN historico_precos h ON p.id = h.id_produto
            WHERE 1=1 {where_grupo}
            ORDER BY p.nome
            ''', params)
            
            produtos = cursor.fetchall()
            
            print("\nProdutos disponíveis:")
            for i, p in enumerate(produtos, 1):
                print(f"{i}. {p['nome']}")
            
            escolha_produto = input("\nDigite o número do produto que deseja visualizar (ou 'todos' para ver todos): ")
            
            if escolha_produto.lower() == 'todos':
                print("\nHistórico completo de preços:")
                
                # Buscar todo o histórico
                cursor.execute(f'''
                SELECT h.data, c.nome as cliente, p.nome as produto, p.concorrente, h.preco, p.url
                FROM historico_precos h
                JOIN produtos p ON h.id_produto = p.id
                JOIN clientes c ON p.id_cliente = c.id
                JOIN grupos g ON p.id_grupo = g.id
                WHERE 1=1 {where_grupo}
                ORDER BY h.data DESC, c.nome, p.nome
                ''', params)
                
                historico = cursor.fetchall()
                
                # Exibir os resultados
                print(f"{'Data':<12} | {'Cliente':<20} | {'Produto':<30} | {'Concorrente':<20} | {'Preço':<10} | {'URL':<30}")
                print("-" * 130)
                
                for row in historico:
                    print(f"{row['data']:<12} | {row['cliente'][:20]:<20} | {row['produto'][:30]:<30} | {row['concorrente'][:20]:<20} | R$ {row['preco']:<8.2f} | {row['url'][:30]}")
                
            else:
                try:
                    indice_produto = int(escolha_produto) - 1
                    if 0 <= indice_produto < len(produtos):
                        nome_produto = produtos[indice_produto]['nome']
                        
                        print(f"\nHistórico de preços para '{nome_produto}':")
                        
                        # Buscar histórico para todos os produtos com este nome
                        cursor.execute(f'''
                        SELECT h.data, c.nome as cliente, p.concorrente, h.preco, p.url
                        FROM historico_precos h
                        JOIN produtos p ON h.id_produto = p.id
                        JOIN clientes c ON p.id_cliente = c.id
                        JOIN grupos g ON p.id_grupo = g.id
                        WHERE p.nome = ? {where_grupo}
                        ORDER BY h.data DESC, c.nome
                        ''', (nome_produto,) + params)
                        
                        historico = cursor.fetchall()
                        
                        # Exibir os resultados
                        print(f"{'Data':<12} | {'Cliente':<20} | {'Concorrente':<20} | {'Preço':<10} | {'URL':<50}")
                        print("-" * 120)
                        
                        for row in historico:
                            print(f"{row['data']:<12} | {row['cliente'][:20]:<20} | {row['concorrente'][:20]:<20} | R$ {row['preco']:<8.2f} | {row['url'][:50]}")
                        
                    else:
                        print("Opção inválida.")
                except ValueError:
                    print("Entrada inválida. Digite um número ou 'todos'.")
        else:
            try:
                indice_cliente = int(escolha_cliente) - 1
                if 0 <= indice_cliente < len(clientes):
                    id_cliente = clientes[indice_cliente]['id']
                    nome_cliente = clientes[indice_cliente]['nome']
                    
                    # Buscar produtos distintos do cliente selecionado (pelo nome do produto)
                    cursor.execute(f'''
                    SELECT DISTINCT p.nome
                    FROM produtos p
                    JOIN grupos g ON p.id_grupo = g.id
                    JOIN historico_precos h ON p.id = h.id_produto
                    WHERE p.id_cliente = ? {where_grupo}
                    ORDER BY p.nome
                    ''', (id_cliente,) + params)
                    
                    produtos = cursor.fetchall()
                    
                    print(f"\nProdutos disponíveis para o cliente '{nome_cliente}':")
                    for i, p in enumerate(produtos, 1):
                        print(f"{i}. {p['nome']}")
                    
                    escolha_produto = input("\nDigite o número do produto que deseja visualizar (ou 'todos' para ver todos): ")
                    
                    if escolha_produto.lower() == 'todos':
                        print(f"\nHistórico de preços de todos os produtos do cliente '{nome_cliente}':")
                        
                        # Buscar histórico de todos os produtos do cliente
                        cursor.execute(f'''
                        SELECT h.data, p.nome as produto, p.concorrente, h.preco, p.url
                        FROM historico_precos h
                        JOIN produtos p ON h.id_produto = p.id
                        JOIN grupos g ON p.id_grupo = g.id
                        WHERE p.id_cliente = ? {where_grupo}
                        ORDER BY p.nome, h.data DESC
                        ''', (id_cliente,) + params)
                        
                        historico = cursor.fetchall()
                        
                        # Exibir os resultados
                        print(f"{'Data':<12} | {'Produto':<30} | {'Concorrente':<20} | {'Preço':<10} | {'URL':<50}")
                        print("-" * 120)
                        
                        for row in historico:
                            print(f"{row['data']:<12} | {row['produto'][:30]:<30} | {row['concorrente'][:20]:<20} | R$ {row['preco']:<8.2f} | {row['url'][:50]}")
                        
                    else:
                        try:
                            indice_produto = int(escolha_produto) - 1
                            if 0 <= indice_produto < len(produtos):
                                nome_produto = produtos[indice_produto]['nome']
                                
                                print(f"\nHistórico de preços para '{nome_produto}' do cliente '{nome_cliente}':")
                                
                                # Buscar histórico de todos os produtos com este nome para este cliente
                                cursor.execute(f'''
                                SELECT h.data, p.concorrente, h.preco, p.url
                                FROM historico_precos h
                                JOIN produtos p ON h.id_produto = p.id
                                JOIN grupos g ON p.id_grupo = g.id
                                WHERE p.id_cliente = ? AND p.nome = ? {where_grupo}
                                ORDER BY h.data DESC, p.concorrente
                                ''', (id_cliente, nome_produto) + params)
                                
                                historico = cursor.fetchall()
                                
                                # Exibir os resultados
                                print(f"{'Data':<12} | {'Concorrente':<20} | {'Preço':<10} | {'URL':<50}")
                                print("-" * 100)
                                
                                for row in historico:
                                    print(f"{row['data']:<12} | {row['concorrente'][:20]:<20} | R$ {row['preco']:<8.2f} | {row['url'][:50]}")
                                
                            else:
                                print("Opção inválida.")
                        except ValueError:
                            print("Entrada inválida. Digite um número ou 'todos'.")
                else:
                    print("Opção inválida.")
            except ValueError:
                print("Entrada inválida. Digite um número ou 'todos'.")
        
        conexao.close()
        
    except Exception as e:
        depurar_logs(f"Erro ao visualizar histórico: {e}", "ERROR")
        print(f"Erro ao visualizar histórico: {e}")

def adicionar_cliente(nome_cliente, usuario_atual=None):
    """
    Adiciona um novo cliente ao sistema.
    
    Args:
        nome_cliente (str): Nome do novo cliente
        usuario_atual (str, optional): Nome do usuário que está adicionando o cliente
        
    Returns:
        bool: True se o cliente foi adicionado com sucesso, False caso contrário
    """
    # Verificar se o nome é válido
    if not nome_cliente:
        print("Nome de cliente inválido.")
        return False
    
    try:
        conexao, cursor = criar_conexao()
        
        # Verificar se o cliente já existe
        cursor.execute("SELECT id FROM clientes WHERE nome = ?", (nome_cliente,))
        resultado = cursor.fetchone()
        
        if resultado:
            print(f"Cliente '{nome_cliente}' já existe no sistema.")
            conexao.close()
            return True
        
        # Adicionar o novo cliente
        data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
        INSERT INTO clientes (nome, data_criacao)
        VALUES (?, ?)
        ''', (nome_cliente, data_atual))
        
        conexao.commit()
        conexao.close()
        
        # Associar o cliente aos grupos apropriados
        from grupos_bd import adicionar_cliente_a_todos_grupos_admin, adicionar_cliente_grupo_usuario, obter_grupos_usuario
        
        # Se for admin, adiciona o cliente aos grupos de admin
        if usuario_atual == "admin" or (usuario_atual and "admin" in obter_grupos_usuario(usuario_atual)):
            adicionar_cliente_a_todos_grupos_admin(nome_cliente)
        # Se não for admin, adiciona ao grupo pessoal do usuário
        elif usuario_atual:
            adicionar_cliente_grupo_usuario(usuario_atual, nome_cliente, usuario_atual)
        
        depurar_logs(f"Cliente '{nome_cliente}' adicionado por {usuario_atual}", "INFO")
        print(f"Cliente '{nome_cliente}' adicionado com sucesso!")
        return True
        
    except Exception as e:
        depurar_logs(f"Erro ao adicionar cliente: {str(e)}", "ERROR")
        print(f"Erro ao adicionar cliente: {str(e)}")
        return False