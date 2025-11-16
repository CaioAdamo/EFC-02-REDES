"""
Estrutura de Segmento TCP Simplificado
Define formatos e funções para criar/parsear segmentos TCP
"""

import struct
import hashlib


def calculate_checksum(data):
    return hashlib.md5(data).digest()[:4]

def verify_checksum(data, expected_checksum):
    actual_checksum = calculate_checksum(data)
    return actual_checksum == expected_checksum

# Implementacao da classe TCPSegment:
class TCPSegment:
    FLAG_SYN = 0x02
    FLAG_ACK = 0x10
    FLAG_FIN = 0x01
    
    HEADER_FORMAT = '!HHIIBHH4s'
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)
    
    # Construtor - inicializa o objeto
    def __init__(self, src_port, dst_port, seq_num, ack_num, flags, window, data=b''):
        self.src_port = src_port
        self.dst_port = dst_port
        self.seq_num = seq_num
        self.ack_num = ack_num
        self.flags = flags
        self.window = window
        self.data = data
        header_data = struct.pack('!HHIIBHH', 
                                 src_port, dst_port, seq_num, ack_num, flags, window, 0)
        self.checksum = calculate_checksum(header_data + data)
    
    def to_bytes(self):
        header = struct.pack(self.HEADER_FORMAT,
                           self.src_port,
                           self.dst_port,
                           self.seq_num,
                           self.ack_num,
                           self.flags,
                           self.window,
                           0,
                           self.checksum)
        return header + self.data
    @classmethod
    def from_bytes(cls, segment_bytes):
        if len(segment_bytes) < cls.HEADER_SIZE:
            return None, False
        header = segment_bytes[:cls.HEADER_SIZE]
        src_port, dst_port, seq_num, ack_num, flags, window, _, checksum = \
            struct.unpack(cls.HEADER_FORMAT, header)
        
        data = segment_bytes[cls.HEADER_SIZE:]
        
        header_data = struct.pack('!HHIIBHH', src_port, dst_port, seq_num, ack_num, flags, window, 0)
        is_valid = verify_checksum(header_data + data, checksum)
        
        segment = cls(src_port, dst_port, seq_num, ack_num, flags, window, data)
        segment.checksum = checksum
        
        return segment, is_valid
    
    def has_flag(self, flag):
        return (self.flags & flag) != 0
    def __str__(self):
        flags_str = []
        if self.has_flag(self.FLAG_SYN):
            flags_str.append("SYN")
        if self.has_flag(self.FLAG_ACK):
            flags_str.append("ACK")
        if self.has_flag(self.FLAG_FIN):
            flags_str.append("FIN")
        
        flags_repr = "|".join(flags_str) if flags_str else "NONE"
        return f"TCP[{flags_repr}] seq={self.seq_num} ack={self.ack_num} len={len(self.data)}"
    
    def __repr__(self):
        return self.__str__()

