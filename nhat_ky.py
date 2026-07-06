import logging

def thiet_lap_nhat_ky(ten, file_nhat_ky, cap_do=logging.INFO):
    """
    Hàm thiết lập logger ghi nhật ký hệ thống ra file log với mã hóa UTF-8.
    Dùng để theo dõi chi tiết quá trình bắt tay, mã hóa, ký số và truyền nhận.
    """
    dinh_dang = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    bo_xu_ly = logging.FileHandler(file_nhat_ky, encoding='utf-8')        
    bo_xu_ly.setFormatter(dinh_dang)

    logger = logging.getLogger(ten)
    logger.setLevel(cap_do)
    logger.addHandler(bo_xu_ly)

    return logger
