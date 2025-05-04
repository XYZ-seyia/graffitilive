# 儿童画增强系统

这是一个用于增强儿童绘画作品的Web应用程序。它可以：
1. 上传并分析儿童绘画
2. 自动美化图片质量
3. 调整美化参数
4. 生成简单的动画效果

## 安装

1. 确保你已安装Python 3.7或更高版本
2. 克隆此仓库
3. 安装依赖：
```bash
pip install -r requirements.txt
```

## 使用方法

1. 启动服务器：
```bash
python app.py
```

2. 在浏览器中访问 `http://localhost:5000`

3. 使用步骤：
   - 点击"选择文件"上传儿童绘画图片
   - 等待系统处理并显示美化结果
   - 使用滑块调整美化程度
   - 点击"生成动画"创建动画效果

## 功能说明

- **图片美化**：自动增强图片质量，包括降噪、对比度增强和锐化
- **参数调整**：通过滑块实时调整美化程度
- **动画生成**：将美化后的图片转换为简单的缩放动画

## 注意事项

- 支持的图片格式：PNG、JPG、JPEG、GIF
- 最大文件大小：16MB
- 所有处理后的文件都保存在 `uploads` 目录中

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
2. 点击"选择文件"按钮上传儿童绘画图片
3. 等待系统处理并显示美化结果
4. 使用滑块调整美化程度
5. 点击"生成动画"创建动画效果

## 注意事项

- 确保ComfyUI服务器正常运行
- 确保本地LLM Studio服务器正常运行
- 上传的图片大小不要超过5MB
- 支持的图片格式：PNG、JPG、JPEG

## 许可证

MIT License 