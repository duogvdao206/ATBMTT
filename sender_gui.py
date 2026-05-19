import customtkinter as ctk
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox
import threading
import os
import time
import socket
import base64
from config import HOST, PORT, EAVESDROPPER_PORT
from crypto_utils import load_rsa_key, generate_session_key, rsa_encrypt, rsa_sign, des3_encrypt, calculate_hash
import protocol
from logger import setup_logger

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class SenderGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Hệ Thống Gửi File An Toàn - Đề tài 7")
        self.geometry("850x750")

        self.logger = setup_logger('sender_gui', 'sender_gui.log')
        
        self.step = 0
        self.s = None
        self.session_key = None
        self.parts = []
        self.sender_priv = None
        self.receiver_pub = None

        # UI Components
        self.title_lbl = ctk.CTkLabel(self, text="CHƯƠNG TRÌNH GỬI FILE (SENDER) - TỪNG BƯỚC", font=ctk.CTkFont(size=20, weight="bold"), text_color="#1a73e8")
        self.title_lbl.pack(pady=10)

        # Keys Selection
        self.keys_frame = ctk.CTkFrame(self)
        self.keys_frame.pack(pady=5, fill="x", padx=20)
        
        self.priv_path = ctk.StringVar(value="sender_private.pem")
        ctk.CTkLabel(self.keys_frame, text="Khóa Private (Sender):").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        ctk.CTkEntry(self.keys_frame, textvariable=self.priv_path, width=300).grid(row=0, column=1, padx=5, pady=5)
        ctk.CTkButton(self.keys_frame, text="Chọn", command=lambda: self.browse_key(self.priv_path), width=60).grid(row=0, column=2, padx=5, pady=5)

        self.pub_path = ctk.StringVar(value="receiver_public.pem")
        ctk.CTkLabel(self.keys_frame, text="Khóa Public (Receiver):").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        ctk.CTkEntry(self.keys_frame, textvariable=self.pub_path, width=300).grid(row=1, column=1, padx=5, pady=5)
        ctk.CTkButton(self.keys_frame, text="Chọn", command=lambda: self.browse_key(self.pub_path), width=60).grid(row=1, column=2, padx=5, pady=5)

        # File Selection
        self.file_path = ctk.StringVar()
        self.file_frame = ctk.CTkFrame(self)
        self.file_frame.pack(pady=5, fill="x", padx=20)
        
        self.file_entry = ctk.CTkEntry(self.file_frame, textvariable=self.file_path, font=ctk.CTkFont(size=12), state='readonly')
        self.file_entry.pack(side="left", expand=True, fill="x", padx=(10, 5), pady=10)
        self.browse_btn = ctk.CTkButton(self.file_frame, text="Chọn File Audio", command=self.browse_file, width=120)
        self.browse_btn.pack(side="right", padx=(5, 10), pady=10)

        # Destination Selection
        self.dest_frame = ctk.CTkFrame(self)
        self.dest_frame.pack(pady=5, padx=20, fill="x")
        
        ctk.CTkLabel(self.dest_frame, text="Kết nối đến:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10, pady=5)
        self.dest_var = ctk.IntVar(value=PORT)
        ctk.CTkRadioButton(self.dest_frame, text="Máy Nhận (Bình thường)", variable=self.dest_var, value=PORT).pack(side="left", padx=10, pady=5)
        ctk.CTkRadioButton(self.dest_frame, text="Kẻ Nghe Lén (Đi qua Proxy của Hacker)", variable=self.dest_var, value=EAVESDROPPER_PORT).pack(side="left", padx=10, pady=5)

        # Handshake Input
        self.hs_frame = ctk.CTkFrame(self)
        self.hs_frame.pack(pady=5, padx=20, fill="x")
        
        self.hs_msg_var = ctk.StringVar(value="Hello!")
        ctk.CTkLabel(self.hs_frame, text="Lời chào Bắt tay:").pack(side="left", padx=10)
        ctk.CTkEntry(self.hs_frame, textvariable=self.hs_msg_var, width=150).pack(side="left", padx=5)

        # Control Buttons
        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.pack(pady=10, padx=20, fill="x")
        
        self.next_btn = ctk.CTkButton(self.btn_frame, text="BƯỚC 1: KẾT NỐI & BẮT TAY", command=self.do_next_step, font=ctk.CTkFont(size=14, weight="bold"), height=40)
        self.next_btn.pack(side="left", padx=5, expand=True, fill="x")
        
        self.reset_btn = ctk.CTkButton(self.btn_frame, text="LÀM LẠI", command=self.reset_state, font=ctk.CTkFont(size=14, weight="bold"), height=40, fg_color="#f44336", hover_color="#d32f2f")
        self.reset_btn.pack(side="right", padx=5)

        # Log
        ctk.CTkLabel(self, text="Nhật ký tương tác:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=20)
        self.log_area = ctk.CTkTextbox(self, height=250, font=ctk.CTkFont(family="Consolas", size=12))
        self.log_area.pack(pady=5, padx=20, fill="both", expand=True)

    def log(self, prefix, message):
        full_msg = f"[{time.strftime('%H:%M:%S')}] [{prefix}] {message}\n"
        self.log_area.insert("end", full_msg)
        self.log_area.see("end")
        if prefix == "INFO": self.logger.info(message)
        elif prefix == "WARNING": self.logger.warning(message)
        elif prefix == "ERROR": self.logger.error(message)

    def browse_file(self):
        filename = filedialog.askopenfilename()
        if filename: 
            self.file_path.set(filename)
            self.file_entry.configure(state="normal")
            self.file_entry.delete(0, "end")
            self.file_entry.insert(0, filename)
            self.file_entry.configure(state="readonly")
            
    def browse_key(self, var):
        filename = filedialog.askopenfilename(filetypes=[("PEM Files", "*.pem"), ("All Files", "*.*")])
        if filename: var.set(filename)

    def reset_state(self):
        self.step = 0
        if self.s:
            try: self.s.close()
            except: pass
            self.s = None
        self.session_key = None
        self.parts = []
        self.next_btn.configure(text="BƯỚC 1: KẾT NỐI & BẮT TAY", state="normal")
        self.log("INFO", "Đã reset trạng thái.")

    def do_next_step(self):
        self.next_btn.configure(state="disabled")
        if self.step == 0:
            threading.Thread(target=self.step_handshake, daemon=True).start()
        elif self.step == 1:
            threading.Thread(target=self.step_metadata, daemon=True).start()
        elif self.step == 2:
            threading.Thread(target=self.step_send_part, args=(1,), daemon=True).start()
        elif self.step == 3:
            threading.Thread(target=self.step_send_part, args=(2,), daemon=True).start()
        elif self.step == 4:
            threading.Thread(target=self.step_send_part, args=(3,), daemon=True).start()

    def update_btn(self, text):
        self.after(0, lambda: self.next_btn.configure(text=text, state="normal"))

    def error_state(self):
        self.after(0, lambda: self.next_btn.configure(text="LỖI - HÃY LÀM LẠI", state="disabled"))

    def step_handshake(self):
        if not self.file_path.get():
            self.after(0, lambda: messagebox.showwarning("Lỗi", "Vui lòng chọn file!"))
            self.update_btn("BƯỚC 1: KẾT NỐI & BẮT TAY")
            return
            
        try:
            self.sender_priv = load_rsa_key(self.priv_path.get())
            self.receiver_pub = load_rsa_key(self.pub_path.get())
        except Exception as e:
            self.log("ERROR", f"Lỗi tải khóa: {e}")
            self.update_btn("BƯỚC 1: KẾT NỐI & BẮT TAY")
            return

        target_port = self.dest_var.get()
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.log("INFO", f"Đang kết nối tới cổng {target_port}...")
            self.s.connect((HOST, target_port))
            
            hs_msg = self.hs_msg_var.get()
            self.log("INFO", f"Đang gửi '{hs_msg}' để bắt tay...")
            protocol.send_message(self.s, {"type": "handshake", "msg": hs_msg})
            resp = protocol.receive_message(self.s)
            
            if not resp or resp.get("msg") != "Ready!":
                self.log("ERROR", f"Bắt tay thất bại! Phản hồi nhận được: {resp.get('msg') if resp else 'None'}")
                self.error_state()
                return
                
            self.log("INFO", f"Handshake thành công (Nhận được {resp.get('msg')}).")
            self.step = 1
            self.update_btn("BƯỚC 2: TẠO KHÓA PHIÊN & GỬI METADATA")
        except Exception as e:
            self.log("ERROR", f"Lỗi: {e}")
            self.error_state()

    def step_metadata(self):
        try:
            self.log("INFO", "Tạo Khóa Phiên (3DES) & Đóng gói Metadata...")
            self.session_key = generate_session_key()
            enc_session_key = rsa_encrypt(self.receiver_pub, self.session_key)
            
            filepath = self.file_path.get()
            filename = os.path.basename(filepath)
            ts = int(time.time())
            duration = 180
            
            metadata_str = f"{filename}|{ts}|{duration}"
            signature = rsa_sign(self.sender_priv, metadata_str.encode('utf-8'))

            protocol.send_message(self.s, {
                "type": "metadata", "filename": filename, "timestamp": ts, "duration": duration,
                "enc_session_key": base64.b64encode(enc_session_key).decode('utf-8'),
                "sig": base64.b64encode(signature).decode('utf-8')
            })
            self.log("INFO", "Đã gửi Metadata & Khóa Phiên (Mã hóa bằng RSA Public Key).")
            
            resp = protocol.receive_message(self.s)
            if not resp or resp.get("status") != protocol.ACK_META:
                self.log("ERROR", f"Máy nhận từ chối Metadata: {resp.get('reason')}")
                self.error_state()
                return
                
            self.log("INFO", "Máy nhận đã xác thực Metadata thành công.")
            
            # Chia file thành 3 phần luôn để chuẩn bị
            with open(filepath, 'rb') as f: file_data = f.read()
            part_size = len(file_data) // 3
            self.parts = [file_data[:part_size], file_data[part_size:2*part_size], file_data[2*part_size:]]
            
            self.step = 2
            self.update_btn("BƯỚC 3: MÃ HÓA & GỬI ĐOẠN 1/3")
        except Exception as e:
            self.log("ERROR", f"Lỗi: {e}")
            self.error_state()

    def step_send_part(self, p_idx):
        try:
            part_data = self.parts[p_idx - 1]
            self.log("INFO", f"Đang mã hóa 3DES và ký số đoạn {p_idx}...")
            
            iv, cipher = des3_encrypt(self.session_key, part_data)
            h_val = calculate_hash(iv, cipher)
            p_sig = rsa_sign(self.sender_priv, h_val)

            protocol.send_message(self.s, {
                "type": "data", "part": p_idx, "iv": base64.b64encode(iv).decode('utf-8'),
                "cipher": base64.b64encode(cipher).decode('utf-8'),
                "hash": h_val.hex(), "sig": base64.b64encode(p_sig).decode('utf-8')
            })
            self.log("INFO", f"Đã gửi Đoạn {p_idx}/3.")
            
            resp = protocol.receive_message(self.s)
            if not resp or resp.get("status") != protocol.ACK_PART:
                self.log("ERROR", f"Lỗi tại đoạn {p_idx}: {resp.get('reason')}")
                self.error_state()
                return
                
            self.log("INFO", f"Máy nhận phản hồi thành công (ACK) đoạn {p_idx}.")
            
            if p_idx == 1:
                self.step = 3
                self.update_btn("BƯỚC 4: MÃ HÓA & GỬI ĐOẠN 2/3")
            elif p_idx == 2:
                self.step = 4
                self.update_btn("BƯỚC 5: MÃ HÓA & GỬI ĐOẠN 3/3")
            elif p_idx == 3:
                # Chờ hoàn tất
                resp = protocol.receive_message(self.s)
                if resp and resp.get("status") == protocol.ACK_COMPLETE:
                    self.log("INFO", "TẤT CẢ HOÀN TẤT! File đã được truyền an toàn.")
                    self.after(0, lambda: messagebox.showinfo("Thành công", "Truyền file hoàn tất!"))
                    self.after(0, lambda: self.next_btn.configure(text="HOÀN THÀNH", state="disabled"))
                else:
                    self.log("ERROR", f"Thất bại hoàn tất: {resp.get('reason')}")
                    self.error_state()
        except Exception as e:
            self.log("ERROR", f"Lỗi: {e}")
            self.error_state()

if __name__ == "__main__":
    app = SenderGUI()
    app.mainloop()
