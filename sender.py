import socket
import time
import os
import base64
import argparse
from config import HOST, PORT
from crypto_utils import load_rsa_key, generate_session_key, rsa_encrypt, rsa_sign, des3_encrypt, calculate_hash
from protocol import send_message, receive_message
from logger import setup_logger

logger = setup_logger('sender', 'sender.log')

def start_sender(filepath, tamper=False, replay=False):
    if not os.path.exists(filepath):
        print(f"File {filepath} not found!")
        return

    try:
        sender_priv = load_rsa_key('sender_private.pem')
        receiver_pub = load_rsa_key('receiver_public.pem')
    except FileNotFoundError:
        print("Keys not found. Please run generate_keys.py first.")
        return

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((HOST, PORT))
            logger.info("Connected to receiver.")

            send_message(s, {"type": "handshake", "msg": "Hello!"})
            logger.info("Sent Hello!")
            
            resp = receive_message(s)
            if not resp or resp.get("msg") != "Ready!":
                logger.error("Handshake failed.")
                return
            logger.info("Received Ready!")

            session_key = generate_session_key()
            enc_session_key = rsa_encrypt(receiver_pub, session_key)
            
            filename = os.path.basename(filepath)
            timestamp = int(time.time())
            if replay:
                timestamp -= 100
            duration = "unknown"
            
            metadata_str = f"{filename}|{timestamp}|{duration}"
            signature = rsa_sign(sender_priv, metadata_str.encode('utf-8'))

            send_message(s, {
                "type": "metadata",
                "filename": filename,
                "timestamp": timestamp,
                "duration": duration,
                "enc_session_key": base64.b64encode(enc_session_key).decode('utf-8'),
                "sig": base64.b64encode(signature).decode('utf-8')
            })
            logger.info("Sent metadata and session key.")

            resp = receive_message(s)
            if not resp or resp.get("status") != "ACK":
                logger.error(f"Metadata rejected. Reason: {resp.get('reason')}")
                print(f"Metadata rejected: {resp.get('reason')}")
                return
            
            with open(filepath, 'rb') as f:
                file_data = f.read()
            
            part_size = len(file_data) // 3
            parts = [
                file_data[:part_size],
                file_data[part_size:2*part_size],
                file_data[2*part_size:]
            ]

            seq = 1
            for i, part_data in enumerate(parts):
                part_idx = i + 1
                iv, cipher = des3_encrypt(session_key, part_data)
                
                if tamper and i == 1:
                    cipher = bytearray(cipher)
                    cipher[0] ^= 0xFF
                    cipher = bytes(cipher)

                hash_val = calculate_hash(iv, cipher)
                
                pkt_ts = int(time.time())
                sig_data = hash_val + seq.to_bytes(4, 'big') + pkt_ts.to_bytes(8, 'big')
                packet_sig = rsa_sign(sender_priv, sig_data)

                packet = {
                    "type": "data",
                    "part": part_idx,
                    "iv": base64.b64encode(iv).decode('utf-8'),
                    "cipher": base64.b64encode(cipher).decode('utf-8'),
                    "hash": base64.b64encode(hash_val).decode('utf-8'),
                    "sig": base64.b64encode(packet_sig).decode('utf-8'),
                    "timestamp": pkt_ts,
                    "seq": seq
                }
                
                send_message(s, packet)
                logger.info(f"Sent part {part_idx}")
                seq += 1

            resp = receive_message(s)
            if resp and resp.get("status") == "ACK":
                logger.info("File transfer successful! Received final ACK.")
                print("Transfer completed successfully.")
            else:
                logger.error(f"Transfer failed. Received: {resp}")
                print(f"Transfer failed. Reason: {resp.get('reason')}")

        except Exception as e:
            logger.error(f"Sender error: {e}")
            print(f"Sender error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Secure File Sender")
    parser.add_argument('--file', type=str, default='recording.mp3', help='File to send')
    parser.add_argument('--tamper', action='store_true', help='Tamper data to test integrity check')
    parser.add_argument('--replay', action='store_true', help='Use expired timestamp to test anti-replay')
    args = parser.parse_args()

    start_sender(args.file, args.tamper, args.replay)
