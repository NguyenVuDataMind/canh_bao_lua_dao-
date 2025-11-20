from google import genai
from typing import Dict, List, Optional
import logging
import os
import json
import re

logger = logging.getLogger(__name__)

class GeminiExplanationService:
    """Service để phân loại lừa đảo và giải thích bằng Google Gemini"""
    
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
            logger.warning("No Gemini API key provided. Gemini service will be disabled.")
            self.client = None
        else:
            try:
                self.client = genai.Client(api_key=self.api_key)
                logger.info(f"Gemini client initialized with model: {model_name}")
            except Exception as e:
                logger.error(f"Error initializing Gemini: {str(e)}", exc_info=True)
                self.client = None
    
    def classify_and_explain(self,
                           text: str,
                           detected_urls: List[str] = None,
                           detected_phones: List[str] = None) -> Dict:
        """
        Phân loại lừa đảo và tạo explanation bằng Gemini (một lần gọi)
        
        Args:
            text: Text cần phân loại
            detected_urls: List URL phát hiện được (optional)
            detected_phones: List số điện thoại phát hiện được (optional)
            
        Returns:
            Dict với keys:
                - is_scam: bool - Có lừa đảo không
                - scam_points: List[str] - Các điểm lừa đảo (nếu có)
                - scam_topic: str - Chủ đề lừa đảo (nếu có)
                - recommendations: str - Nên làm gì trong trường hợp lừa đảo này (nếu có)
                - why_not_scam: str - Vì sao không lừa đảo (nếu không lừa đảo)
                - conversation_topic: str - Đây là cuộc trò chuyện về gì (nếu không lừa đảo)
        """
        if not self.client:
            return self._fallback_classification(detected_urls, detected_phones)
        
        if not text or len(text.strip()) == 0:
            return {
                "is_scam": False,
                "scam_points": [],
                "scam_topic": "",
                "recommendations": "",
                "why_not_scam": "Không có text để phân tích.",
                "conversation_topic": "Không xác định được"
            }
        
        try:
            # Tạo prompt cho Gemini để phân loại và giải thích
            prompt = self._create_classification_prompt(text, detected_urls, detected_phones)
            
            logger.info("Classifying and explaining with Gemini...")
            
            # Generate content với Gemini
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
            )
            
            # Lấy text từ response
            response_text = response.text.strip() if hasattr(response, 'text') else str(response).strip()
            
            # Parse response từ Gemini
            classification = self._parse_gemini_response(response_text)
            
            logger.info(f"Classification result: {'lừa đảo' if classification['is_scam'] else 'không lừa đảo'}")
            return classification
            
        except Exception as e:
            logger.error(f"Error in Gemini classification: {str(e)}", exc_info=True)
            return self._fallback_classification(detected_urls, detected_phones)
    
    def _create_classification_prompt(self,
                                     text: str,
                                     detected_urls: List[str] = None,
                                     detected_phones: List[str] = None) -> str:
        """Tạo prompt cho Gemini để phân loại và giải thích"""
        urls_str = ", ".join(detected_urls) if detected_urls else "Không có"
        phones_str = ", ".join(detected_phones) if detected_phones else "Không có"
        
        prompt = f"""Bạn là chuyên gia phân tích tin nhắn lừa đảo. Hãy phân tích tin nhắn sau và trả lời CHỈ bằng JSON, không có text nào khác.

Tin nhắn: "{text[:1000]}"

Thông tin bổ sung:
- URL phát hiện: {urls_str}
- Số điện thoại phát hiện: {phones_str}

QUAN TRỌNG: Trả lời CHỈ bằng JSON sau đây, không có text giải thích thêm:

{{
    "is_scam": false,
    "scam_points": [],
    "scam_topic": "",
    "recommendations": "",
    "why_not_scam": "Giải thích vì sao không lừa đảo",
    "conversation_topic": "Mô tả cuộc trò chuyện này về gì"
}}

Nếu LỪA ĐẢO, trả về:
{{
    "is_scam": true,
    "scam_points": ["điểm lừa đảo 1", "điểm lừa đảo 2"],
    "scam_topic": "Chủ đề lừa đảo (ví dụ: lừa đảo tài chính, phishing, mạo danh)",
    "recommendations": "Nên làm gì trong trường hợp này",
    "why_not_scam": "",
    "conversation_topic": ""
}}

Quy tắc phân tích:
1. Quiz, câu hỏi giáo dục, thông báo chính thức → KHÔNG phải lừa đảo
2. Chỉ đánh dấu lừa đảo nếu có: yêu cầu chuyển tiền, link đáng ngờ, mạo danh, lừa đảo tình cảm
3. scam_points: danh sách các điểm cụ thể cho thấy lừa đảo
4. scam_topic: chủ đề lừa đảo (ví dụ: "Lừa đảo tài chính", "Phishing", "Mạo danh ngân hàng")
5. recommendations: lời khuyên cụ thể nên làm gì (ví dụ: "Không bấm vào link", "Không chuyển tiền")
6. why_not_scam: giải thích rõ ràng vì sao không lừa đảo
7. conversation_topic: mô tả cuộc trò chuyện này về gì (ví dụ: "Thông báo từ ngân hàng", "Câu hỏi quiz giáo dục")

Trả lời CHỈ bằng JSON:"""
        
        return prompt
    
    def _parse_gemini_response(self, response_text: str) -> Dict:
        """Parse response từ Gemini thành dict classification"""
        try:
            # Tìm JSON trong response (có thể có text thêm trước/sau)
            json_matches = list(re.finditer(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL))
            if json_matches:
                # Lấy JSON block lớn nhất
                json_match = max(json_matches, key=lambda m: len(m.group(0)))
                json_str = json_match.group(0)
                data = json.loads(json_str)
            else:
                # Nếu không tìm thấy JSON, thử parse toàn bộ response
                data = json.loads(response_text.strip())
            
            # Validate và normalize
            is_scam = bool(data.get('is_scam', False))
            scam_points = data.get('scam_points', [])
            scam_topic = str(data.get('scam_topic', ''))
            recommendations = str(data.get('recommendations', ''))
            why_not_scam = str(data.get('why_not_scam', ''))
            conversation_topic = str(data.get('conversation_topic', ''))
            
            # Đảm bảo scam_points là list
            if not isinstance(scam_points, list):
                scam_points = []
            
            # Đảm bảo các field string không rỗng nếu cần
            if is_scam:
                if not scam_topic:
                    scam_topic = "Lừa đảo"
                if not recommendations:
                    recommendations = "Hãy cẩn thận và không thực hiện các yêu cầu trong tin nhắn."
            else:
                if not why_not_scam:
                    why_not_scam = "Tin nhắn này không có dấu hiệu lừa đảo rõ ràng."
                if not conversation_topic:
                    conversation_topic = "Không xác định được"
            
            return {
                "is_scam": is_scam,
                "scam_points": scam_points,
                "scam_topic": scam_topic,
                "recommendations": recommendations,
                "why_not_scam": why_not_scam,
                "conversation_topic": conversation_topic
            }
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Could not parse Gemini response as JSON: {e}")
            logger.warning(f"Response text: {response_text[:200]}")
            
            # Fallback: Phân tích text response để tìm is_scam
            response_lower = response_text.lower()
            is_scam = any(keyword in response_lower for keyword in ['lừa đảo', 'scam', 'fraud', 'phishing'])
            
            if is_scam:
                return {
                    "is_scam": True,
                    "scam_points": ["Có dấu hiệu lừa đảo trong tin nhắn"],
                    "scam_topic": "Lừa đảo",
                    "recommendations": "Hãy cẩn thận và không thực hiện các yêu cầu trong tin nhắn.",
                    "why_not_scam": "",
                    "conversation_topic": ""
                }
            else:
                return {
                    "is_scam": False,
                    "scam_points": [],
                    "scam_topic": "",
                    "recommendations": "",
                    "why_not_scam": response_text[:500] if response_text else "Không thể phân tích tin nhắn này.",
                    "conversation_topic": "Không xác định được"
                }
    
    def _fallback_classification(self,
                                 detected_urls: List[str] = None,
                                 detected_phones: List[str] = None) -> Dict:
        """Fallback classification nếu Gemini không available"""
        is_scam = bool(detected_urls or detected_phones)
        if is_scam:
            return {
                "is_scam": True,
                "scam_points": ["Phát hiện URL hoặc số điện thoại đáng ngờ"],
                "scam_topic": "Lừa đảo",
                "recommendations": "Hãy cẩn thận với các link và số điện thoại lạ. Không bấm vào link hoặc chuyển tiền.",
                "why_not_scam": "",
                "conversation_topic": ""
            }
        else:
            return {
                "is_scam": False,
                "scam_points": [],
                "scam_topic": "",
                "recommendations": "",
                "why_not_scam": "Không thể phân tích với Gemini. Hãy cẩn thận với các link và số điện thoại lạ.",
                "conversation_topic": "Không xác định được"
            }

