from paddleocr import PaddleOCR
from PIL import Image
import io
import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)

class VietnameseOCRService:
    """
    OCR tiếng Việt sử dụng PaddleOCR
    Hỗ trợ: Zalo, SMS, web screenshots
    """
    
    def __init__(self, use_angle_cls: bool = True, lang: str = 'vi'):
        """
        Khởi tạo PaddleOCR
        
        Args:
            use_angle_cls: Sử dụng classification để xoay ảnh
            lang: Ngôn ngữ ('vi' cho tiếng Việt)
        """
        try:
            logger.info("Initializing PaddleOCR...")
            self.ocr = PaddleOCR(
                use_angle_cls=use_angle_cls,
                lang=lang,
                use_gpu=False,  # Đặt True nếu có GPU
                show_log=False
            )
            logger.info("PaddleOCR initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing PaddleOCR: {str(e)}")
            raise
    
    async def extract_text(self, image: Image.Image) -> str:
        """
        Trích xuất text từ ảnh
        
        Args:
            image: PIL Image đã được tiền xử lý
            
        Returns:
            Text đã được trích xuất (kết hợp tất cả dòng)
        """
        try:
            # Convert PIL Image sang bytes
            img_bytes = io.BytesIO()
            image.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            
            # OCR với PaddleOCR
            result = self.ocr.ocr(img_bytes.read(), cls=True)
            
            # Xử lý kết quả
            texts = []
            if result and result[0]:
                for line in result[0]:
                    if line and len(line) > 1:
                        # line[1] là tuple (text, confidence)
                        text = line[1][0]
                        confidence = line[1][1]
                        
                        # Chỉ lấy text có confidence > 0.5
                        if confidence > 0.5:
                            texts.append(text)
            
            # Kết hợp tất cả text thành một chuỗi
            full_text = '\n'.join(texts)
            
            logger.info(f"Extracted {len(texts)} text lines")
            return full_text
            
        except Exception as e:
            logger.error(f"Error extracting text: {str(e)}")
            raise
    
    async def extract_text_with_boxes(self, image: Image.Image) -> List[Tuple[str, float, List]]:
        """
        Trích xuất text kèm thông tin vị trí và confidence
        
        Args:
            image: PIL Image
            
        Returns:
            List of (text, confidence, bbox) tuples
        """
        try:
            img_bytes = io.BytesIO()
            image.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            
            result = self.ocr.ocr(img_bytes.read(), cls=True)
            
            extracted_data = []
            if result and result[0]:
                for line in result[0]:
                    if line and len(line) > 1:
                        bbox = line[0]  # Tọa độ 4 điểm
                        text = line[1][0]
                        confidence = line[1][1]
                        
                        if confidence > 0.5:
                            extracted_data.append((text, confidence, bbox))
            
            return extracted_data
            
        except Exception as e:
            logger.error(f"Error extracting text with boxes: {str(e)}")
            raise

