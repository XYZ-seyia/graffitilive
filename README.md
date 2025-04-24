# 儿童涂鸦美化与动画项目

这是一个基于Flask和ComfyUI的Web应用，可以将儿童涂鸦图片自动美化为精美的图片，并转换为动画效果。项目使用本地LLM Studio进行提示词生成。

## 功能特点

- 上传儿童涂鸦图片
- 自动美化图片
- 生成动画效果
- 使用本地LLM Studio自动生成提示词
- 实时处理进度显示
- 美观的用户界面

## 系统要求

- Python 3.8+
- ComfyUI 服务器
- 本地LLM Studio服务器

## 安装步骤

1. 克隆项目到本地：
```bash
git clone [项目地址]
cd kids_art_project
```

2. 创建并激活虚拟环境：
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

4. 配置环境变量：
创建 `.env` 文件并添加以下内容：
```
COMFYUI_URL=http://localhost:8188
LLM_STUDIO_URL=http://localhost:3000
LLM_MODEL=default
```

## 运行项目

1. 确保ComfyUI服务器正在运行
2. 确保本地LLM Studio服务器正在运行
3. 启动Flask应用：
```bash
python app.py
```
4. 在浏览器中访问 `http://localhost:5000`

## 项目结构

```
kids_art_project/
├── app.py                 # 主应用文件
├── config/
│   └── config.py          # 配置文件
├── services/
│   ├── comfyui_service.py # ComfyUI服务
│   └── llm_service.py     # LLM服务
├── static/
│   ├── uploads/           # 上传文件目录
│   └── output/            # 输出文件目录
├── templates/
│   └── index.html         # 前端模板
├── workflows/             # ComfyUI工作流配置
└── requirements.txt       # 项目依赖
```

## 使用说明

1. 打开网页应用
2. 点击"选择文件"按钮上传儿童涂鸦图片
3. 点击"开始处理"按钮
4. 等待处理完成
5. 查看处理结果，包括：
   - 原始图片
   - 美化后的图片
   - 动画效果
   - 生成的提示词

## 注意事项

- 确保ComfyUI服务器正常运行
- 确保本地LLM Studio服务器正常运行
- 上传的图片大小不要超过5MB
- 支持的图片格式：PNG、JPG、JPEG

## 许可证

MIT License 