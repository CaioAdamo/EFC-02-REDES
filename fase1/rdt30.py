"""
RDT 3.0 - Transferência Confiável com Timer (Canal com Perdas)
Implementa protocolo alternante com timeout para detectar perdas
Referência: Seção 3.4.1, Figuras 3.15 e 3.16
"""

import socket
import sys
import time
import threading
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from utils.packet import RDT30Packet, PACKET_TYPE_DATA, PACKET_TYPE_ACK
from utils.simulator import UnreliableChannel
from utils.logger import ProtocolLogger


# Implementacao da classe RDT30Sender:
class RDT30Sender:
    # Construtor - inicializa o objeto
    def __init__(self, dest_addr, timeout=2.0, use_simulator=False, 
                 loss_rate=0.0, corrupt_rate=0.0):
        self.dest_addr = dest_addr
        self.timeout = timeout
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('', 0))
        self.logger = ProtocolLogger("SENDER-3.0")
        self.seq_num = 0
        
        if use_simulator:
            self.channel = UnreliableChannel(
                loss_rate=loss_rate, 
                corrupt_rate=corrupt_rate,
                delay_range=(0.05, 0.5)
            )
        else:
            self.channel = None
        
        self.packets_sent = 0
        self.retransmissions = 0
        self.timeouts = 0
        self.start_time = None
        self.total_bytes_sent = 0
    
    # Metodo para enviar dados
    def send_message(self, message):
        if isinstance(message, str):
            message = message.encode()
        self.total_bytes_sent += len(message)
        
        packet = RDT30Packet(PACKET_TYPE_DATA, self.seq_num, message)
        
        ack_received = False
        attempt = 0
        
        while not ack_received:
            attempt += 1
            
            if attempt == 1:
                self.logger.send(packet)
                self.packets_sent += 1
            else:
                self.logger.retransmit(packet)
                self.retransmissions += 1
            
            packet_bytes = packet.to_bytes()
            
            if self.channel:
                self.channel.send(packet_bytes, self.socket, self.dest_addr)
            else:
                self.socket.sendto(packet_bytes, self.dest_addr)
            
            self.socket.settimeout(self.timeout)
            
            try:
                response_bytes, _ = self.socket.recvfrom(1024)
                response, is_valid = RDT30Packet.from_bytes(response_bytes)
                
                if not is_valid:
                    self.logger.corrupt()
                    self.logger.warning("Corrupted ACK, waiting for timeout...")
                    continue
                
                self.logger.receive(response)
                
                if response.packet_type == PACKET_TYPE_ACK:
                    if response.seq_num == self.seq_num:
                        self.logger.success(f"✓ ACK({self.seq_num}) received")
                        ack_received = True
                    else:
                        self.logger.warning(f"✗ Old ACK (expected {self.seq_num}, got {response.seq_num})")
                        continue
                        
            except socket.timeout:
                self.logger.timeout()
                self.timeouts += 1
                continue
        
        self.seq_num = 1 - self.seq_num
    
    def get_statistics(self):
        return {
            'packets_sent': self.packets_sent,
            'retransmissions': self.retransmissions,
            'timeouts': self.timeouts,
            'total_transmissions': self.packets_sent + self.retransmissions,
            'total_bytes_sent': self.total_bytes_sent
        }
    # Fecha e libera recursos
    def close(self):
        if self.channel:
            stats = self.channel.get_statistics()
            self.logger.info(f"Channel statistics: {stats}")
        self.socket.close()

# Implementacao da classe RDT30Receiver:
class RDT30Receiver:
    # Construtor - inicializa o objeto
    def __init__(self, port):
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('', port))
        self.logger = ProtocolLogger("RECEIVER-3.0")
        self.expected_seq_num = 0
        
        self.received_messages = []
        
        self.packets_received = 0
        self.corrupted_packets = 0
        self.duplicate_packets = 0
        
        self.running = False
        self.recv_thread = None
    
    # Inicia operacao
    def start(self):
        self.running = True
        self.recv_thread = threading.Thread(target=self._receive_loop, daemon=True)
        self.recv_thread.start()
        self.logger.info(f"Listening on port {self.port}")
    def _receive_loop(self):
        while self.running:
            try:
                self.socket.settimeout(1.0)
                packet_bytes, sender_addr = self.socket.recvfrom(1024)
                packet, is_valid = RDT30Packet.from_bytes(packet_bytes)
                
                if packet and packet.packet_type == PACKET_TYPE_DATA:
                    self.logger.receive(packet)
                    self.packets_received += 1
                    
                    if not is_valid:
                        self.logger.corrupt()
                        self.corrupted_packets += 1
                        
                        prev_seq = 1 - self.expected_seq_num
                        ack = RDT30Packet(PACKET_TYPE_ACK, prev_seq)
                        self.logger.send(ack)
                        self.socket.sendto(ack.to_bytes(), sender_addr)
                        
                    elif packet.seq_num == self.expected_seq_num:
                        self.received_messages.append(packet.data)
                        self.logger.deliver(packet.data)
                        
                        ack = RDT30Packet(PACKET_TYPE_ACK, self.expected_seq_num)
                        self.logger.send(ack)
                        self.socket.sendto(ack.to_bytes(), sender_addr)
                        
                        self.expected_seq_num = 1 - self.expected_seq_num
                        
                    else:
                        self.logger.warning(f"Duplicate packet (expected {self.expected_seq_num}, got {packet.seq_num})")
                        self.duplicate_packets += 1
                        
                        ack = RDT30Packet(PACKET_TYPE_ACK, packet.seq_num)
                        self.logger.send(ack)
                        self.socket.sendto(ack.to_bytes(), sender_addr)
                        
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    self.logger.error(f"Error in receive loop: {e}")
    
    # Para operacao
    def stop(self):
        self.running = False
        if self.recv_thread:
            self.recv_thread.join(timeout=2.0)
    def get_messages(self):
        return self.received_messages
    def get_statistics(self):
        return {
            'packets_received': self.packets_received,
            'corrupted_packets': self.corrupted_packets,
            'duplicate_packets': self.duplicate_packets,
            'messages_delivered': len(self.received_messages)
        }
    # Fecha e libera recursos
    def close(self):
        self.stop()
        self.socket.close()

def test_rdt30():
    print("\n" + "="*70)
    print("TESTE RDT 3.0 - Com Timer e Tratamento de Perdas")
    print("="*70 + "\n")
    receiver = RDT30Receiver(9002)
    receiver.start()
    
    time.sleep(0.5)
    
    test_messages = [f"Mensagem {i}" for i in range(20)]
    
    print("\n--- Teste 1: Canal Perfeito ---\n")
    sender = RDT30Sender(('localhost', 9002), timeout=2.0, use_simulator=False)
    
    start_time = time.time()
    
    for msg in test_messages:
        sender.send_message(msg)
    
    end_time = time.time()
    time.sleep(0.5)
    
    received = receiver.get_messages()
    sender_stats = sender.get_statistics()
    
    print(f"\n✓ Teste 1 Completo:")
    print(f"  Enviadas: {len(test_messages)}")
    print(f"  Recebidas: {len(received)}")
    print(f"  Tempo: {end_time - start_time:.3f}s")
    print(f"  Retransmissões: {sender_stats['retransmissions']}")
    print(f"  Timeouts: {sender_stats['timeouts']}")
    
    assert len(received) == len(test_messages), "Número de mensagens não confere!"
    
    sender.close()
    
    print("\n--- Teste 2: 15% Perda de Pacotes e ACKs ---\n")
    receiver.received_messages.clear()
    
    sender = RDT30Sender(('localhost', 9002), timeout=1.5, use_simulator=True,
                        loss_rate=0.15, corrupt_rate=0.0)
    
    start_time = time.time()
    
    for msg in test_messages:
        sender.send_message(msg)
    
    end_time = time.time()
    time.sleep(0.5)
    
    received = receiver.get_messages()
    sender_stats = sender.get_statistics()
    receiver_stats = receiver.get_statistics()
    
    print(f"\n✓ Teste 2 Completo:")
    print(f"  Enviadas: {len(test_messages)}")
    print(f"  Recebidas: {len(received)}")
    print(f"  Tempo: {end_time - start_time:.3f}s")
    print(f"  Retransmissões: {sender_stats['retransmissions']}")
    print(f"  Timeouts: {sender_stats['timeouts']}")
    print(f"  Taxa de retransmissão: {sender_stats['retransmissions']/sender_stats['packets_sent']*100:.1f}%")
    
    assert len(received) == len(test_messages), "Número de mensagens não confere!"
    
    sender.close()
    
    print("\n--- Teste 3: Perda (15%) + Corrupção (10%) + Atraso Variável ---\n")
    receiver.received_messages.clear()
    
    sender = RDT30Sender(('localhost', 9002), timeout=1.5, use_simulator=True,
                        loss_rate=0.15, corrupt_rate=0.10)
    
    start_time = time.time()
    
    for msg in test_messages:
        sender.send_message(msg)
    
    end_time = time.time()
    time.sleep(0.5)
    
    received = receiver.get_messages()
    sender_stats = sender.get_statistics()
    receiver_stats = receiver.get_statistics()
    
    print(f"\n✓ Teste 3 Completo:")
    print(f"  Enviadas: {len(test_messages)}")
    print(f"  Recebidas: {len(received)}")
    print(f"  Tempo: {end_time - start_time:.3f}s")
    print(f"  Retransmissões: {sender_stats['retransmissions']}")
    print(f"  Timeouts: {sender_stats['timeouts']}")
    print(f"  Pacotes corrompidos: {receiver_stats['corrupted_packets']}")
    
    assert len(received) == len(test_messages), "Número de mensagens não confere!"
    
    print("\n--- Teste 4: Análise de Throughput ---\n")
    
    throughput = sender_stats['total_bytes_sent'] / (end_time - start_time)
    retransmit_rate = sender_stats['retransmissions'] / sender_stats['packets_sent']
    
    print(f"  Bytes úteis enviados: {sender_stats['total_bytes_sent']}")
    print(f"  Tempo total: {end_time - start_time:.3f}s")
    print(f"  Throughput efetivo: {throughput:.2f} bytes/s ({throughput*8/1024:.2f} Kbps)")
    print(f"  Taxa de retransmissão: {retransmit_rate*100:.1f}%")
    
    sender.close()
    receiver.close()
    
    print("\n" + "="*70)
    print("✅ TODOS OS TESTES PASSARAM!")
    print("="*70 + "\n")


if __name__ == '__main__':
    test_rdt30()