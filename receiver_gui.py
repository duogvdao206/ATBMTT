import customtkinter as ctk
import tkinter.messagebox as messagebox
import tkinter.filedialog as filedialog
import threading
import socket
import time
import base64
import os
from config import HOST, PORT, MAX_TIME_DIFF
from crypto_utils import load_rsa_key, rsa_decrypt, rsa_verify, des3_decrypt, calculate_hash
import protocol
from logger import setup_logger

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("green")

class ReceiverGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Hệ Thống Nhận File An Toàn - Đề tài 7")
        self.geometry("850x750")

        self.logger = setup_logger('receiver_gui', 'receiver_gui.log')
        self.is_listening = False
        self.server_socket = None
        self.handshake_event = threading.Event()
        self.handshake_response = ""

        # UI Components
        self.title_lbl = ctk.CTkLabel(self, text="CHƯƠNG TRÌNH NHẬN FILE (RECEIVER)", font=ctk.CTkFont(size=20, weight="bold"), text_color="#d32f2f")
        self.title_lbl.pack(pady=10)

        # Keys Selection
        self.keys_frame = ctk.CTkFrame(self)
        self.keys_frame.pack(pady=5, fill="x", padx=20)
        
        self.priv_path = ctk.StringVar(value="receiver_private.pem")
        ctk.CTkLabel(self.keys_frame, text="Khóa Private (Receiver):").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        ctk.CTkEntry(self.keys_frame, textvariable=self.priv_path, width=300).grid(row=0, column=1, padx=5, pady=5)
        ctk.CTkButton(self.keys_frame, text="Chọn", command=lambda: self.browse_key(self.priv_path), width=60).grid(row=0, column=2, padx=5, pady=5)

        self.pub_path = ctk.StringVar(value="sender_public.pem")
        ctk.CTkLabel(self.keys_frame, text="Khóa Public (Sender):").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        ctk.CTkEntry(self.keys_frame, textvariable=self.pub_path, width=300).grid(row=1, column=1, padx=5, pady=5)
        ctk.CTkButton(self.keys_frame, text="Chọn", command=lambda: self.browse_key(self.pub_path), width=60).grid(row=1, column=2, padx=5, pady=5)

        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.pack(pady=10, padx=20, fill="x")
        
        self.listen_btn = ctk.CTkButton(self.btn_frame, text="BẬT CHẾ ĐỘ CHỜ ĐỂ NHẬN", command=self.toggle_listen, fg_color="#4caf50", hover_color="#388e3c", font=ctk.CTkFont(size=14, weight="bold"), height=40)
        self.listen_btn.pack(side="left", padx=5, expand=True, fill="x")

        self.handshake_frame = ctk.CTkFrame(self)
        self.handshake_frame.pack(pady=5, padx=20, fill="x")
        
        self.hs_resp_var = ctk.StringVar(value="Ready!")
        ctk.CTkLabel(self.handshake_frame, text="Phản hồi Bắt tay:").pack(side="left", padx=10)
        ctk.CTkEntry(self.handshake_frame, textvariable=self.hs_resp_var, width=150).pack(side="left", padx=5)
        
        self.hs_btn = ctk.CTkButton(self.handshake_frame, text="GỬI PHẢN HỒI", command=self.send_handshake_resp, state="disabled")
        self.hs_btn.pack(side="left", padx=10)

        self.status_var = ctk.StringVar(value="Trạng thái: Đang dừng")
        self.status_lbl = ctk.CTkLabel(self, textvariable=self.status_var, font=ctk.CTkFont(slant="italic"))
        self.status_lbl.pack(pady=5)

        ctk.CTkLabel(self, text="Nhật ký tương tác & Trạng thái:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=20)
        self.log_area = ctk.CTkTextbox(self, height=350, font=ctk.CTkFont(family="Consolas", size=12))
        self.log_area.pack(pady=5, padx=20, fill="both", expand=True)

    def log(self, prefix, message):
        full_msg = f"[{time.strftime('%H:%M:%S')}] [{prefix}] {message}\n"
        self.log_area.insert("end", full_msg)
        self.log_area.see("end")
        if prefix == "INFO": self.logger.info(message)
        elif prefix == "WARNING": self.logger.warning(message)
        elif prefix == "ERROR": self.logger.error(message)

    def browse_key(self, var):
        filename = filedialog.askopenfilename(filetypes=[("PEM Files", "*.pem"), ("All Files", "*.*")])
        if filename: var.set(filename)

    def enable_handshake_btn(self):
        self.hs_btn.configure(state="normal")
        
    def send_handshake_resp(self):
        self.handshake_response = self.hs_resp_var.get()
        self.hs_btn.configure(state="disabled")
        self.handshake_event.set()

    def toggle_listen(self):
        if not self.is_listening: 
            self.start_listening()
        else: 
            self.stop_listening()

    def start_listening(self):
        self.is_listening = True
        self.listen_btn.configure(text="DỪNG CHẾ ĐỘ CHỜ", fg_color="#f44336", hover_color="#d32f2f")
        self.status_var.set(f"Đang nghe tại {HOST}:{PORT}")
        threading.Thread(target=self.run_server, daemon=True).start()

    def stop_listening(self):
        self.is_listening = False
        self.listen_btn.configure(text="BẬT CHẾ ĐỘ CHỜ ĐỂ NHẬN", fg_color="#4caf50", hover_color="#388e3c")
        self.status_var.set("Trạng thái: Đang dừng")
        if self.server_socket: 
            try: self.server_socket.close()
            except: pass

    def run_server(self):
        try:
            receiver_priv = load_rsa_key(self.priv_path.get())
            sender_pub = load_rsa_key(self.pub_path.get())
        except Exception as e:
            self.log("ERROR", f"Lỗi khóa: {e}")
            self.after(0, self.stop_listening)
            return

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try: 
            self.server_socket.bind((HOST, PORT))
        except Exception: 
            return
        
        self.server_socket.listen(5)
        self.log("INFO", f"Hệ thống máy nhận đã sẵn sàng tại cổng {PORT}.")
        self.log("INFO", "Đang chờ dữ liệu từng bước từ Sender...")

        while self.is_listening:
            try:
                self.server_socket.settimeout(1.0)
                conn, addr = self.server_socket.accept()
                self.log("INFO", f"Phát hiện kết nối từ {addr}")
                # Use standard blocking mode for handler to wait for sender's steps
                conn.settimeout(None) 
                threading.Thread(target=self.handle_client, args=(conn, receiver_priv, sender_pub), daemon=True).start()
            except socket.timeout: 
                continue
            except Exception: 
                break

    def handle_client(self, conn, receiver_priv, sender_pub):
        with conn:
            try:
                # 1. Handshake
                msg = protocol.receive_message(conn)
                if not msg or msg.get("type") != "handshake": return
                
                self.log("INFO", f"Nhận được lời chào: {msg.get('msg')}")
                self.log("INFO", "Vui lòng nhập và bấm 'GỬI PHẢN HỒI' trên giao diện...")
                
                self.after(0, self.enable_handshake_btn)
                self.handshake_event.wait()
                self.handshake_event.clear()
                
                self.log("INFO", f"Đang gửi phản hồi: {self.handshake_response}")
                protocol.send_message(conn, {"type": "handshake", "msg": self.handshake_response})

                # 2. Metadata
                msg = protocol.receive_message(conn)
                if not msg or msg.get("type") != "metadata": return
                self.log("INFO", f"Nhận yêu cầu gửi file: {msg.get('filename')}")
                
                ts = msg["timestamp"]
                duration = msg.get("duration")

                if abs(time.time() - ts) > MAX_TIME_DIFF:
                    self.log("WARNING", "[SECURITY] Replay attack detected! (Timestamp expired)")
                    protocol.send_message(conn, {"status": protocol.NACK_REPLAY, "reason": "lỗi integrity (Timestamp expired)"})
                    return

                metadata_str = f"{msg['filename']}|{ts}|{duration}"
                sig = base64.b64decode(msg["sig"])
                if not rsa_verify(sender_pub, metadata_str.encode('utf-8'), sig):
                    self.log("ERROR", "[SECURITY] Chữ ký Metadata không hợp lệ!")
                    protocol.send_message(conn, {"status": protocol.NACK_SIGNATURE, "reason": "lỗi integrity (Invalid signature)"})
                    return

                # Decrypt RSA Session Key
                try:
                    enc_key = base64.b64decode(msg["enc_session_key"])
                    session_key = rsa_decrypt(receiver_priv, enc_key)
                    self.log("INFO", f"Giải mã khóa Phiên RSA thành công. Xác thực chữ ký đúng.")
                except Exception:
                    protocol.send_message(conn, {"status": protocol.NACK_KEY_ERROR, "reason": "Key decryption failed"})
                    return

                protocol.send_message(conn, {"status": protocol.ACK_META})
                self.log("INFO", "Chờ nhận các đoạn file...")

                # 3. Data Parts
                received_parts = []

                for i in range(3):
                    msg = protocol.receive_message(conn)
                    if not msg: return
                    iv = base64.b64decode(msg["iv"])
                    cipher = base64.b64decode(msg["cipher"])
                    hash_val = bytes.fromhex(msg["hash"])
                    p_sig = base64.b64decode(msg["sig"])

                    # Integrity (SHA-512)
                    if calculate_hash(iv, cipher) != hash_val:
                        self.log("ERROR", f"[SECURITY] Lỗi toàn vẹn (Hash mismatch) tại đoạn {i+1}!")
                        protocol.send_message(conn, {"status": protocol.NACK_INTEGRITY, "reason": "lỗi integrity"})
                        return

                    # Authentication (Signature)
                    if not rsa_verify(sender_pub, hash_val, p_sig):
                        self.log("ERROR", f"[SECURITY] Lỗi xác thực (Signature mismatch) tại đoạn {i+1}!")
                        protocol.send_message(conn, {"status": protocol.NACK_INTEGRITY, "reason": "lỗi integrity"})
                        return

                    # Decrypt (Triple DES)
                    pt = des3_decrypt(session_key, iv, cipher)
                    received_parts.append(pt)
                    self.log("INFO", f"Đã nhận, xác minh và giải mã thành công Đoạn {i+1}/3.")
                    protocol.send_message(conn, {"status": protocol.ACK_PART})

                # Assemble & Save
                full_data = b''.join(received_parts)
                with open("received_recording.mp3", 'wb') as f: 
                    f.write(full_data)
                
                self.log("INFO", "HOÀN TẤT: Đã ghép đủ 3 đoạn và lưu file thành công!")
                protocol.send_message(conn, {"status": protocol.ACK_COMPLETE})
                self.after(0, lambda: messagebox.showinfo("Thành công", "Đã nhận file hoàn tất!"))

            except Exception as e: 
                self.log("ERROR", f"Lỗi xử lý kết nối: {e}")

if __name__ == "__main__":
    app = ReceiverGUI()
    app.mainloop()
