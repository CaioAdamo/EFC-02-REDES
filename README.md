# EFC 02 - Protocolos de Transporte Confiável

Implementação de protocolos de transporte confiável em Python, incluindo RDT (Reliable Data Transfer), Go-Back-N, Selective Repeat e TCP simplificado.

## 📋 Requisitos

- Python 3.8 ou superior
- Nenhuma dependência externa necessária (usa apenas bibliotecas padrão)

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

## 📊 Status dos Testes

**Última atualização**: 16 de novembro de 2025

### ✅ Fase 1 - RDT (Reliable Data Transfer)
**Status**: ✅ **100% COMPLETO** (9/9 testes passando)

**Protocolos implementados**:
- ✅ **RDT 2.0**: Stop-and-wait com ACK/NAK (detecção de corrupção)
- ✅ **RDT 2.1**: Stop-and-wait com números de sequência (elimina duplicatas)
- ✅ **RDT 3.0**: Stop-and-wait com timer (trata perdas e corrupção)

**Testes validados**:
- Canal perfeito (sem erros)
- Corrupção de pacotes (20-30%)
- Perda de pacotes (15%)
- Perda + corrupção combinados
- Throughput em cenários adversos

### ⚠️ Fase 2 - Go-Back-N e Selective Repeat  
**Status**: ⚠️ **77% FUNCIONAL** (10/13 testes passando, 2 skipados, 1 falha)

**Protocolos implementados**:
- ✅ **Go-Back-N (GBN)**: Pipelining com janela deslizante e retransmissão de toda a janela
  - Canal perfeito ✅
  - Janela deslizante ✅  
  - Com perdas (10%) ✅
- ✅ **Selective Repeat (SR)**: Pipelining com bufferização e retransmissão seletiva
  - Canal perfeito ✅
  - Bufferização de pacotes fora-de-ordem ✅
  - ACKs individuais (não cumulativos) ✅
  - Com perdas (10%) ✅

**Testes obrigatórios**:
- ✅ Eficiência GBN vs RDT 3.0
- ✅ Perdas 10% GBN  
- ✅ Perdas 10% SR
- ✅ Ordenação SR (bufferização correta)
- ⏭️ Análise de desempenho (skipado por isolamento de porta)

**Problema conhecido**:
- ❌ **test_throughput_comparison**: GBN entregando apenas 7/10 pacotes
  - Possível causa: Timeout muito curto ou perda excessiva de ACKs
  - **Workaround**: Testes individuais de GBN e SR passam perfeitamente

### ⚠️ Fase 3 - TCP Simplificado
**Status**: ⚠️ **25% FUNCIONAL** (2/8 testes passando)

**Funcionalidades implementadas**:
- ✅ **Three-way handshake** (SYN → SYN-ACK → ACK)
- ✅ **Handshake com perdas** (retransmissão de SYN)
- ⚠️ Data transfer (implementado mas falhando em testes)
- ⚠️ Bidirectional transfer (implementado mas falhando)
- ⚠️ Four-way close (implementado mas falhando)
- ⚠️ Flow control (implementado mas falhando)

**Testes passando**:
- ✅ test_three_way_handshake
- ✅ test_handshake_with_losses

**Testes falhando** (6/8):
- ❌ test_data_transfer: Recebe bytes vazios
- ❌ test_bidirectional_transfer: Lista vazia no servidor
- ❌ test_four_way_close: Estado permanece ESTABLISHED
- ❌ test_large_data_transfer: 0 bytes recebidos
- ❌ test_data_transfer_with_losses: Nenhum dado recebido
- ❌ test_transfer_with_corruption: Nenhum dado recebido

**Problemas conhecidos**:
- Dados não chegam ao receptor (bytes vazios)
- Máquina de estados não transiciona corretamente após handshake
- Race conditions em sockets compartilhados
- Thread de recepção pode não estar processando segmentos DATA

## ⚠️ Problemas Comuns e Soluções

### Python não encontrado
- **Solução**: Instale o Python e certifique-se de marcar "Add Python to PATH"
- Ou use o caminho completo: `C:\Python3X\python.exe -m unittest ...`

### Erro de módulo não encontrado
- **Solução**: Certifique-se de estar na pasta raiz do projeto ao executar
- Verifique se todos os arquivos estão presentes nas pastas `fase1/`, `fase2/`, `fase3/`, `testes/` e `utils/`

### Testes da Fase 3 com race conditions
- **Solução**: Execute os testes da Fase 3 individualmente (veja Opção 3 acima)

### Erro de encoding no Windows
- **Solução**: O logger já está configurado para lidar com encoding UTF-8 no Windows automaticamente

## 💡 Dicas

- Use `-v` para saída verbosa (mostra cada teste)
- Use `-k` para filtrar testes específicos: `python -m unittest -k "rdt" -v`
- Para debugar, adicione `print()` nos arquivos de teste ou implementação
- Os logs coloridos podem não aparecer corretamente em alguns terminais, mas não afetam a funcionalidade

## 📝 Estrutura de Pacotes Python

Todos os diretórios principais (`fase1`, `fase2`, `fase3`, `utils`) são pacotes Python válidos com `__init__.py` que exportam as classes principais.

## 📚 Referências

- **RDT 2.0**: Seção 3.4.1, Figura 3.10
- **RDT 2.1**: Stop-and-wait com números de sequência
- **RDT 3.0**: Stop-and-wait com timer e tratamento de perdas
- **Go-Back-N**: Seção 3.4.3, Figuras 3.19 e 3.20
- **Selective Repeat**: Retransmissão seletiva com bufferização
- **TCP**: Three-way handshake, flow control e four-way close