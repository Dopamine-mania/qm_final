from speech_generator import SpeechGenerator
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)

def main():
    # 初始化语音生成器
    generator = SpeechGenerator()
    
    # 加载模型
    generator.load_model()
    
    # 生成语音
    result = generator.generate_speech(
        text="Welcome to EmoHeal, your personal emotional healing companion. Let's begin our journey to emotional well-being together.",
        language="en"
    )
    
    # 保存音频
    generator.save_audio(result["audio"], "output/welcome_message.wav")
    
if __name__ == "__main__":
    main() 