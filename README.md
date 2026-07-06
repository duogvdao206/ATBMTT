# Hệ Thống Truyền File Âm Thanh An Toàn (Đề tài 7)

Dự án này là hệ thống truyền file an toàn qua mạng (chủ yếu là file âm thanh `.mp3`), áp dụng các tiêu chuẩn mã hóa bảo mật tiên tiến để đảm bảo: **Tính bảo mật** (Triple DES, RSA), **Tính toàn vẹn** (SHA-512), và **Tính xác thực** (RSA Digital Signature). Dự án hỗ trợ chia nhỏ dữ liệu làm 3 đoạn theo yêu cầu của Đề tài 7.

Toàn bộ mã nguồn, tên hàm và tên file đã được Việt hóa (không dấu) đi kèm ghi chú/comment chi tiết để chuẩn bị cho buổi vấn đáp.

---

## 🌟 Chức năng nổi bật
- **Mã hóa đối xứng**: Triple DES (3DES) kết hợp chia 3 đoạn.
- **Mã hóa bất đối xứng**: RSA 2048-bit (OAEP + SHA-512) để trao đổi khóa phiên (Session Key) và Ký số (Digital Signature PSS).
- **Tính toàn vẹn (Integrity)**: Sử dụng hàm băm SHA-512.
- **Giao thức Handshake (Bắt tay)**: Giao thức Hello!/Ready! đảm bảo hai bên sẵn sàng trước khi truyền.
- **Giao diện hiện đại**: Sử dụng thư viện `customtkinter` (Modern UI) đẹp mắt.
- **Mô phỏng Hacker (MITM Proxy)**: Có kẻ nghe lén chen vào giữa quá trình truyền tải nhưng chứng minh không thể đọc được nội dung do sức mạnh của mã hóa RSA.

---

## 📁 Cấu trúc thư mục và Giải thích file

### 🖥️ Các File Giao Diện (GUI)
- `gui_gui.py` (cũ là `sender_gui.py`): Giao diện của **Máy gửi (Sender)**. Cho phép chọn file và tự động gửi đi. Có tùy chọn gửi thẳng qua Máy nhận hoặc gửi thông qua Kênh bị nghe lén (Proxy).
- `nhan_gui.py` (cũ là `receiver_gui.py`): Giao diện của **Máy nhận (Receiver)**. Mở cổng mạng (65432) lắng nghe, nhận dữ liệu, xác thực, tự động giải mã và ghép file.
- `nghe_len_gui.py` (cũ là `eavesdropper_gui.py`): Giao diện của **Kẻ nghe lén (Attacker / MITM Proxy)**. Đóng vai trò là trạm trung gian (cổng 65433). Máy gửi gửi dữ liệu vào đây, nó sẽ ghi lại nhật ký (bắt gói tin) rồi mới chuyển tiếp đến Máy nhận.

### ⚙️ Các File Cốt Lõi (Core Logic)
- `tien_ich_mat_ma.py` (cũ là `crypto_utils.py`): Chứa toàn bộ các hàm xử lý mật mã (Tạo khóa, Mã hóa RSA/3DES, Ký số, Hash SHA-512).
- `giao_thuc.py` (cũ là `protocol.py`): Định nghĩa giao thức truyền nhận qua Socket, đóng gói/mở gói dữ liệu JSON.
- `cau_hinh.py` (cũ là `config.py`): File cấu hình chứa địa chỉ IP (`HOST`), cổng kết nối (`PORT` và `EAVESDROPPER_PORT`).
- `nhat_ky.py` (cũ là `logger.py`): Xử lý việc ghi nhật ký (log) cho cả 3 ứng dụng ra file và console.

### 🛠️ Các File Hỗ Trợ & Tiện Ích
- `sinh_khoa.py` (cũ là `generate_keys.py`): Script dùng để khởi tạo cặp khóa RSA 2048-bit cho Máy gửi và Máy nhận.
- `tao_mp3_ao.py` (cũ là `generate_dummy_mp3.py`): Script dùng để tự động tạo một file âm thanh giả (`recording.mp3`) để phục vụ việc test.
- `chay_tat_ca.py` (cũ là `run_all.py`): Khởi chạy đồng thời cả 3 giao diện chỉ với 1 dòng lệnh duy nhất.
- `do_hieu_nang.py` (cũ là `benchmark.py` trong root): Đo hiệu năng mã hóa/giải mã Triple DES.
- `requirements.txt`: Danh sách các thư viện Python cần thiết.
- `*.pem`: Các file lưu trữ Khóa công khai / Khóa bí mật (Ví dụ: `sender_private.pem`, `receiver_public.pem`).
- `*.log`: Các file ghi lại toàn bộ hoạt động của hệ thống (Ví dụ: `sender_gui.log`).

---

## 🚀 Hướng Dẫn Cài Đặt & Chạy Hệ Thống

Chi tiết hướng dẫn chạy và kiến thức vấn đáp xem tại file:
👉 **[HUONG_DAN_CHAY.md](HUONG_DAN_CHAY.md)**