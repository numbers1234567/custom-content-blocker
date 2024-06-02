# Handles post processing requests from a single client. 
# Usage: python post_prc.py --address [ADDR]
from PIL import Image

import io
import socket
import post_data
import struct
import pickle
import classifier

import argparse

parser = argparse.ArgumentParser(description="Process social media posts using ML.")
parser.add_argument("--address", dest="ADDR", default="127.0.0.1", help="Address of post processor")
parser.add_argument("--port", dest="PORT", default=8001, help="Port of post processor")
parser.add_argument("--net_bufsize", dest="BUFSIZE", default=8192, help="Buffer size (in bytes) for receiving network messages.")
args = parser.parse_args()

ADDRESS = (args.ADDR, args.PORT)
bufsize = args.BUFSIZE

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