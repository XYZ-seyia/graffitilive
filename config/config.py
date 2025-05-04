import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # ComfyUI配置
    COMFYUI_URL = os.getenv('COMFYUI_URL', 'http://localhost:8188')
    
    # LLM配置
    LLM_STUDIO_URL = os.getenv('LLM_STUDIO_URL', 'http://localhost:1234')
    LLM_MODEL = os.getenv('LLM_MODEL', 'default')
    
    # 文件路径配置
    UPLOAD_FOLDER = 'static/uploads'
    OUTPUT_FOLDER = 'static/output'
    
    # 允许的文件类型
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
    
    # 最大文件大小（5MB）
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024 