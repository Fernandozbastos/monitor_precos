#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo para extração de preços de produtos em sites.
"""

import re
import time
import random
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from utils.logger import Logger
from database.connector import DatabaseConnector

class PriceScraper:
    # Lista de user agents para requests
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59'
    ]
    
    def __init__(self):
        # Criamos a sessão uma vez
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": random.choice(self.USER_AGENTS)
        })
        self.db = DatabaseConnector()
    
    def extrair_dominio(self, url):
        """
        Extrai o domínio base de uma URL.
        Exemplo: https://www.tuningparts.com.br/produtos/123 -> tuningparts.com.br
        
        Args:
            url (str): URL do produto
            
        Returns:
            str: Domínio extraído
        """
        parsed_url = urlparse(url)
        dominio = parsed_url.netloc
        
        # Remove 'www.' se presente
        if dominio.startswith('www.'):
            dominio = dominio[4:]
        
        return dominio
    
    def converter_preco(self, preco_texto):
        """
        Converte uma string de preço em float.
        Considera separadores de milhar e decimal (ex.: "R$ 1.234,56" ou "1234.56").
        
        Args:
            preco_texto (str): String contendo o preço
            
        Returns:
            float: Valor numérico do preço
        """
        preco_texto = preco_texto.replace("R$", "").strip()
        padrao = re.compile(r'(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)')
        resultado = padrao.search(preco_texto)
        
        if resultado:
            valor_str = resultado.group(1)
            # Verifica se o separador decimal é uma vírgula
            if valor_str.count(',') > 0 and (valor_str.rfind(',') > valor_str.rfind('.')):
                # Remove os pontos e substitui a vírgula por ponto
                valor_str = valor_str.replace('.', '').replace(',', '.')
            else:
                # Remove a vírgula se não for o separador decimal
                valor_str = valor_str.replace(',', '')
            
            try:
                return float(valor_str)
            except ValueError:
                return None
        return None
    
    def extrair_preco_requests(self, url, seletor_css):
        """
        Tenta extrair o preço usando requests e BeautifulSoup para sites estáticos.
        
        Args:
            url (str): URL do produto
            seletor_css (str): Seletor CSS para encontrar o elemento de preço
            
        Returns:
            str: Texto do preço encontrado ou None se não encontrado
        """
        try:
            response = self.session.get(url, timeout=30)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                elemento = soup.select_one(seletor_css)
                if elemento:
                    return elemento.get_text(strip=True)
        except Exception as e:
            Logger.log(f"Erro com requests em {url}: {e}", "WARNING")
        return None
    
    def extrair_preco_selenium(self, url, seletor_css):
        """
        Usa Selenium para extrair o preço em sites que carregam conteúdo via JavaScript.
        
        Args:
            url (str): URL do produto
            seletor_css (str): Seletor CSS para encontrar o elemento de preço
            
        Returns:
            str: Texto do preço encontrado ou None se não encontrado
        """
        driver = None
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")  # Executa sem interface gráfica
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            # Inicializa o WebDriver automaticamente com webdriver-manager
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
            
            driver.get(url)
            time.sleep(5)  # Aguarda para que o JavaScript carregue o conteúdo
            
            elemento = driver.find_element(By.CSS_SELECTOR, seletor_css)
            preco = elemento.text.strip()
            
            return preco
            
        except Exception as e:
            Logger.log(f"Erro com Selenium em {url}: {e}", "WARNING")
            return None
            
        finally:
            if driver:
                driver.quit()
    
    def extrair_preco(self, url, seletor_css):
        """
        Tenta extrair o preço primeiro com requests.
        Se não conseguir, recorre ao Selenium.
        
        Args:
            url (str): URL do produto
            seletor_css (str): Seletor CSS para encontrar o elemento de preço
            
        Returns:
            str: Texto do preço encontrado ou None se não encontrado
        """
        preco = self.extrair_preco_requests(url, seletor_css)
        if preco:
            return preco
        else:
            Logger.log(f"Fallback para Selenium na URL: {url}", "INFO")
            return self.extrair_preco_selenium(url, seletor_css)
    
    def obter_seletor_para_url(self, url):
        """
        Busca o seletor CSS mais adequado para uma URL.
        Primeiro verifica se já há seletor para a plataforma, depois para o domínio.
        
        Args:
            url (str): URL do produto
            
        Returns:
            str: Seletor CSS ou None se não encontrado
        """
        dominio = self.extrair_dominio(url)
        
        try:
            conexao, cursor = self.db.criar_conexao()
            
            # 1. Primeiro tenta encontrar por plataforma (baseado em produtos anteriores com mesma URL)
            cursor.execute('''
            SELECT pl.seletor_css
            FROM produtos p
            JOIN plataformas pl ON p.id_plataforma = pl.id
            WHERE p.url LIKE ?
            LIMIT 1
            ''', (f"%{dominio}%",))
            
            resultado = cursor.fetchone()
            if resultado and resultado['seletor_css']:
                conexao.close()
                return resultado['seletor_css']
            
            # 2. Tenta encontrar pelo domínio exato
            cursor.execute('''
            SELECT seletor_css FROM dominios WHERE nome = ?
            ''', (dominio,))
            
            resultado = cursor.fetchone()
            if resultado and resultado['seletor_css']:
                conexao.close()
                return resultado['seletor_css']
            
            # 3. Tenta encontrar pelo domínio parcial
            cursor.execute('''
            SELECT seletor_css FROM dominios WHERE ? LIKE CONCAT('%', nome, '%')
            LIMIT 1
            ''', (dominio,))
            
            resultado = cursor.fetchone()
            if resultado and resultado['seletor_css']:
                conexao.close()
                return resultado['seletor_css']
            
            conexao.close()
            
            # Se não encontrou nada, retorna None
            Logger.log(f"Não foi encontrado seletor CSS para o domínio: {dominio}", "WARNING")
            return None
            
        except Exception as e:
            Logger.log(f"Erro ao buscar seletor para URL: {e}", "ERROR")
            return None
    
    def salvar_seletor(self, dominio, seletor_css):
        """
        Salva um seletor CSS para um domínio.
        
        Args:
            dominio (str): Domínio
            seletor_css (str): Seletor CSS
            
        Returns:
            bool: True se a operação foi bem-sucedida, False caso contrário
        """
        try:
            conexao, cursor = self.db.criar_conexao()
            
            # Verificar se o domínio já existe
            cursor.execute("SELECT id FROM dominios WHERE nome = ?", (dominio,))
            resultado = cursor.fetchone()
            
            data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            if resultado:
                # Atualizar seletor
                cursor.execute("UPDATE dominios SET seletor_css = ? WHERE id = ?", 
                             (seletor_css, resultado['id']))
            else:
                # Inserir novo domínio
                cursor.execute('''
                INSERT INTO dominios (nome, seletor_css, data_criacao)
                VALUES (?, ?, ?)
                ''', (dominio, seletor_css, data_atual))
            
            conexao.commit()
            conexao.close()
            
            Logger.log(f"Seletor CSS salvo para o domínio: {dominio}", "INFO")
            return True
            
        except Exception as e:
            Logger.log(f"Erro ao salvar seletor: {e}", "ERROR")
            return False
    
    def salvar_plataforma(self, nome_plataforma, seletor_css):
        """
        Salva um seletor CSS para uma plataforma.
        
        Args:
            nome_plataforma (str): Nome da plataforma
            seletor_css (str): Seletor CSS
            
        Returns:
            bool: True se a operação foi bem-sucedida, False caso contrário
        """
        try:
            conexao, cursor = self.db.criar_conexao()
            
            # Verificar se a plataforma já existe
            cursor.execute("SELECT id FROM plataformas WHERE nome = ?", (nome_plataforma,))
            resultado = cursor.fetchone()
            
            data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            if resultado:
                # Atualizar seletor
                cursor.execute("UPDATE plataformas SET seletor_css = ? WHERE id = ?", 
                             (seletor_css, resultado['id']))
                
                id_plataforma = resultado['id']
            else:
                # Inserir nova plataforma
                cursor.execute('''
                INSERT INTO plataformas (nome, seletor_css, data_criacao)
                VALUES (?, ?, ?)
                ''', (nome_plataforma, seletor_css, data_atual))
                
                # Obter ID da plataforma recém-criada
                cursor.execute("SELECT last_insert_rowid() as id")
                id_plataforma = cursor.fetchone()['id']
            
            conexao.commit()
            conexao.close()
            
            Logger.log(f"Seletor CSS salvo para a plataforma: {nome_plataforma}", "INFO")
            return id_plataforma
            
        except Exception as e:
            Logger.log(f"Erro ao salvar plataforma: {e}", "ERROR")
            return None