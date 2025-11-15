"""
PhoBERT-based scam classifier service
Sử dụng model đã fine-tune để phân loại text có lừa đảo hay không
"""
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer
import logging
import os
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class PhoBERTScamClassifier:
    """PhoBERT-based scam classifier"""
    
    def __init__(
        self, 
        model_path: str = "data/models/phobert-scam-classifier/checkpoint-42",
        use_gpu: bool = False,
        cache_dir: Optional[str] = None
    ):
        """
        Initialize classifier
        
        Args:
            model_path: Path đến model đã fine-tune
            use_gpu: Có dùng GPU không
            cache_dir: Cache directory cho Hugging Face models
        """
        self.model_path = model_path
        self.use_gpu = use_gpu and torch.cuda.is_available()
        self.device = torch.device("cuda" if self.use_gpu else "cpu")
        
        logger.info(f"Loading PhoBERT scam classifier from: {model_path}")
        logger.info(f"Using device: {self.device}")
        
        # Check if model exists
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Model not found at {model_path}. "
                f"Please run fine-tuning script first: python scripts/finetune_phobert.py"
            )
        
        try:
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_path,
                cache_dir=cache_dir,
                trust_remote_code=True
            )
            
            # Load model từ checkpoint
            self.model = AutoModelForSequenceClassification.from_pretrained(
                model_path,
                cache_dir=cache_dir,
                trust_remote_code=True
            )
            
            self.model.to(self.device)
            self.model.eval()  # Set to evaluation mode
            
            logger.info("PhoBERT scam classifier loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}", exc_info=True)
            raise
    
    def predict(self, text: str) -> Dict:
        """
        Predict xem text có lừa đảo hay không
        
        Args:
            text: Text cần phân loại
            
        Returns:
            Dict với keys:
                - is_scam: bool - Có lừa đảo không
                - score: float - Confidence score (0-1)
                - label: str - "lừa đảo" hoặc "không lừa đảo"
                - probabilities: dict - Xác suất cho từng class
        """
        if not text or len(text.strip()) == 0:
            return {
                "is_scam": False,
                "score": 0.0,
                "label": "không lừa đảo",
                "probabilities": {"lừa đảo": 0.0, "không lừa đảo": 1.0}
            }
        
        try:
            # Tokenize
            encoding = self.tokenizer(
                text,
                truncation=True,
                padding='max_length',
                max_length=256,
                return_tensors='pt'
            )
            
            # Move to device
            input_ids = encoding['input_ids'].to(self.device)
            attention_mask = encoding['attention_mask'].to(self.device)
            
            # Predict
            with torch.no_grad():
                outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)
                logits = outputs.logits
                
                # Apply softmax để lấy probabilities
                probabilities = torch.softmax(logits, dim=-1)
                predicted_class = torch.argmax(probabilities, dim=-1).item()
                confidence = probabilities[0][predicted_class].item()
            
            # Map class to label
            is_scam = predicted_class == 1
            label = "lừa đảo" if is_scam else "không lừa đảo"
            
            result = {
                "is_scam": is_scam,
                "score": confidence,
                "label": label,
                "probabilities": {
                    "lừa đảo": probabilities[0][1].item(),
                    "không lừa đảo": probabilities[0][0].item()
                }
            }
            
            logger.info(f"Prediction: {label} (confidence: {confidence:.3f})")
            return result
            
        except Exception as e:
            logger.error(f"Error predicting: {str(e)}", exc_info=True)
            # Return safe default
            return {
                "is_scam": False,
                "score": 0.0,
                "label": "không lừa đảo",
                "probabilities": {"lừa đảo": 0.0, "không lừa đảo": 1.0}
            }

