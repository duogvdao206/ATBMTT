Đề tài 7: Gửi tập tin âm thanh chia thành nhiều đoạn 
Mô tả: Một nhà sản xuất âm thanh gửi file recording.mp3 chứa bản ghi âm quan 
trọng đến studio, chia thành 3 đoạn để đảm bảo truyền an toàn qua mạng không ổn định. 
File được mã hóa và ký số để bảo vệ nội dung, với tính toàn vẹn được kiểm tra nhằm 
ngăn chặn sửa đổi trái phép. 
Yêu cầu: 
Mã hóa: Triple DES 
Trao khóa & ký số: RSA 2048-bit (OAEP + SHA-512) 
Kiểm tra tính toàn vẹn: SHA-512 
Luồng xử lý: 
Handshake: Người gửi gửi "Hello!". Người nhận trả lời "Ready!". 
Xác thực & Trao khóa: Người gửi ký metadata (tên file + timestamp + thời lượng) 
bằng RSA/SHA-512. Người gửi mã hóa SessionKey bằng RSA 2048-bit (OAEP) và gửi. 
Mã hóa & Kiểm tra toàn vẹn: Tạo IV. Chia file thành 3 đoạn, mã hóa mỗi đoạn 
bằng Triple DES. Tính hash: SHA-512(IV || ciphertext) cho mỗi đoạn. Gói tin gửi (mỗi 
đoạn): { "iv": "<Base64>", "cipher": "<Base64>", "hash": "<hex>", "sig": "<Signature>" 
} 
Phía Người nhận: Kiểm tra hash và chữ ký mỗi đoạn. Nếu tất cả hợp lệ: Giải mã 
từng đoạn bằng Triple DES, ghép và lưu file recording.mp3, gửi ACK tới Người gửi. 
Ngược lại nếu hash hoặc chữ ký không hợp lệ: Từ chối, gửi NACK (lỗi integrity) tới 
Người gửi. 