#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Pacote que contém os modelos de dados do Sistema de Monitoramento de Preços.
"""

# Expõe as classes principais para facilitar a importação
from .cliente import Cliente
from .produto import Produto
from .usuario import Usuario
from .grupo import Grupo
from .historico import Historico

# Versão do pacote de modelos
__version__ = '1.0.0'