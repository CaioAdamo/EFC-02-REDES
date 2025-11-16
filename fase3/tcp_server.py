
"""
Aplicação Servidor de Exemplo - TCP Simplificado
Demonstra uso do SimpleTCPSocket como servidor
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fase3.tcp import SimpleTCPSocket


def main():
    porta = 8000
    
    if len(sys.argv) > 1:
        try:
            porta = int(sys.argv[1])
        except ValueError:
            print(f"Erro: Porta inválida '{sys.argv[1]}'")
            sys.exit(1)
    
    print("╔" + "═"*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + "  SERVIDOR TCP SIMPLIFICADO".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "═"*78 + "╝\n")
    
    print(f"[SERVIDOR] Criando socket na porta {porta}...")
    server = SimpleTCPSocket(porta, verbose=True)
    
    print(f"[SERVIDOR] Entrando em modo LISTEN...")
    server.listen()
    
    print(f"\n{'='*80}")
    print(f"[SERVIDOR] Aguardando conexões na porta {porta}...")
    print(f"{'='*80}\n")
    
    try:
        conn, addr = server.accept()
        
        if conn:
            print(f"\n{'='*80}")
            print(f"[SERVIDOR] ✅ Conexão estabelecida com {addr}")
            print(f"[SERVIDOR] Estado: {conn.state}")
            print(f"{'='*80}\n")
            
            print(f"[SERVIDOR] Aguardando dados do cliente...\n")
            
            data_received = b''
            while True:
                chunk = conn.recv(2048, timeout=10.0)
                
                if not chunk:
                    print(f"[SERVIDOR] Fim da transmissão (sem mais dados)")
                    break
                
                data_received += chunk
                print(f"[SERVIDOR] Recebeu {len(chunk)} bytes (total: {len(data_received)} bytes)")
            
            print(f"\n{'='*80}")
            print(f"[SERVIDOR] ✅ Recebeu total de {len(data_received)} bytes")
            print(f"{'='*80}\n")
            
            if len(data_received) > 0:
                amostra = data_received[:100]
                print(f"[SERVIDOR] Amostra dos dados recebidos:")
                print(f"  {amostra}")
                if len(data_received) > 100:
                    print(f"  ... (mais {len(data_received)-100} bytes)")
                print()
            
            print(f"[SERVIDOR] Fechando conexão...")
            conn.close()
            print(f"[SERVIDOR] ✅ Conexão encerrada (estado: {conn.state})")
        
        else:
            print(f"[SERVIDOR] ❌ Falha ao aceitar conexão")
    
    except KeyboardInterrupt:
        print(f"\n\n[SERVIDOR] ⚠️  Interrompido pelo usuário (Ctrl+C)")
    
    except Exception as e:
        print(f"\n[SERVIDOR] ❌ Erro: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        print(f"\n[SERVIDOR] Fechando servidor...")
        server.close()
        print(f"[SERVIDOR] ✅ Servidor encerrado\n")


if __name__ == '__main__':
    main()