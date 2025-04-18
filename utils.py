import os
import json
import random
from datetime import datetime

# Constantes globais
DOMINIOS_SELETORES_FILE = 'dominios_seletores.json'
PRODUTOS_MONITORADOS_FILE = 'produtos_monitorados.csv'
HISTORICO_PRECOS_FILE = 'historico_precos.csv'
AGENDAMENTO_CONFIG_FILE = 'agendamento_config.json'
USUARIOS_FILE = 'usuarios.json'
PLATAFORMAS_SELETORES_FILE = 'plataformas_seletores.json'  # Nova constante
LOG_FILE = 'monitor_precos.log'

# Lista de user agents para requests
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59'
]

def obter_user_agent_aleatorio():
    """
    Retorna um User-Agent aleatório da lista de USER_AGENTS.
    
    Returns:
        str: Um User-Agent aleatório
    """
    return random.choice(USER_AGENTS)

def gerar_timestamp():
    """
    Gera um timestamp formatado como string.
    
    Returns:
        str: Timestamp no formato 'YYYY-MM-DD HH:MM:SS'
    """
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def gerar_data_hoje():
    """
    Gera a data de hoje formatada como string.
    
    Returns:
        str: Data no formato 'YYYY-MM-DD'
    """
    return datetime.now().strftime('%Y-%m-%d')

def verificar_arquivos_sistema():
    """
    Verifica se os arquivos necessários para o sistema existem.
    Se não existirem, cria os arquivos vazios com a estrutura inicial.
    
    Returns:
        dict: Dicionário com o status de cada arquivo
    """
    status = {}
    
    # Lista de arquivos para verificar
    arquivos_verificar = {
        DOMINIOS_SELETORES_FILE: '{}',   # Arquivo JSON vazio
        AGENDAMENTO_CONFIG_FILE: '{}',   # Arquivo JSON vazio
        'plataformas_seletores.json': '{}'  # Novo arquivo JSON vazio
    }
    
    # Verifica e cria os arquivos JSON se necessário
    for arquivo, conteudo_padrao in arquivos_verificar.items():
        if not os.path.isfile(arquivo):
            try:
                with open(arquivo, 'w', encoding='utf-8') as f:
                    f.write(conteudo_padrao)
                status[arquivo] = f"Criado com sucesso"
                depurar_logs(f"Arquivo {arquivo} criado com sucesso", "INFO")
            except Exception as e:
                status[arquivo] = f"Erro ao criar: {str(e)}"
                depurar_logs(f"Erro ao criar {arquivo}: {str(e)}", "ERROR")
        else:
            status[arquivo] = "Já existe"
    
    # Verifica se a pasta de backups existe
    if not os.path.exists('backups'):
        try:
            os.makedirs('backups')
            status['backups/'] = "Diretório criado"
            depurar_logs("Diretório de backups criado com sucesso", "INFO")
        except Exception as e:
            status['backups/'] = f"Erro ao criar: {str(e)}"
            depurar_logs(f"Erro ao criar diretório de backups: {str(e)}", "ERROR")
    else:
        status['backups/'] = "Já existe"
    
    return status

def criar_backup():
    """
    Cria um backup dos arquivos do sistema.
    
    Returns:
        bool: True se o backup foi criado com sucesso, False caso contrário
    """
    try:
        data_hora = datetime.now().strftime('%Y%m%d_%H%M%S')
        pasta_backup = 'backups'
        
        # Cria a pasta de backup se não existir
        if not os.path.exists(pasta_backup):
            os.makedirs(pasta_backup)
            depurar_logs("Diretório de backups criado", "INFO")
        
        # Lista de arquivos para backup
        arquivos = [
            DOMINIOS_SELETORES_FILE,
            PRODUTOS_MONITORADOS_FILE,
            HISTORICO_PRECOS_FILE,
            AGENDAMENTO_CONFIG_FILE,
            USUARIOS_FILE,
            LOG_FILE
        ]
        
        # Copia cada arquivo para o backup
        for arquivo in arquivos:
            if os.path.isfile(arquivo):
                with open(arquivo, 'r', encoding='utf-8') as f_origem:
                    conteudo = f_origem.read()
                    
                nome_backup = f"{pasta_backup}/{os.path.basename(arquivo)}.{data_hora}.bak"
                with open(nome_backup, 'w', encoding='utf-8') as f_destino:
                    f_destino.write(conteudo)
                    
                print(f"Backup do arquivo '{arquivo}' criado em '{nome_backup}'")
        
        depurar_logs(f"Backup completo criado em {pasta_backup}/{data_hora}", "INFO")
        return True
    except Exception as e:
        erro_msg = f"Erro ao criar backup: {e}"
        print(erro_msg)
        depurar_logs(erro_msg, "ERROR")
        return False

def formatar_preco(valor):
    """
    Formata um valor numérico como preço em reais.
    
    Args:
        valor (float): Valor a ser formatado
        
    Returns:
        str: Valor formatado como preço em reais
    """
    try:
        return f"R$ {valor:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.')
    except Exception:
        return "R$ 0,00"

def validar_url(url):
    """
    Verifica se uma string é uma URL válida.
    
    Args:
        url (str): String a ser validada
        
    Returns:
        bool: True se a string for uma URL válida, False caso contrário
    """
    import re
    padrao = re.compile(
        r'^(?:http|ftp)s?://'  # http:// ou https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domínio
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...ou endereço IP
        r'(?::\d+)?'  # porta opcional
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(padrao, url) is not None

def validar_formato_hora(hora_str):
    """
    Verifica se uma string está no formato de hora HH:MM.
    
    Args:
        hora_str (str): String de hora a ser validada
        
    Returns:
        bool: True se a string está no formato correto, False caso contrário
    """
    import re
    if not re.match(r'^\d{2}:\d{2}$', hora_str):
        return False
        
    try:
        horas, minutos = map(int, hora_str.split(':'))
        return 0 <= horas <= 23 and 0 <= minutos <= 59
    except:
        return False

def depurar_logs(mensagem, nivel='INFO'):
    """
    Registra uma mensagem de log em um arquivo de log.
    
    Args:
        mensagem (str): Mensagem a ser registrada
        nivel (str): Nível do log (INFO, WARNING, ERROR, DEBUG)
    """
    try:
        timestamp = gerar_timestamp()
        linha_log = f"[{timestamp}] [{nivel}] {mensagem}\n"
        
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(linha_log)
            
        # Se for erro ou aviso, exibe no console também
        if nivel in ['ERROR', 'WARNING']:
            print(linha_log.strip())
    except Exception as e:
        print(f"Erro ao registrar log: {e}")

def calcular_diferenca_percentual(preco_anterior, preco_atual):
    """
    Calcula a diferença percentual entre dois preços.
    
    Args:
        preco_anterior (float): Preço anterior
        preco_atual (float): Preço atual
        
    Returns:
        float: Diferença percentual. Positivo indica aumento, negativo indica redução.
    """
    try:
        if preco_anterior == 0:
            return float('inf') if preco_atual > 0 else 0
        
        diferenca = ((preco_atual - preco_anterior) / abs(preco_anterior)) * 100
        return round(diferenca, 2)
    except Exception:
        return 0

def limpar_tela():
    """
    Limpa a tela do terminal, independente do sistema operacional.
    """
    if os.name == 'nt':  # Para Windows
        os.system('cls')
    else:  # Para Linux/Mac
        os.system('clear')

def inicializar_sistema():
    """
    Inicializa o sistema, verificando se deve usar o banco de dados SQLite ou arquivos CSV.
    
    Returns:
        bool: True se a inicialização foi bem-sucedida, False caso contrário
    """
    # Verificar se está no modo de banco de dados ou CSV
    modo_bd = os.path.isfile('usar_bd.flag') or os.path.isfile('monitor_precos.db')
    
    if modo_bd:
        try:
            from database_config import inicializar_banco_dados
            sucesso = inicializar_banco_dados()
            if sucesso:
                print("Sistema inicializado com banco de dados SQLite.")
                
                # Criar flag para indicar que está usando banco de dados
                with open('usar_bd.flag', 'w') as f:
                    f.write('1')
                
                return True
            else:
                print("Falha ao inicializar banco de dados. Tentando modo de arquivos...")
                modo_bd = False
        except Exception as e:
            print(f"Erro ao inicializar banco de dados: {e}")
            print("Usando modo de arquivos como fallback...")
            modo_bd = False
    
    if not modo_bd:
        # Usar o modo de arquivos CSV (código original)
        status = verificar_arquivos_sistema()
        for arquivo, state in status.items():
            print(f"- {arquivo}: {state}")
        return True