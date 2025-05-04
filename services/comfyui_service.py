import requests
import json
import os
import logging
from PIL import Image
import io
import time
import traceback
import shutil
from deepseek_api import analyze_image_with_deepseek

logger = logging.getLogger(__name__)

class ComfyUIService:
    def __init__(self, comfyui_url):
        self.comfyui_url = comfyui_url
        self.client_id = "kids_art_project"
        
        # 获取 ComfyUI 根目录
        self.comfyui_root = r"C:\pinokio\api\comfyui.git\app"
        
        # ComfyUI 的输入目录应该在 ComfyUI 根目录下
        self.comfyui_input_dir = os.path.join(self.comfyui_root, 'input')
        
        # 确保输入目录存在
        if not os.path.exists(self.comfyui_input_dir):
            os.makedirs(self.comfyui_input_dir)
            logger.info(f"创建 ComfyUI 输入目录: {self.comfyui_input_dir}")
        
        # 检查 ComfyUI 目录结构
        logger.info("检查 ComfyUI 目录结构:")
        logger.info(f"ComfyUI根目录: {self.comfyui_root}")
        logger.info(f"ComfyUI输入目录: {self.comfyui_input_dir}")
        
        # 列出 ComfyUI 目录内容
        try:
            logger.info("ComfyUI 目录内容:")
            for root, dirs, files in os.walk(self.comfyui_root):
                logger.info(f"目录: {root}")
                for d in dirs:
                    logger.info(f"  子目录: {d}")
                for f in files:
                    logger.info(f"  文件: {f}")
        except Exception as e:
            logger.warning(f"无法列出 ComfyUI 目录内容: {str(e)}")
    
    def enhance_image(self, image_path, denoise_value=0.6):
        """使用ComfyUI美化图片
        
        Args:
            image_path: 图片路径
            denoise_value: 降噪值，范围0.6-1.0，默认0.6
        """
        try:
            logger.info(f"\n{'='*50}")
            logger.info(f"开始处理图片: {image_path}")
            logger.info(f"降噪值: {denoise_value}")
            logger.info(f"{'='*50}")
            
            # 检查文件是否存在
            if not os.path.exists(image_path):
                raise Exception(f"图片文件不存在: {image_path}")
            
            # 验证降噪值范围
            if not 0.6 <= denoise_value <= 1.0:
                raise Exception(f"降噪值必须在0.6到1.0之间，当前值: {denoise_value}")
            
            # 获取原始图片名称
            original_filename = os.path.basename(image_path)
            logger.info(f"原始图片名称: {original_filename}")
            
            # 分析图片并生成提示词
            try:
                from image_analyzer import ImageAnalyzer
                analyzer = ImageAnalyzer()
                analysis = analyzer.analyze_image(image_path)
                
                logger.info(f"\n图片分析结果:")
                logger.info(f"- 亮度: {analysis['brightness']:.2f}")
                logger.info(f"- 对比度: {analysis['contrast']:.2f}")
                logger.info(f"- 噪点水平: {analysis['noise_level']:.2f}")
                logger.info(f"- 边缘密度: {analysis['edges']['edge_density']:.2f}")
                
                # 生成提示词
                from prompt_generation_agent import PromptGenerationAgent
                prompt_agent = PromptGenerationAgent()
                content_desc = analyzer.analyze_content(image_path)
                if content_desc:
                    # 直接用描述生成英文提示词
                    enhancement_prompt = f"Children's drawing, {content_desc}, cute, simple lines, bright colors"
                else:
                    # 回退到原有分析逻辑
                    enhancement_prompt = "Children's drawing, cute, simple lines, bright colors"
                
                logger.info(f"\n生成的提示词:")
                logger.info(f"\n正面提示词:")
                logger.info(f"{'-'*50}")
                logger.info(enhancement_prompt)
                logger.info(f"{'-'*50}")
                
                logger.info(f"\n负面提示词:")
                logger.info(f"{'-'*50}")
                logger.info(prompts['negative_prompt'])
                logger.info(f"{'-'*50}")
                
                positive_prompt = enhancement_prompt
                negative_prompt = prompts.get('negative_prompt', '')
                
            except Exception as e:
                logger.warning(f"提示词生成失败，使用默认提示词: {str(e)}")
                positive_prompt = "A girl in a blue princess dress, one golden crown on her head, her long, soft brown hair falling naturally, smile expression, The overall cartoon style is brightly colored, with smooth lines, simple and white background, no background elements, sticker, Subject is distinguished from background"
                negative_prompt = "bad hands, text, watermark, low quality, blurry, malformed, abnormal"
                
                logger.info(f"\n使用默认提示词:")
                logger.info(f"\n正面提示词:")
                logger.info(f"{'-'*50}")
                logger.info(positive_prompt)
                logger.info(f"{'-'*50}")
                
                logger.info(f"\n负面提示词:")
                logger.info(f"{'-'*50}")
                logger.info(negative_prompt)
                logger.info(f"{'-'*50}")
            
            # 使用原始文件名
            comfyui_image_path = os.path.join(self.comfyui_input_dir, original_filename)
            
            logger.info(f"准备保存图片到: {comfyui_image_path}")
            
            # 检查 ComfyUI 输入目录权限
            if not os.access(self.comfyui_input_dir, os.W_OK):
                raise Exception(f"没有写入权限: {self.comfyui_input_dir}")
            
            # 复制并转换图片为PNG格式
            try:
                with Image.open(image_path) as img:
                    # 确保图片是RGB模式
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    # 记录图片信息
                    logger.info(f"原始图片信息: 大小={img.size}, 模式={img.mode}")
                    
                    # 确保目标目录存在
                    os.makedirs(self.comfyui_input_dir, exist_ok=True)
                    
                    # 保存图片
                    img.save(comfyui_image_path, 'PNG')
                    logger.info(f"已保存PNG图片到: {comfyui_image_path}")
                    
                    # 验证文件是否成功创建
                    if not os.path.exists(comfyui_image_path):
                        raise Exception(f"无法创建输入文件: {comfyui_image_path}")
                    
                    # 验证文件大小
                    file_size = os.path.getsize(comfyui_image_path)
                    logger.info(f"输入文件大小: {file_size} 字节")
                    if file_size == 0:
                        raise Exception("生成的PNG文件大小为0")
                    
                    # 验证文件权限
                    if not os.access(comfyui_image_path, os.R_OK):
                        raise Exception(f"无法读取文件: {comfyui_image_path}")
                    
                    # 验证图片是否可读
                    try:
                        with Image.open(comfyui_image_path) as test_img:
                            logger.info(f"验证保存的图片: 格式={test_img.format}, 大小={test_img.size}, 模式={test_img.mode}")
                    except Exception as e:
                        raise Exception(f"保存的图片无法读取: {str(e)}")
                    
            except Exception as e:
                raise Exception(f"图片处理失败: {str(e)}")
            
            # 读取工作流配置
            workflow = self._load_workflow('enhance_workflow.json')
            logger.info("成功加载美化工作流配置")
            
            # 更新工作流中的图片路径、降噪值和提示词
            workflow["18"]["inputs"]["image"] = original_filename
            workflow["3"]["inputs"]["denoise"] = denoise_value
            workflow["6"]["inputs"]["text"] = positive_prompt
            workflow["7"]["inputs"]["text"] = negative_prompt
            
            # 更新LoRA模型名称
            workflow["28"]["inputs"]["lora_name"] = "白边贴纸·风格_v1.0.safetensors"
            
            logger.info(f"更新工作流配置: 图片={original_filename}, 降噪值={denoise_value}")
            logger.info(f"正面提示词: {positive_prompt}")
            logger.info(f"负面提示词: {negative_prompt}")
            
            # 发送工作流
            prompt_id = self._queue_prompt(workflow)
            if not prompt_id:
                raise Exception("无法将工作流加入队列")
            logger.info(f"工作流已加入队列，ID: {prompt_id}")
            
            # 等待处理完成
            output = self._wait_for_output(prompt_id)
            if not output:
                raise Exception("工作流处理失败或超时")
            logger.info("工作流处理完成")
            
            # 保存美化后的图片
            output_path = os.path.join('uploads', f"enhanced_{original_filename}")
            self._save_output(output, output_path)
            logger.info(f"美化后的图片已保存: {output_path}")
            
            # 清理ComfyUI输入目录中的临时文件
            try:
                os.remove(comfyui_image_path)
                logger.info(f"已清理临时文件: {comfyui_image_path}")
            except Exception as e:
                logger.warning(f"清理临时文件失败: {str(e)}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"图片美化失败: {str(e)}")
            logger.error(f"错误详情: {traceback.format_exc()}")
            return None
    
    def adjust_image(self, image_path, denoise_value):
        """使用ComfyUI调整图片参数"""
        try:
            # 读取工作流配置
            workflow = self._load_workflow('adjust_workflow.json')
            
            # 更新工作流中的参数
            workflow["18"]["inputs"]["image"] = os.path.basename(image_path)
            workflow["6"]["inputs"]["denoise_strength"] = denoise_value / 100.0
            
            # 发送工作流
            prompt_id = self._queue_prompt(workflow)
            if not prompt_id:
                return None
            
            # 等待处理完成
            output = self._wait_for_output(prompt_id)
            if not output:
                return None
            
            # 保存调整后的图片
            output_path = os.path.join('uploads', f"adjusted_{os.path.basename(image_path)}")
            self._save_output(output, output_path)
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error in adjust_image: {str(e)}")
            return None
    
    def create_animation(self, image_path, action='smile'):
        """使用ComfyUI将图片转换为视频
        
        Args:
            image_path: 图片路径
            action: 动画动作类型，可选值：smile, wave, dance, walk, jump, spin
        """
        try:
            logger.info(f"开始生成动画: {image_path}")
            logger.info(f"选择的动作: {action}")
            
            # 获取ComfyUI的output目录
            comfyui_output_dir = os.path.join(self.comfyui_root, 'output')
            logger.info(f"ComfyUI输出目录: {comfyui_output_dir}")
            
            # 确保output目录存在
            if not os.path.exists(comfyui_output_dir):
                os.makedirs(comfyui_output_dir)
                logger.info(f"创建ComfyUI输出目录: {comfyui_output_dir}")
            
            # 获取output目录中最新的图片（美化工作流输出的图片）
            try:
                # 获取所有ComfyUI开头的PNG文件及其修改时间
                output_files = []
                for f in os.listdir(comfyui_output_dir):
                    if f.startswith('ComfyUI_') and f.endswith('.png'):
                        full_path = os.path.join(comfyui_output_dir, f)
                        mtime = os.path.getmtime(full_path)
                        output_files.append((f, mtime))
                        logger.info(f"找到文件: {f}, 路径: {full_path}, 修改时间: {time.ctime(mtime)}")
                
                if not output_files:
                    raise Exception("output目录中没有找到美化工作流输出的图片")
                
                # 按修改时间排序，获取最新的图片
                latest_file = max(output_files, key=lambda x: x[1])[0]
                latest_file_path = os.path.join(comfyui_output_dir, latest_file)
                logger.info(f"找到最新的美化输出图片: {latest_file}")
                logger.info(f"完整路径: {latest_file_path}")
                logger.info(f"文件是否存在: {os.path.exists(latest_file_path)}")
                logger.info(f"文件大小: {os.path.getsize(latest_file_path)} 字节")
                
                # 验证文件是否可读
                try:
                    with Image.open(latest_file_path) as img:
                        logger.info(f"图片格式: {img.format}, 大小: {img.size}, 模式: {img.mode}")
                except Exception as e:
                    logger.error(f"图片处理失败: {str(e)}")
                    raise Exception(f"图片处理失败: {str(e)}")
                
            except Exception as e:
                raise Exception(f"获取最新输出图片失败: {str(e)}")
            
            # 根据动作生成提示词
            action_prompts = {
                'smile': {
                    'positive': "gentle smile, happy expression, subtle facial movement, soft animation, children's animation style",
                    'negative': "exaggerated smile, fast movement, complex facial expressions, realistic style"
                },
                'wave': {
                    'positive': "gentle hand wave, friendly gesture, smooth arm movement, children's animation style",
                    'negative': "fast movement, complex hand gestures, realistic style, multiple hands"
                },
                'dance': {
                    'positive': "playful dance, gentle movement, happy expression, children's animation style, simple dance steps",
                    'negative': "complex dance moves, fast movement, realistic style, professional dance"
                },
                'walk': {
                    'positive': "gentle walking, cute movement, happy expression, children's animation style, simple steps",
                    'negative': "fast walking, complex movement, realistic style, running"
                },
                'jump': {
                    'positive': "cute jump, gentle bounce, happy expression, children's animation style, simple movement",
                    'negative': "high jump, complex movement, realistic style, multiple jumps"
                },
                'spin': {
                    'positive': "gentle spin, cute rotation, happy expression, children's animation style, simple movement",
                    'negative': "fast spin, complex movement, realistic style, multiple rotations"
                }
            }
            
            # 获取动作对应的提示词
            prompts = action_prompts.get(action, action_prompts['smile'])
            positive_prompt = prompts['positive']
            negative_prompt = prompts['negative']
            
            logger.info(f"正面提示词: {positive_prompt}")
            logger.info(f"负面提示词: {negative_prompt}")
            
            # 读取工作流配置
            workflow = self._load_workflow('animation_workflow.json')
            logger.info("成功加载动画工作流配置")
            
            # 更新工作流中的图片路径和提示词
            workflow["52"]["inputs"]["image"] = latest_file
            workflow["52"]["inputs"]["upload"] = "image"
            workflow["52"]["inputs"]["directory"] = "output"  # 设置从output目录读取
            workflow["6"]["inputs"]["text"] = positive_prompt
            workflow["7"]["inputs"]["text"] = negative_prompt
            
            logger.info(f"更新工作流配置:")
            logger.info(f"- 图片文件名: {latest_file}")
            logger.info(f"- 图片目录: output")
            logger.info(f"- 完整路径: {latest_file_path}")
            logger.info(f"- 正面提示词: {positive_prompt}")
            logger.info(f"- 负面提示词: {negative_prompt}")
            
            # 发送工作流
            prompt_id = self._queue_prompt(workflow)
            if not prompt_id:
                raise Exception("无法将工作流加入队列")
            logger.info(f"工作流已加入队列，ID: {prompt_id}")
            
            # 等待处理完成
            output = self._wait_for_output(prompt_id)
            if not output:
                raise Exception("工作流处理失败或超时")
            logger.info("工作流处理完成")
            
            # 保存视频
            output_path = os.path.join('uploads', f"animation_{os.path.splitext(latest_file)[0]}.gif")
            self._save_output(output, output_path)
            logger.info(f"动画已保存: {output_path}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"动画生成失败: {str(e)}")
            logger.error(f"错误详情: {traceback.format_exc()}")
            return None
    
    def _load_workflow(self, workflow_name):
        """加载ComfyUI工作流配置"""
        try:
            workflow_path = os.path.join('workflows', workflow_name)
            if not os.path.exists(workflow_path):
                raise Exception(f"工作流文件不存在: {workflow_path}")
                
            with open(workflow_path, 'r') as f:
                workflow = json.load(f)
            logger.info(f"成功加载工作流: {workflow_name}")
            return workflow
            
        except Exception as e:
            logger.error(f"加载工作流失败: {str(e)}")
            raise
    
    def _queue_prompt(self, workflow):
        """将工作流发送到ComfyUI队列"""
        try:
            logger.info("正在发送工作流到ComfyUI...")
            logger.debug(f"工作流配置: {json.dumps(workflow, indent=2)}")
            
            # 检查工作流中的图片文件是否存在
            if "18" in workflow and "inputs" in workflow["18"] and "image" in workflow["18"]["inputs"]:
                image_filename = workflow["18"]["inputs"]["image"]
                image_path = os.path.join(self.comfyui_input_dir, image_filename)
                
                # 详细记录文件信息
                logger.info(f"检查图片文件: {image_path}")
                if os.path.exists(image_path):
                    logger.info(f"文件存在，大小: {os.path.getsize(image_path)} 字节")
                    logger.info(f"文件权限: 可读={os.access(image_path, os.R_OK)}, 可写={os.access(image_path, os.W_OK)}")
                    
                    # 尝试打开并验证图片
                    try:
                        with Image.open(image_path) as img:
                            logger.info(f"图片格式: {img.format}, 大小: {img.size}, 模式: {img.mode}")
                            # 确保图片是RGB模式
                            if img.mode != 'RGB':
                                logger.info("转换图片为RGB模式")
                                img = img.convert('RGB')
                                img.save(image_path, 'PNG')
                                logger.info("已重新保存为RGB模式的PNG")
                    except Exception as e:
                        logger.error(f"图片验证失败: {str(e)}")
                        raise Exception(f"图片文件无效: {str(e)}")
                else:
                    raise Exception(f"工作流中引用的图片文件不存在: {image_path}")
            
            # 发送工作流到ComfyUI
            logger.info(f"正在发送工作流到ComfyUI服务器: {self.comfyui_url}/prompt")
            response = requests.post(
                f"{self.comfyui_url}/prompt",
                json={"prompt": workflow}
            )
            
            if response.status_code != 200:
                error_msg = f"ComfyUI服务器返回错误: {response.status_code} - {response.text}"
                logger.error(error_msg)
                
                # 尝试解析错误信息
                try:
                    error_data = response.json()
                    if "node_errors" in error_data:
                        for node_id, node_error in error_data["node_errors"].items():
                            for error in node_error.get("errors", []):
                                logger.error(f"节点 {node_id} 错误: {error.get('details', '未知错误')}")
                except:
                    pass
                
                return None
            
            prompt_id = response.json().get("prompt_id")
            if not prompt_id:
                logger.error("ComfyUI未返回有效的prompt_id")
                return None
                
            return prompt_id
            
        except requests.exceptions.ConnectionError:
            logger.error(f"无法连接到ComfyUI服务器: {self.comfyui_url}")
            return None
        except Exception as e:
            logger.error(f"发送工作流失败: {str(e)}")
            logger.error(f"错误详情: {traceback.format_exc()}")
            return None
    
    def _wait_for_output(self, prompt_id, timeout=300):
        """等待工作流处理完成并获取输出"""
        start_time = time.time()
        logger.info(f"等待工作流处理完成，超时时间: {timeout}秒")
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{self.comfyui_url}/history/{prompt_id}")
                if response.status_code != 200:
                    logger.warning(f"获取工作流状态失败: {response.status_code}")
                    time.sleep(1)
                    continue
                
                history = response.json()
                if prompt_id in history:
                    prompt_data = history[prompt_id]
                    
                    if prompt_data.get("outputs"):
                        logger.info("工作流处理成功，获取到输出")
                        return prompt_data["outputs"]
                    
                    if prompt_data.get("status", {}).get("status") == "error":
                        error_msg = prompt_data.get("status", {}).get("error", "未知错误")
                        logger.error(f"工作流处理失败: {error_msg}")
                        return None
                    
                    logger.debug("工作流正在处理中...")
                else:
                    logger.warning(f"未找到工作流ID: {prompt_id}")
                
                time.sleep(1)
            except Exception as e:
                logger.error(f"检查工作流状态时出错: {str(e)}")
                return None
        
        logger.error(f"工作流处理超时 ({timeout}秒)")
        return None
    
    def _save_output(self, output_data, output_path):
        """保存工作流输出"""
        try:
            logger.info(f"正在保存输出到: {output_path}")
            
            # 获取第一个输出节点的数据
            first_node = next(iter(output_data.values()))
            
            if "images" in first_node:
                # 处理图片输出
                image_data = first_node["images"][0]
                image_url = f"{self.comfyui_url}/view?filename={image_data['filename']}"
                logger.info(f"正在下载图片: {image_url}")
                
                response = requests.get(image_url)
                if response.status_code != 200:
                    raise Exception(f"下载图片失败: {response.status_code}")
                    
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                logger.info("图片保存成功")
                
            elif "animated" in first_node:
                # 处理动画输出
                animation_data = first_node["animated"]
                animation_url = f"{self.comfyui_url}/view?filename={animation_data['filename']}"
                logger.info(f"正在下载动画: {animation_url}")
                
                response = requests.get(animation_url)
                if response.status_code != 200:
                    raise Exception(f"下载动画失败: {response.status_code}")
                    
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                logger.info("动画保存成功")
            else:
                raise Exception("输出数据格式不正确")
                
        except Exception as e:
            logger.error(f"保存输出失败: {str(e)}")
            raise 