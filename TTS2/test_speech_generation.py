import sys
import os
import logging
import torch
from speech_generator import SpeechGenerator

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_available_models(generator):
    """测试可用模型"""
    print("\n=== 可用模型 ===")
    for model in generator.get_available_models():
        print(f"- {model}")
        
    print("\n=== 支持的语言 ===")
    for code, name in generator.get_available_languages().items():
        print(f"- {code}: {name}")

def test_chinese_welcome(generator):
    """测试中文欢迎语"""
    print("\n=== 测试中文欢迎语 ===")
    text = "欢迎使用EmoHeal，让我们一起开始这段治愈之旅。"
    result = generator.generate_speech(
        text=text,
        language="zh"
    )
    generator.save_audio(result["audio"], "output/audio/welcome_zh.wav")
    print(f"已保存到: output/audio/welcome_zh.wav")

def test_english_welcome(generator):
    """测试英文欢迎语"""
    print("\n=== 测试英文欢迎语 ===")
    text = "Welcome to EmoHeal, let's begin this healing journey together."
    result = generator.generate_speech(
        text=text,
        language="en"
    )
    generator.save_audio(result["audio"], "output/audio/welcome_en.wav")
    print(f"已保存到: output/audio/welcome_en.wav")

def test_meditation_guide(generator):
    """测试冥想引导语"""
    print("\n=== 测试冥想引导语 ===")
    text = "让我们深呼吸，感受当下的平静。吸气，感受空气充满肺部；呼气，释放所有的紧张。"
    result = generator.generate_speech(
        text=text,
        language="zh"
    )
    generator.save_audio(result["audio"], "output/audio/meditation_guide.wav")
    print(f"已保存到: output/audio/meditation_guide.wav")

def test_custom_text(generator, text, language="zh", output_path="output/audio/custom_output.wav"):
    """测试自定义文本"""
    print(f"\n=== 测试自定义文本 ({language}) ===")
    print(f"输入文本: {text}")
    result = generator.generate_speech(
        text=text,
        language=language
    )
    generator.save_audio(result["audio"], output_path)
    print(f"已保存到: {output_path}")

def main():
    # 创建输出目录
    os.makedirs("output/audio", exist_ok=True)
    
    # 初始化生成器
    generator = SpeechGenerator()
    
    # 加载模型
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"使用设备: {device}")
    generator.load_model(device=device)
    
    # 运行测试
    test_available_models(generator)
    test_chinese_welcome(generator)
    test_english_welcome(generator)
    test_meditation_guide(generator)
    
    # 测试自定义文本
    custom_text = "这是一个测试文本，用于验证语音生成的效果。"
    test_custom_text(generator, custom_text)
    
    print("\n所有测试完成！请检查output/audio目录下的音频文件。")

if __name__ == "__main__":
    main() 