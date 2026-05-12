Dưới đây là toàn bộ cách làm cho Đề tài 7: Gửi tập tin âm thanh chia thành nhiều đoạn theo đúng yêu cầu đề bài: file recording.mp3, chia 3 đoạn, Triple DES, RSA 2048-bit (OAEP + SHA-512), SHA-512, có Hello!/Ready!, có ACK/NACK, có kiểm tra hash + chữ ký, và bắt buộc có thêm threat model, anti-replay, log, test bảo mật, benchmark, GitHub, video demo.
1) Chọn hướng làm
Nên làm bằng Python vì đề tài cho phép dùng Python và có sẵn thư viện phù hợp: pycryptodome cho DES/Triple DES/RSA/SHA-512, socket cho giao tiếp mạng, tkinter nếu cần GUI.
Nếu làm đúng theo đề, bạn sẽ có 2 phần chính:
•	Phần giao thức truyền file an toàn: handshake, ký số, trao khóa, mã hóa 3 đoạn, kiểm tra toàn vẹn, ACK/NACK. 
•	Phần báo cáo + kiểm thử: mô tả hệ thống, threat model, test bình thường, test tấn công, benchmark, nhận xét, hướng phát triển. 
2) Cách thiết kế hệ thống
Vai trò từng phía
Người gửi
•	Gửi Hello! 
•	Chờ Ready! 
•	Tạo metadata: tên file + timestamp + duration 
•	Ký metadata bằng RSA/SHA-512 
•	Mã hóa session key bằng RSA 2048-bit OAEP 
•	Chia file thành 3 đoạn 
•	Mỗi đoạn: tạo IV, mã hóa bằng Triple DES, tính hash SHA-512(IV || ciphertext) 
•	Gửi gói tin có iv, cipher, hash, sig 
Người nhận
•	Nhận Hello! → trả Ready! 
•	Kiểm tra chữ ký và hash của từng đoạn 
•	Nếu hợp lệ hết thì giải mã, ghép lại, lưu recording.mp3 
•	Gửi ACK 
•	Nếu sai hash/chữ ký thì từ chối và gửi NACK 
Sơ đồ luồng xử lý nên vẽ trong báo cáo
Bạn nên vẽ 1 Sequence Diagram hoặc Flowchart gồm các bước:
1.	Start 
2.	Handshake 
3.	Gửi metadata + chữ ký 
4.	Trao session key bằng RSA 
5.	Chia file thành 3 đoạn 
6.	Mã hóa từng đoạn bằng Triple DES 
7.	Tính hash từng đoạn 
8.	Gửi từng gói tin 
9.	Bên nhận kiểm tra hash + signature 
10.	Giải mã + ghép file 
11.	ACK/NACK 
Đây là phần bắt buộc trong báo cáo theo yêu cầu “thiết kế giao thức hoặc luồng xử lý”.
3) Cấu trúc chương trình nên làm
Nên chia project thành các file như sau:
project/
│
├─ sender.py
├─ receiver.py
├─ crypto_utils.py
├─ protocol.py
├─ logger.py
├─ config.py
├─ test/
│  ├─ test_normal.py
│  ├─ test_tamper.py
│  ├─ test_replay.py
│  └─ benchmark.py
├─ docs/
│  ├─ threat_model.md
│  ├─ protocol_design.md
│  └─ test_report.md
└─ report/
   └─ final_report.pdf
Cấu trúc như vậy bám đúng yêu cầu báo cáo: có cấu trúc thư mục, file chính, hàm quan trọng, và tách riêng tài liệu bổ trợ trong /docs/. 
4) Thuật toán dùng như thế nào
a) RSA 2048-bit (OAEP + SHA-512)
Dùng cho:
•	ký metadata 
•	mã hóa session key 
Ý nghĩa:
•	RSA dùng cho trao khóa và xác thực 
•	OAEP giúp mã hóa RSA an toàn hơn khi trao khóa 
•	SHA-512 đi kèm trong ký số và băm 
b) Triple DES
Dùng để mã hóa nội dung file theo từng đoạn.
c) SHA-512
Dùng kiểm tra toàn vẹn:
•	hash = SHA-512(IV || ciphertext) 
d) Signature
Mỗi gói có chữ ký số để người nhận kiểm tra nguồn gửi và nội dung không bị sửa.
5) Quy trình làm chi tiết từng bước
Bước 1: Handshake
•	Người gửi mở kết nối 
•	Gửi chuỗi "Hello!" 
•	Người nhận trả "Ready!" 
Mục đích là kiểm tra kết nối đã thông trước khi vào trao đổi thật.
Bước 2: Xác thực và trao khóa
•	Tạo timestamp 
•	Tạo metadata: filename, timestamp, duration 
•	Ký metadata bằng RSA/SHA-512 
•	Tạo session key cho Triple DES 
•	Mã hóa session key bằng RSA OAEP 
•	Gửi sang bên nhận 
Bên nhận phải:
•	giải mã session key bằng private key RSA 
•	kiểm tra chữ ký metadata 
•	kiểm tra timestamp còn hợp lệ 
•	từ chối nếu metadata cũ hoặc sai chữ ký 
Phần này rất quan trọng vì đề bài yêu cầu xác thực và trao đổi khóa rõ ràng.
Bước 3: Chia file và mã hóa
•	Đọc file recording.mp3 thành bytes 
•	Chia làm 3 đoạn gần bằng nhau 
•	Với mỗi đoạn: 
o	tạo IV mới 
o	mã hóa bằng Triple DES 
o	tính hash SHA-512(IV || ciphertext) 
o	ký gói tin hoặc ký phần metadata/gói theo thiết kế bạn chọn 
Bước 4: Gửi gói tin
Mỗi gói nên có dạng:
{
  "part": 1,
  "iv": "Base64...",
  "cipher": "Base64...",
  "hash": "hex...",
  "sig": "Base64...",
  "timestamp": 1710000000,
  "seq": 1
}
Nên thêm seq và timestamp để chống gửi lại, vì phần bổ sung bắt buộc yêu cầu có anti-replay bằng nonce/timestamp/sequence/session_id.
Bước 5: Bên nhận kiểm tra
•	kiểm tra timestamp/seq còn hợp lệ, chưa bị gửi lại 
•	kiểm tra chữ ký 
•	kiểm tra hash 
•	nếu sai một bước thì NACK 
•	nếu đúng hết thì giải mã 
•	ghép 3 đoạn thành file gốc 
•	lưu recording.mp3 
•	gửi ACK 
Bước 6: Xử lý lỗi
Nếu lỗi thì ghi log:
•	lỗi toàn vẹn 
•	lỗi chữ ký 
•	lỗi replay 
•	lỗi quyền truy cập 
•	dữ liệu hết hạn 
Log không được chứa dữ liệu nhạy cảm thô.
6) Cách viết báo cáo
Báo cáo nên theo đúng khung sau:
Chương 1: Giới thiệu bài toán
•	bối cảnh thực tế 
•	lý do phải bảo mật file âm thanh 
•	mục tiêu: bí mật, toàn vẹn, xác thực, sẵn sàng, truy vết 
Chương 2: Phân tích yêu cầu và threat model
•	tài sản cần bảo vệ: file mp3, session key, metadata 
•	tác nhân tấn công: nghe lén, sửa dữ liệu, replay, giả mạo 
•	nguy cơ: lộ file, sai nội dung, gửi lại gói cũ, giả mạo người gửi 
Chương 3: Thiết kế hệ thống
•	kiến trúc client/server 
•	sequence diagram 
•	mô tả luồng handshake → xác thực → truyền dữ liệu → kiểm tra 
Chương 4: Thuật toán và thư viện sử dụng
•	RSA 2048 OAEP + SHA-512 
•	Triple DES 
•	SHA-512 
•	socket 
•	pycryptodome 
Chương 5: Phân tích mã nguồn
•	mô tả từng file 
•	mô tả hàm mã hóa, giải mã, ký, kiểm tra hash, gửi/nhận socket 
Chương 6: Kiểm thử
•	test chạy đúng 
•	test sửa 1 byte ciphertext 
•	test replay 
•	test sai khóa 
•	test sai chữ ký 
•	test hết hạn 
Chương 7: Benchmark
•	so sánh thời gian mã hóa/giải mã 
•	so sánh theo kích thước file 
Chương 8: Kết luận và hướng phát triển
•	ưu điểm 
•	hạn chế 
•	hướng nâng cấp sang AEAD hoặc RSA-PSS nếu muốn mở rộng 
Các phần này bám đúng yêu cầu báo cáo và phần bổ sung mới.
7) Bộ test nên có
Test chức năng
1.	Gửi file bình thường 
2.	Nhận đủ 3 đoạn 
3.	Ghép lại đúng 
4.	File đầu ra giống file gốc 
Test bảo mật
1.	Sửa 1 byte trong ciphertext → phải báo lỗi hash 
2.	Replay gói cũ → phải bị chặn 
3.	Sai private key / sai session key → giải mã thất bại 
4.	Sai chữ ký → từ chối 
5.	Timestamp hết hạn → từ chối 
Đây là đúng yêu cầu kiểm thử bảo mật trong đề bổ sung.
Test benchmark
•	file nhỏ: vài KB 
•	file vừa: vài MB 
•	file lớn: hàng chục MB 
Ghi:
•	thời gian mã hóa 
•	thời gian giải mã 
•	tổng thời gian 
•	dung lượng trước/sau mã hóa 
8) Video demo cần quay gì
Video 5–7 phút nên có 3 đoạn:
1.	Chạy thành công: Hello → Ready → gửi file → ACK 
2.	Demo lỗi bảo mật: sửa ciphertext hoặc replay → NACK 
3.	Mở file output để chứng minh dữ liệu khớp file gốc 
Phần video demo và GitHub là yêu cầu bắt buộc của đề. 
9) GitHub nên sắp xếp thế nào
Trong repo nên có:
•	mã nguồn 
•	README.md 
•	/docs/threat_model.md 
•	/docs/protocol_design.md 
•	/docs/test_report.md 
•	/docs/benchmark_report.md 
•	/report/final_report.pdf 
Lịch sử commit nên thể hiện tiến trình thật:
init project → socket handshake → rsa key exchange → tripledes encrypt → integrity check → anti replay → test cases → benchmark.
10) Nếu thầy cô hỏi “ý tưởng cốt lõi của bài này là gì?”
Bạn trả lời ngắn gọn:
“Bài này xây dựng hệ thống truyền file âm thanh an toàn: dùng handshake để xác nhận kết nối, RSA để trao khóa và ký số, Triple DES để mã hóa 3 đoạn file, SHA-512 để kiểm tra toàn vẹn, rồi bên nhận xác minh trước khi giải mã và ghép file.”
