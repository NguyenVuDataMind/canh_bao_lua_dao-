from google import genai
from typing import Dict, List, Optional
import logging
import os

logger = logging.getLogger(__name__)

class GeminiExplanationService:
    """Service để tạo explanation bằng Google Gemini"""
    
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.5-flash"):
        """
        Initialize Gemini service với SDK mới
        
        Args:
            api_key: Google AI API key
            model_name: Model name ("gemini-2.5-flash", "gemini-pro", "gemini-ultra")
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model_name
        
        if not self.api_key:
            logger.warning("No Gemini API key provided. Explanation service will be disabled.")
            self.client = None
        else:
            try:
                self.client = genai.Client(api_key=self.api_key)
                logger.info(f"Gemini client initialized with model: {model_name}")
            except Exception as e:
                logger.error(f"Error initializing Gemini: {str(e)}", exc_info=True)
                self.client = None
    
    def explain(self,
                text: str,
                classification: Dict,
                detected_urls: List[str] = None,
                detected_phones: List[str] = None) -> str:
        """
        Tạo explanation bằng Gemini
        
        Args:
            text: Text đã được làm sạch
            classification: Kết quả từ PhoBERT (dict với is_scam, score, label)
            detected_urls: List URL phát hiện được
            detected_phones: List số điện thoại phát hiện được
            
        Returns:
            Explanation string bằng tiếng Việt
        """
        if not self.client:
            return self._fallback_explanation(classification, detected_urls, detected_phones)
        
        try:
            # Tạo prompt
            prompt = self._create_prompt(text, classification, detected_urls, detected_phones)
            
            # Generate explanation
            logger.info("Generating explanation with Gemini...")
            
            # Generate content với Gemini
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
            )
            
            # Lấy text từ response
            explanation = response.text.strip() if hasattr(response, 'text') else str(response).strip()
            logger.info("Explanation generated successfully")
            return explanation
            
        except Exception as e:
            logger.error(f"Error generating explanation: {str(e)}", exc_info=True)
            return self._fallback_explanation(classification, detected_urls, detected_phones)
    
    def _create_prompt(self,
                      text: str,
                      classification: Dict,
                      detected_urls: List[str],
                      detected_phones: List[str]) -> str:
        """Tạo prompt cho Gemini"""
        is_scam = classification.get('is_scam', False)
        score = classification.get('score', 0.0)
        label = classification.get('label', '')
        
        urls_str = ", ".join(detected_urls) if detected_urls else "Không có"
        phones_str = ", ".join(detected_phones) if detected_phones else "Không có"
        
        # Tạo prompt chi tiết
        prompt = f"""Bạn là chuyên gia phân tích tin nhắn lừa đảo. Hãy giải thích bằng tiếng Việt một cách rõ ràng và dễ hiểu.

Tin nhắn: "{text[:500]}"

Kết quả phân loại:
- Phân loại: {label}
- Độ tin cậy: {score:.1%}
- URL phát hiện: {urls_str}
- Số điện thoại phát hiện: {phones_str}

Hãy giải thích:
1. Tại sao tin nhắn này {"là lừa đảo" if is_scam else "không phải lừa đảo"}?
2. Các dấu hiệu cụ thể nào cho thấy điều này?
3. Lời khuyên ngắn gọn cho người nhận tin nhắn này (1-2 câu).

Trả lời bằng tiếng Việt, ngắn gọn (2-3 câu), dễ hiểu cho người dùng bình thường:"""
        
        return prompt
    
    def _fallback_explanation(self,
                              classification: Dict,
                              detected_urls: List[str] = None,
                              detected_phones: List[str] = None) -> str:
        """Fallback explanation nếu Gemini không available"""
        is_scam = classification.get('is_scam', False)
        score = classification.get('score', 0.0)
        
        if is_scam:
            reasons = []
            if detected_urls:
                reasons.append(f"phát hiện {len(detected_urls)} URL đáng ngờ")
            if detected_phones:
                reasons.append(f"có số điện thoại lạ")
            
            reason_text = ", ".join(reasons) if reasons else "có dấu hiệu lừa đảo"
            return f"⚠️ Tin nhắn này có dấu hiệu LỪA ĐẢO (độ tin cậy: {score:.1%}). Lý do: {reason_text}. Hãy cẩn thận và không bấm vào link hoặc chuyển tiền."
        else:
            return f"✅ Tin nhắn này không có dấu hiệu lừa đảo rõ ràng (độ tin cậy: {score:.1%}). Tuy nhiên, hãy luôn cẩn thận với các yêu cầu chuyển tiền hoặc link lạ."

