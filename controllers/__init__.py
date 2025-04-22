#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Pacote que contém os controladores do Sistema de Monitoramento de Preços.
"""

# Expõe as classes principais para facilitar a importação
from .auth_controller import AuthController
from .cliente_controller import ClienteController
from .produto_controller import ProdutoController
from .admin_controller import AdminController
from .scheduler_controller import SchedulerController

# Versão do pacote de controladores
__version__ = '1.0.0'