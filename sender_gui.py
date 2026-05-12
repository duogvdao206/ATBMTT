import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import threading
import os
import time
import socket
import base64
from config import HOST, PORT
from crypto_utils import load_rsa_key, generate_session_key, rsa_encrypt, rsa_sign, des3_encrypt, calculate_hash
import protocol
from logger import setup_logger

class SenderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Hệ Thống Gửi File An Toàn - Đề tài 7 (Bản Chuẩn)")
        self.root.geometry("750x700")
        self.root.configure(bg="#f0f2f5")

        self.logger = setup_logger('sender_gui', 'sender_gui.log')
        self.step_event = threading.Event()

        # UI Components
        tk.Label(root, text="CHƯƠNG TRÌNH GỬI FILE (SENDER)", font=("Arial", 16, "bold"), bg="#f0f2f5", fg="#1a73e8").pack(pady=15)

        # File Selection
        self.file_path = tk.StringVar()
        file_frame = tk.Frame(root, bg="#f0f2f5")
        file_frame.pack(pady=5, fill=tk.X, padx=20)
        tk.Entry(file_frame, textvariable=self.file_path, state='readonly', font=("Arial", 10)).pack(side=tk.LEFT, expand=True, fill=tk.X)
        tk.Button(file_frame, text="Chọn File", command=self.browse_file, bg="#dadce0").pack(side=tk.RIGHT, padx=5)

        # Demo & Options
        control_frame = tk.Frame(root, bg="#f0f2f5")
        control_frame.pack(pady=5, padx=20, fill=tk.X)
        self.demo_mode = tk.BooleanVar(value=True)
        tk.Checkbutton(control_frame, text="Chế độ thuyết trình (Dừng từng bước)", variable=self.demo_mode, bg="#f0f2f5", font=("Arial", 10, "bold"), fg="#d32f2f").pack(side=tk.LEFT)

        self.tamper_var = tk.BooleanVar()
        self.replay_var = tk.BooleanVar()
        tk.Checkbutton(control_frame, text="Giả lập Tamper", variable=self.tamper_var, bg="#f0f2f5").pack(side=tk.LEFT, padx=10)
        tk.Checkbutton(control_frame, text="Giả lập Replay", variable=self.replay_var, bg="#f0f2f5").pack(side=tk.LEFT, padx=10)

        # Control Buttons
        btn_frame = tk.Frame(root, bg="#f0f2f5")
        btn_frame.pack(pady=10, padx=20, fill=tk.X)
        self.send_btn = tk.Button(btn_frame, text="BẮT ĐẦU TRUYỀN TIN", command=self.start_send_thread, bg="#1a73e8", fg="white", font=("Arial", 11, "bold"), height=2, width=20)
        self.send_btn.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        self.next_btn = tk.Button(btn_frame, text="BƯỚC TIẾP THEO >>", command=self.go_next, bg="#ff9800", fg="white", font=("Arial", 11, "bold"), height=2, state=tk.DISABLED)
        self.next_btn.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        # Log & Benchmark
        tk.Label(root, text="Nhật ký tương tác & Hiệu năng:", bg="#f0f2f5", font=("Arial", 10, "bold")).pack(anchor="w", padx=20)
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

    def browse_file(self):
        filename = filedialog.askopenfilename(); 
        if filename: self.file_path.set(filename)

    def go_next(self):
        self.step_event.set()
        self.next_btn.config(state=tk.DISABLED)

    def wait_user(self, step_name):
        if self.demo_mode.get():
            self.log("WAIT", f"Hãy nhấn 'BƯỚC TIẾP THEO' để {step_name}", "red")
            self.next_btn.config(state=tk.NORMAL)
            self.step_event.clear()
            self.step_event.wait()

    def start_send_thread(self):
        if not self.file_path.get(): messagebox.showwarning("Lỗi", "Vui lòng chọn file!"); return
        self.send_btn.config(state=tk.DISABLED)
        threading.Thread(target=self.send_file, daemon=True).start()

    def send_file(self):
        filepath = self.file_path.get()
        try:
            sender_priv = load_rsa_key('sender_private.pem')
            receiver_pub = load_rsa_key('receiver_public.pem')
        except Exception as e:
            self.log("ERROR", f"Lỗi tải khóa: {e}"); self.root.after(0, lambda: self.send_btn.config(state=tk.NORMAL)); return

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.connect((HOST, PORT))
                self.log("INFO", "Đã kết nối thành công tới máy nhận.")

                # 1. HANDSHAKE
                self.wait_user("Gửi Hello!")
                protocol.send_message(s, {"type": "handshake", "msg": "Hello!"})
                resp = protocol.receive_message(s)
                if not resp or resp.get("msg") != "Ready!":
                    self.log("ERROR", "Bắt tay thất bại!"); return
                self.log("INFO", "Handshake thành công (Hello -> Ready).", "green")

                # 2. METADATA & RSA KEY
                self.wait_user("Trao đổi Khóa RSA & Metadata")
                session_key = generate_session_key()
                session_id = os.urandom(8).hex().upper()
                self.log("INFO", f"Đã tạo Khóa phiên Triple DES: {session_key.hex().upper()}", "purple")
                
                start_rsa = time.time()
                enc_session_key = rsa_encrypt(receiver_pub, session_key)
                rsa_time = time.time() - start_rsa
                
                filename = os.path.basename(filepath)
                ts = int(time.time())
                if self.replay_var.get(): ts -= 300
                metadata_str = f"{filename}|{ts}|{session_id}"
                signature = rsa_sign(sender_priv, metadata_str.encode('utf-8'))

                protocol.send_message(s, {
                    "type": "metadata", "filename": filename, "timestamp": ts, "session_id": session_id,
                    "enc_session_key": base64.b64encode(enc_session_key).decode('utf-8'),
                    "sig": base64.b64encode(signature).decode('utf-8')
                })
                self.log("INFO", f"Đã gửi Metadata & Khóa RSA (Thời gian mã hóa RSA: {rsa_time:.4f}s)")
                
                resp = protocol.receive_message(s)
                if not resp or resp.get("status") != protocol.ACK_META:
                    self.log("ERROR", f"Máy nhận từ chối Metadata: {resp.get('reason')}", "red"); return
                self.log("INFO", "Máy nhận đã xác thực Metadata thành công.", "green")

                # 3. DATA PARTS & 3DES
                self.wait_user("Mã hóa Triple DES và gửi 3 đoạn")
                with open(filepath, 'rb') as f: file_data = f.read()
                part_size = len(file_data) // 3
                parts = [file_data[:part_size], file_data[part_size:2*part_size], file_data[2*part_size:]]

                total_enc_time = 0
                for i, part_data in enumerate(parts):
                    p_idx = i + 1
                    
                    # Benchmark Encrypt
                    start_enc = time.time()
                    iv, cipher = des3_encrypt(session_key, part_data)
                    enc_duration = time.time() - start_enc
                    total_enc_time += enc_duration

                    # Tamper Test
                    if self.tamper_var.get() and i == 1:
                        c_l = list(cipher); c_l[10] ^= 0xFF; cipher = bytes(c_l) # Sửa đúng 1 byte theo yêu cầu
                        self.log("WARNING", f"!!! ĐANG GIẢ LẬP TAMPER TẠI ĐOẠN {p_idx}")
                    
                    h_val = calculate_hash(iv, cipher)
                    pkt_ts = int(time.time())
                    sig_d = h_val + p_idx.to_bytes(4, 'big') + pkt_ts.to_bytes(8, 'big')
                    p_sig = rsa_sign(sender_priv, sig_d)

                    protocol.send_message(s, {
                        "type": "data", "part": p_idx, "session_id": session_id,
                        "iv": base64.b64encode(iv).decode('utf-8'),
                        "cipher": base64.b64encode(cipher).decode('utf-8'),
                        "hash": h_val.hex(), "sig": base64.b64encode(p_sig).decode('utf-8'),
                        "timestamp": pkt_ts, "seq": p_idx
                    })
                    self.log("INFO", f"Đoạn {p_idx}/3: Đã gửi (Time: {enc_duration:.4f}s)")
                    
                    # Chờ ACK từng phần (Yêu cầu 5)
                    resp = protocol.receive_message(s)
                    if not resp or resp.get("status") != protocol.ACK_PART:
                        self.log("ERROR", f"Lỗi tại đoạn {p_idx}: {resp.get('reason')}", "red"); return

                # HOÀN TẤT
                resp = protocol.receive_message(s)
                if resp and resp.get("status") == protocol.ACK_COMPLETE:
                    self.log("BENCHMARK", f"Tổng thời gian mã hóa Triple DES: {total_enc_time:.4f}s", "blue")
                    self.log("INFO", "TẤT CẢ HOÀN TẤT! File đã được truyền an toàn.", "green")
                    messagebox.showinfo("Thành công", "Truyền file hoàn tất!")
                else:
                    self.log("ERROR", f"Thất bại: {resp.get('reason')}", "red")

            except Exception as e:
                self.log("ERROR", f"Lỗi hệ thống: {e}", "red")
            finally:
                self.root.after(0, lambda: self.send_btn.config(state=tk.NORMAL))

if __name__ == "__main__":
    root = tk.Tk(); gui = SenderGUI(root); root.mainloop()
