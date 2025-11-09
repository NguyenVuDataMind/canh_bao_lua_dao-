from fastapi import APIRouter, File, UploadFile, Depends, HTTPException, status
from app.deps.users import CurrentUser
from app.services.vintern_ocr_service import VinternOCRService
from app.services.text_cleaning import TextCleaner
from app.schemas.scam_detection import TextExtractionResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/image-processing")

# Initialize services
ocr_service = VinternOCRService(use_gpu=False)
text_cleaner = TextCleaner()

@router.post("/extract-text", response_model=TextExtractionResponse)
async def extract_text_from_image(
    # TODO: Thêm lại authentication sau khi hoàn thành dịch vụ
    # user: CurrentUser,  # ← Uncomment dòng này để bật lại authentication
    image: UploadFile = File(...)
):
    """
    Trích xuất text từ ảnh sử dụng Vintern-1B-v3.5 từ Hugging Face:
    1. OCR tiếng Việt (Vintern-1B-v3.5) - trích xuất toàn bộ text trong ảnh
       - Sử dụng Vintern model được fine-tune đặc biệt cho tiếng Việt
       - Model tự động xử lý preprocessing (dynamic_preprocess, build_transform)
       - Rất tốt cho OCR và hiểu tài liệu tiếng Việt
    2. Làm sạch text (giữ dấu tiếng Việt)
    
    **Lưu ý**: 
    - Text trả về sẽ GIỮ NGUYÊN DẤU TIẾNG VIỆT
    - Hỗ trợ ảnh chat screenshots với nhiều dòng text
    - Trích xuất toàn bộ nội dung trong ảnh
    """
    try:
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
        
        # Bước 1: OCR tiếng Việt với Vintern - model tự động xử lý preprocessing
        logger.info("Step 1: Extracting text with Vintern OCR...")
        raw_text = await ocr_service.extract_text(image_bytes)
        
        if not raw_text or len(raw_text.strip()) == 0:
            logger.warning("No text extracted from image")
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
                }
            )
        
        # Bước 2: Làm sạch text (GIỮ DẤU TIẾNG VIỆT)
        logger.info("Step 2: Cleaning text (preserving Vietnamese accents)...")
        cleaned_text = text_cleaner.clean_text(raw_text)
        
        # Đảm bảo giữ dấu tiếng Việt
        cleaned_text = text_cleaner.preserve_vietnamese_accents(cleaned_text)
        
        # Trích xuất thông tin
        urls = text_cleaner.extract_urls(cleaned_text)
        phones = text_cleaner.extract_phones(cleaned_text)
        emails = text_cleaner.extract_emails(cleaned_text)
        
        # Thống kê
        stats = text_cleaner.get_cleaning_stats(raw_text, cleaned_text)
        
        logger.info(f"Extraction completed. Text length: {len(cleaned_text)} chars")
        
        return TextExtractionResponse(
            extracted_text=raw_text,
            cleaned_text=cleaned_text,
            detected_urls=urls,
            detected_phones=phones,
            detected_emails=emails,
            cleaning_stats=stats
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi xử lý ảnh: {str(e)}"
        )

