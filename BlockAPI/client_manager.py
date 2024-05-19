import multiprocessing
import threading
import post_data
import socket
import struct
import pickle

"""
Manages shared resources between the API clients. 
Communicate with post processor.
"""
class ClientManager:
    post_processor_address = ("127.0.0.1", 8001)
    post_processor_bufsize = 8192
    def __init__(self):
        self.client_pipes = {} # (ukey, uid): send end of pipe
        self.client_pipes_lock = threading.Lock()
        # Create a listener for the post processor
        self.listener_thread = threading.Thread(target=lambda: self.activate_listener(), name="Post-Processor-Listener")
        self.listener_thread.start()
        self.post_proc_sock = None

    def add_client(self, ukey : str, uid : str):
        with self.client_pipes_lock:
            recv,send = multiprocessing.Pipe(duplex=False)
            self.client_pipes[(ukey, uid)] = send
            return recv

    def block_score(self, post : post_data.PostData):
        # Create a pipe to read from
        recv = self.add_client(post.metadata.ukey, post.metadata.uid)
        # Send post to post processor
        post_raw = pickle.dumps(post)
        self.post_proc_sock.sendall(struct.pack("<Q", len(post_raw)) + post_raw)
        # Wait until the pipe is filled up with the blocking result
        recv.poll(timeout=None)
        # Return pipe contents
        return pickle.loads(recv.recv())
    
    def listen_message(self, s):
        message = s.recv(ClientManager.post_processor_bufsize)
        if len(message)==0: return None
        size, = struct.unpack_from("<Q", message)
        message = message[8:]
        while len(message) < size:
            chunk = s.recv(ClientManager.post_processor_bufsize)
            if len(chunk)==0: return None
            message += chunk
        return message
    
    def activate_listener(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(ClientManager.post_processor_address)
            self.post_proc_sock = s
            message = None
            while message := self.listen_message(s):
                message = pickle.loads(message)
                with self.client_pipes_lock: # Send message to client
                    self.client_pipes[(message["user_key"], message["user_id"])].send(pickle.dumps(message["content"]))