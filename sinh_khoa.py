from tien_ich_mat_ma import tao_khoa_rsa
import os
import sys

# Khắc phục lỗi hiển thị tiếng Việt trên Terminal Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

if __name__ == "__main__":
    if not os.path.exists("sender_private.pem"):
        print("Đang tạo cặp khóa RSA cho Người Gửi...")
        tao_khoa_rsa("sender")
    if not os.path.exists("receiver_private.pem"):
        print("Đang tạo cặp khóa RSA cho Người Nhận...")
        tao_khoa_rsa("receiver")
    print("Đã khởi tạo tất cả các cặp khóa RSA thành công.")
