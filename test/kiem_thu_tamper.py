import os
import subprocess
import time
import sys

# Khắc phục lỗi hiển thị tiếng Việt trên Terminal Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

THU_MUC_GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def test_tamper():
    print("\n--- Bắt đầu kiểm thử tấn công sửa đổi gói tin (Tamper Data) ---")
    receiver = subprocess.Popen([sys.executable, "nguoi_nhan.py"], cwd=THU_MUC_GOC)
    time.sleep(1)
    
    sender = subprocess.Popen([sys.executable, "nguoi_gui.py", "--tamper"], cwd=THU_MUC_GOC)
    
    sender.wait()
    receiver.wait()
    
    print("[+] kiem_thu_tamper: HOÀN TẤT. Xem logs để xác nhận nhận được NACK do sai lệch mã băm (Hash mismatch).")

if __name__ == "__main__":
    test_tamper()
