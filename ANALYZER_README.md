# Qwen3-VL 素材分析工具

本工具使用 Qwen3-VL 视觉语言模型分析素材，可用于内容审核、风格分析、主题识别等场景。

## 功能特点

- 支持图片素材分析
- 可自定义分析提示词
- 支持本地部署的 Qwen3-VL 服务
- 详细的错误处理和结果输出

## 环境要求

- Python 3.7+
- Qwen3-VL 服务（本地部署或云端API）

## 安装依赖

```bash
pip install -r requirements.txt
```

## 启动 Qwen3-VL 服务

在使用本工具前，需要先启动 Qwen3-VL 服务。推荐使用 [Qwen3-VL-WEBUI](https://github.com/QwenLM/Qwen3-VL-WEBUI) 进行本地部署：

1. 克隆仓库：
   ```bash
   git clone https://github.com/QwenLM/Qwen3-VL-WEBUI.git
   cd Qwen3-VL-WEBUI
   ```

2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

3. 启动服务：
   ```bash
   python webui.py
   ```

服务默认在 `http://localhost:8080` 运行。

## 使用方法

### 基本用法

```bash
python qwen3vl_analyzer.py /path/to/image.jpg
```

### 自定义提示词

```bash
python qwen3vl_analyzer.py /path/to/image.jpg --prompt "分析这张图片的构图、色彩搭配和情感表达"
```

### 自定义API地址

```bash
python qwen3vl_analyzer.py /path/to/image.jpg --url "http://localhost:8080"
```

## 示例输出

```
分析结果:
这是一张展示现代办公空间的图片，具有以下特点：

1. **内容**：图片中展示了一个明亮、开放的办公环境，包含办公桌、椅子、书架和一些装饰元素。

2. **风格**：现代简约风格，使用了中性色调（白色、灰色、黑色），线条简洁，空间感强。

3. **主题**：现代办公空间设计，强调功能性和舒适度。

4. **适用场景**：
   - 办公空间设计参考
   - 商业地产宣传
   - 家具产品展示
   - 室内设计灵感

5. **视觉元素**：
   - 大面积的白色墙面和天花板，增强空间感
   - 灰色地毯提供柔和的视觉效果
   - 黑色办公家具增添专业感
   - 书架上的书籍和装饰品增添生活气息
   - 窗外的自然光线让空间更加明亮通透

整体来看，这是一个设计合理、功能完善的现代办公空间，适合用于相关领域的宣传和参考。
```

## 注意事项

1. 确保 Qwen3-VL 服务正在运行
2. 图片文件大小不宜过大，建议控制在 5MB 以内
3. 对于大型图片，可能需要调整 `max_tokens` 参数以获取完整的分析结果
4. 首次使用时，模型可能需要一些时间加载

## 故障排查

- **连接失败**：检查 Qwen3-VL 服务是否正在运行，API 地址是否正确
- **图片编码失败**：检查图片文件是否损坏，格式是否支持
- **分析结果不完整**：增加 `max_tokens` 参数值
- **API 请求失败**：检查网络连接，服务是否正常响应
