"""
Go-Back-N (GBN) - Protocolo de Pipelining
Permite múltiplos pacotes não confirmados em trânsito
Referência: Seção 3.4.3, Figuras 3.19 e 3.20
"""

import socket
import sys
import time
import threading
from pathlib import Path
from collections import deque

sys.path.append(str(Path(__file__).parent.parent))

from utils.gbn_packet import GBNPacket
from utils.simulator import UnreliableChannel
from utils.logger import ProtocolLogger


# Implementacao da classe GBNSender:
class GBNSender:
    # Construtor - inicializa o objeto
    def __init__(self, dest_addr, window_size=5, timeout=1.0, 
                 use_simulator=False, loss_rate=0.0, corrupt_rate=0.0, channel=None):
        self.dest_addr = dest_addr
        self.window_size = window_size
        self.timeout = timeout
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('', 0))
        self.logger = ProtocolLogger("GBN-SENDER")
        
        self.base = 0
        self.next_seq_num = 0
        
        self.sent_packets = {}
        
        self.timer = None
        self.timer_lock = threading.Lock()
        
        self.retransmit_count = 0
        self.max_retransmits = 100
        
        if channel:
            self.channel = channel
        elif use_simulator:
            self.channel = UnreliableChannel(
                loss_rate=loss_rate,
                corrupt_rate=corrupt_rate,
                delay_range=(0.05, 0.3)
            )
        else:
            self.channel = None
        
        self.running = False
        self.recv_thread = None
        
        self.packets_sent = 0
        self.retransmissions = 0
        self.timeouts = 0
        self.total_bytes_sent = 0
        self.start_time = None
        
        self.lock = threading.Lock()
    
    # Inicia operacao
    def start(self):
        self.running = True
        self.recv_thread = threading.Thread(target=self._receive_acks, daemon=True)
        self.recv_thread.start()
        self.start_time = time.time()
    def _start_timer(self):
        with self.timer_lock:
            if self.timer:
                self.timer.cancel()
            self.timer = threading.Timer(self.timeout, self._timeout_handler)
            self.timer.daemon = True
            self.timer.start()
    def _stop_timer(self):
        with self.timer_lock:
            if self.timer:
                self.timer.cancel()
                self.timer = None
    def _timeout_handler(self):
        with self.lock:
            self.retransmit_count += 1
            if self.retransmit_count > self.max_retransmits:
                self.logger.log_error(f"Exceeded max retransmits ({self.max_retransmits}), stopping transmission")
                self.running = False
                return
            self.logger.timeout()
            self.timeouts += 1
            
            for seq in range(self.base, self.next_seq_num):
                if seq in self.sent_packets:
                    self.logger.retransmit(f"Packet seq={seq}")
                    self.retransmissions += 1
                    
                    packet_bytes = self.sent_packets[seq]
                    if self.channel:
                        self.channel.send(packet_bytes, self.socket, self.dest_addr)
                    else:
                        self.socket.sendto(packet_bytes, self.dest_addr)
            
            self._start_timer()
    
    def _receive_acks(self):
        self.socket.settimeout(0.1)
        while self.running:
            try:
                ack_bytes, _ = self.socket.recvfrom(1024)
                ack, is_valid = GBNPacket.from_bytes(ack_bytes)
                
                if not is_valid or ack.packet_type != GBNPacket.TYPE_ACK:
                    continue
                
                with self.lock:
                    self.logger.receive(ack)
                    
                    if ack.seq_num >= self.base:
                        self.retransmit_count = 0
                        
                        old_base = self.base
                        self.base = ack.seq_num + 1
                        
                        for seq in range(old_base, self.base):
                            if seq in self.sent_packets:
                                del self.sent_packets[seq]
                        
                        self.logger.success(f"✓ ACK({ack.seq_num}) - Window moved to [{self.base}, {self.base + self.window_size - 1}]")
                        
                        if self.base == self.next_seq_num:
                            self._stop_timer()
                        else:
                            self._start_timer()
                    else:
                        self.logger.warning(f"Old ACK({ack.seq_num}) ignored (base={self.base})")
                        
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    self.logger.error(f"Error receiving ACK: {e}")
    
    # Metodo para enviar dados
    def send_data(self, data):
        if isinstance(data, list):
            for item in data:
                self._send_single(item)
            return
        if isinstance(data, str):
            data = data.encode()
        
        self._send_single(data)
    
    def _send_single(self, data):
        self.total_bytes_sent += len(data)
        while True:
            with self.lock:
                if self.next_seq_num < self.base + self.window_size:
                    break
            time.sleep(0.01)
        
        with self.lock:
            seq_num = self.next_seq_num
            packet = GBNPacket(GBNPacket.TYPE_DATA, seq_num, data)
            packet_bytes = packet.to_bytes()
            
            self.sent_packets[seq_num] = packet_bytes
            
            self.logger.send(f"Packet seq={seq_num}, window=[{self.base}, {self.base + self.window_size - 1}]")
            self.packets_sent += 1
            
            if self.channel:
                self.channel.send(packet_bytes, self.socket, self.dest_addr)
            else:
                self.socket.sendto(packet_bytes, self.dest_addr)
            
            if self.base == self.next_seq_num:
                self._start_timer()
            
            self.next_seq_num += 1
    
    def wait_for_completion(self, timeout=10.0):
        start = time.time()
        while time.time() - start < timeout:
            with self.lock:
                if self.base == self.next_seq_num:
                    self.logger.success("All packets acknowledged!")
                    return True
            time.sleep(0.1)
        self.logger.warning("Timeout waiting for completion")
        return False
    
    def get_statistics(self):
        elapsed = time.time() - self.start_time if self.start_time else 0
        return {
            'packets_sent': self.packets_sent,
            'retransmissions': self.retransmissions,
            'timeouts': self.timeouts,
            'total_transmissions': self.packets_sent + self.retransmissions,
            'total_bytes_sent': self.total_bytes_sent,
            'elapsed_time': elapsed,
            'throughput': self.total_bytes_sent / elapsed if elapsed > 0 else 0
        }
    # Para operacao
    def stop(self):
        self.running = False
        self._stop_timer()
        if self.recv_thread:
            self.recv_thread.join(timeout=2.0)
    # Fecha e libera recursos
    def close(self):
        self.stop()
        if self.channel:
            stats = self.channel.get_statistics()
            self.logger.info(f"Channel stats: {stats}")
        self.socket.close()

# Implementacao da classe GBNReceiver:
class GBNReceiver:
    # Construtor - inicializa o objeto
    def __init__(self, port, window_size=5, channel=None):
        self.port = port
        self.window_size = window_size
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('', port))
        self.logger = ProtocolLogger("GBN-RECEIVER")
        self.channel = channel
        
        self.expected_seq_num = 0
        
        self.received_data = []
        
        self.packets_received = 0
        self.packets_discarded = 0
        self.corrupted_packets = 0
        
        self.running = False
        self.recv_thread = None
        
        self.lock = threading.Lock()
        
        self.start()
    
    # Inicia operacao
    def start(self):
        self.running = True
        self.recv_thread = threading.Thread(target=self._receive_loop, daemon=True)
        self.recv_thread.start()
        self.logger.info(f"Listening on port {self.port}")
    def _receive_loop(self):
        self.socket.settimeout(1.0)
        while self.running:
            try:
                packet_bytes, sender_addr = self.socket.recvfrom(2048)
                
                packet, is_valid = GBNPacket.from_bytes(packet_bytes)
                
                if not packet or packet.packet_type != GBNPacket.TYPE_DATA:
                    continue
                
                with self.lock:
                    self.packets_received += 1
                    
                    if not is_valid:
                        self.logger.corrupt()
                        self.corrupted_packets += 1
                        
                        if self.expected_seq_num > 0:
                            ack = GBNPacket(GBNPacket.TYPE_ACK, self.expected_seq_num - 1)
                            self.logger.send(f"ACK({self.expected_seq_num - 1}) [duplicate]")
                            self.socket.sendto(ack.to_bytes(), sender_addr)
                    
                    else:
                        self.logger.receive(packet)
                        
                        if packet.seq_num == self.expected_seq_num:
                            self.received_data.append(packet.data)
                            self.logger.deliver(packet.data)
                            
                            ack = GBNPacket(GBNPacket.TYPE_ACK, self.expected_seq_num)
                            self.logger.send(f"ACK({self.expected_seq_num})")
                            if self.channel:
                                self.channel.send(ack.to_bytes(), self.socket, sender_addr)
                            else:
                                self.socket.sendto(ack.to_bytes(), sender_addr)
                            
                            self.expected_seq_num += 1
                        
                        else:
                            self.logger.warning(f"Out-of-order packet (seq={packet.seq_num}, expected {self.expected_seq_num}) - DISCARDED")
                            self.packets_discarded += 1
                            
                            if self.expected_seq_num > 0:
                                ack = GBNPacket(GBNPacket.TYPE_ACK, self.expected_seq_num - 1)
                                self.logger.send(f"ACK({self.expected_seq_num - 1}) [duplicate]")
                                if self.channel:
                                    self.channel.send(ack.to_bytes(), self.socket, sender_addr)
                                else:
                                    self.socket.sendto(ack.to_bytes(), sender_addr)
                        
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    self.logger.error(f"Error in receive loop: {e}")
    
    def get_data(self):
        with self.lock:
            return self.received_data.copy()
    # Metodo para receber dados
    def receive_data(self, expected_count, timeout=10):
        start_time = time.time()
        while len(self.received_data) < expected_count:
            if time.time() - start_time > timeout:
                break
            time.sleep(0.1)
        
        return self.get_data()
    
    def get_statistics(self):
        with self.lock:
            return {
                'packets_received': self.packets_received,
                'packets_discarded': self.packets_discarded,
                'corrupted_packets': self.corrupted_packets,
                'data_delivered': len(self.received_data)
            }
    # Para operacao
    def stop(self):
        self.running = False
        if self.recv_thread:
            self.recv_thread.join(timeout=2.0)
    # Fecha e libera recursos
    def close(self):
        self.stop()
        self.socket.close()

def test_gbn():
    print("\n" + "="*70)
    print("TESTE GO-BACK-N (GBN) - Pipelining")
    print("="*70 + "\n")
    print("\n--- Teste 1: Canal Perfeito (Window=5, 20 pacotes) ---\n")
    
    receiver = GBNReceiver(9010)
    receiver.start()
    time.sleep(0.3)
    
    sender = GBNSender(('localhost', 9010), window_size=5, timeout=1.0, use_simulator=False)
    sender.start()
    
    test_data = [f"Pacote {i:02d}".encode() for i in range(20)]
    
    start_time = time.time()
    for data in test_data:
        sender.send_data(data)
    
    sender.wait_for_completion()
    end_time = time.time()
    
    time.sleep(0.5)
    
    received = receiver.get_data()
    sender_stats = sender.get_statistics()
    receiver_stats = receiver.get_statistics()
    
    print(f"\n✓ Teste 1 Completo:")
    print(f"  Enviados: {len(test_data)} pacotes")
    print(f"  Recebidos: {len(received)} pacotes")
    print(f"  Tempo: {end_time - start_time:.3f}s")
    print(f"  Retransmissões: {sender_stats['retransmissions']}")
    print(f"  Throughput: {sender_stats['throughput']:.2f} bytes/s")
    
    assert len(received) == len(test_data), "Número de pacotes não confere!"
    
    sender.close()
    receiver.close()
    
    print("\n--- Teste 2: 10% Perda (Window=5, 15 pacotes) ---\n")
    
    receiver = GBNReceiver(9011)
    receiver.start()
    time.sleep(0.3)
    
    sender = GBNSender(('localhost', 9011), window_size=5, timeout=0.8,
                       use_simulator=True, loss_rate=0.1, corrupt_rate=0.0)
    sender.start()
    
    test_data = [f"Data{i}".encode() for i in range(15)]
    
    start_time = time.time()
    for data in test_data:
        sender.send_data(data)
    
    sender.wait_for_completion(timeout=15.0)
    end_time = time.time()
    
    time.sleep(0.5)
    
    received = receiver.get_data()
    sender_stats = sender.get_statistics()
    receiver_stats = receiver.get_statistics()
    
    print(f"\n✓ Teste 2 Completo:")
    print(f"  Enviados: {len(test_data)} pacotes")
    print(f"  Recebidos: {len(received)} pacotes")
    print(f"  Tempo: {end_time - start_time:.3f}s")
    print(f"  Retransmissões: {sender_stats['retransmissions']}")
    print(f"  Timeouts: {sender_stats['timeouts']}")
    print(f"  Pacotes descartados: {receiver_stats['packets_discarded']}")
    print(f"  Throughput: {sender_stats['throughput']:.2f} bytes/s")
    
    assert len(received) == len(test_data), "Número de pacotes não confere!"
    
    sender.close()
    receiver.close()
    
    print("\n" + "="*70)
    print("✅ TODOS OS TESTES GBN PASSARAM!")
    print("="*70 + "\n")


if __name__ == '__main__':
    test_gbn()