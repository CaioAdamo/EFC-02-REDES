"""
Módulo tcp - alias para tcp_socket
Mantém compatibilidade com imports fase3.tcp
"""

from .tcp_socket import SimpleTCPSocket

__all__ = ['SimpleTCPSocket']

