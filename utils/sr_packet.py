"""
Estruturas de Pacotes para Selective Repeat (SR)
Define formatos e funções para criar/parsear pacotes SR
"""

import struct
import hashlib


def calculate_checksum(data):
    return hashlib.md5(data).digest()[:4]

def verify_checksum(data, expected_checksum):
    actual_checksum = calculate_checksum(data)
    return actual_checksum == expected_checksum

# Implementacao da classe SRPacket:
class SRPacket:
    TYPE_DATA = 0
    TYPE_ACK = 1
    
    HEADER_FORMAT = '!BI4s'
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)
    
    # Construtor - inicializa o objeto
    def __init__(self, packet_type, seq_num, data=b''):
        self.packet_type = packet_type
        self.seq_num = seq_num
        self.data = data
        self.checksum = calculate_checksum(
            struct.pack('!BI', packet_type, seq_num) + data
        )
    def to_bytes(self):
        header = struct.pack(self.HEADER_FORMAT, 
                           self.packet_type, 
                           self.seq_num, 
                           self.checksum)
        return header + self.data
    @classmethod
    def from_bytes(cls, packet_bytes):
        if len(packet_bytes) < cls.HEADER_SIZE:
            return None
        header = packet_bytes[:cls.HEADER_SIZE]
        packet_type, seq_num, checksum = struct.unpack(cls.HEADER_FORMAT, header)
        
        data = packet_bytes[cls.HEADER_SIZE:]
        
        expected_data = struct.pack('!BI', packet_type, seq_num) + data
        is_valid = verify_checksum(expected_data, checksum)
        
        if not is_valid:
            return None
        
        packet = cls(packet_type, seq_num, data)
        packet.checksum = checksum
        
        return packet
    
    def __str__(self):
        type_names = {self.TYPE_DATA: 'DATA', self.TYPE_ACK: 'ACK'}
        return f"[{type_names.get(self.packet_type, 'UNKNOWN')}] seq={self.seq_num} len={len(self.data)}"
    
    def __repr__(self):
        return self.__str__()
    
    # Metodo para verificar se e ACK
    @property
    def is_ack(self):
        return self.packet_type == self.TYPE_ACK
    
    # Metodo para obter numero de ACK
    @property
    def ack_num(self):
        return self.seq_num
    
    # Metodo para verificar corrupcao
    def is_corrupt(self):
        expected_data = struct.pack('!BI', self.packet_type, self.seq_num) + self.data
        return not verify_checksum(expected_data, self.checksum)
    
    # Metodo para criar pacote ACK
    @classmethod
    def create_ack(cls, seq_num):
        return cls(cls.TYPE_ACK, seq_num, b'')


