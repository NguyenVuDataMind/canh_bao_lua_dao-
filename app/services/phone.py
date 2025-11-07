def normalize_phone(phone: str) -> str:
    phone = phone.strip().replace(" ", "")
    if phone.startswith("+84"):
        phone = "0" + phone[3:]
    return phone