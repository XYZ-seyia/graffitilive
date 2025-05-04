import os
import requests
import base64
from dotenv import load_dotenv

load_dotenv()

class PromptGenerationAgent:
    def __init__(self):
        # 设置LLM Studio配置
        self.llm_studio_url = os.getenv("LLM_STUDIO_URL", "http://localhost:1234")
        self.model_name = os.getenv("LLM_MODEL", "default")
    
    def generate(self, image_description):
        """
        基于图像描述生成增强提示词
        """
        try:
            # 构建系统提示
            system_prompt = """你是一个专业的图像增强提示词生成专家。
你的任务是分析图片描述并生成合适的提示词。
请重点关注：
1. 主要物体和场景
2. 艺术风格（如：儿童画风格、水彩风格等）
3. 颜色和氛围
4. 细节描述"""

            # 构建用户提示
            user_prompt = f"""基于以下儿童画的描述，生成一个详细的提示词，用于图像增强：
            描述：{image_description}
            
            请生成一个包含以下要素的提示词：
            1. 主要物体和场景
            2. 艺术风格（如：儿童画风格、水彩风格等）
            3. 颜色和氛围
            4. 细节描述
            
            提示词应该简洁但详细，适合用于AI图像增强。"""
            
            response = requests.post(
                f"{self.llm_studio_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": user_prompt,
                    "system": system_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "max_tokens": 150
                    }
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"LLM Studio API error: {response.text}")
            
            result = response.json()
            return {
                "status": "success",
                "prompt": result.get("response", "").strip()
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            } 