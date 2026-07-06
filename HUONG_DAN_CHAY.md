# 📋 HƯỚNG DẪN CHẠY DEMO - ĐỀ TÀI 7
## Gửi Tập Tin Âm Thanh Chia Thành Nhiều Đoạn

---

## 🔧 CÀI ĐẶT MÔI TRƯỜNG

```bash
pip install pycryptodome customtkinter
```

---

## 📁 CẤU TRÚC FILE DỰ ÁN

| File | Vai trò |
|---|---|
| `tien_ich_mat_ma.py` | Thư viện mật mã: Triple DES, RSA, SHA-512 |
| `giao_thuc.py` | Giao thức truyền thông qua Socket (JSON framing) |
| `cau_hinh.py` | Cấu hình: HOST, PORT, thời gian hết hạn |
| `sinh_khoa.py` | Sinh cặp khóa RSA 2048-bit |
| `tao_mp3_ao.py` | Tạo file recording.mp3 giả lập |
| `nhan_gui.py` | **GUI Người Nhận** (Studio/Receiver) |
| `gui_gui.py` | **GUI Người Gửi** (Nhà Sản Xuất/Sender) |
| `nghe_len_gui.py` | **GUI Kẻ Nghe Lén** (MITM Proxy/Attacker) |
| `chay_tat_ca.py` | Khởi động cả 3 GUI cùng lúc |
| `nguoi_nhan.py` | Người Nhận dòng lệnh (CLI) |
| `nguoi_gui.py` | Người Gửi dòng lệnh (CLI) |

---

## 🚀 CÁCH CHẠY NHANH (GẦY NẤT)

```bash
# Bước 0: Sinh khóa + tạo file mp3 mẫu
python sinh_khoa.py
python tao_mp3_ao.py

# Bước 1: Khởi động 3 cửa sổ GUI
python chay_tat_ca.py
```

---

## 📖 LUỒNG XỬ LÝ TỪNG BƯỚC (Demo Chi Tiết)

### ════════════════════════════════════
### BƯỚC 0 — CHUẨN BỊ (Chạy 1 lần)
### ════════════════════════════════════

```bash
python sinh_khoa.py    # Tạo sender_private.pem, sender_public.pem,
                       #        receiver_private.pem, receiver_public.pem
python tao_mp3_ao.py   # Tạo recording.mp3 (~1MB) nếu chưa có
```

---

### ════════════════════════════════════
### KỊCH BẢN 1: TRUYỀN FILE BÌNH THƯỜNG ✅
### ════════════════════════════════════

**Mở 2 terminal:**

**Terminal 1 — Người Nhận (Studio):**
```bash
python nhan_gui.py
# Nhấn "BẬT CHẾ ĐỘ CHỜ ĐỂ NHẬN"
```

**Terminal 2 — Người Gửi (Nhà Sản Xuất):**
```bash
python gui_gui.py
# 1. Chọn file recording.mp3
# 2. Chọn kết nối "Máy Nhận (Bình thường)"
# 3. Nhấn "BƯỚC 1: KẾT NỐI & BẮT TAY"  → Hello! / Ready!
# 4. Nhấn "BƯỚC 2: TẠO KHÓA PHIÊN & GỬI METADATA"
# 5. Nhấn "BƯỚC 3: MÃ HÓA & GỬI ĐOẠN 1/3"
# 6. Nhấn "BƯỚC 4: MÃ HÓA & GỬI ĐOẠN 2/3"
# 7. Nhấn "BƯỚC 5: MÃ HÓA & GỬI ĐOẠN 3/3"
```

**Kết quả mong đợi:**
- Người Nhận hiển thị: `"HOÀN TẤT: Đã ghép đủ các đoạn và lưu file thành công: received_recording.mp3"`
- Người Gửi hiển thị: `"TẤT CẢ HOÀN TẤT! File đã được truyền an toàn."`

---

### ════════════════════════════════════
### KỊCH BẢN 2: PHÁT HIỆN GIẢ MẠO DỮ LIỆU ❌
### ════════════════════════════════════

**Chạy kiểm thử tự động:**
```bash
python test/kiem_thu_tamper.py
```

**Hoặc thủ công:**
```bash
# Terminal 1
python nguoi_nhan.py

# Terminal 2
python nguoi_gui.py --tamper
```

**Điều gì xảy ra:**
- Người gửi cố tình sửa đổi 1 byte của Đoạn 2 SAU KHI đã tính Hash và ký số
- Người nhận tính lại `SHA-512(IV || ciphertext)` → không khớp Hash đã nhận
- → Người nhận gửi **NACK** (lỗi integrity) ngay lập tức
- → Quá trình truyền bị HỦY, file không được lưu

**Kết quả mong đợi trong log:**
```
[SECURITY] Lỗi toàn vẹn dữ liệu (Hash mismatch) tại Đoạn 2!
```

---

### ════════════════════════════════════
### KỊCH BẢN 3: PHÁT HIỆN TẤN CÔNG PHÁT LẠI ❌
### ════════════════════════════════════

**Chạy kiểm thử tự động:**
```bash
python test/kiem_thu_replay.py
```

**Hoặc thủ công:**
```bash
# Terminal 1
python nguoi_nhan.py

# Terminal 2
python nguoi_gui.py --replay
```

**Điều gì xảy ra:**
- Người gửi gửi Metadata với `timestamp` bị lùi 100 giây vào quá khứ
- Người nhận kiểm tra: `|time.time() - timestamp| > MAX_TIME_DIFF (60s)` → vi phạm
- → Người nhận gửi **NACK** (Timestamp hết hạn), từ chối kết nối ngay từ bước Metadata

**Kết quả mong đợi trong log:**
```
[SECURITY] Phát hiện tấn công phát lại! (Timestamp quá hạn)
```

---

### ════════════════════════════════════
### KỊCH BẢN 4: KẺ NGHE LÉN (MITM Proxy) 🕵️
### ════════════════════════════════════

**Mở 3 terminal theo đúng thứ tự:**

```bash
# Terminal 1 — Người Nhận (bật trước)
python nhan_gui.py
# → Nhấn "BẬT CHẾ ĐỘ CHỜ ĐỂ NHẬN" (port 65432)

# Terminal 2 — Kẻ Nghe Lén (bật sau)
python nghe_len_gui.py
# → Nhấn "BẮT ĐẦU NGHE LÉN" (proxy tại port 65433 → forward đến 65432)

# Terminal 3 — Người Gửi (kết nối qua proxy)
python gui_gui.py
# → Chọn file, chọn "Kẻ Nghe Lén (Đi qua Proxy của Hacker)"
# → Thực hiện các bước gửi như bình thường
```

**Chế độ "Chỉ Nghe Lén":**
- Kẻ nghe lén thấy toàn bộ gói tin nhưng KHÔNG giải mã được:
  - Khóa phiên mã hóa RSA → cần `receiver_private.pem` (không có)
  - Ciphertext Triple DES → cần Session Key (không có)
- File vẫn truyền thành công đến người nhận

**Chế độ "Chỉnh Sửa Dữ Liệu (Phá hoại)":**
- Kẻ nghe lén sửa 1 byte ciphertext trước khi forward
- Người nhận phát hiện Hash mismatch → gửi NACK
- → Quá trình truyền bị HỦY

---

## 🧪 CHẠY TẤT CẢ KIỂM THỬ TỰ ĐỘNG

```bash
python test/kiem_thu_chuan.py   # Test truyền file thành công
python test/kiem_thu_tamper.py  # Test phát hiện giả mạo dữ liệu
python test/kiem_thu_replay.py  # Test phát hiện tấn công phát lại
python test/do_hieu_nang_mat_ma.py  # Đo hiệu năng Triple DES
```

---

## 📊 CHI TIẾT KỸ THUẬT MẬT MÃ

### Handshake
```
Sender  ──[Hello!]──►  Receiver
Sender  ◄──[Ready!]──  Receiver
```

### Xác Thực & Trao Khóa
```
Sender sinh SessionKey (24 bytes) cho Triple DES
Sender ký: RSA-PSS/SHA-512(filename|timestamp|duration) → Signature
Sender gửi: { metadata, enc_session_key=RSA_OAEP_SHA512(SessionKey), sig }
Receiver xác minh Signature + Giải mã SessionKey
```

### Gửi Từng Đoạn (3 lần)
```
Sender:
  IV = random(8 bytes)
  cipher_i = 3DES_CBC(SessionKey, IV, segment_i)
  hash_i   = SHA-512(IV || cipher_i)             ← hex string
  sig_i    = RSA-PSS/SHA-512(hash_i || seq || ts)
  Gửi: { iv, cipher, hash, sig, timestamp, seq }

Receiver (mỗi đoạn):
  1. Kiểm tra seq không trùng & đúng thứ tự
  2. Tính lại SHA-512(IV || cipher) → so sánh hash → NACK nếu sai
  3. Xác minh chữ ký RSA-PSS → NACK nếu sai
  4. Giải mã 3DES_CBC → lưu segment
  5. Gửi ACK_PART

Sau đủ 3 đoạn:
  Ghép segment_1 + segment_2 + segment_3 → received_recording.mp3
  Gửi ACK_COMPLETE
```

### Sơ Đồ Gói Tin (Đề Bài)
```json
{
  "iv":     "<Base64>",
  "cipher": "<Base64>",
  "hash":   "<hex SHA-512>",
  "sig":    "<Base64 RSA-PSS Signature>"
}
```

---

## ⚡ HIỆU NĂNG TRIPLE DES (đo thực tế)

| Kích thước | Mã hóa | Giải mã | Tổng |
|---|---|---|---|
| 10 KB  | ~0.001 s | ~0.002 s | ~0.003 s |
| 1 MB   | ~0.035 s | ~0.031 s | ~0.066 s |
| 10 MB  | ~0.329 s | ~0.312 s | ~0.641 s |

---

## ❗ LỖI THƯỜNG GẶP & CÁCH SỬA

| Lỗi | Nguyên nhân | Cách xử lý |
|---|---|---|
| `OSError: [WinError 10048]` | Cổng đang bị chiếm | Tắt cửa sổ cũ hoặc chờ 30s |
| `FileNotFoundError: sender_private.pem` | Chưa sinh khóa | Chạy `python sinh_khoa.py` |
| `Không tìm thấy file recording.mp3` | Chưa có file mẫu | Chạy `python tao_mp3_ao.py` |
| Người Nhận chưa bật mà Gửi đã kết nối | Sai thứ tự | Bật Receiver TRƯỚC, rồi mới bật Sender |
| Bắt tay thất bại khi qua Proxy | Receiver chưa bật khi Proxy connect | Bật Receiver → Proxy → Sender theo thứ tự |
