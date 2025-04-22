#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo de logging para o Sistema de Monitoramento de Preços.
"""

import os
from datetime import datetime

class Logger:
    # Arquivo de log
    LOG_FILE = 'monitor_precos.log'
    
    @staticmethod
    def log(mensagem, nivel='INFO'):
        """
        Registra uma mensagem de log em um arquivo de log.
        
        Args:
            mensagem (str): Mensagem a ser registrada
            nivel (str): Nível do log (INFO, WARNING, ERROR, DEBUG)
        """
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            linha_log = f"[{timestamp}] [{nivel}] {mensagem}\n"
            
            with open(Logger.LOG_FILE, 'a', encoding='utf-8') as f:
                f.write(linha_log)
                
            # Se for erro ou aviso, exibe no console também
            if nivel in ['ERROR', 'WARNING']:
                print(linha_log.strip())
                
        except Exception as e:
            print(f"Erro ao registrar log: {e}")