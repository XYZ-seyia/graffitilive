import requests
import logging
import base64
import json

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self, llm_studio_url, model_name):
        self.llm_studio_url = llm_studio_url
        self.model_name = model_name
    
    def generate_prompts(self, original_image_path, enhanced_image_path):
        """根据原始图片和美化后的图片生成提示词"""
        try:
            # 读取并编码图片
            original_image = self._encode_image(original_image_path)
            enhanced_image = self._encode_image(enhanced_image_path)
            
            # 构建系统提示
            system_prompt = """你是一个专业的儿童绘画分析专家，擅长生成创意提示词。
你的任务是分析原始绘画和其美化版本，然后生成适当的提示词用于进一步处理。
请重点关注：
1. 图片中的主要元素和主题
2. 颜色和风格特点
3. 可能的动画效果建议
4. 如何让图片更加生动有趣"""

            # 构建用户提示
            user_prompt = f"""请分析这两张图片：
1. 原始儿童绘画
2. 美化后的版本

请生成一个详细的提示词，描述美化后的图片，并建议如何将其动画化。
重点关注关键元素、颜色和可能的动作。"""

            # 调用本地LLM API
            response = requests.post(
                f"{self.llm_studio_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": user_prompt,
                    "system": system_prompt,
                    "images": [original_image, enhanced_image],
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "max_tokens": 500
                    }
                }
            )
            
            if response.status_code != 200:
                logger.error(f"LLM API call failed: {response.text}")
                return None
            
            # 解析响应
            result = response.json()
            prompt_text = result.get('response', '')
            
            if not prompt_text:
                logger.error("No response from LLM")
                return None
            
            # 返回结构化的提示词
            return {
                "enhancement_prompt": prompt_text,
                "animation_prompt": self._generate_animation_prompt(prompt_text)
            }
            
        except Exception as e:
            logger.error(f"Error in generate_prompts: {str(e)}")
            return None
    
    def _encode_image(self, image_path):
        """将图片编码为base64"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def _generate_animation_prompt(self, enhancement_prompt):
        """根据增强提示生成动画提示"""
        try:
            # 构建系统提示
            system_prompt = """你是一个专业的动画提示词生成专家。
你的任务是将静态图片描述转换为动态动画提示词。
请重点关注：
1. 动作和运动描述
2. 时间和节奏建议
3. 特效和过渡效果
4. 如何让动画更加生动有趣"""

            # 构建用户提示
            user_prompt = f"""基于这个图片描述：
{enhancement_prompt}

请生成一个详细的动画提示词，包括：
1. 具体的动作描述
2. 时间节奏建议
3. 特效建议
4. 如何让动画更加生动有趣"""

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
                        "max_tokens": 300
                    }
                }
            )
            
            if response.status_code != 200:
                logger.error(f"LLM API call failed: {response.text}")
                return None
            
            result = response.json()
            return result.get('response', '')
            
        except Exception as e:
            logger.error(f"Error in _generate_animation_prompt: {str(e)}")
            return None 