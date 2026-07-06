import time
import os
import sys
from tien_ich_mat_ma import tao_khoa_phien, ma_hoa_des3, giai_ma_des3

# Khắc phục lỗi hiển thị tiếng Việt trên Terminal Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def chay_do_hieu_nang(kich_thuoc_mb):
    print(f"\n--- Đang đo hiệu năng mã hóa/giải mã cho file dung lượng {kich_thuoc_mb}MB ---")
    
    # Sinh dữ liệu ngẫu nhiên giả lập file MP3
    du_lieu = os.urandom(kich_thuoc_mb * 1024 * 1024)
    khoa = tao_khoa_phien()
    
    # Đo thời gian mã hóa Triple DES
    bat_dau_ma_hoa = time.time()
    iv, du_lieu_ma_hoa = ma_hoa_des3(khoa, du_lieu)
    ket_thuc_ma_hoa = time.time()
    tg_ma_hoa = ket_thuc_ma_hoa - bat_dau_ma_hoa
    
    # Đo thời gian giải mã Triple DES
    bat_dau_giai_ma = time.time()
    du_lieu_giai_ma = giai_ma_des3(khoa, iv, du_lieu_ma_hoa)
    ket_thuc_giai_ma = time.time()
    tg_giai_ma = ket_thuc_giai_ma - bat_dau_giai_ma
    
    # Kiểm tra tính chính xác sau khi giải mã
    assert du_lieu == du_lieu_giai_ma, "Dữ liệu giải mã bị sai lệch!"
    
    print(f"Kích thước: {kich_thuoc_mb} MB")
    print(f"Thời gian mã hóa (Triple DES): {tg_ma_hoa:.4f} giây")
    print(f"Thời gian giải mã (Triple DES): {tg_giai_ma:.4f} giây")
    print(f"Tổng thời gian xử lý: {tg_ma_hoa + tg_giai_ma:.4f} giây")
    print(f"Tốc độ trung bình: {kich_thuoc_mb / (tg_ma_hoa + tg_giai_ma):.2f} MB/s")

if __name__ == "__main__":
    kich_thuoc_test = [1, 5, 10]
    for kt in kich_thuoc_test:
        chay_do_hieu_nang(kt)
