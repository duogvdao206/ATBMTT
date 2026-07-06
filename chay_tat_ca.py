import subprocess
import sys
import time

# Khắc phục lỗi hiển thị tiếng Việt trên Terminal Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def main():
    print("Đang khởi động cả 3 ứng dụng (Người nhận, Kẻ nghe lén, Người gửi)...")
    
    # Khởi động Receiver (Người nhận)
    p_receiver = subprocess.Popen([sys.executable, "nhan_gui.py"])
    time.sleep(0.3)
    
    # Khởi động Eavesdropper (Kẻ nghe lén / Proxy)
    p_eavesdropper = subprocess.Popen([sys.executable, "nghe_len_gui.py"])
    time.sleep(0.3)
    
    # Khởi động Sender (Người gửi)
    p_sender = subprocess.Popen([sys.executable, "gui_gui.py"])
    
    print("Đã khởi chạy cả 3 giao diện GUI tiếng Việt thành công!")
    print("Bạn có thể tắt terminal này, các cửa sổ GUI vẫn hoạt động độc lập.")

if __name__ == "__main__":
    main()
