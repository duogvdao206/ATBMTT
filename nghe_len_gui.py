import customtkinter as ctk
import threading
import socket
import time
import sys
from cau_hinh import HOST, PORT, EAVESDROPPER_PORT
import giao_thuc
from nhat_ky import thiet_lap_nhat_ky

# Khắc phục lỗi hiển thị tiếng Việt trên Terminal Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

class GiaoDienNgheLen(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Kẻ Nghe Lén (Eavesdropper) - MITM Proxy")
        self.geometry("850x650")

        self.logger = thiet_lap_nhat_ky('eavesdropper_gui', 'eavesdropper_gui.log')
        self.dang_nghe_len = False
        self.socket_server = None

        # UI Components
        self.lbl_tieu_de = ctk.CTkLabel(self, text="⚠️ GIAO DIỆN KẺ NGHE LÉN (ATTACKER) ⚠️", font=ctk.CTkFont(size=20, weight="bold"), text_color="#ff1744")
        self.lbl_tieu_de.pack(pady=15)

        # Khung Hành động tấn công
        self.khung_tan_cong = ctk.CTkFrame(self)
        self.khung_tan_cong.pack(pady=5, padx=20, fill="x")

        ctk.CTkLabel(self.khung_tan_cong, text="Hành động tấn công:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10, pady=5)
        self.bien_che_do_tan_cong = ctk.StringVar(value="listen")
        
        self.nut_radio_nghe = ctk.CTkRadioButton(self.khung_tan_cong, text="Chỉ Nghe Lén (Cố tình giải mã)", variable=self.bien_che_do_tan_cong, value="listen")
        self.nut_radio_nghe.pack(side="left", padx=10, pady=5)
        
        self.nut_radio_sua = ctk.CTkRadioButton(self.khung_tan_cong, text="Chỉnh Sửa Dữ Liệu (Phá hoại)", variable=self.bien_che_do_tan_cong, value="modify")
        self.nut_radio_sua.pack(side="left", padx=10, pady=5)

        # Nút Bật/Tắt
        self.khung_nut = ctk.CTkFrame(self, fg_color="transparent")
        self.khung_nut.pack(pady=10, padx=20, fill="x")
        
        self.nut_nghe_len = ctk.CTkButton(self.khung_nut, text="BẮT ĐẦU NGHE LÉN (Chạy Proxy)", command=self.chuyen_doi_nghe_len, fg_color="#d50000", hover_color="#b71c1c", font=ctk.CTkFont(size=14, weight="bold"), height=40)
        self.nut_nghe_len.pack(side="left", padx=5, expand=True, fill="x")
        
        self.bien_trang_thai = ctk.StringVar(value="Trạng thái: Chưa hoạt động")
        self.lbl_trang_thai = ctk.CTkLabel(self, textvariable=self.bien_trang_thai, font=ctk.CTkFont(slant="italic"), text_color="#ff5252")
        self.lbl_trang_thai.pack(pady=5)

        # Log
        ctk.CTkLabel(self, text="Dữ liệu đánh cắp được (Raw Data):", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=20)
        self.vung_nhat_ky = ctk.CTkTextbox(self, height=450, font=ctk.CTkFont(family="Consolas", size=12), text_color="#00e676", fg_color="#1a1a1a")
        self.vung_nhat_ky.pack(pady=5, padx=20, fill="both", expand=True)

    def ghi_nhat_ky(self, tien_to, thong_diep):
        full_msg = f"[{time.strftime('%H:%M:%S')}] [{tien_to}] {thong_diep}\n"
        self.vung_nhat_ky.insert("end", full_msg)
        self.vung_nhat_ky.see("end")
        if tien_to == "INFO": self.logger.info(thong_diep)
        elif tien_to == "WARNING": self.logger.warning(thong_diep)
        elif tien_to == "ERROR": self.logger.error(thong_diep)

    def chuyen_doi_nghe_len(self):
        if not self.dang_nghe_len: 
            self.bat_dau_nghe_len()
        else: 
            self.dung_nghe_len()

    def bat_dau_nghe_len(self):
        self.dang_nghe_len = True
        self.nut_nghe_len.configure(text="DỪNG NGHE LÉN", fg_color="#424242", hover_color="#212121")
        self.bien_trang_thai.set(f"Đang nghe lén tại cổng {EAVESDROPPER_PORT}...")
        threading.Thread(target=self.chay_server, daemon=True).start()

    def dung_nghe_len(self):
        self.dang_nghe_len = False
        self.nut_nghe_len.configure(text="BẮT ĐẦU NGHE LÉN (Chạy Proxy)", fg_color="#d50000", hover_color="#b71c1c")
        self.bien_trang_thai.set("Trạng thái: Đã dừng")
        if self.socket_server: 
            self.socket_server.close()

    def chay_server(self):
        self.socket_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try: 
            self.socket_server.bind((HOST, EAVESDROPPER_PORT))
        except Exception as e: 
            self.ghi_nhat_ky("ERROR", f"Không thể bind cổng {EAVESDROPPER_PORT}: {e}")
            return
        
        self.socket_server.listen(5)
        self.ghi_nhat_ky("INFO", f"Proxy trung gian đã mở tại cổng {EAVESDROPPER_PORT}.")

        while self.dang_nghe_len:
            try:
                self.socket_server.settimeout(1.0)
                conn_khach, addr = self.socket_server.accept()
                self.ghi_nhat_ky("WARNING", f"Phát hiện Sender kết nối tới proxy từ {addr}!")
                threading.Thread(target=self.xu_ly_mitm, args=(conn_khach,), daemon=True).start()
            except socket.timeout: 
                continue
            except Exception: 
                break

    def xu_ly_mitm(self, conn_khach):
        conn_may_nhan = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            # Kẻ nghe lén kết nối tới Người nhận thật
            conn_may_nhan.connect((HOST, PORT))
            self.ghi_nhat_ky("INFO", f"Kẻ nghe lén đã kết nối lén tới Receiver thật tại cổng {PORT}.")
        except Exception:
            self.ghi_nhat_ky("ERROR", "Máy nhận thật (Receiver) chưa bật, không thể chuyển tiếp gói tin!")
            conn_khach.close()
            return

        # Luồng 1: Chuyển tiếp từ Sender sang Receiver
        def chuyen_tiep_s2r():
            try:
                while True:
                    msg = giao_thuc.nhan_tin_nhan(conn_khach)
                    if not msg: break
                    
                    loai_msg = msg.get("type", "Unknown")
                    self.ghi_nhat_ky("WARNING", f"[Bắt gói tin Sender -> Receiver] Loại gói: {loai_msg}")
                    
                    if loai_msg == "metadata":
                        self.ghi_nhat_ky("ERROR", f"Bắt được khóa phiên mã hóa: {msg.get('enc_session_key')[:40]}...")
                        self.ghi_nhat_ky("ERROR", "❌ Cố tình giải mã RSA nhưng thất bại: Không có Private Key của Receiver!")
                    elif loai_msg == "data":
                        self.ghi_nhat_ky("ERROR", f"Bắt được đoạn {msg.get('part')} mã hóa: {msg.get('cipher')[:40]}...")
                        self.ghi_nhat_ky("ERROR", "❌ Cố tình giải mã 3DES nhưng thất bại: Không có Session Key của phiên truyền!")
                        
                        if self.bien_che_do_tan_cong.get() == "modify":
                            self.ghi_nhat_ky("WARNING", "⚠️ ĐANG TIẾN HÀNH CHỈNH SỬA DỮ LIỆU ĐỂ PHÁ HOẠI (MITM)...")
                            cipher_b64 = msg['cipher']
                            # Đổi ký tự đầu tiên để phá hoại dữ liệu mã hoá (gây lỗi Integrity)
                            ky_tu_sua = "A" if cipher_b64[0] != "A" else "B"
                            msg['cipher'] = ky_tu_sua + cipher_b64[1:]
                            self.ghi_nhat_ky("WARNING", "Đã thay đổi ciphertext và chuyển tiếp cho Receiver để gây lỗi Integrity!")
                    
                    # Chuyển tiếp đi
                    giao_thuc.gui_tin_nhan(conn_may_nhan, msg)
            except: pass
            finally:
                conn_may_nhan.close()

        # Luồng 2: Chuyển tiếp từ Receiver sang Sender
        def chuyen_tiep_r2s():
            try:
                while True:
                    msg = giao_thuc.nhan_tin_nhan(conn_may_nhan)
                    if not msg: break
                    
                    self.ghi_nhat_ky("INFO", f"[Bắt gói tin Receiver -> Sender] Trạng thái: {msg.get('status', msg.get('msg', 'Unknown'))}")
                    giao_thuc.gui_tin_nhan(conn_khach, msg)
            except: pass
            finally:
                conn_khach.close()

        threading.Thread(target=chuyen_tiep_s2r, daemon=True).start()
        threading.Thread(target=chuyen_tiep_r2s, daemon=True).start()

if __name__ == "__main__":
    app = GiaoDienNgheLen()
    app.mainloop()
