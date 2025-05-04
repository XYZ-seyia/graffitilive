from agents.image_analysis_agent import ImageAnalysisAgent
from agents.prompt_generation_agent import PromptGenerationAgent

class TaskCoordinator:
    def __init__(self):
        self.image_analyzer = ImageAnalysisAgent()
        self.prompt_generator = PromptGenerationAgent()
    
    def process_image(self, image_path):
        """
        协调处理图像分析任务
        """
        try:
            # 第一步：分析图像
            analysis_result = self.image_analyzer.analyze(image_path)
            if analysis_result["status"] == "error":
                return analysis_result
            
            # 第二步：生成提示词
            prompt_result = self.prompt_generator.generate(analysis_result["description"])
            if prompt_result["status"] == "error":
                return prompt_result
            
            return {
                "status": "success",
                "description": analysis_result["description"],
                "prompt": prompt_result["prompt"]
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            } 