from flask import Flask, request, jsonify, send_from_directory, render_template
import os
from werkzeug.utils import secure_filename
from image_analyzer import ImageAnalyzer
from prompt_generation_agent import PromptGenerationAgent
from services.comfyui_service import ComfyUIService
import logging
import requests
import time

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 初始化服务
image_analyzer = ImageAnalyzer()
prompt_agent = PromptGenerationAgent()

# 检查 ComfyUI 服务器是否可用
def check_comfyui_server():
    try:
        response = requests.get("http://localhost:8188/history")
        if response.status_code == 200:
            logger.info("ComfyUI 服务器正在运行")
            return True
        else:
            logger.error(f"ComfyUI 服务器返回错误状态码: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        logger.error("无法连接到 ComfyUI 服务器，请确保服务器正在运行")
        return False

# 初始化 ComfyUI 服务
comfyui_service = None
if check_comfyui_server():
    comfyui_service = ComfyUIService("http://localhost:8188")
else:
    logger.error("ComfyUI 服务初始化失败")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/enhance', methods=['POST'])
def enhance_image():
    if 'file' not in request.files:
        return jsonify({'error': '没有上传文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    if not comfyui_service:
        return jsonify({'error': 'ComfyUI 服务未初始化，请确保服务器正在运行'}), 500
    
    try:
        # 获取降噪值，默认为0.6
        denoise_value = float(request.form.get('denoise_value', 0.6))
        
        # 保存上传的文件
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        logger.info(f"文件已保存: {filepath}")
        
        # 使用 ComfyUI 美化图片
        enhanced_path = comfyui_service.enhance_image(filepath, denoise_value)
        if not enhanced_path:
            return jsonify({'error': '图片美化失败'}), 500
        
        return jsonify({
            'success': True,
            'original': f"/uploads/{filename}",
            'enhanced': f"/uploads/{os.path.basename(enhanced_path)}"
        })
        
    except ValueError:
        logger.error("降噪值格式错误")
        return jsonify({'error': '降噪值必须是0.6到1.0之间的数字'}), 400
    except Exception as e:
        logger.error(f"处理失败: {str(e)}")
        return jsonify({'error': '图片美化失败'}), 500

@app.route('/adjust', methods=['POST'])
def adjust_image():
    data = request.json
    image_path = data.get('image_path')
    denoise_value = float(data.get('denoise_value', 0.6))  # 直接使用浮点数值
    
    if not image_path:
        return jsonify({'status': 'error', 'error': '没有提供图片路径'})
    
    try:
        # 从URL路径获取实际文件路径
        filename = os.path.basename(image_path)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # 验证降噪值范围
        if not 0.6 <= denoise_value <= 1.0:
            raise ValueError(f"降噪值必须在0.6到1.0之间，当前值: {denoise_value}")
        
        # 使用ComfyUI调整图片
        enhanced_path = comfyui_service.enhance_image(filepath, denoise_value)
        if not enhanced_path:
            raise Exception("图片调整失败")
        
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
    if 'file' not in request.files:
        return jsonify({'error': '没有上传文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    # 获取动作参数
    action = request.form.get('action', 'smile')
    logger.info(f"选择的动画动作: {action}")
    
    if not comfyui_service:
        return jsonify({'error': 'ComfyUI 服务未初始化，请确保服务器正在运行'}), 500
    
    try:
        # 保存上传的文件
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        logger.info(f"文件已保存: {filepath}")
        
        # 使用 ComfyUI 生成动画
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
        return jsonify({'error': '动画生成失败'}), 500

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True) 