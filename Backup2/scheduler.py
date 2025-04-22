#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo de agendamento para o Sistema de Monitoramento de Preços
---------------------------------------------------------------
Versão para banco de dados SQLite.
"""

import os
import time
import json
import schedule
from datetime import datetime
from utils import depurar_logs
from scraper import registrar_preco
from grupos_bd import obter_grupos_usuario, usuario_pode_acessar_cliente

def processar_fila_agendamento():
    """
    Processa a fila de agendamento, verificando os produtos na ordem da fila.
    Esta função é chamada automaticamente pelo agendador nos horários configurados.
    
    Returns:
        bool: True se o processamento foi concluído com sucesso, False caso contrário
    """
    from utils import depurar_logs
    
    depurar_logs("Iniciando processamento da fila de agendamento", "INFO")
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Iniciando processamento da fila...")
    
    # Obter os produtos da fila
    produtos = obter_proximos_produtos_fila()
    
    if not produtos:
        depurar_logs("Fila de agendamento vazia", "INFO")
        print("Fila vazia. Nenhum produto para verificar.")
        return True
    
    print(f"Processando {len(produtos)} produtos da fila...")
    sucesso = True
    
    # Processar cada produto da fila
    for id_produto in produtos:
        try:
            # Buscar informações do produto
            from database_config import criar_conexao
            conexao, cursor = criar_conexao()
            
            cursor.execute('''
            SELECT p.id, c.nome as cliente, p.nome as produto, p.concorrente, p.url,
                   pl.seletor_css as plataforma_seletor, d.seletor_css as dominio_seletor
            FROM produtos p
            JOIN clientes c ON p.id_cliente = c.id
            LEFT JOIN plataformas pl ON p.id_plataforma = pl.id
            LEFT JOIN dominios d ON d.nome = ?
            WHERE p.id = ?
            ''', (extrair_dominio(p.url), id_produto))
            
            produto_info = cursor.fetchone()
            conexao.close()
            
            if not produto_info:
                depurar_logs(f"Produto ID {id_produto} não encontrado no banco de dados", "WARNING")
                continue
            
            # Registrar o preço do produto
            from scraper import registrar_preco, extrair_dominio
            
            # Determinar qual seletor CSS usar
            seletor_css = produto_info['plataforma_seletor'] or produto_info['dominio_seletor']
            
            if not seletor_css:
                # Se não encontrou seletor no banco, tenta buscar pelo domínio
                dominio = extrair_dominio(produto_info['url'])
                from database_bd import carregar_dominios_seletores
                dominios_seletores = carregar_dominios_seletores()
                
                if dominio in dominios_seletores:
                    seletor_css = dominios_seletores[dominio]
                else:
                    depurar_logs(f"Seletor CSS não encontrado para o produto ID {id_produto}", "WARNING")
                    print(f"Seletor CSS não encontrado para o produto ID {id_produto}")
                    continue
            
            print(f"Verificando produto: {produto_info['produto']} (ID: {id_produto})")
            resultado = registrar_preco(
                cliente=produto_info['cliente'],
                produto=produto_info['produto'],
                concorrente=produto_info['concorrente'],
                url=produto_info['url'],
                id_produto=id_produto,
                seletor_css=seletor_css
            )
            
            if resultado:
                # Mover o produto para o final da fila
                mover_produto_final_fila(id_produto)
            else:
                depurar_logs(f"Falha ao verificar preço do produto ID {id_produto}", "WARNING")
                sucesso = False
            
        except Exception as e:
            depurar_logs(f"Erro ao processar produto ID {id_produto}: {e}", "ERROR")
            print(f"Erro ao processar produto ID {id_produto}: {e}")
            sucesso = False
    
    depurar_logs("Processamento da fila de agendamento concluído", "INFO")
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Processamento da fila concluído!")
    return sucesso

def monitorar_todos_produtos(usuario_atual=None, verificacao_manual=False, limite_produtos=None):
    """
    Monitora produtos cadastrados, extraindo e registrando seus preços.
    Suporta verificação manual ou automática via fila.
    
    Args:
        usuario_atual (str, optional): Nome do usuário que solicitou o monitoramento
        verificacao_manual (bool, optional): Se True, marca os produtos como verificados manualmente
        limite_produtos (int, optional): Limita o número de produtos a serem verificados
    
    Returns:
        bool: True se pelo menos um produto foi monitorado com sucesso, False caso contrário
    """
    try:
        from database_config import criar_conexao
        from grupos_bd import obter_grupos_usuario
        from scraper import registrar_preco, extrair_dominio
        from utils import depurar_logs
        
        # Modo de verificação
        if verificacao_manual:
            depurar_logs(f"Iniciando monitoramento manual por {usuario_atual}", "INFO")
            print("Modo: Verificação manual (produtos serão removidos da fila do dia)")
        else:
            depurar_logs("Iniciando monitoramento automático via fila", "INFO")
            print("Modo: Verificação automática (produtos irão para o final da fila)")
        
        # Se é um monitoramento automático e temos um limite, usamos a fila
        if not verificacao_manual and limite_produtos:
            print(f"Buscando os próximos {limite_produtos} produtos da fila...")
            produtos_ids = obter_proximos_produtos_fila(limite_produtos)
            
            if not produtos_ids:
                print("Fila de agendamento vazia. Nenhum produto para verificar.")
                return True
                
            produtos = []
            conexao, cursor = criar_conexao()
            
            for id_produto in produtos_ids:
                cursor.execute('''
                SELECT p.id, c.nome as cliente, p.nome as produto, p.concorrente, p.url
                FROM produtos p
                JOIN clientes c ON p.id_cliente = c.id
                WHERE p.id = ?
                ''', (id_produto,))
                
                resultado = cursor.fetchone()
                if resultado:
                    produtos.append(dict(resultado))
            
            conexao.close()
            
        else:
            # Monitoramento manual ou sem limite - usa filtro por grupo como antes
            conexao, cursor = criar_conexao()
            
            # Determina os grupos do usuário para filtrar
            where_grupo = ""
            params = []
            
            if usuario_atual == "admin" or (usuario_atual and "admin" in obter_grupos_usuario(usuario_atual)):
                # Administradores monitoram todos os produtos
                pass
            else:
                if not usuario_atual:
                    print("Usuário não identificado. Não é possível monitorar produtos.")
                    conexao.close()
                    return False
                    
                grupos = obter_grupos_usuario(usuario_atual)
                if not grupos:
                    print("Você não tem acesso a nenhum grupo para monitorar produtos.")
                    conexao.close()
                    return False
                    
                # Filtra para obter apenas o grupo pessoal do usuário
                grupos_pessoais = [g for g in grupos if g != "all" and g != "admin"]
                if not grupos_pessoais:
                    print("Você não tem um grupo pessoal. Não é possível monitorar produtos.")
                    conexao.close()
                    return False
                    
                grupo_usuario = grupos_pessoais[0]  # Usa o primeiro grupo pessoal encontrado
                
                # Filtrar por grupo do usuário
                where_grupo = "AND g.id_grupo = ?"
                params.append(grupo_usuario)
            
            # Buscar todos os produtos
            cursor.execute('''
            SELECT p.id, c.nome as cliente, p.nome as produto, p.concorrente, p.url 
            FROM produtos p
            JOIN clientes c ON p.id_cliente = c.id
            JOIN grupos g ON p.id_grupo = g.id
            WHERE 1=1 ''' + where_grupo + '''
            ORDER BY c.nome, p.nome
            ''', params)
            
            produtos = [dict(row) for row in cursor.fetchall()]
            conexao.close()
        
        if not produtos:
            print("Não há produtos cadastrados para monitorar.")
            return False
        
        total_produtos = len(produtos)
        print(f"Iniciando monitoramento de {total_produtos} produtos...")
        sucesso = False
        produtos_verificados = 0
        
        for produto in produtos:
            try:
                # Determinar o domínio para buscar o seletor
                dominio = extrair_dominio(produto['url'])
                
                # Buscar seletor da plataforma e domínio
                conexao, cursor = criar_conexao()
                
                # Buscar seletor da plataforma (se existir)
                cursor.execute('''
                SELECT pl.seletor_css 
                FROM produtos p
                JOIN plataformas pl ON p.id_plataforma = pl.id
                WHERE p.id = ?
                ''', (produto['id'],))
                
                plataforma_result = cursor.fetchone()
                plataforma_seletor = plataforma_result['seletor_css'] if plataforma_result else None
                
                # Buscar seletor do domínio (se existir)
                cursor.execute('''
                SELECT seletor_css FROM dominios WHERE nome = ?
                ''', (dominio,))
                
                dominio_result = cursor.fetchone()
                dominio_seletor = dominio_result['seletor_css'] if dominio_result else None
                
                conexao.close()
                
                # Determinar qual seletor CSS usar
                seletor_css = plataforma_seletor or dominio_seletor
                
                if not seletor_css:
                    # Se não encontrou seletor no banco, tenta buscar pelo domínio
                    from database_bd import carregar_dominios_seletores
                    dominios_seletores = carregar_dominios_seletores()
                    
                    if dominio in dominios_seletores:
                        seletor_css = dominios_seletores[dominio]
                    else:
                        print(f"Não foi encontrado um seletor CSS para a URL: {produto['url']} (Produto ID: {produto['id']})")
                        continue
                
                print(f"Verificando produto: {produto['produto']} (Cliente: {produto['cliente']})")
                resultado = registrar_preco(
                    cliente=produto['cliente'],
                    produto=produto['produto'],
                    concorrente=produto['concorrente'],
                    url=produto['url'],
                    id_produto=produto['id'],
                    seletor_css=seletor_css,
                    usuario_atual=usuario_atual,
                    verificacao_manual=verificacao_manual
                )
                
                if resultado:
                    sucesso = True
                    produtos_verificados += 1
                    print(f"Progresso: {produtos_verificados}/{total_produtos} produtos verificados")
                
                # Pausa pequena entre as verificações para não sobrecarregar os servidores
                time.sleep(0.5)
                
            except Exception as e:
                depurar_logs(f"Erro ao monitorar produto ID {produto['id']}: {e}", "ERROR")
                print(f"Erro ao monitorar produto ID {produto['id']}: {e}")
                continue
        
        print(f"Monitoramento concluído! {produtos_verificados}/{total_produtos} produtos verificados com sucesso.")
        return sucesso
        
    except Exception as e:
        depurar_logs(f"Erro ao executar monitoramento: {e}", "ERROR")
        print(f"Erro ao executar monitoramento: {e}")
        return False

def configurar_agendamento():
    """
    Interface para configurar o agendamento automático do monitoramento 2x por semana.
    
    Returns:
        tuple: (schedule_info, sucesso), onde schedule_info é um dicionário com as informações 
        do agendamento e sucesso é um booleano indicando se a configuração foi bem-sucedida
    """
    print("\nConfigurando agendamento para execução 2x por semana")
    
    schedule_info = {"tipo": "semanal", "dias": [], "horario": None}
    
    # Seleção dos dias da semana
    print("\nSelecione dois dias da semana para executar o agendamento:")
    print("1. Segunda-feira")
    print("2. Terça-feira")
    print("3. Quarta-feira")
    print("4. Quinta-feira")
    print("5. Sexta-feira")
    print("6. Sábado")
    print("7. Domingo")
    
    dias_selecionados = []
    dias_semana = ['segunda', 'terca', 'quarta', 'quinta', 'sexta', 'sabado', 'domingo']
    
    while len(dias_selecionados) < 2:
        try:
            escolha = int(input(f"Escolha o {len(dias_selecionados) + 1}º dia (1-7): "))
            if 1 <= escolha <= 7:
                dia = dias_semana[escolha - 1]
                
                if dia not in dias_selecionados:
                    dias_selecionados.append(dia)
                else:
                    print("Este dia já foi selecionado. Escolha outro dia.")
            else:
                print("Opção inválida. Digite um número entre 1 e 7.")
        except ValueError:
            print("Entrada inválida. Digite um número.")
    
    # Seleção do horário
    horario = input("\nDigite o horário para execução (formato HH:MM): ")
    try:
        # Valida o formato do horário
        horas, minutos = map(int, horario.split(':'))
        if not (0 <= horas <= 23 and 0 <= minutos <= 59):
            print("Horário inválido. Use o formato HH:MM (ex: 08:30).")
            return None, False
            
        schedule_info["dias"] = dias_selecionados
        schedule_info["horario"] = horario
        
        print(f"\nAgendamento configurado para {dias_selecionados[0]} e {dias_selecionados[1]} às {horario}.")
        return schedule_info, True
        
    except ValueError:
        print("Formato de horário inválido. Use o formato HH:MM (ex: 08:30).")
        return None, False

def executar_agendador():
    """
    Inicia o loop de execução do agendador, verificando periodicamente 
    se há tarefas pendentes a serem executadas.
    """
    from utils import depurar_logs
    
    # Carregar configuração do agendamento
    config = carregar_configuracao_agendamento()
    if not config:
        print("Nenhuma configuração de agendamento encontrada. Use 'configurar_agendamento()' para configurar.")
        return
    
    # Configurar o schedule com base nas configurações do banco
    horario = config.get("horario")
    dias = config.get("dias", [])
    
    if not horario or not dias:
        print("Configuração de agendamento incompleta. Use 'configurar_agendamento()' para reconfigurar.")
        return
    
    # Mapear dias da semana para funções do schedule
    dias_semana = {
        'segunda': schedule.every().monday,
        'terca': schedule.every().tuesday,
        'quarta': schedule.every().wednesday,
        'quinta': schedule.every().thursday,
        'sexta': schedule.every().friday,
        'sabado': schedule.every().saturday,
        'domingo': schedule.every().sunday
    }
    
    # Configurar agendamento para cada dia selecionado
    for dia in dias:
        if dia in dias_semana:
            dias_semana[dia].at(horario).do(processar_fila_agendamento)
            print(f"Agendamento configurado para {dia} às {horario}")
    
    print("Agendador iniciado. Pressione Ctrl+C para encerrar.")
    depurar_logs("Agendador iniciado", "INFO")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Verifica a cada minuto
    except KeyboardInterrupt:
        print("\nAgendador encerrado.")
        depurar_logs("Agendador encerrado pelo usuário", "INFO")

def salvar_configuracao_agendamento(schedule_info):
    """
    Salva a configuração de agendamento na tabela de agendamento do banco de dados.
    
    Args:
        schedule_info (dict): Dicionário com as informações do agendamento
    """
    try:
        from database_config import criar_conexao
        from utils import depurar_logs
        
        conexao, cursor = criar_conexao()
        
        # Verificar se já existe uma configuração
        cursor.execute("SELECT id FROM agendamento")
        agendamento_existente = cursor.fetchone()
        
        data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        tipo = schedule_info.get('tipo', '')
        dias = schedule_info.get('dias', [])
        dias_str = ','.join(dias) if dias else ""
        horario = schedule_info.get('horario', '')
        
        if agendamento_existente:
            # Atualizar configuração existente
            cursor.execute('''
            UPDATE agendamento 
            SET tipo = ?, dia = ?, horario = ?, data_criacao = ? 
            WHERE id = ?
            ''', (tipo, dias_str, horario, data_atual, agendamento_existente['id']))
        else:
            # Inserir nova configuração
            cursor.execute('''
            INSERT INTO agendamento (tipo, dia, horario, ativo, data_criacao)
            VALUES (?, ?, ?, ?, ?)
            ''', (tipo, dias_str, horario, 1, data_atual))
        
        conexao.commit()
        conexao.close()
        
        depurar_logs("Configuração de agendamento salva no banco de dados", "INFO")
        print("Configuração de agendamento salva no banco de dados.")
        
    except Exception as e:
        from utils import depurar_logs
        depurar_logs(f"Erro ao salvar configuração de agendamento: {e}", "ERROR")
        print(f"Erro ao salvar configuração de agendamento: {e}")

        
def carregar_configuracao_agendamento():
    """
    Carrega a configuração de agendamento do banco de dados.
    
    Returns:
        dict: Dicionário com as informações do agendamento, ou None se não existir
    """
    try:
        from database_config import criar_conexao
        from utils import depurar_logs
        
        conexao, cursor = criar_conexao()
        
        cursor.execute("SELECT tipo, dia, horario FROM agendamento WHERE ativo = 1")
        config = cursor.fetchone()
        
        conexao.close()
        
        if config:
            # Converter para o formato de dicionário
            dias_str = config['dia'] if config['dia'] else ""
            dias = dias_str.split(',') if dias_str else []
            
            schedule_info = {
                "tipo": config['tipo'],
                "dias": dias,
                "horario": config['horario']
            }
            return schedule_info
        
        depurar_logs("Nenhuma configuração de agendamento encontrada", "INFO")
        return None
            
    except Exception as e:
        from utils import depurar_logs
        depurar_logs(f"Erro ao carregar configuração de agendamento: {e}", "ERROR")
        print(f"Erro ao carregar configuração de agendamento: {e}")
        return None
        
def restaurar_agendamento():
    """
    Restaura o agendamento a partir da configuração salva.
    
    Returns:
        bool: True se o agendamento foi restaurado, False caso contrário
    """
    config = carregar_configuracao_agendamento()
    if not config:
        return False
        
    try:
        tipo = config.get("tipo")
        dia = config.get("dia")
        horario = config.get("horario")
        
        if not (tipo and horario):
            return False
            
        if tipo == "diario":
            schedule.every().day.at(horario).do(monitorar_todos_produtos)
            print(f"Monitoramento restaurado: todos os dias às {horario}.")
        elif tipo == "semanal" and dia:
            dias = {
                'segunda': schedule.every().monday,
                'terca': schedule.every().tuesday,
                'quarta': schedule.every().wednesday,
                'quinta': schedule.every().thursday,
                'sexta': schedule.every().friday,
                'sabado': schedule.every().saturday,
                'domingo': schedule.every().sunday
            }
            if dia in dias:
                dias[dia].at(horario).do(monitorar_todos_produtos)
                print(f"Monitoramento restaurado: toda {dia} às {horario}.")
            else:
                return False
        elif tipo == "mensal" and dia:
            schedule.every().month.at(f"{int(dia):02d} {horario}").do(monitorar_todos_produtos)
            print(f"Monitoramento restaurado: dia {dia} de cada mês às {horario}.")
        else:
            return False
            
        return True
    except Exception as e:
        print(f"Erro ao restaurar agendamento: {e}")
        return False

# Atualizar registro de última execução
def atualizar_ultima_execucao():
    """
    Atualiza o registro de última execução do agendamento.
    """
    try:
        from database_config import criar_conexao
        
        conexao, cursor = criar_conexao()
        
        data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute("UPDATE agendamento SET ultima_execucao = ?", (data_atual,))
        
        conexao.commit()
        conexao.close()
        
        depurar_logs(f"Registro de última execução atualizado: {data_atual}", "INFO")
        
    except Exception as e:
        depurar_logs(f"Erro ao atualizar registro de última execução: {e}", "ERROR")

def adicionar_produto_fila(id_produto):
    """
    Adiciona um produto à fila de agendamento na última posição.
    
    Args:
        id_produto (int): ID do produto a ser adicionado na fila
        
    Returns:
        bool: True se o produto foi adicionado com sucesso, False caso contrário
    """
    try:
        from database_config import criar_conexao
        from utils import depurar_logs
        
        conexao, cursor = criar_conexao()
        
        # Verificar se o produto já está na fila
        cursor.execute("SELECT id FROM fila_agendamento WHERE id_produto = ?", (id_produto,))
        if cursor.fetchone():
            conexao.close()
            return True  # Produto já está na fila
        
        # Buscar a última posição da fila
        cursor.execute("SELECT MAX(posicao_fila) as ultima_posicao FROM fila_agendamento")
        resultado = cursor.fetchone()
        ultima_posicao = resultado['ultima_posicao'] if resultado and resultado['ultima_posicao'] is not None else 0
        
        # Adicionar o produto na última posição
        data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
        INSERT INTO fila_agendamento (id_produto, posicao_fila, data_inclusao)
        VALUES (?, ?, ?)
        ''', (id_produto, ultima_posicao + 1, data_atual))
        
        conexao.commit()
        conexao.close()
        
        depurar_logs(f"Produto ID {id_produto} adicionado à fila de agendamento", "INFO")
        return True
        
    except Exception as e:
        from utils import depurar_logs
        depurar_logs(f"Erro ao adicionar produto à fila: {e}", "ERROR")
        print(f"Erro ao adicionar produto à fila: {e}")
        return False
    
def mover_produto_final_fila(id_produto):
    """
    Move um produto verificado para o final da fila.
    
    Args:
        id_produto (int): ID do produto a ser movido
        
    Returns:
        bool: True se o produto foi movido com sucesso, False caso contrário
    """
    try:
        from database_config import criar_conexao
        from utils import depurar_logs
        
        conexao, cursor = criar_conexao()
        
        # Verificar se o produto está na fila
        cursor.execute("SELECT id FROM fila_agendamento WHERE id_produto = ?", (id_produto,))
        if not cursor.fetchone():
            conexao.close()
            return False  # Produto não está na fila
        
        # Buscar a última posição da fila
        cursor.execute("SELECT MAX(posicao_fila) as ultima_posicao FROM fila_agendamento")
        resultado = cursor.fetchone()
        ultima_posicao = resultado['ultima_posicao'] if resultado and resultado['ultima_posicao'] is not None else 0
        
        # Atualizar a posição do produto para o final da fila
        data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
        UPDATE fila_agendamento 
        SET posicao_fila = ?, ultima_verificacao = ?, verificacao_manual = 0
        WHERE id_produto = ?
        ''', (ultima_posicao + 1, data_atual, id_produto))
        
        # Reorganizar a fila (opcional, mas mantém os números sequenciais)
        cursor.execute('''
        SELECT id, id_produto, posicao_fila
        FROM fila_agendamento
        ORDER BY posicao_fila
        ''')
        
        produtos_fila = cursor.fetchall()
        
        for i, produto in enumerate(produtos_fila, 1):
            cursor.execute('''
            UPDATE fila_agendamento
            SET posicao_fila = ?
            WHERE id = ?
            ''', (i, produto['id']))
        
        conexao.commit()
        conexao.close()
        
        depurar_logs(f"Produto ID {id_produto} movido para o final da fila", "INFO")
        return True
        
    except Exception as e:
        from utils import depurar_logs
        depurar_logs(f"Erro ao mover produto para o final da fila: {e}", "ERROR")
        print(f"Erro ao mover produto para o final da fila: {e}")
        return False
    
def remover_produto_fila_dia(id_produto):
    """
    Marca um produto como verificado manualmente para removê-lo da fila do dia.
    
    Args:
        id_produto (int): ID do produto a ser removido da fila do dia
        
    Returns:
        bool: True se o produto foi marcado com sucesso, False caso contrário
    """
    try:
        from database_config import criar_conexao
        from utils import depurar_logs
        
        conexao, cursor = criar_conexao()
        
        # Verificar se o produto está na fila
        cursor.execute("SELECT id FROM fila_agendamento WHERE id_produto = ?", (id_produto,))
        if not cursor.fetchone():
            conexao.close()
            return False  # Produto não está na fila
        
        # Marcar o produto como verificado manualmente
        data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
        UPDATE fila_agendamento 
        SET verificacao_manual = 1, ultima_verificacao = ?
        WHERE id_produto = ?
        ''', (data_atual, id_produto))
        
        conexao.commit()
        conexao.close()
        
        depurar_logs(f"Produto ID {id_produto} removido da fila do dia (verificação manual)", "INFO")
        return True
        
    except Exception as e:
        from utils import depurar_logs
        depurar_logs(f"Erro ao remover produto da fila do dia: {e}", "ERROR")
        print(f"Erro ao remover produto da fila do dia: {e}")
        return False
    
def obter_proximos_produtos_fila(limite=50):
    """
    Obtém os próximos produtos da fila para verificação.
    
    Args:
        limite (int): Número máximo de produtos a serem retornados
        
    Returns:
        list: Lista de IDs dos produtos na ordem da fila
    """
    try:
        from database_config import criar_conexao
        from utils import depurar_logs
        
        conexao, cursor = criar_conexao()
        
        # Buscar os próximos produtos na fila 
        # Excluindo os que foram verificados manualmente hoje
        data_hoje = datetime.now().strftime('%Y-%m-%d')
        
        cursor.execute('''
        SELECT id_produto 
        FROM fila_agendamento
        WHERE (verificacao_manual = 0 OR substr(ultima_verificacao, 1, 10) != ?)
        ORDER BY posicao_fila
        LIMIT ?
        ''', (data_hoje, limite))
        
        produtos = [row['id_produto'] for row in cursor.fetchall()]
        
        conexao.close()
        
        depurar_logs(f"Obtidos {len(produtos)} produtos da fila para verificação", "INFO")
        return produtos
        
    except Exception as e:
        from utils import depurar_logs
        depurar_logs(f"Erro ao obter produtos da fila: {e}", "ERROR")
        print(f"Erro ao obter produtos da fila: {e}")
        return []
    
def adicionar_novo_produto_ao_banco_e_fila(cliente, produto, concorrente, url, seletor_css, usuario_atual=None):
    """
    Adiciona um novo produto ao banco de dados e à fila de agendamento.
    Esta função estende o comportamento da função adicionar_produto original.
    
    Args:
        cliente (str): Nome do cliente
        produto (str): Nome do produto
        concorrente (str): Nome do concorrente
        url (str): URL do produto
        seletor_css (str): Seletor CSS para extrair o preço
        usuario_atual (str, optional): Nome do usuário que está adicionando o produto
        
    Returns:
        tuple: (id_produto, sucesso) onde id_produto é o ID do produto adicionado
               e sucesso é um booleano indicando se a operação foi bem-sucedida
    """
    try:
        # Chamar a função original para adicionar o produto ao banco
        from database_bd import adicionar_produto
        
        sucesso = adicionar_produto(
            cliente=cliente,
            produto=produto,
            concorrente=concorrente,
            url=url,
            usuario_atual=usuario_atual
        )
        
        if not sucesso:
            from utils import depurar_logs
            depurar_logs(f"Falha ao adicionar produto '{produto}'", "ERROR")
            return None, False
        
        # Buscar o ID do produto recém adicionado
        from database_config import criar_conexao
        conexao, cursor = criar_conexao()
        
        cursor.execute('''
        SELECT p.id 
        FROM produtos p
        JOIN clientes c ON p.id_cliente = c.id
        WHERE c.nome = ? AND p.nome = ? AND p.url = ?
        ''', (cliente, produto, url))
        
        resultado = cursor.fetchone()
        conexao.close()
        
        if not resultado:
            from utils import depurar_logs
            depurar_logs(f"Produto '{produto}' adicionado, mas não foi possível encontrar seu ID", "WARNING")
            return None, False
        
        id_produto = resultado['id']
        
        # Adicionar o produto à fila de agendamento
        sucesso_fila = adicionar_produto_fila(id_produto)
        
        if sucesso_fila:
            from utils import depurar_logs
            depurar_logs(f"Produto '{produto}' (ID: {id_produto}) adicionado à fila de agendamento", "INFO")
            return id_produto, True
        else:
            from utils import depurar_logs
            depurar_logs(f"Produto '{produto}' adicionado ao banco, mas falha ao adicionar à fila", "WARNING")
            return id_produto, False
        
    except Exception as e:
        from utils import depurar_logs
        depurar_logs(f"Erro ao adicionar produto ao banco e à fila: {e}", "ERROR")
        print(f"Erro ao adicionar produto ao banco e à fila: {e}")
        return None, False