import json
import struct

# Định nghĩa các hằng số phản hồi (ACK/NACK)
ACK_HANDSHAKE = "ACK_HANDSHAKE"
ACK_META = "ACK_META"
ACK_PART = "ACK_PART"
ACK_COMPLETE = "ACK_COMPLETE"

NACK_INTEGRITY = "NACK_INTEGRITY"
NACK_SIGNATURE = "NACK_SIGNATURE"
NACK_REPLAY = "NACK_REPLAY"
NACK_KEY_ERROR = "NACK_KEY_ERROR"

def send_message(sock, message):
    data = json.dumps(message).encode('utf-8')
    length = len(data)
    sock.sendall(struct.pack('!I', length) + data)

def receive_message(sock):
    try:
        raw_msg_len = sock.recv(4)
        if not raw_msg_len: return None
        msg_len = struct.unpack('!I', raw_msg_len)[0]
        
        chunks = []
        bytes_recd = 0
        while bytes_recd < msg_len:
            chunk = sock.recv(min(msg_len - bytes_recd, 4096))
            if not chunk: break
            chunks.append(chunk)
            bytes_recd += len(chunk)
        
        data = b"".join(chunks)
        return json.loads(data.decode('utf-8'))
    except Exception:
        return None
