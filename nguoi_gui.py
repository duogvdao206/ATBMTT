import socket
import time
import os
import base64
import argparse
import sys
from cau_hinh import HOST, PORT
from tien_ich_mat_ma import tai_khoa_rsa, tao_khoa_phien, ma_hoa_rsa, ky_so_rsa, ma_hoa_des3, tinh_toan_hash
from giao_thuc import gui_tin_nhan, nhan_tin_nhan
from nhat_ky import thiet_lap_nhat_ky

# Khắc phục lỗi hiển thị tiếng Việt trên Terminal Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

nhat_ky = thiet_lap_nhat_ky('sender', 'sender.log')

def khoi_dong_nguoi_gui(duong_dan_file, gia_mao_du_lieu=False, tan_cong_phat_lai=False):
    """
    Hàm khởi chạy tiến trình gửi file âm thanh an toàn qua giao thức TCP.
    
    Các bước thực hiện (Đáp ứng yêu cầu vấn đáp):
    1. Bắt tay (Handshake) với Người nhận.
    2. Sinh khóa phiên đối xứng (Triple DES Session Key) 24 bytes.
    3. Mã hóa khóa phiên bằng khóa công khai RSA của Người nhận (RSA-OAEP 2048-bit + SHA-512).
    4. Ký số lên dữ liệu metadata bằng khóa bí mật RSA của Người gửi (RSA-PSS + SHA-512).
    5. Gửi Metadata và Khóa phiên được mã hóa sang Người nhận để xác thực & thiết lập phiên truyền.
    6. Đọc file âm thanh, chia làm 3 phần bằng nhau.
    7. Mã hóa từng phần bằng Triple DES CBC (mỗi phần sinh 1 IV ngẫu nhiên).
    8. Tính toán mã băm SHA-512(IV || ciphertext) làm chứng thư toàn vẹn.
    9. Ký số lên mã băm và các thông số thứ tự (seq) & timestamp của gói tin.
    10. Gửi lần lượt 3 đoạn dữ liệu và chờ ACK xác nhận từ Người nhận.
    """
    if not os.path.exists(duong_dan_file):
        print(f"Không tìm thấy file {duong_dan_file}!")
        return

    try:
        khoa_bi_mat_gui = tai_khoa_rsa('sender_private.pem')
        khoa_cong_khai_nhan = tai_khoa_rsa('receiver_public.pem')
    except FileNotFoundError:
        print("Không tìm thấy các file khóa RSA. Vui lòng chạy sinh_khoa.py trước.")
        return

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((HOST, PORT))
            nhat_ky.info("Đã kết nối thành công tới Người nhận.")

            # Bước 1: Handshake
            gui_tin_nhan(s, {"type": "handshake", "msg": "Hello!"})
            nhat_ky.info("Đã gửi thông điệp chào: Hello!")
            
            phan_hoi = nhan_tin_nhan(s)
            if not phan_hoi or phan_hoi.get("msg") != "Ready!":
                nhat_ky.error("Quá trình bắt tay thất bại.")
                return
            nhat_ky.info("Nhận được phản hồi: Ready!")

            # Bước 2: Sinh khóa phiên và mã hóa RSA
            khoa_phien = tao_khoa_phien()
            khoa_phien_ma_hoa = ma_hoa_rsa(khoa_cong_khai_nhan, khoa_phien)
            
            ten_file = os.path.basename(duong_dan_file)
            nhan_thoi_gian = int(time.time())
            
            # Kịch bản giả lập tấn công phát lại (Replay Attack) bằng cách lùi thời gian
            if tan_cong_phat_lai:
                nhan_thoi_gian -= 100
                
            thoi_luong = "unknown"
            
            chuoi_metadata = f"{ten_file}|{nhan_thoi_gian}|{thoi_luong}"
            chu_ky = ky_so_rsa(khoa_bi_mat_gui, chuoi_metadata.encode('utf-8'))

            # Gửi Metadata và Khóa phiên được mã hóa
            gui_tin_nhan(s, {
                "type": "metadata",
                "filename": ten_file,
                "timestamp": nhan_thoi_gian,
                "duration": thoi_luong,
                "enc_session_key": base64.b64encode(khoa_phien_ma_hoa).decode('utf-8'),
                "sig": base64.b64encode(chu_ky).decode('utf-8')
            })
            nhat_ky.info("Đã gửi dữ liệu Metadata và Khóa phiên mã hóa RSA.")

            phan_hoi = nhan_tin_nhan(s)
            if not phan_hoi or phan_hoi.get("status") != "ACK":
                nhat_ky.error(f"Người nhận từ chối Metadata. Lý do: {phan_hoi.get('reason')}")
                print(f"Người nhận từ chối Metadata: {phan_hoi.get('reason')}")
                return
            
            # Bước 3: Đọc file và chia nhỏ thành 3 phần
            with open(duong_dan_file, 'rb') as f:
                du_lieu_file = f.read()
            
            kich_thuoc_phan = len(du_lieu_file) // 3
            cac_phan = [
                du_lieu_file[:kich_thuoc_phan],
                du_lieu_file[kich_thuoc_phan:2*kich_thuoc_phan],
                du_lieu_file[2*kich_thuoc_phan:]
            ]

            thu_tu = 1
            for i, du_lieu_phan in enumerate(cac_phan):
                chi_so_phan = i + 1
                iv, ma_hoa_phan = ma_hoa_des3(khoa_phien, du_lieu_phan)
                # Tính mã băm SHA-512 của IV và ciphertext để bảo vệ toàn vẹn
                ma_hash = tinh_toan_hash(iv, ma_hoa_phan)
                
                nhan_thoi_gian_goi = int(time.time())
                # Dữ liệu dùng để ký số gồm: hash || seq || timestamp
                du_lieu_ky_so = ma_hash + thu_tu.to_bytes(4, 'big') + nhan_thoi_gian_goi.to_bytes(8, 'big')
                chu_ky_goi = ky_so_rsa(khoa_bi_mat_gui, du_lieu_ky_so)

                # Giả lập sửa đổi dữ liệu trái phép (Tamper) SAU KHI đã băm và ký để Người nhận phát hiện
                ma_hoa_phan_gui = ma_hoa_phan
                if gia_mao_du_lieu and i == 1:
                    ma_hoa_phan_gui = bytearray(ma_hoa_phan)
                    ma_hoa_phan_gui[0] ^= 0xFF
                    ma_hoa_phan_gui = bytes(ma_hoa_phan_gui)

                goi_tin = {
                    "type": "data",
                    "part": chi_so_phan,
                    "iv": base64.b64encode(iv).decode('utf-8'),
                    "cipher": base64.b64encode(ma_hoa_phan_gui).decode('utf-8'),
                    "hash": base64.b64encode(ma_hash).decode('utf-8'),
                    "sig": base64.b64encode(chu_ky_goi).decode('utf-8'),
                    "timestamp": nhan_thoi_gian_goi,
                    "seq": thu_tu
                }
                
                gui_tin_nhan(s, goi_tin)
                nhat_ky.info(f"Đã gửi thành công Đoạn {chi_so_phan}/3.")
                thu_tu += 1

            # Nhận phản hồi hoàn tất cuối cùng
            phan_hoi = nhan_tin_nhan(s)
            if phan_hoi and phan_hoi.get("status") == "ACK":
                nhat_ky.info("Quá trình truyền file hoàn tất thành công! Đã nhận ACK cuối cùng.")
                print("Truyền file thành công.")
            else:
                nhat_ky.error(f"Truyền file thất bại. Phản hồi nhận được: {phan_hoi}")
                print(f"Truyền file thất bại. Lý do: {phan_hoi.get('reason') if phan_hoi else 'Không phản hồi'}")

        except Exception as e:
            nhat_ky.error(f"Lỗi phía Người gửi: {e}")
            print(f"Lỗi phía Người gửi: {e}")

if __name__ == "__main__":
    bo_phan_tich = argparse.ArgumentParser(description="Người Gửi File An Toàn - Secure File Sender")
    bo_phan_tich.add_argument('--file', type=str, default='recording.mp3', help='Đường dẫn file cần gửi')
    bo_phan_tich.add_argument('--tamper', action='store_true', help='Giả lập phá hoại dữ liệu (kiểm tra tính toàn vẹn)')
    bo_phan_tich.add_argument('--replay', action='store_true', help='Giả lập tấn công phát lại (hết hạn timestamp)')
    tham_so = bo_phan_tich.parse_args()

    khoi_dong_nguoi_gui(tham_so.file, tham_so.tamper, tham_so.replay)
