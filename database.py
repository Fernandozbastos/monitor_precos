import os
import json
import pandas as pd
from scraper import extrair_dominio, extrair_preco
from grupos import (
    obter_clientes_usuario, 
    usuario_pode_acessar_cliente, 
    sincronizar_clientes,
    adicionar_cliente_a_todos_grupos_admin,
    obter_grupos_usuario,
    adicionar_cliente_grupo_usuario  # Adicionada importação faltante
)
from utils import depurar_logs

# Constante para o arquivo de domínios e seletores
DOMINIOS_SELETORES_FILE = 'dominios_seletores.json'

def adicionar_cliente_grupo_usuario_local(usuario, cliente, operador=None):
    """
    Versão local da função para adicionar um cliente ao grupo de um usuário.
    Evita problemas de importação.
    """
    from grupos import adicionar_cliente_a_todos_grupos_admin, carregar_grupos, salvar_grupos
    
    # Primeiro, adiciona aos grupos de administração
    adicionar_cliente_a_todos_grupos_admin(cliente)
    
    # Em seguida, adiciona ao grupo pessoal do usuário
    grupos = carregar_grupos()
    
    # Verifica se o grupo do usuário existe
    if usuario not in grupos:
        depurar_logs(f"Tentativa de adicionar cliente a grupo de usuário inexistente: {usuario}", "WARNING")
        return False
    
    # Verifica se o cliente já está no grupo
    if cliente in grupos[usuario]["clientes"]:
        return True  # Cliente já está no grupo, não precisa adicionar
    
    # Adiciona o cliente ao grupo
    grupos[usuario]["clientes"].append(cliente)
    
    sucesso = salvar_grupos(grupos)
    if sucesso:
        depurar_logs(f"Cliente {cliente} adicionado ao grupo do usuário {usuario}", "INFO")
    
    return sucesso

def carregar_dominios_seletores():
    """
    Carrega o dicionário de domínios e seus seletores CSS do arquivo JSON.
    
    Returns:
        dict: Dicionário com domínios como chaves e seletores CSS como valores
    """
    if os.path.isfile(DOMINIOS_SELETORES_FILE):
        try:
            with open(DOMINIOS_SELETORES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Erro ao carregar arquivo {DOMINIOS_SELETORES_FILE}. Criando novo.")
    return {}

def salvar_dominios_seletores(dominios_seletores):
    """
    Salva o dicionário de domínios e seletores CSS no arquivo JSON.
    
    Args:
        dominios_seletores (dict): Dicionário com domínios e seletores CSS
    """
    with open(DOMINIOS_SELETORES_FILE, 'w', encoding='utf-8') as f:
        json.dump(dominios_seletores, f, ensure_ascii=False, indent=4)

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
    
    # Carregar dicionário de domínios e seletores
    dominios_seletores = carregar_dominios_seletores()
    
    # Arquivo de produtos e URLs
    arquivo_produtos = 'produtos_monitorados.csv'
    arquivo_urls = 'urls_monitoradas.csv'
    
    # Variável para armazenar o seletor CSS que será usado
    seletor_css = None
    url_ja_monitorada = False
    
    # Primeiro, verificar se a URL já está sendo monitorada
    if os.path.isfile(arquivo_urls):
        try:
            df_urls = pd.read_csv(arquivo_urls)
            url_match = df_urls[df_urls['url'] == url]
            
            if not url_match.empty:
                # A URL já existe no sistema
                url_ja_monitorada = True
                seletor_existente = url_match.iloc[0]['seletor_css']
                print(f"\nEsta URL já está sendo monitorada com o seletor CSS: '{seletor_existente}'")
                
                usar_seletor_existente = input("Deseja usar o seletor existente? (s/n): ")
                if usar_seletor_existente.lower() == 's':
                    seletor_css = seletor_existente
                
                # Se não desejar usar o seletor existente, continuará o fluxo normal
        except Exception as e:
            print(f"Erro ao verificar URLs monitoradas: {e}")
    
    # Se não encontrou a URL ou optou por não usar o seletor existente
    if seletor_css is None:
        # Verificar se o domínio já existe na base
        if dominio in dominios_seletores:
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
    
    # Testar o seletor final
    print(f"Testando seletor final: {seletor_css}")
    preco_teste = extrair_preco(url, seletor_css)
    
    if preco_teste:
        print(f"Teste bem-sucedido! Preço encontrado: {preco_teste}")
        
        # Salvar o domínio e o seletor na base
        dominios_seletores[dominio] = seletor_css
        salvar_dominios_seletores(dominios_seletores)
        print(f"Seletor para o domínio '{dominio}' salvo com sucesso!")
        
        # 1. Salvar/atualizar a URL no arquivo de URLs monitoradas
        if not url_ja_monitorada:
            nova_url = pd.DataFrame({
                'url': [url],
                'dominio': [dominio],
                'seletor_css': [seletor_css]
            })
            
            if os.path.isfile(arquivo_urls):
                try:
                    df_urls = pd.read_csv(arquivo_urls)
                    df_atualizado = pd.concat([df_urls, nova_url], ignore_index=True)
                    df_atualizado.to_csv(arquivo_urls, index=False)
                except Exception as e:
                    print(f"Erro ao atualizar arquivo de URLs: {e}")
                    nova_url.to_csv(arquivo_urls, index=False)
            else:
                nova_url.to_csv(arquivo_urls, index=False)
        
        # 2. Verificar se já existe essa combinação cliente-produto-url-grupo
        produto_existente = False
        if os.path.isfile(arquivo_produtos):
            try:
                df_produtos = pd.read_csv(arquivo_produtos)
                
                # Verifica se a coluna 'grupo' existe
                if 'grupo' not in df_produtos.columns:
                    # Migra para novo formato com coluna de grupo
                    df_produtos['grupo'] = 'admin'  # Atribui o grupo admin aos produtos existentes
                
                # Verifica se o produto já existe com este cliente e grupo
                produto_existente = ((df_produtos['cliente'] == cliente) & 
                                     (df_produtos['produto'] == produto) & 
                                     (df_produtos['url'] == url) &
                                     (df_produtos['grupo'] == grupo_usuario)).any()
                    
                if produto_existente:
                    print(f"AVISO: O produto '{produto}' já existe para o cliente '{cliente}' neste grupo com esta URL.")
                    atualizar = input("Deseja atualizar as informações? (s/n): ")
                    if atualizar.lower() != 's':
                        print("Operação cancelada. O produto não foi alterado.")
                        return False
                    # Se sim, continua para atualizar
            except Exception as e:
                print(f"Erro ao verificar produtos existentes: {e}")
        
        # 3. Salvar o produto na base de monitoramento
        novo_produto = pd.DataFrame({
            'cliente': [cliente],
            'produto': [produto],
            'concorrente': [concorrente],
            'url': [url],
            'grupo': [grupo_usuario]  # Adiciona o grupo do usuário
        })
        
        if os.path.isfile(arquivo_produtos):
            try:
                df_produtos = pd.read_csv(arquivo_produtos)
                
                # Verifica se a coluna 'grupo' existe
                if 'grupo' not in df_produtos.columns:
                    # Migra para novo formato com coluna de grupo
                    df_produtos['grupo'] = 'admin'  # Atribui o grupo admin aos produtos existentes
                
                # Remove o registro existente se houver
                if produto_existente:
                    df_produtos = df_produtos.drop(df_produtos[
                        (df_produtos['cliente'] == cliente) & 
                        (df_produtos['produto'] == produto) & 
                        (df_produtos['url'] == url) &
                        (df_produtos['grupo'] == grupo_usuario)
                    ].index)
                
                # Adiciona o novo registro
                df_atualizado = pd.concat([df_produtos, novo_produto], ignore_index=True)
                df_atualizado.to_csv(arquivo_produtos, index=False)
            except Exception as e:
                print(f"Erro ao atualizar arquivo de produtos: {e}")
                # Tenta criar um novo arquivo caso dê erro
                novo_produto.to_csv(arquivo_produtos, index=False)
        else:
            novo_produto.to_csv(arquivo_produtos, index=False)
        
        # Registra o evento no log
        depurar_logs(f"Produto '{produto}' do cliente '{cliente}' adicionado por {usuario_atual} no grupo {grupo_usuario}", "INFO")
            
        print(f"Produto '{produto}' do cliente '{cliente}' adicionado com sucesso para monitoramento!")
        
        # Verifica se o cliente existe no arquivo de clientes
        arquivo_clientes = 'clientes.csv'
        try:
            if os.path.isfile(arquivo_clientes):
                df_clientes = pd.read_csv(arquivo_clientes)
                if cliente not in df_clientes['cliente'].values:
                    # Adiciona o cliente ao arquivo de clientes se ainda não existir
                    novo_cliente = pd.DataFrame({'cliente': [cliente]})
                    df_clientes = pd.concat([df_clientes, novo_cliente], ignore_index=True)
                    df_clientes.to_csv(arquivo_clientes, index=False)
            else:
                # Cria o arquivo de clientes se não existir
                pd.DataFrame({'cliente': [cliente]}).to_csv(arquivo_clientes, index=False)
        except Exception as e:
            print(f"Erro ao atualizar arquivo de clientes: {e}")
        
        # Adiciona o cliente aos grupos administrativos
        adicionar_cliente_a_todos_grupos_admin(cliente)
        
        # Se o usuário não for admin, adiciona ao grupo do usuário
        if usuario_atual and usuario_atual != "admin" and "admin" not in obter_grupos_usuario(usuario_atual):
            # Usa a função importada se ela existir, caso contrário, usa a versão local
            try:
                from grupos import adicionar_cliente_grupo_usuario
                adicionar_cliente_grupo_usuario(usuario_atual, cliente, usuario_atual)
            except ImportError:
                # Implementação local como fallback
                def adicionar_cliente_grupo_usuario_local(usuario, cliente, operador=None):
                    from grupos import carregar_grupos, salvar_grupos
                    grupos = carregar_grupos()
                    if usuario in grupos and cliente not in grupos[usuario]["clientes"]:
                        grupos[usuario]["clientes"].append(cliente)
                        return salvar_grupos(grupos)
                    return True
                adicionar_cliente_grupo_usuario_local(usuario_atual, cliente, usuario_atual)
        
        # Atualiza o grupo "all" com o novo cliente, se necessário
        try:
            if os.path.isfile(arquivo_produtos):
                df_produtos = pd.read_csv(arquivo_produtos)
                todos_clientes = df_produtos['cliente'].unique().tolist()
                sincronizar_clientes(todos_clientes)
        except Exception as e:
            print(f"Erro ao sincronizar clientes: {e}")
        
        # Tentar extrair e registrar o preço atual
        from scraper import registrar_preco
        registrar_preco(
            cliente=cliente,
            produto=produto,
            concorrente=concorrente,
            url=url,
            seletor_css=seletor_css,
            usuario_atual=usuario_atual  # Passa o usuário atual para a função
        )
        
        return True
    else:
        print("Não foi possível encontrar o preço com o seletor fornecido.")
        tentar_novamente = input("Deseja tentar adicionar o produto novamente? (s/n): ")
        if tentar_novamente.lower() == 's':
            # Chama a função novamente, mas mantém os dados já fornecidos
            return adicionar_produto(cliente, produto, concorrente, url, usuario_atual)
        return False

def remover_produto(usuario_atual=None):
    """
    Remove um produto da lista de monitoramento.
    Filtra por produtos do grupo do usuário.
    
    Args:
        usuario_atual (str, optional): Nome do usuário que está removendo o produto
    """
    if os.path.isfile('produtos_monitorados.csv'):
        df_produtos = pd.read_csv('produtos_monitorados.csv')
        
        if df_produtos.empty:
            print("Não há produtos cadastrados para remover.")
            return
        
        # Verifica se a coluna 'grupo' existe
        if 'grupo' not in df_produtos.columns:
            # Adiciona a coluna grupo se não existir
            df_produtos['grupo'] = 'admin'
            # Salva o arquivo atualizado
            df_produtos.to_csv('produtos_monitorados.csv', index=False)
        
        # Determina o grupo do usuário
        grupo_usuario = None
        if usuario_atual:
            if usuario_atual == "admin" or "admin" in obter_grupos_usuario(usuario_atual):
                # Administradores veem todos os produtos
                pass
            else:
                # Usuários comuns veem apenas produtos do seu grupo
                grupos = obter_grupos_usuario(usuario_atual)
                # Filtra para obter apenas o grupo pessoal do usuário
                grupos_pessoais = [g for g in grupos if g != "all" and g != "admin"]
                if grupos_pessoais:
                    grupo_usuario = grupos_pessoais[0]  # Usa o primeiro grupo pessoal encontrado
                    # Filtra produtos apenas do grupo do usuário
                    df_produtos = df_produtos[df_produtos['grupo'] == grupo_usuario]
                    
                    if df_produtos.empty:
                        print("Você não tem acesso a nenhum produto para remover.")
                        return
        
        print("Produtos monitorados:")
        for i, row in df_produtos.iterrows():
            grupo_txt = f" (Grupo: {row['grupo']})" if 'grupo' in row else ""
            print(f"{i + 1}. Cliente: {row['cliente']} - Produto: {row['produto']} - Concorrente: {row['concorrente']}{grupo_txt}")
        
        escolha = input("Digite o número do produto que deseja remover (0 para cancelar): ")
        
        if escolha == "0":
            return
            
        try:
            indice = int(escolha) - 1
            if 0 <= indice < len(df_produtos):
                # Remove o produto selecionado
                produto_removido = df_produtos.iloc[indice]
                df_produtos = df_produtos.drop(indice).reset_index(drop=True)
                df_produtos.to_csv('produtos_monitorados.csv', index=False)
                
                # Registra o evento no log
                grupo_info = f" do grupo {produto_removido['grupo']}" if 'grupo' in produto_removido else ""
                depurar_logs(f"Produto '{produto_removido['produto']}' do cliente '{produto_removido['cliente']}'{grupo_info} removido por {usuario_atual}", "INFO")
                
                print("Produto removido com sucesso!")
            else:
                print("Opção inválida.")
        except ValueError:
            print("Entrada inválida. Digite um número.")
    else:
        print("Arquivo de produtos monitorados não encontrado.")

def listar_dominios_seletores():
    """
    Lista todos os domínios e seus seletores CSS salvos.
    """
    dominios_seletores = carregar_dominios_seletores()
    
    if not dominios_seletores:
        print("Não há domínios e seletores salvos.")
        return
    
    print("\nDomínios e seletores cadastrados:")
    for i, (dominio, seletor) in enumerate(dominios_seletores.items(), 1):
        print(f"{i}. {dominio}: {seletor}")

def remover_dominio_seletor():
    """
    Remove um domínio e seu seletor da base.
    """
    dominios_seletores = carregar_dominios_seletores()
    
    if not dominios_seletores:
        print("Não há domínios e seletores salvos para remover.")
        return
    
    print("\nDomínios disponíveis para remoção:")
    dominios = list(dominios_seletores.keys())
    for i, dominio in enumerate(dominios, 1):
        print(f"{i}. {dominio}: {dominios_seletores[dominio]}")
    
    escolha = input("Digite o número do domínio que deseja remover (ou 'cancelar'): ")
    
    if escolha.lower() == 'cancelar':
        return
    
    try:
        indice = int(escolha) - 1
        if 0 <= indice < len(dominios):
            dominio_a_remover = dominios[indice]
            del dominios_seletores[dominio_a_remover]
            salvar_dominios_seletores(dominios_seletores)
            print(f"Domínio '{dominio_a_remover}' removido com sucesso!")
        else:
            print("Opção inválida.")
    except ValueError:
        print("Entrada inválida. Digite um número ou 'cancelar'.")

def listar_clientes(usuario_atual=None):
    """
    Lista todos os clientes cadastrados e a quantidade de produtos monitorados para cada um.
    Filtra os clientes de acordo com os grupos aos quais o usuário pertence.
    
    Args:
        usuario_atual (str, optional): Nome do usuário logado atualmente
        
    Returns:
        list: Lista dos clientes disponíveis
    """
    if os.path.isfile('produtos_monitorados.csv'):
        df_produtos = pd.read_csv('produtos_monitorados.csv')
        if df_produtos.empty:
            print("Não há clientes cadastrados.")
            return []
        
        # Obtém a lista completa de clientes
        todos_clientes = df_produtos['cliente'].unique().tolist()
        
        # Se um usuário está especificado, filtra a lista de acordo com as permissões
        clientes_permitidos = []
        if usuario_atual:
            # Se for admin, pode ver todos os clientes
            if usuario_atual == "admin" or "admin" in obter_clientes_usuario(usuario_atual):
                clientes_permitidos = todos_clientes
            else:
                # Filtra apenas os clientes que o usuário pode acessar
                clientes_autorizados = obter_clientes_usuario(usuario_atual)
                # Filtra apenas os clientes que o usuário pode acessar e que existem no sistema
                clientes_permitidos = [c for c in todos_clientes if c in clientes_autorizados]
        else:
            # Se nenhum usuário especificado, mostra todos os clientes
            clientes_permitidos = todos_clientes
        
        if not clientes_permitidos:
            print("Você não tem acesso a nenhum cliente.")
            return []
        
        print("\nClientes cadastrados:")
        for i, cliente in enumerate(clientes_permitidos, 1):
            num_produtos = len(df_produtos[df_produtos['cliente'] == cliente])
            print(f"{i}. {cliente} ({num_produtos} produtos)")
            
        return clientes_permitidos
    else:
        print("Não há clientes cadastrados.")
        return []

def visualizar_historico(usuario_atual=None, cliente_filtro=None):
    """
    Visualiza o histórico de preços com opções de filtro por cliente e produto.
    Filtra por grupo do usuário.
    
    Args:
        usuario_atual (str, optional): Nome do usuário logado atualmente
        cliente_filtro (str, optional): Nome do cliente para filtrar automaticamente
    """
    arquivo_csv = 'historico_precos.csv'
    
    if not os.path.isfile(arquivo_csv):
        print("Nenhum histórico de preços encontrado.")
        return
    
    try:
        # Carregar histórico de preços
        df_historico = pd.read_csv(arquivo_csv)
        if df_historico.empty:
            print("Ainda não há dados no histórico de preços.")
            return
            
        # Verifica se a coluna 'grupo' existe no histórico
        if 'grupo' not in df_historico.columns:
            # Adiciona a coluna grupo se não existir
            df_historico['grupo'] = 'admin'
            # Salva o arquivo atualizado
            df_historico.to_csv(arquivo_csv, index=False)
            
        # Determina o grupo do usuário
        grupo_usuario = None
        if usuario_atual:
            if usuario_atual == "admin" or "admin" in obter_grupos_usuario(usuario_atual):
                # Administradores veem todo o histórico
                pass
            else:
                # Usuários comuns veem apenas histórico do seu grupo
                grupos = obter_grupos_usuario(usuario_atual)
                # Filtra para obter apenas o grupo pessoal do usuário
                grupos_pessoais = [g for g in grupos if g != "all" and g != "admin"]
                if grupos_pessoais:
                    grupo_usuario = grupos_pessoais[0]  # Usa o primeiro grupo pessoal encontrado
                    # Filtra histórico apenas do grupo do usuário
                    df_historico = df_historico[df_historico['grupo'] == grupo_usuario]
                    
                    if df_historico.empty:
                        print("Não há histórico para os produtos do seu grupo.")
                        return
        
        # Se um cliente específico foi passado, filtra diretamente
        if cliente_filtro:
            if cliente_filtro in df_historico['cliente'].values:
                # Filtra diretamente para o cliente atual
                df_cliente = df_historico[df_historico['cliente'] == cliente_filtro]
                produtos_cliente = df_cliente['produto'].unique()
                
                if len(produtos_cliente) == 0:
                    print(f"Não há produtos com histórico para o cliente '{cliente_filtro}'.")
                    return
                
                print(f"\nProdutos disponíveis para o cliente '{cliente_filtro}':")
                for i, produto in enumerate(produtos_cliente, 1):
                    print(f"{i}. {produto}")
                
                escolha_produto = input("\nDigite o número do produto que deseja visualizar (ou 'todos' para ver todos): ")
                if escolha_produto.lower() == 'todos':
                    print(f"\nHistórico de preços de todos os produtos do cliente '{cliente_filtro}':")
                    # Reordene as colunas para mostrar 'concorrente' em vez de 'cliente'
                    colunas = ['data', 'produto', 'concorrente', 'preco', 'url']
                    df_display = df_cliente[colunas]
                    print(df_display)
                else:
                    try:
                        indice_produto = int(escolha_produto) - 1
                        if 0 <= indice_produto < len(produtos_cliente):
                            produto_selecionado = produtos_cliente[indice_produto]
                            historico_produto = df_cliente[df_cliente['produto'] == produto_selecionado]
                            print(f"\nHistórico de preços para '{produto_selecionado}' do cliente '{cliente_filtro}':")
                            # Reordene as colunas para mostrar 'concorrente' em vez de 'cliente'
                            colunas = ['data', 'concorrente', 'preco', 'url']
                            historico_display = historico_produto[colunas]
                            print(historico_display)
                        else:
                            print("Opção inválida.")
                    except ValueError:
                        print("Entrada inválida. Digite um número ou 'todos'.")
            else:
                print(f"Não há histórico para o cliente '{cliente_filtro}'.")
            return
        
        # Opção para filtrar por cliente primeiro
        clientes_unicos = df_historico['cliente'].unique()
        print("\nClientes disponíveis:")
        for i, cliente in enumerate(clientes_unicos, 1):
            print(f"{i}. {cliente}")
        
        escolha_cliente = input("\nDigite o número do cliente que deseja visualizar (ou 'todos' para ver todos): ")
        
        if escolha_cliente.lower() == 'todos':
            # Mostra todos os produtos de todos os clientes
            produtos_unicos = df_historico['produto'].unique()
            print("\nProdutos disponíveis:")
            for i, produto in enumerate(produtos_unicos, 1):
                print(f"{i}. {produto}")
            
            escolha_produto = input("\nDigite o número do produto que deseja visualizar (ou 'todos' para ver todos): ")
            if escolha_produto.lower() == 'todos':
                print("\nHistórico completo de preços:")
                # Reordene as colunas para mostrar 'concorrente' em vez de 'cliente'
                colunas = ['data', 'produto', 'concorrente', 'preco', 'url']
                df_display = df_historico[colunas]
                print(df_display)
            else:
                try:
                    indice = int(escolha_produto) - 1
                    if 0 <= indice < len(produtos_unicos):
                        produto_selecionado = produtos_unicos[indice]
                        historico_produto = df_historico[df_historico['produto'] == produto_selecionado]
                        print(f"\nHistórico de preços para '{produto_selecionado}':")
                        # Reordene as colunas para mostrar 'concorrente' em vez de 'cliente'
                        colunas = ['data', 'concorrente', 'preco', 'url']
                        historico_display = historico_produto[colunas]
                        print(historico_display)
                    else:
                        print("Opção inválida.")
                except ValueError:
                    print("Entrada inválida. Digite um número ou 'todos'.")
        else:
            try:
                indice_cliente = int(escolha_cliente) - 1
                if 0 <= indice_cliente < len(clientes_unicos):
                    cliente_selecionado = clientes_unicos[indice_cliente]
                    
                    # Filtra produtos do cliente selecionado
                    df_cliente = df_historico[df_historico['cliente'] == cliente_selecionado]
                    produtos_cliente = df_cliente['produto'].unique()
                    
                    print(f"\nProdutos disponíveis para o cliente '{cliente_selecionado}':")
                    for i, produto in enumerate(produtos_cliente, 1):
                        print(f"{i}. {produto}")
                    
                    escolha_produto = input("\nDigite o número do produto que deseja visualizar (ou 'todos' para ver todos): ")
                    if escolha_produto.lower() == 'todos':
                        print(f"\nHistórico de preços de todos os produtos do cliente '{cliente_selecionado}':")
                        # Reordene as colunas para mostrar 'concorrente' em vez de 'cliente'
                        colunas = ['data', 'produto', 'concorrente', 'preco', 'url']
                        df_display = df_cliente[colunas]
                        print(df_display)
                    else:
                        try:
                            indice_produto = int(escolha_produto) - 1
                            if 0 <= indice_produto < len(produtos_cliente):
                                produto_selecionado = produtos_cliente[indice_produto]
                                historico_produto = df_cliente[df_cliente['produto'] == produto_selecionado]
                                print(f"\nHistórico de preços para '{produto_selecionado}' do cliente '{cliente_selecionado}':")
                                # Reordene as colunas para mostrar 'concorrente' em vez de 'cliente'
                                colunas = ['data', 'concorrente', 'preco', 'url']
                                historico_display = historico_produto[colunas]
                                print(historico_display)
                            else:
                                print("Opção inválida.")
                        except ValueError:
                            print("Entrada inválida. Digite um número ou 'todos'.")
                else:
                    print("Opção inválida.")
            except ValueError:
                print("Entrada inválida. Digite um número ou 'todos'.")
    except Exception as e:
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
    
    # Criar arquivo de clientes se não existir
    arquivo_clientes = 'clientes.csv'
    
    try:
        import pandas as pd
        
        # Verifica se o arquivo já existe
        if os.path.isfile(arquivo_clientes):
            df_clientes = pd.read_csv(arquivo_clientes)
            
            # Verifica se o cliente já existe
            if nome_cliente in df_clientes['cliente'].values:
                print(f"Cliente '{nome_cliente}' já existe no sistema.")
                return True
                
            # Adiciona o novo cliente
            novo_cliente = pd.DataFrame({'cliente': [nome_cliente]})
            df_atualizado = pd.concat([df_clientes, novo_cliente], ignore_index=True)
            df_atualizado.to_csv(arquivo_clientes, index=False)
        else:
            # Cria o arquivo com o primeiro cliente
            df_clientes = pd.DataFrame({'cliente': [nome_cliente]})
            df_clientes.to_csv(arquivo_clientes, index=False)
        
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
        print(f"Erro ao adicionar cliente: {str(e)}")
        depurar_logs(f"Erro ao adicionar cliente '{nome_cliente}': {str(e)}", "ERROR")
        return False

def migrar_para_novo_formato():
    """
    Migra os dados do formato antigo para o novo formato.
    Separa URLs e seletores CSS dos produtos.
    
    Returns:
        bool: True se a migração foi bem-sucedida, False caso contrário
    """
    print("Iniciando migração para o novo formato de dados...")
    
    arquivo_produtos_antigo = 'produtos_monitorados.csv'
    arquivo_produtos_novo = 'produtos_monitorados_novo.csv'
    arquivo_urls = 'urls_monitoradas.csv'
    
    if not os.path.isfile(arquivo_produtos_antigo):
        print("Arquivo de produtos não encontrado. Não há dados para migrar.")
        # Criar arquivo de URLs vazio para evitar erros futuros
        pd.DataFrame(columns=['url', 'dominio', 'seletor_css']).to_csv(arquivo_urls, index=False)
        return False
    
    try:
        # Carrega dados existentes
        df_produtos = pd.read_csv(arquivo_produtos_antigo)
        
        if df_produtos.empty:
            print("Não há produtos para migrar.")
            # Criar arquivo de URLs vazio para evitar erros futuros
            pd.DataFrame(columns=['url', 'dominio', 'seletor_css']).to_csv(arquivo_urls, index=False)
            return False
        
        # Verifica se o arquivo já contém a estrutura antiga (com seletor_css)
        if 'seletor_css' not in df_produtos.columns:
            print("Os dados já parecem estar no novo formato.")
            # Verifica se o arquivo de URLs existe
            if not os.path.isfile(arquivo_urls):
                print("Arquivo de URLs não encontrado. Criando arquivo vazio.")
                pd.DataFrame(columns=['url', 'dominio', 'seletor_css']).to_csv(arquivo_urls, index=False)
            return True
        
        # Extrai dados para o arquivo de URLs
        urls_unicas = df_produtos[['url', 'seletor_css']].drop_duplicates()
        
        # Adiciona a coluna 'dominio'
        from scraper import extrair_dominio
        urls_unicas['dominio'] = urls_unicas['url'].apply(extrair_dominio)
        
        # Cria o novo DataFrame de produtos sem a coluna seletor_css
        df_produtos_novo = df_produtos.drop(columns=['seletor_css'])
        
        # Salva os novos arquivos
        urls_unicas.to_csv(arquivo_urls, index=False)
        df_produtos_novo.to_csv(arquivo_produtos_novo, index=False)
        
        # Backup do arquivo antigo
        import shutil
        from datetime import datetime
        data_backup = datetime.now().strftime('%Y%m%d_%H%M%S')
        shutil.copy2(arquivo_produtos_antigo, f"{arquivo_produtos_antigo}.{data_backup}.bak")
        
        # Substitui o arquivo antigo pelo novo
        os.remove(arquivo_produtos_antigo)  # Remove o arquivo antigo primeiro
        shutil.move(arquivo_produtos_novo, arquivo_produtos_antigo)
        
        print("Migração concluída com sucesso:")
        print(f"- {len(urls_unicas)} URLs únicas extraídas")
        print(f"- {len(df_produtos_novo)} produtos migrados para o novo formato")
        print(f"- Backup do arquivo original criado: {arquivo_produtos_antigo}.{data_backup}.bak")
        
        return True
        
    except Exception as e:
        print(f"Erro durante a migração: {e}")
        # Criar arquivo de URLs vazio se não existir
        if not os.path.isfile(arquivo_urls):
            pd.DataFrame(columns=['url', 'dominio', 'seletor_css']).to_csv(arquivo_urls, index=False)
        return False