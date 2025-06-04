from speech_generator import SpeechGenerator
import logging
import os

# 配置日志
logging.basicConfig(level=logging.INFO)

def test_speech_generation():
    # 创建输出目录
    os.makedirs("output/audio", exist_ok=True)
    
    # 初始化语音生成器
    generator = SpeechGenerator()
    
    # 加载模型
    generator.load_model()
    
    # 获取可用的声音预设
    available_voices = generator.get_available_voices()
    print("\nAvailable voices:")
    for voice in available_voices:
        print(f"- {voice}")
    
    # 测试用例
    test_cases = [
        {
            "name": "welcome_en",
            "text": "Welcome to EmoHeal, your personal emotional healing companion. Let's begin our journey to emotional well-being together.",
            "voice_preset": "v2/en_speaker_1",
            "language": "en",
            "temperature": 0.7
        },
        {
            "name": "welcome_zh",
            "text": "欢迎来到EmoHeal，您的个人情感治愈伙伴。让我们一起开始这段情感疗愈之旅。",
            "voice_preset": "v2/zh_speaker_1",
            "language": "zh",
            "temperature": 0.7
        },
        {
            "name": "meditation_guide",
            "text": "Take a deep breath. Feel the air filling your lungs. As you exhale, let go of any tension. Feel your body becoming lighter with each breath.",
            "voice_preset": "v2/en_speaker_0",
            "language": "en",
            "temperature": 0.6
        }
    ]
    
    # 运行测试
    for case in test_cases:
        print(f"\nGenerating speech for: {case['name']}")
        print(f"Text: {case['text']}")
        print(f"Voice: {case['voice_preset']}")
        
        # 生成语音
        result = generator.generate_speech(
            text=case["text"],
            voice_preset=case["voice_preset"],
            language=case["language"],
            temperature=case["temperature"]
        )
        
        # 保存音频
        output_path = f"output/audio/{case['name']}.wav"
        generator.save_audio(result["audio"], output_path)
        print(f"Audio saved to: {output_path}")

if __name__ == "__main__":
    test_speech_generation() 