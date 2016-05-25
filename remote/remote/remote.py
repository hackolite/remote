#!/usr/bin/python
#-*- coding: utf-8 -*-

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
from multiprocessing import Process



__author__ = "Loic laureote"
__credits__ = ["Loic.laureote"]
__version__ = "1.0.O"
__maintainer__ = "Loic.laureote"
__email__ = "laureote-loic@hotmail.com"
__status__ = "Developpement"

class SshClient:

    TIMEOUT = 4

    def __init__(self, host, port, username, password, key=None, passphrase=None):
        self.username = username
        self.password = password
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        if key is not None:
            key = paramiko.RSAKey.from_private_key(StringIO(key), password=passphrase)
        self.client.connect(host, port, username=username, password=password, pkey=key, timeout=self.TIMEOUT)

    def close(self):
        if self.client is not None:
            self.client.close()
            self.client = None

    def execute(self, command, sudo=False, feed_password=False):
        if sudo and self.username != "root":
            command = "sudo -S -p '' %s" % command
            feed_password = self.password is not None and len(self.password) > 0
        stdin, stdout, stderr = self.client.exec_command(command)

        if feed_password:
            stdin.write(self.password + "\n")
            stdin.flush()
        return {'out': stdout.readlines(),
                'err': stderr.readlines(),
                'retval': stdout.channel.recv_exit_status()}



def start_remote(HOST,USER,PASSWORD, PORT):
        #client = paramiko.SSHClient()
        #client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        #client.connect(HOST, 22, username=USER, password=PASSWORD)
        #cmd = """python -c 'from remote.remote import start_server;start_server("%s", %s)' """ % (HOST, PORT,)  
        client = SshClient(HOST, 22, USER, PASSWORD)
        cmd = """python -c 'from remote.remote import start_server;start_server("%s", %s)' """ % (HOST, PORT)
        ret = client.execute(cmd, sudo = True, feed_password=True)        
        print cmd
                
        print stderr.readlines(),stdout.readlines()


def encryption():
    """
    this method allow to encrypt communication between server and client,
    """
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




def start_remote(HOST,USER,PASSWORD, PORT):
        """
        start the remote server
        """
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(HOST, 22, username=USER, password=PASSWORD)
        cmd = """python -c 'from remote.remote import start_server;start_server("%s", %s)' """ % (HOST, PORT,)
        print HOST, PORT
        stdin, stdout, stderr = client.exec_command(cmd)

def stop_remote(HOST,USER,PASSWORD):
        pass


def start_server(HOST, PORT):
        """
        server creation implementation, the goal est to use multithread, but,
        it is not implemented yet
        """
        server = ThreadedTCPServer((HOST, PORT), ThreadedTCPRequestHandler)
        server.serve_forever()
        #server_thread = threading.Thread(target=server.serve_forever)
        #server_thread.daemon = True
        #server_thread.start()

def remoteFunction():
    """
    decorate the function, send the pickled function with the import list, kwargs and args, the Md5checksum,
    which is compared in the other side.
    wait for an answer. close and terminate.
    """
    
    def decorate(func):
        def wrapper(*args, **kwds):
            pickledfunc = dill.dumps(func)            
            try:
                HOST, USER, PASSWORD = kwds['remote'][0], kwds['remote'][1], kwds['remote'][2] 
            except:
                return func(*args, **kwds)
            PORT = random.randrange(10000, 20000)
            threads = []
            t = Process(target=start_remote, args=(HOST,USER,PASSWORD,PORT))
            t.start()
            time.sleep(2)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((HOST, PORT))
            modules_list = [itm for itm in  func.func_globals.keys() if itm.count("_")== 0 and itm != func.__name__ and itm != 'remoteFunction']
            h = hashlib.sha1()
            h.update(pickledfunc)
            hexdigestkey = h.hexdigest()
            del kwds['remote']
            lis = [pickledfunc, modules_list, args, kwds, hexdigestkey]
            lis = dill.dumps(lis)
            sock.sendall(lis)
            response = sock.recv(4096)
            response = dill.loads(response)
            return response
            sock.close()
            t.terminate()
        return wrapper
    return decorate


class ThreadedTCPRequestHandler(SocketServer.BaseRequestHandler):
    """
    the handle method process the received data,
    check the checksum,
    import all necessary modules,
    dump and send the processed answer
    """
    def handle(self):
        import sys
        data = self.request.recv(4096)
        cur_thread = threading.current_thread()
        response = "{}: {}".format(cur_thread.name, data)
        rec = dill.loads(data)
        modulesNames = rec[1]
        h = hashlib.sha1()
        h.update(rec[0])
        hexdigestkey = h.hexdigest()
        if hexdigestkey != rec[4]:
        	sys.exit(1)
        remfunc = dill.loads(rec[0])
        for mod_name in modulesNames:
            remfunc.__globals__[mod_name] = import_module(mod_name)
        try :
            res = remfunc(*rec[2], **rec[3])
        except:
            msgerr= sys.exc_info()[0]
            res_pack = dill.dumps(msgerr)
            self.request.sendall(res_pack)             
            self.server.shutdown()            
        res_pack = dill.dumps(res)
        self.request.sendall(res_pack)
        self.server.shutdown()



class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass


@remoteFunction('127.0.0.1', 'loic', '')
def toto(path):
    ret = os.listdir(path)
    return ret


if __name__ == '__main__':
	toto('.')

