# Cấu hình hệ thống truyền file âm thanh an toàn
HOST = '127.0.0.1'
PORT = 65432
EAVESDROPPER_PORT = 65433
BUFFER_SIZE = 4096
MAX_TIME_DIFF = 60 # Khoảng thời gian lệch tối đa (giây) để chống tấn công phát lại (replay attack)
