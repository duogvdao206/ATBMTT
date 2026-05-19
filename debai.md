Hãy xây dựng mô phỏng hệ thống truyền file âm thanh an toàn theo các yêu cầu sau:

Đề tài:
Gửi tập tin âm thanh recording.mp3 được chia thành nhiều đoạn để truyền qua mạng không ổn định.

Mục tiêu:

* Đảm bảo bảo mật dữ liệu
* Đảm bảo toàn vẹn dữ liệu
* Xác thực người gửi
* Phát hiện chỉnh sửa trái phép

Yêu cầu kỹ thuật:

1. Thuật toán sử dụng

* Mã hóa dữ liệu: Triple DES
* Trao khóa: RSA 2048-bit dùng OAEP padding
* Chữ ký số: RSA + SHA-512
* Kiểm tra toàn vẹn: SHA-512

2. Luồng hoạt động

Bước 1: Handshake

* Người gửi gửi: "Hello!"
* Người nhận phản hồi: "Ready!"

Bước 2: Xác thực và trao khóa

* Metadata gồm:

  * filename
  * timestamp
  * duration
* Người gửi:

  * Tạo SessionKey cho Triple DES
  * Ký metadata bằng RSA private key + SHA-512
  * Mã hóa SessionKey bằng RSA public key của người nhận với OAEP
* Gửi:
  {
  "metadata": "...",
  "metadata_signature": "...",
  "encrypted_session_key": "..."
  }

Bước 3: Chia và mã hóa file

* Chia recording.mp3 thành 3 phần bằng nhau
* Mỗi phần:

  * Tạo IV riêng
  * Mã hóa bằng Triple DES CBC mode
  * Tính hash:
    SHA-512(IV || ciphertext)
  * Ký hash bằng RSA private key

Gói tin mỗi đoạn:
{
"iv": "<Base64>",
"cipher": "<Base64>",
"hash": "<hex>",
"sig": "<Signature>"
}

Bước 4: Phía người nhận

* Giải mã SessionKey bằng RSA private key
* Với từng đoạn:

  * Kiểm tra hash
  * Verify chữ ký số
* Nếu tất cả hợp lệ:

  * Giải mã Triple DES
  * Ghép 3 đoạn thành recording.mp3
  * Gửi ACK
* Nếu có lỗi:

  * Từ chối dữ liệu
  * Gửi NACK (Integrity Error)

3. Yêu cầu triển khai

* Viết rõ:

  * Sender
  * Receiver
* Có log từng bước:

  * Handshake
  * Generate key
  * Encrypt
  * Hash
  * Sign
  * Verify
  * Decrypt
  * Merge file
* Encode dữ liệu binary bằng Base64
* Có xử lý ngoại lệ nếu hash/signature sai

4. Kết quả mong muốn

* Chạy mô phỏng hoàn chỉnh
* Sau khi nhận:

  * File recording.mp3 được khôi phục chính xác
* Nếu sửa dữ liệu:

  * Hệ thống phát hiện lỗi integrity và trả NACK

5. Công nghệ đề xuất

* Python
* pycryptodome
* hashlib
* base64
* json
* os

Hãy viết:

* Kiến trúc hệ thống
* Giải thích từng bước
* Source code đầy đủ
* Có comment rõ ràng
* Có ví dụ output khi chạy chương trình
