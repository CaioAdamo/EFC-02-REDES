import socket
import threading
import time
from utils.sr_packet import SRPacket
from utils.logger import ProtocolLogger

# Implementacao da classe SRSender
class SRSender:
    # Construtor - inicializa o objeto
    def __init__(self, receiver_address, window_size=5, timeout=1.0, channel=None):
        self.receiver_address = receiver_address
        self.window_size = window_size
        self.timeout = timeout
        self.channel = channel
        self.logger = ProtocolLogger("SR-SENDER")
        
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('localhost', 0))
        
        self.base = 0
        self.next_seq_num = 0
        self.packets = {}
        self.acked = set()
        self.timers = {}
        self.retransmit_count = {}  # Track retransmissions per packet
        self.max_retransmits = 30    # Limit retransmissions
        self.lock = threading.Lock()
        
        self.running = True
        self.recv_thread = threading.Thread(target=self._receive_acks, daemon=True)
        self.recv_thread.start()
    
    # Metodo para enviar dados
    def send_data(self, data_list):
        total_packets = len(data_list)
        seq_num = 0
        
        while seq_num < total_packets or self.base < total_packets:
            with self.lock:
                while seq_num < total_packets and seq_num < self.base + self.window_size:
                    if seq_num not in self.acked:
                        packet = SRPacket(SRPacket.TYPE_DATA, seq_num, data_list[seq_num])
                        self.packets[seq_num] = packet
                        
                        self._send_packet(packet, seq_num)
                        self._start_timer(seq_num)
                        
                    seq_num += 1
                
                if self.base >= total_packets:
                    break
            
            time.sleep(0.01)
        
        while self.base < total_packets:
            time.sleep(0.01)
    
    # Metodo para enviar pacote
    def _send_packet(self, packet, seq_num):
        raw_packet = packet.to_bytes()
        if self.channel:
            self.channel.send(raw_packet, self.socket, self.receiver_address)
        else:
            self.socket.sendto(raw_packet, self.receiver_address)
        window_end = min(self.base + self.window_size - 1, len(self.packets) - 1)
        self.logger.log_send(f"Packet seq={seq_num}, window=[{self.base}, {window_end}]")
    
    # Metodo para iniciar timer
    def _start_timer(self, seq_num):
        if seq_num in self.timers:
            self.timers[seq_num].cancel()
        timer = threading.Timer(self.timeout, self._timeout, args=[seq_num])
        timer.daemon = True
        timer.start()
        self.timers[seq_num] = timer
    
    # Metodo para processar timeout
    def _timeout(self, seq_num):
        with self.lock:
            if seq_num not in self.acked and seq_num in self.packets:
                # Check retransmission limit
                if seq_num not in self.retransmit_count:
                    self.retransmit_count[seq_num] = 0
                
                if self.retransmit_count[seq_num] >= self.max_retransmits:
                    self.logger.log_event(f"⚠️  Max retransmits reached for seq={seq_num}, giving up")
                    # Mark as acked to move window
                    self.acked.add(seq_num)
                    if seq_num == self.base:
                        while self.base in self.acked:
                            self.base += 1
                    return
                
                self.retransmit_count[seq_num] += 1
                self.logger.log_timeout(f"Packet seq={seq_num}")
                packet = self.packets[seq_num]
                self._send_packet(packet, seq_num)
                self.logger.log_retransmit(f"Packet seq={seq_num}")
                self._start_timer(seq_num)
    
    # Metodo para receber ACKs
    def _receive_acks(self):
        self.socket.settimeout(0.1)
        
        while self.running:
            try:
                data, _ = self.socket.recvfrom(1024)
                ack_packet = SRPacket.from_bytes(data)
                
                if ack_packet.packet_type == SRPacket.TYPE_ACK:
                    with self.lock:
                        seq_num = ack_packet.seq_num
                        self.logger.log_receive(f"[ACK] seq={seq_num} len=0")
                        
                        if seq_num not in self.acked:
                            self.acked.add(seq_num)
                            
                            if seq_num in self.timers:
                                self.timers[seq_num].cancel()
                                del self.timers[seq_num]
                            
                            if seq_num == self.base:
                                while self.base in self.acked:
                                    self.base += 1
                                
                                new_window_end = self.base + self.window_size - 1
                                self.logger.log_event(f"✓ ACK({seq_num}) - Window moved to [{self.base}, {new_window_end}]")
                            else:
                                self.logger.log_event(f"✓ ACK({seq_num}) - Buffered (base={self.base})")
            
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    continue
    
    # Metodo para fechar conexao
    def close(self):
        self.running = False
        for timer in self.timers.values():
            timer.cancel()
        self.socket.close()

# Implementacao da classe SRReceiver
class SRReceiver:
    # Construtor - inicializa o objeto
    def __init__(self, port, window_size=5, channel=None):
        self.port = port
        self.window_size = window_size
        self.channel = channel
        self.logger = ProtocolLogger("SR-RECEIVER")
        
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('localhost', port))
        
        self.expected_seq = 0
        self.buffer = {}
        self.received_data = []
        self.running = True
        
        self.logger.log_event(f"Listening on port {port}")
    
    # Metodo para receber dados
    def receive_data(self, expected_count, timeout=30):
        self.socket.settimeout(0.5)
        start_time = time.time()
        last_progress = time.time()
        last_count = 0
        
        while len(self.received_data) < expected_count and self.running:
            # Check global timeout
            if time.time() - start_time > timeout:
                self.logger.log_event(f"⏰ Global timeout reached, received {len(self.received_data)}/{expected_count}")
                break
            
            # Check progress timeout (no new packets for 5 seconds)
            if len(self.received_data) != last_count:
                last_progress = time.time()
                last_count = len(self.received_data)
            elif time.time() - last_progress > 5.0:
                self.logger.log_event(f"⏰ No progress for 5s, stopping at {len(self.received_data)}/{expected_count}")
                break
            
            try:
                data, sender_addr = self.socket.recvfrom(2048)
                
                try:
                    packet = SRPacket.from_bytes(data)
                    
                    if packet.packet_type == SRPacket.TYPE_DATA:
                        seq_num = packet.seq_num
                        self.logger.log_receive(f"[DATA] seq={seq_num} len={len(packet.data)}")
                        
                        if self.expected_seq <= seq_num < self.expected_seq + self.window_size:
                            
                            if seq_num == self.expected_seq:
                                self.received_data.append(packet.data)
                                self.logger.log_event(f"✅ DELIVER to app: {len(packet.data)} bytes")
                                
                                self.expected_seq += 1
                                while self.expected_seq in self.buffer:
                                    buffered_data = self.buffer.pop(self.expected_seq)
                                    self.received_data.append(buffered_data)
                                    self.logger.log_event(f"✅ DELIVER from buffer: seq={self.expected_seq}")
                                    self.expected_seq += 1
                                
                            elif seq_num > self.expected_seq:
                                if seq_num not in self.buffer:
                                    self.buffer[seq_num] = packet.data
                                    self.logger.log_event(f"📦 BUFFER: seq={seq_num} (expected={self.expected_seq})")
                            
                            ack = SRPacket(SRPacket.TYPE_ACK, seq_num)
                            self._send_ack(ack, sender_addr)
                        
                        elif seq_num < self.expected_seq:
                            ack = SRPacket(SRPacket.TYPE_ACK, seq_num)
                            self._send_ack(ack, sender_addr)
                            self.logger.log_send(f"ACK({seq_num}) [duplicate]")
                
                except ValueError:
                    continue
            
            except socket.timeout:
                continue
            except Exception:
                if self.running:
                    continue
        
        return self.received_data
    
    # Metodo para enviar ACK
    def _send_ack(self, ack, addr):
        raw_ack = ack.to_bytes()
        if self.channel:
            self.channel.send(raw_ack, self.socket, addr)
        else:
            self.socket.sendto(raw_ack, addr)
        self.logger.log_send(f"ACK({ack.seq_num})")
    
    # Metodo para fechar conexao
    def close(self):
        self.running = False
        self.socket.close()
