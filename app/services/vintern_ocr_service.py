import numpy as np
import torch
import torchvision.transforms as T
from PIL import Image
from torchvision.transforms.functional import InterpolationMode
from transformers import AutoModel, AutoTokenizer
import logging

logger = logging.getLogger(__name__)

IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)


def build_transform(input_size):
    MEAN, STD = IMAGENET_MEAN, IMAGENET_STD
    transform = T.Compose([
        T.Lambda(lambda img: img.convert('RGB') if img.mode != 'RGB' else img),
        T.Resize((input_size, input_size), interpolation=InterpolationMode.BICUBIC),
        T.ToTensor(),
        T.Normalize(mean=MEAN, std=STD)
    ])
    return transform


def find_closest_aspect_ratio(aspect_ratio, target_ratios, width, height, image_size):
    best_ratio_diff = float('inf')
    best_ratio = (1, 1)
    area = width * height
    for ratio in target_ratios:
        target_aspect_ratio = ratio[0] / ratio[1]
        ratio_diff = abs(aspect_ratio - target_aspect_ratio)
        if ratio_diff < best_ratio_diff:
            best_ratio_diff = ratio_diff
            best_ratio = ratio
        elif ratio_diff == best_ratio_diff:
            if area > 0.5 * image_size * image_size * ratio[0] * ratio[1]:
                best_ratio = ratio
    return best_ratio


def dynamic_preprocess(image, min_num=1, max_num=12, image_size=448, use_thumbnail=False):
    orig_width, orig_height = image.size
    aspect_ratio = orig_width / orig_height

    # calculate the existing image aspect ratio
    target_ratios = set(
        (i, j) for n in range(min_num, max_num + 1) for i in range(1, n + 1) for j in range(1, n + 1) if
        i * j <= max_num and i * j >= min_num)
    target_ratios = sorted(target_ratios, key=lambda x: x[0] * x[1])

    # find the closest aspect ratio to the target
    target_aspect_ratio = find_closest_aspect_ratio(
        aspect_ratio, target_ratios, orig_width, orig_height, image_size)

    # calculate the target width and height
    target_width = image_size * target_aspect_ratio[0]
    target_height = image_size * target_aspect_ratio[1]
    blocks = target_aspect_ratio[0] * target_aspect_ratio[1]

    # resize the image
    resized_img = image.resize((target_width, target_height))
    processed_images = []
    for i in range(blocks):
        box = (
            (i % (target_width // image_size)) * image_size,
            (i // (target_width // image_size)) * image_size,
            ((i % (target_width // image_size)) + 1) * image_size,
            ((i // (target_width // image_size)) + 1) * image_size
        )
        # split the image
        split_img = resized_img.crop(box)
        processed_images.append(split_img)
    assert len(processed_images) == blocks
    if use_thumbnail and len(processed_images) != 1:
        thumbnail_img = image.resize((image_size, image_size))
        processed_images.append(thumbnail_img)
    return processed_images


def load_image(image_file, input_size=448, max_num=12):
    image = Image.open(image_file).convert('RGB')
    transform = build_transform(input_size=input_size)
    images = dynamic_preprocess(image, image_size=input_size, use_thumbnail=True, max_num=max_num)
    pixel_values = [transform(image) for image in images]
    pixel_values = torch.stack(pixel_values)
    return pixel_values


class VinternOCRService:
    """
    OCR service sử dụng Vintern-1B-v3.5 từ Hugging Face
    Code giống hệt mẫu chính thức từ Hugging Face
    """
    
    def __init__(self, model_name: str = "5CD-AI/Vintern-1B-v3_5", use_gpu: bool = False, cache_dir: str = None):
        import os
        self.model_name = model_name
        self.use_gpu = use_gpu and torch.cuda.is_available()
        # Sử dụng cache_dir từ parameter, hoặc environment variable HF_HOME, hoặc default
        # Trong Docker, HF_HOME sẽ được set thành /app/.cache/huggingface
        if cache_dir:
            self.cache_dir = cache_dir
        elif os.getenv('HF_HOME'):
            self.cache_dir = os.getenv('HF_HOME')
        else:
            # Default: ~/.cache/huggingface hoặc /app/.cache/huggingface trong container
            home = os.getenv('HOME', '/app')
            self.cache_dir = os.path.join(home, '.cache', 'huggingface')
        
        logger.info(f"Loading Vintern model: {model_name}")
        logger.info(f"Using cache directory: {self.cache_dir}")
        
        try:
            # Load model - giống hệt code mẫu, thêm cache_dir để persist
            self.model = AutoModel.from_pretrained(
                model_name,
                cache_dir=self.cache_dir,
                torch_dtype=torch.bfloat16 if self.use_gpu else torch.float32,
                low_cpu_mem_usage=True,
                trust_remote_code=True,
                use_flash_attn=False,
            ).eval()
            
            if self.use_gpu:
                self.model = self.model.cuda()
            
            # Load tokenizer - giống hệt code mẫu, thêm cache_dir để persist
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                cache_dir=self.cache_dir,
                trust_remote_code=True, 
                use_fast=False
            )
            
            logger.info(f"Vintern model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading Vintern model: {str(e)}", exc_info=True)
            raise
    
    async def extract_text(self, image_bytes: bytes, prompt: str = None) -> str:
        """
        Trích xuất text từ ảnh - giống hệt code mẫu
        Args:
            image_bytes: Bytes của ảnh
            prompt: Prompt tùy chỉnh (mặc định: prompt OCR tiếng Việt)
        Returns:
            Text đã được trích xuất
        """
        try:
            # Tạo file tạm từ bytes để load_image có thể đọc
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                tmp_file.write(image_bytes)
                tmp_file_path = tmp_file.name
            
            try:
                # Load và preprocess image - giống hệt code mẫu
                pixel_values = load_image(tmp_file_path, max_num=6)
                
                # Move to device - giống hệt code mẫu
                if self.use_gpu:
                    pixel_values = pixel_values.to(torch.bfloat16).cuda()
                else:
                    pixel_values = pixel_values.to(torch.float32).cpu()
                
                # Generation config - giống hệt code mẫu
                generation_config = dict(
                    max_new_tokens=1024, 
                    do_sample=False, 
                    num_beams=3, 
                    repetition_penalty=2.5
                )
                
                # Default prompt cho OCR tiếng Việt
                if prompt is None:
                    question = '<image>\nTrích xuất toàn bộ text trong ảnh này. Trả về text đã được trích xuất, giữ nguyên dấu tiếng Việt.'
                else:
                    question = prompt
                
                # Generate - giống hệt code mẫu
                with torch.no_grad():
                    response, history = self.model.chat(
                        self.tokenizer, 
                        pixel_values, 
                        question, 
                        generation_config, 
                        history=None, 
                        return_history=True
                    )
                
                text = response.strip()
                
                logger.info(f"Extracted {len(text)} characters with Vintern OCR")
                return text
                
            finally:
                # Xóa file tạm
                if os.path.exists(tmp_file_path):
                    os.unlink(tmp_file_path)
            
        except Exception as e:
            logger.error(f"Error extracting text with Vintern: {str(e)}", exc_info=True)
            raise

