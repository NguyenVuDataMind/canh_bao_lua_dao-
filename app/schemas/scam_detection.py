from pydantic import BaseModel
from typing import List, Optional

class TextExtractionResponse(BaseModel):
    """Response schema cho text extraction từ ảnh"""
    extracted_text: str
    cleaned_text: str
    detected_urls: List[str]
    detected_phones: List[str]
    detected_emails: List[str]
    cleaning_stats: dict

