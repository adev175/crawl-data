def convert_day_to_vietnamese(day: str) -> str:
    """Chuyển thứ tiếng Anh sang tiếng Việt."""
    mapping = {
        "Monday": "Thứ Hai",
        "Tuesday": "Thứ Ba",
        "Wednesday": "Thứ Tư",
        "Thursday": "Thứ Năm",
        "Friday": "Thứ Sáu",
        "Saturday": "Thứ Bảy",
        "Sunday": "Chủ Nhật",
    }
    return mapping.get(day, day)
