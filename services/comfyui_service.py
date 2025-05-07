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
    
    def enhance_image(self, image_path, denoise_value=60):
        """使用ComfyUI美化图片"""
        try:
            logger.info("开始处理图片美化任务")
            
            if not os.path.exists(image_path):
                logger.error(f"图片文件不存在: {image_path}")
                return None
            
            # 将百分比转换为0-1.0范围的值
            denoise_value = float(denoise_value) / 100.0
            
            if not 0.0 <= denoise_value <= 1.0:
                logger.error(f"降噪值必须在0%到100%之间, 当前值: {denoise_value * 100}%")
                return None
            
            original_filename = os.path.basename(image_path)
            logger.info(f"处理文件名: {original_filename}")
            
            # 获取文件大小
            file_size = os.path.getsize(image_path)
            logger.info(f"原始图片文件大小: {file_size} 字节")
            
            # 使用任务协调器处理图片
            logger.info(f"开始使用任务协调器处理图片: {image_path}")
            result = self.task_coordinator.process_image(image_path)
            if result.get("status") == "error":
                logger.error(f"图片处理失败: {result.get('error')}")
                return None
            
            # 获取提示词
            positive_prompt = result["prompts"]["positive_prompt"]
            negative_prompt = result["prompts"]["negative_prompt"]
            
            # 输出提示词
            print("\n" + "="*50)
            print("图片美化提示词信息:")
            print("-"*50)
            print(f"正面提示词: {positive_prompt}")
            print("-"*50)
            print(f"负面提示词: {negative_prompt}")
            print("="*50 + "\n")
            
            # 同时记录到日志
            logger.info("\n=== 图片美化提示词 ===")
            logger.info(f"正面提示词: {positive_prompt}")
            logger.info(f"负面提示词: {negative_prompt}")
            logger.info("=====================\n")
            
            comfyui_image_path = os.path.join(self.comfyui_input_dir, original_filename)
            logger.info(f"ComfyUI输入图片路径: {comfyui_image_path}")
            
            # 复制并转换图片为PNG格式
            try:
                with Image.open(image_path) as img:
                    if img.mode != 'RGB':
                        logger.info(f"转换图片模式: {img.mode} -> RGB")
                        img = img.convert('RGB')
                    img.save(comfyui_image_path, 'PNG')
                    logger.info(f"已保存处理图片: {comfyui_image_path}")
            except Exception as e:
                logger.error(f"图片处理失败: {str(e)}")
                logger.exception("图片处理详细错误")
                return None
            
            # 读取工作流配置
            workflow = self._load_workflow('enhance_workflow.json')
            if not workflow:
                logger.error("加载工作流配置失败")
                return None
            
            # 更新工作流配置
            try:
                # 更新图片加载节点
                workflow["50"]["inputs"]["image"] = original_filename
                
                # 更新降噪值（通过 FloatSlider 节点）
                workflow["48"]["inputs"]["float_value"] = denoise_value
                
                # 更新提示词
                workflow["6"]["inputs"]["text"] = positive_prompt
                workflow["7"]["inputs"]["text"] = negative_prompt
                
                # 更新 LoRA
                workflow["28"]["inputs"]["lora_name"] = "白边贴纸·风格_v1.0.safetensors"
                
                logger.info("已更新工作流配置")
                logger.debug(f"工作流配置详情:")
                logger.debug(f"- 输入图片: {original_filename}")
                logger.debug(f"- 降噪值: {denoise_value}")
                logger.debug(f"- 正面提示词: {positive_prompt}")
                logger.debug(f"- 负面提示词: {negative_prompt}")
            except KeyError as e:
                logger.error(f"工作流配置错误: {str(e)}")
                return None
            
            # 发送工作流
            prompt_id = self._queue_prompt(workflow)
            if not prompt_id:
                logger.error("无法将工作流加入队列")
                return None
            logger.info(f"工作流已加入队列，prompt_id: {prompt_id}")
            
            # 等待处理完成
            output = self._wait_for_output(prompt_id)
            if not output:
                logger.error("工作流处理失败或超时")
                return None
            logger.info(f"工作流处理完成，输出: {output}")
            
            # 保存美化后的图片
            enhanced_filename = f"enhanced_{original_filename}"
            output_path = os.path.join('uploads', enhanced_filename)
            logger.info(f"准备保存美化后的图片: {output_path}")
            
            if self._save_output(output, output_path):
                logger.info(f"美化后的图片已保存: {output_path}")
                
                # 检查文件是否存在和大小
                if os.path.exists(output_path):
                    enhanced_size = os.path.getsize(output_path)
                    logger.info(f"美化后图片文件大小: {enhanced_size} 字节")
                else:
                    logger.error(f"美化后图片文件不存在: {output_path}")
            else:
                logger.error(f"保存美化后的图片失败")
                return None
            
            # 清理临时文件
            try:
                os.remove(comfyui_image_path)
                logger.info("已清理临时文件")
            except Exception as e:
                logger.info(f"清理临时文件失败: {str(e)}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"图片美化失败: {str(e)}")
            logger.exception("美化图片详细错误信息")
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
            
            # 使用任务协调器分析图片
            task_coordinator = TaskCoordinator()
            analysis_result = task_coordinator.image_analyzer.analyze_image(image_path)
            
            if analysis_result.get("status") == "error":
                raise Exception(f"图片分析失败: {analysis_result.get('error')}")
            
            # 从分析结果中获取主体描述
            objects = analysis_result.get('objects', [])
            if not objects:
                subject = "a character"  # 默认值
            else:
                # 使用第一个检测到的物体作为主体
                subject = f"a {objects[0]}"
            
            # 动作提示词配置
            action_prompts = {
                'smile': f"{subject}, smiling, lips slightly open, eyes winking, cheerful expression, white background",
                'wave': f"{subject}, waving hands, arms raised, friendly gesture, dynamic pose, white background",
                'dance': f"{subject}, dancing, arms up, legs moving, joyful movement, dynamic pose, white background",
                'walk': f"{subject}, walking, legs in motion, arms swinging, natural stride, white background",
                'jump': f"{subject}, jumping, legs bent, arms up, mid-air pose, dynamic movement, white background",
                'spin': f"{subject}, spinning, arms spread, body rotating, dynamic motion, white background"
            }
            
            # 获取当前动作的提示词
            current_prompt = action_prompts.get(action, action_prompts['smile'])
            logger.info(f"\n=== 动画生成提示词 ===")
            logger.info(f"检测到的物体: {objects}")
            logger.info(f"选择的主体: {subject}")
            logger.info(f"动作: {action}")
            logger.info(f"完整提示词: {current_prompt}")
            logger.info("=====================\n")
            
            # 加载动画工作流
            workflow = self._load_workflow('animation_workflow.json')
            
            # 更新工作流配置
            workflow["150"]["inputs"]["image"] = input_filename
            workflow["166"]["inputs"]["string"] = current_prompt
            
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
    
    def _extract_subject(self, description):
        """从描述中提取主体"""
        try:
            # 移除标点符号
            description = description.replace('.', '').replace(',', '')
            
            # 分割成单词
            words = description.lower().split()
            
            # 查找量词和主体
            subject_words = []
            found_article = False
            
            for word in words:
                if word in ['a', 'an', 'the']:
                    found_article = True
                    subject_words.append(word)
                elif found_article:
                    subject_words.append(word)
                    # 如果遇到介词或连词，停止收集
                    if word in ['in', 'on', 'at', 'with', 'and', 'or', 'but']:
                        break
            
            if subject_words:
                return ' '.join(subject_words)
            return None
            
        except Exception as e:
            logger.error(f"提取主体失败: {str(e)}")
            return None
    
    def _load_workflow(self, workflow_name):
        """加载ComfyUI工作流配置"""
        try:
            workflow_path = os.path.join('workflows', workflow_name)
            if not os.path.exists(workflow_path):
                raise Exception(f"工作流文件不存在: {workflow_path}")
                
            with open(workflow_path, 'r', encoding='utf-8') as f:
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
            workflow_start_time = time.time()
            logger.info(f"开始等待工作流 {prompt_id} 的输出，超时时间: {timeout}秒")
            
            # 从工作流中获取输入文件名
            input_filename = None
            try:
                response = requests.get(f"{self.comfyui_url}/history")
                if response.status_code == 200:
                    history = response.json()
                    if prompt_id in history:
                        prompt_info = history[prompt_id]
                        if "prompt" in prompt_info:
                            workflow = prompt_info["prompt"]
                            if "150" in workflow and "inputs" in workflow["150"] and "image" in workflow["150"]["inputs"]:
                                input_filename = workflow["150"]["inputs"]["image"]
                                logger.info(f"找到输入文件名: {input_filename}")
            except Exception as e:
                logger.error(f"获取输入文件名失败: {str(e)}")
            
            # 确保输出目录存在
            output_dir = os.path.join(self.comfyui_root, "output")
            logger.info(f"ComfyUI输出目录: {output_dir}")
            if not os.path.exists(output_dir):
                logger.error(f"ComfyUI输出目录不存在: {output_dir}")
                raise Exception(f"ComfyUI输出目录不存在: {output_dir}")
            
            while True:
                # 检查是否超时
                if time.time() - workflow_start_time > timeout:
                    logger.error(f"等待工作流 {prompt_id} 输出超时")
                    # 在超时时尝试查找最新的GIF文件
                    gif_files = []
                    for file in os.listdir(output_dir):
                        if file.endswith('.gif'):
                            file_path = os.path.join(output_dir, file)
                            file_time = os.path.getmtime(file_path)
                            gif_files.append((file_path, file_time))
                            logger.debug(f"找到GIF文件: {file_path}, 修改时间: {file_time}")
                    
                    if gif_files:
                        latest_gif = max(gif_files, key=lambda x: x[1])
                        logger.info(f"找到最新的GIF文件: {latest_gif[0]}")
                        return [latest_gif[0]]
                    else:
                        raise Exception("等待输出超时")

                # 检查历史记录
                history_url = f"{self.comfyui_url}/history"
                try:
                    response = requests.get(history_url)
                    if response.status_code != 200:
                        logger.error(f"获取历史记录失败: HTTP {response.status_code}")
                        time.sleep(1)
                        continue

                    history = response.json()
                    if prompt_id not in history:
                        logger.debug(f"工作流 {prompt_id} 尚未完成，继续等待...")
                        time.sleep(1)
                        continue

                    prompt_info = history[prompt_id]
                    logger.debug(f"工作流状态: {prompt_info.get('status', {})}")
                    
                    # 检查是否执行完成
                    if "outputs" in prompt_info:
                        # 获取输出文件路径
                        output_files = []
                        for node_id, node_output in prompt_info["outputs"].items():
                            logger.debug(f"检查节点 {node_id} 的输出")
                            if "images" in node_output:
                                for image in node_output["images"]:
                                    file_path = os.path.join(output_dir, image["filename"])
                                    logger.debug(f"检查输出文件: {file_path}")
                                    if os.path.exists(file_path):
                                        output_files.append(file_path)
                                        logger.info(f"找到有效输出文件: {file_path}")
                                    else:
                                        logger.warning(f"输出文件不存在: {file_path}")
                        
                        if output_files:
                            logger.info(f"工作流完成，找到 {len(output_files)} 个输出文件")
                            return output_files
                        else:
                            # 查找最新的GIF文件
                            gif_files = []
                            for file in os.listdir(output_dir):
                                if file.endswith('.gif'):
                                    file_path = os.path.join(output_dir, file)
                                    file_time = os.path.getmtime(file_path)
                                    gif_files.append((file_path, file_time))
                                    logger.debug(f"找到GIF文件: {file_path}, 修改时间: {file_time}")
                            
                            if gif_files:
                                # 按修改时间排序，获取最新的文件
                                latest_gif = max(gif_files, key=lambda x: x[1])
                                logger.info(f"找到最新的GIF文件: {latest_gif[0]}")
                                return [latest_gif[0]]
                            else:
                                logger.warning("未找到GIF文件")
                                # 列出输出目录中的所有文件
                                logger.info("输出目录中的文件:")
                                for file in os.listdir(output_dir):
                                    file_path = os.path.join(output_dir, file)
                                    file_time = os.path.getmtime(file_path)
                                    logger.info(f"  - {file} (修改时间: {file_time})")
                            
                            time.sleep(1)
                            continue
                    
                    # 检查是否出错
                    status = prompt_info.get("status", {})
                    if status.get("status", "") == "error":
                        error_msg = status.get("message", "未知错误")
                        logger.error(f"工作流执行出错: {error_msg}")
                        raise Exception(f"工作流执行出错: {error_msg}")
                    
                    # 检查执行状态
                    if status.get("status", "") == "executing":
                        logger.debug("工作流正在执行中...")
                    elif status.get("status", "") == "completed":
                        logger.debug("工作流已完成，但未找到输出")
                    else:
                        logger.debug(f"工作流状态: {status}")

                except requests.exceptions.RequestException as e:
                    logger.error(f"请求历史记录失败: {str(e)}")
                    time.sleep(1)
                    continue
                except json.JSONDecodeError as e:
                    logger.error(f"解析历史记录响应失败: {str(e)}")
                    time.sleep(1)
                    continue
                except Exception as e:
                    logger.error(f"处理历史记录时发生错误: {str(e)}")
                    time.sleep(1)
                    continue

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
                logger.error("没有输出数据")
                return False

            # 确保输出目录存在
            output_dir = os.path.dirname(output_path)
            if not os.path.exists(output_dir):
                logger.info(f"创建输出目录: {output_dir}")
                os.makedirs(output_dir, exist_ok=True)

            # 检查输出类型
            if isinstance(output_data, list) and len(output_data) > 0:
                # 处理图片输出
                if output_path.endswith('.gif'):
                    # 对于动画输出，直接复制生成的GIF文件
                    gif_path = output_data[0]
                    logger.info(f"处理GIF文件:")
                    logger.info(f"  - 源文件路径: {gif_path}")
                    logger.info(f"  - 目标路径: {output_path}")
                    
                    # 检查源文件是否存在
                    if not os.path.exists(gif_path):
                        logger.error(f"源GIF文件不存在: {gif_path}")
                        # 尝试在ComfyUI输出目录中查找
                        comfyui_output_dir = os.path.join(self.comfyui_root, "output")
                        if os.path.exists(comfyui_output_dir):
                            logger.info(f"搜索ComfyUI输出目录: {comfyui_output_dir}")
                            for file in os.listdir(comfyui_output_dir):
                                if file.endswith('.gif'):
                                    potential_path = os.path.join(comfyui_output_dir, file)
                                    logger.info(f"找到潜在的GIF文件: {potential_path}")
                                    gif_path = potential_path
                                    break
                    
                    if os.path.exists(gif_path):
                        logger.info(f"复制GIF文件: {gif_path} -> {output_path}")
                        shutil.copy2(gif_path, output_path)
                        logger.info(f"已保存动画到: {output_path}")
                    else:
                        logger.error(f"找不到生成的GIF文件: {gif_path}")
                        return False
                else:
                    # 对于普通图片输出，保存第一张图片
                    image_path = output_data[0]
                    logger.info(f"处理图片文件:")
                    logger.info(f"  - 源文件路径: {image_path}")
                    logger.info(f"  - 目标路径: {output_path}")
                    
                    if os.path.exists(image_path):
                        shutil.copy2(image_path, output_path)
                        logger.info(f"已保存图片到: {output_path}")
                    else:
                        logger.error(f"找不到生成的图片文件: {image_path}")
                        return False
            else:
                logger.error(f"无效的输出数据格式: {type(output_data)}")
                return False
            
            # 验证输出文件是否创建成功
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                logger.info(f"输出文件大小: {file_size} 字节")
                if file_size == 0:
                    logger.error("输出文件大小为0")
                    return False
                return True
            else:
                logger.error(f"输出文件不存在: {output_path}")
                return False

        except Exception as e:
            logger.error(f"保存输出失败: {str(e)}")
            logger.exception("保存输出详细错误")
            return False 