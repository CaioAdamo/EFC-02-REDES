"""
Simulador de Canal Não Confiável
Simula perdas, corrupções e atrasos em pacotes UDP
"""

import random
import threading
import time


# Implementacao da classe UnreliableChannel:
class UnreliableChannel:
    # Construtor - inicializa o objeto
    def __init__(self, loss_rate=0.1, corrupt_rate=0.1, delay_range=(0.01, 0.5)):
        self.loss_rate = loss_rate
        self.corrupt_rate = corrupt_rate
        self.delay_range = delay_range
        self.packets_sent = 0
        self.packets_lost = 0
        self.packets_corrupted = 0
    
    # Metodo para enviar dados
    def send(self, packet, dest_socket, dest_addr):
        self.packets_sent += 1
        if random.random() < self.loss_rate:
            self.packets_lost += 1
            print(f"[SIMULADOR] 📦❌ Pacote {self.packets_sent} PERDIDO")
            return
        
        if random.random() < self.corrupt_rate:
            packet = self._corrupt_packet(packet)
            self.packets_corrupted += 1
            print(f"[SIMULADOR] 📦⚠️  Pacote {self.packets_sent} CORROMPIDO")
        
        delay = random.uniform(*self.delay_range)
        timer = threading.Timer(delay, lambda: dest_socket.sendto(packet, dest_addr))
        timer.daemon = True
        timer.start()
    
    def _corrupt_packet(self, packet):
        if len(packet) == 0:
            return packet
        packet_list = list(packet)
        num_corruptions = random.randint(1, min(5, len(packet)))
        
        for _ in range(num_corruptions):
            idx = random.randint(0, len(packet_list) - 1)
            packet_list[idx] = packet_list[idx] ^ 0xFF
        
        return bytes(packet_list)
    
    def get_statistics(self):
        return {
            'packets_sent': self.packets_sent,
            'packets_lost': self.packets_lost,
            'packets_corrupted': self.packets_corrupted,
            'loss_rate_actual': self.packets_lost / max(1, self.packets_sent),
            'corrupt_rate_actual': self.packets_corrupted / max(1, self.packets_sent)
        }
    def get_stats(self):
        return self.get_statistics()
    def reset_statistics(self):
        self.packets_sent = 0
        self.packets_lost = 0
        self.packets_corrupted = 0
    def print_stats(self, logger=None):
        stats = self.get_statistics()
        msg = (f"Channel stats: {{'packets_sent': {stats['packets_sent']}, "
               f"'packets_lost': {stats['packets_lost']}, "
               f"'packets_corrupted': {stats['packets_corrupted']}, "
               f"'loss_rate_actual': {stats['loss_rate_actual']}, "
               f"'corrupt_rate_actual': {stats['corrupt_rate_actual']}}}")
        if logger:
            logger.info(msg)
        else:
            print(msg)
