# Hướng Dẫn Chạy Hệ Thống Truyền File Âm Thanh An Toàn (Đề Tài 7)

Tài liệu này hướng dẫn chi tiết cách cài đặt, chạy ứng dụng bằng tiếng Việt và các kiến thức trọng tâm phục vụ cho buổi vấn đáp.

---

## I. HƯỚNG DẪN CÀI ĐẶT & CHẠY HỆ THỐNG

### Bước 1: Cài đặt thư viện cần thiết
Đảm bảo máy tính của bạn đã cài đặt Python (phiên bản 3.7 trở lên). Mở terminal tại thư mục dự án và chạy:
```bash
pip install -r requirements.txt
```
*(Thư viện cốt lõi là `pycryptodome` và `customtkinter` để thiết lập mã hóa và giao diện đồ họa).*

### Bước 2: Sinh khóa RSA và tạo file test mẫu
Trước khi bắt đầu, bạn cần chạy 2 lệnh sau để sinh cặp khóa công khai/bí mật và tạo file âm thanh kiểm thử:
1. **Sinh cặp khóa RSA (2048-bit):**
   ```bash
   python sinh_khoa.py
   ```
   *Lệnh này sinh ra 4 file: `sender_public.pem`, `sender_private.pem`, `receiver_public.pem`, `receiver_private.pem`.*
2. **Tạo file âm thanh mẫu (.mp3) dung lượng ~1MB:**
   ```bash
   python tao_mp3_ao.py
   ```
   *Lệnh này sinh ra file `recording.mp3` trong thư mục.*

---

### Bước 3: Khởi chạy Giao diện đồ họa (GUI) - Khuyên dùng khi vấn đáp
Bạn có 2 sự lựa chọn để khởi động giao diện đồ họa:

#### Cách 1: Bật nhanh cả 3 cửa sổ cùng lúc (Chỉ 1 lệnh)
```bash
python chay_tat_ca.py
```
*Lệnh này sẽ tự động bật đồng thời cả 3 giao diện:*
*   **Người Nhận (Receiver - `nhan_gui.py`)**
*   **Kẻ Nghe Lén (Eavesdropper / Proxy - `nghe_len_gui.py`)**
*   **Người Gửi (Sender - `gui_gui.py`)**

#### Cách 2: Khởi chạy độc lập từng giao diện
Nếu muốn chia ra nhiều cửa sổ dòng lệnh riêng biệt:
1. **Bật giao diện Người nhận:** `python nhan_gui.py` (Bấm **BẬT CHẾ ĐỘ CHỜ ĐỂ NHẬN**)
2. **Bật giao diện Nghe lén (Proxy):** `python nghe_len_gui.py` (Bấm **BẮT ĐẦU NGHE LÉN**)
3. **Bật giao diện Người gửi:** `python gui_gui.py`

---

### Bước 4: Khởi chạy bằng Dòng lệnh (CLI)
Nếu không muốn dùng GUI, bạn có thể thực hiện truyền file trực tiếp thông qua CLI:
1. **Phía Nhận:**
   ```bash
   python nguoi_nhan.py
   ```
2. **Phía Gửi:**
   ```bash
   python nguoi_gui.py
   ```

---

### Bước 5: Chạy các kịch bản kiểm thử & Đo hiệu năng
Thư mục `test/` chứa các kịch bản tự động để chứng minh tính năng an toàn bảo mật:
- **Đo hiệu năng mật mã (Mã hóa/Giải mã):**
  ```bash
  python test/do_hieu_nang_mat_ma.py
  ```
- **Kiểm thử truyền nhận thông thường:**
  ```bash
  python test/kiem_thu_chuan.py
  ```
- **Kiểm thử chống sửa đổi dữ liệu (Tamper):**
  ```bash
  python test/kiem_thu_tamper.py
  ```
- **Kiểm thử chống tấn công phát lại (Replay):**
  ```bash
  python test/kiem_thu_replay.py
  ```

---

## II. KIẾN THỨC TRỌNG TÂM PHỤC VỤ VẤN ĐÁP (Q&A)

### 1. Tại sao phải dùng kết hợp cả Triple DES (3DES) và RSA?
- **3DES (Mã hóa đối xứng):** Dùng để mã hóa dữ liệu file âm thanh dung lượng lớn vì tốc độ mã hóa rất nhanh và tốn ít tài nguyên. Tuy nhiên, 3DES gặp khó khăn trong việc phân phối khóa bí mật một cách an toàn qua mạng công cộng.
- **RSA (Mã hóa bất đối xứng):** Dùng để mã hóa và chuyển giao an toàn khóa phiên (Session Key) của 3DES từ Người gửi sang Người nhận. Quá trình này tận dụng ưu điểm bảo mật cao của khóa công khai/bí mật của RSA để bảo vệ khóa đối xứng.

### 2. Luồng bảo mật chi tiết của hệ thống (4 Bước cốt lõi)
1. **Bước 1: Bắt tay (Handshake):** Người gửi gửi `"Hello!"`, người nhận xác nhận trạng thái sẵn sàng bằng `"Ready!"`.
2. **Bước 2: Xác thực & Trao khóa:**
   - Người gửi tạo **khóa phiên đối xứng** ngẫu nhiên dùng cho 3DES.
   - Người gửi **ký số** lên Metadata (tên file, nhãn thời gian,...) bằng khóa bí mật RSA của mình.
   - Người gửi **mã hóa khóa phiên** bằng khóa công khai RSA của Người nhận (dùng cơ chế đệm tối ưu **PKCS1_OAEP** cùng mã băm **SHA-512**).
   - Người nhận giải mã khóa phiên bằng khóa bí mật RSA của mình, và xác minh chữ ký Metadata bằng khóa công khai RSA của Người gửi.
3. **Bước 3: Chia nhỏ và mã hóa dữ liệu:**
   - File âm thanh được chia làm 3 phần đều nhau để truyền tải hiệu quả qua mạng.
   - Mỗi phần được mã hóa bằng 3DES chế độ **CBC**, sử dụng vector khởi tạo **IV** ngẫu nhiên độc lập.
   - Để bảo vệ tính toàn vẹn (Integrity), hệ thống tính mã băm **SHA-512(IV || Dữ liệu mã hóa)**.
   - Để xác thực (Authentication), người gửi dùng khóa bí mật RSA ký số lên mã băm và thông tin số thứ tự gói tin (`seq`), nhãn thời gian (`timestamp`).
4. **Bước 4: Người nhận kiểm tra & Ghép file:**
   - Người nhận tính toán lại mã băm SHA-512 của gói tin nhận được và đối chiếu với mã băm đính kèm (Tính toàn vẹn).
   - Xác minh chữ ký số bằng khóa công khai RSA của Người gửi (Xác thực & Không chối bỏ).
   - Giải mã từng phần bằng 3DES, sắp xếp lại theo số thứ tự (`seq`) và ghép thành file âm thanh gốc.

### 3. Hệ thống chống các kiểu tấn công mạng như thế nào?
- **Tấn công nghe lén (Eavesdropping):** Kẻ tấn công trên đường truyền chỉ thu được dữ liệu mã hóa (Ciphertext) và khóa phiên đã mã hóa. Nếu không có khóa bí mật RSA của Người nhận, kẻ tấn công không thể giải mã để lấy khóa phiên, từ đó không thể giải mã dữ liệu file âm thanh.
- **Tấn công sửa đổi dữ liệu (Tampering):** Nếu kẻ tấn công thay đổi dù chỉ 1 bit dữ liệu trên đường truyền, khi Người nhận tính toán lại mã băm **SHA-512(IV || Ciphertext)** sẽ thấy khác biệt hoàn toàn với mã băm ban đầu. Đồng thời chữ ký số trên mã băm cũng bị sai lệch. Hệ thống sẽ phát hiện ngay lập tức, từ chối file và trả về mã lỗi **NACK**.
- **Tấn công phát lại (Replay Attack):** Kẻ tấn công ghi lại một gói tin hợp lệ trong quá khứ rồi gửi lại. Hệ thống ngăn chặn bằng 2 cơ chế:
  1. **Nhãn thời gian (Timestamp):** Nếu thời gian gói tin lệch quá 60 giây (`MAX_TIME_DIFF = 60`) so với thời gian hiện tại của Người nhận, gói tin sẽ bị loại bỏ.
  2. **Số thứ tự (Sequence number `seq`):** Người nhận lưu giữ danh sách số thứ tự đã nhận trong phiên truyền. Nếu nhận được số thứ tự trùng lặp hoặc sai thứ tự mong đợi, hệ thống lập tức phát hiện tấn công và hủy bỏ kết nối.
