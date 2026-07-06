"""
Chạy tất cả kiểm thử theo trình tự, chờ giải phóng port giữa các lần chạy.
"""
import subprocess
import sys
import time
import os
import re

# Khắc phục lỗi hiển thị tiếng Việt trên Terminal Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

THU_MUC_GOC = os.path.dirname(os.path.abspath(__file__))
THU_MUC_TEST = os.path.join(THU_MUC_GOC, "test")


def giai_phong_cong(cong):
    """Dừng mọi tiến trình đang chiếm cổng mạng."""
    try:
        output = subprocess.check_output(
            f'netstat -aon | findstr :{cong}', shell=True
        ).decode('utf-8', errors='ignore')
        for line in output.strip().split('\n'):
            parts = re.split(r'\s+', line.strip())
            if len(parts) >= 5:
                pid = parts[-1]
                if pid.isdigit() and int(pid) > 0:
                    subprocess.run(f'taskkill /F /PID {pid}', shell=True,
                                   capture_output=True)
    except Exception:
        pass


def chay_kiem_thu(ten, script):
    print(f"\n{'='*55}")
    print(f"  Đang chạy: {ten}")
    print(f"{'='*55}")
    giai_phong_cong(65432)
    time.sleep(1)
    ket_qua = subprocess.run(
        [sys.executable, script],
        cwd=THU_MUC_TEST,
        capture_output=True, text=True, encoding='utf-8', errors='ignore'
    )
    stdout = ket_qua.stdout.strip()
    stderr = ket_qua.stderr.strip()
    if stdout:
        print(stdout)
    if stderr:
        print("[STDERR]", stderr[:500])
    giai_phong_cong(65432)
    time.sleep(1)


if __name__ == "__main__":
    print("╔══════════════════════════════════════════════════════╗")
    print("║       CHẠY TOÀN BỘ KIỂM THỬ - ĐỀ TÀI 7             ║")
    print("╚══════════════════════════════════════════════════════╝")

    chay_kiem_thu("Truyền file chuẩn (không có tấn công)",    "kiem_thu_chuan.py")
    chay_kiem_thu("Phát hiện giả mạo dữ liệu (Tamper Data)", "kiem_thu_tamper.py")
    chay_kiem_thu("Phát hiện tấn công phát lại (Replay)",    "kiem_thu_replay.py")

    print("\n╔══════════════════════════════════════════════════════╗")
    print("║          TẤT CẢ KIỂM THỬ ĐÃ HOÀN TẤT               ║")
    print("╚══════════════════════════════════════════════════════╝")
