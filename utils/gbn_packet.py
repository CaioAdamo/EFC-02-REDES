"""
Estruturas de Pacotes para Go-Back-N (GBN)
Define formatos e funções para criar/parsear pacotes GBN
"""

import struct
import hashlib


def calculate_checksum(data):
    return hashlib.md5(data).digest()[:4]

def verify_checksum(data, expected_checksum):
    actual_checksum = calculate_checksum(data)
    return actual_checksum == expected_checksum

# Implementacao da classe GBNPacket:
class GBNPacket:
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
            return None, False
        header = packet_bytes[:cls.HEADER_SIZE]
        packet_type, seq_num, checksum = struct.unpack(cls.HEADER_FORMAT, header)
        
        data = packet_bytes[cls.HEADER_SIZE:]
        
        expected_data = struct.pack('!BI', packet_type, seq_num) + data
        is_valid = verify_checksum(expected_data, checksum)
        
        packet = cls(packet_type, seq_num, data)
        packet.checksum = checksum
        
        return packet, is_valid
    
    def __str__(self):
        type_names = {self.TYPE_DATA: 'DATA', self.TYPE_ACK: 'ACK'}
        return f"[{type_names.get(self.packet_type, 'UNKNOWN')}] seq={self.seq_num} len={len(self.data)}"
    
    def __repr__(self):
        return self.__str__()


