# EFC 02 - Protocolos de Transporte Confiável

Implementação de protocolos de transporte confiável em Python, incluindo RDT (Reliable Data Transfer), Go-Back-N, Selective Repeat e TCP simplificado.

## 📋 Requisitos

- Python 3.8 ou superior

### Instalação do Python

Se o Python não estiver instalado:

1. Acesse: https://www.python.org/downloads/
2. Baixe a versão **3.8 ou superior**
3. Durante a instalação, **marque a opção "Add Python to PATH"**
4. Verifique a instalação abrindo um novo terminal e digitando:
   ```bash
   python --version
   ```

## 📁 Estrutura do Projeto

```
EFC 02 REDES/
├── fase1/              # Fase 1 - Protocolos RDT (Reliable Data Transfer)
│   ├── __init__.py     # Exporta RDT20Sender, RDT20Receiver, etc.
│   ├── rdt20.py        # RDT 2.0 - Stop-and-wait com ACK/NAK
│   ├── rdt21.py        # RDT 2.1 - Stop-and-wait com números de sequência
│   └── rdt30.py        # RDT 3.0 - Stop-and-wait com timer e perdas
│
├── fase2/              # Fase 2 - Protocolos de Pipelining
│   ├── __init__.py     # Exporta GBNSender, GBNReceiver, SRSender, SRReceiver
│   ├── gbn.py          # Go-Back-N - Protocolo de janela deslizante
│   └── sr.py           # Selective Repeat - Retransmissão seletiva
│
├── fase3/              # Fase 3 - TCP Simplificado
│   ├── __init__.py     # Exporta SimpleTCPSocket
│   ├── tcp.py          # Alias para tcp_socket (compatibilidade)
│   ├── tcp_socket.py   # Implementação principal do TCP
│   ├── tcp_client.py   # Cliente TCP
│   └── tcp_server.py   # Servidor TCP
│
├── utils/               # Utilitários compartilhados
│   ├── __init__.py     # Exporta todas as classes utilitárias
│   ├── packet.py       # Pacotes RDT (RDT20Packet, RDT21Packet, RDT30Packet)
│   ├── gbn_packet.py   # Pacotes Go-Back-N
│   ├── sr_packet.py    # Pacotes Selective Repeat
│   ├── tcp_segment.py  # Segmentos TCP
│   ├── logger.py       # Sistema de logging colorido
│   └── simulator.py    # Simulador de canal não confiável
│
├── testes/              # Testes automatizados
│   ├── test_fase1.py   # Testes da Fase 1 (RDT)
│   ├── test_fase2.py   # Testes da Fase 2 (GBN e SR)
│   └── test_fase3.py   # Testes da Fase 3 (TCP)
│
├── relatório/          # Relatórios e documentação
│
├── executar_teste.bat  # Script Windows para executar testes
├── executar_teste.ps1  # Script PowerShell para executar testes
└── README.md           # Este arquivo
```

## 🔧 Convenções de Importação

### Importar classes da Fase 1
```python
from fase1 import RDT20Sender, RDT20Receiver
from fase1 import RDT21Sender, RDT21Receiver
from fase1 import RDT30Sender, RDT30Receiver

# Ou importar módulos específicos
from fase1.rdt20 import RDT20Sender, RDT20Receiver
```

### Importar classes da Fase 2
```python
from fase2 import GBNSender, GBNReceiver
from fase2 import SRSender, SRReceiver

# Ou importar módulos específicos
from fase2.gbn import GBNSender, GBNReceiver
from fase2.sr import SRSender, SRReceiver
```

### Importar classes da Fase 3
```python
from fase3 import SimpleTCPSocket
# Ou
from fase3.tcp import SimpleTCPSocket
# Ou
from fase3.tcp_socket import SimpleTCPSocket
```

### Importar utilitários
```python
from utils import (
    RDT20Packet, GBNPacket, SRPacket, TCPSegment,
    ProtocolLogger, UnreliableChannel
)
```

## 🚀 Executando os Testes

### Opção 1: Script Automatizado (Recomendado)

**Windows (CMD):**
1. Clique duas vezes no arquivo `executar_teste.bat`
2. Escolha a opção desejada no menu

**PowerShell:**
1. Clique duas vezes no arquivo `executar_teste.ps1`
2. Escolha a opção desejada no menu

### Opção 2: Linha de Comando

Abra o terminal (CMD ou PowerShell) na pasta do projeto e execute:

#### Testar Fase 1 (RDT 2.0, 2.1, 3.0)
```bash
python -m unittest discover -s testes -p "test_fase1.py" -v
```

#### Testar Fase 2 (GBN e SR)
```bash
python -m unittest discover -s testes -p "test_fase2.py" -v
```

#### Testar Fase 3 (TCP)
```bash
python -m unittest discover -s testes -p "test_fase3.py" -v
```

#### Testar Tudo
```bash
python -m unittest discover -s testes -v
```

### Opção 3: Testes Individuais

#### RDT 2.0
```bash
python -m unittest testes.test_fase1.TestRDT20.test_perfect_channel -v
```

#### GBN
```bash
python -m unittest testes.test_fase2.TestGBN.test_gbn_perfect_channel -v
```

#### SR
```bash
python -m unittest testes.test_fase2.TestSR.test_sr_perfect_channel -v
```

#### TCP
```bash
python -m unittest testes.test_fase3.TestTCPBasic.test_three_way_handshake -v
```

## 📚 Referências

- **RDT 2.0**: Seção 3.4.1, Figura 3.10
- **RDT 2.1**: Stop-and-wait com números de sequência
- **RDT 3.0**: Stop-and-wait com timer e tratamento de perdas
- **Go-Back-N**: Seção 3.4.3, Figuras 3.19 e 3.20
- **Selective Repeat**: Retransmissão seletiva com bufferização
- **TCP**: Three-way handshake, flow control e four-way close
