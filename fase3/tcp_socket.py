"""
TCP Simplificado - Implementação Completa
Implementa conexão TCP com three-way handshake, flow control e four-way close
"""

import socket
import threading
import time
import random
from collections import deque
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.tcp_segment import TCPSegment
from utils.logger import ProtocolLogger


# Implementacao da classe SimpleTCPSocket:
class SimpleTCPSocket:
    CLOSED = 'CLOSED'
    LISTEN = 'LISTEN'
    SYN_SENT = 'SYN_SENT'
    SYN_RECEIVED = 'SYN_RECEIVED'
    ESTABLISHED = 'ESTABLISHED'
    FIN_WAIT_1 = 'FIN_WAIT_1'
    FIN_WAIT_2 = 'FIN_WAIT_2'
    CLOSE_WAIT = 'CLOSE_WAIT'
    LAST_ACK = 'LAST_ACK'
    TIME_WAIT = 'TIME_WAIT'
    
    BUFFER_SIZE = 4096
    MSS = 1460
    INITIAL_TIMEOUT = 1.0
    MAX_RETRIES = 5
    TIME_WAIT_DURATION = 2.0
    
    # Construtor - inicializa o objeto
    def __init__(self, src_port=0, channel=None, verbose=True):
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.src_port = src_port
        if src_port == 0:
            self.src_port = random.randint(10000, 60000)
        
        try:
            self.udp_socket.bind(('localhost', self.src_port))
        except OSError:
            self.src_port = random.randint(10000, 60000)
            self.udp_socket.bind(('localhost', self.src_port))
        
        self.channel = channel
        
        self.state = self.CLOSED
        self.dst_addr = None
        
        self.seq_num = random.randint(0, 1000)
        self.ack_num = 0
        
        self.send_buffer = deque()
        self.recv_buffer = deque()
        self.out_of_order_buffer = {}
        
        self.rwnd = self.BUFFER_SIZE
        self.cwnd = self.MSS
        
        self.last_byte_sent = self.seq_num
        self.last_byte_acked = self.seq_num
        
        self.next_seq_expected = 0
        
        self.estimated_rtt = self.INITIAL_TIMEOUT
        self.dev_rtt = 0
        self.timeout_interval = self.INITIAL_TIMEOUT
        
        self.lock = threading.Lock()
        self.recv_thread = None
        self.running = False
        
        self.connection_event = threading.Event()
        self.data_available_event = threading.Event()
        self.close_event = threading.Event()
        
        self.accept_queue = deque()
        self.accept_event = threading.Event()
        
        self.established_connections = {}
        
        self.shared_udp_socket = False
        
        self.logger = ProtocolLogger("TCP", verbose=verbose)
        
        self.timer = None
        self.pending_segment = None
        
        self.logger.log_event(f"Socket criado na porta {self.src_port}")
    
    def _send_segment(self, segment, addr=None):
        if addr is None:
            addr = self.dst_addr
        segment_bytes = segment.to_bytes()
        
        if self.channel:
            self.channel.send(segment_bytes, self.udp_socket, addr)
        else:
            self.udp_socket.sendto(segment_bytes, addr)
        
        self.logger.log_send(
            f"{segment} -> {addr[1]}"
        )
    
    def _receive_loop(self):
        try:
            self.udp_socket.settimeout(0.1)
        except:
            return
        while self.running:
            try:
                data, addr = self.udp_socket.recvfrom(65535)
                segment, is_valid = TCPSegment.from_bytes(data)
                
                if not is_valid:
                    self.logger.log_event(f"Segmento corrompido recebido de {addr}")
                    continue
                
                self.logger.log_receive(f"{segment} <- {addr[1]}")
                
                self._process_segment(segment, addr)
                
            except socket.timeout:
                continue
            except OSError as e:
                if self.running:
                    self.running = False
                break
            except Exception as e:
                if self.running:
                    self.logger.log_event(f"Erro no receive loop: {e}")
                    continue
    
    def _process_segment(self, segment, addr):
        if self.state == self.LISTEN and addr in self.established_connections:
            conn_socket = self.established_connections[addr]
            conn_socket._process_segment(segment, addr)
            return
        with self.lock:
            if self.state == self.LISTEN:
                self._handle_listen(segment, addr)
            elif self.state == self.SYN_SENT:
                self._handle_syn_sent(segment, addr)
            elif self.state == self.SYN_RECEIVED:
                self._handle_syn_received(segment, addr)
            elif self.state == self.ESTABLISHED:
                self._handle_established(segment, addr)
            elif self.state == self.FIN_WAIT_1:
                self._handle_fin_wait_1(segment, addr)
            elif self.state == self.FIN_WAIT_2:
                self._handle_fin_wait_2(segment, addr)
            elif self.state == self.CLOSE_WAIT:
                self._handle_close_wait(segment, addr)
            elif self.state == self.LAST_ACK:
                self._handle_last_ack(segment, addr)
    
    # Trata evento especifico
    def _handle_listen(self, segment, addr):
        if segment.has_flag(TCPSegment.FLAG_SYN):
            self.logger.log_event("Recebido SYN, enviando SYN-ACK")
            self.dst_addr = addr
            self.ack_num = segment.seq_num + 1
            self.next_seq_expected = self.ack_num
            
            new_socket = SimpleTCPSocket(0, self.channel, self.logger.verbose)
            
            old_socket = new_socket.udp_socket
            new_socket.udp_socket = self.udp_socket
            new_socket.src_port = self.src_port
            new_socket.shared_udp_socket = True
            old_socket.close()
            
            new_socket.state = self.SYN_RECEIVED
            new_socket.dst_addr = addr
            new_socket.ack_num = segment.seq_num + 1
            new_socket.next_seq_expected = new_socket.ack_num
            new_socket.rwnd = segment.window
            
            syn_ack = TCPSegment(
                new_socket.src_port,
                segment.src_port,
                new_socket.seq_num,
                new_socket.ack_num,
                TCPSegment.FLAG_SYN | TCPSegment.FLAG_ACK,
                self.BUFFER_SIZE
            )
            new_socket._send_segment(syn_ack, addr)
            new_socket.seq_num += 1
            
            self.accept_queue.append((new_socket, segment, addr))
            self.accept_event.set()
    
    # Trata evento especifico
    def _handle_syn_sent(self, segment, addr):
        if segment.has_flag(TCPSegment.FLAG_SYN) and segment.has_flag(TCPSegment.FLAG_ACK):
            if segment.ack_num == self.seq_num:
                self.logger.log_event("Recebido SYN-ACK, enviando ACK final")
                if self.timer:
                    self.timer.cancel()
                    self.timer = None
                
                self.ack_num = segment.seq_num + 1
                self.next_seq_expected = self.ack_num
                self.rwnd = segment.window
                
                ack = TCPSegment(
                    self.src_port,
                    segment.src_port,
                    self.seq_num,
                    self.ack_num,
                    TCPSegment.FLAG_ACK,
                    self.BUFFER_SIZE
                )
                self._send_segment(ack, addr)
                
                self.state = self.ESTABLISHED
                self.logger.log_event(f"Conexão ESTABELECIDA com {addr}")
                self.connection_event.set()
    
    # Trata evento especifico
    def _handle_syn_received(self, segment, addr):
        if segment.has_flag(TCPSegment.FLAG_ACK):
            if segment.ack_num == self.seq_num:
                self.logger.log_event("Recebido ACK final do handshake")
                self.state = self.ESTABLISHED
                self.rwnd = segment.window
                self.logger.log_event(f"Conexão ESTABELECIDA com {addr}")
                self.connection_event.set()
    
    # Trata evento especifico
    def _handle_established(self, segment, addr):
        self.rwnd = segment.window
        if segment.has_flag(TCPSegment.FLAG_ACK):
            if segment.ack_num > self.last_byte_acked:
                bytes_acked = segment.ack_num - self.last_byte_acked
                self.last_byte_acked = segment.ack_num
                self.logger.log_event(f"ACK recebido: {bytes_acked} bytes confirmados")
                
                if self.timer:
                    self.timer.cancel()
                    self.timer = None
                    self.pending_segment = None
                
                sample_rtt = self.timeout_interval * 0.8
                self._update_rtt(sample_rtt)
        
        if segment.has_flag(TCPSegment.FLAG_FIN):
            self.logger.log_event("Recebido FIN, iniciando fechamento passivo")
            
            if len(segment.data) > 0:
                if segment.seq_num == self.next_seq_expected:
                    self.recv_buffer.append(segment.data)
                    self.next_seq_expected += len(segment.data)
                    self.data_available_event.set()
            
            self.ack_num = segment.seq_num + len(segment.data) + 1
            
            ack = TCPSegment(
                self.src_port,
                segment.src_port,
                self.seq_num,
                self.ack_num,
                TCPSegment.FLAG_ACK,
                self.BUFFER_SIZE
            )
            self._send_segment(ack, addr)
            
            self.state = self.CLOSE_WAIT
            self.close_event.set()
            return
        
        if len(segment.data) > 0:
            if segment.seq_num == self.next_seq_expected:
                self.recv_buffer.append(segment.data)
                self.next_seq_expected += len(segment.data)
                self.ack_num = self.next_seq_expected
                self.logger.log_event(f"Dados recebidos: {len(segment.data)} bytes")
                
                while self.next_seq_expected in self.out_of_order_buffer:
                    data = self.out_of_order_buffer.pop(self.next_seq_expected)
                    self.recv_buffer.append(data)
                    self.next_seq_expected += len(data)
                    self.ack_num = self.next_seq_expected
                
                self.data_available_event.set()
            
            ack = TCPSegment(
                self.src_port,
                segment.src_port,
                self.seq_num,
                self.ack_num,
                TCPSegment.FLAG_ACK,
                self.BUFFER_SIZE
            )
            self._send_segment(ack, addr)
            
            if segment.seq_num > self.next_seq_expected:
                self.logger.log_event(f"Dados fora de ordem: seq={segment.seq_num}, esperado={self.next_seq_expected}")
                self.out_of_order_buffer[segment.seq_num] = segment.data
    
    # Trata evento especifico
    def _handle_fin_wait_1(self, segment, addr):
        if segment.has_flag(TCPSegment.FLAG_ACK):
            self.logger.log_event("ACK do FIN recebido")
            self.state = self.FIN_WAIT_2
            if self.timer:
                self.timer.cancel()
                self.timer = None
        
        if segment.has_flag(TCPSegment.FLAG_FIN):
            self.logger.log_event("FIN simultâneo recebido")
            self.ack_num = segment.seq_num + 1
            
            ack = TCPSegment(
                self.src_port,
                segment.src_port,
                self.seq_num,
                self.ack_num,
                TCPSegment.FLAG_ACK,
                self.BUFFER_SIZE
            )
            self._send_segment(ack, addr)
            
            if self.state == self.FIN_WAIT_2:
                self._enter_time_wait()
    
    # Trata evento especifico
    def _handle_fin_wait_2(self, segment, addr):
        if segment.has_flag(TCPSegment.FLAG_FIN):
            self.logger.log_event("FIN do peer recebido")
            self.ack_num = segment.seq_num + 1
            ack = TCPSegment(
                self.src_port,
                segment.src_port,
                self.seq_num,
                self.ack_num,
                TCPSegment.FLAG_ACK,
                self.BUFFER_SIZE
            )
            self._send_segment(ack, addr)
            
            self._enter_time_wait()
    
    # Trata evento especifico
    def _handle_close_wait(self, segment, addr):
        if segment.has_flag(TCPSegment.FLAG_ACK):
            if segment.ack_num > self.last_byte_acked:
                self.last_byte_acked = segment.ack_num
    # Trata evento especifico
    def _handle_last_ack(self, segment, addr):
        if segment.has_flag(TCPSegment.FLAG_ACK):
            self.logger.log_event("ACK final recebido, fechando conexão")
            if self.timer:
                self.timer.cancel()
                self.timer = None
            
            self.state = self.CLOSED
            self.close_event.set()
    
    def _enter_time_wait(self):
        self.state = self.TIME_WAIT
        self.logger.log_event(f"Entrando em TIME_WAIT por {self.TIME_WAIT_DURATION}s")
        def exit_time_wait():
            with self.lock:
                self.logger.log_event("Saindo de TIME_WAIT, fechando conexão")
                self.state = self.CLOSED
                self.close_event.set()
        
        timer = threading.Timer(self.TIME_WAIT_DURATION, exit_time_wait)
        timer.daemon = True
        timer.start()
    
    def _update_rtt(self, sample_rtt):
        if self.estimated_rtt == self.INITIAL_TIMEOUT:
            self.estimated_rtt = sample_rtt
            self.dev_rtt = sample_rtt / 2
        else:
            alpha = 0.125
            beta = 0.25
            self.estimated_rtt = (1 - alpha) * self.estimated_rtt + alpha * sample_rtt
            self.dev_rtt = (1 - beta) * self.dev_rtt + beta * abs(sample_rtt - self.estimated_rtt)
        self.timeout_interval = self.estimated_rtt + 4 * self.dev_rtt
        self.timeout_interval = max(0.2, min(self.timeout_interval, 5.0))
    
    def connect(self, host, port):
        if self.state != self.CLOSED:
            raise RuntimeError(f"Socket já está em uso (estado: {self.state})")
        self.dst_addr = (host, port)
        self.logger.log_event(f"Iniciando conexão com {host}:{port}")
        
        self.connection_event.clear()
        self.data_available_event.clear()
        self.close_event.clear()
        
        self.running = True
        self.recv_thread = threading.Thread(target=self._receive_loop, daemon=True)
        self.recv_thread.start()
        
        time.sleep(0.05)
        
        syn = TCPSegment(
            self.src_port,
            port,
            self.seq_num,
            0,
            TCPSegment.FLAG_SYN,
            self.BUFFER_SIZE
        )
        
        self.state = self.SYN_SENT
        self._send_segment(syn)
        self.seq_num += 1
        
        self.pending_segment = syn
        self._set_retransmission_timer()
        
        success = self.connection_event.wait(timeout=10.0)
        
        if not success or self.state != self.ESTABLISHED:
            self.logger.log_event("Timeout na conexão")
            self.running = False
            if self.timer:
                self.timer.cancel()
            return False
        
        return True
    
    def listen(self, backlog=5):
        if self.state != self.CLOSED:
            raise RuntimeError(f"Socket já está em uso (estado: {self.state})")
        self.state = self.LISTEN
        self.logger.log_event(f"Socket em LISTEN na porta {self.src_port}")
        
        self.accept_event.clear()
        self.accept_queue.clear()
        self.established_connections.clear()
        
        self.running = True
        self.recv_thread = threading.Thread(target=self._receive_loop, daemon=True)
        self.recv_thread.start()
        
        time.sleep(0.05)
    
    def accept(self):
        if self.state != self.LISTEN:
            raise RuntimeError(f"Socket não está em LISTEN (estado: {self.state})")
        while self.running and len(self.accept_queue) == 0:
            self.accept_event.wait(timeout=0.1)
            self.accept_event.clear()
        
        if not self.running:
            return None, None
        
        with self.lock:
            if len(self.accept_queue) == 0:
                return None, None
            
            new_socket, syn_segment, addr = self.accept_queue.popleft()
        
        new_socket.running = True
        new_socket.recv_thread = threading.Thread(target=new_socket._receive_loop, daemon=True)
        new_socket.recv_thread.start()
        
        success = new_socket.connection_event.wait(timeout=5.0)
        
        if not success or new_socket.state != self.ESTABLISHED:
            new_socket.logger.log_event("Timeout no handshake")
            new_socket.running = False
            return None, None
        
        self.established_connections[addr] = new_socket
        
        return new_socket, addr
    
    # Metodo para enviar dados
    def send(self, data):
        if isinstance(data, str):
            data = data.encode('utf-8')
        if self.state != self.ESTABLISHED:
            raise RuntimeError(f"Cannot send: connection not established (state={self.state})")
        
        total_sent = len(data)
        offset = 0
        
        while offset < len(data):
            chunk_size = min(self.MSS, len(data) - offset)
            chunk = data[offset:offset + chunk_size]
            
            segment = TCPSegment(
                self.src_port,
                self.dst_addr[1],
                self.seq_num,
                self.ack_num,
                TCPSegment.FLAG_ACK,
                self.BUFFER_SIZE,
                chunk
            )
            
            self._send_segment(segment, self.dst_addr)
            
            self.seq_num += len(chunk)
            offset += chunk_size
            
            time.sleep(0.01)
        
        return total_sent
    
    # Metodo para receber dados
    def recv(self, buffer_size=4096, timeout=None):
        if self.state not in [self.ESTABLISHED, self.CLOSE_WAIT]:
            return b''
        start_time = time.time()
        
        while True:
            with self.lock:
                if len(self.recv_buffer) > 0:
                    result = b''
                    bytes_read = 0
                    
                    while len(self.recv_buffer) > 0 and bytes_read < buffer_size:
                        chunk = self.recv_buffer.popleft()
                        if bytes_read + len(chunk) <= buffer_size:
                            result += chunk
                            bytes_read += len(chunk)
                        else:
                            remaining = buffer_size - bytes_read
                            result += chunk[:remaining]
                            self.recv_buffer.appendleft(chunk[remaining:])
                            break
                    
                    if len(self.recv_buffer) == 0:
                        self.data_available_event.clear()
                    
                    return result
            
            if self.state == self.CLOSE_WAIT:
                return b''
            
            if timeout is not None:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    return b''
                remaining_timeout = timeout - elapsed
            else:
                remaining_timeout = 0.1
            
            self.data_available_event.wait(timeout=remaining_timeout)
    
    # Fecha e libera recursos
    def close(self):
        if self.state == self.CLOSED:
            return
        self.logger.log_event("Iniciando fechamento da conexão")
        
        if self.state == self.LISTEN:
            self.state = self.CLOSED
            self.running = False
            
            for conn_socket in list(self.established_connections.values()):
                try:
                    conn_socket.close()
                except:
                    pass
            self.established_connections.clear()
            
            if self.recv_thread and self.recv_thread.is_alive():
                self.recv_thread.join(timeout=2.0)
            
            try:
                self.udp_socket.close()
            except:
                pass
            return
        
        if self.state == self.ESTABLISHED:
            with self.lock:
                fin = TCPSegment(
                    self.src_port,
                    self.dst_addr[1],
                    self.seq_num,
                    self.ack_num,
                    TCPSegment.FLAG_FIN | TCPSegment.FLAG_ACK,
                    self.BUFFER_SIZE
                )
                
                self._send_segment(fin)
                self.seq_num += 1
                
                self.state = self.FIN_WAIT_1
                
                self.pending_segment = fin
                self._set_retransmission_timer()
        
        elif self.state == self.CLOSE_WAIT:
            with self.lock:
                fin = TCPSegment(
                    self.src_port,
                    self.dst_addr[1],
                    self.seq_num,
                    self.ack_num,
                    TCPSegment.FLAG_FIN | TCPSegment.FLAG_ACK,
                    self.BUFFER_SIZE
                )
                
                self._send_segment(fin)
                self.seq_num += 1
                
                self.state = self.LAST_ACK
                
                self.pending_segment = fin
                self._set_retransmission_timer()
        
        if not self.close_event.wait(timeout=10.0):
            self.logger.log_event("Warning: close timeout, forçando fechamento")
        
        self.running = False
        
        if self.timer:
            self.timer.cancel()
            self.timer = None
        
        if self.recv_thread and self.recv_thread.is_alive():
            for attempt in range(5):
                self.recv_thread.join(timeout=0.3)
                if not self.recv_thread.is_alive():
                    break
                self.running = False
                time.sleep(0.1)
        
        if not self.shared_udp_socket:
            try:
                self.udp_socket.close()
            except:
                pass
        
        self.connection_event.clear()
        self.data_available_event.clear()
        self.close_event.clear()
        
        self.logger.log_event("Conexão fechada")
    
    def _set_retransmission_timer(self):
        if self.timer:
            self.timer.cancel()
        def retransmit():
            with self.lock:
                if self.pending_segment and self.state not in [self.CLOSED]:
                    self.logger.log_event("Timeout - retransmitindo segmento")
                    self._send_segment(self.pending_segment)
                    self._set_retransmission_timer()
        
        self.timer = threading.Timer(self.timeout_interval, retransmit)
        self.timer.daemon = True
        self.timer.start()
    
    def _retransmit_data(self):
        with self.lock:
            if self.pending_segment and self.state == self.ESTABLISHED:
                self.logger.log_event("Timeout - retransmitindo dados")
                self._send_segment(self.pending_segment, self.dst_addr)
                if self.timer:
                    self.timer.cancel()
                self.timer = threading.Timer(self.timeout_interval, self._retransmit_data)
                self.timer.daemon = True
                self.timer.start()
    def __del__(self):
        try:
            if self.state != self.CLOSED:
                self.close()
        except:
            pass
