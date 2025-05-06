import os
import requests
from dotenv import load_dotenv
from typing import Dict, Tuple
import logging

load_dotenv()
logger = logging.getLogger(__name__)

class PromptGenerationAgent:
    def __init__(self):
        self.llm_studio_url = os.getenv("LLM_STUDIO_URL", "http://localhost:1234")
        self.model_name = os.getenv("LLM_MODEL", "default")
        self.style_base = "cute style, simple lines, children's drawing style, white background"
        self.negative_base = "low quality, blurry, distorted, bad anatomy, text, watermark, multiple characters, duplicate, multiple views"
    
    def generate_from_analysis(self, analysis_result: Dict) -> Dict:
        """
        基于图像分析结果生成增强提示词
        
        Args:
            analysis_result: 来自图像分析代理的分析结果
            
        Returns:
            Dict: 包含生成的提示词的字典
        """
        try:
            # 构建提示词
            prompt = f"""你是一个专业的图像提示词生成专家。请基于以下图片分析结果生成一个简洁的英文提示词串。

图片分析结果：
描述：{analysis_result.get('description', '')}
场景：{analysis_result.get('scene', '')}
风格：{analysis_result.get('style', '')}
颜色：{', '.join(analysis_result.get('colors', []))}
物体：{', '.join(analysis_result.get('objects', []))}

要求：
1. 使用英文
2. 所有提示词用逗号和空格分隔
3. 不要使用冒号和换行
4. 为主体添加量词(a, one)确保生成单个角色
5. 保持简洁清晰的描述
6. 确保提示词间的关系合理
7. 如果图片是黑白的，那么提示词中不需要出现black and white

示例格式：
a cute little girl, wearing blue dress, holding a teddy bear, standing in garden, soft lighting

请直接给出提示词，不要包含任何解释或前缀。"""
            
            response = requests.post(
                f"{self.llm_studio_url}/v1/chat/completions",
                json={
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.7,
                    "max_tokens": 150
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"LLM API error: {response.text}")
            
            try:
                generated_prompt = response.json()["choices"][0]["message"]["content"].strip()
            except (KeyError, IndexError) as e:
                error_msg = f"解析API响应失败: {str(e)}, 响应内容: {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
            
            positive_prompt, negative_prompt = self.generate_prompts(generated_prompt)
            
            return {
                "status": "success",
                "positive_prompt": positive_prompt,
                "negative_prompt": negative_prompt,
                "raw_prompt": generated_prompt
            }
            
        except Exception as e:
            logger.error(f"提示词生成失败: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }

    def generate_prompts(self, features: str) -> Tuple[str, str]:
        """
        根据图像特征生成正面和负面提示词
        
        Args:
            features: 图像特征描述
            
        Returns:
            Tuple[str, str]: (正面提示词, 负面提示词)
        """
        try:
            # 处理正面提示词
            if features:
                main_subject = self._extract_main_subject(features)
                # 确保提示词之间只用逗号和空格分隔
                positive_prompt = f"{main_subject}, {self.style_base}"
            else:
                positive_prompt = f"a children's drawing, {self.style_base}"
            
            logger.debug(f"生成的正面提示词: {positive_prompt}")
            logger.debug(f"生成的负面提示词: {self.negative_base}")
            
            return positive_prompt, self.negative_base
            
        except Exception as e:
            logger.error(f"生成提示词失败: {str(e)}")
            return "a children's drawing, cute style, white background", self.negative_base
    
    def _extract_main_subject(self, features: str) -> str:
        """
        从特征描述中提取主要主体，并格式化为适合SD模型的格式
        
        Args:
            features: 图像特征描述
            
        Returns:
            str: 主要主体描述
        """
        try:
            # 移除多余的空格和标点
            features = features.strip().rstrip(',.。，')
            
            # 确保描述以量词开头
            if not any(features.lower().startswith(prefix) for prefix in ['a ', 'an ', 'one ', 'the ']):
                features = 'a ' + features
            
            # 确保提示词之间只用逗号和空格分隔
            features = features.replace('，', ', ').replace('。', ', ').replace(';', ', ')
            
            return features
            
        except Exception as e:
            logger.error(f"提取主体失败: {str(e)}")
            return "a children's drawing" 