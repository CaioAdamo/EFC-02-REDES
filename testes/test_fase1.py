import sys
import time
import unittest
from pathlib import Path


sys.path.append(str(Path(__file__).parent.parent))

from fase1.rdt20 import RDT20Sender, RDT20Receiver
from fase1.rdt21 import RDT21Sender, RDT21Receiver
from fase1.rdt30 import RDT30Sender, RDT30Receiver


class TestRDT20(unittest.TestCase):
    """Testes para RDT 2.0"""
    
    def setUp(self):
        """Configuração antes de cada teste"""
        self.receiver = RDT20Receiver(9100)
        self.receiver.start()
        time.sleep(0.3)
    
    def tearDown(self):
        """Limpeza após cada teste"""
        self.receiver.close()
    
    def test_perfect_channel(self):
        """Teste com canal perfeito"""
        sender = RDT20Sender(('localhost', 9100), use_simulator=False)
        
        messages = [f"Test{i}" for i in range(10)]
        for msg in messages:
            sender.send_message(msg)
        
        time.sleep(0.5)
        received = self.receiver.get_messages()
        
        self.assertEqual(len(received), len(messages))
        self.assertEqual(sender.get_statistics()['retransmissions'], 0)
        
        sender.close()
    
    def test_with_corruption(self):
        """Teste com 30% de corrupção"""
        sender = RDT20Sender(('localhost', 9100), use_simulator=True, corrupt_rate=0.3)
        
        messages = [f"Test{i}" for i in range(10)]
        for msg in messages:
            sender.send_message(msg)
        
        time.sleep(0.5)
        received = self.receiver.get_messages()
        
        # Todas as mensagens devem chegar
        self.assertEqual(len(received), len(messages))
        # Deve haver retransmissões
        self.assertGreater(sender.get_statistics()['retransmissions'], 0)
        
        sender.close()


class TestRDT21(unittest.TestCase):
    """Testes para RDT 2.1"""
    
    def setUp(self):
        """Configuração antes de cada teste"""
        self.receiver = RDT21Receiver(9101)
        self.receiver.start()
        time.sleep(0.3)
    
    def tearDown(self):
        """Limpeza após cada teste"""
        self.receiver.close()
    
    def test_perfect_channel(self):
        """Teste com canal perfeito"""
        sender = RDT21Sender(('localhost', 9101), use_simulator=False)
        
        messages = [f"Test{i}" for i in range(10)]
        for msg in messages:
            sender.send_message(msg)
        
        time.sleep(0.5)
        received = self.receiver.get_messages()
        
        self.assertEqual(len(received), len(messages))
        self.assertEqual(sender.get_statistics()['retransmissions'], 0)
        
        sender.close()
    
    def test_with_corruption(self):
        """Teste com 20% de corrupção em DATA e ACK"""
        sender = RDT21Sender(('localhost', 9101), use_simulator=True, corrupt_rate=0.2)
        
        messages = [f"Test{i}" for i in range(10)]
        for msg in messages:
            sender.send_message(msg)
        
        time.sleep(0.5)
        received = self.receiver.get_messages()
        stats = self.receiver.get_statistics()
        
        # Todas as mensagens devem chegar
        self.assertEqual(len(received), len(messages))
        # Não deve haver duplicatas
        self.assertEqual(stats['messages_delivered'], len(messages))
        
        sender.close()
    
    def test_no_duplicates(self):
        """Teste para verificar que não há duplicatas"""
        sender = RDT21Sender(('localhost', 9101), use_simulator=True, corrupt_rate=0.2)
        
        messages = [f"Message_{i}" for i in range(15)]
        for msg in messages:
            sender.send_message(msg)
        
        time.sleep(0.5)
        received = self.receiver.get_messages()
        
        # Converter para strings para comparação
        received_str = [m.decode() for m in received]
        
        # Verificar que todas as mensagens são únicas
        self.assertEqual(len(received_str), len(set(received_str)))
        # Verificar que todas as mensagens esperadas chegaram
        self.assertEqual(len(received_str), len(messages))
        
        sender.close()


class TestRDT30(unittest.TestCase):
    """Testes para RDT 3.0"""
    
    def setUp(self):
        """Configuração antes de cada teste"""
        self.receiver = RDT30Receiver(9102)
        self.receiver.start()
        time.sleep(0.3)
    
    def tearDown(self):
        """Limpeza após cada teste"""
        self.receiver.close()
    
    def test_perfect_channel(self):
        """Teste com canal perfeito"""
        sender = RDT30Sender(('localhost', 9102), timeout=2.0, use_simulator=False)
        
        messages = [f"Test{i}" for i in range(10)]
        for msg in messages:
            sender.send_message(msg)
        
        time.sleep(0.5)
        received = self.receiver.get_messages()
        stats = sender.get_statistics()
        
        self.assertEqual(len(received), len(messages))
        self.assertEqual(stats['retransmissions'], 0)
        self.assertEqual(stats['timeouts'], 0)
        
        sender.close()
    
    def test_with_loss(self):
        """Teste com 15% de perda de pacotes"""
        sender = RDT30Sender(('localhost', 9102), timeout=1.0, use_simulator=True,
                            loss_rate=0.15, corrupt_rate=0.0)
        
        messages = [f"Test{i}" for i in range(15)]
        for msg in messages:
            sender.send_message(msg)
        
        time.sleep(0.5)
        received = self.receiver.get_messages()
        stats = sender.get_statistics()
        
        # Todas as mensagens devem chegar
        self.assertEqual(len(received), len(messages))
        # Deve haver timeouts devido a perdas
        self.assertGreater(stats['timeouts'], 0)
        
        sender.close()
    
    def test_with_loss_and_corruption(self):
        """Teste com perda e corrupção"""
        sender = RDT30Sender(('localhost', 9102), timeout=1.0, use_simulator=True,
                            loss_rate=0.15, corrupt_rate=0.10)
        
        messages = [f"Test{i}" for i in range(15)]
        for msg in messages:
            sender.send_message(msg)
        
        time.sleep(0.5)
        received = self.receiver.get_messages()
        stats = sender.get_statistics()
        
        # Todas as mensagens devem chegar
        self.assertEqual(len(received), len(messages))
        # Deve haver retransmissões
        self.assertGreater(stats['retransmissions'], 0)
        
        sender.close()
    
    def test_throughput(self):
        """Teste de throughput"""
        sender = RDT30Sender(('localhost', 9102), timeout=1.0, use_simulator=True,
                            loss_rate=0.10, corrupt_rate=0.05)
        
        # Enviar mensagens maiores
        messages = [f"Message{i}" * 10 for i in range(20)]
        
        start_time = time.time()
        for msg in messages:
            sender.send_message(msg)
        end_time = time.time()
        
        time.sleep(0.5)
        received = self.receiver.get_messages()
        stats = sender.get_statistics()
        
        # Verificar que todas chegaram
        self.assertEqual(len(received), len(messages))
        
        # Calcular throughput
        total_time = end_time - start_time
        throughput = stats['total_bytes_sent'] / total_time
        
        # Throughput deve ser positivo
        self.assertGreater(throughput, 0)
        
        print(f"\nThroughput: {throughput:.2f} bytes/s ({throughput*8/1024:.2f} Kbps)")
        print(f"Taxa de retransmissão: {stats['retransmissions']/stats['packets_sent']*100:.1f}%")
        
        sender.close()


def run_all_tests():
    """Executa todos os testes da Fase 1"""
    print("\n" + "="*70)
    print("EXECUTANDO TODOS OS TESTES DA FASE 1")
    print("="*70 + "\n")
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Adicionar todos os testes
    suite.addTests(loader.loadTestsFromTestCase(TestRDT20))
    suite.addTests(loader.loadTestsFromTestCase(TestRDT21))
    suite.addTests(loader.loadTestsFromTestCase(TestRDT30))
    
    # Executar
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Sumário
    print("\n" + "="*70)
    print("SUMÁRIO DOS TESTES")
    print("="*70)
    print(f"Testes executados: {result.testsRun}")
    print(f"Sucessos: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Falhas: {len(result.failures)}")
    print(f"Erros: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n✅ TODOS OS TESTES PASSARAM!")
    else:
        print("\n❌ ALGUNS TESTES FALHARAM")
    
    print("="*70 + "\n")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
