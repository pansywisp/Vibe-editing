import base64
import argparse
import os
import json
import requests
from PIL import Image
import io

# 尝试导入pillow-heif以支持HEIC格式
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    pass

class Qwen3VLAnalyzer:
    def __init__(self, api_key=None):
        """初始化Qwen3-VL分析器"""
        self.api_key = api_key
        self.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
    
    def encode_image(self, image_path):
        """将图片编码为base64格式"""
        with Image.open(image_path) as img:
            # 调整图片大小以减少请求大小
            max_size = 512
            if img.width > max_size or img.height > max_size:
                img.thumbnail((max_size, max_size))
            
            img_byte_arr = io.BytesIO()
            # 降低图片质量以减小大小
            img.save(img_byte_arr, format='JPEG', quality=50)
            img_byte_arr = img_byte_arr.getvalue()
            return base64.b64encode(img_byte_arr).decode('utf-8')
    
    def encode_video(self, video_path):
        """将视频编码为base64格式"""
        with open(video_path, 'rb') as f:
            video_data = f.read()
        return base64.b64encode(video_data).decode('utf-8')
    
    def analyze_material(self, material_path, prompt="分析这个素材，包括内容、风格、主题、适用场景等"):
        """分析素材（图片或视频）并返回结果"""
        # 检查文件是否存在
        if not os.path.exists(material_path):
            return {"error": f"文件不存在: {material_path}"}
        
        # 判断文件类型
        ext = os.path.splitext(material_path)[1].lower()
        is_video = ext in ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv']
        
        if is_video:
            # 处理视频
            print("检测到视频文件，开始分析...")
            try:
                # 编码视频
                video_base64 = self.encode_video(material_path)
                print("视频编码成功，大小:", len(video_base64), "字符")
                
                # 构建请求数据（OpenAI兼容格式）
                payload = {
                    "model": "qwen3.5-plus",  # 使用Qwen3.5 Plus模型
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"{prompt}，请同时分析视频中的声音内容"
                                },
                                {
                                    "type": "video_url",
                                    "video_url": {
                                        "url": f"data:video/mp4;base64,{video_base64}"
                                    }
                                }
                            ]
                        }
                    ],
                    "temperature": 0.7,
                    "max_tokens": 2000
                }
                
                # 发送请求
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                }
                
                print("发送API请求...")
                response = requests.post(
                    self.base_url,
                    headers=headers,
                    data=json.dumps(payload),
                    timeout=120  # 视频分析需要更长的超时时间
                )
                
                print("响应状态码:", response.status_code)
                print("响应内容:", response.text[:500], "...")
                
                if response.status_code == 200:
                    result = response.json()
                    # 解析OpenAI兼容格式的响应
                    if "choices" in result:
                        choices = result["choices"]
                        if choices and "message" in choices[0]:
                            message = choices[0]["message"]
                            if "content" in message:
                                return {
                                    "success": True,
                                    "analysis": message["content"]
                                }
                    return {"error": "API返回格式错误"}
                else:
                    return {
                        "error": f"API请求失败: {response.status_code}",
                        "details": response.text
                    }
            except Exception as e:
                return {"error": f"视频处理失败: {str(e)}"}
        else:
            # 处理图片
            try:
                image_base64 = self.encode_image(material_path)
                print("图片编码成功，大小:", len(image_base64), "字符")
            except Exception as e:
                return {"error": f"图片编码失败: {str(e)}"}
            
            # 构建请求数据（OpenAI兼容格式）
            payload = {
                "model": "qwen3.5-plus",  # 使用Qwen3.5 Plus模型
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 1000
            }
            
            # 发送请求
            try:
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                }
                
                print("发送API请求...")
                response = requests.post(
                    self.base_url,
                    headers=headers,
                    data=json.dumps(payload),
                    timeout=60
                )
                
                print("响应状态码:", response.status_code)
                print("响应内容:", response.text[:500], "...")
                
                if response.status_code == 200:
                    result = response.json()
                    # 解析OpenAI兼容格式的响应
                    if "choices" in result:
                        choices = result["choices"]
                        if choices and "message" in choices[0]:
                            message = choices[0]["message"]
                            if "content" in message:
                                return {
                                    "success": True,
                                    "analysis": message["content"]
                                }
                    return {"error": "API返回格式错误"}
                else:
                    return {
                        "error": f"API请求失败: {response.status_code}",
                        "details": response.text
                    }
            except Exception as e:
                return {"error": f"请求失败: {str(e)}"}

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="使用Qwen3-VL分析素材（支持图片和视频）")
    parser.add_argument("material_path", help="素材路径（图片或视频）")
    parser.add_argument("--prompt", default="分析这个素材，包括内容、风格、主题、适用场景等", help="分析提示词")
    parser.add_argument("--api-key", default=None, help="API密钥")
    
    args = parser.parse_args()
    
    # 创建分析器
    analyzer = Qwen3VLAnalyzer(api_key=args.api_key)
    
    # 分析素材
    result = analyzer.analyze_material(args.material_path, args.prompt)
    
    # 输出结果
    if "success" in result and result["success"]:
        print("\n分析结果:")
        print(result["analysis"])
    else:
        print("\n分析失败:")
        print(result.get("error", "未知错误"))
        if "details" in result:
            print("详细信息:", result["details"])

if __name__ == "__main__":
    main()
