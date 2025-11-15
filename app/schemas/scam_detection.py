from pydantic import BaseModel
from typing import List, Optional, Dict

class ScamClassification(BaseModel):
    """Kết quả phân loại lừa đảo từ PhoBERT"""
    is_scam: bool
    score: float  # Confidence score (0-1)
    label: str  # "lừa đảo" hoặc "không lừa đảo"
    probabilities: Dict[str, float]  # Xác suất cho từng class
    explanation: Optional[str] = None  # Giải thích tại sao lừa đảo/không lừa đảo (từ Gemini)

class TextExtractionResponse(BaseModel):
    """Response schema cho text extraction từ ảnh"""
    extracted_text: str
    cleaned_text: str
    detected_urls: List[str]
    detected_phones: List[str]
    detected_emails: List[str]
    cleaning_stats: dict
    classification: Optional[ScamClassification] = None  # Kết quả phân loại từ PhoBERT

