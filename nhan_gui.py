import customtkinter as ctk
import tkinter.messagebox as messagebox
import tkinter.filedialog as filedialog
import threading
import socket
import time
import base64
import os
import sys
from cau_hinh import HOST, PORT, MAX_TIME_DIFF
from tien_ich_mat_ma import tai_khoa_rsa, giai_ma_rsa, xac_minh_chu_ky_rsa, giai_ma_des3, tinh_toan_hash
import giao_thuc
from nhat_ky import thiet_lap_nhat_ky

# Khắc phục lỗi hiển thị tiếng Việt trên Terminal Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("green")

class GiaoDienNguoiNhan(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Hệ Thống Nhận File An Toàn - Đề tài 7")
        self.geometry("850x750")

        self.logger = thiet_lap_nhat_ky('receiver_gui', 'receiver_gui.log')
        self.dang_lang_nghe = False
        self.socket_server = None
        self.su_kien_bat_tay = threading.Event()
        self.phan_hoi_bat_tay = ""

        # UI Components
        self.lbl_tieu_de = ctk.CTkLabel(self, text="CHƯƠNG TRÌNH NHẬN FILE (RECEIVER)", font=ctk.CTkFont(size=20, weight="bold"), text_color="#d32f2f")
        self.lbl_tieu_de.pack(pady=10)

        # Chọn Khóa
        self.khung_khoa = ctk.CTkFrame(self)
        self.khung_khoa.pack(pady=5, fill="x", padx=20)
        
        self.duong_dan_khoa_bi_mat = ctk.StringVar(value="receiver_private.pem")
        ctk.CTkLabel(self.khung_khoa, text="Khóa Private (Receiver):").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        ctk.CTkEntry(self.khung_khoa, textvariable=self.duong_dan_khoa_bi_mat, width=300).grid(row=0, column=1, padx=5, pady=5)
        ctk.CTkButton(self.khung_khoa, text="Chọn", command=lambda: self.chon_khoa(self.duong_dan_khoa_bi_mat), width=60).grid(row=0, column=2, padx=5, pady=5)

        self.duong_dan_khoa_cong_khai = ctk.StringVar(value="sender_public.pem")
        ctk.CTkLabel(self.khung_khoa, text="Khóa Public (Sender):").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        ctk.CTkEntry(self.khung_khoa, textvariable=self.duong_dan_khoa_cong_khai, width=300).grid(row=1, column=1, padx=5, pady=5)
        ctk.CTkButton(self.khung_khoa, text="Chọn", command=lambda: self.chon_khoa(self.duong_dan_khoa_cong_khai), width=60).grid(row=1, column=2, padx=5, pady=5)

        # Khung Bật Chờ Nhận
        self.khung_nut = ctk.CTkFrame(self, fg_color="transparent")
        self.khung_nut.pack(pady=10, padx=20, fill="x")
        
        self.nut_lang_nghe = ctk.CTkButton(self.khung_nut, text="BẬT CHẾ ĐỘ CHỜ ĐỂ NHẬN", command=self.chuyen_doi_lang_nghe, fg_color="#4caf50", hover_color="#388e3c", font=ctk.CTkFont(size=14, weight="bold"), height=40)
        self.nut_lang_nghe.pack(side="left", padx=5, expand=True, fill="x")

        # Khung Phản Hồi Bắt Tay
        self.khung_phan_hoi = ctk.CTkFrame(self)
        self.khung_phan_hoi.pack(pady=5, padx=20, fill="x")
        
        self.bien_phan_hoi_chao = ctk.StringVar(value="Ready!")
        ctk.CTkLabel(self.khung_phan_hoi, text="Phản hồi Bắt tay:").pack(side="left", padx=10)
        ctk.CTkEntry(self.khung_phan_hoi, textvariable=self.bien_phan_hoi_chao, width=150).pack(side="left", padx=5)
        
        self.nut_gui_phan_hoi = ctk.CTkButton(self.khung_phan_hoi, text="GỬI PHẢN HỒI", command=self.gui_phan_hoi_bat_tay, state="disabled")
        self.nut_gui_phan_hoi.pack(side="left", padx=10)

        # Trạng Thái
        self.bien_trang_thai = ctk.StringVar(value="Trạng thái: Đang dừng")
        self.lbl_trang_thai = ctk.CTkLabel(self, textvariable=self.bien_trang_thai, font=ctk.CTkFont(slant="italic"))
        self.lbl_trang_thai.pack(pady=5)

        # Log nhật ký
        ctk.CTkLabel(self, text="Nhật ký tương tác & Trạng thái:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=20)
        self.vung_nhat_ky = ctk.CTkTextbox(self, height=350, font=ctk.CTkFont(family="Consolas", size=12))
        self.vung_nhat_ky.pack(pady=5, padx=20, fill="both", expand=True)

    def ghi_nhat_ky(self, tien_to, thong_diep):
        full_msg = f"[{time.strftime('%H:%M:%S')}] [{tien_to}] {thong_diep}\n"
        self.vung_nhat_ky.insert("end", full_msg)
        self.vung_nhat_ky.see("end")
        if tien_to == "INFO": self.logger.info(thong_diep)
        elif tien_to == "WARNING": self.logger.warning(thong_diep)
        elif tien_to == "ERROR": self.logger.error(thong_diep)

    def chon_khoa(self, var):
        filename = filedialog.askopenfilename(filetypes=[("PEM Files", "*.pem"), ("All Files", "*.*")])
        if filename: var.set(filename)

    def kich_hoat_nut_bat_tay(self):
        self.nut_gui_phan_hoi.configure(state="normal")
        
    def gui_phan_hoi_bat_tay(self):
        self.phan_hoi_bat_tay = self.bien_phan_hoi_chao.get()
        self.nut_gui_phan_hoi.configure(state="disabled")
        self.su_kien_bat_tay.set()

    def chuyen_doi_lang_nghe(self):
        if not self.dang_lang_nghe: 
            self.bat_dau_lang_nghe()
        else: 
            self.dung_lang_nghe()

    def bat_dau_lang_nghe(self):
        self.dang_lang_nghe = True
        self.nut_lang_nghe.configure(text="DỪNG CHẾ ĐỘ CHỜ", fg_color="#f44336", hover_color="#d32f2f")
        self.bien_trang_thai.set(f"Đang nghe tại {HOST}:{PORT}")
        threading.Thread(target=self.chay_server, daemon=True).start()

    def dung_lang_nghe(self):
        self.dang_lang_nghe = False
        self.nut_lang_nghe.configure(text="BẬT CHẾ ĐỘ CHỜ ĐỂ NHẬN", fg_color="#4caf50", hover_color="#388e3c")
        self.bien_trang_thai.set("Trạng thái: Đang dừng")
        if self.socket_server: 
            try: self.socket_server.close()
            except: pass

    def chay_server(self):
        try:
            khoa_bi_mat_nhan = tai_khoa_rsa(self.duong_dan_khoa_bi_mat.get())
            khoa_cong_khai_gui = tai_khoa_rsa(self.duong_dan_khoa_cong_khai.get())
        except Exception as e:
            self.ghi_nhat_ky("ERROR", f"Lỗi khóa: {e}")
            self.after(0, self.dung_lang_nghe)
            return

        self.socket_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try: 
            self.socket_server.bind((HOST, PORT))
        except Exception as e: 
            self.ghi_nhat_ky("ERROR", f"Không thể liên kết cổng {PORT}: {e}")
            return
        
        self.socket_server.listen(5)
        self.ghi_nhat_ky("INFO", f"Hệ thống máy nhận đã sẵn sàng tại cổng {PORT}.")
        self.ghi_nhat_ky("INFO", "Đang chờ dữ liệu từng bước từ Sender...")

        while self.dang_lang_nghe:
            try:
                self.socket_server.settimeout(1.0)
                conn, addr = self.socket_server.accept()
                self.ghi_nhat_ky("INFO", f"Phát hiện kết nối từ {addr}")
                conn.settimeout(None) 
                threading.Thread(target=self.xu_ly_khach_hang, args=(conn, khoa_bi_mat_nhan, khoa_cong_khai_gui), daemon=True).start()
            except socket.timeout: 
                continue
            except Exception: 
                break

    def xu_ly_khach_hang(self, conn, khoa_bi_mat_nhan, khoa_cong_khai_gui):
        with conn:
            try:
                # 1. Handshake
                msg = giao_thuc.nhan_tin_nhan(conn)
                if not msg or msg.get("type") != "handshake": return
                
                self.ghi_nhat_ky("INFO", f"Nhận được lời chào bắt tay: '{msg.get('msg')}'")
                self.ghi_nhat_ky("INFO", "Vui lòng nhập phản hồi và bấm 'GỬI PHẢN HỒI' trên giao diện...")
                
                self.after(0, self.kich_hoat_nut_bat_tay)
                self.su_kien_bat_tay.wait()
                self.su_kien_bat_tay.clear()
                
                self.ghi_nhat_ky("INFO", f"Đang gửi phản hồi bắt tay: '{self.phan_hoi_bat_tay}'")
                giao_thuc.gui_tin_nhan(conn, {"type": "handshake", "msg": self.phan_hoi_bat_tay})

                # 2. Nhận Metadata
                msg = giao_thuc.nhan_tin_nhan(conn)
                if not msg or msg.get("type") != "metadata": return

                # Gán tên file từ metadata — BẮT BUỘC để dùng khi ghép và lưu file cuối
                ten_file = msg["filename"]
                ts = msg["timestamp"]
                duration = msg.get("duration")
                self.ghi_nhat_ky("INFO", f"Nhận yêu cầu truyền file: {ten_file}")

                # Chống tấn công phát lại dựa trên nhãn thời gian
                if abs(time.time() - ts) > MAX_TIME_DIFF:
                    self.ghi_nhat_ky("WARNING", "[SECURITY] Phát hiện tấn công phát lại! (Timestamp quá hạn)")
                    giao_thuc.gui_tin_nhan(conn, {"status": giao_thuc.NACK_REPLAY, "reason": "lỗi integrity (Timestamp expired)"})
                    return

                chuoi_metadata = f"{msg['filename']}|{ts}|{duration}"
                sig = base64.b64decode(msg["sig"])
                
                # Xác thực chữ ký số trên Metadata
                if not xac_minh_chu_ky_rsa(khoa_cong_khai_gui, chuoi_metadata.encode('utf-8'), sig):
                    self.ghi_nhat_ky("ERROR", "[SECURITY] Chữ ký Metadata không hợp lệ!")
                    giao_thuc.gui_tin_nhan(conn, {"status": giao_thuc.NACK_SIGNATURE, "reason": "lỗi integrity (Invalid signature)"})
                    return

                # Giải mã Khóa phiên RSA
                try:
                    enc_key = base64.b64decode(msg["enc_session_key"])
                    khoa_phien = giai_ma_rsa(khoa_bi_mat_nhan, enc_key)
                    self.ghi_nhat_ky("INFO", "Giải mã khóa phiên RSA thành công. Chữ ký số Metadata hợp lệ.")
                except Exception:
                    giao_thuc.gui_tin_nhan(conn, {"status": giao_thuc.NACK_KEY_ERROR, "reason": "Key decryption failed"})
                    return

                giao_thuc.gui_tin_nhan(conn, {"status": giao_thuc.ACK_META})
                self.ghi_nhat_ky("INFO", "Sẵn sàng nhận các đoạn dữ liệu mã hóa...")

                # 3. Nhận các phần dữ liệu
                cac_phan_da_nhan = []
                cac_goi_da_nhan = set()
                thu_tu_mong_doi = 1

                for i in range(3):
                    msg = giao_thuc.nhan_tin_nhan(conn)
                    if not msg or msg.get("type") != "data": return
                    
                    phan = msg["part"]
                    iv = base64.b64decode(msg["iv"])
                    cipher = base64.b64decode(msg["cipher"])
                    hash_val = bytes.fromhex(msg["hash"])
                    p_sig = base64.b64decode(msg["sig"])
                    ts_goi = msg.get("timestamp", int(time.time()))
                    thu_tu = msg.get("seq", i + 1)

                    # Kiểm tra trùng lặp gói tin và sai thứ tự gói tin
                    if thu_tu in cac_goi_da_nhan or thu_tu != thu_tu_mong_doi:
                        self.ghi_nhat_ky("ERROR", "[SECURITY] Phát hiện tấn công phát lại gói tin hoặc sai thứ tự!")
                        giao_thuc.gui_tin_nhan(conn, {"status": giao_thuc.NACK_INTEGRITY, "reason": "lỗi integrity (Replay or wrong sequence)"})
                        return
                    cac_goi_da_nhan.add(thu_tu)
                    thu_tu_mong_doi += 1

                    # Kiểm tra tính toàn vẹn (SHA-512)
                    if tinh_toan_hash(iv, cipher) != hash_val:
                        self.ghi_nhat_ky("ERROR", f"[SECURITY] Lỗi toàn vẹn dữ liệu (Hash mismatch) tại Đoạn {phan}!")
                        giao_thuc.gui_tin_nhan(conn, {"status": giao_thuc.NACK_INTEGRITY, "reason": "lỗi integrity"})
                        return

                    # Xác thực chữ ký số của gói tin
                    du_lieu_xac_minh = hash_val + thu_tu.to_bytes(4, 'big') + ts_goi.to_bytes(8, 'big')
                    if not xac_minh_chu_ky_rsa(khoa_cong_khai_gui, du_lieu_xac_minh, p_sig):
                        self.ghi_nhat_ky("ERROR", f"[SECURITY] Xác thực chữ ký gói tin thất bại tại Đoạn {phan}!")
                        giao_thuc.gui_tin_nhan(conn, {"status": giao_thuc.NACK_INTEGRITY, "reason": "lỗi integrity"})
                        return

                    # Giải mã (Triple DES)
                    pt = giai_ma_des3(khoa_phien, iv, cipher)
                    cac_phan_da_nhan.append((phan, pt))
                    self.ghi_nhat_ky("INFO", f"Đã nhận, xác minh và giải mã thành công Đoạn {phan}/3.")
                    giao_thuc.gui_tin_nhan(conn, {"status": giao_thuc.ACK_PART})

                # Ghép và lưu file
                cac_phan_da_nhan.sort(key=lambda x: x[0])
                du_lieu_day_du = b''.join([p[1] for p in cac_phan_da_nhan])
                ten_file_ra = "received_" + ten_file
                with open(ten_file_ra, 'wb') as f: 
                    f.write(du_lieu_day_du)
                
                self.ghi_nhat_ky("INFO", f"HOÀN TẤT: Đã ghép đủ các đoạn và lưu file thành công: {ten_file_ra}")
                giao_thuc.gui_tin_nhan(conn, {"status": giao_thuc.ACK_COMPLETE})
                self.after(0, lambda: messagebox.showinfo("Thành công", f"Đã nhận file hoàn tất: {ten_file_ra}"))

            except Exception as e: 
                self.ghi_nhat_ky("ERROR", f"Lỗi xử lý kết nối: {e}")

if __name__ == "__main__":
    app = GiaoDienNguoiNhan()
    app.mainloop()
