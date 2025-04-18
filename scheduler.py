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

def monitorar_todos_produtos(usuario_atual=None):
    """
    Monitora todos os produtos cadastrados, extraindo e registrando seus preços.
    
    Args:
        usuario_atual (str, optional): Nome do usuário que solicitou o monitoramento
    
    Returns:
        bool: True se pelo menos um produto foi monitorado com sucesso, False caso contrário
    """
    try:
        from database_config import criar_conexao
        from grupos_bd import obter_grupos_usuario
        from scraper import registrar_preco, extrair_dominio
        
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
        query = f'''
        SELECT p.id, c.nome as cliente, p.nome as produto, p.concorrente, p.url, 
               pl.seletor_css as plataforma_seletor, d.seletor_css as dominio_seletor
        FROM produtos p
        JOIN clientes c ON p.id_cliente = c.id
        JOIN grupos g ON p.id_grupo = g.id
        LEFT JOIN plataformas pl ON p.id_plataforma = pl.id
        LEFT JOIN dominios d ON d.nome = ?
        WHERE 1=1 {where_grupo}
        ORDER BY c.nome, p.nome
        '''
        
        produtos = []
        
        # Para cada produto, vamos determinar o seletor correto depois
        for p in cursor.execute('''
        SELECT p.id, c.nome as cliente, p.nome as produto, p.concorrente, p.url 
        FROM produtos p
        JOIN clientes c ON p.id_cliente = c.id
        JOIN grupos g ON p.id_grupo = g.id
        WHERE 1=1 ''' + where_grupo + '''
        ORDER BY c.nome, p.nome
        ''', params):
            dominio = extrair_dominio(p['url'])
            
            # Buscar seletor da plataforma (se existir)
            cursor.execute('''
            SELECT pl.seletor_css 
            FROM produtos p
            JOIN plataformas pl ON p.id_plataforma = pl.id
            WHERE p.id = ?
            ''', (p['id'],))
            
            plataforma_result = cursor.fetchone()
            plataforma_seletor = plataforma_result['seletor_css'] if plataforma_result else None
            
            # Buscar seletor do domínio (se existir)
            cursor.execute('''
            SELECT seletor_css FROM dominios WHERE nome = ?
            ''', (dominio,))
            
            dominio_result = cursor.fetchone()
            dominio_seletor = dominio_result['seletor_css'] if dominio_result else None
            
            # Adicionar todas as informações ao produto
            produto_info = dict(p)
            produto_info['plataforma_seletor'] = plataforma_seletor
            produto_info['dominio_seletor'] = dominio_seletor
            produto_info['dominio'] = dominio
            
            produtos.append(produto_info)
        
        conexao.close()
        
        if not produtos:
            print("Não há produtos cadastrados para monitorar.")
            return False
        
        print(f"Iniciando monitoramento de {len(produtos)} produtos...")
        sucesso = False
        
        for produto in produtos:
            try:
                # Determinar qual seletor CSS usar
                seletor_css = produto['plataforma_seletor'] or produto['dominio_seletor']
                
                if not seletor_css:
                    # Se não encontrou seletor no banco, tenta buscar pelo domínio
                    dominio = produto['dominio']
                    from database_bd import carregar_dominios_seletores
                    dominios_seletores = carregar_dominios_seletores()
                    
                    if dominio in dominios_seletores:
                        seletor_css = dominios_seletores[dominio]
                    else:
                        print(f"Não foi encontrado um seletor CSS para a URL: {produto['url']}")
                        continue
                
                resultado = registrar_preco(
                    cliente=produto['cliente'],
                    produto=produto['produto'],
                    concorrente=produto['concorrente'],
                    url=produto['url'],
                    id_produto=produto['id'],
                    seletor_css=seletor_css,
                    usuario_atual=usuario_atual
                )
                
                if resultado:
                    sucesso = True
            except Exception as e:
                print(f"Erro ao monitorar produto {produto['produto']}: {e}")
                continue
        
        print("Monitoramento concluído!")
        return sucesso
        
    except Exception as e:
        print(f"Erro ao executar monitoramento: {e}")
        return False

def configurar_agendamento():
    """
    Interface para configurar o agendamento automático do monitoramento.
    
    Returns:
        tuple: (schedule_info, sucesso), onde schedule_info é um dicionário com as informações 
        do agendamento e sucesso é um booleano indicando se a configuração foi bem-sucedida
    """
    print("\nQuando deseja executar o monitoramento automático?")
    print("1. Diariamente")
    print("2. Semanalmente")
    print("3. Mensalmente")
    escolha = input("Escolha uma opção (1-3): ")
    
    schedule_info = {"tipo": None, "dia": None, "horario": None}
    
    if escolha == '1':
        horario = input("Digite o horário (formato HH:MM): ")
        try:
            # Valida o formato do horário (horas entre 0-23, minutos entre 0-59)
            horas, minutos = map(int, horario.split(':'))
            if not (0 <= horas <= 23 and 0 <= minutos <= 59):
                print("Horário inválido. Use o formato HH:MM (ex: 08:30).")
                return None, False
                
            schedule.every().day.at(horario).do(monitorar_todos_produtos)
            print(f"Monitoramento agendado para todos os dias às {horario}.")
            
            schedule_info["tipo"] = "diario"
            schedule_info["horario"] = horario
            return schedule_info, True
            
        except ValueError:
            print("Formato de horário inválido. Use o formato HH:MM (ex: 08:30).")
            return None, False
            
    elif escolha == '2':
        dia_semana = input("Digite o dia da semana (segunda, terca, quarta, quinta, sexta, sabado, domingo): ")
        horario = input("Digite o horário (formato HH:MM): ")
        
        try:
            # Valida o formato do horário
            horas, minutos = map(int, horario.split(':'))
            if not (0 <= horas <= 23 and 0 <= minutos <= 59):
                print("Horário inválido. Use o formato HH:MM (ex: 08:30).")
                return None, False
                
            dias = {
                'segunda': schedule.every().monday,
                'terca': schedule.every().tuesday,
                'quarta': schedule.every().wednesday,
                'quinta': schedule.every().thursday,
                'sexta': schedule.every().friday,
                'sabado': schedule.every().saturday,
                'domingo': schedule.every().sunday
            }
            
            if dia_semana.lower() in dias:
                dias[dia_semana.lower()].at(horario).do(monitorar_todos_produtos)
                print(f"Monitoramento agendado para toda {dia_semana} às {horario}.")
                
                schedule_info["tipo"] = "semanal"
                schedule_info["dia"] = dia_semana.lower()
                schedule_info["horario"] = horario
                return schedule_info, True
            else:
                print("Dia da semana inválido.")
                return None, False
        except ValueError:
            print("Formato de horário inválido. Use o formato HH:MM (ex: 08:30).")
            return None, False
            
    elif escolha == '3':
        dia = input("Digite o dia do mês (1-31): ")
        horario = input("Digite o horário (formato HH:MM): ")
        
        try:
            # Valida o formato do horário
            horas, minutos = map(int, horario.split(':'))
            if not (0 <= horas <= 23 and 0 <= minutos <= 59):
                print("Horário inválido. Use o formato HH:MM (ex: 08:30).")
                return None, False
                
            dia = int(dia)
            if 1 <= dia <= 31:
                # O formato para agendamento mensal no schedule é "day HH:MM"
                schedule.every().month.at(f"{dia:02d} {horario}").do(monitorar_todos_produtos)
                print(f"Monitoramento agendado para o dia {dia} de cada mês às {horario}.")
                
                schedule_info["tipo"] = "mensal"
                schedule_info["dia"] = dia
                schedule_info["horario"] = horario
                return schedule_info, True
            else:
                print("Dia do mês inválido.")
                return None, False
        except ValueError:
            print("Dia ou horário inválido. O dia deve ser um número entre 1 e 31 e o horário no formato HH:MM.")
            return None, False
    else:
        print("Opção inválida.")
        return None, False

def executar_agendador():
    """
    Inicia o loop de execução do agendador, verificando periodicamente 
    se há tarefas pendentes a serem executadas.
    """
    print("Agendador iniciado. Pressione Ctrl+C para encerrar.")
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Verifica a cada minuto
    except KeyboardInterrupt:
        print("\nAgendador encerrado.")

def salvar_configuracao_agendamento(schedule_info):
    """
    Salva a configuração de agendamento na tabela de agendamento do banco de dados.
    
    Args:
        schedule_info (dict): Dicionário com as informações do agendamento
    """
    try:
        from database_config import criar_conexao
        
        conexao, cursor = criar_conexao()
        
        # Verificar se já existe uma configuração
        cursor.execute("SELECT id FROM agendamento")
        agendamento_existente = cursor.fetchone()
        
        data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        tipo = schedule_info.get('tipo', '')
        dia = schedule_info.get('dia', '')
        horario = schedule_info.get('horario', '')
        
        if agendamento_existente:
            # Atualizar configuração existente
            cursor.execute('''
            UPDATE agendamento 
            SET tipo = ?, dia = ?, horario = ?, data_criacao = ? 
            WHERE id = ?
            ''', (tipo, str(dia), horario, data_atual, agendamento_existente['id']))
        else:
            # Inserir nova configuração
            cursor.execute('''
            INSERT INTO agendamento (tipo, dia, horario, ativo, data_criacao)
            VALUES (?, ?, ?, ?, ?)
            ''', (tipo, str(dia), horario, 1, data_atual))
        
        conexao.commit()
        conexao.close()
        
        print("Configuração de agendamento salva no banco de dados.")
        
        # Também salva em arquivo para compatibilidade
        with open('agendamento_config.json', 'w', encoding='utf-8') as f:
            json.dump(schedule_info, f, ensure_ascii=False, indent=4)
        
    except Exception as e:
        print(f"Erro ao salvar configuração de agendamento: {e}")
        
        # Fallback para salvar em arquivo
        with open('agendamento_config.json', 'w', encoding='utf-8') as f:
            json.dump(schedule_info, f, ensure_ascii=False, indent=4)
        print("Configuração de agendamento salva em arquivo.")

def carregar_configuracao_agendamento():
    """
    Carrega a configuração de agendamento do banco de dados.
    
    Returns:
        dict: Dicionário com as informações do agendamento, ou None se não existir
    """
    try:
        from database_config import criar_conexao
        
        conexao, cursor = criar_conexao()
        
        cursor.execute("SELECT tipo, dia, horario FROM agendamento WHERE ativo = 1")
        config = cursor.fetchone()
        
        conexao.close()
        
        if config:
            # Converter para o formato de dicionário
            schedule_info = {
                "tipo": config['tipo'],
                "dia": config['dia'],
                "horario": config['horario']
            }
            return schedule_info
            
        # Se não encontrar no banco, tenta carregar do arquivo
        if os.path.isfile('agendamento_config.json'):
            with open('agendamento_config.json', 'r', encoding='utf-8') as f:
                return json.load(f)
                
    except Exception as e:
        print(f"Erro ao carregar configuração de agendamento: {e}")
        
        # Fallback para carregar de arquivo
        try:
            if os.path.isfile('agendamento_config.json'):
                with open('agendamento_config.json', 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
            
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