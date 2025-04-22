#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo com funções de validação para o Sistema de Monitoramento de Preços.
"""

import re
from urllib.parse import urlparse

class Validators:
    @staticmethod
    def validar_url(url):
        """
        Verifica se uma string é uma URL válida.
        
        Args:
            url (str): String a ser validada
            
        Returns:
            bool: True se a string for uma URL válida, False caso contrário
        """
        try:
            resultado = urlparse(url)
            return all([resultado.scheme, resultado.netloc])
        except:
            return False
    
    @staticmethod
    def validar_email(email):
        """
        Verifica se uma string é um email válido.
        
        Args:
            email (str): String a ser validada
            
        Returns:
            bool: True se a string for um email válido, False caso contrário
        """
        padrao = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        return bool(re.match(padrao, email))
    
    @staticmethod
    def validar_formato_hora(hora_str):
        """
        Verifica se uma string está no formato de hora HH:MM.
        
        Args:
            hora_str (str): String de hora a ser validada
            
        Returns:
            bool: True se a string está no formato correto, False caso contrário
        """
        if not re.match(r'^\d{2}:\d{2}$', hora_str):
            return False
            
        try:
            horas, minutos = map(int, hora_str.split(':'))
            return 0 <= horas <= 23 and 0 <= minutos <= 59
        except:
            return False
    
    @staticmethod
    def validar_nome_arquivo(nome):
        """
        Verifica se um nome de arquivo é válido.
        
        Args:
            nome (str): Nome de arquivo a ser validado
            
        Returns:
            bool: True se o nome for válido, False caso contrário
        """
        return bool(re.match(r'^[a-zA-Z0-9_\-\.]+$', nome))