#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Controlador para agendamento de monitoramento de preços.
"""

from datetime import datetime
import schedule
import time
from models.produto import Produto
from utils.logger import Logger
from database.connector import DatabaseConnector

class SchedulerController:
    @staticmethod
    def configurar_agendamento(dias, horario):
        """
        Configura o agendamento automático.
        
        Args:
            dias (list): Lista de dias da semana para execução
            horario (str): Horário para execução (formato HH:MM)
            
        Returns:
            bool: True se a configuração foi bem-sucedida, False caso contrário
        """
        try:
            db = DatabaseConnector()
            conexao, cursor = db.criar_conexao()
            
            # Verificar se já existe uma configuração
            cursor.execute("SELECT id FROM agendamento")
            agendamento_existente = cursor.fetchone()
            
            data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            dias_str = ','.join(dias) if dias else ""
            
            if agendamento_existente:
                # Atualizar configuração existente
                cursor.execute('''
                UPDATE agendamento 
                SET tipo = ?, dia = ?, horario = ?, data_criacao = ? 
                WHERE id = ?
                ''', ("semanal", dias_str, horario, data_atual, agendamento_existente['id']))
            else:
                # Inserir nova configuração
                cursor.execute('''
                INSERT INTO agendamento (tipo, dia, horario, ativo, data_criacao)
                VALUES (?, ?, ?, ?, ?)
                ''', ("semanal", dias_str, horario, 1, data_atual))
            
            conexao.commit()
            conexao.close()
            
            Logger.log(f"Configuração de agendamento: {dias} às {horario}", "INFO")
            return True
            
        except Exception as e:
            Logger.log(f"Erro ao configurar agendamento: {e}", "ERROR")
            return False
    
    @staticmethod
    def obter_configuracao_agendamento():
        """
        Obtém a configuração atual do agendamento.
        
        Returns:
            dict: Configuração do agendamento
        """
        try:
            db = DatabaseConnector()
            conexao, cursor = db.criar_conexao()
            
            cursor.execute("SELECT tipo, dia, horario, ativo, ultima_execucao FROM agendamento")
            configuracao = cursor.fetchone()
            
            conexao.close()
            
            if configuracao:
                dias = configuracao['dia'].split(',') if configuracao['dia'] else []
                
                return {
                    'tipo': configuracao['tipo'],
                    'dias': dias,
                    'horario': configuracao['horario'],
                    'ativo': bool(configuracao['ativo']),
                    'ultima_execucao': configuracao['ultima_execucao']
                }
            
            return None
            
        except Exception as e:
            Logger.log(f"Erro ao obter configuração de agendamento: {e}", "ERROR")
            return None
    
    @staticmethod
    def executar_agendador():
        """
        Inicia o loop de execução do agendador.
        
        Returns:
            bool: True se o agendador foi iniciado com sucesso, False caso contrário
        """
        try:
            # Obter configuração do agendamento
            config = SchedulerController.obter_configuracao_agendamento()
            
            if not config:
                Logger.log("Nenhuma configuração de agendamento encontrada", "WARNING")
                return False
            
            if not config['ativo']:
                Logger.log("Agendamento está desativado", "WARNING")
                return False
            
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
            for dia in config['dias']:
                if dia in dias_semana:
                    dias_semana[dia].at(config['horario']).do(SchedulerController.processar_fila_agendamento)
                    Logger.log(f"Agendamento configurado para {dia} às {config['horario']}", "INFO")
            
            Logger.log("Agendador iniciado", "INFO")
            
            # Loop principal do agendador
            try:
                while True:
                    schedule.run_pending()
                    time.sleep(60)  # Verifica a cada minuto
            except KeyboardInterrupt:
                Logger.log("Agendador encerrado pelo usuário", "INFO")
                return True
                
            return True
            
        except Exception as e:
            Logger.log(f"Erro ao executar agendador: {e}", "ERROR")
            return False
    
    @staticmethod
    def processar_fila_agendamento():
        """
        Processa a fila de agendamento.
        
        Returns:
            bool: True se o processamento foi concluído com sucesso, False caso contrário
        """
        try:
            Logger.log("Iniciando processamento da fila de agendamento", "INFO")
            
            # Atualizar registro de última execução
            db = DatabaseConnector()
            conexao, cursor = db.criar_conexao()
            
            data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute("UPDATE agendamento SET ultima_execucao = ?", (data_atual,))
            
            conexao.commit()
            conexao.close()
            
            # Obter produtos da fila
            produtos_ids = SchedulerController.obter_proximos_produtos_fila(50)  # Processa 50 por vez
            
            if not produtos_ids:
                Logger.log("Fila de agendamento vazia", "INFO")
                return True
            
            Logger.log(f"Processando {len(produtos_ids)} produtos da fila", "INFO")
            
            from controllers.produto_controller import ProdutoController
            resultado = ProdutoController.monitorar_todos_produtos(verificacao_manual=False, limite_produtos=len(produtos_ids))
            
            if resultado:
                Logger.log("Processamento da fila de agendamento concluído com sucesso", "INFO")
            else:
                Logger.log("Processamento da fila concluído, mas com possíveis falhas", "WARNING")
            
            return resultado
            
        except Exception as e:
            Logger.log(f"Erro ao processar fila de agendamento: {e}", "ERROR")
            return False
    
    @staticmethod
    def obter_proximos_produtos_fila(limite=50):
        """
        Obtém os próximos produtos da fila para verificação.
        
        Args:
            limite (int): Número máximo de produtos a retornar
            
        Returns:
            list: Lista de IDs dos produtos na ordem da fila
        """
        try:
            db = DatabaseConnector()
            conexao, cursor = db.criar_conexao()
            
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
            
            return produtos
            
        except Exception as e:
            Logger.log(f"Erro ao obter produtos da fila: {e}", "ERROR")
            return []
    
    @staticmethod
    def reorganizar_fila():
        """
        Reorganiza a fila de agendamento para garantir posições sequenciais.
        
        Returns:
            bool: True se a reorganização foi concluída com sucesso, False caso contrário
        """
        try:
            db = DatabaseConnector()
            conexao, cursor = db.criar_conexao()
            
            # Obter todos os produtos da fila ordenados pela posição atual
            cursor.execute('''
            SELECT id, id_produto, posicao_fila
            FROM fila_agendamento
            ORDER BY posicao_fila
            ''')
            
            produtos_fila = cursor.fetchall()
            
            # Reorganizar as posições
            for i, produto in enumerate(produtos_fila, 1):
                cursor.execute('''
                UPDATE fila_agendamento
                SET posicao_fila = ?
                WHERE id = ?
                ''', (i, produto['id']))
            
            conexao.commit()
            conexao.close()
            
            Logger.log(f"Fila reorganizada: {len(produtos_fila)} produtos", "INFO")
            return True
            
        except Exception as e:
            Logger.log(f"Erro ao reorganizar fila: {e}", "ERROR")
            return False