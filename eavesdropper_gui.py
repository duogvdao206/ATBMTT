import customtkinter as ctk
import threading
import socket
import time
from config import HOST, PORT, EAVESDROPPER_PORT
import protocol
from logger import setup_logger

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

class EavesdropperGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Kẻ Nghe Lén (Eavesdropper) - MITM Proxy")
        self.geometry("850x650")

        self.logger = setup_logger('eavesdropper_gui', 'eavesdropper_gui.log')
        self.is_listening = False
        self.server_socket = None

        # UI Components
        self.title_lbl = ctk.CTkLabel(self, text="⚠️ GIAO DIỆN KẺ NGHE LÉN (ATTACKER) ⚠️", font=ctk.CTkFont(size=20, weight="bold"), text_color="#ff1744")
        self.title_lbl.pack(pady=15)

        # Thêm lựa chọn hành động
        self.attack_frame = ctk.CTkFrame(self)
        self.attack_frame.pack(pady=5, padx=20, fill="x")

        ctk.CTkLabel(self.attack_frame, text="Hành động tấn công:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10, pady=5)
        self.attack_mode = ctk.StringVar(value="listen")
        
        self.radio_listen = ctk.CTkRadioButton(self.attack_frame, text="Chỉ Nghe Lén (Cố tình giải mã)", variable=self.attack_mode, value="listen")
        self.radio_listen.pack(side="left", padx=10, pady=5)
        
        self.radio_modify = ctk.CTkRadioButton(self.attack_frame, text="Chỉnh Sửa Dữ Liệu (Phá hoại)", variable=self.attack_mode, value="modify")
        self.radio_modify.pack(side="left", padx=10, pady=5)

        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.pack(pady=10, padx=20, fill="x")
        
        self.listen_btn = ctk.CTkButton(self.btn_frame, text="BẮT ĐẦU NGHE LÉN (Chạy Proxy)", command=self.toggle_listen, fg_color="#d50000", hover_color="#b71c1c", font=ctk.CTkFont(size=14, weight="bold"), height=40)
        self.listen_btn.pack(side="left", padx=5, expand=True, fill="x")
        
        self.status_var = ctk.StringVar(value="Trạng thái: Chưa hoạt động")
        self.status_lbl = ctk.CTkLabel(self, textvariable=self.status_var, font=ctk.CTkFont(slant="italic"), text_color="#ff5252")
        self.status_lbl.pack(pady=5)

        ctk.CTkLabel(self, text="Dữ liệu đánh cắp được (Raw Data):", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=20)
        self.log_area = ctk.CTkTextbox(self, height=450, font=ctk.CTkFont(family="Consolas", size=12), text_color="#00e676", fg_color="#1a1a1a")
        self.log_area.pack(pady=5, padx=20, fill="both", expand=True)

    def log(self, prefix, message):
        full_msg = f"[{time.strftime('%H:%M:%S')}] [{prefix}] {message}\n"
        self.log_area.insert("end", full_msg)
        self.log_area.see("end")
        if prefix == "INFO": self.logger.info(message)
        elif prefix == "WARNING": self.logger.warning(message)
        elif prefix == "ERROR": self.logger.error(message)

    def toggle_listen(self):
        if not self.is_listening: 
            self.start_listening()
        else: 
            self.stop_listening()

    def start_listening(self):
        self.is_listening = True
        self.listen_btn.configure(text="DỪNG NGHE LÉN", fg_color="#424242", hover_color="#212121")
        self.status_var.set(f"Đang nghe lén tại cổng {EAVESDROPPER_PORT}...")
        threading.Thread(target=self.run_server, daemon=True).start()

    def stop_listening(self):
        self.is_listening = False
        self.listen_btn.configure(text="BẮT ĐẦU NGHE LÉN (Chạy Proxy)", fg_color="#d50000", hover_color="#b71c1c")
        self.status_var.set("Trạng thái: Đã dừng")
        if self.server_socket: 
            self.server_socket.close()

    def run_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try: 
            self.server_socket.bind((HOST, EAVESDROPPER_PORT))
        except Exception as e: 
            self.log("ERROR", f"Không thể bind cổng {EAVESDROPPER_PORT}: {e}")
            return
        
        self.server_socket.listen(5)
        self.log("INFO", f"Proxy trung gian đã mở tại cổng {EAVESDROPPER_PORT}.")

        while self.is_listening:
            try:
                self.server_socket.settimeout(1.0)
                client_conn, addr = self.server_socket.accept()
                self.log("WARNING", f"Phát hiện Sender kết nối từ {addr}!")
                threading.Thread(target=self.handle_mitm, args=(client_conn,), daemon=True).start()
            except socket.timeout: 
                continue
            except Exception: 
                break

    def handle_mitm(self, client_conn):
        server_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            # Kẻ nghe lén lập tức kết nối đến Máy nhận thật
            server_conn.connect((HOST, PORT))
            self.log("INFO", f"Kẻ nghe lén đã kết nối lén tới Receiver tại cổng {PORT}.")
        except Exception:
            self.log("ERROR", "Máy nhận thật (Receiver) chưa bật, không thể làm trung gian proxy!")
            client_conn.close()
            return

        # Luồng 1: Forward từ Sender sang Receiver
        def forward_s2r():
            try:
                while True:
                    msg = protocol.receive_message(client_conn)
                    if not msg: break
                    
                    mtype = msg.get("type", "Unknown")
                    self.log("WARNING", f"[Bắt gói tin Sender -> Receiver] Loại: {mtype}")
                    
                    if mtype == "metadata":
                        self.log("ERROR", f"Bắt được khóa phiên mã hóa: {msg.get('enc_session_key')[:40]}...")
                        self.log("ERROR", "❌ Cố tình giải mã RSA nhưng thất bại: Không có Private Key của Receiver!")
                    elif mtype == "data":
                        self.log("ERROR", f"Bắt được đoạn {msg.get('part')} mã hóa: {msg.get('cipher')[:40]}...")
                        self.log("ERROR", "❌ Cố tình giải mã 3DES nhưng thất bại: Không có Session Key hợp lệ!")
                        
                        if self.attack_mode.get() == "modify":
                            self.log("WARNING", "⚠️ ĐANG TIẾN HÀNH CHỈNH SỬA DỮ LIỆU ĐỂ PHÁ HOẠI (MITM)...")
                            cipher_b64 = msg['cipher']
                            # Đổi kí tự đầu tiên để làm sai lệch dữ liệu mã hoá (gây lỗi Integrity)
                            mod_char = "A" if cipher_b64[0] != "A" else "B"
                            msg['cipher'] = mod_char + cipher_b64[1:]
                            self.log("WARNING", "Đã thay đổi cipher text và chuyển tiếp cho Receiver để gây lỗi Integrity!")
                    
                    # Forward đi để quá trình truyền vẫn diễn ra thành công (trừ khi bị phát hiện lỗi integrity)
                    protocol.send_message(server_conn, msg)
            except: pass
            finally:
                server_conn.close()

        # Luồng 2: Forward từ Receiver sang Sender
        def forward_r2s():
            try:
                while True:
                    msg = protocol.receive_message(server_conn)
                    if not msg: break
                    
                    self.log("INFO", f"[Bắt gói tin Receiver -> Sender] Trạng thái: {msg.get('status', msg.get('msg', 'Unknown'))}")
                    protocol.send_message(client_conn, msg)
            except: pass
            finally:
                client_conn.close()

        threading.Thread(target=forward_s2r, daemon=True).start()
        threading.Thread(target=forward_r2s, daemon=True).start()

if __name__ == "__main__":
    app = EavesdropperGUI()
    app.mainloop()
