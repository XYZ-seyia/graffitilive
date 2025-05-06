import requests
import json
import os
import logging
from PIL import Image
import io
import time
import traceback
import shutil
from agents.task_coordinator import TaskCoordinator

logger = logging.getLogger(__name__)
# Set default logging level to INFO
logger.setLevel(logging.INFO)

class ComfyUIService:
    def __init__(self, comfyui_url):
        self.comfyui_url = comfyui_url
        self.client_id = "kids_art_project"
        
        # 获取 ComfyUI 根目录
        self.comfyui_root = r"C:\pinokio\api\comfyui.git\app"
        self.comfyui_input_dir = os.path.join(self.comfyui_root, 'input')
        
        # 初始化任务协调器
        self.task_coordinator = TaskCoordinator()
        
        # 确保输入目录存在
        if not os.path.exists(self.comfyui_input_dir):
            os.makedirs(self.comfyui_input_dir)
            logger.info("已初始化 ComfyUI 输入目录")
        
        # 检查 ComfyUI 目录结构
        logger.debug(f"ComfyUI根目录: {self.comfyui_root}")
        logger.debug(f"ComfyUI输入目录: {self.comfyui_input_dir}")
        
        # 列出 ComfyUI 目录内容
        try:
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("ComfyUI 目录内容:")
                for root, dirs, files in os.walk(self.comfyui_root):
                    logger.debug(f"目录: {root}")
                    for d in dirs:
                        logger.debug(f"  子目录: {d}")
                    for f in files:
                        logger.debug(f"  文件: {f}")
        except Exception as e:
            logger.debug(f"无法列出 ComfyUI 目录内容: {str(e)}")
    
    def enhance_image(self, image_path, denoise_value=0.6):
        """使用ComfyUI美化图片"""
        try:
            logger.info("开始处理图片美化任务")
            
            if not os.path.exists(image_path):
                raise Exception(f"图片文件不存在: {image_path}")
            
            if not 0.6 <= denoise_value <= 1.0:
                raise Exception(f"降噪值必须在0.6到1.0之间")
            
            original_filename = os.path.basename(image_path)
            
            # 使用任务协调器处理图片
            result = self.task_coordinator.process_image(image_path)
            if result.get("status") == "error":
                raise Exception(f"图片处理失败: {result.get('error')}")
            
            # 获取提示词
            positive_prompt = result["prompts"]["positive_prompt"]
            negative_prompt = result["prompts"]["negative_prompt"]
            
            # 输出提示词
            print("\n=== 图片美化提示词 ===")
            print(f"正面提示词: {positive_prompt}")
            print(f"负面提示词: {negative_prompt}")
            print("=====================\n")
            
            logger.debug(f"正面提示词: {positive_prompt}")
            logger.debug(f"负面提示词: {negative_prompt}")
            
            comfyui_image_path = os.path.join(self.comfyui_input_dir, original_filename)
            
            # 复制并转换图片为PNG格式
            try:
                with Image.open(image_path) as img:
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    img.save(comfyui_image_path, 'PNG')
                    logger.debug(f"已保存处理图片: {comfyui_image_path}")
            except Exception as e:
                raise Exception(f"图片处理失败: {str(e)}")
            
            # 读取工作流配置
            workflow = self._load_workflow('enhance_workflow.json')
            
            # 更新工作流配置
            workflow["18"]["inputs"]["image"] = original_filename
            workflow["3"]["inputs"]["denoise"] = denoise_value
            workflow["6"]["inputs"]["text"] = positive_prompt
            workflow["7"]["inputs"]["text"] = negative_prompt
            workflow["28"]["inputs"]["lora_name"] = "白边贴纸·风格_v1.0.safetensors"
            
            # 发送工作流
            prompt_id = self._queue_prompt(workflow)
            if not prompt_id:
                raise Exception("无法将工作流加入队列")
            
            # 等待处理完成
            output = self._wait_for_output(prompt_id)
            if not output:
                raise Exception("工作流处理失败或超时")
            
            # 保存美化后的图片
            output_path = os.path.join('uploads', f"enhanced_{original_filename}")
            self._save_output(output, output_path)
            logger.info("图片美化完成")
            
            # 清理临时文件
            try:
                os.remove(comfyui_image_path)
                logger.debug("已清理临时文件")
            except Exception as e:
                logger.debug(f"清理临时文件失败: {str(e)}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"图片美化失败: {str(e)}")
            return None
    
    def adjust_image(self, image_path, denoise_value):
        """使用ComfyUI调整图片参数"""
        try:
            logger.info("开始处理图片调整任务")
            
            workflow = self._load_workflow('adjust_workflow.json')
            
            workflow["18"]["inputs"]["image"] = os.path.basename(image_path)
            workflow["6"]["inputs"]["denoise_strength"] = denoise_value / 100.0
            
            prompt_id = self._queue_prompt(workflow)
            if not prompt_id:
                return None
            
            output = self._wait_for_output(prompt_id)
            if not output:
                return None
            
            output_path = os.path.join('uploads', f"adjusted_{os.path.basename(image_path)}")
            self._save_output(output, output_path)
            
            logger.info("图片调整完成")
            return output_path
            
        except Exception as e:
            logger.error(f"图片调整失败: {str(e)}")
            return None
    
    def create_animation(self, image_path, action='smile'):
        """使用ComfyUI将图片转换为视频"""
        try:
            logger.info("开始生成动画任务")
            
            if not os.path.exists(image_path):
                raise Exception(f"输入图片不存在: {image_path}")
            
            # 复制输入图片到ComfyUI输入目录
            input_filename = os.path.basename(image_path)
            comfyui_input_path = os.path.join(self.comfyui_input_dir, input_filename)
            
            try:
                shutil.copy2(image_path, comfyui_input_path)
                logger.debug(f"已复制输入图片到ComfyUI: {comfyui_input_path}")
            except Exception as e:
                raise Exception(f"复制输入图片失败: {str(e)}")
            
            # 动作提示词配置
            action_prompts = {
                'smile': "a cute little girl, smiling, white background",
                'wave': "a cute little girl, waving hands, white background",
                'dance': "a cute little girl, dancing, white background",
                'walk': "a cute little girl, walking, white background",
                'jump': "a cute little girl, jumping, white background",
                'spin': "a cute little girl, spinning, white background"
            }
            
            # 加载动画工作流
            workflow = self._load_workflow('animation_workflow.json')
            
            # 更新工作流配置
            workflow["150"]["inputs"]["image"] = input_filename
            workflow["166"]["inputs"]["string"] = action_prompts.get(action, action_prompts['smile'])
            
            # 发送工作流到队列
            prompt_id = self._queue_prompt(workflow)
            if not prompt_id:
                raise Exception("无法将工作流加入队列")
            
            # 等待处理完成
            output = self._wait_for_output(prompt_id, timeout=600)  # 增加超时时间到10分钟
            if not output:
                raise Exception("工作流处理失败或超时")
            
            # 保存生成的动画
            output_filename = f"animated_{os.path.splitext(input_filename)[0]}.gif"
            output_path = os.path.join('uploads', output_filename)
            self._save_output(output, output_path)
            
            # 清理临时文件
            try:
                os.remove(comfyui_input_path)
                logger.debug("已清理临时文件")
            except Exception as e:
                logger.debug(f"清理临时文件失败: {str(e)}")
            
            logger.info("动画生成完成")
            return output_path
            
        except Exception as e:
            logger.error(f"动画生成失败: {str(e)}")
            logger.error(traceback.format_exc())
            return None
    
    def _load_workflow(self, workflow_name):
        """加载ComfyUI工作流配置"""
        try:
            workflow_path = os.path.join('workflows', workflow_name)
            if not os.path.exists(workflow_path):
                raise Exception(f"工作流文件不存在: {workflow_path}")
                
            with open(workflow_path, 'r') as f:
                workflow = json.load(f)
            logger.debug(f"已加载工作流: {workflow_name}")
            return workflow
            
        except Exception as e:
            logger.error(f"加载工作流失败: {str(e)}")
            raise
    
    def _queue_prompt(self, workflow):
        """将工作流发送到ComfyUI队列"""
        try:
            logger.debug("正在发送工作流到ComfyUI...")
            
            # 验证输入图片
            if "18" in workflow and "inputs" in workflow["18"] and "image" in workflow["18"]["inputs"]:
                image_filename = workflow["18"]["inputs"]["image"]
                image_path = os.path.join(self.comfyui_input_dir, image_filename)
                
                if not os.path.exists(image_path):
                    raise Exception(f"输入图片不存在: {image_path}")
                
                # 验证图片格式
                try:
                    with Image.open(image_path) as img:
                        if img.mode != 'RGB':
                            img = img.convert('RGB')
                            img.save(image_path, 'PNG')
                            logger.debug("已转换图片为RGB模式")
                except Exception as e:
                    raise Exception(f"图片验证失败: {str(e)}")
            
            response = requests.post(
                f"{self.comfyui_url}/prompt",
                json={"prompt": workflow}
            )
            
            if response.status_code != 200:
                error_msg = f"ComfyUI服务器返回错误: {response.status_code}"
                logger.error(error_msg)
                return None
            
            prompt_id = response.json().get("prompt_id")
            if not prompt_id:
                logger.error("未获取到有效的prompt_id")
                return None
                
            return prompt_id
            
        except requests.exceptions.ConnectionError:
            logger.error(f"无法连接到ComfyUI服务器")
            return None
        except Exception as e:
            logger.error(f"发送工作流失败: {str(e)}")
            return None
    
    def _wait_for_output(self, prompt_id, timeout=600):
        """等待工作流执行完成并获取输出"""
        try:
            start_time = time.time()
            while True:
                if time.time() - start_time > timeout:
                    raise Exception("等待输出超时")

                # 检查历史记录
                history_url = f"{self.comfyui_url}/history"
                response = requests.get(history_url)
                if response.status_code != 200:
                    raise Exception(f"获取历史记录失败: {response.status_code}")

                history = response.json()
                if prompt_id in history:
                    prompt_info = history[prompt_id]
                    
                    # 检查是否执行完成
                    if "outputs" in prompt_info and prompt_info.get("status", {}).get("status", "") == "success":
                        # 获取输出文件路径
                        output_files = []
                        for node_id, node_output in prompt_info["outputs"].items():
                            if "images" in node_output:
                                for image in node_output["images"]:
                                    file_path = os.path.join(self.comfyui_root, "output", image["filename"])
                                    if os.path.exists(file_path):
                                        output_files.append(file_path)
                        
                        if output_files:
                            return output_files
                        else:
                            raise Exception("找不到输出文件")
                    
                    # 检查是否出错
                    if prompt_info.get("status", {}).get("status", "") == "error":
                        error_msg = prompt_info.get("status", {}).get("message", "未知错误")
                        raise Exception(f"工作流执行出错: {error_msg}")

                # 等待一段时间后再次检查
                time.sleep(1)

        except Exception as e:
            logger.error(f"等待输出失败: {str(e)}")
            logger.error(traceback.format_exc())
            return None
    
    def _save_output(self, output_data, output_path):
        """保存ComfyUI的输出"""
        try:
            if not output_data:
                raise Exception("没有输出数据")

            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # 检查输出类型
            if isinstance(output_data, list) and len(output_data) > 0:
                # 处理图片输出
                if output_path.endswith('.gif'):
                    # 对于动画输出，直接复制生成的GIF文件
                    gif_path = output_data[0]
                    if os.path.exists(gif_path):
                        shutil.copy2(gif_path, output_path)
                        logger.info(f"已保存动画到: {output_path}")
                    else:
                        raise Exception(f"找不到生成的GIF文件: {gif_path}")
                else:
                    # 对于普通图片输出，保存第一张图片
                    image_path = output_data[0]
                    if os.path.exists(image_path):
                        shutil.copy2(image_path, output_path)
                        logger.info(f"已保存图片到: {output_path}")
                    else:
                        raise Exception(f"找不到生成的图片文件: {image_path}")
            else:
                raise Exception("无效的输出数据格式")

            return True

        except Exception as e:
            logger.error(f"保存输出失败: {str(e)}")
            logger.error(traceback.format_exc())
            return False 