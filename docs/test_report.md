# Test Report

## 1. Test Chức Năng (Normal Test)
- Gửi file bình thường.
- Nhận đủ 3 đoạn.
- Ghép lại đúng.
- File đầu ra giống file gốc.
**Kết quả**: PASS.

## 2. Test Bảo Mật (Tamper Test)
- Sửa 1 byte trong ciphertext (Part 2).
- Bên nhận kiểm tra mã băm SHA-512 thất bại.
- Trả về NACK với lỗi "Hash mismatch".
**Kết quả**: PASS.

## 3. Test Bảo Mật (Replay Test)
- Giả lập tấn công gửi lại (replay attack) bằng cách dùng timestamp cũ (quá hạn).
- Bên nhận kiểm tra timestamp và từ chối.
- Trả về NACK với lỗi "Timestamp expired".
**Kết quả**: PASS.
