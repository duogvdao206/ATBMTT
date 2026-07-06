import os
import time
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tien_ich_mat_ma import tao_khoa_phien, ma_hoa_des3, giai_ma_des3

# Khắc phục lỗi hiển thị tiếng Việt trên Terminal Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def benchmark():
    print("--- Đo hiệu năng mật mã Triple DES ---")
    sizes = [
        (10 * 1024, "10 KB"),
        (1 * 1024 * 1024, "1 MB"),
        (10 * 1024 * 1024, "10 MB")
    ]
    
    key = tao_khoa_phien()
    
    for size, name in sizes:
        data = os.urandom(size)
        
        start_enc = time.time()
        iv, cipher = ma_hoa_des3(key, data)
        end_enc = time.time()
        
        start_dec = time.time()
        pt = giai_ma_des3(key, iv, cipher)
        end_dec = time.time()
        
        assert data == pt
        
        print(f"Kích thước file: {name}")
        print(f"  Thời gian mã hóa: {end_enc - start_enc:.4f} s")
        print(f"  Thời gian giải mã: {end_dec - start_dec:.4f} s")
        print(f"  Tổng thời gian:   {(end_enc - start_enc) + (end_dec - start_dec):.4f} s")
        print("-" * 30)

if __name__ == "__main__":
    benchmark()
