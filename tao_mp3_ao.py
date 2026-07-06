import os
import sys

# Khắc phục lỗi hiển thị tiếng Việt trên Terminal Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

if __name__ == "__main__":
    if not os.path.exists("recording.mp3"):
        with open("recording.mp3", "wb") as f:
            f.write(os.urandom(1024 * 1024)) # Tạo file giả dung lượng khoảng 1MB
        print("Đã tạo file âm thanh giả lập recording.mp3 thành công.")
    else:
        print("File recording.mp3 đã tồn tại.")
