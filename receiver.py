import socket
import time
import base64
from config import HOST, PORT, MAX_TIME_DIFF
from crypto_utils import load_rsa_key, rsa_decrypt, rsa_verify, des3_decrypt, calculate_hash
from protocol import send_message, receive_message
from logger import setup_logger

logger = setup_logger('receiver', 'receiver.log')

def start_receiver():
    try:
        receiver_priv = load_rsa_key('receiver_private.pem')
        sender_pub = load_rsa_key('sender_public.pem')
    except FileNotFoundError:
        print("Keys not found. Please run generate_keys.py first.")
        return

    seen_seqs = set()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"Listening on {HOST}:{PORT}")
        logger.info("Receiver started.")

        conn, addr = s.accept()
        with conn:
            logger.info(f"Connected by {addr}")
            
            msg = receive_message(conn)
            if not msg or msg.get("type") != "handshake" or msg.get("msg") != "Hello!":
                logger.error("Invalid handshake.")
                return
            
            logger.info("Received Hello! Sending Ready!")
            send_message(conn, {"type": "handshake", "msg": "Ready!"})

            msg = receive_message(conn)
            if not msg or msg.get("type") != "metadata":
                logger.error("Expected metadata.")
                return
            
            filename = msg["filename"]
            ts = msg["timestamp"]
            duration = msg["duration"]
            
            if abs(time.time() - ts) > MAX_TIME_DIFF:
                logger.error("Metadata timestamp expired.")
                send_message(conn, {"status": "NACK", "reason": "Timestamp expired"})
                return

            metadata_str = f"{filename}|{ts}|{duration}"
            sig = base64.b64decode(msg["sig"])
            
            if not rsa_verify(sender_pub, metadata_str.encode('utf-8'), sig):
                logger.error("Metadata signature invalid.")
                send_message(conn, {"status": "NACK", "reason": "Invalid signature"})
                return

            try:
                enc_session_key = base64.b64decode(msg["enc_session_key"])
                session_key = rsa_decrypt(receiver_priv, enc_session_key)
            except Exception as e:
                logger.error("Failed to decrypt session key.")
                send_message(conn, {"status": "NACK", "reason": "Session key decryption failed"})
                return

            logger.info("Metadata and session key verified.")
            send_message(conn, {"status": "ACK"})

            received_parts = []
            expected_seq = 1
            
            for i in range(3):
                msg = receive_message(conn)
                if not msg or msg.get("type") != "data":
                    logger.error("Expected data packet.")
                    send_message(conn, {"status": "NACK", "reason": "Expected data packet"})
                    return
                
                part = msg["part"]
                iv = base64.b64decode(msg["iv"])
                cipher = base64.b64decode(msg["cipher"])
                hash_val = base64.b64decode(msg["hash"])
                packet_sig = base64.b64decode(msg["sig"])
                packet_ts = msg["timestamp"]
                seq = msg["seq"]

                if abs(time.time() - packet_ts) > MAX_TIME_DIFF:
                    logger.error("Packet timestamp expired.")
                    send_message(conn, {"status": "NACK", "reason": "Packet timestamp expired"})
                    return
                
                if seq in seen_seqs or seq != expected_seq:
                    logger.error("Replay attack detected or wrong sequence.")
                    send_message(conn, {"status": "NACK", "reason": "Replay detected or wrong sequence"})
                    return
                seen_seqs.add(seq)
                expected_seq += 1

                calc_hash = calculate_hash(iv, cipher)
                if calc_hash != hash_val:
                    logger.error(f"Hash mismatch for part {part}")
                    send_message(conn, {"status": "NACK", "reason": f"Hash mismatch for part {part}"})
                    return

                sig_data = hash_val + seq.to_bytes(4, 'big') + packet_ts.to_bytes(8, 'big')
                if not rsa_verify(sender_pub, sig_data, packet_sig):
                    logger.error(f"Signature mismatch for part {part}")
                    send_message(conn, {"status": "NACK", "reason": f"Signature mismatch for part {part}"})
                    return

                try:
                    pt = des3_decrypt(session_key, iv, cipher)
                    received_parts.append((part, pt))
                    logger.info(f"Verified and decrypted part {part}")
                except Exception as e:
                    logger.error(f"Decryption failed for part {part}")
                    send_message(conn, {"status": "NACK", "reason": f"Decryption failed for part {part}"})
                    return

            received_parts.sort(key=lambda x: x[0])
            full_data = b''.join([p[1] for p in received_parts])
            
            output_filename = "received_" + filename
            with open(output_filename, 'wb') as f:
                f.write(full_data)
            
            logger.info(f"File assembled and saved to {output_filename}")
            send_message(conn, {"status": "ACK", "reason": "File received successfully"})
            print(f"Successfully received and saved {output_filename}")

if __name__ == "__main__":
    start_receiver()
