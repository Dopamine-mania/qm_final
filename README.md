# 情感视频生成系统

这是一个基于情感理解的多模态内容生成系统，可以根据用户输入的文本生成相应的视频内容。

## 系统功能

系统由以下几个模块组成：

1. **情感理解模块 (Emo_LLM)**: 分析用户输入的文本，生成情感标签和多模态提示词
2. **文本到图像模块 (TTI)**: 根据提示词生成相关图像
3. **文本到语音模块 (TTS)**: 根据语音文本生成语音内容
4. **文本到音乐模块 (TTM)**: 根据音乐提示词生成音乐
5. **多模态集成模块**: 将图像、语音和音乐合成为最终视频

## 使用方法

### Web界面

系统提供了一个友好的Web界面，可以通过以下方式启动：

#### Windows用户

双击运行 `run_webapp.bat` 文件，将自动启动Web服务器。

#### Linux/Mac用户

在终端中执行：

```bash
chmod +x run_webapp.sh
./run_webapp.sh
```

启动后，在浏览器中访问 `http://localhost:5000` 即可使用Web界面：

1. 在文本框中输入您想要转换的文字
2. 点击"生成视频"按钮
3. 等待处理完成（会显示进度动画）
4. 生成的视频会直接在页面上显示，可以立即播放

### 命令行界面

除了Web界面外，系统还提供命令行方式使用：

#### 交互模式

```bash
python -m Emo_LLM.full_pipeline --interactive
```

#### 单次处理模式

```bash
python -m Emo_LLM.full_pipeline --input "您的输入文本" --output_dir output_videos
```

## 依赖安装

安装所需的依赖包：

```bash
pip install -r requirements.txt
```

## 系统要求

- Python 3.8+
- 确保已安装所有必要的Python包
- 足够的磁盘空间用于存储生成的媒体文件

## 目录结构

- `Emo_LLM/`: 情感理解模块
- `TTI/`: 文本到图像模块
- `TTS/`: 文本到语音模块
- `TTM/`: 文本到音乐模块
- `integration2/`: 多模态集成模块
- `templates/`: Web界面模板
- `static/`: 静态资源文件
- `app.py`: Flask Web应用
- `run_webapp.bat/sh`: 启动脚本 