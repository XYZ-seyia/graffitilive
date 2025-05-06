from agents.image_analysis_agent import ImageAnalysisAgent
from agents.prompt_generation_agent import PromptGenerationAgent
from agents.art_review_agent import ArtReviewAgent
import logging

logger = logging.getLogger(__name__)

class TaskCoordinator:
    def __init__(self):
        self.image_analyzer = ImageAnalysisAgent()
        self.prompt_generator = PromptGenerationAgent()
        self.art_reviewer = ArtReviewAgent()
    
    def process_image(self, image_path):
        """
        协调处理图像分析任务
        
        Args:
            image_path: 图片文件路径
            
        Returns:
            Dict: 包含所有处理结果的字典
        """
        try:
            logger.info(f"开始处理图片: {image_path}")
            
            # 第一步：分析图像
            analysis_result = self.image_analyzer.analyze_image(image_path)
            if analysis_result.get("status") == "error":
                logger.error(f"图像分析失败: {analysis_result.get('error')}")
                return analysis_result
            
            # 第二步：生成艺术评论
            logger.info("开始生成艺术评论")
            review_result = self.art_reviewer.generate_review(analysis_result)
            if review_result.get("status") == "error":
                logger.error(f"艺术评论生成失败: {review_result.get('error')}")
            else:
                logger.info("艺术评论生成成功")
                logger.debug(f"评论内容: {review_result.get('review', '')}")
            
            # 第三步：生成提示词
            logger.info("开始生成提示词")
            prompt_result = self.prompt_generator.generate_from_analysis(analysis_result)
            if prompt_result.get("status") == "error":
                logger.error(f"提示词生成失败: {prompt_result.get('error')}")
            else:
                logger.info("提示词生成成功")
            
            # 整合所有结果
            return {
                "status": "success",
                "analysis": {
                    "description": analysis_result.get("description", ""),
                    "scene": analysis_result.get("scene", ""),
                    "style": analysis_result.get("style", ""),
                    "colors": analysis_result.get("colors", []),
                    "objects": analysis_result.get("objects", [])
                },
                "review": {
                    "status": review_result.get("status", "error"),
                    "content": review_result.get("review", ""),
                    "error": review_result.get("error")
                },
                "prompts": {
                    "positive_prompt": prompt_result.get("positive_prompt", ""),
                    "negative_prompt": prompt_result.get("negative_prompt", ""),
                    "raw_prompt": prompt_result.get("raw_prompt", "")
                }
            }
            
        except Exception as e:
            logger.error(f"任务处理失败: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            } 