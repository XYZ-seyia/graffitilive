import cv2
import numpy as np
from PIL import Image
import logging

logger = logging.getLogger(__name__)

class ImageAnalyzer:
    def __init__(self):
        """初始化图片分析器"""
        pass

    def analyze_image(self, image_path):
        """
        分析图片并返回分析结果
        
        Args:
            image_path (str): 图片文件路径
            
        Returns:
            dict: 包含图片分析结果的字典
        """
        try:
            # 读取图片
            image = cv2.imread(image_path)
            if image is None:
                raise Exception("无法读取图片")

            # 转换为灰度图
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # 分析图片特征
            analysis = {
                "size": image.shape[:2],  # (height, width)
                "channels": image.shape[2] if len(image.shape) > 2 else 1,
                "brightness": self._analyze_brightness(gray),
                "contrast": self._analyze_contrast(gray),
                "noise_level": self._analyze_noise(gray),
                "color_distribution": self._analyze_colors(image),
                "edges": self._analyze_edges(gray)
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"图片分析失败: {str(e)}")
            raise

    def _analyze_brightness(self, gray_image):
        """分析图片亮度"""
        return float(np.mean(gray_image)) / 255.0

    def _analyze_contrast(self, gray_image):
        """分析图片对比度"""
        return float(np.std(gray_image)) / 255.0

    def _analyze_noise(self, gray_image):
        """分析图片噪点水平"""
        # 使用拉普拉斯算子检测边缘
        laplacian = cv2.Laplacian(gray_image, cv2.CV_64F)
        return float(np.var(laplacian)) / 255.0

    def _analyze_colors(self, image):
        """分析图片颜色分布"""
        # 将图片转换为HSV颜色空间
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # 计算主要颜色的分布
        h_hist = cv2.calcHist([hsv], [0], None, [180], [0, 180])
        s_hist = cv2.calcHist([hsv], [1], None, [256], [0, 256])
        v_hist = cv2.calcHist([hsv], [2], None, [256], [0, 256])
        
        # 归一化直方图
        h_hist = h_hist.flatten() / h_hist.sum()
        s_hist = s_hist.flatten() / s_hist.sum()
        v_hist = v_hist.flatten() / v_hist.sum()
        
        return {
            "hue_distribution": h_hist.tolist(),
            "saturation_distribution": s_hist.tolist(),
            "value_distribution": v_hist.tolist()
        }

    def _analyze_edges(self, gray_image):
        """分析图片边缘特征"""
        # 使用Canny边缘检测
        edges = cv2.Canny(gray_image, 100, 200)
        edge_density = float(np.sum(edges > 0)) / (edges.shape[0] * edges.shape[1])
        
        return {
            "edge_density": edge_density,
            "edge_count": int(np.sum(edges > 0))
        } 