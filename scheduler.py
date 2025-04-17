#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import pandas as pd
import schedule
from scraper import registrar_preco
from grupos import obter_clientes_usuario, usuario_pode_acessar_cliente, obter_grupos_usuario

def monitorar_todos_produtos(usuario_atual=None):
    """
    Monitora todos os produtos cadastrados, extraindo e registrando seus preços.
    Se um usuário for especificado, monitora apenas os produtos dos grupos
    aos quais o usuário tem acesso.
    
    Args:
        usuario_atual (str, optional): Nome do usuário que solicitou o monitoramento
    
    Returns:
        bool: True se pelo menos um produto foi monitorado com sucesso, False caso contrário
    """
    arquivo_produtos = 'produtos_monitorados.csv'
    arquivo_urls = 'urls_monitoradas.csv'
    
    if not os.path.isfile(arquivo_produtos):
        print("Arquivo de produtos monitorados não encontrado. Adicione produtos primeiro.")
        return False
        
    if not os.path.isfile(arquivo_urls):
        print("Arquivo de URLs monitoradas não encontrado. Isso pode causar problemas no monitoramento.")
    
    # Carregar dados de produtos
    try:
        df_produtos = pd.read_csv(arquivo_produtos)
        if df_produtos.empty:
            print("Não há produtos cadastrados para monitoramento.")
            return False
            
        # Verifica se a coluna 'grupo' existe
        if 'grupo' not in df_produtos.columns:
            # Adiciona a coluna grupo se não existir
            df_produtos['grupo'] = 'admin'
            # Salva o arquivo atualizado
            df_produtos.to_csv(arquivo_produtos, index=False)
    except Exception as e:
        print(f"Erro ao ler arquivo de produtos: {e}")
        return False
    
    # Carregar dados de URLs (com seletores CSS)
    try:
        if os.path.isfile(arquivo_urls):
            df_urls = pd.read_csv(arquivo_urls)
        else:
            print("Arquivo de URLs monitoradas não encontrado. Isso pode causar problemas no monitoramento.")
            df_urls = pd.DataFrame(columns=['url', 'dominio', 'seletor_css'])
    except Exception as e:
        print(f"Erro ao ler arquivo de URLs: {e}")
        df_urls = pd.DataFrame(columns=['url', 'dominio', 'seletor_css'])
    
    # Se um usuário for especificado, filtra os produtos de acordo com as permissões
    if usuario_atual:
        if usuario_atual == "admin" or "admin" in obter_grupos_usuario(usuario_atual):
            # Administradores monitoram todos os produtos
            pass
        else:
            # Usuários comuns monitoram apenas produtos do seu grupo
            grupos = obter_grupos_usuario(usuario_atual)
            # Filtra para obter apenas o grupo pessoal do usuário
            grupos_pessoais = [g for g in grupos if g != "all" and g != "admin"]
            if grupos_pessoais:
                grupo_usuario = grupos_pessoais[0]  # Usa o primeiro grupo pessoal encontrado
                # Filtra produtos apenas do grupo do usuário
                df_produtos = df_produtos[df_produtos['grupo'] == grupo_usuario]
                
                if df_produtos.empty:
                    print("Você não tem produtos no seu grupo para monitorar.")
                    return False
    
    print(f"Iniciando monitoramento de {len(df_produtos)} produtos...")
    sucesso = False
    
    for _, row in df_produtos.iterrows():
        try:
            # Busca o seletor CSS para a URL
            seletor_css = None
            url_row = df_urls[df_urls['url'] == row['url']]
            
            if not url_row.empty:
                seletor_css = url_row.iloc[0]['seletor_css']
            else:
                # Se não encontrar, busca pelo domínio
                from scraper import extrair_dominio
                dominio = extrair_dominio(row['url'])
                from database import carregar_dominios_seletores
                dominios_seletores = carregar_dominios_seletores()
                
                if dominio in dominios_seletores:
                    seletor_css = dominios_seletores[dominio]
                else:
                    print(f"Não foi encontrado um seletor CSS para a URL: {row['url']}")
                    continue
            
            resultado = registrar_preco(
                cliente=row['cliente'],
                produto=row['produto'],
                concorrente=row['concorrente'],
                url=row['url'],
                seletor_css=seletor_css,
                usuario_atual=usuario_atual  # Passa o usuário atual para a função
            )
            if resultado:
                sucesso = True
        except KeyError as e:
            print(f"Erro ao processar produto: Coluna '{e}' não encontrada. Verifique o formato dos dados.")
            continue
        except Exception as e:
            print(f"Erro ao monitorar produto {row.get('produto', 'desconhecido')}: {e}")
            continue
            
    print("Monitoramento concluído!")
    return sucesso

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
    Salva a configuração de agendamento em um arquivo para poder 
    restaurar após reinicialização do programa.
    
    Args:
        schedule_info (dict): Dicionário com as informações do agendamento
    """
    import json
    with open('agendamento_config.json', 'w', encoding='utf-8') as f:
        json.dump(schedule_info, f, ensure_ascii=False, indent=4)
    print("Configuração de agendamento salva.")

def carregar_configuracao_agendamento():
    """
    Carrega a configuração de agendamento do arquivo.
    
    Returns:
        dict: Dicionário com as informações do agendamento, ou None se não existir
    """
    import json
    try:
        if os.path.isfile('agendamento_config.json'):
            with open('agendamento_config.json', 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        print("Erro ao carregar configuração de agendamento.")
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
    except:
        print("Erro ao restaurar agendamento.")
        return False