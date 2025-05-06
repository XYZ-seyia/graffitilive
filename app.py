from flask import Flask, request, jsonify, send_from_directory, render_template
import os
from werkzeug.utils import secure_filename
from agents.task_coordinator import TaskCoordinator
from services.comfyui_service import ComfyUIService
import logging
import time

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 初始化服务和代理
task_coordinator = TaskCoordinator()
comfyui_service = ComfyUIService("http://localhost:8188")

def allowed_file(filename):
    """检查文件类型是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

def process_uploaded_file(file, denoise_value=0.6):
    """处理上传的文件
    
    Args:
        file: 上传的文件对象
        denoise_value: 降噪值，默认0.6
        
    Returns:
        tuple: (success, data, status_code)
    """
    try:
        if not file:
            logger.error("没有上传文件")
            return False, {'error': '没有上传文件'}, 400
            
        if file.filename == '':
            logger.error("空的文件名")
            return False, {'error': '没有选择文件'}, 400
            
        if not allowed_file(file.filename):
            logger.error(f"不支持的文件格式: {file.filename}")
            return False, {'error': '不支持的文件格式'}, 400
            
        # 保存文件
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # 确保上传目录存在
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # 保存文件
        file.save(filepath)
        logger.info(f"文件已保存: {filepath}")
        
        # 确认文件已保存
        if not os.path.exists(filepath):
            logger.error(f"文件保存失败，文件不存在: {filepath}")
            return False, {'error': '文件保存失败'}, 500
            
        file_size = os.path.getsize(filepath)
        logger.info(f"文件大小: {file_size} 字节")
        
        if file_size == 0:
            logger.error("文件为空")
            return False, {'error': '文件为空'}, 400
            
        return True, {'filepath': filepath, 'filename': filename}, 200
        
    except Exception as e:
        logger.error(f"处理上传文件失败: {str(e)}")
        logger.exception("文件处理详细错误")
        return False, {'error': f'文件处理失败: {str(e)}'}, 500

@app.route('/')
def index():
    """渲染主页"""
    return render_template('index.html')

@app.route('/enhance', methods=['POST'])
def enhance_image():
    """处理图片美化请求"""
    try:
        # 处理上传文件
        success, result, status_code = process_uploaded_file(request.files.get('file'))
        if not success:
            return jsonify(result), status_code
            
        filepath = result['filepath']
        filename = result['filename']
        
        logger.info(f"文件上传成功：{filepath}")
        
        # 检查文件是否存在
        if not os.path.exists(filepath):
            logger.error(f"上传后文件不存在: {filepath}")
            return jsonify({'error': '文件上传后未找到'}), 500
            
        # 获取降噪值
        try:
            denoise_value = float(request.form.get('denoise_value', 0.6))
            if not 0.6 <= denoise_value <= 1.0:
                return jsonify({'error': '降噪值必须在0.6到1.0之间'}), 400
        except ValueError:
            return jsonify({'error': '降噪值格式错误'}), 400
            
        # 使用ComfyUI美化图片
        logger.info(f"开始美化图片: {filepath}, 降噪值: {denoise_value}")
        enhanced_path = comfyui_service.enhance_image(filepath, denoise_value)
        
        if not enhanced_path:
            logger.error("美化图片失败，enhanced_path为空")
            return jsonify({'error': '图片美化失败'}), 500
            
        # 检查美化后的图片是否存在
        if not os.path.exists(enhanced_path):
            logger.error(f"美化后的图片不存在: {enhanced_path}")
            return jsonify({'error': '美化后的图片未找到'}), 500
            
        # 构建响应数据 - 只返回图片路径，不包含评论
        original_url = f"/uploads/{filename}"
        enhanced_url = f"/uploads/{os.path.basename(enhanced_path)}"
        
        logger.info(f"原始图片URL: {original_url}")
        logger.info(f"美化后图片URL: {enhanced_url}")
        logger.info(f"美化后图片文件路径: {enhanced_path}")
        
        response_data = {
            'success': True,
            'original': original_url,
            'enhanced': enhanced_url
        }
            
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"处理失败: {str(e)}")
        logger.exception("详细错误信息")  # 输出详细错误堆栈
        return jsonify({'error': '处理失败', 'details': str(e)}), 500

@app.route('/adjust', methods=['POST'])
def adjust_image():
    """调整图片参数"""
    try:
        data = request.json
        image_path = data.get('image_path', '').split('?')[0]  # 移除查询参数
        denoise_value = float(data.get('denoise_value', 0.6))
        
        if not image_path:
            return jsonify({'status': 'error', 'error': '没有提供图片路径'})
            
        # 验证文件路径
        filename = os.path.basename(image_path)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(filepath):
            return jsonify({'status': 'error', 'error': f"找不到图片文件: {filename}"})
            
        # 验证降噪值
        if not 0.6 <= denoise_value <= 1.0:
            return jsonify({'status': 'error', 'error': f"降噪值必须在0.6到1.0之间，当前值: {denoise_value}"})
            
        # 使用ComfyUI调整图片
        enhanced_path = comfyui_service.enhance_image(filepath, denoise_value)
        if not enhanced_path:
            return jsonify({'status': 'error', 'error': '图片调整失败'})
            
        # 添加时间戳到返回的URL
        timestamp = int(time.time())
        return jsonify({
            'status': 'success',
            'enhanced_image': f"/uploads/{os.path.basename(enhanced_path)}?t={timestamp}"
        })
        
    except ValueError as e:
        logger.error(f"参数错误: {str(e)}")
        return jsonify({'status': 'error', 'error': str(e)})
    except Exception as e:
        logger.error(f"调整失败: {str(e)}")
        return jsonify({'status': 'error', 'error': str(e)})

@app.route('/animate', methods=['POST'])
def animate_image():
    """生成图片动画"""
    try:
        # 处理上传文件
        success, result, status_code = process_uploaded_file(request.files.get('file'))
        if not success:
            return jsonify(result), status_code
            
        filepath = result['filepath']
        filename = result['filename']
        
        # 获取动作参数
        action = request.form.get('action', 'smile')
        logger.info(f"选择的动画动作: {action}")
        
        # 使用ComfyUI生成动画
        animation_path = comfyui_service.create_animation(filepath, action)
        if not animation_path:
            return jsonify({'error': '动画生成失败'}), 500
            
        return jsonify({
            'success': True,
            'original': f"/uploads/{filename}",
            'animation': f"/uploads/{os.path.basename(animation_path)}"
        })
        
    except Exception as e:
        logger.error(f"处理失败: {str(e)}")
        return jsonify({'error': '动画生成失败', 'details': str(e)}), 500

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """提供上传文件的访问"""
    logger.info(f"请求访问文件: {filename}")
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    if not os.path.exists(file_path):
        logger.error(f"请求的文件不存在: {file_path}")
        return "File not found", 404
    
    logger.info(f"文件存在，返回: {file_path}")
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/generate_review', methods=['POST'])
def generate_review():
    """生成图片评论"""
    try:
        data = request.json
        image_path = data.get('image_path', '').split('?')[0]  # 移除查询参数
        
        logger.info(f"收到评论生成请求: {image_path}")
        
        if not image_path:
            logger.error("未提供图片路径")
            return jsonify({'status': 'error', 'error': '没有提供图片路径'})
            
        # 验证文件路径
        filename = os.path.basename(image_path)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(filepath):
            logger.error(f"找不到图片文件: {filepath}")
            return jsonify({'status': 'error', 'error': f"找不到图片文件: {filename}"})
            
        # 使用任务协调器生成评论
        logger.info(f"开始生成图片评论: {filepath}")
        result = task_coordinator.process_image(filepath)
        
        if result.get("status") == "success":
            if result["review"]["status"] == "success":
                logger.info("评论生成成功")
                # 将评论格式化为前端期望的HTML格式
                formatted_review = f"<i class=\"fas fa-comment-dots me-2\"></i>{result['review']['content']}"
                logger.info(f"格式化后的评论: {formatted_review[:50]}...")  # 只记录前50个字符
                return jsonify({
                    'status': 'success',
                    'review': formatted_review,
                    'analysis': result["analysis"]
                })
            else:
                error_msg = f"评论生成失败: {result['review']['error']}"
                logger.error(error_msg)
                return jsonify({'status': 'error', 'error': error_msg})
        else:
            error_msg = f"图片分析失败: {result.get('error')}"
            logger.error(error_msg)
            return jsonify({'status': 'error', 'error': error_msg})
            
    except Exception as e:
        logger.error(f"评论生成失败: {str(e)}")
        return jsonify({'status': 'error', 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True) 