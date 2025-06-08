# Totally Ordered Multicast using Lamport Logical Clocks

Este projeto demonstra a implementação de um sistema de **multicast com ordenação total** de mensagens, utilizando **relógios lógicos de Lamport**, conforme a Seção 5.2.1 do livro texto.

## 📚 Objetivo

Garantir que todas as mensagens multicast enviadas por processos distribuídos sejam entregues na **mesma ordem** para todos os membros do grupo, mesmo em uma rede com diferentes atrasos de propagação.

---

## 🧠 Conceitos utilizados

- **Relógios Lógicos de Lamport**
- **UDP Multicast** para envio de mensagens entre peers
- **TCP** para controle de grupo e coleta de logs
- **EC2 da AWS** em múltiplas regiões para simular ambiente distribuído

---

## 🧪 Arquitetura do sistema

- **Group Manager (`GroupMngr.py`)**: registra os peers antes do início
- **Peers (`peerCommunicatorUDP.py`)**: enviam mensagens e recebem de outros processos
- **Servidor de comparação (`comparisonServer.py`)**: inicia a execução, coleta os logs e verifica a ordenação das mensagens

---

## ⚙️ Tecnologias

- Python
- EC2 AWS com Ubuntu/Amazon Linux

---

## 📦 Estrutura do código

```bash
.
├── GroupMngr.py              # Gerenciador de grupo
├── peerCommunicatorUDP.py    # Lógica de envio e recebimento de mensagens pelos peers
├── comparisonServer.py       # Coordena a execução e coleta os logs
├── constMP.py                # Configurações globais: IPs, portas, número de peers
└── README.md                 # Este arquivo
