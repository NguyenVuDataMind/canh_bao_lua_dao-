from pydantic import BaseModel, Field
from typing import List, Optional, Dict

from app.schemas.whitelist import URLWhitelistMatchResult

class ScamClassification(BaseModel):
    """Kết quả phân loại lừa đảo từ Gemini"""
    is_scam: bool
    scam_points: List[str] = Field(default_factory=list)  # Các điểm lừa đảo (nếu có)
    scam_topic: str = ""  # Chủ đề lừa đảo (nếu có)
    recommendations: str = ""  # Nên làm gì trong trường hợp lừa đảo này (nếu có)
    why_not_scam: str = ""  # Vì sao không lừa đảo (nếu không lừa đảo)
    conversation_topic: str = ""  # Đây là cuộc trò chuyện về gì (nếu không lừa đảo)

class TextExtractionResponse(BaseModel):
    """Response schema cho text extraction từ ảnh"""
    extracted_text: str
    cleaned_text: str
    detected_urls: List[str]
    detected_phones: List[str]
    detected_emails: List[str]
    cleaning_stats: dict
    classification: Optional[ScamClassification] = None  # Kết quả phân loại từ Gemini
    whitelist_results: List[URLWhitelistMatchResult] = Field(default_factory=list)

