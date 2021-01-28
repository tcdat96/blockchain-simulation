'''
network.py
handling p2p communication
'''
import socket
from queue import Queue
import logging
import time
import random
import pickle

#Default Ports
FLOODING_PORT = 18015
SYN_PORT = 9898
#Tags
MAX_SIZE = 8196
FIRST_BLOCK = 100
REQUEST_IP_LIST = 0
RETURN_IP_LIST = 1
REQUEST_TO_CONNECT = 11
ACCEPT_TO_CONNECT = 12
REQUEST_LEDGER_SIZE = 13
RETURN_LEDGER_SIZE = 14
REQUEST_TO_SYNC = 15
RETURN_TO_SYNC = 16
NEW_TRANSACTION = 21
NEW_BLOCK = 22
INVALID_TRANSACTION = 23
INVALID_BLOCK = 24

class Networking:
    # BUFFER: FIFO Queue
    # PORT: Default is flooding port
    def __init__(self, MY_IP:str, BUFFER: Queue, PORT=FLOODING_PORT): 
        self.MY_IP = MY_IP
        self.HOSTs = []
        self.PORT = PORT
        self.BUFFER = BUFFER
        self.sync_ready = [False, None, None] # ready, address, ledger size of bytes
        self.stop = False

    # Call after init in separated Thread
    # listening for new connection
    # and receiving data --> BUFFER
    def listening (self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', self.PORT))
            s.listen(5)
            logging.info('Net - Start listening....')
            while not self.stop:
                conn, address = s.accept()
                with conn:
                    data = conn.recv(MAX_SIZE)
                    if data:
                        tag = data[-1]
                        logging.debug(('receiving', tag, address[0]))
                        DAT = (address, tag, data[:-1])
                        if tag>14 or tag==13:
                            self.BUFFER.put(DAT)
                            continue
                        if self.request(DAT=DAT) != 1:
                            continue
                        if self.reply(DAT) != 1:
                            continue
                        if self.sync_ledger_size(DAT) != 1:
                            continue
                        
                    else:
                        logging.error('Net - Data receive NONE....')
        return 1

    # Send data
    # set IS_SYN True to send data to SYNC_PORT
    def sending (self, HOST:str, data:bytes, tag:int, IS_SYN=False):
        if HOST==self.MY_IP:
            logging.debug('NET - Send to self....')
            return
        if HOST=='127.0.0.1':
            logging.debug('NET - Send to self....')
            return
        PORT = self.PORT if not IS_SYN else SYN_PORT
        data += tag.to_bytes(1, 'big')
        # logging.debug(('sending', tag, data[-1], HOST))
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.connect((HOST, PORT))
                s.sendall(data)
            except:
                logging.error('NET - Connect error to %s....', HOST)

    # Send data to servers specified in list HOSTs
    # If HOSTs not specified, broadcast to self.HOSTs
    def broadcast (self, data:bytes, tag:int, HOSTs:list=None, exclude=[]):
        if HOSTs==None:
            HOSTs = self.HOSTs
        random.shuffle(HOSTs)
        for HOST in HOSTs:
            if HOST not in exclude:
                self.sending(HOST, data, tag)

    # Call only ONCE in main to build up self.HOSTs list
    # HOST: Must specify 1st target IP
    # DAT: internal used only, ignore!
    # thres_min: minimum number of connected hosts before stop send requesting
    def request (self, HOST:str=None, DAT=None, thres_min=2):
        if HOST != None:
            self.sending(HOST, b'r1', REQUEST_IP_LIST)
            self.sending(HOST, b'', REQUEST_TO_CONNECT)
            return 0
        if DAT:
            address = DAT[0]; tag=DAT[1]; data = DAT[2]
            if tag == RETURN_IP_LIST and len(self.HOSTs) < thres_min:
                data = data.decode()
                hosts = data.split('\n')
                if self.MY_IP in hosts:
                    hosts.remove(self.MY_IP)
                if len(hosts) < 1:
                    return None
                random.shuffle(hosts)
                self.broadcast(b'r2', REQUEST_IP_LIST, HOSTs=hosts)
                self.broadcast(b'', REQUEST_TO_CONNECT, HOSTs=hosts)
                return None
            if tag == ACCEPT_TO_CONNECT:
                if address[0] not in self.HOSTs and address[0]!=self.MY_IP:
                    self.HOSTs.append(address[0])
                return None
            return 1
        logging.error('NET - Request to join error....')
        return -1

    # Internal used only, to send reply to the request() func
    # thres_max: maximum number of connected hosts before stop accepting more hosts
    def reply(self, DAT:tuple, thres_max=10):
        address = DAT[0]; tag=DAT[1]; data = DAT[2]
        if tag == REQUEST_IP_LIST:
            data = '\n'.join(self.HOSTs)
            data = data.encode()
            self.sending(address[0], data, RETURN_IP_LIST)
            return None
        if tag == REQUEST_TO_CONNECT and len(self.HOSTs) < thres_max:
            host = address[0]
            if host not in self.HOSTs:
                self.HOSTs.append(host)
            self.sending(host, b'', ACCEPT_TO_CONNECT)
            return None
        return 1

    # Internal used only, request size (in bytes) of current ledger
    def sync_ledger_size(self, DAT=None, addr:list=None, **kwargs):
        if not DAT:
            logging.error('NET - SYNC start....')
            data=pickle.dumps(kwargs)
            self.broadcast(data, REQUEST_LEDGER_SIZE)
            return 0

        address, tag, sz = DAT
        if tag==RETURN_LEDGER_SIZE and self.sync_ready[0]==False and address[0] not in addr:
            self.sync_ready = (True, address[0], int(sz.decode()))
            return None
        
        return 1

    # Sync ledger, listen for new connection at SYNC_PORT to receive sync data
    # timeout (in second): wait time before exit if no server accept to sync
    # address: IP. If specified, don't receive sync data from this address
    # kwargs: to specify what to sync
    # returning (data, from_address)
    def sync(self, timeout:float, address:list=None, **kwargs):
        self.sync_ledger_size(address, kwargs)
        start = time.time()
        while not self.sync_ready[0]:
            if time.time()-start > timeout:
                logging.error('NET - SYNC timeout....')
                return None
            time.sleep(1)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', SYN_PORT))
            s.listen(1)
            conn, _ = s.accept()
            with conn:
                data = conn.recv(self.sync_ready[2]+MAX_SIZE)
                if data:
                    return data, self.sync_ready[1]
        
        logging.info('NET - SYNC done....')
        self.sync_ready[0] = False
        return None
    
# net = Networking(Buffer)
# net.listening() #new thread
# net.request(HOST='10.0.100.97')
# data = net.sync(5, {}) #new thread, block
# previous_sync_address = net.sync_ready[1]
# client: last_block_hash
# miner: ledger_size, pool