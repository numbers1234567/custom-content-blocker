# Handles post processing requests from a single client
from PIL import Image

import io
import socket
import post_data
import struct
import pickle
import classifier

ADDRESS = ("127.0.0.1", 8001)
bufsize = 8192

def process_post(post : post_data.PostData):
    return 0.5

def listen_message(s : socket.socket):
    message = s.recv(bufsize)
    if len(message)==0: return None
    size, = struct.unpack_from("<Q", message)
    message = message[8:]
    while len(message) < size:
        chunk = s.recv(bufsize)
        if len(chunk)==0: return None
        message += chunk

    return message

def deserialize_post(post_raw : bytes) -> post_data.PostData:
    return pickle.loads(post_raw)

print("Loading Classifier")
cls = classifier.BLIPClassifier()

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    print("Starting server")
    s.bind(ADDRESS)
    print(f"Bind to port {ADDRESS}")
    s.listen()
    print("Accepting Connections")
    conn, addr = s.accept()
    print(f"Connected by {addr}")
    with conn:
        message = None
        while message := listen_message(conn):
            post = deserialize_post(message)
            image = Image.new('RGB', (1000, 1000))
            has_image=False
            if len(post.media.images) > 0:
                image_raw = post.media.images[-1].content
                image = Image.open(io.BytesIO(image_raw)).convert("RGB")
                has_image=True
            elif len(post.media.video) > 0:
                image_raw = post.media.video[-1].content
                image = Image.open(io.BytesIO(image_raw)).convert("RGB")
                has_image=True
            response = {"user_key" : post.metadata.ukey, 
                        "user_id" : post.metadata.uid, 
                        "content" : cls(image=image, text=post.media.text, has_image=has_image)}
            raw = pickle.dumps(response)
            conn.sendall(struct.pack("<Q", len(raw)) + raw)