from fastapi import APIRouter, File, UploadFile, HTTPException, status, Form
from app.deps.db import CurrentAsyncSession
from app.services.vintern_ocr_service import VinternOCRService
from app.services.text_cleaning import TextCleaner
from app.services.gemini_explanation_service import GeminiExplanationService
from app.schemas.scam_detection import TextExtractionResponse
from app.services.url_whitelist import WhitelistService
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/image-processing")

# Initialize services
ocr_service = VinternOCRService(use_gpu=False)
text_cleaner = TextCleaner()

# Initialize Gemini service (lazy load)
gemini_service = None

def get_gemini_service():
    """Lazy load Gemini service"""
    global gemini_service
    if gemini_service is None:
        try:
            gemini_service = GeminiExplanationService(
                api_key=os.getenv("GEMINI_API_KEY"),
                model_name=os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
            )
            logger.info("Gemini service initialized")
        except Exception as e:
            logger.warning(f"Could not load Gemini service: {str(e)}")
            logger.warning("Classification will use fallback")
    return gemini_service

@router.post("/extract-text", response_model=TextExtractionResponse)
async def extract_text_from_image(
    # TODO: Thêm lại authentication sau khi hoàn thành dịch vụ
    # user: CurrentUser,  # ← Uncomment dòng này để bật lại authentication
    session: CurrentAsyncSession,
    image: Optional[UploadFile] = File(None),
    raw_text_input: Optional[str] = Form(None)
):
    """
    Trích xuất text từ ảnh HOẶC nhận text trực tiếp, sau đó phân loại lừa đảo và giải thích:
    1. OCR tiếng Việt (Vintern-1B-v3.5) - nếu có ảnh
    2. Làm sạch text (giữ dấu tiếng Việt)
    3. Phân loại lừa đảo và giải thích (Gemini AI)
    4. Kiểm tra URL với whitelist
    
    **Input options:**
    - `image`: Upload ảnh (multipart/form-data)
    - `raw_text_input`: Nhập text trực tiếp (form-data)
    
    **Lưu ý**: 
    - Phải có ít nhất 1 trong 2: `image` hoặc `raw_text_input`
    - Text trả về sẽ GIỮ NGUYÊN DẤU TIẾNG VIỆT
    - Kết quả phân loại lừa đảo và giải thích được tạo bằng Gemini AI (tiếng Việt, dễ hiểu)
    - Cần GEMINI_API_KEY trong environment variables
    """
    try:
        # Validate input
        if not image and not raw_text_input:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cần upload ảnh (image) hoặc nhập text (raw_text_input)"
            )
        
        raw_text = ""
        
        # Option 1: Extract từ ảnh
        if image:
            # Validate file type
            if not image.content_type or not image.content_type.startswith('image/'):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="File phải là ảnh (image/*)"
                )
            
            # Đọc ảnh
            image_bytes = await image.read()
            
            if len(image_bytes) == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="File ảnh rỗng"
                )
            
            logger.info(f"Processing image: {image.filename}, size: {len(image_bytes)} bytes")
            
            # OCR với Vintern
            logger.info("Step 1: Extracting text with Vintern OCR...")
            raw_text = await ocr_service.extract_text(image_bytes)
        
        # Option 2: Nhận text trực tiếp
        elif raw_text_input:
            raw_text = raw_text_input.strip()
            logger.info(f"Processing direct text input: {len(raw_text)} characters")
        
        # Validate text
        if not raw_text or len(raw_text.strip()) == 0:
            logger.warning("No text to process")
            return TextExtractionResponse(
                extracted_text="",
                cleaned_text="",
                detected_urls=[],
                detected_phones=[],
                detected_emails=[],
                cleaning_stats={
                    'original_length': 0,
                    'cleaned_length': 0,
                    'removed_chars': 0,
                    'urls_found': 0,
                    'phones_found': 0,
                    'emails_found': 0
                },
                classification=None
            )
        
        # Bước 2: Làm sạch text (GIỮ DẤU TIẾNG VIỆT)
        logger.info("Step 2: Cleaning text (preserving Vietnamese accents)...")
        cleaned_text = text_cleaner.clean_text(raw_text)
        cleaned_text = text_cleaner.preserve_vietnamese_accents(cleaned_text)
        
        # Trích xuất thông tin
        urls = text_cleaner.extract_urls(cleaned_text)
        phones = text_cleaner.extract_phones(cleaned_text)
        emails = text_cleaner.extract_emails(cleaned_text)
        
        # Thống kê
        stats = text_cleaner.get_cleaning_stats(raw_text, cleaned_text)
        
        whitelist_results = []
        if urls:
            try:
                whitelist_service = WhitelistService(session=session)
                whitelist_results = await whitelist_service.check_urls(urls)
            except Exception as e:
                logger.error(f"Lỗi kiểm tra whitelist: {str(e)}", exc_info=True)

        # Bước 3: Phân loại lừa đảo và giải thích với Gemini
        classification = None
        try:
            service = get_gemini_service()
            if service:
                logger.info("Step 3: Classifying and explaining with Gemini...")
                classification = service.classify_and_explain(
                    text=cleaned_text,
                    detected_urls=urls,
                    detected_phones=phones
                )
                logger.info(f"Classification result: {'lừa đảo' if classification['is_scam'] else 'không lừa đảo'}")
        except Exception as e:
            logger.error(f"Error in Gemini classification: {str(e)}", exc_info=True)
            # Continue without classification
        
        logger.info(f"Extraction completed. Text length: {len(cleaned_text)} chars")
        
        return TextExtractionResponse(
            extracted_text=raw_text,
            cleaned_text=cleaned_text,
            detected_urls=urls,
            detected_phones=phones,
            detected_emails=emails,
            cleaning_stats=stats,
            classification=classification,
            whitelist_results=whitelist_results
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing image/text: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi xử lý: {str(e)}"
        )

