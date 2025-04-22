# Sistema de Monitoramento de Preços

Um sistema completo para monitoramento automático de preços de produtos em sites concorrentes, desenvolvido em Python com arquitetura MVC.

## Descrição

O Sistema de Monitoramento de Preços permite acompanhar variações de preços de produtos em sites concorrentes, gerando históricos e análises para tomada de decisões estratégicas. O sistema utiliza técnicas de web scraping para extrair informações de preços automaticamente.

## Funcionalidades Principais

- Extração automática de preços de produtos em sites diversos
- Histórico completo de variações de preços
- Gerenciamento de múltiplos clientes e produtos
- Agendamento de verificações periódicas
- Sistema de permissões com diferentes níveis de acesso
- Interface de linha de comando completa
- Suporte a sites estáticos e dinâmicos (com JavaScript)

## Estrutura do Projeto

```
monitora_precos/
├── models/            # Camada de dados (Model)
│   ├── __init__.py
│   ├── cliente.py
│   ├── produto.py
│   ├── usuario.py
│   ├── grupo.py
│   └── historico.py
├── views/             # Camada de interface (View)
│   ├── __init__.py
│   ├── menu_view.py
│   ├── admin_view.py
│   └── usuario_view.py
├── controllers/       # Camada de lógica de negócio (Controller)
│   ├── __init__.py
│   ├── auth_controller.py
│   ├── cliente_controller.py
│   ├── produto_controller.py
│   └── admin_controller.py
├── utils/             # Utilitários
│   ├── __init__.py
│   ├── logger.py
│   └── validators.py
├── database/          # Acesso ao banco de dados
│   ├── __init__.py
│   └── connector.py
├── scraper/           # Funcionalidade de extração de dados
│   ├── __init__.py
│   └── price_scraper.py
└── main.py            # Ponto de entrada da aplicação
```

## Pré-requisitos

- Python 3.6 ou superior
- Bibliotecas: requests, beautifulsoup4, selenium, webdriver_manager, schedule
- Conexão com a internet para acessar sites de monitoramento

## Instalação

1. Clone o repositório:
   ```
   git clone https://github.com/seu-usuario/monitora_precos.git
   cd monitora_precos
   ```

2. Crie e ative um ambiente virtual (recomendado):
   ```
   python -m venv .venv
   # No Windows:
   .venv\Scripts\activate
   # No Mac/Linux:
   source .venv/bin/activate
   ```

3. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```

4. Inicialize o banco de dados:
   ```
   python main.py
   ```

## Uso Básico

1. Execute o programa:
   ```
   python main.py
   ```

2. Faça login com as credenciais padrão:
   - Usuário: admin
   - Senha: admin

3. No menu principal, você poderá:
   - Acessar o monitoramento de preços
   - Gerenciar clientes
   - Acessar funcionalidades administrativas
   - Configurar ferramentas do sistema

## Fluxo Principal

1. Selecione ou adicione um cliente
2. Adicione produtos para monitoramento (fornecendo URL e outras informações)
3. Execute o monitoramento manual ou configure o agendamento automático
4. Visualize o histórico de preços e relatórios

## Arquitetura MVC

O sistema segue estritamente o padrão MVC:

- **Models**: Representam os dados e regras de negócio
- **Views**: Interfaces com o usuário
- **Controllers**: Lógica que conecta modelos e views

## Autenticação e Permissões

- **Administradores**: Acesso completo a todas as funcionalidades
- **Usuários Regulares**: Acesso limitado a clientes específicos

## Web Scraping

O sistema utiliza duas abordagens para extração de preços:

1. **Requests + BeautifulSoup**: Para sites estáticos
2. **Selenium + ChromeDriver**: Para sites dinâmicos com JavaScript

## Agendamento

Permite configurar monitoramento em dias e horários específicos:

- Dias da semana personalizáveis
- Horário exato
- Fila inteligente de produtos

## Funcionalidades Administrativas

- Backup do sistema
- Relatórios de atividade
- Otimização do banco de dados
- Gestão de usuários e grupos

## Problemas Conhecidos

- Para resolver problemas com dependências, certifique-se de usar a versão correta do Python e das bibliotecas
- Se encontrar problemas com o Selenium, verifique se o ChromeDriver está instalado corretamente
- Em caso de erros com o banco de dados, verifique permissões de escrita na pasta do projeto

## Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para enviar pull requests com melhorias ou correções.

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo LICENSE para detalhes.

## Autor

Fernando Bastos - Bastin Marketing

---

Para sugestões ou dúvidas, entre em contato através de issues no GitHub.