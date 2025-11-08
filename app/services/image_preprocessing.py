import cv2
import numpy as np
from PIL import Image
from io import BytesIO
from typing import Tuple
import logging

logger = logging.getLogger(__name__)

class ImagePreprocessor:
    """
    Tiền xử lý ảnh: làm nét, resize, crop ảnh chat
    Sử dụng: OpenCV + Pillow
    """
    
    def __init__(self, max_width: int = 2000, max_height: int = 3000):
        """
        Args:
            max_width: Chiều rộng tối đa sau khi resize
            max_height: Chiều cao tối đa sau khi resize
        """
        self.max_width = max_width
        self.max_height = max_height
    
    async def preprocess(self, image_bytes: bytes) -> Image.Image:
        """
        Tiền xử lý ảnh từ bytes
        
        Args:
            image_bytes: Bytes của ảnh đầu vào
            
        Returns:
            PIL Image đã được xử lý
        """
        try:
            # 1. Đọc ảnh từ bytes
            image = Image.open(BytesIO(image_bytes))
            logger.info(f"Original image size: {image.size}")
            
            # 2. Convert sang RGB nếu cần (xử lý RGBA, L mode)
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # 3. Convert PIL Image sang numpy array (OpenCV format)
            img_array = np.array(image)
            
            # 4. Làm nét ảnh (Sharpen)
            sharpened = self._sharpen_image(img_array)
            
            # 5. Tăng độ tương phản (Contrast Enhancement)
            enhanced = self._enhance_contrast(sharpened)
            
            # 6. Resize nếu quá lớn
            resized = self._resize_if_needed(enhanced)
            
            # 7. Convert lại về PIL Image
            processed_image = Image.fromarray(resized)
            
            logger.info(f"Processed image size: {processed_image.size}")
            return processed_image
            
        except Exception as e:
            logger.error(f"Error preprocessing image: {str(e)}")
            raise
    
    def _sharpen_image(self, img_array: np.ndarray) -> np.ndarray:
        """
        Làm nét ảnh bằng kernel sharpening
        
        Args:
            img_array: Numpy array của ảnh
            
        Returns:
            Ảnh đã được làm nét
        """
        # Kernel để làm nét (sharpen kernel)
        kernel = np.array([
            [0, -1, 0],
            [-1, 5, -1],
            [0, -1, 0]
        ])
        
        # Áp dụng filter
        sharpened = cv2.filter2D(img_array, -1, kernel)
        
        # Đảm bảo giá trị pixel trong khoảng [0, 255]
        sharpened = np.clip(sharpened, 0, 255).astype(np.uint8)
        
        return sharpened
    
    def _enhance_contrast(self, img_array: np.ndarray) -> np.ndarray:
        """
        Tăng độ tương phản để text dễ đọc hơn
        
        Args:
            img_array: Numpy array của ảnh
            
        Returns:
            Ảnh đã được tăng độ tương phản
        """
        # Chuyển sang LAB color space
        lab = cv2.cvtColor(img_array, cv2.COLOR_RGB2LAB)
        l, a, b = cv2.split(lab)
        
        # Áp dụng CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        
        # Merge lại và convert về RGB
        enhanced = cv2.merge([l, a, b])
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2RGB)
        
        return enhanced
    
    def _resize_if_needed(self, img_array: np.ndarray) -> np.ndarray:
        """
        Resize ảnh nếu quá lớn (giữ tỷ lệ)
        
        Args:
            img_array: Numpy array của ảnh
            
        Returns:
            Ảnh đã được resize (nếu cần)
        """
        height, width = img_array.shape[:2]
        
        # Kiểm tra nếu cần resize
        if width > self.max_width or height > self.max_height:
            # Tính scale factor
            scale_w = self.max_width / width
            scale_h = self.max_height / height
            scale = min(scale_w, scale_h)  # Giữ tỷ lệ
            
            # Chọn scale nhỏ hơn để đảm bảo fit cả width và height
            new_width = int(width * scale)
            new_height = int(height * scale)
            
            # Resize với interpolation tốt
            resized = cv2.resize(
                img_array, 
                (new_width, new_height),
                interpolation=cv2.INTER_LANCZOS4  # Chất lượng cao
            )
            
            logger.info(f"Resized from {width}x{height} to {new_width}x{new_height}")
            return resized
        
        return img_array
    
    def crop_chat_area(self, image: Image.Image, bbox: Tuple[int, int, int, int] = None) -> Image.Image:
        """
        Crop vùng chat cụ thể (nếu biết tọa độ)
        
        Args:
            image: PIL Image
            bbox: (left, top, right, bottom) - tọa độ vùng cần crop
            
        Returns:
            Ảnh đã được crop
        """
        if bbox:
            left, top, right, bottom = bbox
            cropped = image.crop((left, top, right, bottom))
            return cropped
        return image

