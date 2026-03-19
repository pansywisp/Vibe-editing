import requests
import base64
import json
from PIL import Image
import io
import argparse
import os

class Qwen3VLAnalyzer:
    def __init__(self, base_url="http://localhost:8080"):
        """初始化Qwen3-VL分析器"""
        self.base_url = base_url
    
    def encode_image(self, image_path):
        """将图片编码为base64格式"""
        with Image.open(image_path) as img:
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format=img.format)
            img_byte_arr = img_byte_arr.getvalue()
            return base64.b64encode(img_byte_arr).decode('utf-8')
    
    def analyze_material(self, image_path, prompt="分析这个素材，包括内容、风格、主题、适用场景等"):
        """分析素材并返回结果"""
        # 检查文件是否存在
        if not os.path.exists(image_path):
            return {"error": f"文件不存在: {image_path}"}
        
        # 编码图片
        try:
            image_base64 = self.encode_image(image_path)
        except Exception as e:
            return {"error": f"图片编码失败: {str(e)}"}
        
        # 构建请求数据
        payload = {
            "model": "qwen3-vl-4b-instruct",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image",
                            "data": image_base64
                        }
                    ]
                }
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        # 发送请求
        try:
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                headers={"Content-Type": "application/json"},
                data=json.dumps(payload)
            )
            
            # 检查响应状态
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "analysis": result["choices"][0]["message"]["content"]
                }
            else:
                return {
                    "error": f"API请求失败: {response.status_code}",
                    "details": response.text
                }
        except Exception as e:
            return {"error": f"请求失败: {str(e)}"}

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="使用Qwen3-VL分析素材")
    parser.add_argument("image_path", help="素材图片路径")
    parser.add_argument("--prompt", default="分析这个素材，包括内容、风格、主题、适用场景等", help="分析提示词")
    parser.add_argument("--url", default="http://localhost:8080", help="Qwen3-VL API地址")
    
    args = parser.parse_args()
    
    # 创建分析器
    analyzer = Qwen3VLAnalyzer(base_url=args.url)
    
    # 分析素材
    result = analyzer.analyze_material(args.image_path, args.prompt)
    
    # 输出结果
    if "success" in result and result["success"]:
        print("分析结果:")
        print(result["analysis"])
    else:
        print("分析失败:")
        print(result.get("error", "未知错误"))
        if "details" in result:
            print("详细信息:", result["details"])

if __name__ == "__main__":
    main()
