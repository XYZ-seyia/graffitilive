import requests

DEEPSEEK_API_KEY = "sk-c9b3ef38f15d4370aea3d260075c1f34"
DEEPSEEK_VL_URL = "https://api.deepseek.com/v1/vl/describe"

def analyze_image_with_deepseek(image_path):
    with open(image_path, "rb") as f:
        files = {"image": f}
        headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}"}
        response = requests.post(DEEPSEEK_VL_URL, files=files, headers=headers)
    if response.status_code == 200:
        return response.json()  # 包含 description 字段
    else:
        print("DeepSeek API error:", response.text)
        return None