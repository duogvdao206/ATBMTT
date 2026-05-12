import time
import os
from crypto_utils import generate_session_key, des3_encrypt, des3_decrypt

def run_benchmark(file_size_mb):
    print(f"\n--- Đang chạy Benchmark cho file {file_size_mb}MB ---")
    
    # Tạo dữ liệu giả lập
    data = os.urandom(file_size_mb * 1024 * 1024)
    key = generate_session_key()
    
    # Đo thời gian mã hóa
    start_enc = time.time()
    iv, cipher = des3_encrypt(key, data)
    end_enc = time.time()
    enc_time = end_enc - start_enc
    
    # Đo thời gian giải mã
    start_dec = time.time()
    pt = des3_decrypt(key, iv, cipher)
    end_dec = time.time()
    dec_time = end_dec - start_dec
    
    print(f"Kích thước: {file_size_mb} MB")
    print(f"Thời gian mã hóa (Triple DES): {enc_time:.4f} giây")
    print(f"Thời gian giải mã (Triple DES): {dec_time:.4f} giây")
    print(f"Tổng cộng: {enc_time + dec_time:.4f} giây")
    print(f"Tốc độ trung bình: {file_size_mb / (enc_time + dec_time):.2f} MB/s")

if __name__ == "__main__":
    sizes = [1, 5, 10] # Các kích thước file cần test
    for size in sizes:
        run_benchmark(size)
