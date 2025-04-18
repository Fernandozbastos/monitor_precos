#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import re
import random
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urlparse
# Selenium e webdriver-manager para fallback dinâmico
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Lista de user agents para requests
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59'
]

# Criamos a sessão uma vez fora da função
session = requests.Session()
session.headers.update({
    "User-Agent": random.choice(USER_AGENTS)
})

def extrair_dominio(url):
    """
    Extrai o domínio base de uma URL.
    Exemplo: https://www.tuningparts.com.br/produtos/123 -> tuningparts.com.br
    """
    parsed_url = urlparse(url)
    dominio = parsed_url.netloc
    
    # Remove 'www.' se presente
    if dominio.startswith('www.'):
        dominio = dominio[4:]
    
    return dominio

def converter_preco(preco_texto):
    """
    Converte uma string de preço em float.
    Considera separadores de milhar e decimal (ex.: "R$ 1.234,56" ou "1234.56").
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

def extrair_preco_requests(url, seletor_css):
    """
    Tenta extrair o preço usando requests e BeautifulSoup para sites estáticos.
    """
    try:
        response = session.get(url, timeout=30)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            elemento = soup.select_one(seletor_css)
            if elemento:
                return elemento.get_text(strip=True)
    except Exception as e:
        print(f"Erro com requests em {url}: {e}")
    return None

def extrair_preco_selenium(url, seletor_css):
    """
    Usa Selenium para extrair o preço em sites que carregam conteúdo via JavaScript.
    Usa webdriver-manager para gerenciar automaticamente o ChromeDriver.
    """
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
        driver.quit()
        return preco
    except Exception as e:
        print(f"Erro com Selenium em {url}: {e}")
        if 'driver' in locals():
            driver.quit()
        return None

def extrair_preco(url, seletor_css):
    """
    Tenta extrair o preço primeiro com requests.
    Se não conseguir, recorre ao Selenium.
    """
    preco = extrair_preco_requests(url, seletor_css)
    if preco:
        return preco
    else:
        print("Tentando extrair preço com Selenium (fallback)...")
        return extrair_preco_selenium(url, seletor_css)

def registrar_preco(cliente=None, produto=None, concorrente=None, url=None, id_produto=None, seletor_css=None, usuario_atual=None):
    """
    Extrai o preço de um produto e registra no histórico.
    Versão compatível com banco de dados.
    
    Args:
        cliente (str): Nome do cliente
        produto (str): Nome do produto
        concorrente (str): Nome do concorrente
        url (str): URL do produto
        id_produto (int, optional): ID do produto no banco de dados
        seletor_css (str, optional): Seletor CSS do elemento de preço
        usuario_atual (str, optional): Nome do usuário que está registrando o preço
        
    Returns:
        bool: True se o preço foi registrado com sucesso, False caso contrário
    """
    # Se estamos usando o banco de dados e temos o ID do produto
    if id_produto is not None:
        try:
            from database_config import criar_conexao
            
            # Se não tiver seletor, busca no banco de dados
            if seletor_css is None:
                conexao, cursor = criar_conexao()
                
                # Tenta buscar seletor da plataforma do produto
                cursor.execute('''
                SELECT ps.seletor_css 
                FROM produtos p
                JOIN plataformas ps ON p.id_plataforma = ps.id
                WHERE p.id = ?
                ''', (id_produto,))
                
                resultado = cursor.fetchone()
                
                if resultado:
                    seletor_css = resultado['seletor_css']
                else:
                    # Se não tiver plataforma, busca pelo domínio
                    dominio = extrair_dominio(url)
                    
                    cursor.execute('''
                    SELECT seletor_css FROM dominios WHERE nome = ?
                    ''', (dominio,))
                    
                    resultado = cursor.fetchone()
                    
                    if resultado:
                        seletor_css = resultado['seletor_css']
                    else:
                        print(f"Não foi encontrado um seletor CSS para a URL: {url}")
                        conexao.close()
                        return False
                
                conexao.close()
            
            # Extrair o preço usando o seletor
            preco_texto = extrair_preco(url, seletor_css)
            
            if preco_texto:
                valor = converter_preco(preco_texto)
                
                if valor is None:
                    print(f"Falha ao converter o preço extraído: '{preco_texto}'")
                    return False
                
# Registrar o preço no histórico
                conexao, cursor = criar_conexao()
                data_hoje = datetime.now().strftime('%Y-%m-%d')
                
                cursor.execute('''
                INSERT INTO historico_precos (id_produto, preco, data) 
                VALUES (?, ?, ?)
                ''', (id_produto, valor, data_hoje))
                
                conexao.commit()
                conexao.close()
                
                # Buscar informações do produto para exibição
                conexao, cursor = criar_conexao()
                cursor.execute('''
                SELECT c.nome as cliente, p.nome as produto, p.concorrente 
                FROM produtos p
                JOIN clientes c ON p.id_cliente = c.id
                WHERE p.id = ?
                ''', (id_produto,))
                
                info_produto = cursor.fetchone()
                conexao.close()
                
                if info_produto:
                    cliente = info_produto['cliente']
                    produto = info_produto['produto']
                    concorrente = info_produto['concorrente']
                    
                print(f"Preço de {produto} (Cliente: {cliente}) em {concorrente}: R$ {valor:.2f} registrado com sucesso!")
                return True
            else:
                print(f"Não foi possível obter o preço de {produto} (Cliente: {cliente}) em {concorrente}.")
                return False
                
        except Exception as e:
            depurar_logs(f"Erro ao registrar preço: {e}", "ERROR")
            print(f"Erro ao registrar preço: {e}")
            return False
    
    # Modo de arquivo CSV (código original)
    # Nesta versão híbrida, mantemos o código original como fallback
    import pandas as pd
    
    # Determinar o grupo do usuário
    grupo = None
    if usuario_atual:
        try:
            from grupos import obter_grupos_usuario
            grupos = obter_grupos_usuario(usuario_atual)
            
            if usuario_atual == "admin" or "admin" in grupos:
                grupo = "admin"
            else:
                # Filtra para obter apenas o grupo pessoal do usuário
                grupos_pessoais = [g for g in grupos if g != "all" and g != "admin"]
                if grupos_pessoais:
                    grupo = grupos_pessoais[0]  # Usa o primeiro grupo pessoal encontrado
        except ImportError:
            pass
    
    # Se não conseguir determinar o grupo, verifica no arquivo de produtos
    if not grupo and os.path.isfile('produtos_monitorados.csv'):
        try:
            df_produtos = pd.read_csv('produtos_monitorados.csv')
            
            # Verifica se a coluna 'grupo' existe
            if 'grupo' in df_produtos.columns:
                # Busca o grupo para esta combinação específica de cliente, produto e URL
                produto_match = df_produtos[(df_produtos['cliente'] == cliente) & 
                                          (df_produtos['produto'] == produto) &
                                          (df_produtos['url'] == url)]
                
                if not produto_match.empty:
                    grupo = produto_match.iloc[0]['grupo']
        except Exception:
            pass
    
    # Se mesmo assim não conseguir determinar o grupo, usa 'admin' como padrão
    if not grupo:
        grupo = "admin"
    
    # Se não tiver seletor, busca do arquivo de URLs
    if seletor_css is None:
        try:
            if os.path.isfile('urls_monitoradas.csv'):
                df_urls = pd.read_csv('urls_monitoradas.csv')
                url_match = df_urls[df_urls['url'] == url]
                
                if not url_match.empty:
                    seletor_css = url_match.iloc[0]['seletor_css']
                else:
                    # Se não encontrar a URL, tenta buscar pelo domínio
                    dominio = extrair_dominio(url)
                    from database import carregar_dominios_seletores
                    dominios_seletores = carregar_dominios_seletores()
                    
                    if dominio in dominios_seletores:
                        seletor_css = dominios_seletores[dominio]
                    else:
                        print(f"Não foi encontrado um seletor CSS para a URL: {url}")
                        return False
        except Exception as e:
            print(f"Erro ao buscar seletor CSS: {e}")
            return False
    
    # Continua com a extração do preço
    preco_texto = extrair_preco(url, seletor_css)
    
    if preco_texto:
        valor = converter_preco(preco_texto)
        if valor is None:
            print(f"Falha ao converter o preço extraído: '{preco_texto}'")
            return False
        
        data_hoje = datetime.now().strftime('%Y-%m-%d')
        arquivo_csv = 'historico_precos.csv'
        
        # Novo registro com o campo 'grupo'
        novo_registro = pd.DataFrame({
            'data': [data_hoje],
            'cliente': [cliente],
            'produto': [produto],
            'concorrente': [concorrente],
            'preco': [valor],
            'url': [url],
            'grupo': [grupo]  # Adiciona o grupo ao registro
        })
        
        if os.path.isfile(arquivo_csv):
            try:
                df_existente = pd.read_csv(arquivo_csv)
                
                # Verifica se a coluna 'grupo' existe
                if 'grupo' not in df_existente.columns:
                    # Adiciona a coluna grupo se não existir
                    df_existente['grupo'] = 'admin'
                
                df_atualizado = pd.concat([df_existente, novo_registro], ignore_index=True)
                df_atualizado.to_csv(arquivo_csv, index=False)
            except Exception as e:
                print(f"Erro ao atualizar arquivo de histórico: {e}")
                # Cria um novo arquivo se houver erro
                novo_registro.to_csv(arquivo_csv, index=False)
        else:
            novo_registro.to_csv(arquivo_csv, index=False)
            
        print(f"Preço de {produto} (Cliente: {cliente}) em {concorrente}: R$ {valor:.2f} registrado com sucesso!")
        return True
    else:
        print(f"Não foi possível obter o preço de {produto} (Cliente: {cliente}) em {concorrente}.")
        return False