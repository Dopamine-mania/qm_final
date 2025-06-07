# Emoheal LLM 测试脚本

这个测试脚本用于测试Emoheal模型的情感反馈生成功能。

## 功能

该脚本可以:
- 调用预训练的Emoheal LLM模型
- 接收用户输入的文本
- 生成包含emotion_tag、music_prompt、image_prompt和voice_text的情感反馈
- 支持交互式模式和命令行参数模式

## 目录结构

```
Emo_LLM/
├── Data/                   # 训练数据
├── LLaMA-Factory/          # LLaMA-Factory框架
├── Model_results/          # 模型权重
│   └── emoheal_merged/     # 微调后的模型权重
├── test_model.py           # 测试脚本
├── run_test.sh             # 运行脚本的Shell脚本
└── README.md               # 本文档
```

## 使用方法

### 准备工作

确保已经将微调好的模型放在`Model_results/emoheal_merged`目录下。

### 运行方式1: 使用Shell脚本

```bash
# 交互模式
bash run_test.sh

# 直接传入文本参数
bash run_test.sh --input "我今天心情不太好，感到有点焦虑"
```

### 运行方式2: 直接使用Python

```bash
# 交互模式
python test_model.py

# 直接传入文本参数
python test_model.py --input "我今天心情不太好，感到有点焦虑"
```

### 参数说明

- `--model_path`: 模型路径，默认为`Model_results/emoheal_merged`
- `--input`: 输入文本，如果不提供则进入交互模式

## 输出示例

```
===== EMOHEAL RESPONSE =====
Emotion Tag: calmness

Music Prompt: A 30-second soothing ambient piece featuring slow, rhythmic breathing-like pads, gentle flowing water sounds, and a single, reassuring melodic line from a soft flute. Designed for grounding during anxiety.

Image Prompt: Abstract calming art with soft, diffused shapes in light teal and lavender. Flowing, gentle movements, no hard edges. A central, softly glowing orb suggesting inner peace. Overall impression of safety and tranquility.

Voice Text: 听起来你今天感觉不太好，有些焦虑。这种感觉很常见，但确实不舒服。尝试慢慢地深呼吸，专注于当下。我们为你准备了一些平静的音乐和画面，希望能帮你稳住心神，让这种不适感慢慢退去。
===========================
```

## 与其他模块集成

该模型输出的格式可以直接用于：
- TTI模块 (Text-to-Image): 使用`image_prompt`生成图像
- TTS模块 (Text-to-Speech): 使用`voice_text`生成语音
- TTM模块 (Text-to-Music): 使用`music_prompt`生成音乐 