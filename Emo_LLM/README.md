# 情感反馈全流程系统

本系统将情感反馈大语言模型与多模态生成系统集成，实现了从文本输入到视频生成的全流程。

## 系统组件

- **情感反馈模型**：接收用户文本输入，生成情感标签及各个模态的提示词
- **图像生成模块(TTI)**：基于提示词生成图像
- **语音合成模块(TTS)**：将文本转换为语音
- **音乐生成模块(TTM)**：基于情感提示词生成背景音乐
- **视频合成模块**：将图像、语音和音乐合成为视频

## 运行方式

### 1. 准备环境

确保已安装所有必要的依赖，并且三个生成模块(TTI、TTS、TTM)已正确配置。

### 2. 运行全流程脚本

#### 交互模式

```bash
python full_pipeline.py --interactive
```

在交互模式下，您可以输入任意文本，系统将生成相应的视频。

#### 单次处理模式

```bash
python full_pipeline.py --input "您想要处理的文本"
```

您也可以指定自定义输出目录：

```bash
python full_pipeline.py --input "您想要处理的文本" --output_dir "custom_output"
```

### 3. 参数说明

- `--llm_model_path`：情感反馈模型的路径（默认为 `Model_results/emoheal_merged`）
- `--input`：用户输入文本
- `--output_dir`：输出视频目录（默认为 `output_videos`）
- `--interactive`：启用交互模式

## 输出结果

运行脚本后，系统将：

1. 显示情感反馈模型的JSON响应（情感标签、图像提示词、语音文本、音乐提示词）
2. 依次生成图像、语音和音乐
3. 合成最终视频
4. 显示生成视频的路径

## 示例输出

```
===== 情感反馈模型响应 =====
情感标签: happy

音乐提示词: uplifting cheerful melody with bright piano and strings

图像提示词: A person standing on a mountain peak, arms raised in joy, surrounded by a beautiful sunrise landscape

语音文本: 恭喜你成功了！这是值得庆祝的时刻，你应该为自己感到骄傲。你的努力和坚持得到了回报。
===========================

✓ 视频生成成功: output_videos/happy_response.mp4
```

## 注意事项

- 确保所有模型已正确加载
- 生成视频可能需要一定时间，请耐心等待
- 如遇到错误，请查看控制台输出和日志文件 `full_pipeline.log` 