
"""
Aplicação Cliente de Exemplo - TCP Simplificado
Demonstra uso do SimpleTCPSocket como cliente
"""

import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fase3.tcp import SimpleTCPSocket


def main():
    host = 'localhost'
    porta = 8000
    mensagem = "Olá, servidor TCP simplificado! Esta é uma mensagem de teste."
    
    if len(sys.argv) > 1:
        host = sys.argv[1]
    if len(sys.argv) > 2:
        try:
            porta = int(sys.argv[2])
        except ValueError:
            print(f"Erro: Porta inválida '{sys.argv[2]}'")
            sys.exit(1)
    if len(sys.argv) > 3:
        mensagem = ' '.join(sys.argv[3:])
    
    print("╔" + "═"*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + "  CLIENTE TCP SIMPLIFICADO".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "═"*78 + "╝\n")
    
    print(f"[CLIENTE] Configuração:")
    print(f"  • Servidor: {host}:{porta}")
    print(f"  • Mensagem: \"{mensagem}\"")
    print(f"  • Tamanho: {len(mensagem.encode())} bytes\n")
    
    print(f"[CLIENTE] Criando socket...")
    client = SimpleTCPSocket(verbose=True)
    
    try:
        print(f"\n{'='*80}")
        print(f"[CLIENTE] Conectando a {host}:{porta}...")
        print(f"{'='*80}\n")
        
        start_time = time.time()
        success = client.connect(host, porta)
        elapsed = time.time() - start_time
        
        if not success:
            print(f"\n[CLIENTE] ❌ Falha ao conectar ao servidor")
            print(f"[CLIENTE] Verifique se o servidor está rodando em {host}:{porta}")
            return
        
        print(f"\n{'='*80}")
        print(f"[CLIENTE] ✅ Conexão estabelecida!")
        print(f"[CLIENTE] Estado: {client.state}")
        print(f"[CLIENTE] Tempo de conexão: {elapsed:.3f}s")
        print(f"{'='*80}\n")
        
        print(f"[CLIENTE] Enviando dados...\n")
        
        data = mensagem.encode()
        start_time = time.time()
        bytes_sent = client.send(data)
        elapsed = time.time() - start_time
        
        print(f"\n{'='*80}")
        print(f"[CLIENTE] ✅ Dados enviados com sucesso!")
        print(f"  • Bytes enviados: {bytes_sent}")
        print(f"  • Tempo de envio: {elapsed:.3f}s")
        print(f"  • Taxa: {(bytes_sent/1024)/elapsed:.2f} KB/s")
        print(f"{'='*80}\n")
        
        time.sleep(0.5)
        
        print(f"[CLIENTE] Fechando conexão...")
        client.close()
        print(f"[CLIENTE] ✅ Conexão encerrada (estado: {client.state})\n")
    
    except KeyboardInterrupt:
        print(f"\n\n[CLIENTE] ⚠️  Interrompido pelo usuário (Ctrl+C)")
        client.close()
    
    except Exception as e:
        print(f"\n[CLIENTE] ❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        client.close()


if __name__ == '__main__':
    main()