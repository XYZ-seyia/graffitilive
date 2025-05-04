from PIL import Image
import torch
from transformers import AutoProcessor, AutoModelForVision2Seq

class ImageAnalysisAgent:
    def __init__(self):
        # 初始化图像识别模型
        self.processor = AutoProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
        self.model = AutoModelForVision2Seq.from_pretrained("Salesforce/blip-image-captioning-base")
    
    def analyze(self, image_path):
        """
        分析图像并生成描述
        """
        try:
            # 加载并处理图像
            image = Image.open(image_path).convert('RGB')
            inputs = self.processor(image, return_tensors="pt")
            
            # 生成图像描述
            outputs = self.model.generate(**inputs, max_length=50)
            description = self.processor.decode(outputs[0], skip_special_tokens=True)
            
            return {
                "status": "success",
                "description": description
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            } 