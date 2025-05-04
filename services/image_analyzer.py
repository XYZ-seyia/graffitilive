import os
from PIL import Image
import torch
from transformers import AutoProcessor, AutoModelForVision2Seq
import openai
from dotenv import load_dotenv

load_dotenv()

class ImageAnalyzer:
    def __init__(self):
        # 初始化图像识别模型
        self.processor = AutoProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
        self.model = AutoModelForVision2Seq.from_pretrained("Salesforce/blip-image-captioning-base")
        
        # 设置OpenAI API密钥
        openai.api_key = os.getenv("OPENAI_API_KEY")
        
    def analyze_image(self, image_path):
        """
        分析图像并生成描述
        """
        # 加载并处理图像
        image = Image.open(image_path).convert('RGB')
        inputs = self.processor(image, return_tensors="pt")
        
        # 生成图像描述
        outputs = self.model.generate(**inputs, max_length=50)
        description = self.processor.decode(outputs[0], skip_special_tokens=True)
        
        return description
    
    def generate_prompt(self, image_description):
        """
        基于图像描述生成增强提示词
        """
        prompt = f"""基于以下儿童画的描述，生成一个详细的提示词，用于图像增强：
        描述：{image_description}
        
        请生成一个包含以下要素的提示词：
        1. 主要物体和场景
        2. 艺术风格（如：儿童画风格、水彩风格等）
        3. 颜色和氛围
        4. 细节描述
        
        提示词应该简洁但详细，适合用于AI图像增强。"""
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "你是一个专业的图像增强提示词生成专家。"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
    
    def process_image(self, image_path):
        """
        处理图像并返回分析结果和提示词
        """
        try:
            # 分析图像
            description = self.analyze_image(image_path)
            
            # 生成提示词
            prompt = self.generate_prompt(description)
            
            return {
                "description": description,
                "prompt": prompt
            }
        except Exception as e:
            return {
                "error": str(e)
            } 