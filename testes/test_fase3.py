"""
Testes para TCP Simplificado (Fase 3)

Inclui:
- Testes Básicos: Three-way handshake, transferência, four-way close
- Testes Obrigatórios: Conforme especificação 3.3.3 do EFC 02
"""

import unittest
import threading
import time
import sys
import os
import socket as real_socket

# Adicionar diretório pai ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fase3.tcp import SimpleTCPSocket
from utils.simulator import UnreliableChannel


class TestTCPBasic(unittest.TestCase):
    """Testes básicos do TCP"""
    
    def tearDown(self):
        """Cleanup após cada teste"""
        # Dar tempo para sockets fecharem completamente e threads terminarem
        # Aumentado para garantir cleanup completo
        time.sleep(2.0)
    
    def test_three_way_handshake(self):
        """Testa o three-way handshake (SYN, SYN-ACK, ACK)"""
        print("\n=== Teste: Three-Way Handshake ===")
        
        # Criar servidor
        server = SimpleTCPSocket(5000, verbose=False)
        server.listen()
        
        # Função do servidor
        def server_thread():
            conn, addr = server.accept()
            if conn:
                self.assertEqual(conn.state, SimpleTCPSocket.ESTABLISHED)
                conn.close()
        
        # Iniciar servidor em thread
        thread = threading.Thread(target=server_thread, daemon=True)
        thread.start()
        
        # Aguardar servidor estar pronto
        time.sleep(0.2)
        
        # Criar cliente e conectar
        client = SimpleTCPSocket(verbose=False)
        success = client.connect('localhost', 5000)
        
        self.assertTrue(success)
        self.assertEqual(client.state, SimpleTCPSocket.ESTABLISHED)
        
        # Aguardar servidor
        thread.join(timeout=2.0)
        
        # Limpar
        client.close()
        server.close()
        
        print("✓ Handshake completado com sucesso")
    
    def test_data_transfer(self):
        """Testa transferência de dados"""
        print("\n=== Teste: Transferência de Dados ===")
        
        test_data = b"Hello, TCP World!" * 100  # ~1.7 KB
        received_data = []
        
        # Criar servidor
        server = SimpleTCPSocket(5001, verbose=False)
        server.listen()
        
        # Função do servidor
        def server_thread():
            conn, addr = server.accept()
            if conn:
                # Receber dados
                data = b''
                while len(data) < len(test_data):
                    chunk = conn.recv(1024, timeout=2.0)
                    if not chunk:
                        break
                    data += chunk
                
                received_data.append(data)
                conn.close()
        
        # Iniciar servidor
        thread = threading.Thread(target=server_thread, daemon=True)
        thread.start()
        
        time.sleep(0.1)
        
        # Cliente conecta e envia
        client = SimpleTCPSocket(verbose=False)
        client.connect('localhost', 5001)
        
        bytes_sent = client.send(test_data)
        self.assertEqual(bytes_sent, len(test_data))
        
        # Aguardar servidor receber
        thread.join(timeout=5.0)
        
        # Verificar dados
        self.assertEqual(len(received_data), 1)
        self.assertEqual(received_data[0], test_data)
        
        # Limpar
        client.close()
        server.close()
        
        print(f"✓ Transferidos {bytes_sent} bytes com sucesso")
    
    def test_bidirectional_transfer(self):
        """Testa transferência bidirecional"""
        print("\n=== Teste: Transferência Bidirecional ===")
        
        client_data = b"Client to Server" * 50
        server_data = b"Server to Client" * 50
        received_by_server = []
        received_by_client = []
        
        # Servidor
        server = SimpleTCPSocket(5002, verbose=False)
        server.listen()
        
        def server_thread():
            conn, addr = server.accept()
            if conn:
                # Receber do cliente
                data = b''
                while len(data) < len(client_data):
                    chunk = conn.recv(1024, timeout=2.0)
                    if not chunk:
                        break
                    data += chunk
                received_by_server.append(data)
                
                # Enviar para o cliente
                conn.send(server_data)
                time.sleep(0.2)  # Aguardar envio
                conn.close()
        
        thread = threading.Thread(target=server_thread, daemon=True)
        thread.start()
        
        time.sleep(0.1)
        
        # Cliente
        client = SimpleTCPSocket(verbose=False)
        client.connect('localhost', 5002)
        
        # Enviar para servidor
        client.send(client_data)
        
        # Receber do servidor
        data = b''
        while len(data) < len(server_data):
            chunk = client.recv(1024, timeout=2.0)
            if not chunk:
                break
            data += chunk
        received_by_client.append(data)
        
        thread.join(timeout=5.0)
        
        # Verificar
        self.assertEqual(received_by_server[0], client_data)
        self.assertEqual(received_by_client[0], server_data)
        
        client.close()
        server.close()
        
        print("✓ Transferência bidirecional bem-sucedida")
    
    def test_four_way_close(self):
        """Testa o four-way handshake no fechamento"""
        print("\n=== Teste: Four-Way Close ===")
        
        # Servidor
        server = SimpleTCPSocket(5003, verbose=False)
        server.listen()
        
        close_states = []
        
        def server_thread():
            conn, addr = server.accept()
            if conn:
                # Aguardar um pouco
                time.sleep(0.2)
                
                # Cliente vai iniciar o fechamento
                # Servidor deve entrar em CLOSE_WAIT
                time.sleep(0.5)
                close_states.append(conn.state)
                
                conn.close()
        
        thread = threading.Thread(target=server_thread, daemon=True)
        thread.start()
        
        time.sleep(0.1)
        
        # Cliente
        client = SimpleTCPSocket(verbose=False)
        client.connect('localhost', 5003)
        
        time.sleep(0.3)
        
        # Cliente inicia fechamento
        client.close()
        
        thread.join(timeout=3.0)
        
        # Verificar que servidor entrou em CLOSE_WAIT
        self.assertIn(close_states[0], [SimpleTCPSocket.CLOSE_WAIT, SimpleTCPSocket.LAST_ACK, SimpleTCPSocket.CLOSED])
        
        server.close()
        
        print("✓ Four-way close executado corretamente")


class TestTCPReliability(unittest.TestCase):
    """Testes de confiabilidade com perdas e corrupção"""
    
    def tearDown(self):
        """Cleanup após cada teste"""
        # Dar tempo para sockets fecharem completamente
        time.sleep(2.0)
    
    def test_handshake_with_losses(self):
        """Testa handshake com perdas de pacotes"""
        print("\n=== Teste: Handshake com Perdas (10%) ===")
        
        # Canal com 10% de perda
        channel = UnreliableChannel(loss_rate=0.1, corrupt_rate=0.0)
        
        # Servidor
        server = SimpleTCPSocket(5004, channel=channel, verbose=False)
        server.listen()
        
        def server_thread():
            conn, addr = server.accept()
            if conn:
                self.assertEqual(conn.state, SimpleTCPSocket.ESTABLISHED)
                conn.close()
        
        thread = threading.Thread(target=server_thread, daemon=True)
        thread.start()
        
        time.sleep(0.1)
        
        # Cliente
        client = SimpleTCPSocket(channel=channel, verbose=False)
        success = client.connect('localhost', 5004)
        
        self.assertTrue(success)
        
        thread.join(timeout=5.0)
        
        client.close()
        server.close()
        
        stats = channel.get_stats()
        print(f"✓ Handshake bem-sucedido com {stats['packets_lost']} pacotes perdidos")
    
    def test_data_transfer_with_losses(self):
        """Testa transferência com perdas"""
        print("\n=== Teste: Transferência com Perdas (15%) ===")
        
        test_data = b"TCP Reliable Transfer!" * 100
        received_data = []
        
        # Canal com 15% de perda
        channel = UnreliableChannel(loss_rate=0.15, corrupt_rate=0.0)
        
        # Servidor
        server = SimpleTCPSocket(5005, channel=channel, verbose=False)
        server.listen()
        
        def server_thread():
            conn, addr = server.accept()
            if conn:
                data = b''
                while len(data) < len(test_data):
                    chunk = conn.recv(1024, timeout=3.0)
                    if not chunk:
                        break
                    data += chunk
                received_data.append(data)
                conn.close()
        
        thread = threading.Thread(target=server_thread, daemon=True)
        thread.start()
        
        time.sleep(0.1)
        
        # Cliente
        client = SimpleTCPSocket(channel=channel, verbose=False)
        client.connect('localhost', 5005)
        client.send(test_data)
        
        thread.join(timeout=10.0)
        
        # Verificar integridade
        self.assertEqual(len(received_data), 1)
        self.assertEqual(received_data[0], test_data)
        
        client.close()
        server.close()
        
        stats = channel.get_stats()
        print(f"✓ {len(test_data)} bytes transferidos com {stats['packets_lost']} perdas")
    
    def test_transfer_with_corruption(self):
        """Testa transferência com corrupção de dados"""
        print("\n=== Teste: Transferência com Corrupção (10%) ===")
        
        test_data = b"Corrupted but Reliable!" * 50
        received_data = []
        
        # Canal com 10% de corrupção
        channel = UnreliableChannel(loss_rate=0.0, corrupt_rate=0.1)
        
        # Servidor
        server = SimpleTCPSocket(5006, channel=channel, verbose=False)
        server.listen()
        
        def server_thread():
            conn, addr = server.accept()
            if conn:
                data = b''
                while len(data) < len(test_data):
                    chunk = conn.recv(1024, timeout=3.0)
                    if not chunk:
                        break
                    data += chunk
                received_data.append(data)
                conn.close()
        
        thread = threading.Thread(target=server_thread, daemon=True)
        thread.start()
        
        time.sleep(0.1)
        
        # Cliente
        client = SimpleTCPSocket(channel=channel, verbose=False)
        client.connect('localhost', 5006)
        client.send(test_data)
        
        thread.join(timeout=10.0)
        
        # Dados devem chegar íntegros (corrupção detectada e descartada)
        self.assertEqual(len(received_data), 1)
        self.assertEqual(received_data[0], test_data)
        
        client.close()
        server.close()
        
        stats = channel.get_stats()
        print(f"✓ Dados íntegros apesar de {stats['packets_corrupted']} corrupções")


class TestTCPFlowControl(unittest.TestCase):
    """Testes de controle de fluxo"""
    
    def tearDown(self):
        """Cleanup após cada teste"""
        # Dar tempo para sockets fecharem completamente
        time.sleep(2.0)
    
    def test_large_data_transfer(self):
        """Testa transferência de dados grandes (flow control)"""
        print("\n=== Teste: Transferência Grande (10 KB) ===")
        
        # 10 KB de dados
        test_data = b"X" * 10240
        received_data = []
        
        # Servidor
        server = SimpleTCPSocket(5007, verbose=False)
        server.listen()
        
        def server_thread():
            conn, addr = server.accept()
            if conn:
                data = b''
                while len(data) < len(test_data):
                    chunk = conn.recv(2048, timeout=3.0)
                    if not chunk:
                        break
                    data += chunk
                received_data.append(data)
                conn.close()
        
        thread = threading.Thread(target=server_thread, daemon=True)
        thread.start()
        
        time.sleep(0.1)
        
        # Cliente
        client = SimpleTCPSocket(verbose=False)
        client.connect('localhost', 5007)
        
        start_time = time.time()
        bytes_sent = client.send(test_data)
        elapsed = time.time() - start_time
        
        thread.join(timeout=10.0)
        
        # Verificar
        self.assertEqual(bytes_sent, len(test_data))
        self.assertEqual(len(received_data), 1)
        self.assertEqual(len(received_data[0]), len(test_data))
        
        throughput = len(test_data) / elapsed / 1024  # KB/s
        
        client.close()
        server.close()
        
        print(f"✓ 10 KB transferidos em {elapsed:.2f}s ({throughput:.1f} KB/s)")


def run_tests():
    """Executa todos os testes"""
    print("\n" + "="*70)
    print("TESTES DO TCP SIMPLIFICADO (FASE 3)")
    print("="*70)
    
    # Criar test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Adicionar testes
    suite.addTests(loader.loadTestsFromTestCase(TestTCPBasic))
    suite.addTests(loader.loadTestsFromTestCase(TestTCPReliability))
    suite.addTests(loader.loadTestsFromTestCase(TestTCPFlowControl))
    
    # Executar
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Resumo
    print("\n" + "="*70)
    print("RESUMO DOS TESTES")
    print("="*70)
    print(f"Testes executados: {result.testsRun}")
    print(f"Sucessos: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Falhas: {len(result.failures)}")
    print(f"Erros: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n✓ TODOS OS TESTES PASSARAM!")
    else:
        print("\n✗ ALGUNS TESTES FALHARAM")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
