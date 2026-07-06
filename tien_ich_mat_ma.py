import os
from Crypto.PublicKey import RSA
from Crypto.Cipher import DES3, PKCS1_OAEP
from Crypto.Hash import SHA512
from Crypto.Signature import pss
from Crypto.Util.Padding import pad, unpad

def tao_khoa_rsa(tien_to_ten_file):
    """
    Sinh cặp khóa RSA 2048-bit cho Người gửi/Người nhận.
    Gồm khóa bí mật (_private.pem) và khóa công khai (_public.pem).
    """
    khoa = RSA.generate(2048)
    khoa_bi_mat = khoa.export_key()
    with open(f"{tien_to_ten_file}_private.pem", "wb") as f:
        f.write(khoa_bi_mat)

    khoa_cong_khai = khoa.publickey().export_key()
    with open(f"{tien_to_ten_file}_public.pem", "wb") as f:
        f.write(khoa_cong_khai)

def tai_khoa_rsa(ten_file):
    """
    Tải khóa RSA từ file .pem lên bộ nhớ để sử dụng.
    """
    with open(ten_file, "rb") as f:
        return RSA.import_key(f.read())

def ma_hoa_rsa(khoa_cong_khai, du_lieu):
    """
    Mã hóa dữ liệu (thường là khóa phiên Triple DES) bằng khóa công khai RSA của người nhận.
    Sử dụng cơ chế PKCS1_OAEP kết hợp mã băm SHA-512 để bảo vệ tối đa dữ liệu khóa.
    """
    cipher_rsa = PKCS1_OAEP.new(khoa_cong_khai, hashAlgo=SHA512.new())
    return cipher_rsa.encrypt(du_lieu)

def giai_ma_rsa(khoa_bi_mat, du_lieu_ma_hoa):
    """
    Giải mã dữ liệu bằng khóa bí mật RSA của người nhận.
    Sử dụng PKCS1_OAEP cùng mã băm SHA-512.
    """
    cipher_rsa = PKCS1_OAEP.new(khoa_bi_mat, hashAlgo=SHA512.new())
    return cipher_rsa.decrypt(du_lieu_ma_hoa)

def ky_so_rsa(khoa_bi_mat, du_lieu):
    """
    Ký số dữ liệu bằng khóa bí mật RSA.
    Sử dụng lược đồ ký PSS (Probabilistic Signature Scheme) cùng mã băm SHA-512.
    Đảm bảo tính toàn vẹn và xác thực nguồn gốc (Không thể chối bỏ).
    """
    h = SHA512.new(du_lieu)
    chu_ky = pss.new(khoa_bi_mat).sign(h)
    return chu_ky

def xac_minh_chu_ky_rsa(khoa_cong_khai, du_lieu, chu_ky):
    """
    Xác minh chữ ký số của dữ liệu bằng khóa công khai RSA.
    Trả về True nếu chữ ký hợp lệ, False nếu không hợp lệ.
    """
    h = SHA512.new(du_lieu)
    nguoi_xac_minh = pss.new(khoa_cong_khai)
    try:
        nguoi_xac_minh.verify(h, chu_ky)
        return True
    except (ValueError, TypeError):
        return False

def tao_khoa_phien():
    """
    Sinh ngẫu nhiên khóa phiên 24 bytes (192 bits) cho Triple DES (3DES).
    Đồng thời hiệu chỉnh tính chẵn lẻ (parity check) của khóa để phù hợp với chuẩn DES3.
    """
    return DES3.adjust_key_parity(os.urandom(24))

def ma_hoa_des3(khoa, du_lieu):
    """
    Mã hóa dữ liệu bằng Triple DES chế độ CBC.
    Sinh ngẫu nhiên vector khởi tạo IV (8 bytes).
    Dữ liệu được đệm (padding) theo chuẩn PKCS7 trước khi mã hóa.
    """
    iv = os.urandom(8)
    cipher = DES3.new(khoa, DES3.MODE_CBC, iv)
    ct_bytes = cipher.encrypt(pad(du_lieu, DES3.block_size))
    return iv, ct_bytes

def giai_ma_des3(khoa, iv, du_lieu_ma_hoa):
    """
    Giải mã dữ liệu bằng Triple DES chế độ CBC.
    Sử dụng IV và khóa phiên, sau đó loại bỏ phần đệm (unpadding).
    """
    cipher = DES3.new(khoa, DES3.MODE_CBC, iv)
    pt = unpad(cipher.decrypt(du_lieu_ma_hoa), DES3.block_size)
    return pt

def tinh_toan_hash(iv, du_lieu_ma_hoa):
    """
    Tính mã băm SHA-512 của dữ liệu mã hóa kết hợp với IV để kiểm tra tính toàn vẹn gói tin.
    Công thức: SHA-512(IV || ciphertext)
    """
    h = SHA512.new()
    h.update(iv + du_lieu_ma_hoa)
    return h.digest()
