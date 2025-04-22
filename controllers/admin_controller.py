#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Controlador para operações administrativas.
"""

import os
import shutil
from datetime import datetime, timedelta
from models.usuario import Usuario
from models.grupo import Grupo
from models.cliente import Cliente
from utils.logger import Logger

class AdminController:
    @staticmethod
    def criar_backup():
        """
        Cria um backup completo do sistema.
        
        Returns:
            bool: True se o backup foi criado com sucesso, False caso contrário
        """
        try:
            data_hora = datetime.now().strftime('%Y%m%d_%H%M%S')
            pasta_backup = 'backups'
            
            # Cria a pasta de backup se não existir
            if not os.path.exists(pasta_backup):
                os.makedirs(pasta_backup)
                Logger.log("Diretório de backups criado", "INFO")
            
            # Backup do banco de dados
            db_file = 'monitor_precos.db'
            if os.path.isfile(db_file):
                shutil.copy2(db_file, f"{pasta_backup}/{db_file}.{data_hora}.bak")
                print(f"Backup do banco de dados criado: {pasta_backup}/{db_file}.{data_hora}.bak")
            
            # Backup do arquivo de log
            log_file = 'monitor_precos.log'
            if os.path.isfile(log_file):
                shutil.copy2(log_file, f"{pasta_backup}/{log_file}.{data_hora}.bak")
                print(f"Backup do arquivo de log criado: {pasta_backup}/{log_file}.{data_hora}.bak")
            
            Logger.log(f"Backup completo criado em {pasta_backup}/{data_hora}", "INFO")
            return True
            
        except Exception as e:
            Logger.log(f"Erro ao criar backup: {e}", "ERROR")
            print(f"Erro ao criar backup: {e}")
            return False
    
    @staticmethod
    def relatorio_atividade(periodo='24h'):
        """
        Gera um relatório de atividade do sistema baseado nos logs.
        
        Args:
            periodo (str): Período do relatório ('24h', '7d', '30d', 'all')
            
        Returns:
            dict: Relatório de atividade
        """
        try:
            log_file = 'monitor_precos.log'
            
            if not os.path.isfile(log_file):
                return {'erro': 'Arquivo de log não encontrado.'}
            
            # Determina a data de corte baseada na opção
            data_atual = datetime.now()
            data_corte = None
            
            if periodo == '24h':
                data_corte = data_atual - timedelta(days=1)
                periodo_txt = "Últimas 24 horas"
            elif periodo == '7d':
                data_corte = data_atual - timedelta(days=7)
                periodo_txt = "Últimos 7 dias"
            elif periodo == '30d':
                data_corte = data_atual - timedelta(days=30)
                periodo_txt = "Últimos 30 dias"
            elif periodo == 'all':
                data_corte = datetime(1970, 1, 1)  # Data bem antiga para incluir tudo
                periodo_txt = "Todo o histórico"
            else:
                data_corte = data_atual - timedelta(days=1)
                periodo_txt = "Últimas 24 horas"
            
            # Carrega o arquivo de log
            with open(log_file, 'r', encoding='utf-8') as f:
                linhas_log = f.readlines()
            
            # Filtra as linhas por data
            logs_filtrados = []
            
            for linha in linhas_log:
                try:
                    # Formato esperado: [YYYY-MM-DD HH:MM:SS] [NIVEL] mensagem
                    partes = linha.split('] [')
                    if len(partes) >= 2:
                        data_str = partes[0].strip('[')
                        data_log = datetime.strptime(data_str, '%Y-%m-%d %H:%M:%S')
                        
                        if data_log >= data_corte:
                            logs_filtrados.append(linha)
                except Exception as e:
                    Logger.log(f"Erro ao processar linha de log: {e}", "WARNING")
                    continue
            
            # Análise dos logs
            total_logs = len(logs_filtrados)
            logs_por_nivel = {"INFO": 0, "WARNING": 0, "ERROR": 0, "DEBUG": 0}
            acoes_login = []
            acoes_monitoramento = []
            
            for linha in logs_filtrados:
                # Conta logs por nível
                for nivel in logs_por_nivel.keys():
                    if f"[{nivel}]" in linha:
                        logs_por_nivel[nivel] += 1
                
                # Identifica logins
                if "login" in linha.lower():
                    acoes_login.append(linha)
                
                # Identifica monitoramentos
                if "monitoramento" in linha.lower() or "verificação" in linha.lower():
                    acoes_monitoramento.append(linha)
            
            # Monta o relatório
            relatorio = {
                'periodo': periodo_txt,
                'total_eventos': total_logs,
                'distribuicao_nivel': logs_por_nivel,
                'logins': {
                    'total': len(acoes_login),
                    'recentes': acoes_login[-5:] if acoes_login else []
                },
                'monitoramentos': {
                    'total': len(acoes_monitoramento),
                    'recentes': acoes_monitoramento[-5:] if acoes_monitoramento else []
                }
            }
            
            return relatorio
            
        except Exception as e:
            Logger.log(f"Erro ao gerar relatório: {e}", "ERROR")
            return {'erro': f"Erro ao gerar relatório: {e}"}
    
    @staticmethod
    def validar_estrutura_banco():
        """
        Valida a estrutura do banco de dados.
        
        Returns:
            dict: Resultados da validação
        """
        try:
            from database.connector import DatabaseConnector
            db = DatabaseConnector()
            conexao, cursor = db.criar_conexao()
            
            resultado = {
                'tabelas': {},
                'indices': {},
                'integridade': None
            }
            
            # Verificar tabelas existentes
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tabelas = cursor.fetchall()
            
            for tabela in tabelas:
                nome_tabela = tabela['name']
                
                # Verificar estrutura da tabela
                cursor.execute(f"PRAGMA table_info({nome_tabela})")
                colunas = cursor.fetchall()
                
                resultado['tabelas'][nome_tabela] = {
                    'colunas': len(colunas),
                    'estrutura': [col['name'] for col in colunas]
                }
            
            # Verificar índices
            cursor.execute("SELECT name, tbl_name FROM sqlite_master WHERE type='index'")
            indices = cursor.fetchall()
            
            for indice in indices:
                nome_indice = indice['name']
                tabela_indice = indice['tbl_name']
                
                resultado['indices'][nome_indice] = {
                    'tabela': tabela_indice
                }
            
            # Verificar integridade do banco
            cursor.execute("PRAGMA integrity_check")
            integridade = cursor.fetchone()
            
            resultado['integridade'] = integridade[0] if integridade else None
            
            conexao.close()
            return resultado
            
        except Exception as e:
            Logger.log(f"Erro ao validar estrutura do banco: {e}", "ERROR")
            return {'erro': f"Erro ao validar estrutura do banco: {e}"}
    
    @staticmethod
    def otimizar_banco():
        """
        Otimiza o banco de dados (VACUUM).
        
        Returns:
            bool: True se a operação foi bem-sucedida, False caso contrário
        """
        try:
            from database.connector import DatabaseConnector
            db = DatabaseConnector()
            conexao, cursor = db.criar_conexao()
            
            cursor.execute("VACUUM")
            
            conexao.close()
            
            Logger.log("Banco de dados otimizado (VACUUM)", "INFO")
            return True
            
        except Exception as e:
            Logger.log(f"Erro ao otimizar banco de dados: {e}", "ERROR")
            return False
    
    @staticmethod
    def reconstruir_indices():
        """
        Reconstrói os índices do banco de dados.
        
        Returns:
            bool: True se a operação foi bem-sucedida, False caso contrário
        """
        try:
            from database.connector import DatabaseConnector
            db = DatabaseConnector()
            conexao, cursor = db.criar_conexao()
            
            # Reconstruir índices para as principais tabelas
            for tabela in ["usuarios", "grupos", "clientes", "produtos", "historico_precos"]:
                cursor.execute(f"REINDEX {tabela}")
                
            conexao.close()
            
            Logger.log("Índices reconstruídos com sucesso", "INFO")
            return True
            
        except Exception as e:
            Logger.log(f"Erro ao reconstruir índices: {e}", "ERROR")
            return False