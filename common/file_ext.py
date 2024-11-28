import os


def get_file_extension(file_name):
    """
    Hàm lấy đuôi file từ tên file.

    Args:
        file_name (str): Tên file (có thể từ request.FILES).

    Returns:
        str: Đuôi file (bao gồm dấu chấm), hoặc chuỗi rỗng nếu không có đuôi.
    """
    return os.path.splitext(file_name)[1]  # Trả về phần mở rộng (đuôi file)