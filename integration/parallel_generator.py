import os
import logging
import torch
import concurrent.futures
from typing import Dict, Any, Tuple
import sys
import time

# 添加模块路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from TTS2.speech_generator import SpeechGenerator
from TTI.image_generator import ImageGenerator
from TTM.music_generator import MusicGenerator

class ParallelGenerator:
    def __init__(self, output_dir: str = "output"):
        """
        初始化并行生成器
        
        Args:
            output_dir: 输出目录
        """
        self.logger = logging.getLogger(__name__)
        self.output_dir = output_dir
        
        # 创建输出目录
        self.audio_dir = os.path.join(output_dir, "audio")
        self.image_dir = os.path.join(output_dir, "images")
        os.makedirs(self.audio_dir, exist_ok=True)
        os.makedirs(self.image_dir, exist_ok=True)
        
        # 初始化设备
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.logger.info(f"Using device: {self.device}")
        
        # 初始化生成器
        self.speech_generator = SpeechGenerator()
        self.image_generator = ImageGenerator()
        self.music_generator = MusicGenerator()
        
        # 加载模型
        self._load_models()
        
    def _load_models(self):
        """加载所有模型"""
        self.logger.info("Loading models...")
        self.speech_generator.load_model(device=self.device)
        self.image_generator.load_model(device=self.device)
        self.music_generator.load_model(device=self.device)
        self.logger.info("All models loaded successfully")
        
    def generate_speech(self, text: str, language: str = "zh") -> str:
        """生成语音"""
        output_path = os.path.join(self.audio_dir, f"speech_{int(time.time())}.wav")
        result = self.speech_generator.generate_speech(
            text=text,
            language=language
        )
        self.speech_generator.save_audio(result["audio"], output_path)
        return output_path
        
    def generate_image(self, prompt: str) -> str:
        """生成图像"""
        output_path = os.path.join(self.image_dir, f"image_{int(time.time())}.png")
        result = self.image_generator.generate_image(prompt)
        self.image_generator.save_image(result["image"], output_path)
        return output_path
        
    def generate_music(self, prompt: str) -> str:
        """生成音乐"""
        output_path = os.path.join(self.audio_dir, f"music_{int(time.time())}.wav")
        result = self.music_generator.generate_music(prompt)
        self.music_generator.save_audio(result["audio"], output_path)
        return output_path
        
    def generate_all(self, 
                    speech_text: str,
                    image_prompt: str,
                    music_prompt: str,
                    language: str = "zh") -> Dict[str, str]:
        """
        并行生成所有内容
        
        Args:
            speech_text: 语音文本
            image_prompt: 图像提示词
            music_prompt: 音乐提示词
            language: 语音语言
            
        Returns:
            包含所有生成文件路径的字典
        """
        self.logger.info("Starting parallel generation...")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            # 提交所有任务
            speech_future = executor.submit(self.generate_speech, speech_text, language)
            image_future = executor.submit(self.generate_image, image_prompt)
            music_future = executor.submit(self.generate_music, music_prompt)
            
            # 等待所有任务完成
            speech_path = speech_future.result()
            image_path = image_future.result()
            music_path = music_future.result()
            
        self.logger.info("All generations completed")
        
        return {
            "speech": speech_path,
            "image": image_path,
            "music": music_path
        }
        
    def cleanup(self):
        """清理资源"""
        # 如果有需要清理的资源，在这里添加代码
        pass 