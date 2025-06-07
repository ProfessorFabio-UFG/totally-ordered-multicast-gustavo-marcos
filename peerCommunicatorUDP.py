from socket  import *
from constMP import *
import threading
import random
import time
import pickle
import heapq
from requests import get

# -------------------
# Lamport clock and message queue structures
logical_clock = 0
message_queue = []  # Min-heap based on (timestamp, sender_id)
delivered_messages = set()

handShakeCount = 0
PEERS = []

sendSocket = socket(AF_INET, SOCK_DGRAM)
recvSocket = socket(AF_INET, SOCK_DGRAM)
recvSocket.bind(('0.0.0.0', PEER_UDP_PORT))

serverSock = socket(AF_INET, SOCK_STREAM)
serverSock.bind(('0.0.0.0', PEER_TCP_PORT))
serverSock.listen(1)

# -------------------
def get_public_ip():
    ipAddr = get('https://api.ipify.org').content.decode('utf8')
    print('My public IP address is: {}'.format(ipAddr))
    return ipAddr

def registerWithGroupManager():
    clientSock = socket(AF_INET, SOCK_STREAM)
    print('Connecting to group manager:', (GROUPMNGR_ADDR, GROUPMNGR_TCP_PORT))
    clientSock.connect((GROUPMNGR_ADDR, GROUPMNGR_TCP_PORT))
    ipAddr = get_public_ip()
    req = {"op": "register", "ipaddr": ipAddr, "port": PEER_UDP_PORT}
    msg = pickle.dumps(req)
    print('Registering with group manager:', req)
    clientSock.send(msg)
    clientSock.close()

def getListOfPeers():
    clientSock = socket(AF_INET, SOCK_STREAM)
    clientSock.connect((GROUPMNGR_ADDR, GROUPMNGR_TCP_PORT))
    req = {"op": "list"}
    msg = pickle.dumps(req)
    clientSock.send(msg)
    msg = clientSock.recv(2048)
    PEERS = pickle.loads(msg)
    clientSock.close()
    return PEERS

# -------------------
class MsgHandler(threading.Thread):
    def __init__(self, sock):
        threading.Thread.__init__(self)
        self.sock = sock

    def run(self):
        global handShakeCount, logical_clock, message_queue, delivered_messages
        logList = []

        while handShakeCount < N:
            msgPack = self.sock.recv(1024)
            msg = pickle.loads(msgPack)
            if msg[0] == 'READY':
                handShakeCount += 1
                print('--- Handshake received from:', msg[1])

        print('All handshakes received. Listening for messages...')
        stopCount = 0

        while True:
            msgPack, addr = self.sock.recvfrom(4096)
            msg = pickle.loads(msgPack)

            if msg["type"] == "DATA":
                sender = msg["sender_id"]
                timestamp = msg["timestamp"]
                seq = msg["seq"]

                # Atualizar relógio local
                logical_clock = max(logical_clock, timestamp) + 1
                heapq.heappush(message_queue, ((timestamp, sender), msg))

                # Tentar entregar mensagens na ordem correta
                while message_queue:
                    top_key, top_msg = message_queue[0]
                    if top_key not in delivered_messages:
                        delivered_messages.add(top_key)
                        heapq.heappop(message_queue)
                        print(f'Entregue: {top_msg}')
                        logList.append(top_msg)
                    else:
                        break

            elif msg["type"] == "STOP":
                stopCount += 1
                if stopCount == N:
                    break

        with open(f'logfile{myself}.log', 'w') as logFile:
            logFile.writelines(str(logList))

        print('Enviando log ao servidor...')
        clientSock = socket(AF_INET, SOCK_STREAM)
        clientSock.connect((SERVER_ADDR, SERVER_PORT))
        msgPack = pickle.dumps(logList)
        clientSock.send(msgPack)
        clientSock.close()

        handShakeCount = 0
        exit(0)

# -------------------
def waitToStart():
    (conn, addr) = serverSock.accept()
    msgPack = conn.recv(1024)
    msg = pickle.loads(msgPack)
    conn.send(pickle.dumps('Peer process ' + str(msg[0]) + ' started.'))
    conn.close()
    return msg

# -------------------
registerWithGroupManager()

while True:
    print('Waiting for start...')
    myself, nMsgs = waitToStart()
    print(f'I am up. My ID is {myself}')

    if nMsgs == 0:
        print('Terminating.')
        exit(0)

    time.sleep(5)

    msgHandler = MsgHandler(recvSocket)
    msgHandler.start()

    PEERS = getListOfPeers()

    for addrToSend in PEERS:
        msg = ('READY', myself)
        msgPack = pickle.dumps(msg)
        sendSocket.sendto(msgPack, (addrToSend, PEER_UDP_PORT))

    while handShakeCount < N:
        pass

    for msgNumber in range(nMsgs):
        time.sleep(random.uniform(0.01, 0.1))
        logical_clock += 1
        msg = {
            "type": "DATA",
            "timestamp": logical_clock,
            "sender_id": myself,
            "seq": msgNumber
        }
        msgPack = pickle.dumps(msg)
        for addrToSend in PEERS:
            sendSocket.sendto(msgPack, (addrToSend, PEER_UDP_PORT))
            print(f'Sent message {msgNumber} with timestamp {logical_clock}')

    for addrToSend in PEERS:
        stopMsg = {"type": "STOP"}
        sendSocket.sendto(pickle.dumps(stopMsg), (addrToSend, PEER_UDP_PORT))
