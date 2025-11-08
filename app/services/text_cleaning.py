import re
import unicodedata
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class TextCleaner:
    """
    Làm sạch text từ OCR output
    - Chuẩn hóa Unicode
    - Loại bỏ emoji, ký tự đặc biệt
    - GIỮ LẠI DẤU TIẾNG VIỆT (ă, â, ê, ô, ơ, ư, đ, và các dấu thanh)
    - Trích xuất URL, số điện thoại, email
    """
    
    def __init__(self):
        # Pattern để tìm URL
        self.url_pattern = re.compile(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        )
        
        # Pattern để tìm số điện thoại Việt Nam
        self.phone_pattern = re.compile(
            r'(\+84|0)[0-9]{9,10}'
        )
        
        # Pattern để tìm email
        self.email_pattern = re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        )
    
    def clean_text(self, text: str) -> str:
        """
        Làm sạch text: loại bỏ emoji, normalize Unicode
        QUAN TRỌNG: Giữ lại dấu tiếng Việt
        
        Args:
            text: Text thô từ OCR
            
        Returns:
            Text đã được làm sạch (vẫn giữ dấu tiếng Việt)
        """
        if not text:
            return ""
        
        try:
            # 1. Normalize Unicode (NFKC: Normalization Form Compatibility Composition)
            # Chuyển các ký tự tương tự về dạng chuẩn
            # QUAN TRỌNG: NFKC giữ lại dấu tiếng Việt
            text = unicodedata.normalize('NFKC', text)
            
            # 2. Loại bỏ emoji (không ảnh hưởng đến dấu tiếng Việt)
            text = self._remove_emoji(text)
            
            # 3. Loại bỏ ký tự điều khiển (control characters)
            # Giữ lại các ký tự tiếng Việt có dấu
            text = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1f\x7f-\x9f]', '', text)
            
            # 4. Chuẩn hóa dấu câu và khoảng trắng
            # Giữ lại: . , ! ? : - ( ) [ ] { } / \
            # Giữ lại tất cả ký tự tiếng Việt (Unicode range)
            # Loại bỏ các ký tự đặc biệt khác như @#$%^&* nhưng giữ trong URL/email
            # Pattern này giữ lại:
            # - Chữ cái (bao gồm tiếng Việt): \w
            # - Khoảng trắng: \s
            # - Dấu câu cơ bản: . , ! ? : - ( ) [ ] { } / \
            # - Ký tự tiếng Việt: ă, â, ê, ô, ơ, ư, đ và các dấu thanh
            
            # Chỉ loại bỏ các ký tự đặc biệt không phải dấu câu cơ bản
            # Giữ lại tất cả ký tự Unicode hợp lệ cho tiếng Việt
            text = re.sub(r'[^\w\s\.\,\!\?\:\-\(\)\[\]\{\}\/\\]', ' ', text)
            
            # 5. Loại bỏ khoảng trắng thừa
            text = re.sub(r'\s+', ' ', text)  # Nhiều space thành 1 space
            text = re.sub(r'\n\s*\n', '\n', text)  # Nhiều newline thành 1 newline
            
            # 6. Trim đầu cuối
            text = text.strip()
            
            logger.info(f"Cleaned text length: {len(text)} characters")
            return text
            
        except Exception as e:
            logger.error(f"Error cleaning text: {str(e)}")
            return text  # Trả về text gốc nếu có lỗi
    
    def _remove_emoji(self, text: str) -> str:
        """
        Loại bỏ emoji khỏi text
        QUAN TRỌNG: Không ảnh hưởng đến dấu tiếng Việt
        
        Args:
            text: Text có thể chứa emoji
            
        Returns:
            Text không còn emoji (vẫn giữ dấu tiếng Việt)
        """
        # Pattern để match emoji
        # Chỉ match các range emoji, không match ký tự tiếng Việt
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map
            "\U0001F1E0-\U0001F1FF"  # flags
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "\U0001F900-\U0001F9FF"  # supplemental symbols
            "\U00002600-\U000026FF"  # miscellaneous symbols
            "\U00002700-\U000027BF"  # dingbats
            "]+", 
            flags=re.UNICODE
        )
        
        return emoji_pattern.sub('', text)
    
    def extract_urls(self, text: str) -> List[str]:
        """
        Trích xuất URLs từ text
        
        Args:
            text: Text cần tìm URL
            
        Returns:
            List các URL tìm được
        """
        urls = self.url_pattern.findall(text)
        # Loại bỏ duplicate và sort
        unique_urls = list(set(urls))
        logger.info(f"Found {len(unique_urls)} URLs")
        return unique_urls
    
    def extract_phones(self, text: str) -> List[str]:
        """
        Trích xuất số điện thoại từ text
        
        Args:
            text: Text cần tìm số điện thoại
            
        Returns:
            List các số điện thoại tìm được
        """
        phones = self.phone_pattern.findall(text)
        # Normalize: chuyển +84 thành 0
        normalized_phones = []
        for phone in phones:
            if isinstance(phone, tuple):
                phone = phone[0] if phone[0] else phone[1]
            if phone.startswith('+84'):
                normalized = '0' + phone[3:]
            else:
                normalized = phone
            normalized_phones.append(normalized)
        
        # Loại bỏ duplicate
        unique_phones = list(set(normalized_phones))
        logger.info(f"Found {len(unique_phones)} phone numbers")
        return unique_phones
    
    def extract_emails(self, text: str) -> List[str]:
        """
        Trích xuất email từ text
        
        Args:
            text: Text cần tìm email
            
        Returns:
            List các email tìm được
        """
        emails = self.email_pattern.findall(text)
        unique_emails = list(set(emails))
        logger.info(f"Found {len(unique_emails)} emails")
        return unique_emails
    
    def get_cleaning_stats(self, original_text: str, cleaned_text: str) -> Dict:
        """
        Thống kê quá trình làm sạch
        
        Args:
            original_text: Text gốc
            cleaned_text: Text đã làm sạch
            
        Returns:
            Dictionary chứa thống kê
        """
        return {
            'original_length': len(original_text),
            'cleaned_length': len(cleaned_text),
            'removed_chars': len(original_text) - len(cleaned_text),
            'urls_found': len(self.extract_urls(cleaned_text)),
            'phones_found': len(self.extract_phones(cleaned_text)),
            'emails_found': len(self.extract_emails(cleaned_text))
        }
    
    def preserve_vietnamese_accents(self, text: str) -> str:
        """
        Đảm bảo giữ lại dấu tiếng Việt
        (Hàm helper để kiểm tra)
        
        Args:
            text: Text cần kiểm tra
            
        Returns:
            Text với dấu tiếng Việt được giữ nguyên
        """
        # Pattern để match ký tự tiếng Việt có dấu
        vietnamese_pattern = re.compile(
            r'[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđĐ]',
            re.IGNORECASE
        )
        
        # Kiểm tra xem có ký tự tiếng Việt không
        has_vietnamese = bool(vietnamese_pattern.search(text))
        
        if has_vietnamese:
            logger.info("Text contains Vietnamese characters with accents - preserved")
        
        return text

