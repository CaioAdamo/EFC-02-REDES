"""
RDT 2.1 - Transferência Confiável com Números de Sequência
Implementa protocolo alternante (0 e 1) para detectar duplicatas
Referência: Seção 3.4.1, Figuras 3.11 e 3.12
"""

import socket
import sys
import time
import threading
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from utils.packet import RDT21Packet, PACKET_TYPE_DATA, PACKET_TYPE_ACK
from utils.simulator import UnreliableChannel
from utils.logger import ProtocolLogger


# Implementacao da classe RDT21Sender:
class RDT21Sender:
    # Construtor - inicializa o objeto
    def __init__(self, dest_addr, use_simulator=False, corrupt_rate=0.0):
        self.dest_addr = dest_addr
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('', 0))
        self.logger = ProtocolLogger("SENDER-2.1")
        self.seq_num = 0
        
        if use_simulator:
            self.channel = UnreliableChannel(loss_rate=0.0, corrupt_rate=corrupt_rate)
        else:
            self.channel = None
        
        self.packets_sent = 0
        self.retransmissions = 0
    
    # Metodo para enviar dados
    def send_message(self, message):
        if isinstance(message, str):
            message = message.encode()
        packet = RDT21Packet(PACKET_TYPE_DATA, self.seq_num, message)
        
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
            
            self.socket.settimeout(2.0)
            
            try:
                response_bytes, _ = self.socket.recvfrom(1024)
                response, is_valid = RDT21Packet.from_bytes(response_bytes)
                
                if not is_valid:
                    self.logger.corrupt()
                    self.logger.warning("Corrupted ACK, retransmitting...")
                    continue
                
                self.logger.receive(response)
                
                if response.packet_type == PACKET_TYPE_ACK:
                    if response.seq_num == self.seq_num:
                        self.logger.success(f"✓ ACK({self.seq_num}) received")
                        ack_received = True
                    else:
                        self.logger.warning(f"✗ Wrong ACK number (expected {self.seq_num}, got {response.seq_num})")
                        continue
                        
            except socket.timeout:
                self.logger.timeout()
                continue
        
        self.seq_num = 1 - self.seq_num
    
    def get_statistics(self):
        return {
            'packets_sent': self.packets_sent,
            'retransmissions': self.retransmissions,
            'total_transmissions': self.packets_sent + self.retransmissions
        }
    # Fecha e libera recursos
    def close(self):
        self.socket.close()

# Implementacao da classe RDT21Receiver:
class RDT21Receiver:
    # Construtor - inicializa o objeto
    def __init__(self, port):
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('', port))
        self.logger = ProtocolLogger("RECEIVER-2.1")
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
                packet, is_valid = RDT21Packet.from_bytes(packet_bytes)
                
                if packet and packet.packet_type == PACKET_TYPE_DATA:
                    self.logger.receive(packet)
                    self.packets_received += 1
                    
                    if not is_valid:
                        self.logger.corrupt()
                        self.corrupted_packets += 1
                        
                        prev_seq = 1 - self.expected_seq_num
                        ack = RDT21Packet(PACKET_TYPE_ACK, prev_seq)
                        self.logger.send(ack)
                        self.socket.sendto(ack.to_bytes(), sender_addr)
                        
                    elif packet.seq_num == self.expected_seq_num:
                        self.received_messages.append(packet.data)
                        self.logger.deliver(packet.data)
                        
                        ack = RDT21Packet(PACKET_TYPE_ACK, self.expected_seq_num)
                        self.logger.send(ack)
                        self.socket.sendto(ack.to_bytes(), sender_addr)
                        
                        self.expected_seq_num = 1 - self.expected_seq_num
                        
                    else:
                        self.logger.warning(f"Duplicate packet (expected {self.expected_seq_num}, got {packet.seq_num})")
                        self.duplicate_packets += 1
                        
                        ack = RDT21Packet(PACKET_TYPE_ACK, packet.seq_num)
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

def test_rdt21():
    print("\n" + "="*70)
    print("TESTE RDT 2.1 - Com Números de Sequência")
    print("="*70 + "\n")
    receiver = RDT21Receiver(9001)
    receiver.start()
    
    time.sleep(0.5)
    
    print("\n--- Teste 1: Canal Perfeito (10 mensagens) ---\n")
    sender = RDT21Sender(('localhost', 9001), use_simulator=False)
    
    test_messages = [f"Mensagem {i}" for i in range(10)]
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
    
    assert len(received) == len(test_messages), "Número de mensagens não confere!"
    
    sender.close()
    
    print("\n--- Teste 2: 20% Corrupção em DATA e ACK ---\n")
    receiver.received_messages.clear()
    
    sender = RDT21Sender(('localhost', 9001), use_simulator=True, corrupt_rate=0.2)
    
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
    print(f"  Pacotes corrompidos: {receiver_stats['corrupted_packets']}")
    print(f"  Pacotes duplicados: {receiver_stats['duplicate_packets']}")
    
    assert len(received) == len(test_messages), "Número de mensagens não confere!"
    
    print("\n--- Teste 3: Análise de Overhead ---\n")
    
    sample_message = "X" * 100
    packet = RDT21Packet(PACKET_TYPE_DATA, 0, sample_message.encode())
    packet_bytes = packet.to_bytes()
    
    data_size = len(sample_message)
    total_size = len(packet_bytes)
    overhead = total_size - data_size
    overhead_percent = (overhead / data_size) * 100
    
    print(f"  Dados úteis: {data_size} bytes")
    print(f"  Tamanho total do pacote: {total_size} bytes")
    print(f"  Overhead: {overhead} bytes ({overhead_percent:.1f}%)")
    
    sender.close()
    receiver.close()
    
    print("\n" + "="*70)
    print("✅ TODOS OS TESTES PASSARAM!")
    print("="*70 + "\n")


if __name__ == '__main__':
    test_rdt21()