import base64
import argparse
import os
import json
import requests
from PIL import Image
import io
import cv2
import numpy as np

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
    
    def extract_key_frames(self, video_path, max_frames=10, frame_interval=30):
        """从视频中提取关键帧"""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return []
        
        frames = []
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        # 计算提取间隔
        interval = max(1, min(frame_interval, total_frames // max_frames))
        
        count = 0
        frame_count = 0
        
        while cap.isOpened() and frame_count < max_frames:
            ret, frame = cap.read()
            if not ret:
                break
            
            if count % interval == 0:
                # 转换为PIL Image
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)
                
                # 调整大小
                max_size = 512
                if img.width > max_size or img.height > max_size:
                    img.thumbnail((max_size, max_size))
                
                # 编码为base64
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='JPEG', quality=50)
                img_byte_arr = img_byte_arr.getvalue()
                frames.append(base64.b64encode(img_byte_arr).decode('utf-8'))
                frame_count += 1
            
            count += 1
        
        cap.release()
        return frames
    
    def analyze_image(self, image_base64, prompt):
        """分析单张图片"""
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
            
            response = requests.post(
                self.base_url,
                headers=headers,
                data=json.dumps(payload),
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                if "choices" in result:
                    choices = result["choices"]
                    if choices and "message" in choices[0]:
                        message = choices[0]["message"]
                        if "content" in message:
                            return message["content"]
            return None
        except Exception as e:
            print(f"分析图片时出错: {str(e)}")
            return None
    
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
            print("检测到视频文件，开始提取关键帧...")
            try:
                frames = self.extract_key_frames(material_path)
                print(f"成功提取 {len(frames)} 个关键帧")
                
                if not frames:
                    return {"error": "无法从视频中提取关键帧"}
                
                # 分析每个关键帧
                frame_analyses = []
                for i, frame_base64 in enumerate(frames):
                    print(f"分析第 {i+1}/{len(frames)} 个关键帧...")
                    analysis = self.analyze_image(frame_base64, prompt)
                    if analysis:
                        frame_analyses.append({
                            "frame_index": i,
                            "analysis": analysis
                        })
                
                if not frame_analyses:
                    return {"error": "无法分析视频帧"}
                
                # 汇总分析结果
                summary_prompt = f"基于以下视频关键帧的分析结果，生成一个综合的视频分析报告，包括：1. 视频内容和场景 2. 视觉风格和构图 3. 色彩搭配 4. 主题和情感 5. 适用的使用场景\n\n" + "\n\n".join([f"帧 {item['frame_index']} 分析: {item['analysis']}" for item in frame_analyses])
                
                summary = self.analyze_image(frames[0], summary_prompt)
                if summary:
                    return {
                        "success": True,
                        "analysis": summary,
                        "frame_analyses": frame_analyses
                    }
                else:
                    return {"error": "无法生成视频分析汇总"}
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
    parser.add_argument("--max-frames", type=int, default=10, help="视频最大提取帧数")
    parser.add_argument("--frame-interval", type=int, default=30, help="视频帧提取间隔")
    
    args = parser.parse_args()
    
    # 创建分析器
    analyzer = Qwen3VLAnalyzer(api_key=args.api_key)
    
    # 分析素材
    result = analyzer.analyze_material(args.material_path, args.prompt)
    
    # 输出结果
    if "success" in result and result["success"]:
        print("\n分析结果:")
        print(result["analysis"])
        
        # 如果是视频分析，输出帧分析详情
        if "frame_analyses" in result:
            print("\n关键帧分析详情:")
            for item in result["frame_analyses"]:
                print(f"\n帧 {item['frame_index']}:")
                print(item['analysis'])
    else:
        print("\n分析失败:")
        print(result.get("error", "未知错误"))
        if "details" in result:
            print("详细信息:", result["details"])

if __name__ == "__main__":
    main()
