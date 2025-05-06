import base64
import json
import requests
import logging
import os
from dotenv import load_dotenv
from typing import Dict

load_dotenv()

# 配置日志
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class ImageAnalysisAgent:
    def __init__(self):
        # 使用直接的Bearer token认证
        self.baidu_api_url = "https://qianfan.baidubce.com/v2/chat/completions"
        self.baidu_token = os.getenv("BAIDU_TOKEN", "bce-v3/ALTAK-5vJ2WWcxX1gOitlDF7bDt/d00bb952484368905660e7444ecda5fbbaffca52")

    def analyze_image(self, image_path: str) -> Dict:
        """
        使用百度多模态模型分析图片
        
        Args:
            image_path: 图片文件路径
            
        Returns:
            Dict: 包含图片分析结果的字典
        """
        try:
            # 读取图片文件并转换为base64
            img_base64 = self._process_local_image(image_path)
            
            payload = json.dumps({
                "model": "ernie-4.5-8k-preview",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """请分析这幅儿童涂鸦并返回以下信息：
1. 描述：一句话描述图片主要内容
2. 场景：画面场景
3. 风格：画风特点
4. 颜色：主要使用的颜色
5. 主体：画面中的主要物体
6. 主体特征：主体的特征"""
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": img_base64
                                }
                            }
                        ]
                    }
                ]
            })
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.baidu_token}"
            }

            response = requests.post(self.baidu_api_url, headers=headers, data=payload)
            
            if response.status_code != 200:
                raise Exception(f"Baidu API error: {response.text}")

            result = response.json()
            
            # 解析返回的结果
            if "error_code" in result:
                raise Exception(f"API返回错误: {result}")
                
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            # 解析返回的文本内容
            lines = content.strip().split('\n')
            analysis_result = {
                "status": "success",
                "description": "",
                "scene": "",
                "style": "",
                "colors": [],
                "objects": []
            }
            
            for line in lines:
                if "描述：" in line:
                    analysis_result["description"] = line.split("描述：")[1].strip()
                elif "场景：" in line:
                    analysis_result["scene"] = line.split("场景：")[1].strip()
                elif "风格：" in line:
                    analysis_result["style"] = line.split("风格：")[1].strip()
                elif "颜色：" in line:
                    colors = line.split("颜色：")[1].strip()
                    analysis_result["colors"] = [c.strip() for c in colors.split("、")]
                elif "物体：" in line:
                    objects = line.split("物体：")[1].strip()
                    analysis_result["objects"] = [o.strip() for o in objects.split("、")]
            
            logger.debug(f"Image analysis result: {analysis_result}")
            return analysis_result

        except Exception as e:
            logger.error(f"Image analysis failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }

    def _process_local_image(self, image_path):
        """处理本地图片，返回base64编码"""
        try:
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"图片文件不存在: {image_path}")
                
            with open(image_path, 'rb') as f:
                image_data = f.read()
                if not image_data:
                    raise ValueError("图片文件为空")
                return base64.b64encode(image_data).decode()
        except Exception as e:
            logger.error(f"处理图片失败: {str(e)}")
            raise 