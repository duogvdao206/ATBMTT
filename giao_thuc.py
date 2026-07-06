import json
import struct

# Định nghĩa các hằng số phản hồi (ACK/NACK)
ACK_HANDSHAKE = "ACK_HANDSHAKE"
ACK_META = "ACK_META"
ACK_PART = "ACK_PART"
ACK_COMPLETE = "ACK_COMPLETE"

NACK_INTEGRITY = "NACK_INTEGRITY"
NACK_SIGNATURE = "NACK_SIGNATURE"
NACK_REPLAY = "NACK_REPLAY"
NACK_KEY_ERROR = "NACK_KEY_ERROR"

def gui_tin_nhan(sock, tin_nhan):
    """
    Gửi tin nhắn dạng JSON qua Socket.
    Độ dài tin nhắn được gửi trước dưới dạng 4 byte (big-endian) để người nhận biết trước kích thước gói tin.
    """
    du_lieu = json.dumps(tin_nhan).encode('utf-8')
    do_dai = len(du_lieu)
    sock.sendall(struct.pack('!I', do_dai) + du_lieu)

def nhan_tin_nhan(sock):
    """
    Nhận tin nhắn dạng JSON qua Socket.
    Đầu tiên đọc 4 byte để xác định kích thước gói tin, sau đó đọc toàn bộ nội dung.
    """
    try:
        do_dai_goc = sock.recv(4)
        if not do_dai_goc: return None
        do_dai_tin = struct.unpack('!I', do_dai_goc)[0]
        
        cac_phan = []
        so_byte_da_nhan = 0
        while so_byte_da_nhan < do_dai_tin:
            phan = sock.recv(min(do_dai_tin - so_byte_da_nhan, 4096))
            if not phan: break
            cac_phan.append(phan)
            so_byte_da_nhan += len(phan)
        
        du_lieu = b"".join(cac_phan)
        return json.loads(du_lieu.decode('utf-8'))
    except Exception:
        return None
