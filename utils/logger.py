"""
Sistema de Logging para Protocolos RDT
Fornece logging colorido e formatado
"""

import time
import sys
import io
from datetime import datetime

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except (AttributeError, ValueError):
        pass


# Implementacao da classe Colors:
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# Implementacao da classe ProtocolLogger:
class ProtocolLogger:
    # Construtor - inicializa o objeto
    def __init__(self, name, verbose=True):
        self.name = name
        self.verbose = verbose
        self.start_time = time.time()
    def _get_timestamp(self):
        elapsed = time.time() - self.start_time
        return f"{elapsed:7.3f}s"
    def _log(self, message, color=''):
        if self.verbose:
            timestamp = self._get_timestamp()
            try:
                print(f"{color}[{timestamp}] [{self.name}] {message}{Colors.ENDC}")
            except UnicodeEncodeError:
                safe_message = message.encode('ascii', 'ignore').decode('ascii')
                print(f"{color}[{timestamp}] [{self.name}] {safe_message}{Colors.ENDC}")
    def info(self, message):
        self._log(message, Colors.OKBLUE)
    def success(self, message):
        self._log(message, Colors.OKGREEN)
    def warning(self, message):
        self._log(message, Colors.WARNING)
    def error(self, message):
        self._log(message, Colors.FAIL)
    # Metodo para enviar dados
    def send(self, packet):
        self._log(f"📤 SEND: {packet}", Colors.OKCYAN)
    # Metodo para receber dados
    def receive(self, packet):
        self._log(f"📥 RECV: {packet}", Colors.OKGREEN)
    def retransmit(self, packet):
        self._log(f"🔄 RETRANSMIT: {packet}", Colors.WARNING)
    def timeout(self):
        self._log(f"⏰ TIMEOUT!", Colors.FAIL)
    def corrupt(self):
        self._log(f"⚠️  CORRUPT packet received", Colors.WARNING)
    def deliver(self, data):
        self._log(f"✅ DELIVER to app: {len(data)} bytes", Colors.OKGREEN)
    def log_event(self, message):
        self.info(message)
    def log_send(self, message):
        self._log(f"📤 SEND: {message}", Colors.OKCYAN)
    def log_receive(self, message):
        self._log(f"📥 RECV: {message}", Colors.OKGREEN)
    def log_timeout(self, message=""):
        self._log(f"⏰ TIMEOUT! {message}", Colors.FAIL)
    def log_retransmit(self, message):
        self._log(f"🔄 RETRANSMIT: {message}", Colors.WARNING)
    def log_error(self, message):
        self.error(message)