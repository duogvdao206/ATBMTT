import socket
import time
import base64
import sys
from cau_hinh import HOST, PORT, MAX_TIME_DIFF
from tien_ich_mat_ma import tai_khoa_rsa, giai_ma_rsa, xac_minh_chu_ky_rsa, giai_ma_des3, tinh_toan_hash
from giao_thuc import gui_tin_nhan, nhan_tin_nhan
from nhat_ky import thiet_lap_nhat_ky

# Khắc phục lỗi hiển thị tiếng Việt trên Terminal Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

nhat_ky = thiet_lap_nhat_ky('receiver', 'receiver.log')

def khoi_dong_nguoi_nhan():
    """
    Hàm khởi chạy tiến trình nhận file âm thanh an toàn qua giao thức TCP.
    
    Các bước thực hiện (Đáp ứng yêu cầu vấn đáp):
    1. Lắng nghe và chấp nhận kết nối từ Người gửi.
    2. Bắt tay (Handshake) để xác lập trạng thái sẵn sàng.
    3. Nhận Metadata, chữ ký số và Khóa phiên được mã hóa RSA.
    4. Kiểm tra Timestamp chống tấn công phát lại (Replay Attack).
    5. Xác minh chữ ký số của Metadata bằng khóa công khai RSA của Người gửi.
    6. Giải mã khóa phiên Triple DES bằng khóa bí mật RSA của Người nhận.
    7. Nhận lần lượt từng đoạn dữ liệu, kiểm tra tính toàn vẹn bằng SHA-512(IV || ciphertext) và kiểm tra chữ ký số.
    8. Giải mã các đoạn dữ liệu bằng Triple DES CBC.
    9. Sắp xếp thứ tự các đoạn dữ liệu và lắp ghép lại thành file gốc ban đầu.
    """
    try:
        khoa_bi_mat_nhan = tai_khoa_rsa('receiver_private.pem')
        khoa_cong_khai_gui = tai_khoa_rsa('sender_public.pem')
    except FileNotFoundError:
        print("Không tìm thấy các file khóa RSA. Vui lòng chạy sinh_khoa.py trước.")
        return

    cac_goi_da_nhan = set()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"Người nhận đang lắng nghe kết nối tại {HOST}:{PORT}...")
        nhat_ky.info("Người nhận đã khởi động và đang chờ kết nối.")

        ket_noi, dia_chi = s.accept()
        with ket_noi:
            nhat_ky.info(f"Phát hiện kết nối từ địa chỉ: {dia_chi}")
            
            # Bước 1: Handshake
            tin_nhan = nhan_tin_nhan(ket_noi)
            if not tin_nhan or tin_nhan.get("type") != "handshake" or tin_nhan.get("msg") != "Hello!":
                nhat_ky.error("Quá trình bắt tay không hợp lệ.")
                return
            
            nhat_ky.info("Nhận được 'Hello!'. Đang gửi phản hồi 'Ready!'...")
            gui_tin_nhan(ket_noi, {"type": "handshake", "msg": "Ready!"})

            # Bước 2: Nhận và xác thực Metadata
            tin_nhan = nhan_tin_nhan(ket_noi)
            if not tin_nhan or tin_nhan.get("type") != "metadata":
                nhat_ky.error("Không nhận được gói tin Metadata hợp lệ.")
                return
            
            ten_file = tin_nhan["filename"]
            nhan_thoi_gian = tin_nhan["timestamp"]
            thoi_luong = tin_nhan["duration"]
            
            # Chống tấn công phát lại (Replay Attack) dựa trên nhãn thời gian
            if abs(time.time() - nhan_thoi_gian) > MAX_TIME_DIFF:
                nhat_ky.error("Nhãn thời gian Metadata đã hết hạn. Nghi ngờ tấn công phát lại (Replay attack)!")
                gui_tin_nhan(ket_noi, {"status": "NACK", "reason": "Nhãn thời gian hết hạn"})
                return

            chuoi_metadata = f"{ten_file}|{nhan_thoi_gian}|{thoi_luong}"
            chu_ky = base64.b64decode(tin_nhan["sig"])
            
            # Xác minh chữ ký số của Metadata
            if not xac_minh_chu_ky_rsa(khoa_cong_khai_gui, chuoi_metadata.encode('utf-8'), chu_ky):
                nhat_ky.error("Chữ ký Metadata không hợp lệ!")
                gui_tin_nhan(ket_noi, {"status": "NACK", "reason": "Chữ ký không hợp lệ"})
                return

            # Giải mã RSA để lấy khóa phiên Triple DES
            try:
                khoa_phien_ma_hoa = base64.b64decode(tin_nhan["enc_session_key"])
                khoa_phien = giai_ma_rsa(khoa_bi_mat_nhan, khoa_phien_ma_hoa)
            except Exception as e:
                nhat_ky.error("Giải mã khóa phiên thất bại.")
                gui_tin_nhan(ket_noi, {"status": "NACK", "reason": "Giải mã khóa phiên thất bại"})
                return

            nhat_ky.info("Metadata và Khóa phiên được xác minh và giải mã thành công.")
            gui_tin_nhan(ket_noi, {"status": "ACK"})

            # Bước 3: Nhận và giải mã các gói tin dữ liệu
            cac_phan_du_lieu = []
            thu_tu_mong_doi = 1
            
            for i in range(3):
                tin_nhan = nhan_tin_nhan(ket_noi)
                if not tin_nhan or tin_nhan.get("type") != "data":
                    nhat_ky.error("Không nhận được gói tin dữ liệu đúng định dạng.")
                    gui_tin_nhan(ket_noi, {"status": "NACK", "reason": "Thiếu gói tin dữ liệu"})
                    return
                
                phan = tin_nhan["part"]
                iv = base64.b64decode(tin_nhan["iv"])
                ma_hoa_phan = base64.b64decode(tin_nhan["cipher"])
                ma_hash = bytes.fromhex(tin_nhan["hash"])
                chu_ky_goi = base64.b64decode(tin_nhan["sig"])
                nhan_thoi_gian_goi = tin_nhan["timestamp"]
                thu_tu = tin_nhan["seq"]

                # Kiểm tra nhãn thời gian của từng gói dữ liệu
                if abs(time.time() - nhan_thoi_gian_goi) > MAX_TIME_DIFF:
                    nhat_ky.error(f"Nhãn thời gian gói tin {phan} đã hết hạn.")
                    gui_tin_nhan(ket_noi, {"status": "NACK", "reason": f"Nhãn thời gian gói tin {phan} hết hạn"})
                    return
                
                # Kiểm tra trùng lặp gói tin và sai lệch thứ tự truyền nhận
                if thu_tu in cac_goi_da_nhan or thu_tu != thu_tu_mong_doi:
                    nhat_ky.error("Phát hiện tấn công phát lại hoặc sai lệch thứ tự gói tin!")
                    gui_tin_nhan(ket_noi, {"status": "NACK", "reason": "Tấn công phát lại hoặc sai thứ tự gói"})
                    return
                cac_goi_da_nhan.add(thu_tu)
                thu_tu_mong_doi += 1

                # Kiểm tra tính toàn vẹn (Integrity) bằng mã băm SHA-512
                ma_hash_tinh_duoc = tinh_toan_hash(iv, ma_hoa_phan)
                if ma_hash_tinh_duoc != ma_hash:
                    nhat_ky.error(f"Lỗi toàn vẹn dữ liệu (Hash mismatch) tại đoạn {phan}!")
                    gui_tin_nhan(ket_noi, {"status": "NACK", "reason": f"Lỗi toàn vẹn (Hash mismatch) đoạn {phan}"})
                    return

                # Kiểm tra xác thực (Authentication) bằng chữ ký số
                du_lieu_xac_minh = ma_hash + thu_tu.to_bytes(4, 'big') + nhan_thoi_gian_goi.to_bytes(8, 'big')
                if not xac_minh_chu_ky_rsa(khoa_cong_khai_gui, du_lieu_xac_minh, chu_ky_goi):
                    nhat_ky.error(f"Xác minh chữ ký số thất bại tại đoạn {phan}!")
                    gui_tin_nhan(ket_noi, {"status": "NACK", "reason": f"Chữ ký không khớp ở đoạn {phan}"})
                    return

                # Giải mã Triple DES
                try:
                    du_lieu_goc_phan = giai_ma_des3(khoa_phien, iv, ma_hoa_phan)
                    cac_phan_du_lieu.append((phan, du_lieu_goc_phan))
                    nhat_ky.info(f"Đã nhận, xác minh và giải mã thành công Đoạn {phan}/3.")
                except Exception as e:
                    nhat_ky.error(f"Giải mã Triple DES thất bại tại đoạn {phan}.")
                    gui_tin_nhan(ket_noi, {"status": "NACK", "reason": f"Giải mã thất bại đoạn {phan}"})
                    return

            # Sắp xếp và ghép nối các đoạn file
            cac_phan_du_lieu.sort(key=lambda x: x[0])
            du_lieu_toan_bo = b''.join([p[1] for p in cac_phan_du_lieu])
            
            ten_file_ra = "received_" + ten_file
            with open(ten_file_ra, 'wb') as f:
                f.write(du_lieu_toan_bo)
            
            nhat_ky.info(f"Ghép nối file thành công và lưu tại: {ten_file_ra}")
            gui_tin_nhan(ket_noi, {"status": "ACK", "reason": "Nhận file hoàn tất thành công"})
            print(f"Nhận file thành công. Đã khôi phục thành file: {ten_file_ra}")

if __name__ == "__main__":
    khoi_dong_nguoi_nhan()
