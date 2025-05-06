import os
import requests
from dotenv import load_dotenv
from typing import Dict
import logging

load_dotenv()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # 设置日志级别为INFO

class ArtReviewAgent:
    def __init__(self):
        self.llm_studio_url = os.getenv("LLM_STUDIO_URL", "http://localhost:1234")
        self.model_name = os.getenv("LLM_MODEL", "default")
        logger.info(f"ArtReviewAgent initialized with LLM URL: {self.llm_studio_url}")
    
    def generate_review(self, analysis_result: Dict) -> Dict:
        """
        基于图像分析结果生成艺术评论
        
        Args:
            analysis_result: 来自图像分析代理的分析结果
            
        Returns:
            Dict: 包含生成的艺术评论的字典
        """
        try:
            logger.info("开始生成艺术评论")
            logger.info(f"收到的图片分析结果: {analysis_result}")
            
            # 构建提示词
            prompt = f"""你是一个专业的儿童艺术教育专家。请基于以下图片分析结果生成一段温暖友好的艺术评论。

图片分析结果：
描述：{analysis_result.get('description', '')}
场景：{analysis_result.get('scene', '')}
风格：{analysis_result.get('style', '')}
颜色：{', '.join(analysis_result.get('colors', []))}
物体：{', '.join(analysis_result.get('objects', []))}

你的评论应该：
1. 积极正面，突出作品的优点
2. 使用适合儿童理解的语言
3. 包含具体的观察和建议
4. 鼓励孩子继续创作和探索

请在评论中包含：
1. 对画作主题和创意的赞赏
2. 对色彩运用的观察
3. 对细节表现的肯定
4. 鼓励性的建议和期待

请直接给出评论内容，不要包含任何前缀或格式说明。"""

            logger.info("正在调用本地LLM生成评论")
            
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
                    "max_tokens": 300
                }
            )
            
            if response.status_code != 200:
                error_msg = f"LLM API error: {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
            
            try:
                review = response.json()["choices"][0]["message"]["content"].strip()
            except (KeyError, IndexError) as e:
                error_msg = f"解析API响应失败: {str(e)}, 响应内容: {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
            
            logger.info("成功生成艺术评论")
            logger.debug(f"生成的评论内容: {review}")
            
            return {
                "status": "success",
                "review": review
            }
            
        except Exception as e:
            error_msg = f"艺术评论生成失败: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "error": str(e)
            } 