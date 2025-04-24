from flask import Flask, render_template, request, jsonify, Response, send_from_directory
import os
import traceback
import logging
from services.comfyui_service import ComfyUIService
from services.llm_service import LLMService
from config.config import Config

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_url_path='/static')
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['OUTPUT_FOLDER'] = 'static/output'

# 确保上传和输出目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# 初始化服务
comfyui_service = ComfyUIService(Config.COMFYUI_URL)
llm_service = LLMService(Config.LLM_STUDIO_URL, Config.LLM_MODEL)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

def process_art_stream(image_path):
    try:
        # 第一步：美化图片
        logger.debug("Starting image enhancement...")
        yield jsonify({"status": "enhancing_image"})
        enhanced_image_path = comfyui_service.enhance_image(image_path)
        if not enhanced_image_path:
            logger.error("Image enhancement failed")
            yield jsonify({"error": "Image enhancement failed"})
            return

        # 第二步：生成提示词
        logger.debug("Generating prompts...")
        yield jsonify({"status": "generating_prompts"})
        prompts = llm_service.generate_prompts(image_path, enhanced_image_path)
        if not prompts:
            logger.error("Prompt generation failed")
            yield jsonify({"error": "Prompt generation failed"})
            return

        # 第三步：转换为动图
        logger.debug("Converting to animation...")
        yield jsonify({"status": "creating_animation"})
        animation_path = comfyui_service.create_animation(enhanced_image_path, prompts)
        if not animation_path:
            logger.error("Animation creation failed")
            yield jsonify({"error": "Animation creation failed"})
            return

        # 返回结果
        yield jsonify({
            "status": "completed",
            "enhanced_image": enhanced_image_path,
            "animation": animation_path,
            "prompts": prompts
        })

    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        logger.error(traceback.format_exc())
        yield jsonify({"error": str(e)})

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    try:
        # 保存上传的图片
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(image_path)
        
        # 处理图片
        return Response(process_art_stream(image_path), mimetype='application/json')
    
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True) 