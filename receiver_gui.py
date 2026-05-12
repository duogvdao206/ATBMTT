import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading
import socket
import time
import base64
import os
from config import HOST, PORT, MAX_TIME_DIFF
from crypto_utils import load_rsa_key, rsa_decrypt, rsa_verify, des3_decrypt, calculate_hash
import protocol
from logger import setup_logger

class ReceiverGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Hệ Thống Nhận File An Toàn - Đề tài 7 (Bản Chuẩn)")
        self.root.geometry("750x700")
        self.root.configure(bg="#f0f2f5")

        self.logger = setup_logger('receiver_gui', 'receiver_gui.log')
        self.is_listening = False
        self.server_socket = None
        self.step_event = threading.Event()

        # UI Components
        tk.Label(root, text="CHƯƠNG TRÌNH NHẬN FILE (RECEIVER)", font=("Arial", 16, "bold"), bg="#f0f2f5", fg="#d32f2f").pack(pady=15)

        control_frame = tk.Frame(root, bg="#f0f2f5")
        control_frame.pack(pady=5, padx=20, fill=tk.X)
        self.demo_mode = tk.BooleanVar(value=True)
        tk.Checkbutton(control_frame, text="Chế độ thuyết trình (Xác nhận thủ công)", variable=self.demo_mode, bg="#f0f2f5", font=("Arial", 10, "bold"), fg="#1b5e20").pack(side=tk.LEFT)

        btn_frame = tk.Frame(root, bg="#f0f2f5")
        btn_frame.pack(pady=10, padx=20, fill=tk.X)
        self.listen_btn = tk.Button(btn_frame, text="BẬT CHẾ ĐỘ CHỜ", command=self.toggle_listen, bg="#4caf50", fg="white", font=("Arial", 11, "bold"), height=2, width=20)
        self.listen_btn.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        self.confirm_btn = tk.Button(btn_frame, text="XÁC NHẬN BƯỚC >>", command=self.confirm_step, bg="#2196f3", fg="white", font=("Arial", 11, "bold"), height=2, state=tk.DISABLED)
        self.confirm_btn.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        self.status_var = tk.StringVar(value="Trạng thái: Đang dừng")
        tk.Label(root, textvariable=self.status_var, font=("Arial", 10, "italic"), bg="#f0f2f5").pack(pady=5)

        self.log_area = scrolledtext.ScrolledText(root, height=18, font=("Consolas", 10))
        self.log_area.pack(pady=5, padx=20, fill=tk.BOTH, expand=True)

    def log(self, prefix, message, color="black"):
        tag = f"tag_{time.time()}"
        self.log_area.tag_config(tag, foreground=color)
        full_msg = f"[{time.strftime('%H:%M:%S')}] [{prefix}] {message}"
        self.log_area.insert(tk.END, full_msg + "\n", tag)
        self.log_area.see(tk.END)
        if prefix == "INFO": self.logger.info(message)
        elif prefix == "WARNING": self.logger.warning(message)
        elif prefix == "ERROR": self.logger.error(message)

    def confirm_step(self):
        self.step_event.set()
        self.confirm_btn.config(state=tk.DISABLED)

    def wait_user(self, prompt):
        if self.demo_mode.get():
            self.log("WAIT", f"Chờ xác nhận: {prompt}", "red")
            self.confirm_btn.config(state=tk.NORMAL)
            self.step_event.clear()
            self.step_event.wait()

    def toggle_listen(self):
        if not self.is_listening: self.start_listening()
        else: self.stop_listening()

    def start_listening(self):
        self.is_listening = True
        self.listen_btn.config(text="DỪNG CHẾ ĐỘ CHỜ", bg="#f44336")
        self.status_var.set(f"Đang nghe tại {HOST}:{PORT}")
        threading.Thread(target=self.run_server, daemon=True).start()

    def stop_listening(self):
        self.is_listening = False
        self.listen_btn.config(text="BẬT CHẾ ĐỘ CHỜ", bg="#4caf50")
        self.status_var.set("Trạng thái: Đang dừng")
        if self.server_socket: self.server_socket.close()

    def run_server(self):
        try:
            receiver_priv = load_rsa_key('receiver_private.pem')
            sender_pub = load_rsa_key('sender_public.pem')
        except Exception as e:
            self.log("ERROR", f"Lỗi khóa: {e}"); self.root.after(0, self.stop_listening); return

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try: self.server_socket.bind((HOST, PORT))
        except Exception: return
        self.server_socket.listen(5)
        self.log("INFO", "Hệ thống máy nhận đã sẵn sàng.")

        while self.is_listening:
            try:
                self.server_socket.settimeout(1.0)
                conn, addr = self.server_socket.accept()
                self.log("INFO", f"Phát hiện kết nối từ {addr}", "blue")
                threading.Thread(target=self.handle_client, args=(conn, receiver_priv, sender_pub), daemon=True).start()
            except socket.timeout: continue
            except Exception: break

    def handle_client(self, conn, receiver_priv, sender_pub):
        with conn:
            try:
                # 1. Handshake
                msg = protocol.receive_message(conn)
                if not msg or msg.get("type") != "handshake": return
                self.wait_user("Phản hồi 'Ready!' để bắt tay?")
                protocol.send_message(conn, {"type": "handshake", "msg": "Ready!"})
                self.log("INFO", "Handshake thành công.", "green")

                # 2. Metadata
                msg = protocol.receive_message(conn)
                if not msg or msg.get("type") != "metadata": return
                current_session_id = msg.get("session_id")
                self.log("INFO", f"Nhận yêu cầu: {msg.get('filename')} (ID: {current_session_id})")
                self.wait_user("Xác thực Metadata?")
                
                ts = msg["timestamp"]
                if abs(time.time() - ts) > MAX_TIME_DIFF:
                    self.log("WARNING", "[SECURITY] Replay attack detected! (Timestamp expired)", "red")
                    protocol.send_message(conn, {"status": protocol.NACK_REPLAY, "reason": "lỗi integrity (Timestamp expired)"})
                    return

                metadata_str = f"{msg['filename']}|{ts}|{current_session_id}"
                sig = base64.b64decode(msg["sig"])
                if not rsa_verify(sender_pub, metadata_str.encode('utf-8'), sig):
                    self.log("ERROR", "[SECURITY] Chữ ký Metadata không hợp lệ!", "red")
                    protocol.send_message(conn, {"status": protocol.NACK_SIGNATURE, "reason": "lỗi integrity (Invalid signature)"})
                    return

                # Decrypt RSA Session Key
                start_rsa = time.time()
                try:
                    enc_key = base64.b64decode(msg["enc_session_key"])
                    session_key = rsa_decrypt(receiver_priv, enc_key)
                    rsa_time = time.time() - start_rsa
                    self.log("INFO", f"Giải mã khóa RSA thành công ({rsa_time:.4f}s). Khóa: {session_key.hex().upper()}", "purple")
                except Exception:
                    protocol.send_message(conn, {"status": protocol.NACK_KEY_ERROR, "reason": "Key decryption failed"}); return

                protocol.send_message(conn, {"status": protocol.ACK_META})

                # 3. Data Parts
                self.wait_user("Bắt đầu nhận 3 đoạn dữ liệu?")
                received_parts = []
                seen_seqs = set()
                total_dec_time = 0

                for i in range(3):
                    msg = protocol.receive_message(conn)
                    if not msg: return
                    p = msg["part"]
                    msg_sid = msg.get("session_id")
                    iv = base64.b64decode(msg["iv"])
                    cipher = base64.b64decode(msg["cipher"])
                    hash_val = bytes.fromhex(msg["hash"])
                    p_sig = base64.b64decode(msg["sig"])
                    p_ts = msg["timestamp"]
                    seq = msg["seq"]

                    # Anti-Replay
                    if msg_sid != current_session_id or seq in seen_seqs or abs(time.time() - p_ts) > MAX_TIME_DIFF:
                        self.log("WARNING", f"[SECURITY] Replay detected tại đoạn {p}!", "red")
                        protocol.send_message(conn, {"status": protocol.NACK_REPLAY, "reason": "lỗi integrity (Replay)"})
                        return
                    seen_seqs.add(seq)

                    # Integrity (SHA-512)
                    if calculate_hash(iv, cipher) != hash_val:
                        self.log("ERROR", f"[SECURITY] Lỗi toàn vẹn (Hash mismatch) tại đoạn {p}!", "red")
                        protocol.send_message(conn, {"status": protocol.NACK_INTEGRITY, "reason": "lỗi integrity"})
                        return

                    # Authentication (Signature)
                    sig_d = hash_val + seq.to_bytes(4, 'big') + p_ts.to_bytes(8, 'big')
                    if not rsa_verify(sender_pub, sig_d, p_sig):
                        self.log("ERROR", f"[SECURITY] Lỗi xác thực (Signature mismatch) tại đoạn {p}!", "red")
                        protocol.send_message(conn, {"status": protocol.NACK_SIGNATURE, "reason": "lỗi integrity"})
                        return

                    # Decrypt (Triple DES) & Benchmark
                    start_dec = time.time()
                    pt = des3_decrypt(session_key, iv, cipher)
                    dec_duration = time.time() - start_dec
                    total_dec_time += dec_duration
                    
                    received_parts.append((p, pt))
                    self.log("INFO", f"Đoạn {p}/3: Đã giải mã thành công (Time: {dec_duration:.4f}s)", "green")
                    protocol.send_message(conn, {"status": protocol.ACK_PART})

                # Assemble & Save
                received_parts.sort(key=lambda x: x[0])
                full_data = b''.join([p[1] for p in received_parts])
                with open("received_recording.mp3", 'wb') as f: f.write(full_data)
                
                self.log("BENCHMARK", f"Tổng thời gian giải mã Triple DES: {total_dec_time:.4f}s", "blue")
                self.log("INFO", "HOÀN TẤT: Đã nhận và ghép file thành công!", "blue")
                protocol.send_message(conn, {"status": protocol.ACK_COMPLETE})
                messagebox.showinfo("Thành công", "Đã nhận file hoàn tất!")

            except Exception as e: self.log("ERROR", f"Lỗi: {e}", "red")

if __name__ == "__main__":
    root = tk.Tk(); gui = ReceiverGUI(root); root.mainloop()
