# Hướng Dẫn Chạy Hệ Thống Truyền File Âm Thanh An Toàn

Tài liệu này hướng dẫn chi tiết cách cài đặt và chạy ứng dụng truyền file âm thanh an toàn. Dự án cung cấp cả giao diện dòng lệnh (CLI) và giao diện đồ họa (GUI).

## Bước 1: Cài đặt môi trường
Đảm bảo bạn đã cài đặt Python (phiên bản 3.7 trở lên) trên máy tính.

1. Mở Terminal (hoặc Command Prompt / PowerShell).
2. Di chuyển vào thư mục của dự án:
   ```bash
   cd đường_dẫn_đến_thư_mục_atbmtt_btl
   ```
3. Cài đặt các thư viện cần thiết (cụ thể là `pycryptodome`):
   ```bash
   pip install -r requirements.txt
   ```

## Bước 2: Chuẩn bị dữ liệu và khóa mã hóa
Trước khi chạy hệ thống truyền file, bạn cần tạo các cặp khóa RSA và chuẩn bị file âm thanh để test.

1. **Sinh cặp khóa RSA (Public/Private key):**
   ```bash
   python generate_keys.py
   ```
   *Lệnh này sẽ tạo ra 4 file: `sender_public.pem`, `sender_private.pem`, `receiver_public.pem`, `receiver_private.pem` nằm trong thư mục hiện tại.*

2. **Tạo file âm thanh mẫu (để test nếu chưa có file MP3 thực tế):**
   ```bash
   python generate_dummy_mp3.py
   ```
   *Lệnh này sẽ tạo ra một file tên là `recording.mp3` có dung lượng khoảng 1MB.*

---

## Bước 3: Chạy ứng dụng với Giao diện đồ họa (GUI)
Đây là cách dễ dàng nhất để sử dụng ứng dụng.

1. **Khởi động phần mềm Nhận (Receiver):**
   Mở một Terminal mới, chạy lệnh:
   ```bash
   python receiver_gui.py
   ```
   - Trên giao diện Receiver, nhấn **Start Receiver** để bắt đầu lắng nghe kết nối (mặc định ở cổng 5000).

2. **Khởi động phần mềm Gửi (Sender):**
   Mở một Terminal khác, chạy lệnh:
   ```bash
   python sender_gui.py
   ```
   - Trên giao diện Sender:
     - Chọn file Private Key của Sender (`sender_private.pem`).
     - Chọn file Public Key của Receiver (`receiver_public.pem`).
     - Chọn file MP3 cần gửi (ví dụ: `recording.mp3`).
     - Nhập địa chỉ IP là `127.0.0.1` và Port là `5000` (nếu chạy trên cùng 1 máy).
     - Nhấn nút **Send File** để gửi đi. File nhận được sẽ được tự động lưu lại ở phía Receiver (ví dụ: `received_recording.mp3`).

---

## Bước 4: Chạy ứng dụng bằng dòng lệnh (CLI)
Nếu bạn muốn sử dụng dòng lệnh thay cho GUI:

1. Bật Server nhận file:
   ```bash
   python receiver.py
   ```
2. Mở một cửa sổ dòng lệnh khác, chạy Client để gửi file:
   ```bash
   python sender.py
   ```
   *Lưu ý: Bạn có thể cần chỉnh sửa cứng đường dẫn file trong mã nguồn `sender.py` nếu muốn gửi file khác với thiết lập mặc định.*

---

## Bước 5: Chạy các kịch bản kiểm thử (Test & Benchmark)
Hệ thống cung cấp các file để kiểm tra hiệu năng và các kịch bản tấn công thử nghiệm (replay attack, tamper data,...).

- **Đo lường hiệu năng mã hóa/giải mã:**
  ```bash
  python benchmark.py
  ```

- **Chạy các file test trong thư mục `test/` (nếu có):**
  ```bash
  python test/test_normal.py
  python test/test_tamper.py
  python test/test_replay.py
  ```
