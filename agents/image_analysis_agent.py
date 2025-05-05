import base64
import json
import requests
import logging
import os

# 配置日志
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class ImageAnalysisAgent:
    def __init__(self):
        # 百度API配置
        self.baidu_api_url = "https://qianfan.baidubce.com/v2/chat/completions"
        self.baidu_api_key = "bce-v3/ALTAK-5vJ2WWcxX1gOitlDF7bDt/d00bb952484368905660e7444ecda5fbbaffca52"
    
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
    
    def _call_baidu_api(self, image_base64, prompt):
        """调用百度API的通用方法"""
        try:
            logger.info("准备调用百度API")
            logger.debug(f"提示词: {prompt}")
            
            payload = json.dumps({
                "model": "ernie-4.5-8k-preview",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": image_base64
                                }
                            }
                        ]
                    }
                ]
            })
            
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.baidu_api_key}'
            }
            
            logger.debug("发送请求到百度API")
            response = requests.post(self.baidu_api_url, headers=headers, data=payload)
            
            if response.status_code != 200:
                logger.error(f"API请求失败: 状态码 {response.status_code}")
                logger.error(f"错误响应: {response.text}")
                return {"error": f"API请求失败: {response.status_code}"}
            
            response_data = response.json()
            logger.debug(f"API响应: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
            
            # 检查响应格式并提取内容
            if not response_data.get("choices") or not response_data["choices"][0].get("message", {}).get("content"):
                logger.error(f"API响应格式错误: {response_data}")
                return {"error": "API响应格式错误"}
            
            content = response_data["choices"][0]["message"]["content"].strip()
            return {"result": content}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API请求异常: {str(e)}")
            return {"error": f"API请求异常: {str(e)}"}
        except json.JSONDecodeError as e:
            logger.error(f"API响应解析失败: {str(e)}")
            return {"error": f"API响应解析失败: {str(e)}"}
        except Exception as e:
            logger.error(f"调用API时发生未知错误: {str(e)}")
            return {"error": f"未知错误: {str(e)}"}

    def get_humorous_review(self, image_path):
        """获取幽默尖锐的涂鸦评价"""
        try:
            logger.info("开始生成幽默评价")
            img_base64 = self._process_local_image(image_path)
            prompt = """请以一个幽默尖锐的艺术评论家的身份，用2-3句话评价这幅儿童涂鸦。
            要求：
            1. 语气要诙谐幽默，带点善意的调侃
            2. 要体现出专业的艺术评论视角
            3. 可以适当夸张，但不能打击信心
            4. 用中文回答"""
            
            response_data = self._call_baidu_api(img_base64, prompt)
            
            if "error" in response_data:
                logger.error(f"生成评价失败: {response_data['error']}")
                return {
                    "status": "error",
                    "error": response_data["error"]
                }
            
            review = response_data.get("result", "").strip()
            if not review:
                logger.error("API返回的评价为空")
                return {
                    "status": "error",
                    "error": "生成的评价为空"
                }
            
            logger.info("成功生成评价")
            logger.debug(f"评价内容: {review}")
            return {
                "status": "success",
                "review": review
            }
            
        except Exception as e:
            logger.error(f"生成评价时发生错误: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def extract_features(self, image_path):
        """提取图片的主要特征用于生成提示词"""
        try:
            logger.info("开始提取图片特征")
            img_base64 = self._process_local_image(image_path)
            prompt = """请分析这幅儿童涂鸦的主要特征，并按以下格式返回（用英文回答）：
            1. Main subjects: (描述主要物体/人物)
            2. Colors: (描述主要使用的颜色)
            3. Style: (描述画风特点，如粗犷、细腻等)
            4. Mood: (描述画面情绪/氛围)
            5. Special details: (描述任何特别之处)"""
            
            response_data = self._call_baidu_api(img_base64, prompt)
            
            if "error" in response_data:
                logger.error(f"提取特征失败: {response_data['error']}")
                return {
                    "status": "error",
                    "error": response_data["error"]
                }
            
            features = response_data.get("result", "").strip()
            if not features:
                logger.error("API返回的特征为空")
                return {
                    "status": "error",
                    "error": "提取的特征为空"
                }
            
            logger.info("成功提取特征")
            logger.debug(f"特征内容: {features}")
            return {
                "status": "success",
                "features": features
            }
            
        except Exception as e:
            logger.error(f"提取特征时发生错误: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def analyze(self, image_path):
        """完整分析图像，返回幽默评价和特征提取结果"""
        logger.info(f"开始分析图片: {image_path}")
        
        review_result = self.get_humorous_review(image_path)
        features_result = self.extract_features(image_path)
        
        if review_result["status"] == "error" and features_result["status"] == "error":
            logger.error("评价生成和特征提取都失败了")
            return {
                "status": "error",
                "error": {
                    "review_error": review_result["error"],
                    "features_error": features_result["error"]
                }
            }
        
        result = {
            "status": "success",
            "review": review_result.get("review", "无法生成评价"),
            "features": features_result.get("features", "无法提取特征"),
            "partial_success": review_result["status"] != "success" or features_result["status"] != "success"
        }
        
        logger.info("图片分析完成")
        logger.debug(f"分析结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
        return result 