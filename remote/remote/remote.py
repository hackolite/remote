import socket
import threading
import SocketServer
import dill 
import psutil
import sys
from  importlib import import_module
import paramiko
import time
import random
import hashlib
import ssl
from Crypto.Cipher import AES
import base64
import os
import time
from  importlib import import_module



def start_remote(HOST,USER,PASSWORD, PORT):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(HOST, 22, username=USER, password=PASSWORD)
        cmd = """python -c 'from remote.remote import start_server;start_server("%s", %s)' """ % (HOST, PORT,)  
        print cmd
        stdin, stdout, stderr = client.exec_command(cmd)
        print stderr.readlines(),stdout.readlines()

def encryption():
    BLOCK_SIZE = 32
    PADDING = '{'
    pad = lambda s: s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * PADDING
    EncodeAES = lambda c, s: base64.b64encode(c.encrypt(pad(s)))
    DecodeAES = lambda c, e: c.decrypt(base64.b64decode(e)).rstrip(PADDING)
    secret = os.urandom(BLOCK_SIZE)
    cipher = AES.new(secret)
    encoded = EncodeAES(cipher, 'password') 
    print 'Encrypted string:', encoded
    decoded = DecodeAES(cipher, encoded)
    print 'Decrypted string:', decoded


def start_server(HOST, PORT):
        print HOST, PORT
        server = ThreadedTCPServer((HOST, PORT), ThreadedTCPRequestHandler) 
        server.serve_forever()
        #server_thread = threading.Thread(target=server.serve_forever)
        #server_thread.daemon = True
        #server_thread.start()

def remoteFunction(HOST, USER,PASSWORD):
    def decorate(func):         
        def wrapper(*args, **kwds):
            PORT = random.randrange(10000, 20000)
            threads = []
            t = threading.Thread(target=start_remote, args=(HOST,USER,PASSWORD,PORT))
            threads.append(t)
            t.daemon = True
            t.start()
            time.sleep(0.9)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((HOST, PORT))
            modules_list = sys.modules.keys()
            # i dont know why sys.modules.keys give psutils.sys, i remove this
            modules_list = [i for i in modules_list if i.count('.') == 0]
            print 'module list', modules_list
            h = hashlib.sha1()
            pickledfunc = dill.dumps(func)
            h.update(pickledfunc)
            hexdigestkey = h.hexdigest()
            lis = [pickledfunc, modules_list, args, kwds, hexdigestkey]
            lis = dill.dumps(lis)
            sock.sendall(lis)   
            response = sock.recv(4096)             
            response = dill.loads(response)
            sock.close()
            print response
        return wrapper
    return decorate


class ThreadedTCPRequestHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        data = self.request.recv(4096)
        cur_thread = threading.current_thread()
        response = "{}: {}".format(cur_thread.name, data)
        rec = dill.loads(data)
        modulesNames = rec[1]
        h = hashlib.sha1()
        h.update(rec[0])
        hexdigestkey = h.hexdigest() 
        print rec[4],hexdigestkey
        if hexdigestkey != rec[4]:
        	sys.exit(1)
        remfunc = dill.loads(rec[0])
        for mod_name in modulesNames:
            remfunc.__globals__[mod_name] = import_module(mod_name)
        res = remfunc(*rec[2], **rec[3])
        res_pack = dill.dumps(res)
        self.request.sendall(res_pack)



class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass


@remoteFunction('localhost', '', '')
def toto(path):
    ret = os.listdir(path)
    return ret


toto('.')
