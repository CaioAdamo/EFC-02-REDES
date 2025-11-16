"""
RDT 2.0 - Transferência Confiável sobre Canal com Erros de Bits
Implementa protocolo stop-and-wait com ACK/NAK
Referência: Seção 3.4.1, Figura 3.10
"""

import socket
import sys
import time
import threading
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from utils.packet import RDT20Packet, PACKET_TYPE_DATA, PACKET_TYPE_ACK, PACKET_TYPE_NAK
from utils.simulator import UnreliableChannel
from utils.logger import ProtocolLogger


# Implementacao da classe RDT20Sender:
class RDT20Sender:
    # Construtor - inicializa o objeto
    def __init__(self, dest_addr, use_simulator=False, corrupt_rate=0.0):
        self.dest_addr = dest_addr
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('', 0))
        self.logger = ProtocolLogger("SENDER-2.0")
        if use_simulator:
            self.channel = UnreliableChannel(loss_rate=0.0, corrupt_rate=corrupt_rate)
        else:
            self.channel = None
        
        self.packets_sent = 0
        self.retransmissions = 0
        
        self.current_packet = None
        self.waiting_ack = False
    
    # Metodo para enviar dados
    def send_message(self, message):
        if isinstance(message, str):
            message = message.encode()
        packet = RDT20Packet(PACKET_TYPE_DATA, message)
        self.current_packet = packet
        
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
                response, is_valid = RDT20Packet.from_bytes(response_bytes)
                
                if not is_valid:
                    self.logger.corrupt()
                    continue
                
                self.logger.receive(response)
                
                if response.packet_type == PACKET_TYPE_ACK:
                    self.logger.success("✓ ACK received")
                    ack_received = True
                elif response.packet_type == PACKET_TYPE_NAK:
                    self.logger.warning("✗ NAK received, retransmitting...")
                    continue
                    
            except socket.timeout:
                self.logger.timeout()
                continue
        
        self.current_packet = None
        self.waiting_ack = False
    
    def get_statistics(self):
        return {
            'packets_sent': self.packets_sent,
            'retransmissions': self.retransmissions,
            'total_transmissions': self.packets_sent + self.retransmissions
        }
    # Fecha e libera recursos
    def close(self):
        self.socket.close()

# Implementacao da classe RDT20Receiver:
class RDT20Receiver:
    # Construtor - inicializa o objeto
    def __init__(self, port):
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('', port))
        self.logger = ProtocolLogger("RECEIVER-2.0")
        self.received_messages = []
        
        self.packets_received = 0
        self.corrupted_packets = 0
        
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
                packet, is_valid = RDT20Packet.from_bytes(packet_bytes)
                
                if packet and packet.packet_type == PACKET_TYPE_DATA:
                    self.logger.receive(packet)
                    self.packets_received += 1
                    
                    if is_valid:
                        self.received_messages.append(packet.data)
                        self.logger.deliver(packet.data)
                        
                        ack = RDT20Packet(PACKET_TYPE_ACK)
                        self.logger.send(ack)
                        self.socket.sendto(ack.to_bytes(), sender_addr)
                    else:
                        self.logger.corrupt()
                        self.corrupted_packets += 1
                        
                        nak = RDT20Packet(PACKET_TYPE_NAK)
                        self.logger.send(nak)
                        self.socket.sendto(nak.to_bytes(), sender_addr)
                        
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
            'messages_delivered': len(self.received_messages)
        }
    # Fecha e libera recursos
    def close(self):
        self.stop()
        self.socket.close()

def test_rdt20():
    print("\n" + "="*70)
    print("TESTE RDT 2.0 - Canal com Erros de Bits")
    print("="*70 + "\n")
    receiver = RDT20Receiver(9000)
    receiver.start()
    
    time.sleep(0.5)
    
    print("\n--- Teste 1: Canal Perfeito (10 mensagens) ---\n")
    sender = RDT20Sender(('localhost', 9000), use_simulator=False)
    
    test_messages = [f"Mensagem {i}" for i in range(10)]
    start_time = time.time()
    
    for msg in test_messages:
        sender.send_message(msg)
    
    end_time = time.time()
    time.sleep(0.5)
    
    received = receiver.get_messages()
    print(f"\n✓ Teste 1 Completo:")
    print(f"  Enviadas: {len(test_messages)}")
    print(f"  Recebidas: {len(received)}")
    print(f"  Tempo: {end_time - start_time:.3f}s")
    print(f"  Retransmissões: {sender.get_statistics()['retransmissions']}")
    
    assert len(received) == len(test_messages), "Número de mensagens não confere!"
    
    sender.close()
    
    print("\n--- Teste 2: Canal com 30% de Corrupção ---\n")
    receiver.received_messages.clear()
    
    sender = RDT20Sender(('localhost', 9000), use_simulator=True, corrupt_rate=0.3)
    
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
    print(f"  Taxa de retransmissão: {sender_stats['retransmissions']/sender_stats['packets_sent']*100:.1f}%")
    
    assert len(received) == len(test_messages), "Número de mensagens não confere!"
    
    sender.close()
    receiver.close()
    
    print("\n" + "="*70)
    print("✅ TODOS OS TESTES PASSARAM!")
    print("="*70 + "\n")


if __name__ == '__main__':
    test_rdt20()