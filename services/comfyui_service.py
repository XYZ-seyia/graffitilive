import requests
import json
import os
import logging
from PIL import Image
import io

logger = logging.getLogger(__name__)

class ComfyUIService:
    def __init__(self, comfyui_url):
        self.comfyui_url = comfyui_url
        self.client_id = "kids_art_project"
    
    def enhance_image(self, image_path):
        """使用ComfyUI美化图片"""
        try:
            # 读取图片
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            # 准备API请求
            workflow = self._load_workflow('enhance_workflow.json')
            workflow['inputs']['image'] = image_data
            
            # 发送请求
            response = requests.post(
                f"{self.comfyui_url}/prompt",
                json=workflow
            )
            
            if response.status_code != 200:
                logger.error(f"ComfyUI enhancement failed: {response.text}")
                return None
            
            # 处理响应
            result = response.json()
            if 'output' not in result:
                logger.error("No output in ComfyUI response")
                return None
            
            # 保存美化后的图片
            output_path = os.path.join('static/output', f"enhanced_{os.path.basename(image_path)}")
            with open(output_path, 'wb') as f:
                f.write(result['output'])
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error in enhance_image: {str(e)}")
            return None
    
    def create_animation(self, image_path, prompts):
        """使用ComfyUI将图片转换为动图"""
        try:
            # 读取图片
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            # 准备API请求
            workflow = self._load_workflow('animation_workflow.json')
            workflow['inputs']['image'] = image_data
            workflow['inputs']['prompt'] = prompts['animation_prompt']
            
            # 发送请求
            response = requests.post(
                f"{self.comfyui_url}/prompt",
                json=workflow
            )
            
            if response.status_code != 200:
                logger.error(f"ComfyUI animation failed: {response.text}")
                return None
            
            # 处理响应
            result = response.json()
            if 'output' not in result:
                logger.error("No output in ComfyUI response")
                return None
            
            # 保存动图
            output_path = os.path.join('static/output', f"animated_{os.path.basename(image_path)}")
            with open(output_path, 'wb') as f:
                f.write(result['output'])
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error in create_animation: {str(e)}")
            return None
    
    def _load_workflow(self, workflow_name):
        """加载ComfyUI工作流配置"""
        workflow_path = os.path.join('workflows', workflow_name)
        with open(workflow_path, 'r') as f:
            return json.load(f) 