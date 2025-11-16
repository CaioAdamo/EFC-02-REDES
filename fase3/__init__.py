"""
Pacote Fase 3 - TCP Simplificado
Implementa conexão TCP com three-way handshake, flow control e four-way close
"""

from .tcp_socket import SimpleTCPSocket

# Para compatibilidade com imports como fase3.tcp
from . import tcp_socket as tcp

__all__ = ['SimpleTCPSocket']
