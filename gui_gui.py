import customtkinter as ctk
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox
import threading
import os
import time
import socket
import base64
import sys
from cau_hinh import HOST, PORT, EAVESDROPPER_PORT
from tien_ich_mat_ma import tai_khoa_rsa, tao_khoa_phien, ma_hoa_rsa, ky_so_rsa, ma_hoa_des3, tinh_toan_hash
import giao_thuc
from nhat_ky import thiet_lap_nhat_ky

# Khắc phục lỗi hiển thị tiếng Việt trên Terminal Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class GiaoDienNguoiGui(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Hệ Thống Gửi File An Toàn - Đề tài 7")
        self.geometry("850x750")

        self.logger = thiet_lap_nhat_ky('sender_gui', 'sender_gui.log')
        
        self.buoc = 0
        self.ket_noi = None
        self.khoa_phien = None
        self.cac_phan = []
        self.khoa_bi_mat_gui = None
        self.khoa_cong_khai_nhan = None

        # UI Components
        self.lbl_tieu_de = ctk.CTkLabel(self, text="CHƯƠNG TRÌNH GỬI FILE (SENDER) - TỪNG BƯỚC", font=ctk.CTkFont(size=20, weight="bold"), text_color="#1a73e8")
        self.lbl_tieu_de.pack(pady=10)

        # Chọn khóa
        self.khung_khoa = ctk.CTkFrame(self)
        self.khung_khoa.pack(pady=5, fill="x", padx=20)
        
        self.duong_dan_khoa_bi_mat = ctk.StringVar(value="sender_private.pem")
        ctk.CTkLabel(self.khung_khoa, text="Khóa Private (Sender):").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        ctk.CTkEntry(self.khung_khoa, textvariable=self.duong_dan_khoa_bi_mat, width=300).grid(row=0, column=1, padx=5, pady=5)
        ctk.CTkButton(self.khung_khoa, text="Chọn", command=lambda: self.chon_khoa(self.duong_dan_khoa_bi_mat), width=60).grid(row=0, column=2, padx=5, pady=5)

        self.duong_dan_khoa_cong_khai = ctk.StringVar(value="receiver_public.pem")
        ctk.CTkLabel(self.khung_khoa, text="Khóa Public (Receiver):").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        ctk.CTkEntry(self.khung_khoa, textvariable=self.duong_dan_khoa_cong_khai, width=300).grid(row=1, column=1, padx=5, pady=5)
        ctk.CTkButton(self.khung_khoa, text="Chọn", command=lambda: self.chon_khoa(self.duong_dan_khoa_cong_khai), width=60).grid(row=1, column=2, padx=5, pady=5)

        # Chọn File
        self.duong_dan_file = ctk.StringVar()
        self.khung_file = ctk.CTkFrame(self)
        self.khung_file.pack(pady=5, fill="x", padx=20)
        
        self.o_nhap_file = ctk.CTkEntry(self.khung_file, textvariable=self.duong_dan_file, font=ctk.CTkFont(size=12), state='readonly')
        self.o_nhap_file.pack(side="left", expand=True, fill="x", padx=(10, 5), pady=10)
        self.nut_duyet_file = ctk.CTkButton(self.khung_file, text="Chọn File Audio", command=self.chon_file, width=120)
        self.nut_duyet_file.pack(side="right", padx=(5, 10), pady=10)

        # Chọn Cổng Đích (Trực tiếp hoặc qua Nghe lén)
        self.khung_dich = ctk.CTkFrame(self)
        self.khung_dich.pack(pady=5, padx=20, fill="x")
        
        ctk.CTkLabel(self.khung_dich, text="Kết nối đến:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10, pady=5)
        self.bien_cong_dich = ctk.IntVar(value=PORT)
        ctk.CTkRadioButton(self.khung_dich, text="Máy Nhận (Bình thường)", variable=self.bien_cong_dich, value=PORT).pack(side="left", padx=10, pady=5)
        ctk.CTkRadioButton(self.khung_dich, text="Kẻ Nghe Lén (Đi qua Proxy của Hacker)", variable=self.bien_cong_dich, value=EAVESDROPPER_PORT).pack(side="left", padx=10, pady=5)

        # Lời chào bắt tay
        self.khung_bat_tay = ctk.CTkFrame(self)
        self.khung_bat_tay.pack(pady=5, padx=20, fill="x")
        
        self.bien_chao_mung = ctk.StringVar(value="Hello!")
        ctk.CTkLabel(self.khung_bat_tay, text="Lời chào Bắt tay:").pack(side="left", padx=10)
        ctk.CTkEntry(self.khung_bat_tay, textvariable=self.bien_chao_mung, width=150).pack(side="left", padx=5)

        # Nút điều khiển
        self.khung_nut = ctk.CTkFrame(self, fg_color="transparent")
        self.khung_nut.pack(pady=10, padx=20, fill="x")
        
        self.nut_tiep_tuc = ctk.CTkButton(self.khung_nut, text="BƯỚC 1: KẾT NỐI & BẮT TAY", command=self.thuc_hien_buoc_tiep, font=ctk.CTkFont(size=14, weight="bold"), height=40)
        self.nut_tiep_tuc.pack(side="left", padx=5, expand=True, fill="x")
        
        self.nut_lam_lai = ctk.CTkButton(self.khung_nut, text="LÀM LẠI", command=self.dat_lai_trang_thai, font=ctk.CTkFont(size=14, weight="bold"), height=40, fg_color="#f44336", hover_color="#d32f2f")
        self.nut_lam_lai.pack(side="right", padx=5)

        # Log
        ctk.CTkLabel(self, text="Nhật ký tương tác:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=20)
        self.vung_nhat_ky = ctk.CTkTextbox(self, height=250, font=ctk.CTkFont(family="Consolas", size=12))
        self.vung_nhat_ky.pack(pady=5, padx=20, fill="both", expand=True)

    def ghi_nhat_ky(self, tien_to, thong_diep):
        full_msg = f"[{time.strftime('%H:%M:%S')}] [{tien_to}] {thong_diep}\n"
        self.vung_nhat_ky.insert("end", full_msg)
        self.vung_nhat_ky.see("end")
        if tien_to == "INFO": self.logger.info(thong_diep)
        elif tien_to == "WARNING": self.logger.warning(thong_diep)
        elif tien_to == "ERROR": self.logger.error(thong_diep)

    def chon_file(self):
        filename = filedialog.askopenfilename()
        if filename: 
            self.duong_dan_file.set(filename)
            self.o_nhap_file.configure(state="normal")
            self.o_nhap_file.delete(0, "end")
            self.o_nhap_file.insert(0, filename)
            self.o_nhap_file.configure(state="readonly")
            
    def chon_khoa(self, var):
        filename = filedialog.askopenfilename(filetypes=[("PEM Files", "*.pem"), ("All Files", "*.*")])
        if filename: var.set(filename)

    def dat_lai_trang_thai(self):
        self.buoc = 0
        if self.ket_noi:
            try: self.ket_noi.close()
            except: pass
            self.ket_noi = None
        self.khoa_phien = None
        self.cac_phan = []
        self.nut_tiep_tuc.configure(text="BƯỚC 1: KẾT NỐI & BẮT TAY", state="normal")
        self.ghi_nhat_ky("INFO", "Đã reset trạng thái hệ thống.")

    def thuc_hien_buoc_tiep(self):
        self.nut_tiep_tuc.configure(state="disabled")
        if self.buoc == 0:
            threading.Thread(target=self.buoc_bat_tay, daemon=True).start()
        elif self.buoc == 1:
            threading.Thread(target=self.buoc_metadata, daemon=True).start()
        elif self.buoc == 2:
            threading.Thread(target=self.buoc_gui_phan, args=(1,), daemon=True).start()
        elif self.buoc == 3:
            threading.Thread(target=self.buoc_gui_phan, args=(2,), daemon=True).start()
        elif self.buoc == 4:
            threading.Thread(target=self.buoc_gui_phan, args=(3,), daemon=True).start()

    def cap_nhat_nut(self, text):
        self.after(0, lambda: self.nut_tiep_tuc.configure(text=text, state="normal"))

    def trang_thai_loi(self):
        self.after(0, lambda: self.nut_tiep_tuc.configure(text="LỖI - HÃY LÀM LẠI", state="disabled"))

    def buoc_bat_tay(self):
        if not self.duong_dan_file.get():
            self.after(0, lambda: messagebox.showwarning("Lỗi", "Vui lòng chọn file!"))
            self.cap_nhat_nut("BƯỚC 1: KẾT NỐI & BẮT TAY")
            return
            
        try:
            self.khoa_bi_mat_gui = tai_khoa_rsa(self.duong_dan_khoa_bi_mat.get())
            self.khoa_cong_khai_nhan = tai_khoa_rsa(self.duong_dan_khoa_cong_khai.get())
        except Exception as e:
            self.ghi_nhat_ky("ERROR", f"Lỗi tải khóa RSA: {e}")
            self.cap_nhat_nut("BƯỚC 1: KẾT NỐI & BẮT TAY")
            return

        target_port = self.bien_cong_dich.get()
        try:
            self.ket_noi = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.ghi_nhat_ky("INFO", f"Đang kết nối tới cổng {target_port}...")
            self.ket_noi.connect((HOST, target_port))
            
            hs_msg = self.bien_chao_mung.get()
            self.ghi_nhat_ky("INFO", f"Đang gửi '{hs_msg}' để bắt tay...")
            giao_thuc.gui_tin_nhan(self.ket_noi, {"type": "handshake", "msg": hs_msg})
            resp = giao_thuc.nhan_tin_nhan(self.ket_noi)
            
            if not resp or resp.get("msg") != "Ready!":
                self.ghi_nhat_ky("ERROR", f"Bắt tay thất bại! Phản hồi nhận được: {resp.get('msg') if resp else 'None'}")
                self.trang_thai_loi()
                return
                
            self.ghi_nhat_ky("INFO", f"Bắt tay thành công (Nhận phản hồi {resp.get('msg')}).")
            self.buoc = 1
            self.cap_nhat_nut("BƯỚC 2: TẠO KHÓA PHIÊN & GỬI METADATA")
        except Exception as e:
            self.ghi_nhat_ky("ERROR", f"Lỗi kết nối: {e}")
            self.trang_thai_loi()

    def buoc_metadata(self):
        try:
            self.ghi_nhat_ky("INFO", "Sinh Khóa Phiên (3DES) & Đóng gói Metadata...")
            self.khoa_phien = tao_khoa_phien()
            khoa_phien_ma_hoa = ma_hoa_rsa(self.khoa_cong_khai_nhan, self.khoa_phien)
            
            filepath = self.duong_dan_file.get()
            filename = os.path.basename(filepath)
            ts = int(time.time())
            duration = 180
            
            chuoi_metadata = f"{filename}|{ts}|{duration}"
            chu_ky = ky_so_rsa(self.khoa_bi_mat_gui, chuoi_metadata.encode('utf-8'))

            giao_thuc.gui_tin_nhan(self.ket_noi, {
                "type": "metadata", "filename": filename, "timestamp": ts, "duration": duration,
                "enc_session_key": base64.b64encode(khoa_phien_ma_hoa).decode('utf-8'),
                "sig": base64.b64encode(chu_ky).decode('utf-8')
            })
            self.ghi_nhat_ky("INFO", "Đã gửi Metadata & Khóa Phiên (đã được mã hóa RSA).")
            
            resp = giao_thuc.nhan_tin_nhan(self.ket_noi)
            if not resp or resp.get("status") != giao_thuc.ACK_META:
                self.ghi_nhat_ky("ERROR", f"Người nhận từ chối Metadata: {resp.get('reason') if resp else 'Không phản hồi'}")
                self.trang_thai_loi()
                return
                
            self.ghi_nhat_ky("INFO", "Người nhận đã xác minh chữ ký số và nhận Metadata thành công.")
            
            # Chia file thành 3 phần bằng nhau
            with open(filepath, 'rb') as f: file_data = f.read()
            part_size = len(file_data) // 3
            self.cac_phan = [file_data[:part_size], file_data[part_size:2*part_size], file_data[2*part_size:]]
            
            self.buoc = 2
            self.cap_nhat_nut("BƯỚC 3: MÃ HÓA & GỬI ĐOẠN 1/3")
        except Exception as e:
            self.ghi_nhat_ky("ERROR", f"Lỗi Metadata: {e}")
            self.trang_thai_loi()

    def buoc_gui_phan(self, p_idx):
        try:
            part_data = self.cac_phan[p_idx - 1]
            self.ghi_nhat_ky("INFO", f"Đang mã hóa 3DES và ký số đoạn {p_idx}...")
            
            iv, cipher = ma_hoa_des3(self.khoa_phien, part_data)
            h_val = tinh_toan_hash(iv, cipher)
            
            # Ký số lên mã băm + thứ tự + nhãn thời gian để chống tấn công phát lại/giả mạo gói tin
            ts_goi = int(time.time())
            du_lieu_ky_so = h_val + p_idx.to_bytes(4, 'big') + ts_goi.to_bytes(8, 'big')
            p_sig = ky_so_rsa(self.khoa_bi_mat_gui, du_lieu_ky_so)

            giao_thuc.gui_tin_nhan(self.ket_noi, {
                "type": "data", "part": p_idx, "iv": base64.b64encode(iv).decode('utf-8'),
                "cipher": base64.b64encode(cipher).decode('utf-8'),
                "hash": base64.b64encode(h_val).decode('utf-8'), 
                "sig": base64.b64encode(p_sig).decode('utf-8'),
                "timestamp": ts_goi,
                "seq": p_idx
            })
            self.ghi_nhat_ky("INFO", f"Đã gửi Đoạn {p_idx}/3.")
            
            resp = giao_thuc.nhan_tin_nhan(self.ket_noi)
            if not resp or resp.get("status") != giao_thuc.ACK_PART:
                self.ghi_nhat_ky("ERROR", f"Lỗi ở đoạn {p_idx}: {resp.get('reason') if resp else 'Không phản hồi'}")
                self.trang_thai_loi()
                return
                
            self.ghi_nhat_ky("INFO", f"Người nhận phản hồi thành công (ACK) đoạn {p_idx}.")
            
            if p_idx == 1:
                self.buoc = 3
                self.cap_nhat_nut("BƯỚC 4: MÃ HÓA & GỬI ĐOẠN 2/3")
            elif p_idx == 2:
                self.buoc = 4
                self.cap_nhat_nut("BƯỚC 5: MÃ HÓA & GỬI ĐOẠN 3/3")
            elif p_idx == 3:
                # Nhận phản hồi hoàn thành từ người nhận
                resp = giao_thuc.nhan_tin_nhan(self.ket_noi)
                if resp and resp.get("status") == giao_thuc.ACK_COMPLETE:
                    self.ghi_nhat_ky("INFO", "TẤT CẢ HOÀN TẤT! File đã được truyền an toàn.")
                    self.after(0, lambda: messagebox.showinfo("Thành công", "Truyền file hoàn tất!"))
                    self.after(0, lambda: self.nut_tiep_tuc.configure(text="HOÀN THÀNH", state="disabled"))
                else:
                    self.ghi_nhat_ky("ERROR", f"Lỗi hoàn tất: {resp.get('reason') if resp else 'Không phản hồi'}")
                    self.trang_thai_loi()
        except Exception as e:
            self.ghi_nhat_ky("ERROR", f"Lỗi gửi dữ liệu: {e}")
            self.trang_thai_loi()

if __name__ == "__main__":
    app = GiaoDienNguoiGui()
    app.mainloop()
