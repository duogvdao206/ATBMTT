# Threat Model
## Tài sản cần bảo vệ
- File mp3
- Session key
- Metadata

## Tác nhân tấn công
- Kẻ nghe lén mạng
- Kẻ sửa đổi dữ liệu (tamper)
- Kẻ gửi lại dữ liệu (replay)
- Kẻ giả mạo

## Nguy cơ
- Lộ nội dung file -> Chống lại bằng Triple DES
- Sai lệch nội dung -> Chống lại bằng SHA-512 Hash và RSA Signature
- Gửi lại gói tin cũ -> Chống lại bằng Timestamp và Sequence Number
- Giả mạo người gửi -> Chống lại bằng RSA Signature
