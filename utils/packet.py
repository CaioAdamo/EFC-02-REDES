"""
Estruturas de Pacotes para Protocolos RDT
Define formatos e funções para criar/parsear pacotes
"""

import struct
import hashlib


PACKET_TYPE_DATA = 0
PACKET_TYPE_ACK = 1
PACKET_TYPE_NAK = 2


def calculate_checksum(data):
    return hashlib.md5(data).digest()[:4]

def verify_checksum(data, expected_checksum):
    actual_checksum = calculate_checksum(data)
    return actual_checksum == expected_checksum

# Implementacao da classe RDT20Packet:
class RDT20Packet:
    HEADER_FORMAT = '!B4s'
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)
    
    # Construtor - inicializa o objeto
    def __init__(self, packet_type, data=b''):
        self.packet_type = packet_type
        self.data = data
        self.checksum = calculate_checksum(bytes([packet_type]) + data)
    def to_bytes(self):
        header = struct.pack(self.HEADER_FORMAT, self.packet_type, self.checksum)
        return header + self.data
    @classmethod
    def from_bytes(cls, packet_bytes):
        if len(packet_bytes) < cls.HEADER_SIZE:
            return None, False
        header = packet_bytes[:cls.HEADER_SIZE]
        packet_type, checksum = struct.unpack(cls.HEADER_FORMAT, header)
        
        data = packet_bytes[cls.HEADER_SIZE:]
        
        expected_data = bytes([packet_type]) + data
        is_valid = verify_checksum(expected_data, checksum)
        
        packet = cls(packet_type, data)
        packet.checksum = checksum
        
        return packet, is_valid
    
    def __str__(self):
        type_names = {PACKET_TYPE_DATA: 'DATA', PACKET_TYPE_ACK: 'ACK', PACKET_TYPE_NAK: 'NAK'}
        return f"[{type_names.get(self.packet_type, 'UNKNOWN')}] len={len(self.data)}"


# Implementacao da classe RDT21Packet:
class RDT21Packet:
    HEADER_FORMAT = '!BB4s'
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)
    
    # Construtor - inicializa o objeto
    def __init__(self, packet_type, seq_num, data=b''):
        self.packet_type = packet_type
        self.seq_num = seq_num
        self.data = data
        self.checksum = calculate_checksum(bytes([packet_type, seq_num]) + data)
    def to_bytes(self):
        header = struct.pack(self.HEADER_FORMAT, self.packet_type, 
                           self.seq_num, self.checksum)
        return header + self.data
    @classmethod
    def from_bytes(cls, packet_bytes):
        if len(packet_bytes) < cls.HEADER_SIZE:
            return None, False
        header = packet_bytes[:cls.HEADER_SIZE]
        packet_type, seq_num, checksum = struct.unpack(cls.HEADER_FORMAT, header)
        
        data = packet_bytes[cls.HEADER_SIZE:]
        
        expected_data = bytes([packet_type, seq_num]) + data
        is_valid = verify_checksum(expected_data, checksum)
        
        packet = cls(packet_type, seq_num, data)
        packet.checksum = checksum
        
        return packet, is_valid
    
    def __str__(self):
        type_names = {PACKET_TYPE_DATA: 'DATA', PACKET_TYPE_ACK: 'ACK', PACKET_TYPE_NAK: 'NAK'}
        return f"[{type_names.get(self.packet_type, 'UNKNOWN')}] seq={self.seq_num} len={len(self.data)}"


# Implementacao da classe RDT30Packet
class RDT30Packet(RDT21Packet):
    pass