import os
import subprocess
import time
import sys

# Khắc phục lỗi hiển thị tiếng Việt trên Terminal Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Lấy đường dẫn thư mục gốc của dự án (thư mục chứa các file .py chính)
THU_MUC_GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def test_chuan():
    # Đảm bảo các khóa và file mp3 tồn tại
    subprocess.run([sys.executable, "sinh_khoa.py"], cwd=THU_MUC_GOC)
    subprocess.run([sys.executable, "tao_mp3_ao.py"], cwd=THU_MUC_GOC)
    
    print("\n--- Bắt đầu kiểm thử chế độ truyền file chuẩn ---")
    receiver = subprocess.Popen([sys.executable, "nguoi_nhan.py"], cwd=THU_MUC_GOC)
    time.sleep(1) # Chờ server receiver khởi động xong
    sender = subprocess.Popen([sys.executable, "nguoi_gui.py"], cwd=THU_MUC_GOC)
    
    sender.wait()
    receiver.wait()
    
    # Kiểm tra xem file nhận được có trùng khớp kích thước với file gốc không
    duong_dan_goc = os.path.join(THU_MUC_GOC, "recording.mp3")
    duong_dan_nhan = os.path.join(THU_MUC_GOC, "received_recording.mp3")
    
    if os.path.exists(duong_dan_nhan):
        kt_goc = os.path.getsize(duong_dan_goc)
        kt_nhan = os.path.getsize(duong_dan_nhan)
        if kt_goc == kt_nhan:
            print("[+] kiem_thu_chuan: THÀNH CÔNG (PASS)")
        else:
            print("[-] kiem_thu_chuan: THẤT BẠI (Lệch kích thước file)")
    else:
        print("[-] kiem_thu_chuan: THẤT BẠI (Không tìm thấy file nhận được)")

if __name__ == "__main__":
    test_chuan()
